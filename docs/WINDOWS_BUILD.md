# Windows Portable App Build Guide

## Overview

The Korean Vocab Extractor can be packaged as a Windows portable application.
A non-technical user downloads a ZIP file, extracts it, and runs `KoreanVocabExtractor.exe` — no Python, Node, or other dependencies required.

## Quick Start for End Users

1. Download the latest `KoreanVocabExtractor-Windows-*` artifact from GitHub Actions
2. Extract the GitHub artifact ZIP to any folder (for example, `C:\Apps\`)
3. Open the extracted `KoreanVocabExtractor` folder
4. Double-click `KoreanVocabExtractor.exe`
5. The app opens automatically in your default browser at `http://127.0.0.1:8765`
6. Paste Korean text, start a quest, save cards, and review them locally

The artifact also includes `KoreanVocabExtractor.zip`, which contains the same
portable app folder for release uploads or re-sharing. End users do not need
Python, Node.js, or a repo checkout.

## Build Locally (Windows)

### Prerequisites
- **Node.js 20+** — [nodejs.org](https://nodejs.org/)
- **Python 3.12+** — [python.org](https://www.python.org/)
- **PowerShell 5+** — included with Windows 10/11

### Build Steps

```powershell
# Clone the repository
git clone https://github.com/Aveer/korean-vocabulary-extractor.git
cd korean-vocabulary-extractor

# Build, smoke-test, and zip the Windows portable app
.\scripts\build-windows.ps1 -Clean

# Output:
#   dist\KoreanVocabExtractor\KoreanVocabExtractor.exe
#   dist\KoreanVocabExtractor.zip
```

### Build Options

```powershell
# Skip frontend build (if already built)
.\scripts\build-windows.ps1 -SkipFrontend

# Clean previous build before building
.\scripts\build-windows.ps1 -Clean

# Build without the executable smoke test
.\scripts\build-windows.ps1 -NoSmoke

# Build just the frontend
.\scripts\build-frontend.ps1
```

`build-windows.ps1` delegates to `scripts/build_package.py`, which verifies the
packaged executable by starting it with `--no-browser`, checking `/api/health`,
loading the frontend, verifying the bundled dictionary, running one extraction
request with sentence translation disabled, and exercising the local study APIs
(stats, save card, due reviews, review submission) using a temporary app-data
directory.

## Trigger GitHub Actions Build

The Windows CI job runs automatically on pushes and pull requests, and it can
also be started manually for ad-hoc portable builds.

1. Go to the [GitHub repository](https://github.com/Aveer/korean-vocabulary-extractor)
2. Click the **Actions** tab
3. Select **Build Windows Portable** workflow
4. Click **Run workflow** → **Run workflow**
5. Wait for the build to complete (typically 3-5 minutes)

## Download the Artifact

After the workflow completes:

1. Go to the [Actions run](https://github.com/Aveer/korean-vocabulary-extractor/actions)
2. Click on the completed workflow run
3. Scroll down to **Artifacts**
4. Download the **KoreanVocabExtractor-Windows-...** artifact
5. Extract the artifact ZIP and run `KoreanVocabExtractor\KoreanVocabExtractor.exe`

The artifact is retained for 30 days after the build. It contains both a
directly runnable `KoreanVocabExtractor` folder and a `KoreanVocabExtractor.zip`
copy of the same portable app.

## App Behavior

- **Port**: Starts on `127.0.0.1:8765` by default. If port 8765 is in use, it tries 8766, 8767, etc.
- **Browser**: Opens automatically in your default browser
- **CLI smoke-test mode**: `KoreanVocabExtractor.exe --no-browser --port 8765`
- **Config/study data**: Dictionary settings, cache, and `study.sqlite3` are stored in `%APPDATA%\KoreanVocabExtractor\`
- **Dictionary**: Uses the bundled offline dictionary by default (no API key needed)
- **Study deck**: Saved cards, known/ignored lemmas, reviews, XP, streak, and level are local to this device
- **NIKL API**: Optional — configure via the Settings panel in the app
- **Translations**: Google Translate is used for sentence-level English translations (requires internet)

## Troubleshooting

### App won't start
- Check if another instance is running on port 8765
- Try running from PowerShell: `cd C:\path\to\app && .\KoreanVocabExtractor.exe`

### "Kiwi model not found" error
- The `kiwipiepy_model` NLP data may not have been included in the package
- Rebuild with `.\scripts\build-windows.ps1 -Clean`
- Ensure `kiwipiepy` and `kiwipiepy_model` are installed before running PyInstaller

### Dictionary shows no results
- The bundled dictionary works offline — no API key needed
- For NIKL dictionary: go to Settings → switch to NIKL → enter your API key

### Port already in use
- The app auto-selects the next available port
- Check the console window for the actual port number
