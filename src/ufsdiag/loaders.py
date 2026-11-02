import json
import os

from .geo import feature_point


def load_geojson(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("features", [])


def build_pois(category, data_dir):
    path = os.path.join(data_dir, category["file"])
    if not os.path.exists(path):
        return []
    pois = []
    for ft in load_geojson(path):
        lon, lat = feature_point(ft["geometry"])
        props = ft.get("properties", {}) or {}
        name_field = category.get("name_field") or "nom"
        name = props.get(name_field) or props.get("identifiant") or props.get("commune") or "?"
        pois.append({"name": str(name), "lon": lon, "lat": lat, "props": props})
    return pois
