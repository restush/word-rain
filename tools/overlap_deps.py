#!/usr/bin/env python3
"""overlap_deps.py v2 - shop UNLOCK-dependency calculator (Restu's rule, 2026-11-15).

RULE: "you cannot buy x if x is overlapped with old or new object" -> every overlap
resolves as ONE of:
  replaces : x swaps the same-spot old layer (declared, kept as-is)
  requires : UNLOCK CHAIN - old o sits on x's spot -> x.requires += the item that
             REPLACES o (buy it first -> o hidden -> spot free). If the replacement's
             own footprint still overlaps x: WARN (chain broken, Restu decides).
             new/both y overlaps x -> smaller footprint requires the larger one's item
             (composition anchors: curtains->fix-window, tv->whiteboard).
  WARN     : both-group (always-visible, e.g. desks) or broken chains -> manual review.
No clears. Skins (old-wall, wall-paint, old-floor, floor-tiles) are SURFACES:
never blockers, their shop rows keep replaces only.

Geometry: rendered rect = (x, y, w*scx, w*(ch/cw)*scy), rot/skx/sky-aware AABB
(tuner CSS semantics). Overlap = inter/min(area) >= TOL.

Usage:  python3 tools/overlap_deps.py [slots.json]   (default tools/slots.json)
Prints pair report + proposed shop fields; writes tools/shop_deps.json.
"""
import json
import math
import re
import sys
from pathlib import Path

from PIL import Image

TOOLS = Path(__file__).resolve().parent
GAME = TOOLS.parent
TOL = 0.20
SKINS = {"old-wall", "wall-paint", "old-floor", "floor-tiles"}


def rendered_rect(name, s, aspects):
    ar = aspects[name]  # h/w
    w = s["w"] * s["scx"]
    h = s["w"] * ar * s["scy"]
    cx, cy = s["x"] + s["w"] / 2, s["y"] + s["w"] * ar / 2
    rot = math.radians(s["rot"])
    kx = math.tan(math.radians(s["skx"]))
    ky = math.tan(math.radians(s["sky"]))
    pts = []
    for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        x1, y1 = dx, dy + ky * dx          # skewY
        x2, y2 = x1 + kx * y1, y1          # skewX
        xr = x2 * math.cos(rot) - y2 * math.sin(rot)
        yr = x2 * math.sin(rot) + y2 * math.cos(rot)
        pts.append((cx + xr, cy + yr))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def area(r):
    return max(0.0, r[2] - r[0]) * max(0.0, r[3] - r[1])


def inter(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def main():
    slots_path = Path(sys.argv[1]) if len(sys.argv) > 1 else TOOLS / "slots.json"
    slots = json.load(open(slots_path))
    aspects = {n: Image.open(GAME / "assets" / f"{n}-cut.webp").size for n in slots}
    aspects = {n: sz[1] / sz[0] for n, sz in aspects.items()}
    rects = {n: rendered_rect(n, s, aspects) for n, s in slots.items()}

    src = (GAME / "index.html").read_text()
    shop_src = re.search(r"const SHOP = \[(.*?)\n\];", src, re.S).group(1)
    items = []
    for m in re.finditer(r'\{id:"([^"]+)",layer:"([^"]+)",name:"([^"]+)",price:(\d+),'
                         r'replaces:\[([^\]]*)\],requires:\[([^\]]*)\],clears:\[([^\]]*)\]\}', shop_src):
        ids, layer, nm, price, rep, req, clr = m.groups()
        g = lambda t: [q.strip().strip('"') for q in t.split(",") if q.strip()]
        items.append({"id": ids, "layer": layer, "name": nm, "price": int(price), "replaces": g(rep)})
    item_by_layer = {it["layer"]: it["id"] for it in items}
    replace_of = {r: it["id"] for it in items for r in it["replaces"]}
    layer_of_item = {it["id"]: it["layer"] for it in items}

    deps = {it["id"]: {"replaces": it["replaces"], "requires": [], "clears": []} for it in items}
    warns = []
    print(f"{len(slots)} layers, {len(items)} shop items, TOL={TOL:.0%}, skins excluded: {sorted(SKINS)}")
    objs = [n for n in slots if n not in SKINS]
    for a in objs:
        for b in objs:
            if a >= b:
                continue
            ov = inter(rects[a], rects[b])
            if ov <= 0:
                continue
            cov = ov / max(1e-6, min(area(rects[a]), area(rects[b])))
            tag = f"{a} x {b}: {cov:.0%}"
            if cov < TOL:
                print(f"  . {tag} (below tol)")
                continue
            it_a, it_b = item_by_layer.get(a), item_by_layer.get(b)
            for x, o, itx in ((a, b, it_a), (b, a, it_b)):
                if not itx:
                    continue
                rep = next((it for it in items if it["id"] == itx), None)
                if o in rep["replaces"]:
                    print(f"  R {tag} (replaces: {itx} <- {o})")
                    break
            else:
                pair_done = False
                for x, o, itx in ((a, b, it_a), (b, a, it_b)):
                    if not itx or pair_done:
                        continue
                    if slots[o]["group"] == "before":
                        r = replace_of.get(o)
                        if not r:
                            if o not in deps[itx]["clears"]:
                                deps[itx]["clears"].append(o)
                            print(f"  C {tag} -> {itx}.clears += {o} (no replacement exists)")
                            pair_done = True
                        elif inter(rects[x], rects[layer_of_item[r]]) >= 0.8 * area(rects[x]):
                            warns.append(f"WARN {tag}: {itx} would hide under replacement {r} - manual")
                            pair_done = True
                        elif inter(rects[x], rects[layer_of_item[r]]) > 0.1 * area(rects[x]):
                            if r not in deps[itx]["requires"]:
                                deps[itx]["requires"].append(r)
                            print(f"  Q {tag} -> {itx}.requires += {r} (compose with {o}'s replacement)")
                            pair_done = True
                        elif r not in deps[itx]["requires"]:
                            deps[itx]["requires"].append(r)
                            print(f"  Q {tag} -> {itx}.requires += {r} (free {o}'s spot first)")
                            pair_done = True
                if not pair_done and it_a and it_b:
                    if "both" in (slots[a]["group"], slots[b]["group"]):
                        warns.append(f"WARN {tag}: always-visible depth overlap - manual review")
                    else:
                        small, big = (it_a, it_b) if area(rects[a]) < area(rects[b]) else (it_b, it_a)
                        if big not in deps[small]["requires"]:
                            deps[small]["requires"].append(big)
                        print(f"  Q {tag} -> {small}.requires += {big} (smaller composes with larger)")
                elif not pair_done:
                    both = it_a is None and it_b is None or "both" in (slots[a]["group"], slots[b]["group"])
                    print(f"  I {tag} (depth/by-design overlap, no dependency)" if both else f"  ? {tag} (no shop item on either side)")

    # cycle check on requires graph
    def cyc(n, stack):
        for m in deps[n]["requires"]:
            if m in stack or (m in deps and cyc(m, stack | {m})):
                return True
        return False
    for n in deps:
        if cyc(n, {n}):
            warns.append(f"WARN requires cycle involving {n}")

    for w in warns:
        print(" ", w)
    out = TOOLS / "shop_deps.json"
    out.write_text(json.dumps(deps, indent=1))
    print(f"\nwrote {out}")
    for iid, d in deps.items():
        print(f'  {iid:15} replaces:{d["replaces"]} requires:{d["requires"]} clears:{d["clears"]}')


if __name__ == "__main__":
    main()
