#!/usr/bin/env python3
"""Point d'entrée du prototype ufs-diagnostic (v0.2).

Usage :
    python3 run_diagnostic.py --perimeter config/perimeter_buers.json \
        --indicators config/indicators.json --keys config/isadora_keys.json \
        --kickoff config/kickoff.json --project config/project_buers.json \
        --data data/raw/buers --out outputs/buers

Données réseau optionnelles : si data/raw/<cas>/reseau_routier.geojson existe,
les distances réseau (Dijkstra) et l'isochrone sont calculées.
Pour (re)télécharger les données ouvertes : python3 tools/fetch_data.py buers
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from ufsdiag.geo import make_grid
from ufsdiag.loaders import build_pois, load_geojson
from ufsdiag.indicators import compute_indicators, attach_network, summarize
from ufsdiag.isadora import build_checklist
from ufsdiag.kickoff import build_kickoff
from ufsdiag.report import render_report
from ufsdiag.mapview import write_map
from ufsdiag import network as net
from ufsdiag.eqis import compute_eqis_block, compute_scenario_marche
from ufsdiag import zone as zonemod
from ufsdiag.docx import html_to_docx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--perimeter", required=True)
    ap.add_argument("--indicators", required=True)
    ap.add_argument("--keys", required=True)
    ap.add_argument("--kickoff", default=None)
    ap.add_argument("--project", default=None)
    ap.add_argument("--eqis", default=None)
    ap.add_argument("--scenarios", default=None)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(args.perimeter, encoding="utf-8") as f:
        perimeter = json.load(f)
    with open(args.indicators, encoding="utf-8") as f:
        indicators_cfg = json.load(f)
    cats = indicators_cfg["categories"]

    os.makedirs(args.out, exist_ok=True)

    cells = make_grid(perimeter["bbox"], perimeter["grid_cell_m"])
    radius = perimeter["walk_radius_m"]

    pois_by_cat = {}
    cat_to_key = {}
    for cat in cats:
        pois = build_pois(cat, args.data)
        pois_by_cat[cat["id"]] = pois
        cat_to_key[cat["id"]] = cat.get("isadora_key")
        print(f"[data] {cat['id']}: {len(pois)} objets")

    cells = compute_indicators(cells, pois_by_cat, radius)

    # --- v0.2 : distances réseau + isochrone ---
    net_cfg = indicators_cfg.get("reseau", {})
    net_file = os.path.join(args.data, net_cfg.get("file", "reseau_routier.geojson"))
    net_min_by_cat = {}
    iso_fc = None
    if os.path.exists(net_file):
        features = load_geojson(net_file)
        adj, edges = net.build_graph(features)
        print(f"[reseau] {len(features)} tronçons, {len(adj)} nœuds")
        for cat_id, pois in pois_by_cat.items():
            if pois:
                net_min_by_cat[cat_id] = net.network_distances_to_pois(adj, edges, cells, pois)
        cells = attach_network(cells, net_min_by_cat, radius)
        iso_m = round(radius)  # 800 m ≈ 10 min à 4,8 km/h
        # origine de l'isochrone : nœud le plus connecté (centre réel du réseau)
        hub = max(adj, key=lambda n: len(adj[n]))
        keep, _dist = net.isochrone_edges(adj, edges, hub, iso_m)
        iso_fc = net.isochrone_geojson(keep, iso_m)
        perimeter["network"] = {"isochrone_m": iso_m, "nb_troncons": len(keep),
                                "hub": [round(hub[0], 6), round(hub[1], 6)]}
        with open(os.path.join(args.out, "isochrone.geojson"), "w", encoding="utf-8") as f:
            json.dump(iso_fc, f, ensure_ascii=False)
        print(f"[isochrone] {len(keep)} tronçons atteignables à ~{iso_m} m à pied depuis le centre du périmètre")
    else:
        print("[reseau] pas de reseau_routier.geojson : distances réseau ignorées (voir tools/fetch_data.py)")

    summary = summarize(cells, pois_by_cat, radius, net_min_by_cat)
    checklist = build_checklist(args.keys, summary, cat_to_key)

    # --- v0.4 : zone définie (ex. QPV) + point d'ancrage (adresse) ---
    zone_info = None
    point_info = None
    zone_cfg = perimeter.get("zone")
    zone_file = os.path.join(args.data, zone_cfg["file"]) if zone_cfg else None
    adj = edges = None
    if os.path.exists(net_file):
        features = load_geojson(net_file)
        adj, edges = net.build_graph(features)
    if zone_file and os.path.exists(zone_file):
        polygons, zprops, zname = zonemod.load_zone(zone_file)
        area_m2 = zonemod.polygon_area_m2(polygons)
        surf_com = perimeter.get("surface_commune_ha")
        pop_com = perimeter.get("population_commune")
        pop_zone = round(pop_com * (area_m2 / 1e4) / surf_com) if (surf_com and pop_com) else None
        zone_info = zonemod.zone_indicators(polygons, cells, pois_by_cat, net_min_by_cat, radius, pop_zone)
        zone_info["nom"] = zone_cfg.get("nom")
        zone_info["source"] = zone_cfg.get("source")
        zone_info["population_note"] = "estimation = population communale × (surface zone / surface commune)"
        print(f"[zone] {zone_info['nom']}: {zone_info['area_km2']} km², {zone_info['nb_mailles']} mailles, pop estimée {pop_zone}")
        for cat_id, d in zone_info["categories"].items():
            extra = f", distance moyenne réseau {d.get('dist_moyenne_reseau_m')} m" if d.get("dist_moyenne_reseau_m") else ""
            print(f"[zone] {cat_id}: {d['nb_dans_zone']} dans la zone, {d['densite_par_km2']}/km², {d.get('pour_10000_hab')}/10k hab{extra}")
    pa = perimeter.get("point_ancrage")
    if pa and adj is not None:
        point_info = zonemod.point_distances(pa["lon"], pa["lat"], pois_by_cat, adj, edges)
        point_info["_adresse"] = pa["adresse"]
        point_info["_lon"] = pa["lon"]
        point_info["_lat"] = pa["lat"]
        print(f"[point] depuis {pa['adresse']} :")
        for cat_id, d in point_info.items():
            if cat_id.startswith("_"):
                continue
            print(f"  {cat_id}: vol d'oiseau {d['min_dist_vol_m']} m, réseau {d.get('min_dist_reseau_m')} m ({d.get('plus_proche')})")
    if zone_info or point_info:
        with open(os.path.join(args.out, "zone.json"), "w", encoding="utf-8") as f:
            json.dump({"zone": zone_info, "point_ancrage": point_info}, f, ensure_ascii=False, indent=2)
    kickoff = build_kickoff(args.kickoff, args.project) if args.kickoff and args.project else None

    # --- v0.3 : EQIS-lite PM2.5 + scénario marche (HEAT-lite) ---
    eqis_block = None
    scenario_marche = None
    if args.eqis and os.path.exists(args.eqis):
        with open(args.eqis, encoding="utf-8") as f:
            eqis_cfg = json.load(f)
        eqis_block = compute_eqis_block(args.data, eqis_cfg)
        if eqis_block:
            print(f"[eqis] {eqis_block['commune']}: pop {eqis_block['population']:,}, indice PM2.5 modélisé {eqis_block['indice_communal_pm25']} µg/m³, "
                  f"stations 2024 moy {eqis_block['moyenne_stations_pm25']} µg/m³")
            for label, r in eqis_block["resultats"].items():
                print(f"[eqis] {label}: C={r['concentration_ugm3']} µg/m³ -> {r['deces_attribuables_an']} décès/an attribuables")
        if args.scenarios and os.path.exists(args.scenarios):
            with open(args.scenarios, encoding="utf-8") as f:
                scenarios_cfg = json.load(f)
            scenario_marche = compute_scenario_marche(args.data, eqis_block, scenarios_cfg)
            if scenario_marche:
                print(f"[scenario] {scenario_marche['libelle']}: {scenario_marche['deces_evites_an']} décès/an évités")

    indicators_fc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "id": c["id"],
                    "score": c["score"],
                    "indicators": c["indicators"],
                    "radius_m": radius,
                },
                "geometry": {"type": "Polygon", "coordinates": c["polygon"]},
            }
            for c in cells
        ],
    }
    pois_features = []
    for cat in cats:
        for p in pois_by_cat[cat["id"]]:
            detail = "; ".join(f"{k}={v}" for k, v in list(p["props"].items())[:6])
            pois_features.append({
                "type": "Feature",
                "properties": {"category": cat["id"], "name": p["name"], "detail": detail},
                "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},
            })
    pois_fc = {"type": "FeatureCollection", "features": pois_features}

    with open(os.path.join(args.out, "indicators.geojson"), "w", encoding="utf-8") as f:
        json.dump(indicators_fc, f, ensure_ascii=False)
    with open(os.path.join(args.out, "pois.geojson"), "w", encoding="utf-8") as f:
        json.dump(pois_fc, f, ensure_ascii=False)
    with open(os.path.join(args.out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.out, "checklist.json"), "w", encoding="utf-8") as f:
        json.dump(checklist, f, ensure_ascii=False, indent=2)
    if kickoff:
        with open(os.path.join(args.out, "kickoff.json"), "w", encoding="utf-8") as f:
            json.dump(kickoff, f, ensure_ascii=False, indent=2)

    write_map(args.out)

    if eqis_block:
        with open(os.path.join(args.out, "eqis.json"), "w", encoding="utf-8") as f:
            json.dump({"eqis": eqis_block, "scenario_marche": scenario_marche}, f, ensure_ascii=False, indent=2)

    report = render_report(perimeter, cells, summary, checklist, cats, kickoff=kickoff, eqis=eqis_block,
                           scenario=scenario_marche, zone_info=zone_info, point_info=point_info)
    with open(os.path.join(args.out, "report.html"), "w", encoding="utf-8") as f:
        f.write(report)
    html_to_docx(report, os.path.join(args.out, "rapport.docx"))
    print("[docx] rapport.docx exporté")

    print(f"[ok] {len(cells)} mailles analysées, rayon {radius} m")
    for cat_id, s in summary.items():
        net_txt = f", réseau {s['pct_cells_reseau']}% ≤{radius} m (médiane {s['median_min_dist_reseau_m']} m)" if "pct_cells_reseau" in s else ""
        print(f"[indicateur] {cat_id}: {s['nb_pois']} objets, {s['pct_cells']}% des mailles à <={radius} m (médiane {s['median_min_dist_m']} m){net_txt}")
    print(f"[sorties] {args.out}/ (report.html, map.html, indicators.geojson, pois.geojson, isochrone.geojson, summary.json, checklist.json, kickoff.json)")


if __name__ == "__main__":
    main()
