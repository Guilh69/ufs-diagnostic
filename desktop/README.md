# ufs-diagnostic — application de bureau

## Lancer sans rien installer (juste Python 3)
```
python3 desktop/app.py
```
(Python officiel sur Windows/Mac inclut tkinter, donc aucune installation nécessaire.)

## Interface
- **Cas existant** : liste déroulante + « Lancer le diagnostic » + « Ouvrir le rapport ».
- **Nouveau diagnostic** : nom + adresse + rayon → géocodage automatique (API Adresse/BAN), création du périmètre, téléchargement des données ouvertes, lancement, ouverture du rapport dans le navigateur.

## Fabriquer un vrai exécutable (.exe / .app) — optionnel
```
pip install pyinstaller
pyinstaller desktop/build.spec
```
→ produit `dist/ufs-diagnostic.exe` (Windows) ou `dist/ufs-diagnostic.app` (Mac), partageable tel quel.

## Note
L'interface utilise tkinter (bibliothèque standard de Python). Si tkinter manque (rare, certaines installations Linux minimales), installer le paquet système `python3-tk`.
