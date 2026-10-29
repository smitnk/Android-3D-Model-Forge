---
name: android-3d-model-forge
description: Generate real, validated 3D models (GLB, optional BLEND) with Blender Python running headless in GitHub Actions, operable from a phone browser. Use when asked to create, modify, export, validate or publish procedural 3D characters or props in the Android-3D-Model-Forge repository, or to add a new procedural model generator. Humanoids are always built in a verified T-pose.
license: MIT
compatibility: Requires a GitHub repository with Actions enabled (ubuntu-24.04 runner, no GPU). Blender 4.2.3 LTS is downloaded by the workflow. Local runs need Blender 4.2.x.
---

# Android-3D-Model-Forge

Procedural 3D asset generation with Blender's Python API (`bpy`), executed in the cloud by
GitHub Actions. No local Blender, PC, API key, MCP server or paid service is needed.

**What works today:** a deterministic, rigged chibi humanoid generator (`chibi_humanoid`)
with colour options, GLB + BLEND export, Cycles CPU preview renders, and automated
validation (container, geometry, materials, scale, grounding, symmetry, T-pose, skeleton).

**What does not exist yet:** image-to-3D or AI reconstruction, creatures, props, clothing
variants, smooth (blended) joint weights. Never claim these work until implemented and tested.

## Repository map

| Path | Role |
|---|---|
| `scripts/generate_model.py` | Builds the character in Blender, rigs it, runs self-checks, exports |
| `scripts/export_model.py` | GLB/BLEND export and preview rendering helpers |
| `scripts/validate_model.py` | Re-imports the GLB in a clean scene and runs all checks; exit 1 on failure |
| `scripts/glb_inspect.py` | Pure-Python GLB parser (no Blender) |
| `scripts/make_report.py` | Builds `REPORT.md` from the JSON outputs |
| `.github/workflows/generate-model.yml` | Downloads pinned Blender, generates, validates, uploads, publishes |
| `.github/workflows/validate-model.yml` | Fast checks without Blender |
| `references/` | Modeling and export guidelines (read before changing geometry) |

## Running from the GitHub website (phone friendly)

1. Open the repository → **Actions** tab → **Generate 3D Model** (left list; on mobile tap "All workflows").
2. Tap **Run workflow**, keep defaults or change name/colours, optionally tick **publish**, tap the green **Run workflow**.
3. Wait (~3–6 min first run, faster once Blender is cached). Open the run; the **Summary** shows the validation report.
4. Scroll to **Artifacts** → tap `model-<number>` to download a ZIP containing `.glb`, `.blend`, previews and reports.
5. On Android, open the `.glb` from the ZIP with any glTF viewer (e.g. a 3D viewer app or an online glTF viewer in the browser).

Artifacts expire after 30 days. Runs with **publish** (and every push to `main` that touches
`scripts/`) upload to the permanent `model-latest` Release and commit previews to `docs/preview/`.

## Running locally (optional, for agents with Blender 4.2)

```bash
blender -b --factory-startup --python-exit-code 1 --python scripts/generate_model.py -- \
  --name "Forge Kid" --out out --blend --render
blender -b --factory-startup --python-exit-code 1 --python scripts/validate_model.py -- \
  --glb out/forge-kid.glb --report out/validation.json --expect-rig
python3 -m unittest discover tests
```

Always pass `--python-exit-code 1`; without it Blender exits 0 even when the script raises.

## Modeling workflow

1. Start from an empty scene (`bpy.ops.wm.read_factory_settings(use_empty=True)`).
2. Build each part with `part()` in `generate_model.py`: a bmesh primitive (`sphere`, `cyl`, `cone`, `cube`)
   transformed by size → rotation → location and **baked in world space** (object transform stays identity).
3. Refine shape with modifiers passed to `part()` (`bevel`, `subsurf`, `solidify`, `cut` to delete vertices);
   modifiers are baked into the mesh immediately so what is exported is exactly what is validated.
4. All faces are smooth-shaded. Keep total triangles below ~100k for mobile viewers (current model ≈ 25k).
5. Name parts consistently: central parts plain (`Head`, `Torso`), sided parts with `_L` / `_R` suffix.
   Character's **left is +X**; the character faces **-Y** in Blender (exported as +Z front, Y-up).

### Materials

Create with `material(name, "#RRGGBB", roughness)` — Principled BSDF only, colours converted from
sRGB hex to linear. Every part gets exactly one material. No image textures are required.

### Proportions (chibi)

Total height ≈ 1.3 m. Head ≈ 38% of height (validator requires > 30%). Compact torso, short limbs,
eyes on the lower half of the head, feet slightly longer than wide. Facial parts must protrude
1–15 mm from the head surface to avoid z-fighting.

## Mandatory T-pose (humanoids)

Every humanoid generator **must** build its rest pose as a T-pose, with no option that changes it:
upright, facing forward, arms horizontal from the shoulders (within 8°), straight elbows, hands
continuing the arm line, straight vertical legs, feet pointing forward, left/right mirror-symmetric,
grounded at z = 0 and centred on the origin. An A-pose (arms angled down 30–45°) is a failure.

Enforced twice: `tpose_selfcheck()` in the generator (from construction geometry) and the validator
on the re-imported GLB (part bounding boxes **and** armature rest-pose bone directions).

## Rigging

`build_rig()` creates 17 bones: `root, pelvis, spine, neck, head` and `upper_arm/forearm/hand/thigh/shin/foot` `.L/.R`.
Each part is bound to one bone with weight 1.0 (**rigid per-part skinning**) via an Armature modifier.
`deformation_selftest()` rotates `upper_arm.L` and confirms the hand moves and the torso does not.
This is good for posing and simple animation; joints do not bend smoothly (no blended weights yet).
Do not describe the model as "production animation-ready" until blended weights exist and are tested.

## Exports

- **GLB**: `export_model.export_glb()` → `export_yup=True`, skins on, animations off. Verified non-empty.
- **BLEND**: `export_model.save_blend()` (compressed). Saved before preview lights/camera are added.
- **Previews**: Cycles on CPU, 48 samples, 800×800; the render aborts if any part would be outside the frame.

See `references/export-guidelines.md` for details.

## Validation

`validate_model.py` checks: GLB container/JSON/buffer bounds, meshes with vertices and faces,
materials present and assigned, expected parts present, finite non-degenerate geometry, height
0.5–3 m, grounded, centred, upright, T-pose arms/elbows/legs/feet, arm span ≥ 0.8 × height,
symmetry, facing direction, chibi head ratio, skin present in GLB, armature + expected bones,
all meshes bound, rest-pose arm bones horizontal and leg bones vertical. Output: `validation.json`;
`make_report.py` turns it into `REPORT.md` (also shown on the run's Summary page).

## Diagnosing failed runs

1. Open the failed run → tap the red step → read the last lines. Validation lines start with `[FAIL]`.
2. The workflow also pushes `logs.txt`, `generation.json` and `validation.json` to the
   `ci-results` branch (`latest/` folder) on every run — readable without Actions-log access.
3. Common causes: Blender download failed (retry; check `BLENDER_VERSION` exists on download.blender.org);
   bpy API changed (pin stays 4.2.3 unless you test a new version); a geometry change broke a T-pose
   or symmetry check (fix the geometry, never loosen the threshold to make it pass).

## Adding a new generator

1. Add a choice to `--model-type` in `generate_model.py` and the `model_type` workflow input.
2. Write a `build_<type>(args)` returning a list of parts built with `part()`; reuse `material()`.
3. If humanoid: reuse `BONES`/`build_rig()` naming and keep the T-pose. If not humanoid, add
   type-specific expected parts and skip the T-pose checks in the validator for that type explicitly.
4. Run the workflow, read the report, and only then document the new type as working.

## Evidence before claims

Never say a model was generated, exported, rigged, validated or displayed unless you have seen the
evidence: a green run, `validation.json` with `"overall": "PASS"`, an uploaded artifact or Release
asset, and a real rendered PNG. If a run has not happened, say "pending".
