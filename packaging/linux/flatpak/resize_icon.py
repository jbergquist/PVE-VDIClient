#!/usr/bin/env python3
"""Pad the source icon to a 256x256 square and write it to FLATPAK_DEST."""
import glob
import os
import sys

# Pillow is installed to FLATPAK_DEST by the python-dependencies module
sp = glob.glob('/app/lib/python*/site-packages')
if sp:
    sys.path.insert(0, sp[0])

from PIL import Image  # noqa: E402

src = 'vdiclient/static/vdiclient.png'
dest_dir = os.path.join(
    os.environ.get('FLATPAK_DEST', '/app'),
    'share', 'icons', 'hicolor', '256x256', 'apps',
)
dest = os.path.join(dest_dir, 'org.proxmox.VDIClient.png')

img = Image.open(src).convert('RGBA')
canvas = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
canvas.paste(img, ((256 - img.width) // 2, (256 - img.height) // 2))
os.makedirs(dest_dir, exist_ok=True)
canvas.save(dest)
print(f'Icon written to {dest}')
