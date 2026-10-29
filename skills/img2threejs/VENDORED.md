# Vendored: img2threejs

- Upstream: https://github.com/img2threejs/img2threejs
- Commit: 3e7099e1b7fe93e187e06db4bdbe1e1906c21a28 (2026-10-27)
- License: Apache-2.0 (see `LICENSE` in this folder). Files are copied unmodified; nothing was removed from them.
- Copied: `SKILL.md`, `README.md`, `LICENSE`, `CHANGELOG.md`, `ROADMAP.md`, `grimoire/`, `forge/`, `docs/`, `scripts/`,
  `bin/`, `skills/`, `package.json`. Not copied: `.github/`, `assets/` (sponsor logos), `integrations/`.

## How Android-3D-Model-Forge uses it

img2threejs rebuilds an object from a reference image as procedural Three.js code, gated by staged passes and
agent-vision review in a browser preview. This repository has no browser/Three.js preview in CI and emits GLB
from Blender instead, so its Three.js pipeline is **not** run here. What we take from it:

- **Visual hull** (`forge/stage3_build/visual_hull.py`): carve the shape as the intersection of the reference
  silhouettes. `scripts/hull.py` reimplements this idea in numpy at higher resolution (img2threejs caps the grid
  at 32^3 with three axis views) and adds rounded per-row / per-column cross-sections for limbs.
- **Projected texture** (`forge/stage3_build/bake_projected_texture.py`): colour the surface from the reference
  views. `scripts/gorilla.py` projects the T-pose front/back panels onto the faces that face them.
- **Reference-loop review**: compare renders with the reference after every build (done here from CI previews).

To use img2threejs itself (Claude Code, Codex, OpenCode), install it as its README / `docs/INSTALL.md` describe.
