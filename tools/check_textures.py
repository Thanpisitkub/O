#!/usr/bin/env python3
"""Automated + visual checks of the particle PNGs.  Usage: check_textures.py <particle_dir> <preview_out.png>"""
import os
import sys

import numpy as np
from PIL import Image

d = sys.argv[1]
out = sys.argv[2]
names = ["shinra_tensei_wave", "shinra_tensei_burst", "bansho_tenin_aura",
         "chibaku_tensei_core", "chibaku_tensei_debris", "rinnegan_energy"]
ok = True
tiles = []
for n in names:
    p = os.path.join(d, n + ".png")
    im = Image.open(p)
    arr = np.array(im.convert("RGBA"))
    a = arr[..., 3]
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    transparent = float((a == 0).mean())
    partial = float(((a > 0) & (a < 255)).mean())
    opaque = float((a == 255).mean())
    # halo check: colour of pixels with alpha==0 should not be pure black or pure white
    z = arr[a == 0][:, :3]
    halo_black = float((z.sum(axis=1) == 0).mean()) if len(z) else 0.0
    halo_white = float((z.min(axis=1) == 255).mean()) if len(z) else 0.0
    res = "OK" if (im.mode == "RGBA" and border.max() == 0 and transparent > 0.05 and halo_black < 0.5 and halo_white < 0.5) else "FAIL"
    if res != "OK":
        ok = False
    print(f"{n:28s} {im.size} {im.mode} border_alpha_max={border.max()} transparent={transparent:.2f} "
          f"partial={partial:.2f} opaque={opaque:.2f} halo_black={halo_black:.2f} halo_white={halo_white:.2f} -> {res}")
    tiles.append(im.convert("RGBA"))

# debris sheet frame margin check
sheet = np.array(Image.open(os.path.join(d, "chibaku_tensei_debris.png")).convert("RGBA"))
for i, (ox, oy) in enumerate([(0, 0), (64, 0), (0, 64), (64, 64)]):
    fr = sheet[oy:oy + 64, ox:ox + 64, 3]
    edge = np.concatenate([fr[:3].ravel(), fr[-3:].ravel(), fr[:, :3].ravel(), fr[:, -3:].ravel()])
    cover = float((fr > 0).mean())
    print(f"debris frame {i}: margin_alpha_max={edge.max()} coverage={cover:.2f}")
    if edge.max() != 0:
        ok = False

# contact sheet: each texture on dark gray, mid blue-gray and a bright sky colour
W = 256
sheet_img = Image.new("RGB", (W * len(tiles), W * 3), (0, 0, 0))
bgs = [(28, 28, 36), (110, 120, 140), (140, 190, 235)]
for ci, im in enumerate(tiles):
    im2 = im.resize((W, W), Image.NEAREST) if im.size != (W, W) else im
    if im.size == (128, 128):
        im2 = im.resize((W, W), Image.NEAREST)
    for ri, bg in enumerate(bgs):
        tile = Image.new("RGBA", (W, W), bg + (255,))
        tile.alpha_composite(im2)
        sheet_img.paste(tile.convert("RGB"), (ci * W, ri * W))
sheet_img.save(out)
print("preview:", out)
print("ALL OK" if ok else "SOME CHECKS FAILED")
