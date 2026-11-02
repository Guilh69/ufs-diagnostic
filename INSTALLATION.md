# Installer et lancer ufs-diagnostic sur ton ordinateur

## 1. Prérequis
- **Python 3** installé (gratuit) :
  - Windows : https://www.python.org/downloads/ → coche « Add Python to PATH » pendant l'installation
  - Mac : préinstallé (ou `brew install python3`)
  - Linux : `sudo apt install python3 python3-tk`
- Vérifie dans un terminal : `python3 --version` doit afficher un numéro (ex. 3.12.x)

## 2. Télécharger le projet
Sur https://github.com/Guilh69/ufs-diagnostic → bouton vert **Code** → **Download ZIP** → dézippe le dossier où tu veux (ex. Bureau).

## 3. Lancer l'application
Double-clique sur :
- Windows : `Lancer-ufs-diagnostic.bat`
- Mac : `Lancer-ufs-diagnostic.command` (clic droit → Ouvrir si « développeur non identifié »)
- Linux : `Lancer-ufs-diagnostic.sh` (clic droit → Exécuter, ou `./Lancer-ufs-diagnostic.sh` en terminal)

Ou en terminal, dans le dossier du projet : `python3 desktop/app.py`

## 4. Utiliser
- **Cas existant** : choisis `buers` → « Lancer le diagnostic » → le rapport s'ouvre dans le navigateur.
- **Nouveau quartier** : nom + adresse + rayon → « Créer et lancer » (géocodage automatique, données téléchargées, rapport ouvert).

## 4bis. Mises à jour (plus besoin de re-télécharger)
Dans l'application, clique sur **🔄 Mise à jour** : elle vérifie la version en ligne et, si une nouvelle existe, la télécharge et se met à jour toute seule. **Tes diagnostics (quartiers, adresses, rapports) sont conservés automatiquement.**

## 5. (Optionnel) Fabriquer un .exe / .app autonome
```
pip install pyinstaller
pyinstaller desktop/build.spec
```
→ `dist/ufs-diagnostic.exe` (Windows) / `dist/ufs-diagnostic.app` (Mac), partageable tel quel.

## Problèmes fréquents
- « python3 introuvable » → réinstalle Python en cochant « Add to PATH » (Windows)
- Fenêtre qui ne s'ouvre pas sur Linux → `sudo apt install python3-tk`
- « adresse introuvable » → vérifie l'orthographe de l'adresse (avec code postal)
