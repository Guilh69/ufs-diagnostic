"""Mini-API HTTP (stdlib) exposant le moteur ufs-diagnostic.

Endpoints (JSON) :
  GET  /health
  GET  /perimeters                      -> périmètres connus (config/perimeter_*.json)
  POST /diagnostic  {"perimeter": "buers", "radius_m": 800, "with_network": true}
       -> indicateurs par maille, zone, point, eqis, bruit (réutilise run_diagnostic en mémoire)
  GET  /report/<perimeter>              -> sert outputs/<perimeter>/report.html

Lancement : python3 -m ufsdiag.api --port 8080   (depuis src/)
"""
import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from ufsdiag.geo import make_grid
from ufsdiag.loaders import build_pois, load_geojson
from ufsdiag.indicators import compute_indicators, attach_network, summarize
from ufsdiag.isadora import build_checklist
from ufsdiag.kickoff import build_kickoff
from ufsdiag.eqis import compute_eqis_block, compute_scenario_marche
from ufsdiag import network as net
from ufsdiag import zone as zonemod


def list_perimeters():
    cfg = os.path.join(ROOT, "config")
    out = []
    for fn in sorted(os.listdir(cfg)):
        if fn.startswith("perimeter_") and fn.endswith(".json"):
            with open(os.path.join(cfg, fn), encoding="utf-8") as f:
                p = json.load(f)
            out.append({"id": fn[len("perimeter_"):-len(".json")], "name": p.get("name")})
    return out


def run_diagnostic(perimeter_id, radius_m=800, with_network=True):
    with open(os.path.join(ROOT, "config", f"perimeter_{perimeter_id}.json"), encoding="utf-8") as f:
        perimeter = json.load(f)
    with open(os.path.join(ROOT, "config", "indicators.json"), encoding="utf-8") as f:
        cats = json.load(f)["categories"]
    data_dir = os.path.join(ROOT, "data", "raw", perimeter_id)
    radius = radius_m or perimeter["walk_radius_m"]

    cells = make_grid(perimeter["bbox"], perimeter["grid_cell_m"])
    pois_by_cat, cat_to_key = {}, {}
    for cat in cats:
        pois_by_cat[cat["id"]] = build_pois(cat, data_dir)
        cat_to_key[cat["id"]] = cat.get("isadora_key")
    cells = compute_indicators(cells, pois_by_cat, radius)

    net_min_by_cat = {}
    adj = edges = None
    net_file = os.path.join(data_dir, "reseau_routier.geojson")
    if with_network and os.path.exists(net_file):
        adj, edges = net.build_graph(load_geojson(net_file))
        for cat_id, pois in pois_by_cat.items():
            if pois:
                net_min_by_cat[cat_id] = net.network_distances_to_pois(adj, edges, cells, pois)
        cells = attach_network(cells, net_min_by_cat, radius)

    summary = summarize(cells, pois_by_cat, radius, net_min_by_cat)
    checklist = build_checklist(os.path.join(ROOT, "config", "isadora_keys.json"), summary, cat_to_key)

    zone_info = point_info = None
    zone_cfg = perimeter.get("zone")
    zone_file = os.path.join(data_dir, zone_cfg["file"]) if zone_cfg else None
    if zone_file and os.path.exists(zone_file):
        polygons, _, _ = zonemod.load_zone(zone_file)
        area_m2 = zonemod.polygon_area_m2(polygons)
        pop_zone = round(perimeter["population_commune"] * (area_m2 / 1e4) / perimeter["surface_commune_ha"])
        zone_info = zonemod.zone_indicators(polygons, cells, pois_by_cat, net_min_by_cat, radius, pop_zone)
        zone_info["nom"] = (zone_cfg or {}).get("nom")
        pa = perimeter.get("point_ancrage")
        if pa and adj is not None:
            point_info = zonemod.point_distances(pa["lon"], pa["lat"], pois_by_cat, adj, edges)
            point_info["_adresse"] = pa["adresse"]

    eqis_block = scenario = None
    eqis_cfg_path = os.path.join(ROOT, "config", "eqis.json")
    if os.path.exists(eqis_cfg_path):
        with open(eqis_cfg_path, encoding="utf-8") as f:
            eqis_cfg = json.load(f)
        eqis_block = compute_eqis_block(data_dir, eqis_cfg)
        with open(os.path.join(ROOT, "config", "scenarios.json"), encoding="utf-8") as f:
            scenario = compute_scenario_marche(data_dir, eqis_block, json.load(f))

    return {
        "perimeter": {"id": perimeter_id, "name": perimeter["name"], "bbox": perimeter["bbox"],
                      "grid_cell_m": perimeter["grid_cell_m"], "radius_m": radius},
        "nb_cells": len(cells),
        "summary": summary,
        "zone": zone_info,
        "point_ancrage": point_info,
        "checklist": checklist,
        "eqis": eqis_block,
        "scenario_marche": scenario,
        "cells_sample": [
            {"id": c["id"], "score": c["score"],
             "indicators": {k: v for k, v in c["indicators"].items()},
             "centroid": [round(c["lon"], 6), round(c["lat"], 6)]}
            for c in cells[:200]
        ],
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj, ctype="application/json"):
        body = obj if isinstance(obj, bytes) else json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"status": "ok"})
        if self.path == "/perimeters":
            return self._send(200, list_perimeters())
        if self.path.startswith("/report/"):
            pid = self.path[len("/report/"):]
            p = os.path.join(ROOT, "outputs", pid, "report.html")
            if os.path.exists(p):
                return self._send(200, open(p, "rb").read(), "text/html")
            return self._send(404, {"error": "rapport non généré"})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/diagnostic":
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")
            pid = body.get("perimeter", "buers")
            try:
                return self._send(200, run_diagnostic(pid, body.get("radius_m"), body.get("with_network", True)))
            except Exception as e:
                return self._send(500, {"error": str(e)})
        return self._send(404, {"error": "not found"})

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"ufs-diagnostic API sur http://{args.host}:{args.port} (GET /perimeters, POST /diagnostic)")
    srv.serve_forever()


if __name__ == "__main__":
    main()
