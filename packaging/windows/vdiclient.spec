# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PVE VDI Client Windows build.
Replaces inline pyinstaller command for reproducible builds.
"""

import os
import sys

# Get paths
block_cipher = None
project_root = os.path.abspath(os.path.join(SPECPATH, '..', '..'))
vdiclient_script = os.path.join(project_root, 'vdiclient.py')
templates_dir = os.path.join(project_root, 'vdiclient', 'templates')
static_dir = os.path.join(project_root, 'vdiclient', 'static')

# Analysis: specify all hidden imports
a = Analysis(
    [vdiclient_script],
    pathex=[project_root],
    binaries=[],
    datas=[
        (templates_dir, 'vdiclient/templates'),
        (static_dir, 'vdiclient/static'),
    ],
    hiddenimports=[
        # Proxmoxer
        'proxmoxer.backends',
        'proxmoxer.backends.https',
        'proxmoxer.backends.https.AuthenticationError',
        'proxmoxer.core',
        'proxmoxer.core.ResourceException',
        # Subprocess
        'subprocess.TimeoutExpired',
        'subprocess.CalledProcessError',
        # Requests
        'requests.exceptions',
        'requests.exceptions.ReadTimeout',
        'requests.exceptions.ConnectTimeout',
        'requests.exceptions.ConnectionError',
        # Flask
        'flask',
        'jinja2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ: Python archive
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# EXE: Executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='vdiclient',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX compression
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'vdiclient', 'static', 'vdiicon.ico'),
)

# COLLECT: Collect all files into dist folder
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='vdiclient',
)
