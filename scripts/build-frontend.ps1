# build-frontend.ps1
# Build the React frontend into static files for packaging.
#
# Prerequisites:
#   - Node.js 18+ installed
#   - Run from the project root directory
#
# Usage:
#   .\scripts\build-frontend.ps1
#
# Output:
#   frontend\dist\  — Static files (HTML, CSS, JS)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $projectRoot "frontend"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Korean Vocab Extractor — Build Frontend" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Node.js is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Install from https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

Write-Host "Node.js: $(node --version)" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location $frontendDir
npm ci --prefer-offline 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Falling back to npm install..." -ForegroundColor Yellow
    npm install 2>&1 | Out-Null
}
Write-Host "Dependencies installed." -ForegroundColor Green
Write-Host ""

# Build
Write-Host "Building frontend..." -ForegroundColor Yellow
npm run build 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Frontend build failed." -ForegroundColor Red
    exit 1
}

# Verify output
$distDir = Join-Path $frontendDir "dist"
$indexHtml = Join-Path $distDir "index.html"
if (Test-Path $indexHtml) {
    $fileCount = (Get-ChildItem -Path $distDir -Recurse -File).Count
    Write-Host ""
    Write-Host "Frontend build complete!" -ForegroundColor Green
    Write-Host "  Output: $distDir" -ForegroundColor Green
    Write-Host "  Files:  $fileCount" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "ERROR: Build output not found at $indexHtml" -ForegroundColor Red
    exit 1
}

Set-Location $projectRoot
