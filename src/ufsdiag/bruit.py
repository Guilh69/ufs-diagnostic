"""Exposition au bruit routier Lden 2022 via WMS GetFeatureInfo (DataGrandLyon, couche grandlyon:road_lden_p).
GRAY_INDEX = niveau Lden en dB(A). Seuils UE : Lden > 68 dB(A) = dépassement valeur limite ; OMS 2018 recommande < 53 dB(A) Lden.
"""
import json
import math
import urllib.parse
import urllib.request

from .geotiff import wgs84_to_l93

WMS = "https://data.grandlyon.com/geoserver/wms"
LAYER = "grandlyon:road_lden_p"
SEUIL_UE_LDEN = 68.0
SEUIL_OMS_LDEN = 53.0


def _get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "ufs-diagnostic/0.7"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def lden_at(lon, lat):
    """Niveau Lden (dB(A)) au point lon/lat via GetFeatureInfo. None si hors raster."""
    x, y = wgs84_to_l93(lon, lat)
    half = 250.0
    q = urllib.parse.urlencode({
        "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetFeatureInfo",
        "LAYERS": LAYER, "QUERY_LAYERS": LAYER, "STYLES": "",
        "CRS": "EPSG:2154", "BBOX": f"{x-half},{y-half},{x+half},{y+half}",
        "WIDTH": 100, "HEIGHT": 100, "I": 50, "J": 50,
        "INFO_FORMAT": "application/json", "FEATURE_COUNT": 1,
    })
    d = json.loads(_get(f"{WMS}?{q}"))
    feats = d.get("features", [])
    if not feats:
        return None
    v = feats[0].get("properties", {}).get("GRAY_INDEX")
    return float(v) if v is not None else None


def bruit_zone(cells_in_zone, point=None, max_points=40):
    """Échantillonne le Lden sur les mailles de la zone (sous-échantillonnage si > max_points)."""
    pts = list(cells_in_zone)
    if len(pts) > max_points:
        step = len(pts) / max_points
        pts = [pts[int(i * step)] for i in range(max_points)]
    vals = []
    for c in pts:
        v = lden_at(c["lon"], c["lat"])
        if v is not None:
            vals.append(v)
    result = {
        "nb_points_echantillonnes": len(pts),
        "nb_avec_valeur": len(vals),
        "lden_moyen": round(sum(vals) / len(vals), 1) if vals else None,
        "lden_max": max(vals) if vals else None,
        "pct_points_depassement_ue_68": round(100.0 * sum(1 for v in vals if v > SEUIL_UE_LDEN) / len(vals), 1) if vals else None,
        "pct_points_depassement_oms_53": round(100.0 * sum(1 for v in vals if v > SEUIL_OMS_LDEN) / len(vals), 1) if vals else None,
        "seuils": {"UE_Lden_68": SEUIL_UE_LDEN, "OMS_Lden_53": SEUIL_OMS_LDEN},
        "source": "WMS DataGrandLyon grandlyon:road_lden_p (cartes stratégiques de bruit routier 2022, Lden dB(A))",
    }
    if point:
        result["point_ancrage"] = {"adresse": point.get("adresse"), "lden_dba": lden_at(point["lon"], point["lat"])}
    return result
