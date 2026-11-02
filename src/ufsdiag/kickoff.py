import json


def build_kickoff(kickoff_path, project_path):
    with open(kickoff_path, encoding="utf-8") as f:
        template = json.load(f)
    with open(project_path, encoding="utf-8") as f:
        project = json.load(f)
    reponses = project.get("reponses", {})
    blocs = []
    for b in template["blocs"]:
        reps = reponses.get(b["id"], [])
        items = []
        for i, q in enumerate(b["questions"]):
            items.append({"question": q, "reponse": reps[i] if i < len(reps) else ""})
        blocs.append({"id": b["id"], "titre": b["titre"], "items": items})
    return {"nom_projet": project.get("nom_projet", ""), "commande": project.get("commande", ""), "blocs": blocs}
