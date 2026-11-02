# ufs-diagnostic — prototype de diagnostic territorial « Urbanisme Favorable à la Santé » (v0.5)

Outil libre (EUPL-1.2) qui enchaîne, pour un périmètre donné (quartier, rue) :

0. **Fiche de démarrage du projet** — les questions de cadrage à se poser avant tout livrable
   (objectif, périmètre, données/acteurs, méthode/livrables, budget/compétences/cadre réglementaire/contraintes),
   avec réponses éditables dans `config/project_<cas>.json` ;
1. **Où se trouve-t-on : périmètre + zone définie** (ex. QPV Les Buers, polygone ANCT) avec indicateurs calculés DANS la zone
   (effectifs, densités /km² et /10 000 hab, distance moyenne au plus proche par le réseau) ; **point d'ancrage** (adresse géocodée)
   pour les distances d'une personne précise ;
2. **Données ouvertes souveraines** (WFS Métropole de Lyon / data.gouv.fr-magOSM) ;
3. **Géotraitements de proximité** : distance au plus proche à vol d'oiseau **et par le réseau routier**
   (graphe + Dijkstra, tronçons CRITER avec longueur en m), **isochrone piéton ~10 min** ;
4. **Checklist des 15 clefs ISadOrA** avec statut et preuves chiffrées ;
5. **EQIS-lite PM2,5** (méthode OMS/SPF, contrefactuel 5 µg/m³, RR 1,062/10 µg/m³) + **scénario HEAT-lite marche** ;
6. **Carte interactive** (Leaflet) + **rapport HTML templatisé** imprimable en PDF.

## Cas concret livré

Quartier des **Buers, Villeurbanne** (Métropole de Lyon) — quartier prioritaire avec une EIS documentée
([revue Pollution Atmosphérique](https://www.peren-revues.fr/pollutionatmospherique/6681)).

Données réelles (provenance + licence dans chaque fichier de `data/raw/buers/`) :

- Bornes-fontaines d'eau potable : WFS `metropole-de-lyon:adr_voie_lieu.adrbornefontaine_latest` (ODbL) ;
- Producteurs locaux / AMAP / épiceries (dont label AB) : `metropole-de-lyon:eco_economie.ecomangerlocal_latest` (LO) ;
- Parcs et jardins de Villeurbanne (surfaces, eau) : `ville-de-villeurbanne:villeurbanne.parcjardin` (LO) ;
- Pharmacies : extrait OSM quotidien magOSM via data.gouv.fr (ODbL) ;
- Réseau routier (tronçons CRITER, longueur en m) : `pvo_patrimoine_voirie.pvotronconwebcriter` (LO) ;
- Commerces bio NAF 4729Z : Sirene géolocalisée `metropole-de-lyon:insee.sirene` (LO) — 0 objet géocodé dans le périmètre, catégorie optionnelle.

## Lancer

```bash
python3 run_diagnostic.py --perimeter config/perimeter_buers.json \
  --indicators config/indicators.json --keys config/isadora_keys.json \
  --kickoff config/kickoff.json --project config/project_buers.json \
  --eqis config/eqis.json --scenarios config/scenarios.json \
  --data data/raw/buers --out outputs/buers
```

Aucune dépendance (Python 3 stdlib). Pour (re)télécharger les données ouvertes :
`python3 tools/fetch_data.py buers`.

Sorties dans `outputs/buers/` : `report.html`, `map.html`, `indicators.geojson`, `pois.geojson`,
`isochrone.geojson`, `summary.json`, `checklist.json`, `kickoff.json`.

**Voir le rapport en ligne (jolie page)** : activer GitHub Pages sur ce dépôt
(Settings → Pages → Deploy from a branch → branche de travail, dossier `/ (root)`),
puis ouvrir `https://<ton-pseudo>.github.io/ufs-diagnostic/outputs/buers/report.html`.

## Résultats v0.2 (Buers, 130 mailles, rayon 800 m ≈ 10 min à pied)

| Catégorie | Objets | Vol d'oiseau ≤800 m | Réseau ≤800 m (médiane réseau) |
|---|---|---|---|
| Espaces verts (clef 12) | 26 | 100 % | **85,4 %** (457 m) |
| Pharmacies (clef 7) | 20 | 100 % | **70,0 %** (567 m) |
| Alimentation locale/bio (clef 7) | 9 | 100 % | 32,3 % (1372 m) |
| Eau potable (clef 11) | 6 | 94,6 % | 30,8 % (1649 m) |

Lecture : le quartier est très bien doté en espaces verts et pharmacies accessibles à pied par le réseau ;
l'alimentation bio et les fontaines sont plus éloignées en distance réelle de marche — piste d'action concrète.

## Résultats v0.4 — zone QPV « Les Buers » (0,156 km², ~1 700 hab estimés)

| Catégorie | Nb dans la zone | Densité | Distance moyenne au plus proche (réseau) |
|---|---|---|---|
| Alimentation locale/bio | 1 | 6,4/km² | ~660 m |
| Espaces verts | 0 (les plus proches sont en lisière) | — | ~390 m |
| Eau potable | 0 | — | ~3,8 km (réseau voies principales) |
| Pharmacies | 0 | — | ~515 m |

Point d'ancrage « 130 rue Anatole France » : alimentation bio à 0 m (vol d'oiseau) / 147 m réseau ; pharmacie la plus proche à 170 m / 401 m (Pharmacie Daviet) ; espace vert à 25 m / 540 m.

Lecture : dans le QPV strict, les équipements sont en lisière — la distance moyenne réseau est le bon indicateur pour dire « on trouve X à ~Y m en moyenne dans cette zone ».

## Résultats v0.5 — EQIS multi-polluants (Villeurbanne, 163 684 hab)

| Polluant | Source | C (µg/m³) | Décès attribuables/an |
|---|---|---|---|
| PM2,5 | modèle communal Atmo AURA 2016-2018 | 14,8 | 86,2 |
| PM2,5 | moyenne stations 2024 | 8,2 | 29,0 |
| NO2 | stations fond 2024 | 15,9 | 26,2 |
| NO2 | stations trafic 2024 (dont Lyon Périphérique, Villeurbanne : 39,5) | 32,6 | 97,2 |

Croisement santé : mortalité infantile Rhône (69) = 3,643 ‰ (Odissé/SPF 2020-2024). Export **rapport.docx** (stdlib, sans dépendance).
Bruit (cartes Lden/Ln 2022 Métropole de Lyon) et îlots de chaleur (Diaclimap/Copernicus) : sources identifiées, à brancher en v0.6.

## Résultats v0.3 — EQIS air (Villeurbanne, 163 684 hab)

| Source PM2,5 | C (µg/m³) | Décès attribuables/an |
|---|---|---|
| Modélisation communale Atmo AURA 2016-2018 (indice air-santé) | 14,8 | **86,2** |
| Mesures 2024, moyenne stations proches (Lyon Centre 9,5 ; Lyon Gerland 10,0 ; Vaulx-en-Velin 5,2) | 8,2 | **29,0** |

Scénarios : atteindre la ligne directrice OMS 5 µg/m³ → ~86 décès/an évités (selon modèle communal) ; +30 min de marche/jour pour les 18-64 ans → ~83 décès/an évités (HEAT-lite, hypothèses éditables).
Seuils de référence : UE 2024 = 20, UE 2030 = 10, OMS 2021 = 5 µg/m³.

## Limites connues

- Isochrone = tronçons atteignables (approximation), pas de polygone lissé ; vitesse piéton fixe 4,8 km/h.
- Quelques tronçons isolés (bretelles A42/N383) restent hors graphe ; clustering des carrefours à 18 m.
- EQIS (AirQ+, HEAT, ITHIM) listés dans le rapport mais non branchés ; données santé agrégées (Géodes/ARS) à croiser.
- Données collaboratives (OSM) : recouper sur le terrain (clef 2 ISadOrA).

## Feuille de route

- v0.6 : AirQ+ (OMS) en moteur EQIS complet, bruit Lden/Ln branché, ICU Diaclimap, plus d'indicateurs Odissé/Géodes, gabarits personnalisables, version web (GeoNode/MapStore + plugin QGIS).
- v1.0 : version web (GeoNode/PostGIS + MapStore, hébergement souverain UE) + plugin QGIS, pour le Club UFS AURA.

## Licence

Code : EUPL-1.2 (`LICENSE`). Données : ODbL (OSM) et Licence Ouverte 2.0 selon les sources — attribution conservée dans les rapports.
