# Plugin QGIS ufs-diagnostic — installation

## 1. Localiser le dossier plugins de QGIS
Dans QGIS : **Préférences → Profils utilisateur → Ouvrir le dossier du profil actif**, puis `python/plugins/`.
- Windows : `C:\Users\<toi>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
- Mac : `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
- Linux : `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`

## 2. Copier le plugin
Télécharge le dépôt (Code → Download ZIP), dézippe, copie le dossier **`qgis-plugin/ufs_diagnostic/`** dans `python/plugins/`.

## 3. Activer
**Extensions → Installer/Gérer les extensions → Installé** → coche **ufs-diagnostic**.

## 4. Lancer l'API (obligatoire avant)
Dans un terminal, à la racine du projet :
```
cd src && python3 -m ufsdiag.api --port 8080
```

## 5. Utiliser
Nouvelle icône dans la barre d'outils → « Diagnostic UFS… » → URL de l'API (`http://127.0.0.1:8080`), périmètre (`buers`), rayon (800 m) → **Lancer**. Le plugin charge les mailles, la zone, le point d'ancrage dans QGIS (groupe « UFS buers »), affiche le résumé et ouvre le rapport HTML.

## Dépannage
- « API injoignable » → l'API n'est pas lancée (étape 4)
- Le calcul tourne en arrière-plan : QGIS reste utilisable pendant le diagnostic
