"""Cut a turnaround sheet (textured row + light wireframe row) into per-angle reference views.

Run once on a PC/cloud shell with Pillow + numpy (not inside Blender); the outputs are committed.
For each angle: alpha = figure mask from the WIREFRAME row (connected shape grown from the panel centre,
floor removed, holes filled); RGB = the TEXTURED row aligned to it by gradient correlation, with the
drawn outline and the background replaced by nearby figure colour (clean texture edges).
Writes <out>/vNNN.png and <out>/views.json (angle, metres-per-pixel, axis column, bottom row).

Usage: python3 scripts/prep_turnaround.py SHEET.png OUT_DIR --height 1.9 \
          --wire-rows 540 878 --floor-row 337 --centres 77,210,330,...  (one per 30 degrees from 0)
"""
import argparse
import json
import os
from collections import deque

import numpy as np
from PIL import Image


def grow(mask, seeds):
    h, w = mask.shape
    out = np.zeros_like(mask)
    q = deque(s for s in seeds if mask[s])
    for s in q:
        out[s] = True
    while q:
        y, x = q.popleft()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not out[yy, xx]:
                    out[yy, xx] = True
                    q.append((yy, xx))
    return out


def fill_holes(m):
    return ~grow(~m, [(0, x) for x in range(m.shape[1])] + [(m.shape[0] - 1, x) for x in range(m.shape[1])]
                 + [(y, 0) for y in range(m.shape[0])] + [(y, m.shape[1] - 1) for y in range(m.shape[0])])


def shift(a, d):
    return np.roll(a, d, (0, 1))


def erode(m, n):
    for _ in range(n):
        m = m & shift(m, (1, 0)) & shift(m, (-1, 0)) & shift(m, (0, 1)) & shift(m, (0, -1))
    return m


def spread_colour(rgb, known, steps):
    rgb, known = rgb.copy(), known.copy()
    for _ in range(steps):
        acc, cnt = np.zeros_like(rgb), np.zeros(known.shape)
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = shift(known, d)
            acc += shift(rgb, d) * k[..., None]
            cnt += k
        new = (~known) & (cnt > 0)
        rgb[new] = acc[new] / cnt[new][:, None]
        known |= new
    return rgb


def hip_centre(mask):
    rows = np.where(mask.any(1))[0]
    t, b = rows.min(), rows.max()
    band = range(int(b - 0.55 * (b - t)), int(b - 0.45 * (b - t)))  # pelvis height: legs/arms excluded
    return float(np.median([np.where(mask[r])[0].mean() for r in band]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("sheet")
    p.add_argument("out")
    p.add_argument("--height", type=float, required=True, help="real height of the figure, metres")
    p.add_argument("--wire-rows", type=int, nargs=2, required=True)
    p.add_argument("--floor-row", type=int, required=True, help="first floor row, relative to wire-rows[0]")
    p.add_argument("--centres", required=True, help="comma list of panel centre columns, one per 30 degrees")
    p.add_argument("--half-width", type=int, default=95)
    p.add_argument("--tex-dy", type=int, nargs=2, default=(-500, -460), help="search range, textured row offset")
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    im = np.asarray(Image.open(a.sheet).convert("RGB")).astype(float)
    g = im.sum(2)
    y0, y1 = a.wire_rows
    views = []
    for i, cx in enumerate(int(c) for c in a.centres.split(",")):
        x0, x1 = max(0, cx - a.half_width), min(im.shape[1], cx + a.half_width)
        wire = g[y0:y1, x0:x1] > 200
        wire[a.floor_row:] = False
        fig = fill_holes(grow(wire, [(y, cx - x0) for y in range(40, a.floor_row - 40, 4)]))
        gy, gx = np.gradient(g[y0:y1, x0:x1])
        wgrad = np.hypot(gx, gy).ravel()
        best = (-2, 0, 0)
        for dy in range(*a.tex_dy):
            for dx in range(-4, 5):
                if x0 + dx < 0 or x1 + dx > im.shape[1]:
                    continue
                ty, tx = np.gradient(g[y0 + dy:y1 + dy, x0 + dx:x1 + dx])
                c = np.corrcoef(wgrad, np.hypot(tx, ty).ravel())[0, 1]
                if c > best[0]:
                    best = (c, dy, dx)
        _, dy, dx = best
        tex = im[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
        rgb = spread_colour(tex, erode(fig, 2), 40)
        Image.fromarray(np.dstack([rgb.clip(0, 255), fig * 255]).astype(np.uint8), "RGBA").save(
            os.path.join(a.out, f"v{30 * i:03d}.png"))
        rows = np.where(fig.any(1))[0]
        views.append({"angle": 30 * i, "file": f"v{30 * i:03d}.png", "axis_col": hip_centre(fig),
                      "bottom_row": int(rows.max()), "top_row": int(rows.min()),
                      "tex_offset": [dy, dx], "tex_corr": round(float(best[0]), 3)})
        print(views[-1])
    s = a.height / np.median([v["bottom_row"] - v["top_row"] + 1 for v in views])
    for v in views:
        v["m_per_px"] = s
    with open(os.path.join(a.out, "views.json"), "w") as f:
        json.dump({"height_m": a.height, "views": views}, f, indent=1)


if __name__ == "__main__":
    main()
