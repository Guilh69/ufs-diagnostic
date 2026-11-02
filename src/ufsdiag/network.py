import heapq
import math

from .geo import haversine_m

CLUSTER_M = 18.0  # deux extrémités à moins de 12 m sont fusionnées (carrefours)


def _node_key(lon, lat):
    return (round(lon, 6), round(lat, 6))


class _UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def _cluster_nodes(nodes, cell_m=CLUSTER_M):
    """Regroupe les nœuds proches (carrefours où les tronçons ne se touchent pas exactement)."""
    uf = _UnionFind()
    grid = {}
    for n in nodes:
        lon, lat = n
        gx = int(lon * 111320.0 / cell_m)
        gy = int(lat * 111320.0 / cell_m)
        grid.setdefault((gx, gy), []).append(n)
    done = set()
    for (gx, gy), ns in grid.items():
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                others = grid.get((gx + dx, gy + dy), [])
                for i, a in enumerate(ns):
                    for b in others:
                        pair = (a, b) if a < b else (b, a)
                        if pair in done:
                            continue
                        done.add(pair)
                        if haversine_m(a[0], a[1], b[0], b[1]) <= cell_m:
                            uf.union(a, b)
    return {n: uf.find(n) for n in nodes}


def build_graph(features):
    """Graphe non orienté à partir de LineStrings, avec clustering des carrefours. Poids = longueur (m)."""
    raw_edges = []
    nodes = set()
    for ft in features:
        coords = ft["geometry"]["coordinates"]
        props = ft.get("properties", {}) or {}
        declared = props.get("longueur")
        for a, b in zip(coords[:-1], coords[1:]):
            na, nb = _node_key(*a), _node_key(*b)
            if na == nb:
                continue
            w = float(declared) if declared else 0
            w = max(w, haversine_m(a[0], a[1], b[0], b[1]))
            nodes.add(na)
            nodes.add(nb)
            raw_edges.append((na, nb, w, a, b, props.get("libelle", "")))
    remap = _cluster_nodes(nodes)
    adj = {}
    edges = []
    for na, nb, w, a, b, libelle in raw_edges:
        ra, rb = remap[na], remap[nb]
        if ra == rb:
            continue
        adj.setdefault(ra, []).append((rb, w))
        adj.setdefault(rb, []).append((ra, w))
        edges.append({"a": a, "b": b, "na": ra, "nb": rb, "w": w, "libelle": libelle})
    return adj, edges


def snap_to_graph(adj, edges, lon, lat):
    """Projette un point sur l'arête la plus proche. Retourne (node_a, node_b, dist_a, dist_b, proj, offset)."""
    best = None
    for e in edges:
        ax, ay = e["a"]
        bx, by = e["b"]
        dx, dy = bx - ax, by - ay
        if dx == 0 and dy == 0:
            continue
        t = ((lon - ax) * dx + (lat - ay) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        px, py = ax + t * dx, ay + t * dy
        d = haversine_m(lon, lat, px, py)
        if best is None or d < best[0]:
            best = (d, e, t, (px, py))
    d, e, t, proj = best
    la = haversine_m(e["a"][0], e["a"][1], proj[0], proj[1])
    lb = haversine_m(proj[0], proj[1], e["b"][0], e["b"][1])
    return e["na"], e["nb"], la, lb, proj, d


def dijkstra_multi_source(adj, sources):
    dist = {}
    pq = []
    for n, c in sources.items():
        if c < dist.get(n, math.inf):
            dist[n] = c
            heapq.heappush(pq, (c, n))
    while pq:
        d, n = heapq.heappop(pq)
        if d > dist.get(n, math.inf):
            continue
        for m, w in adj.get(n, []):
            nd = d + w
            if nd < dist.get(m, math.inf):
                dist[m] = nd
                heapq.heappush(pq, (nd, m))
    return dist


def network_distances_to_pois(adj, edges, cells, pois):
    """Distance réseau (m) de chaque maille au POI le plus proche (multi-source Dijkstra)."""
    sources = {}
    for p in pois:
        na, nb, la, lb, proj, off = snap_to_graph(adj, edges, p["lon"], p["lat"])
        sources[na] = min(sources.get(na, math.inf), la + off)
        sources[nb] = min(sources.get(nb, math.inf), lb + off)
    dist = dijkstra_multi_source(adj, sources)
    out = []
    for c in cells:
        na, nb, la, lb, proj, off = snap_to_graph(adj, edges, c["lon"], c["lat"])
        da = dist.get(na, math.inf)
        db = dist.get(nb, math.inf)
        best = math.inf
        if math.isfinite(da):
            best = da + la + off
        if math.isfinite(db):
            best = min(best, db + lb + off)
        out.append(best if math.isfinite(best) else None)
    return out


def isochrone_edges(adj, edges, center, radius_m):
    """Arêtes dont au moins une extrémité est à moins de radius_m du centre en réseau."""
    na, nb, la, lb, proj, off = snap_to_graph(adj, edges, center[0], center[1])
    dist = dijkstra_multi_source(adj, {na: la + off, nb: lb + off})
    keep = []
    for e in edges:
        da, db = dist.get(e["na"], math.inf), dist.get(e["nb"], math.inf)
        if min(da, db) <= radius_m:
            keep.append(e)
    return keep, dist


def isochrone_geojson(keep_edges, radius_m):
    feats = []
    for e in keep_edges:
        feats.append({
            "type": "Feature",
            "properties": {"libelle": e["libelle"], "longueur_m": round(e["w"]), "isochrone_m": radius_m},
            "geometry": {"type": "LineString", "coordinates": [list(e["a"]), list(e["b"])]},
        })
    return {"type": "FeatureCollection",
            "name": f"Isochrone piéton ~{radius_m} m par le réseau routier (tronçons atteignables)",
            "features": feats}
