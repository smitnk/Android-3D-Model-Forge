# Modeling guidelines

## Units and axes
- Metres, Blender Z-up. Ground plane is z = 0; the character is centred on x = 0, y = 0.
- Character faces **-Y** in Blender. The glTF exporter (`export_yup=True`) turns this into +Z front, Y-up,
  which is what glTF viewers and engines expect.
- Character's left = **+X**. Sided parts use `_L` / `_R`; bones use `.L` / `.R`.

## Building parts
- Use `part(name, kind, size, loc, mat, bone, rot=..., taper=..., bevel=..., subsurf=..., solidify=..., cut=...)`.
- `size` is the full extent of the unit primitive along x, y, z (a sphere of size (0.5, 0.5, 0.5) has 0.25 m radius).
- Rotation is applied before translation; a cylinder rotated `(0, 90, 0)` lies along X (used for T-pose arms).
- `bevel` (metres) + `subsurf=1` turns hard primitives into soft cartoon shapes.
- `cut(v)` deletes vertices of the unit primitive (coordinates in -0.5..0.5) — used for the hair shell;
  combine with `solidify` so the shell has thickness and no open single-sided surfaces.

## Topology and quality
- Keep parts closed (watertight) where possible; avoid single-sided planes.
- Small overlaps between parts at joints are fine (they hide seams). Coplanar overlapping faces are not
  (z-fighting): facial features must protrude 1–15 mm.
- Keep each part's segment count modest (16–32). Target < 100k triangles total.
- All parts smooth-shaded.

## Chibi proportions (reference values)
| Region | z range (m) |
|---|---|
| Shoes | 0.00 – 0.095 |
| Shins | 0.07 – 0.26 |
| Shorts | 0.22 – 0.45 |
| Torso | 0.43 – 0.70 |
| Shoulder line | 0.645 |
| Head | 0.73 – 1.23 (≈38% of height) |
| Hair top | ≈ 1.33 |

## T-pose (mandatory for humanoids)
Arms horizontal at shoulder height along ±X, straight; legs vertical and parallel at x = ±0.085;
feet along -Y. Never expose a pose parameter on a humanoid generator. Posing belongs in the rig,
not in the rest geometry.

## Colours and materials
One Principled BSDF material per part, colour from `#RRGGBB` (converted to linear). Reuse materials
across parts (all skin parts share `Skin`). No image textures in the first milestone.
