import json
import math
import os

RR = {"PM2.5": 1.062, "NO2": 1.03}  # RR mortalité toutes causes par +10 µg/m³ (HRAPIE 2013 / OMS, repris par AirQ+ et guide SPF)
CREF = {"PM2.5": 5.0, "NO2": 10.0}   # contrefactuels = lignes directrices OMS 2021 (µg/m³, moyennes annuelles)


def load_air_sante(data_dir):
    path = os.path.join(data_dir, "air_sante_69266.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def eqis_mortalite(population, taux_mortalite, concentration, contrefactuel, rr_par_10):
    """Décès annuels attribuables (mortalité toutes causes), méthode EQIS OMS/SPF.

    PAF = 1 - exp(-beta*(C-Cref)), beta = ln(RR)/10 ; décès attribuables = D * PAF, D = pop x taux.
    """
    if concentration is None or concentration <= contrefactuel:
        return 0.0, 0.0
    beta = math.log(rr_par_10) / 10.0
    paf = 1.0 - math.exp(-beta * (concentration - contrefactuel))
    return population * taux_mortalite * paf, paf


def _mean_station(stations):
    vals = [s["valeur"] for s in stations if isinstance(s.get("valeur"), (int, float))]
    return round(sum(vals) / len(vals), 2) if vals else None


def compute_eqis_block(data_dir, eqis_cfg):
    air = load_air_sante(data_dir)
    if not air:
        return None
    commune = air.get("commune_geoapi", {})
    pop = commune.get("population")
    if not pop:
        return None
    taux = eqis_cfg["taux_mortalite_brut"]

    indice_pm25 = None
    for f in air.get("indice_pm25", []):
        indice_pm25 = f["attributes"].get("indicePM25")
    stations_pm25 = air.get("stations_pm25", [])
    stations_no2 = air.get("stations_no2", [])
    pm25_mean = _mean_station(stations_pm25)
    no2_fond = _mean_station([s for s in stations_no2 if s.get("influence") == "fond"])
    no2_trafic = _mean_station([s for s in stations_no2 if s.get("influence") == "trafic"])

    resultats = {}
    for label, c in [("PM2.5 - modèle communal Atmo AURA 2016-2018", indice_pm25),
                     ("PM2.5 - moyenne stations 2024", pm25_mean),
                     ("NO2 - stations fond 2024", no2_fond),
                     ("NO2 - stations trafic 2024", no2_trafic)]:
        if c:
            pol = "PM2.5" if "PM2.5" in label else "NO2"
            att, paf = eqis_mortalite(pop, taux, c, CREF[pol], RR[pol])
            resultats[label] = {"polluant": pol, "concentration_ugm3": c,
                                "deces_attribuables_an": round(att, 1), "paf": round(paf, 4)}

    scenario_oms = None
    if indice_pm25:
        att0, _ = eqis_mortalite(pop, taux, indice_pm25, CREF["PM2.5"], RR["PM2.5"])
        scenario_oms = {"cible_ugm3": CREF["PM2.5"], "deces_evites_an": round(att0, 1)}

    # indicateur santé Odissé (département 69)
    sante = None
    sp = os.path.join(data_dir, "sante_odisse_69.json")
    if os.path.exists(sp):
        with open(sp, encoding="utf-8") as f:
            sante = json.load(f)

    return {
        "commune": commune.get("nom"), "code_insee": commune.get("code"),
        "population": pop, "taux_mortalite_brut": taux,
        "rr": RR, "contrefactuels": CREF,
        "indice_communal_pm25": indice_pm25,
        "stations_pm25": stations_pm25, "stations_no2": stations_no2,
        "moyenne_stations_pm25": pm25_mean, "moyenne_no2_fond": no2_fond, "moyenne_no2_trafic": no2_trafic,
        "resultats": resultats,
        "scenario_oms": scenario_oms,
        "sante_odisse": sante,
        "references": {
            "valeur_limite_ue_2024_pm25": eqis_cfg.get("valeur_limite_ue_2024_pm25"),
            "valeur_limite_ue_2030_pm25": eqis_cfg.get("valeur_limite_ue_2030_pm25"),
            "ligne_directrice_oms_2021_pm25": eqis_cfg.get("ligne_directrice_oms_2021_pm25"),
            "valeur_limite_ue_no2_2030": 20,
            "ligne_directrice_oms_2021_no2": 10,
            "reference_spf_eqis_nationale": "48 000 décès prématurés/an attribuables aux PM2,5 en France (EQIS SPF 2016)",
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
