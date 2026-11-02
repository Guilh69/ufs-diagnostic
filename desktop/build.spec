# Packaging de l'application en exécutable autonome (PyInstaller).
# Sur ton PC :  pip install pyinstaller   puis   pyinstaller desktop/build.spec
# Résultat : dist/ufs-diagnostic.exe (Windows) ou dist/ufs-diagnostic.app (Mac)
# -*- mode: python ; coding: utf-8 -*-
import os
ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

a = Analysis(
    [os.path.join(ROOT, "desktop", "app.py")],
    pathex=[os.path.join(ROOT, "src")],
    binaries=[],
    datas=[(os.path.join(ROOT, "config"), "config"), (os.path.join(ROOT, "data"), "data"), (os.path.join(ROOT, "run_diagnostic.py"), "."), (os.path.join(ROOT, "src"), "src")],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas,
    name="ufs-diagnostic",
    console=False,
    icon=None,
)
app = BUNDLE(exe, name="ufs-diagnostic.app", icon=None) if os.name == "darwin" else None
