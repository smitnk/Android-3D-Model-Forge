# Vendored: blender-kiln

- Upstream: https://github.com/elithril/blender-kiln
- Commit: 4b170be2756d87d0d5a1b8e7aebef5fd61c7f771 (2026-10-12)
- License: MIT, Copyright (c) 2026 Nicolas Dolphens (see `LICENSE` in this folder)
- Copied: `SKILL.md`, `README.md`, `LICENSE`, `references/`, `tools/`. Not copied: `bench/`, `docs/`, `site/`,
  `examples/`, `plugin/`, logo (large or not needed). Files are unmodified.

## How Android-3D-Model-Forge uses it

blender-kiln is written for an interactive session with Blender + the Blender MCP add-on (port 9876).
This repository runs Blender headless in GitHub Actions instead, so the MCP-driven steps are **not** run.
What we apply from it:

- `references/reference-fidelity.md` — inventory every visible detail before modeling, measure proportions
  from the reference image's silhouette (not by eye), make every part enter the part it joins,
  one material per physical material. Used for the `gorilla` generator (`scripts/gorilla.py`).
- `references/characters.md` — T-pose requirements and rigging patterns (consistent with our T-pose policy).
- `references/validation-checklist.md`, `export-targets.md` — GLB export and validation expectations.
- `tools/*.py` are headless Blender scripts and can be run in CI the same way as our scripts
  (`blender -b --factory-startup --python-exit-code 1 --python skills/blender-kiln/tools/<tool>.py -- ...`).

To use blender-kiln interactively on a PC with Blender, install it as its README describes.
