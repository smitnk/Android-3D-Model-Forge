"""Validate an exported character GLB. Runs inside Blender (re-imports the GLB) plus a pure-Python container check.

Usage:
  blender -b --factory-startup --python-exit-code 1 --python scripts/validate_model.py -- \
      --glb out/forge-kid.glb --report out/validation.json [--expect-rig]
Exit code is non-zero if any check fails.
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb_inspect  # noqa: E402

SIDED = ["Ear", "Eye", "Pupil", "Eyebrow", "UpperArm", "Forearm", "Hand", "ShortsLeg", "Shin", "Shoe"]
CENTRAL = ["Head", "Hair", "Nose", "Mouth", "Neck", "Torso", "Shorts"]
EXPECTED_PARTS = {
    "chibi_humanoid": CENTRAL + [f"{p}_{s}" for p in SIDED for s in ("L", "R")],
    "clay_chibi": ["Head", "Body"],
}
EXPECTED_BONES = ["root", "pelvis", "spine", "neck", "head"] + [
    f"{b}.{s}" for b in ("upper_arm", "forearm", "hand", "thigh", "shin", "foot") for s in ("L", "R")]
MIN_MATERIALS = {"chibi_humanoid": 5, "clay_chibi": 1}
MAX_ARM_ANGLE_DEG = 8.0   # T-pose: arms within 8 degrees of horizontal (an A-pose is ~30-45)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--glb", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--expect-rig", action="store_true")
    p.add_argument("--model-type", default="chibi_humanoid", choices=list(EXPECTED_PARTS))
    return p.parse_args(argv)


class Checks:
    def __init__(self):
        self.items = []

    def add(self, name, ok, detail=""):
        self.items.append({"check": name, "pass": bool(ok), "detail": detail})
        print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")

    @property
    def ok(self):
        return all(i["pass"] for i in self.items)


def bbox(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    pts = [ev.matrix_world @ v.co for v in ev.data.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi, (lo + hi) / 2, hi - lo


def base_name(name):
    return name.split(".")[0]  # importer may add .001 suffixes


def main():
    a = parse_args()
    c = Checks()

    # 1. Container / JSON / buffers (no Blender involved).
    c.add("glb_exists_nonempty", os.path.isfile(a.glb) and os.path.getsize(a.glb) > 0, a.glb)
    with open(a.glb, "rb") as f:
        data = f.read()
    try:
        summary = glb_inspect.inspect(data)
        c.add("glb_structure_valid", True,
              f"{summary['meshes']} meshes, {summary['vertices']} verts, {summary['triangles']} tris")
    except glb_inspect.GLBError as e:
        c.add("glb_structure_valid", False, str(e))
        return finish(a, c, None, None)
    c.add("materials_present", len(summary["materials"]) >= MIN_MATERIALS[a.model_type], ", ".join(summary["materials"]))
    c.add("materials_assigned", summary["primitives_without_material"] == 0,
          f"{summary['primitives_without_material']} primitives without material")
    c.add("size_reasonable", summary["bytes"] < 25 * 1024 * 1024, f"{summary['bytes']} bytes")
    expected = EXPECTED_PARTS[a.model_type]
    missing = [p for p in expected if p not in summary["mesh_nodes"]]
    c.add("expected_parts_present", not missing, f"missing: {missing}" if missing else f"{len(expected)} parts")

    # 2. Re-import into a clean Blender scene and measure real geometry.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(a.glb))
    # Only measure meshes that are nodes in the GLB (the importer adds a hidden bone-shape 'Icosphere').
    glb_nodes = set(summary["mesh_nodes"])
    meshes = {base_name(o.name): o for o in bpy.context.scene.objects
              if o.type == "MESH" and base_name(o.name) in glb_nodes}
    B = {n: bbox(o) for n, o in meshes.items()}
    lo = Vector(tuple(min(b[0][i] for b in B.values()) for i in range(3)))
    hi = Vector(tuple(max(b[1][i] for b in B.values()) for i in range(3)))
    size = hi - lo
    height = size.z
    finite = all(math.isfinite(v) for b in B.values() for v in (*b[0], *b[1]))
    c.add("geometry_finite", finite)
    c.add("bbox_nonzero", min(size) > 0.01, f"size {tuple(round(v, 3) for v in size)} m")
    c.add("scale_usable", 0.5 <= height <= 3.0, f"height {height:.3f} m (expected 0.5-3.0)")
    c.add("grounded", abs(lo.z) < 0.01, f"min z {lo.z:.4f}")
    cx, cy = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2
    c.add("centered", abs(cx) < 0.02 and abs(cy) < 0.08, f"center x {cx:.4f}, y {cy:.4f}")
    c.add("upright", height > size.y, f"height {height:.3f} > depth {size.y:.3f}")
    degenerate = [n for n, b in B.items() if min(b[3]) <= 1e-5]
    c.add("no_degenerate_parts", not degenerate, f"{degenerate}" if degenerate else "")

    # 3a. T-pose from raw geometry (works for one-piece and multi-part meshes).
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in meshes.values():
        ev = o.evaluated_get(dg)
        pts += [ev.matrix_world @ v.co for v in ev.data.vertices]
    geometry_tpose(c, pts, height)

    # 3b. Part-level T-pose checks (multi-part generators only).
    if a.model_type == "chibi_humanoid" and not missing:
        for s, sign in (("L", 1), ("R", -1)):
            sh, hd = B[f"UpperArm_{s}"][2], B[f"Hand_{s}"][2]
            ang = math.degrees(math.atan2(abs(hd.z - sh.z), abs(hd.x - sh.x)))
            c.add(f"tpose_arm_horizontal_{s}", ang <= MAX_ARM_ANGLE_DEG and math.copysign(1, hd.x) == sign,
                  f"arm angle {ang:.2f} deg from horizontal (max {MAX_ARM_ANGLE_DEG})")
            ua = B[f"UpperArm_{s}"][3]
            c.add(f"tpose_upperarm_along_x_{s}", ua.x > 1.5 * ua.z, f"x-extent {ua.x:.3f} vs z-extent {ua.z:.3f}")
            elbow = math.degrees(math.atan2(abs(B[f"Forearm_{s}"][2].z - sh.z), abs(B[f"Forearm_{s}"][2].x - sh.x)))
            c.add(f"tpose_elbow_straight_{s}", elbow <= MAX_ARM_ANGLE_DEG, f"forearm angle {elbow:.2f} deg")
            shin, shoe = B[f"Shin_{s}"], B[f"Shoe_{s}"]
            c.add(f"leg_straight_vertical_{s}", shin[3].z > 1.5 * shin[3].x and abs(shin[2].x - shoe[2].x) < 0.02,
                  f"shin z/x {shin[3].z:.3f}/{shin[3].x:.3f}, shin-shoe dx {abs(shin[2].x - shoe[2].x):.4f}")
            c.add(f"foot_points_forward_{s}", shoe[3].y > shoe[3].x and shoe[1].y <= shin[1].y + 0.05,
                  f"shoe depth {shoe[3].y:.3f} > width {shoe[3].x:.3f}")
        span = B["Hand_L"][1].x - B["Hand_R"][0].x
        c.add("tpose_arm_span", span >= 0.8 * height, f"span {span:.3f} m vs height {height:.3f} m")
        asym = max((B[f"{p}_L"][2] - Vector((-B[f"{p}_R"][2].x, B[f"{p}_R"][2].y, B[f"{p}_R"][2].z))).length
                   for p in SIDED)
        c.add("left_right_symmetry", asym < 0.01 * height, f"max mirror error {asym:.5f} m")
        c.add("faces_forward", B["Nose"][2].y < B["Head"][2].y - 0.1,
              f"nose y {B['Nose'][2].y:.3f} in front of head centre y {B['Head'][2].y:.3f} (Blender -Y = glTF +Z front)")
        c.add("chibi_proportions", B["Head"][3].z > 0.3 * height,
              f"head is {100 * B['Head'][3].z / height:.0f}% of height")

    # 4. Rig.
    rig_info = None
    if a.expect_rig:
        c.add("skin_in_glb", summary["skins"] >= 1 and summary["skinned_primitives"] > 0,
              f"{summary['skins']} skins, {summary['skinned_primitives']} skinned primitives")
        arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
        c.add("armature_present", len(arms) == 1, f"{len(arms)} armatures")
        if arms:
            arm = arms[0]
            names = {b.name for b in arm.data.bones}
            miss_b = [b for b in EXPECTED_BONES if b not in names]
            c.add("expected_bones", not miss_b, f"missing {miss_b}" if miss_b else f"{len(names)} bones")
            unbound = [n for n, o in meshes.items()
                       if not any(m.type == "ARMATURE" and m.object == arm for m in o.modifiers) or not o.vertex_groups]
            c.add("meshes_bound_to_armature", not unbound, f"unbound: {unbound}" if unbound else "all meshes skinned")
            if not miss_b:
                W = arm.matrix_world
                hp = {n: W @ arm.data.bones[n].head_local for n in EXPECTED_BONES}
                for s, sign in (("L", 1), ("R", -1)):
                    d = (hp[f"hand.{s}"] - hp[f"upper_arm.{s}"]).normalized()
                    c.add(f"rest_pose_arm_bones_horizontal_{s}", d.dot(Vector((sign, 0, 0))) > 0.99,
                          f"upper_arm->hand dir {tuple(round(v, 3) for v in d)}")
                    d = (hp[f"foot.{s}"] - hp[f"thigh.{s}"]).normalized()
                    c.add(f"rest_pose_leg_bones_vertical_{s}", d.dot(Vector((0, 0, -1))) > 0.99,
                          f"thigh->foot dir {tuple(round(v, 3) for v in d)}")
            rig_info = {"bones": sorted(names), "skins": summary["skins"]}
    return finish(a, c, summary, rig_info, height=height, size=size, lo=lo, hi=hi)


def _mean(pts):
    return sum(pts, Vector()) / len(pts) if pts else None


def geometry_tpose(c, pts, height):
    arm_angles = {}
    for s, sign in (("L", 1), ("R", -1)):
        side = [p for p in pts if p.x * sign > 0]
        reach = max(abs(p.x) for p in side)
        bands = [_mean([p for p in side if lo_ <= abs(p.x) <= hi_]) for lo_, hi_ in
                 ((0.31, 0.36), (0.38, 0.43), (0.85 * reach, reach))]  # arm bands outside head/hair width
        if None in bands:
            c.add(f"geom_tpose_arm_{s}", False, "no geometry in arm bands")
            continue
        ang = max(math.degrees(math.atan2(abs(b.z - bands[0].z), abs(b.x - bands[0].x))) for b in bands[1:])
        arm_angles[s] = (ang, bands)
        c.add(f"geom_tpose_arm_{s}", ang <= MAX_ARM_ANGLE_DEG,
              f"forearm/hand {ang:.2f} deg from horizontal vs upper arm (max {MAX_ARM_ANGLE_DEG})")
        thin = [p for p in side if 0.31 <= abs(p.x) <= 0.43]
        zs = max(p.z for p in thin) - min(p.z for p in thin)
        c.add(f"geom_arm_is_limb_{s}", zs < 0.15 * height, f"arm band vertical thickness {zs:.3f} m")
        low = [p for p in side if 0.12 <= p.z <= 0.18]
        mid = [p for p in side if 0.25 <= p.z <= 0.30]
        if low and mid:
            dx = abs(_mean(low).x - _mean(mid).x)
            c.add(f"geom_leg_vertical_{s}", dx < 0.03, f"leg centre drift {dx:.4f} m between z 0.15 and 0.28")
        else:
            c.add(f"geom_leg_vertical_{s}", False, "no leg geometry found")
        foot = [p for p in side if p.z <= 0.03]
        fx = max(p.x for p in foot) - min(p.x for p in foot)
        fy = max(p.y for p in foot) - min(p.y for p in foot)
        c.add(f"geom_foot_forward_{s}", fy > fx and min(p.y for p in foot) < -0.05,
              f"foot length {fy:.3f} > width {fx:.3f}, toe at y {min(p.y for p in foot):.3f}")
    if len(arm_angles) == 2:
        l, r = arm_angles["L"][1][2], arm_angles["R"][1][2]
        err = (l - Vector((-r.x, r.y, r.z))).length
        c.add("geom_left_right_symmetry", err < 0.01 * height, f"hand mirror error {err:.5f} m")
        shoulder_z = (arm_angles["L"][1][0].z + arm_angles["R"][1][0].z) / 2
        top = max(p.z for p in pts)
        c.add("geom_chibi_head", top - shoulder_z > 0.3 * height,
              f"head+neck above shoulders = {100 * (top - shoulder_z) / height:.0f}% of height")
        upper = [p for p in pts if p.z > shoulder_z]
        front = min(upper, key=lambda p: p.y)
        c.add("geom_faces_forward", abs(front.x) < 0.03 and front.y < -0.1,
              f"front-most head point at x {front.x:.3f}, y {front.y:.3f} (Blender -Y = glTF +Z front)")
    span = max(p.x for p in pts) - min(p.x for p in pts)
    c.add("geom_tpose_span", span >= 0.8 * height, f"span {span:.3f} m vs height {height:.3f} m")


def finish(a, c, summary, rig, height=None, size=None, lo=None, hi=None):
    report = {
        "overall": "PASS" if c.ok else "FAIL",
        "glb": os.path.basename(a.glb),
        "checks": c.items,
        "summary": summary,
        "dimensions_m": {"height": round(height, 4), "size_xyz": [round(v, 4) for v in size],
                         "bbox_min": [round(v, 4) for v in lo], "bbox_max": [round(v, 4) for v in hi]}
        if height else None,
        "rig": rig,
    }
    with open(a.report, "w") as f:
        json.dump(report, f, indent=2)
    print(f"VALIDATION {report['overall']}: {sum(i['pass'] for i in c.items)}/{len(c.items)} checks passed")
    if not c.ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
