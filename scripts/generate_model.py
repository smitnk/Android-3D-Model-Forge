"""Procedural chibi humanoid generator for Blender (run headless).

Usage (inside Blender):
  blender -b --factory-startup --python-exit-code 1 --python scripts/generate_model.py -- \
      --name "Forge Kid" --out out --blend --render

Coordinate convention: Blender Z-up, metres, character faces -Y (glTF exports this as +Z front, Y-up).
Character's LEFT side is +X. Every humanoid is built in a T-pose by construction.
"""
import argparse
import json
import math
import os
import re
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import export_model  # noqa: E402

GENERATOR_VERSION = "0.1.1"

# --- T-pose construction parameters (the validator re-checks these on the exported GLB) ---
SHOULDER_Z = 0.645
ARM_RADIUS = 0.055
HIP_X = 0.085

BONES = [
    # name, head, tail, parent
    ("root", (0, 0, 0), (0, 0, 0.10), None),
    ("pelvis", (0, 0, 0.36), (0, 0, 0.44), "root"),
    ("spine", (0, 0, 0.44), (0, 0, 0.68), "pelvis"),
    ("neck", (0, 0, 0.68), (0, 0, 0.74), "spine"),
    ("head", (0, 0, 0.74), (0, 0, 1.22), "neck"),
]
for _s, _x in (("L", 1), ("R", -1)):
    BONES += [
        (f"upper_arm.{_s}", (0.10 * _x, 0, SHOULDER_Z), (0.29 * _x, 0, SHOULDER_Z), "spine"),
        (f"forearm.{_s}", (0.29 * _x, 0, SHOULDER_Z), (0.45 * _x, 0, SHOULDER_Z), f"upper_arm.{_s}"),
        (f"hand.{_s}", (0.45 * _x, 0, SHOULDER_Z), (0.56 * _x, 0, SHOULDER_Z), f"forearm.{_s}"),
        (f"thigh.{_s}", (HIP_X * _x, 0, 0.38), (HIP_X * _x, 0, 0.24), "pelvis"),
        (f"shin.{_s}", (HIP_X * _x, 0, 0.24), (HIP_X * _x, 0, 0.06), f"thigh.{_s}"),
        (f"foot.{_s}", (HIP_X * _x, 0, 0.06), (HIP_X * _x, -0.12, 0.03), f"shin.{_s}"),
    ]


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--model-type", default="chibi_humanoid", choices=["chibi_humanoid"])
    p.add_argument("--name", default="Forge Kid")
    p.add_argument("--skin", default="#F2C9A0")
    p.add_argument("--hair", default="#3B2417")
    p.add_argument("--shirt", default="#E8553D")
    p.add_argument("--shorts", default="#2F4A8A")
    p.add_argument("--shoes", default="#F4F1EA")
    p.add_argument("--out", default="out")
    p.add_argument("--blend", action="store_true", help="also save an editable .blend")
    p.add_argument("--render", action="store_true", help="render preview PNGs with Cycles (CPU)")
    p.add_argument("--no-rig", action="store_true")
    return p.parse_args(argv)


def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "character"


def hex_to_linear(h):
    h = h.strip().lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise ValueError(f"Bad colour '{h}', expected #RRGGBB")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name, hexcol, rough=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = hex_to_linear(hexcol)
    bsdf.inputs["Roughness"].default_value = rough
    m.diffuse_color = hex_to_linear(hexcol)
    return m


def build_bmesh(kind, taper=1.0, segments=24):
    bm = bmesh.new()
    if kind == "sphere":
        bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments * 2 // 3, radius=0.5)
    elif kind == "cyl":
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                              radius1=0.5, radius2=0.5 * taper, depth=1.0)
    elif kind == "cone":
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                              radius1=0.5, radius2=0.0, depth=1.0)
    elif kind == "cube":
        bmesh.ops.create_cube(bm, size=1.0)
    else:
        raise ValueError(kind)
    return bm


def part(name, kind, size, loc, mat, bone, rot=(0, 0, 0), taper=1.0, bevel=0.0,
         subsurf=0, solidify=0.0, cut=None, segments=24):
    """Create one mesh part with geometry baked in world space (identity object transform)."""
    bm = build_bmesh(kind, taper, segments)
    if cut:  # cut(v) -> True to delete vertex (in unit-primitive space)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if cut(v.co)], context="VERTS")
    m = (Matrix.Translation(loc) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
         @ Matrix.Diagonal((*size, 1.0)))
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    if solidify:
        mod = obj.modifiers.new("solid", "SOLIDIFY")
        mod.thickness = solidify
        mod.offset = 1.0
    if bevel:
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        mod.limit_method = "ANGLE"
    if subsurf:
        mod = obj.modifiers.new("subsurf", "SUBSURF")
        mod.levels = subsurf
        mod.render_levels = subsurf
    if obj.modifiers:  # bake modifiers into the mesh so export == what we validate
        dg = bpy.context.evaluated_depsgraph_get()
        baked = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
        old = obj.data
        obj.modifiers.clear()
        obj.data = baked
        bpy.data.meshes.remove(old)
        baked.name = name
    for poly in obj.data.polygons:
        poly.use_smooth = True
    obj.data.materials.append(mat)
    obj["bone"] = bone
    return obj


def build_character(a):
    M = {
        "Skin": material("Skin", a.skin, 0.55),
        "Hair": material("Hair", a.hair, 0.45),
        "Shirt": material("Shirt", a.shirt, 0.7),
        "Shorts": material("Shorts", a.shorts, 0.7),
        "Shoe": material("Shoe", a.shoes, 0.5),
        "Sole": material("Sole", "#3A3A3A", 0.8),
        "EyeWhite": material("EyeWhite", "#FFFFFF", 0.3),
        "Pupil": material("Pupil", "#1B1B2A", 0.15),
        "Brow": material("Brow", a.hair, 0.6),
        "Mouth": material("Mouth", "#8E2B2B", 0.5),
    }
    P = []
    # Head (oversized, ~40% of height) and face. Head ellipsoid semi-axes: 0.26, 0.239, 0.247.
    P.append(part("Head", "sphere", (0.52, 0.478, 0.494), (0, 0, 0.98), M["Skin"], "head", segments=32))
    for s, x in (("L", 1), ("R", -1)):
        P.append(part(f"Ear_{s}", "sphere", (0.04, 0.07, 0.09), (0.255 * x, 0.0, 0.97), M["Skin"], "head", segments=16))
        P.append(part(f"Eye_{s}", "sphere", (0.085, 0.035, 0.105), (0.085 * x, -0.222, 0.99), M["EyeWhite"], "head", segments=20))
        P.append(part(f"Pupil_{s}", "sphere", (0.05, 0.02, 0.062), (0.083 * x, -0.236, 0.985), M["Pupil"], "head", segments=16))
        P.append(part(f"EyeShine_{s}", "sphere", (0.016, 0.008, 0.016), (0.072 * x, -0.2465, 1.0), M["EyeWhite"], "head", segments=10))
        P.append(part(f"Eyebrow_{s}", "cube", (0.075, 0.018, 0.017), (0.088 * x, -0.214, 1.068), M["Brow"], "head",
                      rot=(0, 10 * x, 0), bevel=0.006, subsurf=1))
    P.append(part("Nose", "sphere", (0.04, 0.03, 0.035), (0, -0.240, 0.945), M["Skin"], "head", segments=16))
    P.append(part("Mouth", "sphere", (0.10, 0.022, 0.035), (0, -0.222, 0.892), M["Mouth"], "head", segments=16))
    # Hair: a shell over the skull, cut higher at the front to expose the forehead, plus tufts.
    P.append(part("Hair", "sphere", (0.56, 0.53, 0.53), (0, 0.012, 1.0), M["Hair"], "head",
                  cut=lambda c: c.z < 0.06 - 0.5 * c.y, solidify=0.025, subsurf=1, segments=32))
    # Tufts sit on the hair surface, each pointing outward along its own direction (symmetric pairs).
    hc, hr = Vector((0, 0.012, 1.0)), Vector((0.29, 0.28, 0.28))
    tufts = [(0, -0.55, 0.83), (0.38, -0.42, 0.82), (-0.38, -0.42, 0.82), (0, 0.15, 1),
             (0.5, 0.15, 0.85), (-0.5, 0.15, 0.85), (0, 0.65, 0.75), (0.3, 0.55, 0.78), (-0.3, 0.55, 0.78)]
    for i, d in enumerate(tufts):
        d = Vector(d).normalized()
        loc = hc + Vector((d.x * hr.x, d.y * hr.y, d.z * hr.z)) * 0.8
        rot = [math.degrees(v) for v in d.to_track_quat("Z", "Y").to_euler()]
        P.append(part(f"HairTuft_{i}", "cone", (0.15, 0.15, 0.22), loc, M["Hair"], "head",
                      rot=rot, subsurf=1, segments=12))
    # Body
    P.append(part("Neck", "cyl", (0.1, 0.1, 0.09), (0, 0, 0.71), M["Skin"], "neck", segments=16))
    P.append(part("Torso", "cyl", (0.30, 0.234, 0.27), (0, 0, 0.56), M["Shirt"], "spine", taper=0.85,
                  bevel=0.03, subsurf=1))
    P.append(part("Shorts", "cyl", (0.29, 0.232, 0.13), (0, 0, 0.385), M["Shorts"], "pelvis", bevel=0.025, subsurf=1))
    for s, x in (("L", 1), ("R", -1)):
        # Arms: horizontal along X at shoulder height (T-pose).
        P.append(part(f"UpperArm_{s}", "cyl", (0.11, 0.11, 0.21), (0.20 * x, 0, SHOULDER_Z), M["Shirt"],
                      f"upper_arm.{s}", rot=(0, 90, 0), bevel=0.02, subsurf=1, segments=16))
        P.append(part(f"Forearm_{s}", "cyl", (0.084, 0.084, 0.17), (0.37 * x, 0, SHOULDER_Z), M["Skin"],
                      f"forearm.{s}", rot=(0, 90, 0), bevel=0.015, subsurf=1, segments=16))
        P.append(part(f"Hand_{s}", "sphere", (0.12, 0.085, 0.10), (0.50 * x, 0, SHOULDER_Z), M["Skin"],
                      f"hand.{s}", segments=20))
        P.append(part(f"Thumb_{s}", "sphere", (0.055, 0.035, 0.035), (0.475 * x, -0.04, SHOULDER_Z + 0.012),
                      M["Skin"], f"hand.{s}", rot=(0, 0, -30 * x), segments=12))
        # Legs: straight, vertical.
        P.append(part(f"ShortsLeg_{s}", "cyl", (0.13, 0.13, 0.15), (HIP_X * x, 0, 0.30), M["Shorts"],
                      f"thigh.{s}", bevel=0.02, subsurf=1, segments=16))
        P.append(part(f"Shin_{s}", "cyl", (0.09, 0.09, 0.19), (HIP_X * x, 0, 0.165), M["Skin"],
                      f"shin.{s}", segments=16))
        # Feet point forward (-Y).
        P.append(part(f"Shoe_{s}", "cube", (0.12, 0.22, 0.085), (HIP_X * x, -0.03, 0.0525), M["Shoe"],
                      f"foot.{s}", bevel=0.03, subsurf=1))
        P.append(part(f"Sole_{s}", "cube", (0.118, 0.215, 0.03), (HIP_X * x, -0.03, 0.015), M["Sole"],
                      f"foot.{s}", bevel=0.008, subsurf=1))
    return P


def build_rig(parts):
    arm_data = bpy.data.armatures.new("Armature")
    rig = bpy.data.objects.new("Armature", arm_data)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    for name, head, tail, parent in BONES:
        b = arm_data.edit_bones.new(name)
        b.head, b.tail = Vector(head), Vector(tail)
        if parent:
            b.parent = arm_data.edit_bones[parent]
            b.use_connect = (Vector(head) - arm_data.edit_bones[parent].tail).length < 1e-6
    bpy.ops.object.mode_set(mode="OBJECT")
    # shortcut: rigid one-bone-per-part skinning (weight 1.0); upgrade to blended joint weights for smooth bends.
    for obj in parts:
        vg = obj.vertex_groups.new(name=obj["bone"])
        vg.add(range(len(obj.data.vertices)), 1.0, "REPLACE")
        mod = obj.modifiers.new("Armature", "ARMATURE")
        mod.object = rig
        obj.parent = rig
    return rig


def world_bbox(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    pts = [ev.matrix_world @ v.co for v in ev.data.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def deformation_selftest(rig, parts):
    """Pose the left arm, confirm the hand follows and the torso does not, then restore rest pose."""
    by = {o.name: o for o in parts}
    hand0 = sum(world_bbox(by["Hand_L"]), Vector()) / 2
    torso0 = world_bbox(by["Torso"])
    pb = rig.pose.bones["upper_arm.L"]
    pb.rotation_mode = "XYZ"
    pb.rotation_euler = (0, 0, math.radians(-45))
    bpy.context.view_layer.update()
    hand1 = sum(world_bbox(by["Hand_L"]), Vector()) / 2
    torso1 = world_bbox(by["Torso"])
    pb.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    moved = (hand1 - hand0).length
    torso_still = (torso1[0] - torso0[0]).length + (torso1[1] - torso0[1]).length
    ok = moved > 0.05 and torso_still < 1e-5 and all(math.isfinite(c) for c in hand1)
    return {"hand_moved_m": round(moved, 4), "torso_drift_m": round(torso_still, 6), "pass": ok}


def tpose_selfcheck(parts):
    by = {o.name: o for o in parts}
    res = {}
    for s in ("L", "R"):
        sh = sum(world_bbox(by[f"UpperArm_{s}"]), Vector()) / 2
        hd = sum(world_bbox(by[f"Hand_{s}"]), Vector()) / 2
        res[f"arm_angle_deg_{s}"] = round(math.degrees(math.atan2(abs(hd.z - sh.z), abs(hd.x - sh.x))), 3)
    res["pass"] = all(v <= 5.0 for k, v in res.items())
    return res


def main():
    a = parse_args()
    slug = slugify(a.name)
    os.makedirs(a.out, exist_ok=True)
    reset_scene()
    parts = build_character(a)
    rig = None if a.no_rig else build_rig(parts)
    tpose = tpose_selfcheck(parts)
    if not tpose["pass"]:
        raise SystemExit(f"T-pose self-check failed: {tpose}")
    deform = deformation_selftest(rig, parts) if rig else None
    if deform and not deform["pass"]:
        raise SystemExit(f"Rig deformation self-test failed: {deform}")

    files = {"glb": export_model.export_glb(os.path.join(a.out, f"{slug}.glb"))}
    if a.blend:
        files["blend"] = export_model.save_blend(os.path.join(a.out, f"{slug}.blend"))
    if a.render:
        files["previews"] = export_model.render_previews(parts, a.out, slug)

    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in parts)
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for o in parts:
        l, h = world_bbox(o)
        lo = Vector(map(min, lo, l))
        hi = Vector(map(max, hi, h))
    info = {
        "generator": "chibi_humanoid", "generator_version": GENERATOR_VERSION,
        "blender": bpy.app.version_string, "name": a.name, "slug": slug,
        "colors": {"skin": a.skin, "hair": a.hair, "shirt": a.shirt, "shorts": a.shorts, "shoes": a.shoes},
        "parts": len(parts), "triangles": tris,
        "vertices": sum(len(o.data.vertices) for o in parts),
        "materials": sorted({o.data.materials[0].name for o in parts}),
        "bbox_min_m": [round(c, 4) for c in lo], "bbox_max_m": [round(c, 4) for c in hi],
        "rig": {"bones": len(BONES), "skinning": "rigid per-part"} if rig else None,
        "tpose_selfcheck": tpose, "deformation_selftest": deform, "files": files,
    }
    with open(os.path.join(a.out, "generation.json"), "w") as f:
        json.dump(info, f, indent=2)
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
