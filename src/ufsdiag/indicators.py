from .geo import haversine_m


def compute_indicators(cells, pois_by_cat, radius_m):
    """Indicateurs à vol d'oiseau : nb de POI à <= radius_m, distance min, score d'accès 0-1."""
    for cell in cells:
        cell["indicators"] = {}
        scores = []
        for cat_id, pois in pois_by_cat.items():
            if not pois:
                continue
            dists = [haversine_m(cell["lon"], cell["lat"], p["lon"], p["lat"]) for p in pois]
            min_dist = min(dists)
            count = sum(1 for d in dists if d <= radius_m)
            access = 1.0 if count > 0 else max(0.0, 1.0 - min_dist / (2.0 * radius_m))
            cell["indicators"][cat_id] = {
                "count_within": count,
                "min_dist_m": round(min_dist),
                "access_score": round(access, 3),
            }
            scores.append(access)
        cell["score"] = round(sum(scores) / len(scores), 3) if scores else None
    return cells


def attach_network(cells, net_min_by_cat, radius_m):
    """Ajoute à chaque maille la distance au plus proche POI par le réseau (Dijkstra)."""
    for i, cell in enumerate(cells):
        for cat_id, dists in net_min_by_cat.items():
            if not dists or dists[i] is None or cat_id not in cell["indicators"]:
                continue
            cell["indicators"][cat_id]["min_dist_reseau_m"] = round(dists[i])
    return cells


def summarize(cells, pois_by_cat, radius_m, net_min_by_cat=None):
    summary = {}
    for cat_id, pois in pois_by_cat.items():
        if not pois:
            continue
        covered = sum(1 for c in cells if c["indicators"].get(cat_id, {}).get("count_within", 0) > 0)
        dists = sorted(c["indicators"][cat_id]["min_dist_m"] for c in cells if cat_id in c["indicators"])
        median = dists[len(dists) // 2] if dists else None
        s = {
            "nb_pois": len(pois),
            "cells_within_radius": covered,
            "pct_cells": round(100.0 * covered / len(cells), 1) if cells else 0.0,
            "median_min_dist_m": median,
            "radius_m": radius_m,
        }
        if net_min_by_cat and net_min_by_cat.get(cat_id):
            nds = [d for d in net_min_by_cat[cat_id] if d is not None]
            if nds:
                nds.sort()
                s["median_min_dist_reseau_m"] = round(nds[len(nds) // 2])
                s["cells_within_radius_reseau"] = sum(1 for d in nds if d <= radius_m)
                s["pct_cells_reseau"] = round(100.0 * s["cells_within_radius_reseau"] / len(cells), 1)
        summary[cat_id] = s
    return summary
