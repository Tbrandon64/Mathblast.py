# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\tb586\\OneDrive\\Documents\\Mathblast.py\\MathBlast_Universal.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\tb586\\OneDrive\\Documents\\Mathblast.py\\mathblast_server.py', '.'), ('C:\\Users\\tb586\\OneDrive\\Documents\\Mathblast.py\\Mathblast.py', '.')],
    hiddenimports=['onnxruntime', 'speech_recognition', 'pyttsx3', 'PIL'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MathBlast_AllInOne',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
