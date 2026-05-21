# build-windows.ps1
# Build, smoke-test, and zip the Korean Vocab Extractor Windows portable app.
#
# Prerequisites:
#   - Windows host (PyInstaller does not cross-compile Windows .exe files)
#   - Node.js 20+ installed
#   - Python 3.12+ installed
#   - Run from the project root directory
#
# Usage:
#   .\scripts\build-windows.ps1
#   .\scripts\build-windows.ps1 -SkipFrontend    # Reuse frontend\dist\
#   .\scripts\build-windows.ps1 -Clean           # Remove dist\ and build\ first
#   .\scripts\build-windows.ps1 -NoSmoke         # Build without executable smoke test
#
# Output:
#   dist\KoreanVocabExtractor\KoreanVocabExtractor.exe
#   dist\KoreanVocabExtractor.zip

param(
    [switch]$SkipFrontend,
    [switch]$Clean,
    [switch]$NoSmoke
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvDir = Join-Path $projectRoot "backend" "venv"
$pythonExe = Join-Path $venvDir "Scripts" "python.exe"
$buildScript = Join-Path $projectRoot "scripts" "build_package.py"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Korean Vocab Extractor — Windows Build" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $projectRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}
Write-Host "Python: $(python --version 2>&1)" -ForegroundColor Green

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Node.js 20+ is not installed or not in PATH." -ForegroundColor Red
    exit 1
}
Write-Host "Node:   $(node --version 2>&1)" -ForegroundColor Green

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: npm is not installed or not in PATH." -ForegroundColor Red
    exit 1
}
Write-Host "npm:    $(npm --version 2>&1)" -ForegroundColor Green

if (-not (Test-Path $venvDir)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvDir
}

if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Virtual environment Python not found at $pythonExe" -ForegroundColor Red
    exit 1
}

$argsList = @($buildScript)
if ($SkipFrontend) { $argsList += "--skip-frontend" }
if ($Clean) { $argsList += "--clean" }
if ($NoSmoke) { $argsList += "--no-smoke" }

Write-Host "Running package builder..." -ForegroundColor Cyan
& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Windows package build failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
if ($NoSmoke) {
    Write-Host "  Build complete!" -ForegroundColor Green
} else {
    Write-Host "  Build complete and smoke-tested!" -ForegroundColor Green
}
Write-Host "==================================================" -ForegroundColor Green
Write-Host "  App folder: dist\KoreanVocabExtractor" -ForegroundColor Green
Write-Host "  EXE:        dist\KoreanVocabExtractor\KoreanVocabExtractor.exe" -ForegroundColor Green
Write-Host "  ZIP file:   dist\KoreanVocabExtractor.zip" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
