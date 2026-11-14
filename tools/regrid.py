#!/usr/bin/env python3
"""Re-grid every sprite onto ONE chunk pitch (the pixel-perfect grid).

Grid: 1 chunk = 1024/171 stage-px (~5.99). Target grid per sprite comes from
its tuned display box (slot w * scx, height from current grid aspect * scy),
so display size and position stay as tuned — only the internal pixel grid is
made uniform across the whole scene.

Per sprite: ppa raw -> crop alpha bbox -> NEAREST-resize grid to exact target
-> despeckle -> lossless webp over assets/<name>-cut.webp.

Sources: ../word-rain-src (parent vault). Assets: ../assets (deployed repo).
"""
import re
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

from PIL import Image

GRID = 171
CHUNK_ST = 1024 / GRID
TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
ASSETS = ROOT / "assets"
SRC = ROOT.parent / "word-rain-src"


def parse_scene():
    src = (ROOT / "index.html").read_text()
    block = re.search(r"const SCENE = \{(.*?)\n\};", src, re.S).group(1)
    scene = {}
    for em in re.finditer(r'"([A-Za-z0-9_-]+)":\{([^}]*)\}', block):
        g = lambda k: float(re.search(k + r":(-?[\d.]+)", em.group(2)).group(1))
        scene[em.group(1)] = dict(w=g("w"), scx=g("scx"), scy=g("scy"))
    scene["shell-base"] = dict(w=1024.0, scx=1.0, scy=1.0)
    return scene


def content_bbox(im):
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    xs, ys = [], []
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b, a = px[x, y]
            if a > 8 and not (r > 240 and g > 240 and b > 240):
                xs.append(x)
                ys.append(y)
    return (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1) if xs else (w, h)


def despeckle(im):
    """Replace 1px islands whose 8 neighbours are all one other colour."""
    px = im.load()
    w, h = im.size
    for _ in range(2):
        changed = False
        for y in range(h):
            for x in range(w):
                c = px[x, y]
                if c[3] == 0:
                    continue
                neigh = []
                edge = False
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            neigh.append(px[nx, ny])
                        else:
                            edge = True
                if edge or len(neigh) < 8:
                    continue
                if all(n == neigh[0] and n != c for n in neigh):
                    px[x, y] = neigh[0]
                    changed = True
        if not changed:
            break
    return im


def process(item):
    name, s = item
    old = Image.open(ASSETS / f"{name}-cut.webp")
    ow, oh = old.size
    wv = s["w"] * abs(s["scx"])
    hv = s["w"] * (oh / ow) * s["scy"]
    tw = max(2, round(wv / CHUNK_ST))
    th = max(2, round(hv / CHUNK_ST))
    raw_path = SRC / f"{name}.png"
    if not raw_path.exists():
        return f"{name:14} MISSING raw {raw_path}"
    cw, ch = content_bbox(Image.open(raw_path))
    best = None
    for d in (0, -1, 1, -2, 2):
        pw = max(1, round(cw / tw) + d)
        r = subprocess.run(
            ["ppa", str(raw_path), "-o", "/tmp/regrid_try.png", "-t",
             "-u", "4", "-w", str(pw)],
            capture_output=True)
        if r.returncode:
            continue
        out = Image.open("/tmp/regrid_try.png").convert("RGBA")
        bb = out.getbbox()
        if bb:
            out = out.crop(bb)
        diff = abs(out.width - tw) + abs(out.height - th)
        if best is None or diff < best[0]:
            best = (diff, out)
        if out.size == (tw, th):
            break
    out = best[1]
    exact = out.size == (tw, th)
    if not exact:
        out = out.resize((tw, th), Image.NEAREST)
    out = despeckle(out)
    out.save(ASSETS / f"{name}-cut.webp", "WEBP", lossless=True)
    tag = "exact" if exact else f"resized from {best[1].size}"
    return (f"{name:14} grid {tw:3}x{th:<3} chunk {wv / tw:5.2f} "
            f"stage-px  was {ow}x{oh}  [{tag}]")


def main():
    scene = parse_scene()
    names = list(scene.items())
    only = set(sys.argv[1:])
    if only:
        names = [(n, s) for n, s in names if n in only]
    with Pool(3) as p:
        for line in p.imap_unordered(process, names):
            print(line, flush=True)
    print("done")


if __name__ == "__main__":
    main()
