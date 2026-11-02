#!/usr/bin/env python3
"""Point d'entrée du prototype ufs-diagnostic.

Usage :
    python3 run_diagnostic.py --perimeter config/perimeter_buers.json \
        --indicators config/indicators.json --keys config/isadora_keys.json \
        --data data/raw/buers --out outputs/buers
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from ufsdiag.geo import make_grid
from ufsdiag.loaders import build_pois
from ufsdiag.indicators import compute_indicators, summarize
from ufsdiag.isadora import build_checklist
from ufsdiag.report import render_report
from ufsdiag.mapview import write_map


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--perimeter", required=True)
    ap.add_argument("--indicators", required=True)
    ap.add_argument("--keys", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(args.perimeter, encoding="utf-8") as f:
        perimeter = json.load(f)
    with open(args.indicators, encoding="utf-8") as f:
        cats = json.load(f)["categories"]

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
    summary = summarize(cells, pois_by_cat, radius)
    checklist = build_checklist(args.keys, summary, cat_to_key)

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

    write_map(args.out)

    report = render_report(perimeter, cells, summary, checklist, cats)
    with open(os.path.join(args.out, "report.html"), "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[ok] {len(cells)} mailles analysées, rayon {radius} m")
    for cat_id, s in summary.items():
        print(f"[indicateur] {cat_id}: {s['nb_pois']} objets, {s['pct_cells']}% des mailles à <={radius} m, médiane {s['median_min_dist_m']} m")
    print(f"[sorties] {args.out}/ (report.html, map.html, indicators.geojson, pois.geojson, summary.json, checklist.json)")


if __name__ == "__main__":
    main()
