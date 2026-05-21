# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Korean Vocab Extractor.

Builds a one-folder portable application:
  dist/KoreanVocabExtractor/
    KoreanVocabExtractor.exe   (Windows)
    KoreanVocabExtractor       (Linux/macOS)
    frontend_dist/             (built frontend static files)
    ...                        (Python runtime and dependencies)

Usage:
  pyinstaller KoreanVocabExtractor.spec
"""

import os
import sys
from pathlib import Path

# Determine base directory — spec runs from repo root via `pyinstaller KoreanVocabExtractor.spec`
# __file__ is NOT defined inside PyInstaller's spec execution context
BASE_DIR = Path(os.getcwd())

BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

print("=== Spec debug ===")
print(f"BASE_DIR:    {BASE_DIR}")
print(f"BACKEND_DIR: {BACKEND_DIR} (exists: {BACKEND_DIR.exists()})")
print(f"FRONTEND:    {FRONTEND_DIST} (exists: {FRONTEND_DIST.exists()})")

# Data files to include
datas = []
required_missing = []

# 1. Bundled dictionary
bundled_dict = BACKEND_DIR / "dictionary" / "bundled_dict.json"
if bundled_dict.exists():
    datas.append((str(bundled_dict), "backend/dictionary/"))
    print(f"  + bundled_dict: {bundled_dict}")
else:
    print(f"  ! bundled_dict NOT FOUND: {bundled_dict}")
    required_missing.append(f"bundled dictionary: {bundled_dict}")

# 2. Frontend build output
if FRONTEND_DIST.exists():
    datas.append((str(FRONTEND_DIST), "frontend_dist/"))
    print(f"  + frontend_dist: {FRONTEND_DIST}")
else:
    print(f"  ! frontend_dist NOT FOUND: {FRONTEND_DIST}")
    required_missing.append(f"frontend build output: {FRONTEND_DIST}")

# 3. kiwipiepy model data — required for morphological analysis.
#    Current kiwipiepy releases install model files in the sibling
#    kiwipiepy_model package; older layouts used kiwipiepy/model.
def _add_directory_data(source_dir, target_dir, label):
    if not source_dir.exists():
        return False

    files = [
        path
        for path in source_dir.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    ]
    for path in files:
        relative_parent = path.relative_to(source_dir).parent
        datas.append((str(path), str(Path(target_dir) / relative_parent)))
    print(f"  + {label}: {source_dir} ({len(files)} files)")
    return True


kiwi_model_found = False
for site_packages_path in sys.path:
    site_packages = Path(site_packages_path)
    if _add_directory_data(site_packages / "kiwipiepy_model", "kiwipiepy_model", "kiwipiepy_model data"):
        kiwi_model_found = True
        break

if not kiwi_model_found:
    for site_packages_path in sys.path:
        site_packages = Path(site_packages_path)
        if _add_directory_data(site_packages / "kiwipiepy" / "model", "kiwipiepy/model", "legacy kiwipiepy model"):
            kiwi_model_found = True
            break

if not kiwi_model_found:
    print("WARNING: kiwipiepy model data not found. "
          "The app may not work without it. Install kiwipiepy first.")
    required_missing.append("kiwipiepy_model package data")

if required_missing:
    print("ERROR: required package data is missing:")
    for missing in required_missing:
        print(f"  - {missing}")
    raise SystemExit("Cannot build a runnable package until required data is present.")

print(f"Total datas: {len(datas)}")
print(f"=== End spec debug ===")

# Hidden imports — modules imported dynamically
hiddenimports = [
    "api",
    "api.extract_vocab",
    "api.models",
    "api.study",
    "cache",
    "cache.store",
    "config_paths",
    "dictionary",
    "dictionary.bundled",
    "dictionary.nikl",
    "dictionary.provider",
    "nlp",
    "nlp.pipeline",
    "nlp.ranker",
    "nlp.lemmatizer",
    "nlp.filter",
    "nlp.tokenizer",
    "nlp.splitter",
    "nlp.translator",
    "study",
    "study.db",
    "study.service",
    "kiwipiepy",
    "kiwipiepy_model",
    "_kiwipiepy",
    "numpy",
    "deep_translator",
    "deep_translator.google",
]

a = Analysis(
    ["backend/run_app.py"],
    pathex=[str(BACKEND_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "setuptools",
        "pip",
        "tkinter",
        "unittest",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name="KoreanVocabExtractor",
    exclude_binaries=True,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for debugging; set False for GUI-only
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="KoreanVocabExtractor",
)
