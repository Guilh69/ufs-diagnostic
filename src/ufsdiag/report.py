import html
from datetime import date

BIBLIO = [
    ("Guide ISadOrA (EHESP / a-urba, 2020) - 15 clefs opérationnelles", "https://www.aurba.org/productions/isadora-un-outil-daide-a-lintegration-de-la-sante-dans-les-operations-damenagement/"),
    ("Guide ISadOrA, partie 1 (PDF officiel)", "https://www.ecoquartiers.logement.gouv.fr/assets/articles/documents/guide-isadora-partie-1.pdf"),
    ("Guide ISadOrA, partie 2 (PDF officiel)", "https://www.ecoquartiers.logement.gouv.fr/assets/articles/documents/guide-isadora-partie-2.pdf"),
    ("EHESP/DGS, Agir pour un urbanisme favorable à la santé (2014)", "https://www.ehesp.fr/wp-content/uploads/2014/09/guide-agir-urbanisme-sante-2014-v2-opt.pdf"),
    ("ADEME, page Urbanisme favorable à la santé (UFS)", "https://agirpourlatransition.ademe.fr/collectivites/conseils/urbanisme/ufs"),
    ("ADEME / CGDD, Expé URBA SanTé (8 territoires, 2024-2025)", "https://agirpourlatransition.ademe.fr/collectivites/aides-financieres/catalogue-rex/retours-experience-urbanisme-favorable-sante"),
    ("Cerema, fiches Nature en ville (fiche 3 : santé)", "https://www.cerema.fr/fr/centre-ressources/boutique/nature-ville-serie-fiches"),
    ("Cerema, îlots de chaleur urbains / Diaclimap", "https://www.cerema.fr/fr/actualites/ilots-chaleur-agir-territoires-adapter-villes-au-changement"),
    ("HCSP, intégration de la santé dans les documents de planification (2018)", "https://www.hcsp.fr/explore.cgi/avisrapportsdomaine?clefr=638"),
    ("Santé publique France, guide EQIS pollution de l'air (2019)", "https://www.santepubliquefrance.fr/content/download/233580/2517739"),
    ("OMS/Europe, AirQ+ (logiciel libre de quantification)", "https://www.who.int/europe/fr/tools-and-toolkits/airq---software-tool-for-health-risk-assessment-of-air-pollution"),
    ("OMS/Europe, HEAT marche et vélo (mise à jour 2024)", "https://www.who.int/europe/publications/i/item/9789289058377"),
    ("ONU-Habitat & OMS, Integrating health in urban and territorial planning (2020)", "https://unhabitat.org/sites/default/files/2022/03/21235_french_integrating_health_in_urban_and_territorial_planning_2_1.pdf"),
    ("Barton & Grant, A health map for the local human habitat (2006)", "https://journals.sagepub.com/doi/10.1177/1466424006070466"),
    ("Revue Pollution Atmosphérique, EIS des quartiers des Buers (Villeurbanne) et Parc Zénith (Lyon 3)", "https://www.peren-revues.fr/pollutionatmospherique/6681"),
    ("Géodes, observatoire cartographique SPF (>300 indicateurs)", "https://geodes.santepubliquefrance.fr/"),
    ("data.gouv.fr, Bornes fontaine de la Métropole de Lyon", "https://www.data.gouv.fr/datasets/bornes-fontaine-de-la-metropole-de-lyon"),
    ("DataGrandLyon, Producteurs locaux géolocalisés", "https://www.data.gouv.fr/datasets/producteurs-locaux-geolocalises-de-la-metropole-de-lyon"),
    ("DataGrandLyon, Base Sirene de la Métropole de Lyon", "https://www.data.gouv.fr/datasets/base-sirene-de-la-metropole-de-lyon"),
    ("data.gouv.fr / magOSM, Localisation des pharmacies dans OSM (extrait quotidien)", "https://www.data.gouv.fr/datasets/localisation-des-pharmacies-dans-openstreetmap/"),
]

DATA_SOURCES = [
    ("Points d'eau potable (bornes-fontaines)", "Métropole de Lyon via data.gouv.fr, couche WFS metropole-de-lyon:adr_voie_lieu.adrbornefontaine_latest", "ODbL (OSM + communes)"),
    ("Producteurs locaux / alimentation bio", "DataGrandLyon, couche WFS metropole-de-lyon:eco_economie.ecomangerlocal_latest", "Licence Ouverte 2.0"),
    ("Parcs et jardins", "Ville de Villeurbanne via DataGrandLyon, couche WFS ville-de-villeurbanne:villeurbanne.parcjardin", "Licence Ouverte 2.0"),
    ("Commerces bio (NAF 4729Z)", "Base Sirene géolocalisée Métropole de Lyon, couche WFS metropole-de-lyon:insee.sirene (filtre activitenaf='4729Z')", "Licence Ouverte 2.0 - non retenu ici (0 objet géocodé dans le périmètre test)"),
]


def esc(s):
    return html.escape(str(s))


def render_report(perimeter, cells, summary, checklist, cats, out_map="map.html"):
    n_cells = len(cells)
    bbox = perimeter["bbox"]
    radius = perimeter["walk_radius_m"]

    sum_rows = []
    for cat in cats:
        s = summary.get(cat["id"])
        if s:
            sum_rows.append(
                f"<tr><td>{esc(cat['label'])}</td><td>{s['nb_pois']}</td><td>{s['cells_within_radius']} / {n_cells}</td>"
                f"<td>{s['pct_cells']}%</td><td>{s['median_min_dist_m']} m</td></tr>"
            )
        else:
            sum_rows.append(f"<tr><td>{esc(cat['label'])}</td><td colspan='4'><em>donnée non disponible dans le périmètre</em></td></tr>")
    summary_table = "\n".join(sum_rows)

    src_rows = "\n".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in DATA_SOURCES)
    biblio_items = "\n".join(f'<li><a href="{esc(u)}">{esc(t)}</a></li>' for t, u in BIBLIO)

    key_rows = []
    for k in checklist:
        ev = "<br>".join(f"• {esc(e)}" for e in k["evidence"]) or "—"
        key_rows.append(
            f"<tr><td>{k['key']}</td><td><strong>{esc(k['title'])}</strong><br><small>{esc(k['desc'])}</small></td>"
            f"<td>{esc(k['status'])}</td><td><small>{ev}</small></td></tr>"
        )
    checklist_table = "\n".join(key_rows)

    scores = [c["score"] for c in cells if c["score"] is not None]
    mean_score = round(sum(scores) / len(scores), 3) if scores else None

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Diagnostic UFS — {esc(perimeter['name'])}</title>
<style>
 body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 2rem auto; max-width: 1100px; color: #1a1a1a; line-height: 1.5; }}
 h1 {{ color: #0b5d3b; border-bottom: 3px solid #0b5d3b; padding-bottom: .3rem; }}
 h2 {{ color: #0b5d3b; margin-top: 2rem; }}
 table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
 th, td {{ border: 1px solid #ccc; padding: .45rem .6rem; text-align: left; vertical-align: top; font-size: .92rem; }}
 th {{ background: #e8f3ec; }}
 .badge {{ background: #0b5d3b; color: #fff; border-radius: 4px; padding: .1rem .5rem; font-size: .85rem; }}
 .warn {{ background: #fff8e1; border-left: 4px solid #f0a500; padding: .8rem 1rem; }}
 iframe {{ width: 100%; height: 520px; border: 1px solid #ccc; }}
 footer {{ margin-top: 3rem; font-size: .8rem; color: #666; border-top: 1px solid #ccc; padding-top: 1rem; }}
</style>
</head>
<body>
<h1>Diagnostic territorial — Urbanisme Favorable à la Santé</h1>
<p><span class="badge">PROTOTYPE</span> <strong>{esc(perimeter['name'])}</strong> — généré le {date.today().isoformat()} par <code>ufs-diagnostic</code> (logiciel libre, licence EUPL-1.2).</p>

<div class="warn"><strong>Limites du prototype :</strong> distances à vol d'oiseau (pas d'isochrones réseau — voir Valhalla/pgRouting en v2), maillage régulier de {perimeter['grid_cell_m']} m, rayon de marche de {radius} m (~10 min), parcs réduits à leur centroïde. Les données OSM/collectivités sont collaboratives : vérifier sur le terrain (clef 2 ISadOrA).</div>

<h2>1. Périmètre d'étude</h2>
<p>{esc(perimeter.get('description', ''))}<br>
Bbox WGS84 : sud {bbox['south']}, ouest {bbox['west']}, nord {bbox['north']}, est {bbox['east']} — soit {n_cells} mailles de {perimeter['grid_cell_m']} m.
Score moyen d'accès aux équipements de santé/bien-être : <strong>{mean_score}</strong> / 1.</p>

<h2>2. Données mobilisées et sources (open data souveraines)</h2>
<table><tr><th>Donnée</th><th>Source (WFS / portail)</th><th>Licence</th></tr>
{src_rows}
</table>

<h2>3. Indicateurs de proximité (rayon {radius} m)</h2>
<table><tr><th>Catégorie</th><th>Nb objets</th><th>Mailles desservies</th><th>% mailles</th><th>Dist. médiane au plus proche</th></tr>
{summary_table}
</table>
<p>Détail par maille : <code>indicators.geojson</code> (score d'accès par catégorie, 0–1).</p>

<h2>4. Carte</h2>
<iframe src="{out_map}"></iframe>

<h2>5. Checklist ISadOrA — 15 clefs opérationnelles</h2>
<table><tr><th>Clef</th><th>Objectif</th><th>Statut</th><th>Éléments chiffrés disponibles</th></tr>
{checklist_table}
</table>

<h2>6. Pistes EQIS (évaluation quantitative) à brancher</h2>
<ul>
<li>Qualité de l'air : EQIS-PA selon le guide Santé publique France avec <a href="https://www.who.int/europe/fr/tools-and-toolkits/airq---software-tool-for-health-risk-assessment-of-air-pollution">AirQ+ (OMS)</a> (PM2,5, NO2, O3) sur le périmètre.</li>
<li>Mobilités actives : <a href="https://www.who.int/europe/tools-and-toolkits/health-economic-assessment-tool-for-walking-and-cycling">HEAT (OMS)</a> pour chiffrer les bénéfices sanitaires de la marche/du vélo.</li>
<li>Scénarios : ITHIM / UTOPHIA (ISGlobal) pour comparer des variantes d'aménagement.</li>
<li>Données santé : <a href="https://geodes.santepubliquefrance.fr/">Géodes (SPF)</a>, <a href="https://odisse.santepubliquefrance.fr/pages/accueil/">Odissé</a>, ARS AURA (DatARA), INSEE Filosofi (IRIS).</li>
</ul>

<h2>7. Bibliographie et référentiels</h2>
<ul>
{biblio_items}
</ul>

<footer>ufs-diagnostic v0.1 — prototype open source (EUPL-1.2). Données : voir section 2 (ODbL / Licence Ouverte). Ce rapport est un appui au diagnostic (clef 2 ISadOrA), pas un avis sanitaire réglementaire (EIS ARS).</footer>
</body>
</html>
"""
