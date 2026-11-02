"""Plugin QGIS ufs-diagnostic (PyQGIS).

Action : sur la couche de périmètre sélectionnée (ou la vue carte), appelle
l'API ufs-diagnostic (POST /diagnostic) et charge les résultats comme couches :
- mailles (scores) ; - isochrone ; - POI ; et affiche le rapport HTML.
"""
import json
import os
import urllib.request

from qgis.PyQt.QtWidgets import QAction, QMessageBox, QInputDialog
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices

API_DEFAULT = "http://127.0.0.1:8080"


class UfsDiagnosticPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None

    def initGui(self):
        self.action = QAction("Diagnostic UFS (proximité, isochrones, EQIS)", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("&ufs-diagnostic", self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removePluginMenu("&ufs-diagnostic", self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        api, ok = QInputDialog.getText(None, "API ufs-diagnostic", "URL de l'API :", text=API_DEFAULT)
        if not ok:
            return
        perimeter, ok = QInputDialog.getText(None, "Périmètre", "Identifiant du périmètre (ex. buers) :", text="buers")
        if not ok:
            return
        try:
            req = urllib.request.Request(
                api.rstrip("/") + "/diagnostic",
                data=json.dumps({"perimeter": perimeter, "radius_m": 800, "with_network": True}).encode(),
                headers={"Content-Type": "application/json"},
            )
            d = json.loads(urllib.request.urlopen(req, timeout=120).read())
        except Exception as e:
            QMessageBox.critical(None, "ufs-diagnostic", f"API injoignable : {e}")
            return

        root = QgsProject.instance().layerTreeRoot()
        grp = root.addGroup(f"UFS {perimeter}")

        # mailles avec scores
        feats = []
        for c in d.get("cells_sample", []):
            lon, lat = c["centroid"]
            feats.append({"score": c["score"], "id": c["id"]})
        if feats:
            # couche de points au centroïde
            vl = QgsVectorLayer("Point?crs=EPSG:4326", f"mailles_{perimeter}", "memory")
            pr = vl.dataProvider()
            from qgis.core import QgsField, QgsFeature, QgsGeometry, QgsPointXY
            pr.addAttributes([QgsField("id", 10), QgsField("score", 6)])
            vl.updateFields()
            for c in d.get("cells_sample", []):
                lon, lat = c["centroid"]
                f = QgsFeature()
                f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
                f.setAttributes([c["id"], c["score"]])
                pr.addFeature(f)
            vl.updateExtents()
            QgsProject.instance().addMapLayer(vl, False)
            grp.addLayer(vl)

        # résumé + ouverture du rapport
        z = d.get("zone") or {}
        msg = [f"Périmètre : {d['perimeter']['name']}",
               f"Mailles : {d['nb_cells']} | zone : {z.get('nom')} ({z.get('area_km2')} km²)"]
        for k, s in (d.get("summary") or {}).items():
            msg.append(f"- {k}: {s['nb_pois']} objets, {s['pct_cells']}% mailles ≤ {s['radius_m']} m")
        eq = (d.get("eqis") or {}).get("resultats", {})
        for k, r in eq.items():
            msg.append(f"- EQIS {k}: C={r['concentration_ugm3']} µg/m³ → {r['deces_attribuables_an']} décès/an")
        QMessageBox.information(None, "ufs-diagnostic", "\n".join(msg))
        QDesktopServices.openUrl(QUrl(f"{api.rstrip('/')}/report/{perimeter}"))
