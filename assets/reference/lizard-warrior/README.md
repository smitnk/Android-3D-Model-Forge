# Lizard Warrior reference (owner-supplied)

Cropped from the owner's 12-view turnaround sheet. Alpha = figure mask taken from the sheet's light wireframe
row (floor removed); RGB = the textured row aligned to it (-484 px), drawn outline replaced by interior colour,
background filled with the nearest figure colour.
- `front.png` (0°) — silhouette (hanging arms are removed in code) + texture, including the drawn arms.
- `side.png` (90°) — depth profile; the dagger in front of the thigh is cut out.
- `back.png` (180°) — texture for back-facing surfaces.
- `views/` (0°–330° in 30° steps) — made by `scripts/prep_turnaround.py`; used by `scripts/lizard_refined.py` to trim
  the template with all 12 silhouettes and to texture every side from the drawing. `views.json` has the scale/rows.
- `triposr.glb` — the TripoSR template (from `assets/ai-input/lizard-warrior.png`, upright, 1.8 m, linear vertex colours).
