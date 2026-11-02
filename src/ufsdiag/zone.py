import math

from .geo import haversine_m


def rings_to_polygons(rings):
    """Convertit des rings ArcGIS en liste de polygones GeoJSON [[ [lon,lat], ... ]]."""
    polys = []
    for ring in rings:
        pts = [[float(p[0]), float(p[1])] for p in ring]
        if len(pts) > 2 and pts[0] != pts[-1]:
            pts.append(pts[0])
        polys.append(pts)
    return polys


def arcgis_feature_to_polygons(geom):
    """Retourne une liste de polygones, chaque polygone = [ring_extérieur, trou1, ...]."""
    if geom.get("rings"):
        return [[r] for r in rings_to_polygons(geom["rings"])]
    if geom.get("type") == "Polygon":
        return [geom["coordinates"]]
    if geom.get("type") == "MultiPolygon":
        return list(geom["coordinates"])
    return []


def point_in_ring(lon, lat, ring):
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def point_in_polygons(lon, lat, polygons):
    for poly in polygons:
        outer = poly[0]
        if point_in_ring(lon, lat, outer):
            holes = poly[1:]
            if not any(point_in_ring(lon, lat, h) for h in holes):
                return True
    return False


def polygon_area_m2(polygons):
    """Aire approchée (formule de shoelace en mètres, equirectangulaire locale)."""
    total = 0.0
    for poly in polygons:
        ring = poly[0]
        if not ring:
            continue
        lat0 = math.radians(sum(p[1] for p in ring) / len(ring))
        xs = [p[0] * 111320.0 * math.cos(lat0) for p in ring]
        ys = [p[1] * 110540.0 for p in ring]
        a = 0.0
        for i in range(len(ring) - 1):
            a += xs[i] * ys[i + 1] - xs[i + 1] * ys[i]
        total += abs(a) / 2.0
        for hole in poly[1:]:
            hx = [p[0] * 111320.0 * math.cos(lat0) for p in hole]
            hy = [p[1] * 110540.0 for p in hole]
            ah = 0.0
            for i in range(len(hole) - 1):
                ah += hx[i] * hy[i + 1] - hx[i + 1] * hy[i]
            total -= abs(ah) / 2.0
    return total


def load_zone(path):
    """Charge un GeoJSON de zone (polygones standards ou rings ArcGIS). Retourne (polygons, props)."""
    import json
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    feats = data.get("features", [])
    polygons = []
    props = {}
    for ft in feats:
        g = ft.get("geometry", {})
        polys = arcgis_feature_to_polygons(g)
        polygons.extend(polys)
        props.update(ft.get("properties") or ft.get("attributes") or {})
    return polygons, props, data.get("name", "")


def zone_indicators(polygons, cells, pois_by_cat, net_min_by_cat, radius_m, pop_zone=None):
    """Indicateurs calculés DANS la zone : effectifs par catégorie, densités,
    et distance moyenne (médiane + moyenne) au plus proche équipement par le réseau."""
    zone_cells = [c for c in cells if point_in_polygons(c["lon"], c["lat"], polygons)]
    area_m2 = polygon_area_m2(polygons)
    out = {"area_m2": round(area_m2), "area_km2": round(area_m2 / 1e6, 3),
           "nb_mailles": len(zone_cells), "population_estimee": pop_zone, "categories": {}}
    for cat_id, pois in pois_by_cat.items():
        if not pois:
            continue
        in_zone = [p for p in pois if point_in_polygons(p["lon"], p["lat"], polygons)]
        dens_km2 = len(in_zone) / (area_m2 / 1e6) if area_m2 else None
        dens_10k = (len(in_zone) / pop_zone * 10000) if pop_zone else None
        dists = []
        if net_min_by_cat.get(cat_id):
            idx = {c["id"]: i for i, c in enumerate(cells)}
            dists = [net_min_by_cat[cat_id][idx[c["id"]]] for c in zone_cells
                     if net_min_by_cat[cat_id][idx[c["id"]]] is not None]
        d = {
            "nb_dans_zone": len(in_zone),
            "densite_par_km2": round(dens_km2, 1) if dens_km2 is not None else None,
            "pour_10000_hab": round(dens_10k, 1) if dens_10k is not None else None,
        }
        if dists:
            ds = sorted(dists)
            d["dist_moyenne_reseau_m"] = round(sum(ds) / len(ds))
            d["dist_mediane_reseau_m"] = round(ds[len(ds) // 2])
            d["pct_mailles_zone_a_le_radius"] = round(100.0 * sum(1 for x in ds if x <= radius_m) / len(ds), 1)
        out["categories"][cat_id] = d
    return out


def point_distances(lon, lat, pois_by_cat, adj=None, edges=None):
    """Distances depuis un point précis (adresse) vers le plus proche équipement de chaque catégorie."""
    from . import network as net
    out = {}
    for cat_id, pois in pois_by_cat.items():
        if not pois:
            continue
        d_vol = min(haversine_m(lon, lat, p["lon"], p["lat"]) for p in pois)
        entry = {"min_dist_vol_m": round(d_vol)}
        if adj is not None and edges is not None:
            na, nb, la, lb, proj, off = net.snap_to_graph(adj, edges, lon, lat)
            dist = net.dijkstra_multi_source(adj, {na: la + off, nb: lb + off})
            best = math.inf
            for p in pois:
                pa, pb, la2, lb2, _proj, off2 = net.snap_to_graph(adj, edges, p["lon"], p["lat"])
                da = dist.get(pa, math.inf)
                db = dist.get(pb, math.inf)
                if math.isfinite(da):
                    best = min(best, da + la2 + off2)
                if math.isfinite(db):
                    best = min(best, db + lb2 + off2)
            entry["min_dist_reseau_m"] = round(best) if math.isfinite(best) else None
            entry["plus_proche"] = min(pois, key=lambda p: haversine_m(lon, lat, p["lon"], p["lat"]))["name"]
        out[cat_id] = entry
    return out
