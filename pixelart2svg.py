#!/usr/bin/env python3
"""pixelart2svg: turn pixel art (PNG) into a pixel-perfect vector SVG, one <path> per colour.

Usage:
  python3 pixelart2svg.py sprite.png                  -> sprite.svg
  python3 pixelart2svg.py sprite.png out.svg --scale 13
  python3 pixelart2svg.py upscaled.png --cell 13      (PNG already enlarged in NxN blocks)
  python3 pixelart2svg.py sprite.png --disjoint       (non-overlapping shapes, see below)

Options:
  --scale N     Output size = N px per sprite pixel (sets the SVG width/height; the viewBox stays in sprite
                pixels, so 1 SVG unit = 1 sprite pixel). Default: 1
  --cell N      The PNG is an upscaled sprite made of NxN blocks: the centre of each block is sampled.
  --disjoint    Each shape contains ONLY its own pixels (easiest to edit by hand, but a hairline gap may show
                between colours when scaled with anti-aliasing). The default is "underlay" mode: each shape also
                covers the pixels of the shapes painted on top of it, so there are no seams. Visually identical.
                Sprites with semi-transparent pixels switch to --disjoint automatically.
  --no-verify   Skip the check of the SVG against the source PNG.

Requirements: Python 3.8+, Pillow, numpy   (pip install -r requirements.txt)
"""
import sys, argparse, collections
import numpy as np
from PIL import Image, ImageDraw

def trace(mask):
    """bool mask (h,w) -> list of closed loops [(x,y)...] on integer pixel-corner coordinates."""
    h, w = mask.shape
    P = np.pad(mask, 1)
    nxt = collections.defaultdict(list)

    for y, x in zip(*np.nonzero(mask)):                      # directed edges, interior on the right
        if not P[y, x+1]:   nxt[(x, y)].append((x+1, y))
        if not P[y+1, x+2]: nxt[(x+1, y)].append((x+1, y+1))
        if not P[y+2, x+1]: nxt[(x+1, y+1)].append((x, y+1))
        if not P[y+1, x]:   nxt[(x, y+1)].append((x, y))
    loops = []

    while nxt:
        start = next(iter(nxt)); cur = start; path = [start]; prev = None
        while True:
            outs = nxt[cur]
            if len(outs) > 1 and prev is not None:           # vertex with 2 exits (diagonal pixels): turn right so they stay separate
                outs.sort(key=lambda o: prev[0]*(o[1]-cur[1]) - prev[1]*(o[0]-cur[0]), reverse=True)
            n = outs.pop(0)
            if not outs: del nxt[cur]
            prev = (n[0]-cur[0], n[1]-cur[1]); cur = n
            if cur == start: break
            path.append(cur)
        L = len(path)                                         # drop collinear points
        loops.append([path[i] for i in range(L)
                      if (path[i][0]-path[i-1][0])*(path[(i+1) % L][1]-path[i][1]) -
                         (path[i][1]-path[i-1][1])*(path[(i+1) % L][0]-path[i][0]) != 0])
    return loops

def load(png, cell):
    a = np.asarray(Image.open(png).convert("RGBA"))
    if cell > 1:
        a = a[cell//2::cell, cell//2::cell]
    return a

def layers_of(a, disjoint):
    h, w = a.shape[:2]
    flat = [tuple(p) for p in a.reshape(-1, 4)]
    cnt = collections.Counter(p for p in flat if p[3] > 0)
    semi = any(p[3] < 255 for p in cnt)
    if semi and not disjoint:
        print("warning: semi-transparent pixels found -> using --disjoint (underlay would blend them)", file=sys.stderr)
        disjoint = True
    order = [c for c, _ in cnt.most_common()]                # largest area at the bottom
    key = np.zeros((h, w), int) - 1
    idx = {c: i for i, c in enumerate(order)}
    for y in range(h):
        for x in range(w):
            if a[y, x, 3] > 0: key[y, x] = idx[tuple(a[y, x])]
    res = []
    for i, c in enumerate(order):
        mask = (key == i) if disjoint else (key >= i)
        res.append((c, trace(mask)))
    return res, disjoint

def to_svg(a, layers, scale, disjoint):
    h, w = a.shape[:2]
    def d_of(loops): return " ".join("M" + " L".join(f"{x},{y}" for x, y in lp) + "Z" for lp in loops)
    ns = 'xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"'
    body = []
    for (r, g, b, al), loops in layers:
        hexc = "#%02x%02x%02x" % (r, g, b)
        op = "" if al == 255 else f' fill-opacity="{al/255:.3f}"'
        body.append(f'    <path id="c-{hexc[1:]}{"" if al==255 else "-a%d"%al}" inkscape:label="{hexc}{"" if al==255 else " a=%d"%al}" fill="{hexc}"{op} fill-rule="evenodd" d="{d_of(loops)}" />')
    mode = "disjoint shapes" if disjoint else "underlay (each shape also covers the pixels of the shapes above it; no seams)"
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n<svg {ns} width="{w*scale}" height="{h*scale}" viewBox="0 0 {w} {h}" version="1.1">\n'
            f'  <!-- pixelart2svg: 1 unit = 1 pixel ({w}x{h}); one shape per colour, largest area first; mode: {mode} -->\n'
            f'  <g id="sprite" inkscape:label="sprite" inkscape:groupmode="layer">\n' + "\n".join(body) + "\n  </g>\n</svg>\n")

def verify(a, layers):
    h, w = a.shape[:2]; K = 8
    canvas = np.zeros((h*K, w*K, 4), int)
    for (r, g, b, al), loops in layers:
        m = np.zeros((h*K, w*K), bool)
        for lp in loops:
            t = Image.new("1", (w*K, h*K), 0); ImageDraw.Draw(t).polygon([(x*K, y*K) for x, y in lp], fill=1); m ^= np.asarray(t, bool)
        canvas[m] = (r, g, b, al)                            # last painted wins
    cen = canvas[K//2::K, K//2::K]
    ref = a.astype(int).copy(); ref[ref[..., 3] == 0] = 0
    return int((np.abs(cen - ref).sum(axis=2) > 0).sum()), w*h

def main():
    ap = argparse.ArgumentParser()

    ap.add_argument("png"); ap.add_argument("svg", nargs="?")
    ap.add_argument("--scale", type=int, default=1); ap.add_argument("--cell", type=int, default=1)
    ap.add_argument("--disjoint", action="store_true"); ap.add_argument("--no-verify", action="store_true")
    o = ap.parse_args()
    a = load(o.png, o.cell); layers, disj = layers_of(a, o.disjoint)
    out = o.svg or o.png.rsplit(".", 1)[0] + ".svg"
    open(out, "w", encoding="utf-8").write(to_svg(a, layers, o.scale, disj))
    print(f"{out}: {a.shape[1]}x{a.shape[0]} px, {len(layers)} colours/shapes")
    if not o.no_verify:
        bad, tot = verify(a, layers)
        print(f"verification: {bad} of {tot} pixels differ" + (" -> PIXEL-PERFECT" if bad == 0 else " -> CHECK THE RESULT"))

if __name__ == "__main__":
    main()
