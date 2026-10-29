# tests/

- `test_glb_inspect.py` — pure-Python tests for the GLB parser and report builder.
  Run with `python3 -m unittest discover tests` (no Blender needed). Runs in both workflows.
- Full model validation (geometry, T-pose, rig) runs in Blender via `scripts/validate_model.py`
  inside the *Generate 3D Model* workflow.
