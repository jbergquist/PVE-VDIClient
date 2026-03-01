@echo off
REM Build Windows MSI package for PVE VDI Client
REM Uses PyInstaller + WIX Toolset

setlocal enabledelayedexpansion

echo === Building Windows MSI package ===

REM Get script directory and project root
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..
set SPEC_FILE=%SCRIPT_DIR%vdiclient.spec
set WIX_DIR=%SCRIPT_DIR%wix
set DIST_DIR=%PROJECT_ROOT%\dist
set BUILD_DIR=%PROJECT_ROOT%\build

REM Clean previous build artifacts
echo Cleaning previous build artifacts...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
del /q "%PROJECT_ROOT%\*.msi" 2>nul

REM Check for PyInstaller
where pyinstaller >nul 2>&1
if errorlevel 1 (
    echo ERROR: PyInstaller not found!
    echo Install with: pip install pyinstaller
    exit /b 1
)

REM Build with PyInstaller using spec file
echo Building executable with PyInstaller...
cd /d "%PROJECT_ROOT%"
pyinstaller --noconfirm "%SPEC_FILE%"

if not exist "%DIST_DIR%\vdiclient\vdiclient.exe" (
    echo ERROR: PyInstaller build failed!
    exit /b 1
)

echo PyInstaller build successful!

REM Check for WIX Toolset (candle.exe)
where candle >nul 2>&1
if errorlevel 1 (
    echo WARNING: WIX Toolset not found in PATH
    echo MSI creation will be skipped
    echo Download from: https://wixtoolset.org/
    echo Build output available at: %DIST_DIR%\vdiclient\
    exit /b 0
)

REM Create MSI with WIX
echo Creating MSI with WIX Toolset...
cd /d "%DIST_DIR%"
python "%WIX_DIR%\createmsi.py" "%WIX_DIR%\vdiclient.json"

if errorlevel 1 (
    echo ERROR: MSI creation failed!
    exit /b 1
)

REM Find the generated MSI
for %%f in (*.msi) do (
    set MSI_FILE=%%f
    goto :found_msi
)

:found_msi
if not defined MSI_FILE (
    echo ERROR: MSI file not found!
    exit /b 1
)

REM Move MSI to project root
echo Moving MSI to project root...
move /y "!MSI_FILE!" "%PROJECT_ROOT%\"

echo.
echo === Build successful! ===
echo MSI: %PROJECT_ROOT%\!MSI_FILE!
echo.
echo To install:
echo   %PROJECT_ROOT%\!MSI_FILE!
echo.
echo Note: Requires virt-viewer from https://www.spice-space.org/download.html
echo.

exit /b 0
