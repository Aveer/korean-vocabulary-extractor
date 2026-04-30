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

# Determine base directory
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

# Data files to include
datas = []

# 1. Bundled dictionary
bundled_dict = BACKEND_DIR / "dictionary" / "bundled_dict.json"
if bundled_dict.exists():
    datas.append((str(bundled_dict), "backend/dictionary/"))

# 2. Frontend build output
if FRONTEND_DIST.exists():
    datas.append((str(FRONTEND_DIST), "frontend_dist/"))

# 3. kiwipiepy model data — required for morphological analysis
#    kiwipiepy stores models in the site-packages directory
kiwi_model_dirs = []
for site_packages_path in sys.path:
    kiwi_path = Path(site_packages_path) / "kiwipiepy" / "model"
    if kiwi_path.exists():
        kiwi_model_dirs.append(kiwi_path)
        break

if kiwi_model_dirs:
    model_dir = kiwi_model_dirs[0]
    for item in model_dir.iterdir():
        datas.append((str(item), "kiwipiepy/model/"))
else:
    print("WARNING: kiwipiepy model directory not found. "
          "The app may not work without it. Install kiwipiepy first.")

# Hidden imports — modules imported dynamically
hiddenimports = [
    "api",
    "api.extract_vocab",
    "api.models",
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
    "nlp.filtering",
    "nlp.tokenizer",
    "nlp.sentencizer",
    "nlp.translator",
    "deep_translator",
    "deep_translator.google_translator",
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
    exclude_binaries=False,
    name="KoreanVocabExtractor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for debugging; set False for GUI-only
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
