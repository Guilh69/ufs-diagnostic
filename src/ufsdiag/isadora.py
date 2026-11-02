import json


def build_checklist(keys_path, summary, cat_to_key):
    with open(keys_path, encoding="utf-8") as f:
        keys = json.load(f)["keys"]
    by_key = {}
    for cat_id, key_id in cat_to_key.items():
        by_key.setdefault(key_id, []).append(cat_id)
    out = []
    for k in keys:
        evidence = []
        for cat_id in by_key.get(k["id"], []):
            s = summary.get(cat_id)
            if s:
                txt = (f"{cat_id} : {s['nb_pois']} objets recensés, {s['pct_cells']}% des mailles à moins de "
                       f"{s['radius_m']} m à vol d'oiseau (médiane {s['median_min_dist_m']} m)")
                if "pct_cells_reseau" in s:
                    txt += (f" ; par le réseau : {s['pct_cells_reseau']}% à ≤{s['radius_m']} m "
                            f"(médiane {s['median_min_dist_reseau_m']} m)")
                evidence.append(txt)
        if evidence:
            pcts = [summary[c]["pct_cells"] for c in by_key[k["id"]] if c in summary]
            status = "À renforcer" if pcts and max(pcts) < 60 else "Données favorables disponibles"
        else:
            status = "À expertiser sur le terrain"
        out.append({
            "key": k["id"],
            "type": k["type"],
            "title": k["title"],
            "desc": k["desc"],
            "status": status,
            "evidence": evidence,
        })
    return out
