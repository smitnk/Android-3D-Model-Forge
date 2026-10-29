"""Silhouette carving (visual hull) for character turnaround sheets. Pure numpy, no Blender.

Method from img2threejs (skills/img2threejs/forge/stage3_build/visual_hull.py): a voxel survives only
if it projects onto the figure in every view. img2threejs caps its grid at 32^3 with three axis views;
for a character sheet we carve at ~1 cm and shape the unseen depth explicitly:
  - FRONT mask (T-pose) gives x/z; every row run and every column run gets a rounded (superellipse)
    cross-section, so limbs come out round instead of as extruded slabs;
  - SIDE mask (90 deg view) gives the depth profile y(z) of the body;
  - a limb's depth never exceeds its own thickness seen from the front (arms are as deep as they are tall).
Conventions: masks are bool arrays, row 0 = TOP of the image. Blender axes: x right (character's left),
y depth (-y = front), z up.
"""
import numpy as np


def runs_1d(row):
    """Per-pixel (centre, half_len) of the True run containing each pixel; NaN where False."""
    n = len(row)
    c = np.full(n, np.nan)
    h = np.full(n, np.nan)
    padded = np.concatenate([[False], row, [False]]).astype(np.int8)
    d = np.diff(padded)
    for s, e in zip(np.where(d == 1)[0], np.where(d == -1)[0]):  # run is [s, e)
        c[s:e] = (s + e - 1) / 2.0
        h[s:e] = (e - s) / 2.0
    return c, h


def run_maps(mask):
    """Row-run and column-run centre/half-length maps for a 2-D mask."""
    rc = np.full(mask.shape, np.nan)
    rh = np.full(mask.shape, np.nan)
    cc = np.full(mask.shape, np.nan)
    ch = np.full(mask.shape, np.nan)
    for i in range(mask.shape[0]):
        rc[i], rh[i] = runs_1d(mask[i])
    for j in range(mask.shape[1]):
        cc[:, j], ch[:, j] = runs_1d(mask[:, j])
    return rc, rh, cc, ch


def figure_rows(mask):
    rows = np.where(mask.any(1))[0]
    return rows.min(), rows.max()


def carve(front, side, height_m, voxel, power=2.4, side_facing_left=True):
    """Return (occupancy[x, y, z] bool, origin xyz, voxel) for a figure `height_m` tall.

    front: T-pose front mask; side: profile mask (character's front toward image-left if side_facing_left).
    """
    ft, fb = figure_rows(front)
    s = height_m / (fb - ft + 1)                      # metres per front pixel
    st, sb = figure_rows(side)
    ss = height_m / (sb - st + 1)                     # metres per side pixel
    cols = np.where(front.any(0))[0]
    cx = (cols.min() + cols.max()) / 2.0              # symmetric T-pose: centre of the bounding box
    rc, rh, cc, ch = run_maps(front)

    # side depth profile per side row: front edge, back edge (in side pixels)
    sc_cols = np.where(side.any(0))[0]
    scx = (sc_cols.min() + sc_cols.max()) / 2.0
    s_lo = np.array([np.where(r)[0].min() if r.any() else np.nan for r in side], float)
    s_hi = np.array([np.where(r)[0].max() if r.any() else np.nan for r in side], float)

    nx = int(np.ceil((cols.max() - cols.min() + 1) * s / voxel)) + 2
    nz = int(np.ceil(height_m / voxel)) + 1
    depth_px = np.nanmax(s_hi - s_lo) + 1
    ny = int(np.ceil(depth_px * ss / voxel)) + 2
    x = (np.arange(nx) - nx / 2 + 0.5) * voxel
    y = (np.arange(ny) - ny / 2 + 0.5) * voxel
    z = (np.arange(nz) + 0.5) * voxel
    occ = np.zeros((nx, ny, nz), bool)

    fcol = np.clip(np.round(cx + x / s).astype(int), 0, front.shape[1] - 1)
    x_in = (np.abs(cx + x / s - np.clip(cx + x / s, 0, front.shape[1] - 1)) < 1)
    sign = 1.0 if side_facing_left else -1.0  # image-left = character front = -y
    for k, zk in enumerate(z):
        frow = int(round(fb - zk / s))
        srow = int(round(sb - zk / ss))
        if not (0 <= frow < front.shape[0] and 0 <= srow < side.shape[0]) or np.isnan(s_lo[srow]):
            continue
        fm = front[frow, fcol] & x_in                                     # (nx,)
        if not fm.any():
            continue
        # body depth at this height, metres; side image column -> y (front of character = -y)
        y_a = sign * (s_lo[srow] - scx) * ss
        y_b = sign * (s_hi[srow] - scx) * ss
        yc_body, b_body = (y_a + y_b) / 2, abs(y_b - y_a) / 2 + voxel / 2
        a = rh[frow, fcol] * s                                             # row-run half width
        dx = np.abs(x - (rc[frow, fcol] - cx) * s)
        hcol = ch[frow, fcol] * s                                          # column-run half height
        dz = np.abs(zk - (fb - cc[frow, fcol]) * s)
        b = np.minimum(b_body, hcol * 1.05)                                # limbs: depth ~ thickness
        yc = np.where(hcol * 1.05 < b_body, yc_body * 0.5, yc_body)        # limbs sit near the axis
        with np.errstate(invalid="ignore", divide="ignore"):
            ex = (dx / a)[:, None] ** power
            ez = (dz / hcol)[:, None] ** power
            ey = (np.abs(y[None, :] - yc[:, None]) / b[:, None]) ** power
            inside = fm[:, None] & (ex + ey <= 1.0) & (ez + ey <= 1.0)
        occ[:, :, k] = np.nan_to_num(inside, nan=False).astype(bool)
    origin = np.array([x[0], y[0], z[0]]) - voxel / 2
    return occ, origin, s


def boundary_quads(occ, origin, voxel):
    """Closed quad surface between occupied and empty voxels: (vertices Nx3, quads Mx4)."""
    nx, ny, nz = occ.shape
    pad = np.pad(occ, 1)
    quads = []
    # corner offsets per face, wound so normals point out (same table as img2threejs _boundary_surface)
    table = {
        (0, 1): ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)),
        (0, -1): ((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)),
        (1, 1): ((0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)),
        (1, -1): ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)),
        (2, 1): ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)),
        (2, -1): ((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)),
    }
    for (axis, d), offs in table.items():
        nb = np.roll(pad, -d, axis=axis)[1:-1, 1:-1, 1:-1]
        idx = np.argwhere(occ & ~nb)
        if len(idx):
            quads.append(np.stack([idx + np.array(o) for o in offs], axis=1))   # (n,4,3) corners
    corners = np.concatenate(quads)                                            # (M,4,3)
    flat = corners.reshape(-1, 3)
    key = (flat[:, 0] * (ny + 1) + flat[:, 1]) * (nz + 1) + flat[:, 2]
    uniq, inv = np.unique(key, return_inverse=True)
    verts = np.zeros((len(uniq), 3))
    verts[inv] = flat
    return origin + verts * voxel, inv.reshape(-1, 4)
