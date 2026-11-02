"""Plugin QGIS ufs-diagnostic (PyQGIS) — version consolidee.

- N'bloque pas l'interface (calcul en QThread)
- Charge : mailles (scores), polygone de zone, point d'ancrage, POI, isochrone
- Ouvre le rapport HTML dans le navigateur
- Gestion d'erreurs explicite (API absente, perimetre inconnu, timeout)
"""
import json
import os
import urllib.error
import urllib.request

from qgis.PyQt.QtWidgets import QAction, QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
from qgis.PyQt.QtCore import QThread, pyqtSignal, QUrl
from qgis.PyQt.QtGui import QDesktopServices, QColor
from qgis.core import (QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsGeometry,
                       QgsPointXY, QgsRectangle, QgsSingleSymbolRenderer, QgsFillSymbol,
                       QgsLineSymbol, QgsCircleMarkerSymbol, QgsUnitTypes)

API_DEFAULT = "http://127.0.0.1:8080"


class DiagThread(QThread):
    ok = pyqtSignal(dict)
    ko = pyqtSignal(str)

    def __init__(self, api, perimeter, radius):
        super().__init__()
        self.api, self.perimeter, self.radius = api, perimeter, radius

    def run(self):
        try:
            req = urllib.request.Request(
                self.api.rstrip("/") + "/diagnostic",
                data=json.dumps({"perimeter": self.perimeter, "radius_m": self.radius,
                                 "with_network": True}).encode(),
                headers={"Content-Type": "application/json"})
            d = json.loads(urllib.request.urlopen(req, timeout=180).read())
            self.ok.emit(d)
        except urllib.error.URLError as e:
            self.ko.emit(f"API injoignable ({self.api}). Lance-la d'abord : cd src && python3 -m ufsdiag.api\nDétail : {e}")
        except Exception as e:
            self.ko.emit(f"Erreur : {e}")


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ufs-diagnostic — lancer un diagnostic")
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.api_edit = QLineEdit(API_DEFAULT)
        self.perim_edit = QLineEdit("buers")
        self.radius_edit = QLineEdit("800")
        form.addRow("URL de l'API ufs-diagnostic :", self.api_edit)
        form.addRow("Périmètre (id du cas) :", self.perim_edit)
        form.addRow("Rayon d'étude (m) :", self.radius_edit)
        lay.addLayout(form)
        btn = QPushButton("Lancer le diagnostic")
        btn.clicked.connect(self.accept)
        lay.addWidget(btn)


def _memory_layer(name, geom_type, fields, feats, crs="EPSG:4326"):
    vl = QgsVectorLayer(f"{geom_type}?crs={crs}", name, "memory")
    pr = vl.dataProvider()
    pr.addAttributes([QgsField(n, t) for n, t in fields])
    vl.updateFields()
    for geom, attrs in feats:
        f = QgsFeature()
        f.setGeometry(geom)
        f.setAttributes(attrs)
        pr.addFeature(f)
    vl.updateExtents()
    return vl


class UfsDiagnosticPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.thread = None

    def initGui(self):
        self.action = QAction("Diagnostic UFS…", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("&ufs-diagnostic", self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removePluginMenu("&ufs-diagnostic", self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        dlg = ConfigDialog()
        if not dlg.exec():
            return
        api, perim = dlg.api_edit.text().strip(), dlg.perim_edit.text().strip()
        try:
            radius = int(dlg.radius_edit.text())
        except ValueError:
            radius = 800
        self.iface.messageBar().pushInfo("ufs-diagnostic", f"Diagnostic « {perim} » en cours…")
        self.thread = DiagThread(api, perim, radius)
        self.thread.ok.connect(lambda d: self._on_ok(api, perim, d))
        self.thread.ko.connect(self._on_ko)
        self.thread.start()

    def _on_ko(self, msg):
        self.iface.messageBar().pushCritical("ufs-diagnostic", msg[:300])
        QMessageBox.critical(None, "ufs-diagnostic", msg)

    def _on_ok(self, api, perim, d):
        root = QgsProject.instance().layerTreeRoot()
        grp = root.addGroup(f"UFS {perim}")
        proj = QgsProject.instance()

        # mailles (points au centroïde, score en attribut)
        feats = [(QgsGeometry.fromPointXY(QgsPointXY(c["centroid"][0], c["centroid"][1])),
                  [c["id"], c["score"]]) for c in d.get("cells_sample", [])]
        if feats:
            vl = _memory_layer(f"mailles_{perim}", "Point", [("id", 10), ("score", 6)], feats)
            r = QgsSingleSymbolRenderer(QgsCircleMarkerSymbol.createSimple({"size": "3", "color": "#27ae60"}))
            vl.setRenderer(r)
            proj.addMapLayer(vl, False)
            grp.addLayer(vl)

        # zone (polygone) si dispo
        z = d.get("zone") or {}
        zfile = os.path.join(ROOT_OUT, perim, "zone.geojson") if (ROOT_OUT := os.path.join(os.path.dirname(__file__), "..", "..", "outputs")) else None
        zpath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "outputs", perim, "zone.geojson"))
        if os.path.exists(zpath):
            vz = QgsVectorLayer(zpath, f"zone_{perim}", "ogr")
            if vz.isValid():
                sym = QgsFillSymbol.createSimple({"color": "#e74c3c55", "outline_color": "#c0392b", "outline_width": "0.6"})
                vz.setRenderer(QgsSingleSymbolRenderer(sym))
                proj.addMapLayer(vz, False)
                grp.addLayer(vz)
                self.iface.mapCanvas().setExtent(vz.extent())
                self.iface.mapCanvas().refresh()

        # point d'ancrage
        pa = d.get("point_ancrage") or {}
        if pa.get("_lon"):
            vp = _memory_layer(f"point_ancrage_{perim}", "Point",
                               [("adresse", 10)],
                               [(QgsGeometry.fromPointXY(QgsPointXY(pa["_lon"], pa["_lat"])), [pa.get("_adresse", "")])])
            vp.setRenderer(QgsSingleSymbolRenderer(QgsCircleMarkerSymbol.createSimple({"size": "7", "color": "#2c3e50"})))
            proj.addMapLayer(vp, False)
            grp.addLayer(vp)

        # résumé
        msg = [f"Périmètre : {d['perimeter']['name']}", f"Mailles : {d['nb_cells']}"]
        if z:
            msg.append(f"Zone : {z.get('nom')} ({z.get('area_km2')} km²)")
        for k, s in (d.get("summary") or {}).items():
            msg.append(f"• {k}: {s['nb_pois']} objets, {s['pct_cells']}% mailles ≤ {s['radius_m']} m")
        eq = (d.get("eqis") or {}).get("resultats", {})
        for k, r in eq.items():
            msg.append(f"• EQIS {k}: {r['concentration_ugm3']} µg/m³ → {r['deces_attribuables_an']} décès/an")
        self.iface.messageBar().pushSuccess("ufs-diagnostic", f"Diagnostic « {perim} » terminé — {d['nb_cells']} mailles")
        QMessageBox.information(None, "ufs-diagnostic", "\n".join(msg) + "\n\nOuvrir le rapport ?")
        QDesktopServices.openUrl(QUrl(f"{api.rstrip('/')}/report/{perim}"))
