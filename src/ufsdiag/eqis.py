import json
import math
import os


def load_air_sante(data_dir):
    path = os.path.join(data_dir, "air_sante_69266.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def eqis_pm25_mortalite(population, taux_mortalite, concentration, contrefactuel, rr_par_10):
    """Décès annuels attribuables aux PM2.5 (mortalité toutes causes), méthode EQIS OMS/SPF.

    beta = ln(RR)/10 ; PAF = 1 - exp(-beta*(C-Cref)) ; décès attribuables = D * PAF.
    """
    if concentration is None or concentration <= contrefactuel:
        return 0.0, 0.0
    beta = math.log(rr_par_10) / 10.0
    paf = 1.0 - math.exp(-beta * (concentration - contrefactuel))
    deces_annuels = population * taux_mortalite
    return deces_annuels * paf, paf


def compute_eqis_block(data_dir, eqis_cfg):
    air = load_air_sante(data_dir)
    if not air:
        return None
    commune = air.get("commune_geoapi", {})
    pop = commune.get("population")
    if not pop:
        return None
    taux = eqis_cfg["taux_mortalite_brut"]
    rr = eqis_cfg["rr_pm25_par_10ugm3"]
    cref = eqis_cfg["contrefactuel_ugm3"]
    indice = None
    for f in air.get("indice_pm25", []):
        indice = f["attributes"].get("indicePM25")
    stations = air.get("stations_pm25", [])
    station_mean = None
    vals = [s["valeur"] for s in stations if isinstance(s.get("valeur"), (int, float))]
    if vals:
        station_mean = round(sum(vals) / len(vals), 2)
    c_modele = indice
    results = {}
    for label, c in [("modele_commune_2016_2018", c_modele), ("stations_2024_moyenne", station_mean)]:
        if c:
            att, paf = eqis_pm25_mortalite(pop, taux, c, cref, rr)
            results[label] = {"concentration_ugm3": c, "deces_attribuables_an": round(att, 1), "paf": round(paf, 4)}
    # scénario : atteindre la ligne directrice OMS
    if c_modele:
        att0, _ = eqis_pm25_mortalite(pop, taux, c_modele, cref, rr)
        scenario_oms = {"cible_ugm3": cref, "deces_evites_an": round(att0, 1),
                        "note": "si la commune atteignait 5 µg/m³ (OMS 2021), tous les décès attribuables au-dessus de ce seuil seraient évités"}
    else:
        scenario_oms = None
    return {
        "commune": commune.get("nom"), "code_insee": commune.get("code"),
        "population": pop, "taux_mortalite_brut": taux,
        "contrefactuel_ugm3": cref, "rr_pm25_par_10ugm3": rr,
        "indice_communal_pm25": c_modele,
        "stations_pm25": stations,
        "moyenne_stations_pm25": station_mean,
        "resultats": results,
        "scenario_oms": scenario_oms,
        "references": {
            "valeur_limite_ue_2024": eqis_cfg.get("valeur_limite_ue_2024_pm25"),
            "valeur_limite_ue_2030": eqis_cfg.get("valeur_limite_ue_2030_pm25"),
            "ligne_directrice_oms_2021": eqis_cfg.get("ligne_directrice_oms_2021_pm25"),
        },
    }


def compute_scenario_marche(data_dir, eqis_block, scenarios_cfg):
    sc = scenarios_cfg.get("scenario_marche")
    if not sc or not eqis_block:
        return None
    pop = eqis_block["population"]
    taux = eqis_block["taux_mortalite_brut"]
    part = sc["part_population_cible"]
    rr = sc["rr_mortalite_marche"]
    pop_cible = pop * part
    deces_base = pop_cible * taux
    evites = deces_base * (1.0 - rr)
    return {
        "libelle": sc["libelle"],
        "population_cible": round(pop_cible),
        "deces_base_an": round(deces_base, 1),
        "rr": rr,
        "deces_evites_an": round(evites, 1),
        "note": "HEAT-lite (hypothèses éditables dans config/scenarios.json) ; remplacer par HEAT officiel (OMS) en production",
    }
