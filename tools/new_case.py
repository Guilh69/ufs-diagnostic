#!/usr/bin/env python3
"""Prépare un nouveau cas d'étude (nouveau quartier) en 3 étapes guidées.

Usage : python3 tools/new_case.py mon_quartier
Puis répondre aux questions (ou éditer config/perimeter_mon_quartier.json).
"""
import json
import os
import sys
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def geocode_ban(adresse):
    """Géocode une adresse en France via l'API Adresse (BAN, Etalab) — gratuite, officielle."""
    q = urllib.parse.urlencode({"q": adresse, "limit": 1})
    with urllib.request.urlopen(f"https://api-adresse.data.gouv.fr/search/?{q}", timeout=30) as r:
        d = json.load(r)
    if not d.get("features"):
        return None, None
    c = d["features"][0]["geometry"]["coordinates"]
    return c[0], c[1]


def main():
    case = sys.argv[1] if len(sys.argv) > 1 else None
    if not case:
        print("Usage: python3 tools/new_case.py <id_quartier>   (ex. maurepas_rennes)")
        print("Puis édite config/perimeter_<id_quartier>.json")
        return
    case = case.lower().replace(" ", "_")
    tpl = os.path.join(ROOT, "config", "perimeter_template.json")
    dst = os.path.join(ROOT, "config", f"perimeter_{case}.json")
    if os.path.exists(dst):
        print(f"{dst} existe déjà.")
        return
    s = open(tpl, encoding="utf-8").read()
    open(dst, "w", encoding="utf-8").write(s)
    os.makedirs(os.path.join(ROOT, "data", "raw", case), exist_ok=True)
    print(f"OK -> {dst}")
    print(f"Dossier données créé : data/raw/{case}/")
    print("\nÉtapes suivantes :")
    print(f"  1. Ouvre {dst} et remplis : name, bbox (sud/ouest/nord/est en degrés), zone, point_ancrage.adresse")
    print(f"  2. Géocode l'adresse : python3 tools/new_case.py geocode \"<adresse>\"")
    print(f"  3. Télécharge les données : python3 tools/fetch_data.py {case}   (modifie CASES dans fetch_data.py pour la bbox)")
    print(f"  4. Lance le diagnostic : python3 run_diagnostic.py --perimeter config/perimeter_{case}.json --indicators config/indicators.json --keys config/isadora_keys.json --kickoff config/kickoff.json --project config/project_buers.json --eqis config/eqis.json --scenarios config/scenarios.json --data data/raw/{case} --out outputs/{case}")
    if len(sys.argv) > 2 and sys.argv[1] == "geocode":
        lon, lat = geocode_ban(sys.argv[2])
        print(f"geocode BAN: lon={lon} lat={lat}")


if __name__ == "__main__":
    main()
