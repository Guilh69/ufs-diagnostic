"""Mise à jour de ufs-diagnostic depuis GitHub, sans toucher aux données utilisateur.

Règles de protection (jamais écrasés) :
  - config/perimeter_*.json créés par l'utilisateur (sauf template)
  - config/project_*.json
  - data/raw/<cas>/   (données téléchargées)
  - outputs/          (rapports générés)
"""
import io
import json
import os
import urllib.request
import zipfile

REPO = "Guilh69/ufs-diagnostic"
BRANCH = "vibe/ufs-diagnostic-prototype-83eb68"
VERSION_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/VERSION"
ZIP_URL = f"https://github.com/{REPO}/archive/refs/heads/{BRANCH}.zip"

PROTECTED_PREFIXES = ("data/raw/", "outputs/")
PROTECTED_CONFIG = ("config/perimeter_", "config/project_")


def local_version(root):
    p = os.path.join(root, "VERSION")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read().strip()
    return "0.0.0"


def remote_version():
    req = urllib.request.Request(VERSION_URL, headers={"User-Agent": "ufs-diagnostic-updater"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode().strip()


def _vkey(v):
    return tuple(int(x) for x in v.split(".") if x.isdigit())


def check_update(root):
    try:
        rv = remote_version()
    except Exception as e:
        return {"ok": False, "error": str(e)}
    lv = local_version(root)
    return {"ok": True, "local": lv, "remote": rv, "update_available": _vkey(rv) > _vkey(lv)}


def _is_protected(rel):
    rel = rel.replace("\\", "/")
    for p in PROTECTED_PREFIXES:
        if rel.startswith(p):
            return True
    for p in PROTECTED_CONFIG:
        if rel.startswith(p) and "template" not in rel:
            return True
    return False


def apply_update(root, log=print):
    """Télécharge le ZIP de la branche et écrase le code, en protégeant les données utilisateur."""
    req = urllib.request.Request(ZIP_URL, headers={"User-Agent": "ufs-diagnostic-updater"})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read()
    z = zipfile.ZipFile(io.BytesIO(data))
    base = z.namelist()[0].split("/")[0] + "/"
    n_ok = n_skip = 0
    for name in z.namelist():
        if name.endswith("/"):
            continue
        rel = name[len(base):]
        if _is_protected(rel):
            n_skip += 1
            continue
        if rel in ("Lancer-ufs-diagnostic.bat", "Lancer-ufs-diagnostic.command", "Lancer-ufs-diagnostic.sh", "diagnostic.bat"):
            pass  # on les met à jour aussi
        dst = os.path.join(root, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as f:
            f.write(z.read(name))
        n_ok += 1
    log(f"Mise à jour appliquée : {n_ok} fichiers mis à jour, {n_skip} fichiers utilisateur protégés.")
    return {"updated": n_ok, "protected": n_skip, "version": remote_version()}
