import math


def haversine_m(lon1, lat1, lon2, lat2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def make_grid(bbox, cell_m):
    south, west, north, east = bbox["south"], bbox["west"], bbox["north"], bbox["east"]
    lat0 = (south + north) / 2.0
    dlat = cell_m / 111320.0
    dlon = cell_m / (111320.0 * math.cos(math.radians(lat0)))
    cells = []
    lat = south + dlat / 2.0
    i = 0
    while lat < north:
        lon = west + dlon / 2.0
        j = 0
        while lon < east:
            ring = [
                [lon - dlon / 2, lat - dlat / 2],
                [lon + dlon / 2, lat - dlat / 2],
                [lon + dlon / 2, lat + dlat / 2],
                [lon - dlon / 2, lat + dlat / 2],
                [lon - dlon / 2, lat - dlat / 2],
            ]
            cells.append({"id": f"maille_{i}_{j}", "lon": lon, "lat": lat, "polygon": [ring]})
            lon += dlon
            j += 1
        lat += dlat
        i += 1
    return cells


def ring_centroid(ring):
    xs = [c[0] for c in ring]
    ys = [c[1] for c in ring]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def feature_point(geom):
    t = geom["type"]
    c = geom["coordinates"]
    if t == "Point":
        return c[0], c[1]
    if t == "Polygon":
        return ring_centroid(c[0])
    if t == "MultiPolygon":
        return ring_centroid(c[0][0])
    raise ValueError(f"type de géométrie non géré: {t}")
