#!/usr/bin/env python3
"""ufs-diagnostic — application de bureau (tkinter, stdlib uniquement).

Lancer : python3 desktop/app.py
Interface épurée : choisir un cas existant ou en créer un (nom, adresse, rayon),
puis « Lancer le diagnostic ». Le rapport s'ouvre dans le navigateur.
"""
import json
import os
import subprocess
import sys
import threading
import webbrowser

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

import tkinter as tk
from tkinter import messagebox, ttk

CONFIG = os.path.join(ROOT, "config")
DATA = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "outputs")


def list_cases():
    out = []
    if os.path.isdir(CONFIG):
        for fn in sorted(os.listdir(CONFIG)):
            if fn.startswith("perimeter_") and fn.endswith(".json") and "template" not in fn:
                out.append(fn[len("perimeter_"):-len(".json")])
    return out


def geocode_ban(adresse):
    """Géocode une adresse : API Adresse (BAN, officiel) d'abord, Nominatim (OSM) en secours."""
    import urllib.parse, urllib.request
    UA = {"User-Agent": "ufs-diagnostic/1.0 (projet perso UFS)"}
    for q in (adresse, adresse + ", France"):
        try:
            req = urllib.request.Request(
                f"https://api-adresse.data.gouv.fr/search/?{urllib.parse.urlencode({'q': q, 'limit': 3})}",
                headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)
            for f in d.get("features", []):
                c = f["geometry"]["coordinates"]
                if c and c[0] is not None:
                    return c[0], c[1]
        except Exception:
            pass
    try:
        req = urllib.request.Request(
            f"https://nominatim.openstreetmap.org/search?{urllib.parse.urlencode({'q': adresse, 'format': 'json', 'limit': 1, 'countrycodes': 'fr'})}",
            headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        if d:
            return float(d[0]["lon"]), float(d[0]["lat"])
    except Exception:
        pass
    raise ValueError(f"Adresse introuvable : « {adresse} ». Mets la ville + code postal (ex. « 4 rue Fénelon, 69003 Lyon »).")


def bbox_autour(lon, lat, rayon_m=900):
    import math
    dlat = rayon_m / 111320.0
    dlon = rayon_m / (111320.0 * math.cos(math.radians(lat)))
    return {"south": lat - dlat, "west": lon - dlon, "north": lat + dlat, "east": lon + dlon}


def run_diagnostic(case, log):
    log(f"▶ Lancement du diagnostic pour « {case} »…")
    proj = os.path.join(CONFIG, f"project_{case}.json")
    if not os.path.exists(proj):
        proj = os.path.join(CONFIG, "project_buers.json")
    cmd = [sys.executable, os.path.join(ROOT, "run_diagnostic.py"),
           "--perimeter", os.path.join(CONFIG, f"perimeter_{case}.json"),
           "--indicators", os.path.join(CONFIG, "indicators.json"),
           "--keys", os.path.join(CONFIG, "isadora_keys.json"),
           "--kickoff", os.path.join(CONFIG, "kickoff.json"),
           "--project", proj,
           "--eqis", os.path.join(CONFIG, "eqis.json"),
           "--scenarios", os.path.join(CONFIG, "scenarios.json"),
           "--data", os.path.join(DATA, case),
           "--out", os.path.join(OUT, case)]
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    for line in p.stdout.splitlines():
        if line.strip():
            log("  " + line.strip())
    if p.returncode != 0:
        log("✗ ERREUR :\n" + p.stderr[-2000:])
        return None
    log("✔ Diagnostic terminé.")
    return os.path.join(OUT, case, "report.html")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ufs-diagnostic")
        self.geometry("720x560")
        self.configure(bg="#f7f7f5")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f7f7f5")
        style.configure("TLabel", background="#f7f7f5", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#0b5d3b", background="#f7f7f5")
        style.configure("Sub.TLabel", font=("Segoe UI", 9), foreground="#666", background="#f7f7f5")

        ttk.Label(self, text="ufs-diagnostic", style="Header.TLabel").pack(anchor="w", padx=20, pady=(16, 0))
        ttk.Label(self, text="Diagnostic territorial — urbanisme favorable à la santé (open source, données souveraines)",
                  style="Sub.TLabel").pack(anchor="w", padx=20, pady=(0, 12))

        f1 = ttk.Frame(self)
        f1.pack(fill="x", padx=20, pady=4)
        ttk.Label(f1, text="Cas existant :").pack(side="left")
        self.case_var = tk.StringVar(value=list_cases()[0] if list_cases() else "buers")
        self.case_box = ttk.Combobox(f1, textvariable=self.case_var, values=list_cases(), state="readonly", width=30)
        self.case_box.pack(side="left", padx=8)
        ttk.Button(f1, text="Lancer le diagnostic", command=self.on_run).pack(side="left", padx=8)
        ttk.Button(f1, text="Ouvrir le rapport", command=self.on_open).pack(side="left")

        ttk.Label(self, text="Nouveau diagnostic (quartier) :", style="Header.TLabel").pack(anchor="w", padx=20, pady=(18, 4))
        f2 = ttk.Frame(self)
        f2.pack(fill="x", padx=20, pady=2)
        ttk.Label(f2, text="Nom (id) :").grid(row=0, column=0, sticky="w")
        self.new_id = ttk.Entry(f2, width=28)
        self.new_id.grid(row=0, column=1, padx=6, pady=3, sticky="w")
        ttk.Label(f2, text="Adresse de référence :").grid(row=1, column=0, sticky="w")
        self.new_addr = ttk.Entry(f2, width=48)
        self.new_addr.grid(row=1, column=1, columnspan=2, padx=6, pady=3, sticky="w")
        ttk.Label(f2, text="Rayon d'étude (m) :").grid(row=2, column=0, sticky="w")
        self.new_radius = ttk.Entry(f2, width=10)
        self.new_radius.insert(0, "900")
        self.new_radius.grid(row=2, column=1, padx=6, pady=3, sticky="w")
        ttk.Button(f2, text="Créer et lancer", command=self.on_new).grid(row=3, column=1, pady=8, sticky="w")
        ttk.Label(f2, text="(si l'adresse n'est pas trouvée : mets la ville + code postal, ex. « 4 rue Fénelon, 69003 Lyon »)",
                  style="Sub.TLabel").grid(row=4, column=1, sticky="w")

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=20, pady=(14, 4))
        self.log = tk.Text(self, height=14, bg="#fff", fg="#222", font=("Consolas", 9), relief="flat")
        self.log.pack(fill="both", expand=True, padx=20, pady=(0, 12))

    def write_log(self, msg):
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.update_idletasks()

    def on_run(self):
        case = self.case_var.get()
        self.progress.start(10)
        threading.Thread(target=self._run, args=(case,), daemon=True).start()

    def _run(self, case):
        report = run_diagnostic(case, self.write_log)
        self.progress.stop()
        if report:
            self.write_log(f"Rapport : {report}")
            if messagebox.askyesno("Diagnostic terminé", "Ouvrir le rapport dans le navigateur ?"):
                webbrowser.open("file://" + report)

    def on_open(self):
        p = os.path.join(OUT, self.case_var.get(), "report.html")
        if os.path.exists(p):
            webbrowser.open("file://" + p)
        else:
            messagebox.showinfo("Rapport", "Pas encore de rapport pour ce cas. Lance d'abord le diagnostic.")

    def on_new(self):
        cid = self.new_id.get().strip().lower().replace(" ", "_")
        addr = self.new_addr.get().strip()
        if not cid or not addr:
            messagebox.showerror("Champs manquants", "Donne un nom et une adresse.")
            return
        try:
            lon, lat = geocode_ban(addr)
        except Exception as e:
            messagebox.showerror("Géocodage", str(e))
            return
        self.write_log(f"Adresse trouvée : lon={lon:.5f}, lat={lat:.5f}")
        try:
            radius = int(self.new_radius.get() or "900")
        except ValueError:
            radius = 900
        cfg = {
            "name": f"{cid} — {addr}",
            "description": "Cas créé depuis l'application de bureau.",
            "bbox": bbox_autour(lon, lat, radius),
            "grid_cell_m": 150,
            "walk_radius_m": radius,
            "point_ancrage": {"adresse": addr, "lon": lon, "lat": lat,
                               "geocodeur": "api-adresse.data.gouv.fr (BAN) + nominatim (secours)"},
        }
        os.makedirs(os.path.join(DATA, cid), exist_ok=True)
        with open(os.path.join(CONFIG, f"perimeter_{cid}.json"), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        self.case_box["values"] = list_cases()
        self.case_var.set(cid)
        self.write_log(f"Cas « {cid} » créé (rayon {radius} m). Téléchargement des données…")
        self.progress.start(10)
        threading.Thread(target=self._new_run, args=(cid,), daemon=True).start()

    def _new_run(self, cid):
        with open(os.path.join(CONFIG, f"perimeter_{cid}.json"), encoding="utf-8") as f:
            bbox = json.load(f)["bbox"]
        m = 0.004
        s, w, n, e = bbox["south"] - m, bbox["west"] - m, bbox["north"] + m, bbox["east"] + m
        tiles = [(s, w, (s + n) / 2, (w + e) / 2), (s, (w + e) / 2, (s + n) / 2, e),
                 ((s + n) / 2, w, n, (w + e) / 2), ((s + n) / 2, (w + e) / 2, n, e)]
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import fetch_data
        fetch_data.CASES[cid] = {"bbox_margin": (s, w, n, e), "tiles": tiles}
        try:
            fetch_data.fetch_network(cid, os.path.join(DATA, cid))
            fetch_data.fetch_pharmacies(cid, os.path.join(DATA, cid))
        except Exception as e:
            self.write_log(f"⚠ téléchargement partiel : {e}")
        report = run_diagnostic(cid, self.write_log)
        self.progress.stop()
        if report:
            self.write_log(f"Rapport : {report}")
            webbrowser.open("file://" + report)


if __name__ == "__main__":
    App().mainloop()
