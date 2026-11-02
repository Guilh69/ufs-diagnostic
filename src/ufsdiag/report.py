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
    ("Points d'eau potable (bornes-fontaines)", "Métropole de Lyon via data.gouv.fr, WFS metropole-de-lyon:adr_voie_lieu.adrbornefontaine_latest", "ODbL (OSM + communes)"),
    ("Producteurs locaux / alimentation bio", "DataGrandLyon, WFS metropole-de-lyon:eco_economie.ecomangerlocal_latest", "Licence Ouverte 2.0"),
    ("Parcs et jardins", "Ville de Villeurbanne via DataGrandLyon, WFS ville-de-villeurbanne:villeurbanne.parcjardin", "Licence Ouverte 2.0"),
    ("Pharmacies (accès aux soins)", "magOSM / data.gouv.fr, WFS magosm:pharmacies_point (extrait OSM quotidien)", "ODbL"),
    ("Réseau routier (isochrones)", "DataGrandLyon, WFS pvo_patrimoine_voirie.pvotronconwebcriter (tronçons CRITER, longueur en m)", "Licence Ouverte 2.0"),
    ("Commerces bio (NAF 4729Z)", "Base Sirene géolocalisée Métropole de Lyon, filtre activitenaf='4729Z'", "Licence Ouverte 2.0 - 0 objet géocodé dans le périmètre test, catégorie non retenue"),
]


def esc(s):
    return html.escape(str(s))


def render_kickoff_html(kickoff):
    blocs = []
    for b in kickoff["blocs"]:
        items = "\n".join(
            f"<tr><td>{esc(it['question'])}</td><td>{esc(it['reponse']) if it['reponse'] else '<em>à compléter</em>'}</td></tr>"
            for it in b["items"]
        )
        blocs.append(f"<h3>{esc(b['titre'])}</h3><table><tr><th>Question de cadrage</th><th>Réponse du projet</th></tr>{items}</table>")
    return f"""
<h2>0. Fiche de démarrage du projet</h2>
<p><strong>{esc(kickoff['nom_projet'])}</strong> — {esc(kickoff['commande'])}<br>
<small>Avant le livrable, le projet répond à ces questions de cadrage (modèle dans <code>config/kickoff.json</code>, réponses dans <code>config/project_buers.json</code>).</small></p>
{''.join(blocs)}
"""


def render_eqis_html(eqis, scenario):
    if not eqis:
        return ""
    ref = eqis["references"]
    res_rows = ""
    for label, r in eqis["resultats"].items():
        res_rows += (f"<tr><td>{r['polluant']}</td><td>{label}</td><td>{r['concentration_ugm3']} µg/m³</td>"
                     f"<td>{r['paf']*100:.2f} %</td><td><strong>{r['deces_attribuables_an']}</strong></td></tr>")
    st_rows = "".join(
        f"<tr><td>{s['nom_station']}</td><td>{s['nom_com']}</td><td>{s['annee']}</td>"
        f"<td>{s['valeur']} µg/m³</td><td>{s['typologie']}/{s['influence']}</td><td>{s['dist_m']} m</td></tr>"
        for s in eqis["stations_pm25"] + eqis.get("stations_no2", [])
    )
    sante_html = ""
    so = eqis.get("sante_odisse") or {}
    if so.get("records"):
        r0 = so["records"][0]
        sante_html = (f"<p>Indicateur santé croisé (Odissé/SPF, département {so.get('dep')} {r0.get('libgeo')}, {r0.get('annees')}) : "
                      f"mortalité infantile <strong>{r0.get('tx1000_mortalite_infantile')} ‰</strong> naissances vivantes. "
                      f"Source : <a href=\"https://odisse.santepubliquefrance.fr\">Odissé</a> ({so.get('dataset')}).</p>")
    sc_html = ""
    if eqis.get("scenario_oms"):
        s = eqis["scenario_oms"]
        sc_html += f"<li>Atteindre la ligne directrice OMS (5 µg/m³) : <strong>{s['deces_evites_an']} décès/an évités</strong> à {eqis['commune']}.</li>"
    if scenario:
        sc_html += (f"<li>{esc(scenario['libelle'])} : <strong>{scenario['deces_evites_an']} décès/an évités</strong> "
                    f"(population cible {scenario['population_cible']}, {esc(scenario['note'])}).</li>")
    return f"""
<h2>6. Évaluation quantitative (EQIS multi-polluants PM2,5 / NO2) et scénarios</h2>
<p>Commune : <strong>{esc(eqis['commune'])}</strong> ({eqis['code_insee']}) — population {eqis['population']:,} hab (geo.api.gouv.fr/INSEE).
Méthode EQIS OMS/SPF (guide EQIS-PA 2019) : décès attribuables = D × (1 − e<sup>−β(C−C<sub>ref</sub>)</sup>), β = ln(RR)/10 ;
RR PM2,5 = {eqis['rr']['PM2.5']}/10 µg/m³ (C<sub>ref</sub> = {eqis['contrefactuels']['PM2.5']} µg/m³), RR NO2 = {eqis['rr']['NO2']}/10 µg/m³ (C<sub>ref</sub> = {eqis['contrefactuels']['NO2']} µg/m³, OMS 2021) ;
taux de mortalité brut {eqis['taux_mortalite_brut']*1000:.1f} ‰ (référence nationale INSEE). En production : AirQ+ (OMS).</p>
<table><tr><th>Polluant</th><th>Source de concentration</th><th>C (µg/m³)</th><th>PAF</th><th>Décès attribuables/an</th></tr>
{res_rows}
</table>
{sante_html}
<p>Indice communal air-santé modélisé (Atmo AURA 2016-2018) : PM2,5 = <strong>{eqis['indice_communal_pm25']} µg/m³</strong>.
Mesures 2024 des stations proches (moyenne {eqis['moyenne_stations_pm25']} µg/m³) :</p>
<table><tr><th>Station</th><th>Commune</th><th>Année</th><th>Valeur</th><th>Type</th><th>Dist.</th></tr>
{st_rows}
</table>
<p>Seuils de référence PM2,5 : valeur limite UE 2024 = {ref['valeur_limite_ue_2024_pm25']} µg/m³, UE 2030 = {ref['valeur_limite_ue_2030_pm25']} µg/m³, OMS 2021 = {ref['ligne_directrice_oms_2021_pm25']} µg/m³. NO2 : UE 2030 = {ref['valeur_limite_ue_no2_2030']} µg/m³, OMS 2021 = {ref['ligne_directrice_oms_2021_no2']} µg/m³.
Référence nationale : {esc(ref['reference_spf_eqis_nationale'])}.
Bruit : cartes stratégiques Lden/Ln 2022 de la Métropole de Lyon (DataGrandLyon, plan bruit routier/ferroviaire/aérien) — à brancher en v0.6.
Îlots de chaleur : Diaclimap (Cerema) / Copernicus — à brancher en v0.6.</p>
<ul>{sc_html}</ul>
<p><small>EQIS simplifiée (AirQ+ OMS en production ; guide SPF 2019). Données agrégées uniquement — jamais de données individuelles (RGPD).</small></p>
"""


def render_zone_html(perimeter, zone_info, point_info, cats):
    if not zone_info and not point_info:
        return ""
    bbox = perimeter["bbox"]
    zone_html = ""
    if zone_info:
        rows = ""
        for cat in cats:
            d = zone_info["categories"].get(cat["id"])
            if d:
                dist = ""
                if d.get("dist_moyenne_reseau_m"):
                    dist = f"~{d['dist_moyenne_reseau_m']} m en moyenne (réseau), médiane {d['dist_mediane_reseau_m']} m ; {d.get('pct_mailles_zone_a_le_radius')}% des mailles à ≤{perimeter['walk_radius_m']} m"
                rows += (f"<tr><td>{esc(cat['label'])}</td><td><strong>{d['nb_dans_zone']}</strong></td>"
                         f"<td>{d['densite_par_km2']}/km²</td><td>{d.get('pour_10000_hab') or '—'}/10 000 hab</td><td>{dist or '—'}</td></tr>")
        pop = f"{zone_info['population_estimee']:,} hab ({esc(zone_info.get('population_note',''))})" if zone_info.get("population_estimee") else "non estimée"
        zone_html = f"""
<p><strong>Zone d'étude :</strong> {esc(zone_info.get('nom') or '—')} — {zone_info['area_km2']} km² ({zone_info['nb_mailles']} mailles de {perimeter['grid_cell_m']} m), population {pop}.<br>
<small>Source : {esc(zone_info.get('source') or '')}. Les indicateurs ci-dessous sont calculés DANS cette zone (effectifs et densités), pas à partir de l'extérieur.</small></p>
<table><tr><th>Catégorie</th><th>Nb dans la zone</th><th>Densité</th><th>Pour 10 000 hab</th><th>Distance moyenne au plus proche (réseau)</th></tr>
{rows}
</table>"""
    point_html = ""
    if point_info:
        rows = ""
        for cat in cats:
            d = point_info.get(cat["id"])
            if d:
                net = f"{d.get('min_dist_reseau_m')} m (réseau)" if d.get("min_dist_reseau_m") is not None else "—"
                rows += (f"<tr><td>{esc(cat['label'])}</td><td>{d['min_dist_vol_m']} m</td><td>{net}</td>"
                         f"<td>{esc(d.get('plus_proche') or '')}</td></tr>")
        point_html = f"""
<p><strong>Point d'ancrage</strong> (mise en situation d'une personne) : {esc(point_info.get('_adresse',''))}
— coordonnées {point_info.get('_lon')}, {point_info.get('_lat')} (géocodage Photon/BAN, Métropole de Lyon).</p>
<table><tr><th>Catégorie</th><th>Distance à vol d'oiseau</th><th>Distance par le réseau</th><th>Équipement le plus proche</th></tr>
{rows}
</table>"""
    return f"""
<h2>1. Où se trouve-t-on ? Périmètre et zone d'étude</h2>
<p>{esc(perimeter.get('description', ''))}<br>
Bbox WGS84 : sud {bbox['south']}, ouest {bbox['west']}, nord {bbox['north']}, est {bbox['east']} — {len(zone_info['categories']) and '' or ''}maillage de {perimeter['grid_cell_m']} m.</p>
{zone_html}
{point_html}
"""


def render_report(perimeter, cells, summary, checklist, cats, kickoff=None, eqis=None, scenario=None, zone_info=None, point_info=None, bruit_info=None, bruit_reel=None, out_map="map.html"):
    n_cells = len(cells)
    bbox = perimeter["bbox"]
    radius = perimeter["walk_radius_m"]
    net = perimeter.get("network", {})
    iso_m = net.get("isochrone_m")

    sum_rows = []
    for cat in cats:
        s = summary.get(cat["id"])
        if s:
            extra = ""
            if "pct_cells_reseau" in s:
                extra = f"<br>Réseau : {s['pct_cells_reseau']}% des mailles à ≤{radius} m, médiane {s['median_min_dist_reseau_m']} m"
            sum_rows.append(
                f"<tr><td>{esc(cat['label'])}</td><td>{s['nb_pois']}</td><td>{s['cells_within_radius']} / {n_cells}</td>"
                f"<td>{s['pct_cells']}%</td><td>{s['median_min_dist_m']} m{extra}</td></tr>"
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

    kickoff_html = render_kickoff_html(kickoff) if kickoff else ""
    eqis_html = render_eqis_html(eqis, scenario) if eqis else ""
    zone_html = render_zone_html(perimeter, zone_info, point_info, cats)
    if zone_info and zone_info.get("pct_mailles_avec_espace_vert_300m") is not None:
        zone_html += (f"<p><strong>Proxy îlot de fraîcheur (ICU)</strong> : {zone_info['pct_mailles_avec_espace_vert_300m']}% des mailles de la zone "
                      f"ont un espace vert à ≤ 300 m à pied (réseau). <small>{esc(zone_info.get('icu_note',''))}</small></p>")
    if bruit_info:
        s = summary.get("exposition_bruit_routier")
        extra = ""
        if s and "pct_cells_reseau" in s:
            extra = f" ; par le réseau : {s['pct_cells_reseau']}% des mailles à ≤{radius} m, médiane {s['median_min_dist_reseau_m']} m"
        zone_html += (f"<p><strong>Exposition au bruit routier</strong> (proxy voies à trafic) : {bruit_info['nb_troncons_infotrafic']} voies recensées ; "
                      f"{s['pct_cells']}% des mailles à ≤{radius} m d'une voie à trafic à vol d'oiseau{extra}. "
                      f"<small>{esc(bruit_info['note'])}</small></p>")
    if bruit_reel:
        pa = bruit_reel.get("point_ancrage") or {}
        zone_html += (f"<p><strong>Bruit routier Lden 2022 (mesuré/modélisé, dB(A))</strong> : sur {bruit_reel['nb_avec_valeur']} points de la zone, "
                      f"Lden moyen <strong>{bruit_reel['lden_moyen']} dB(A)</strong>, max {bruit_reel['lden_max']} dB(A) ; "
                      f"{bruit_reel['pct_points_depassement_ue_68']}% des points > 68 dB(A) (valeur limite UE), "
                      f"{bruit_reel['pct_points_depassement_oms_53']}% > 53 dB(A) (recommandation OMS 2018). "
                      f"Au point d'ancrage ({esc(pa.get('adresse') or '')}) : <strong>{pa.get('lden_dba')} dB(A)</strong>. "
                      f"<small>Source : {esc(bruit_reel['source'])}.</small></p>")
    iso_note = (f"Isochrone piéton ~{iso_m} m calculée sur le réseau routier ({perimeter.get('network',{}).get('nb_troncons','?')} tronçons) "
                f"et affichée sur la carte (<code>isochrone.geojson</code>).") if iso_m else ""

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Diagnostic UFS — {esc(perimeter['name'])}</title>
<style>
 body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 2rem auto; max-width: 1100px; color: #1a1a1a; line-height: 1.5; }}
 h1 {{ color: #0b5d3b; border-bottom: 3px solid #0b5d3b; padding-bottom: .3rem; }}
 h2 {{ color: #0b5d3b; margin-top: 2rem; }}
 h3 {{ color: #14724c; margin-top: 1.4rem; }}
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
<p><span class="badge">PROTOTYPE v0.2</span> <strong>{esc(perimeter['name'])}</strong> — généré le {date.today().isoformat()} par <code>ufs-diagnostic</code> (logiciel libre, licence EUPL-1.2).</p>

{kickoff_html}

<div class="warn"><strong>Limites du prototype :</strong> maillage régulier de {perimeter['grid_cell_m']} m ; distances à vol d'oiseau ET par le réseau routier (Dijkstra sur tronçons CRITER) ; isochrone = tronçons atteignables à pied en ~{iso_m} m. Les données OSM/collectivités sont collaboratives : vérifier sur le terrain (clef 2 ISadOrA).</div>

{zone_html}
<p>Soit {n_cells} mailles de {perimeter['grid_cell_m']} m au total. Score moyen d'accès aux équipements de santé/bien-être (vol d'oiseau) : <strong>{mean_score}</strong> / 1.</p>

<h2>2. Données mobilisées et sources (open data souveraines)</h2>
<table><tr><th>Donnée</th><th>Source (WFS / portail)</th><th>Licence</th></tr>
{src_rows}
</table>

<h2>3. Indicateurs de proximité par maille (rayon {radius} m ≈ 10 min à pied)</h2>
<table><tr><th>Catégorie</th><th>Nb objets</th><th>Mailles desservies</th><th>% mailles</th><th>Dist. médiane au plus proche (vol d'oiseau + réseau)</th></tr>
{summary_table}
</table>
<p>{iso_note}</p>
<p>Détail par maille : <code>indicators.geojson</code> (score d'accès par catégorie, distances vol d'oiseau et réseau).</p>

<h2>4. Carte</h2>
<iframe src="{out_map}"></iframe>

<h2>5. Checklist ISadOrA — 15 clefs opérationnelles</h2>
<table><tr><th>Clef</th><th>Objectif</th><th>Statut</th><th>Éléments chiffrés disponibles</th></tr>
{checklist_table}
</table>

{eqis_html}
<h2>7. Pistes EQIS avancées à brancher</h2>
<ul>
<li>Qualité de l'air : EQIS-PA selon le guide Santé publique France avec <a href="https://www.who.int/europe/fr/tools-and-toolkits/airq---software-tool-for-health-risk-assessment-of-air-pollution">AirQ+ (OMS)</a> (PM2,5, NO2, O3) sur le périmètre.</li>
<li>Mobilités actives : <a href="https://www.who.int/europe/tools-and-toolkits/health-economic-assessment-tool-for-walking-and-cycling">HEAT (OMS)</a> pour chiffrer les bénéfices sanitaires de la marche/du vélo.</li>
<li>Scénarios : ITHIM / UTOPHIA (ISGlobal) pour comparer des variantes d'aménagement.</li>
<li>Données santé : <a href="https://geodes.santepubliquefrance.fr/">Géodes (SPF)</a>, <a href="https://odisse.santepubliquefrance.fr/pages/accueil/">Odissé</a>, ARS AURA (DatARA), INSEE Filosofi (IRIS).</li>
</ul>

<h2>8. Bibliographie et référentiels</h2>
<ul>
{biblio_items}
</ul>

<footer>ufs-diagnostic v0.2 — prototype open source (EUPL-1.2). Données : voir section 2 (ODbL / Licence Ouverte). Ce rapport est un appui au diagnostic (clef 2 ISadOrA), pas un avis sanitaire réglementaire (EIS ARS).</footer>
</body>
</html>
"""
