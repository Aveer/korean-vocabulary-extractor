# build-windows.ps1
# Build the Korean Vocab Extractor Windows portable application.
#
# This script:
#   1. Builds the frontend (or skips if already built)
#   2. Installs Python dependencies
#   3. Runs PyInstaller to create a portable app
#
# Prerequisites:
#   - Node.js 18+ installed
#   - Python 3.10+ installed
#   - Run from the project root directory
#
# Usage:
#   .\scripts\build-windows.ps1
#   .\scripts\build-windows.ps1 -SkipFrontend    # Skip frontend build
#   .\scripts\build-windows.ps1 -Clean           # Clean dist/ before building
#
# Output:
#   dist\KoreanVocabExtractor\  — Portable application folder
#   dist\KoreanVocabExtractor.zip — Zipped portable app (for distribution)

param(
    [switch]$SkipFrontend,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$distDir = Join-Path $projectRoot "dist"
$frontendDist = Join-Path $projectRoot "frontend" "dist"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Korean Vocab Extractor — Windows Build" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $projectRoot

# Clean previous build
if ($Clean) {
    Write-Host "Cleaning previous build..." -ForegroundColor Yellow
    if (Test-Path $distDir) {
        Remove-Item -Path $distDir -Recurse -Force
    }
    Write-Host "Cleaned." -ForegroundColor Green
    Write-Host ""
}

# Step 1: Build frontend
if (-not $SkipFrontend) {
    Write-Host "Step 1: Building frontend..." -ForegroundColor Cyan
    & (Join-Path $PSScriptRoot "build-frontend.ps1")
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Frontend build failed." -ForegroundColor Red
        exit 1
    }
    Write-Host ""
} else {
    Write-Host "Step 1: Skipping frontend build." -ForegroundColor Yellow
    if (-not (Test-Path (Join-Path $frontendDist "index.html"))) {
        Write-Host "ERROR: Frontend not built. Run without -SkipFrontend." -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

# Step 2: Install Python dependencies
Write-Host "Step 2: Installing Python dependencies..." -ForegroundColor Cyan

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}
Write-Host "Python: $(python --version 2>&1)" -ForegroundColor Green

# Create virtual environment if it doesn't exist
$venvDir = Join-Path $projectRoot "backend" "venv"
if (-not (Test-Path $venvDir)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvDir
}

# Activate and install
$activateScript = Join-Path $venvDir "Scripts" "Activate.ps1"
if (Test-Path $activateScript) {
    # PowerShell activation
    & $activateScript
} else {
    # Fallback: use python from venv directly
    $pythonExe = Join-Path $venvDir "Scripts" "python.exe"
}

$requirementsFile = Join-Path $projectRoot "backend" "requirements.txt"
Write-Host "Installing requirements..." -ForegroundColor Yellow
pip install -r $requirementsFile 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install Python dependencies." -ForegroundColor Red
    exit 1
}

# Install PyInstaller
Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
pip install pyinstaller 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install PyInstaller." -ForegroundColor Red
    exit 1
}
Write-Host "Python dependencies installed." -ForegroundColor Green
Write-Host ""

# Step 3: PyInstaller build
Write-Host "Step 3: Building with PyInstaller..." -ForegroundColor Cyan
$specFile = Join-Path $projectRoot "KoreanVocabExtractor.spec"
if (-not (Test-Path $specFile)) {
    Write-Host "ERROR: PyInstaller spec file not found at $specFile" -ForegroundColor Red
    exit 1
}

pyinstaller $specFile --clean 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: PyInstaller build failed." -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 4: Create ZIP
Write-Host "Step 4: Creating distribution ZIP..." -ForegroundColor Cyan
$appDir = Join-Path $distDir "KoreanVocabExtractor"
$zipFile = Join-Path $distDir "KoreanVocabExtractor.zip"

if (Test-Path $appDir) {
    if (Test-Path $zipFile) {
        Remove-Item $zipFile -Force
    }
    Compress-Archive -Path "$appDir\*" -DestinationPath $zipFile -Force
    $zipSize = [math]::Round((Get-Item $zipFile).Length / 1MB, 2)
    Write-Host "ZIP created: $zipFile ($zipSize MB)" -ForegroundColor Green
} else {
    Write-Host "WARNING: App directory not found at $appDir" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "  Build complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "  App folder: $appDir" -ForegroundColor Green
Write-Host "  ZIP file:   $zipFile" -ForegroundColor Green
Write-Host ""
Write-Host "To run: KoreanVocabExtractor.exe" -ForegroundColor Yellow
Write-Host "To distribute: share the ZIP file or the folder." -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Green
