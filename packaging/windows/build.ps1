# Build Windows MSI package for PVE VDI Client
# PowerShell version for GitHub Actions and modern Windows

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "=== Building Windows MSI package ===" -ForegroundColor Cyan

# Get paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.Parent.FullName
$SpecFile = Join-Path $ScriptDir "vdiclient.spec"
$WixDir = Join-Path $ScriptDir "wix"
$DistDir = Join-Path $ProjectRoot "dist"
$BuildDir = Join-Path $ProjectRoot "build"

# Clean previous build artifacts
Write-Host "Cleaning previous build artifacts..."
if (Test-Path $DistDir) { Remove-Item -Recurse -Force $DistDir }
if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
Get-ChildItem -Path $ProjectRoot -Filter "*.msi" | Remove-Item -Force

# Check for PyInstaller
if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Error "PyInstaller not found! Install with: pip install pyinstaller"
    exit 1
}

# Build with PyInstaller using spec file
Write-Host "Building executable with PyInstaller..." -ForegroundColor Green
Push-Location $ProjectRoot
try {
    pyinstaller --noconfirm $SpecFile
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

$ExePath = Join-Path $DistDir "vdiclient\vdiclient.exe"
if (-not (Test-Path $ExePath)) {
    Write-Error "PyInstaller build failed! Executable not found at: $ExePath"
    exit 1
}

Write-Host "PyInstaller build successful!" -ForegroundColor Green

# Check for WIX Toolset
if (-not (Get-Command candle -ErrorAction SilentlyContinue)) {
    Write-Warning "WIX Toolset not found in PATH"
    Write-Host "MSI creation will be skipped" -ForegroundColor Yellow
    Write-Host "Download from: https://wixtoolset.org/"
    Write-Host "Build output available at: $DistDir\vdiclient\"
    exit 0
}

# Create MSI with WIX
# createmsi.py must be run from the dist dir with a bare filename (no path separators)
Write-Host "Creating MSI with WIX Toolset..." -ForegroundColor Green
Push-Location $DistDir
try {
    Copy-Item (Join-Path $WixDir "vdiclient.json") "vdiclient.json" -Force
    Copy-Item (Join-Path $WixDir "License.rtf")    "License.rtf"    -Force
    $CreateMsiPy = Join-Path $WixDir "createmsi.py"

    python $CreateMsiPy vdiclient.json
    if ($LASTEXITCODE -ne 0) {
        throw "MSI creation failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

# Find the generated MSI
$MsiFile = Get-ChildItem -Path $DistDir -Filter "*.msi" | Select-Object -First 1

if (-not $MsiFile) {
    Write-Error "MSI file not found in $DistDir"
    exit 1
}

# Move MSI to project root
Write-Host "Moving MSI to project root..."
$DestMsi = Join-Path $ProjectRoot $MsiFile.Name
Move-Item -Path $MsiFile.FullName -Destination $DestMsi -Force

Write-Host ""
Write-Host "=== Build successful! ===" -ForegroundColor Green
Write-Host "MSI: $DestMsi"
Write-Host ""
Write-Host "To install:"
Write-Host "  $DestMsi"
Write-Host ""
Write-Host "Note: Requires virt-viewer from https://www.spice-space.org/download.html"
Write-Host ""

exit 0
