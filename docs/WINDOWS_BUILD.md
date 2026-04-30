# Windows Portable App Build Guide

## Overview

The Korean Vocab Extractor can be packaged as a Windows portable application.
A non-technical user downloads a ZIP file, extracts it, and runs `KoreanVocabExtractor.exe` — no Python, Node, or other dependencies required.

## Quick Start for End Users

1. Download the latest `KoreanVocabExtractor-Windows.zip` artifact from GitHub Actions
2. Extract the ZIP to any folder (e.g., `C:\Apps\KoreanVocabExtractor\`)
3. Double-click `KoreanVocabExtractor.exe`
4. The app opens automatically in your default browser at `http://127.0.0.1:8765`
5. Paste Korean text and click "Extract"

## Build Locally (Windows)

### Prerequisites
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)
- **Python 3.10+** — [python.org](https://www.python.org/)
- **PowerShell 5+** — included with Windows 10/11

### Build Steps

```powershell
# Clone the repository
git clone https://github.com/Aveer/korean-vocabulary-extractor.git
cd korean-vocabulary-extractor

# Build the Windows portable app (frontend + backend + packaging)
.\scripts\build-windows.ps1

# Output:
#   dist\KoreanVocabExtractor\    — Portable app folder
#   dist\KoreanVocabExtractor.zip — ZIP for distribution
```

### Build Options

```powershell
# Skip frontend build (if already built)
.\scripts\build-windows.ps1 -SkipFrontend

# Clean previous build before building
.\scripts\build-windows.ps1 -Clean

# Build just the frontend
.\scripts\build-frontend.ps1
```

## Trigger GitHub Actions Build

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
4. Download **KoreanVocabExtractor-Windows.zip**

The artifact is retained for 30 days after the build.

## App Behavior

- **Port**: Starts on `127.0.0.1:8765` by default. If port 8765 is in use, it tries 8766, 8767, etc.
- **Browser**: Opens automatically in your default browser
- **Config**: Dictionary settings and cache are stored in `%APPDATA%\KoreanVocabExtractor\`
- **Dictionary**: Uses the bundled offline dictionary by default (no API key needed)
- **NIKL API**: Optional — configure via the Settings panel in the app
- **Translations**: Google Translate is used for sentence-level English translations (requires internet)

## Troubleshooting

### App won't start
- Check if another instance is running on port 8765
- Try running from PowerShell: `cd C:\path\to\app && .\KoreanVocabExtractor.exe`

### "Kiwi model not found" error
- The kiwipiepy NLP model may not have been included in the package
- Rebuild with `.\scripts\build-windows.ps1 -Clean`
- Ensure `kiwipiepy` is installed before running PyInstaller

### Dictionary shows no results
- The bundled dictionary works offline — no API key needed
- For NIKL dictionary: go to Settings → switch to NIKL → enter your API key

### Port already in use
- The app auto-selects the next available port
- Check the console window for the actual port number
