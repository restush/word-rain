#!/usr/bin/env python3
"""bake_scene.py - bake slot transforms into sprites (Restu, 2026-11-15).

Room is locked -> each sprite is pre-rendered at its FINAL displayed geometry:
scale (scx/scy), skewX/skewY, rotate, flip baked in; runtime = plain blit at the
recorded AABB. Sources = before-ppa originals (true art, shadows intact) in
word-rain-src/originals/. Resample = LANCZOS/BICUBIC (matches the tuner's approved
CSS smoothness). Target density = display size x REF (device headroom).

Kept as-is (no bake): shell-base (full frame, drawn 0,0,size,size) and any layer
whose display >= source (wall skins at ~1:1). Everything smaller gets baked.

Writes: assets/<name>-cut.webp (baked) + const BAKED block in index.html
(name -> [x, y, w, h] in 1024-stage coords). Re-run after any slot move.

Usage:  python3 tools/bake_scene.py
"""
import json
import math
import re
from pathlib import Path

from PIL import Image

TOOLS = Path(__file__).resolve().parent
GAME = TOOLS.parent
SRC = GAME.parent / "word-rain-src" / "originals"
REF = 1.2  # device px per stage px (phones 1.08, big phones 1.19)
Q = 89
KEEP = {"shell-base"}  # full frame, drawn as-is


def bake(name, s):
    im = Image.open(SRC / f"{name}-cut.webp").convert("RGBA")
    ar = im.height / im.width
    w0, h0 = s["w"], s["w"] * ar
    tw, th = w0 * REF, h0 * REF
    if tw >= im.width and th >= im.height and not (s["rot"] or s["skx"] or s["sky"]):
        return None  # no win: keep original + runtime exact-draw
    raster = im.resize((max(2, round(tw)), max(2, round(th))), Image.LANCZOS)
    if s["flip"]:
        raster = raster.transpose(Image.FLIP_LEFT_RIGHT)
    W, H = raster.size
    rot = math.radians(s["rot"])
    kx, ky = math.tan(math.radians(s["skx"])), math.tan(math.radians(s["sky"]))
    sx, sy = s["scx"], s["scy"]
    # CSS chain: rotate -> skewX -> skewY -> scale  (point sees scale first)
    R = (math.cos(rot), -math.sin(rot), math.sin(rot), math.cos(rot))
    Kx = (1.0, kx, 0.0, 1.0)
    Ky = (1.0, 0.0, ky, 1.0)
    S = (sx, 0.0, 0.0, sy)

    def mul(A, B):  # 2x2 row-major (a,b,c,d)
        return (A[0] * B[0] + A[1] * B[2], A[0] * B[1] + A[1] * B[3],
                A[2] * B[0] + A[3] * B[2], A[2] * B[1] + A[3] * B[3])

    M = mul(R, mul(Kx, mul(Ky, S)))
    det = M[0] * M[3] - M[1] * M[2]
    Mi = (M[3] / det, -M[1] / det, -M[2] / det, M[0] / det)
    corners = [(-W / 2, -H / 2), (W / 2, -H / 2), (W / 2, H / 2), (-W / 2, H / 2)]
    proj = [(M[0] * x + M[1] * y, M[2] * x + M[3] * y) for x, y in corners]
    xs = [p[0] for p in proj]
    ys = [p[1] for p in proj]
    ax, ay = min(xs), min(ys)
    out_w, out_h = math.ceil(max(xs) - ax) + 2, math.ceil(max(ys) - ay) + 2
    # PIL affine: in = Mi * (out + aabbmin - center) + center
    cx, cy = W / 2, H / 2
    ox, oy = ax + 1, ay + 1  # +1: 1px pad; rel_s is center-relative (no c shift!)
    coeffs = (Mi[0], Mi[1], Mi[0] * ox + Mi[1] * oy + cx,
              Mi[2], Mi[3], Mi[2] * ox + Mi[3] * oy + cy)
    out = raster.transform((out_w, out_h), Image.AFFINE, coeffs, resample=Image.BICUBIC)
    out.save(GAME / "assets" / f"{name}-cut.webp", "WEBP", quality=Q)
    # stage-space AABB (floats, 0.1 precision)
    return [round(s["x"] + w0 / 2 + (ax + 1) / REF, 1), round(s["y"] + h0 / 2 + (ay + 1) / REF, 1),
            round(out_w / REF, 1), round(out_h / REF, 1)]


def main():
    slots = json.load(open(TOOLS / "slots.json"))
    baked = {}
    tot_before = tot_after = 0
    for name, s in slots.items():
        if name in KEEP:
            continue
        b = Path(GAME / "assets" / f"{name}-cut.webp")
        before = b.stat().st_size
        r = bake(name, s)
        after = b.stat().st_size
        if r is None:
            tot_before += before
            tot_after += after
            print(f"{name:14} keep original ({before/1024:.1f}K, display >= source)")
            continue
        baked[name] = r
        tot_before += before
        tot_after += after
        im = Image.open(b)
        print(f"{name:14} baked {im.size[0]}x{im.size[1]}  {before/1024:6.1f}K -> {after/1024:6.1f}K")
    print(f"\ntotal baked set: {tot_before/1024:.1f}K -> {tot_after/1024:.1f}K  ({len(baked)} baked)")
    block = "const BAKED = " + json.dumps(baked, separators=(",", ":")) + "; /* baked AABBs, stage coords (bake_scene.py) */"
    idx = GAME / "index.html"
    src = idx.read_text()
    if "const BAKED = " in src:
        src = re.sub(r"const BAKED = .*?/\* baked AABBs[^*]*\*/", block, src, count=1)
    else:
        src = src.replace("const SPRITES = {};", block + "\nconst SPRITES = {};")
    idx.write_text(src)
    print("index.html BAKED block updated")


if __name__ == "__main__":
    main()
