# Export guidelines

## GLB
- `bpy.ops.export_scene.gltf(export_format="GLB", export_yup=True, export_skins=True, export_animations=False, export_apply=False)`.
- `export_apply=False` because modifiers are already baked by `part()`; applying again could drop skinning.
- Each part exports as its own skinned mesh node named after the part (the validator relies on these names).
- Export **before** adding preview cameras, lights and the floor, so they never end up in the asset.
- Expected size: well under 5 MB. The validator fails above 25 MB.

## BLEND
- `bpy.ops.wm.save_as_mainfile(filepath=..., compress=True)` right after the GLB export.
- Opening it in Blender 4.2+ gives the editable parts, armature and materials.

## Previews
- Cycles, CPU device, 48 samples, OpenImageDenoise, 800×800 PNG, "Standard" view transform.
- Two cameras: `front` (shows the T-pose clearly) and `three-quarter`.
- `render_previews()` projects every part's bounding box into the camera and aborts if anything would be clipped.

## Validating an export
1. `python3 scripts/glb_inspect.py model.glb` — container/JSON/buffers, no Blender needed.
2. `blender -b --factory-startup --python-exit-code 1 --python scripts/validate_model.py -- --glb model.glb --report v.json --expect-rig`.
3. Only a `"overall": "PASS"` report counts as a validated model.

## Publishing
- Every run uploads an Actions artifact (`model-<run number>`, kept 30 days).
- Permanent downloads: the `model-latest` GitHub Release. The workflow updates it (assets replaced with
  `--clobber`) when the run was started with **publish** ticked or by a push to `main` touching `scripts/`.
- Generated binaries (`.glb`, `.blend`) are **not** committed to Git; only small PNG previews and the
  report are committed under `docs/preview/` so the README can show them.
