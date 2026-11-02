#!/usr/bin/env python3
"""Télécharge les données ouvertes (WFS souverains) pour un cas d'étude.

Usage : python3 tools/fetch_data.py buers
Écrit dans data/raw/buers/ : reseau_routier.geojson, pharmacies.geojson, etc.
Toutes les sources sont des WFS français (Métropole de Lyon / data.gouv.fr-magOSM).
"""
import json
import os
import sys
import urllib.parse
import urllib.request

BASE = "https://data.grandlyon.com/geoserver/ows"
MAGOSM = "https://magosm.magellium.com/geoserver/wfs"

CASES = {
    "buers": {
        "bbox_margin": (45.766, 4.865, 45.784, 4.896),  # sud, ouest, nord, est (marge autour du périmètre)
        "tiles": [(45.766, 4.865, 45.775, 4.8805), (45.766, 4.8805, 45.775, 4.896),
                  (45.775, 4.865, 45.784, 4.8805), (45.775, 4.8805, 45.784, 4.896)],
    }
}


def wfs(base, typename, bbox, count, props, srs="EPSG:4326"):
    q = urllib.parse.urlencode({
        "SERVICE": "WFS", "VERSION": "2.0.0", "request": "GetFeature",
        "typename": typename, "outputFormat": "application/json",
        "SRSNAME": srs, "count": count, "propertyname": props,
        "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
    })
    with urllib.request.urlopen(f"{base}?{q}", timeout=60) as r:
        return json.load(r)


def fetch_network(case, out_dir):
    feats, seen = [], set()
    for tile in CASES[case]["tiles"]:
        fc = wfs(BASE, "pvo_patrimoine_voirie.pvotronconwebcriter", tile, 2000,
                 "the_geom,longueur,libelle,sens,infotrafic,nombrevoies")
        for f in fc.get("features", []):
            if f["id"] not in seen:
                seen.add(f["id"])
                feats.append(f)
    fc = {"type": "FeatureCollection",
          "name": "Réseau routier (tronçons CRITER) - source WFS pvo_patrimoine_voirie.pvotronconwebcriter, DataGrandLyon, Licence Ouverte",
          "features": feats}
    path = os.path.join(out_dir, "reseau_routier.geojson")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False)
    print(f"reseau_routier.geojson: {len(feats)} tronçons -> {path}")


def fetch_pharmacies(case, out_dir):
    s, w, n, e = CASES[case]["bbox_margin"]
    q = urllib.parse.urlencode({
        "request": "GetFeature", "version": "2.0.0", "count": 500,
        "outputFormat": "application/json", "typeName": "magosm:pharmacies_point",
        "srsName": "EPSG:4326", "bbox": f"{s},{w},{n},{e}",
    })
    try:
        with urllib.request.urlopen(f"{MAGOSM}?{q}", timeout=60) as r:
            fc = json.load(r)
    except Exception as ex:
        print(f"pharmacies: échec ({ex})")
        return
    fc["name"] = "Pharmacies (extrait OSM quotidien via magOSM/data.gouv.fr, ODbL)"
    path = os.path.join(out_dir, "pharmacies.geojson")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False)
    print(f"pharmacies.geojson: {len(fc.get('features', []))} -> {path}")


def main():
    case = sys.argv[1] if len(sys.argv) > 1 else "buers"
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "raw", case)
    os.makedirs(out_dir, exist_ok=True)
    fetch_network(case, out_dir)
    fetch_pharmacies(case, out_dir)


if __name__ == "__main__":
    main()
