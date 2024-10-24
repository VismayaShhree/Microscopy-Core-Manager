 # -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['Microscope_use.py'],
    pathex=['/Users/Dhanashree/Documents/GitHub/Microscope_use'],
    binaries=[],
    datas=[],
    hiddenimports=['tkcalendar', 'babel', 'babel.numbers', 'babel.dates', 'babel.localedata'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Microscope_use',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Microscope_use'
)
app = BUNDLE(
    exe,
    name='Microscope_use.app',
    icon=None,
    bundle_identifier=None,
)
