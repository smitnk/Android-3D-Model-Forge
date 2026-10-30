"""Render a short portrait animation of a Forge character (Blender 4.2, headless).

    blender -b --factory-startup --python-exit-code 1 --python animation/make_video.py -- \
        --model forge-kid.glb --out anim_out [--fps 24 --duration 8 --width 720 --height 1280]

Writes <out>/frames/####.png (transparent RGBA, shadow-catcher floor), <out>/background.ppm (blue
radial backdrop) and <out>/scene_check.json. Captions and the backdrop are composited by FFmpeg in the
workflow (see .github/workflows/render-animation.yml). Motion is a pure function of the frame number,
so identical inputs always give identical keyframes.

If the model has the Forge 17-bone rig, the skeleton is animated (walk, wave, jump). Without a rig
only the whole character object moves, and scene_check.json says so (rig: "none").
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Euler, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline  # noqa: E402


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True, help=".glb or .blend")
    p.add_argument("--out", default="anim_out")
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--duration", type=float, default=8.0)
    p.add_argument("--width", type=int, default=720)
    p.add_argument("--height", type=int, default=1280)
    p.add_argument("--samples", type=int, default=24)
    p.add_argument("--caption", default=timeline.DEFAULT_CAPTION)
    p.add_argument("--model2", default="", help="second .glb (rival scene)")
    p.add_argument("--frames", default="", help="render only FIRST-LAST (1-based, inclusive)")
    p.add_argument("--check-only", action="store_true", help="build and check the scene, do not render")
    return p.parse_args(argv)


def load_model(path):
    if not os.path.isfile(path):
        sys.exit(f"[FAIL] model not found: {path}")
    if path.lower().endswith(".blend"):
        bpy.ops.wm.open_mainfile(filepath=path)
        for o in [o for o in bpy.data.objects if o.type in {"CAMERA", "LIGHT"}]:
            bpy.data.objects.remove(o)
    elif path.lower().endswith(".glb"):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=path)
    else:
        sys.exit(f"[FAIL] unsupported model format: {path}")
    meshes = [o for o in bpy.data.objects if o.type == "MESH" and o.visible_get()]
    if not meshes:
        sys.exit("[FAIL] model contains no visible meshes")
    return meshes


def bbox(meshes):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi


def make_actor(meshes):
    """Parent every top-level object to an 'Actor' empty scaled so the character is 1 unit tall."""
    lo, hi = bbox(meshes)
    actor = bpy.data.objects.new("Actor", None)
    bpy.context.scene.collection.objects.link(actor)
    tops = [o for o in bpy.data.objects if o.parent is None and o is not actor]
    for o in tops:
        mw = o.matrix_world.copy()
        o.parent = actor
        o.matrix_world = mw
    # move feet-centre to the origin, then scale to unit height (children keep their offsets)
    for o in tops:
        o.location -= Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    actor.scale = [1 / max(hi.z - lo.z, 1e-6)] * 3
    return actor


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


class Rig:
    """Rotates Forge bones about armature-space axes, whatever each bone's roll is."""

    def __init__(self, arm):
        self.arm = arm
        self.to_arm = arm.matrix_world.to_quaternion().inverted()  # world axes -> armature space
        for pb in arm.pose.bones:
            pb.rotation_mode = "QUATERNION"

    def rot(self, name, axis, deg):
        pb = self.arm.pose.bones.get(name)
        if pb is None:
            return
        rest = pb.bone.matrix_local.to_quaternion()
        q = Quaternion(self.to_arm @ Vector(axis), math.radians(deg))
        pb.rotation_quaternion = rest.inverted() @ q @ rest

    def reset(self):
        for pb in self.arm.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0)


def pose(f, n, actor, rig):
    """Character pose at frame f (1..n). Shot 1 walk in, shot 2 wave, shot 3 jump."""
    t = (f - 1) / max(n - 1, 1)
    X, Y = (1, 0, 0), (0, 1, 0)
    walk = ease(t / 0.30)
    actor.location = (-0.6 + 0.6 * walk, 0, 0)
    actor.rotation_euler = Euler((0, 0, math.radians(90 * (1 - ease((t - 0.22) / 0.10)))))
    if not rig:
        actor.location.z = 0.03 * abs(math.sin(t * 40)) if t < 0.3 else 0
        return
    rig.reset()
    arms_down = 70
    if t < 0.32:  # walk cycle, fades out as the character arrives
        amp = 28 * (1 - ease((t - 0.26) / 0.06))
        s = math.sin(t * 60)
        rig.rot("thigh.L", X, amp * s)
        rig.rot("thigh.R", X, -amp * s)
        rig.rot("shin.L", X, -abs(amp * s) * 0.6)
        rig.rot("shin.R", X, -abs(amp * s) * 0.6)
        rig.rot("upper_arm.L", Y, arms_down)
        rig.rot("upper_arm.R", Y, -arms_down)
    elif t < 2 / 3:  # wave with the right arm
        up = ease((t - 0.36) / 0.08) * (1 - ease((t - 0.60) / 0.06))
        rig.rot("upper_arm.L", Y, arms_down)
        rig.rot("upper_arm.R", Y, -arms_down + 135 * up)
        rig.rot("forearm.R", Y, 30 * up * math.sin(t * 70))
        rig.rot("head", Y, -8 * up)
    else:  # crouch, jump with arms up, land
        k = (t - 2 / 3) * 3  # 0..1 within the shot
        crouch = ease(k / 0.2) * (1 - ease((k - 0.2) / 0.1)) + ease((k - 0.62) / 0.06) * (1 - ease((k - 0.7) / 0.1))
        air = math.sin(math.pi * min(max((k - 0.28) / 0.36, 0), 1))
        lift = ease((k - 0.2) / 0.1) * (1 - ease((k - 0.8) / 0.15))
        actor.location.z = 0.28 * air - 0.06 * crouch
        rig.rot("thigh.L", X, 45 * crouch)
        rig.rot("thigh.R", X, 45 * crouch)
        rig.rot("shin.L", X, -80 * crouch)
        rig.rot("shin.R", X, -80 * crouch)
        rig.rot("spine", X, 15 * crouch)
        rig.rot("upper_arm.L", Y, arms_down - 130 * lift)
        rig.rot("upper_arm.R", Y, -arms_down + 130 * lift)


def add_stage(sc):
    """Shadow-catcher floor, soft world light, key + rim area lights and a portrait camera."""
    floor_mesh = bpy.data.meshes.new("Floor")
    floor_mesh.from_pydata([(-30, -30, 0), (30, -30, 0), (30, 30, 0), (-30, 30, 0)], [], [(0, 1, 2, 3)])
    floor = bpy.data.objects.new("Floor", floor_mesh)
    floor.is_shadow_catcher = True  # transparent except for the soft contact shadows
    sc.collection.objects.link(floor)

    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.72, 0.9, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.7
    sc.world = world
    for name, kind, energy, loc, size in (("Key", "AREA", 300, (2.5, -3, 4), 3), ("Rim", "AREA", 120, (-3, 3, 3), 2)):
        d = bpy.data.lights.new(name, kind)
        d.energy, d.size = energy, size
        L = bpy.data.objects.new(name, d)
        L.location = loc
        L.rotation_euler = (Vector((0, 0, 0.6)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(L)

    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    cam.data.lens, cam.data.sensor_fit = 40, "VERTICAL"
    sc.collection.objects.link(cam)
    sc.camera = cam
    return floor


def build_scene(a):
    meshes = load_model(a.model)
    arm = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
    for o in bpy.data.objects:  # drop any animation that came with the file
        if o.animation_data:
            o.animation_data_clear()
    actor = make_actor(meshes)
    sc = bpy.context.scene
    n = round(a.fps * a.duration)
    sc.render.fps, sc.frame_start, sc.frame_end = a.fps, 1, n
    sc.render.resolution_x, sc.render.resolution_y = a.width, a.height

    floor = add_stage(sc)
    cam = sc.camera

    rig = Rig(arm) if arm and len(arm.pose.bones) >= 10 else None
    shots = timeline.shot_frames(a.fps, a.duration)
    for f in range(1, n + 1):
        s0, s1, p0, p1, lz = next(s for s in shots if s[0] <= f <= s[1])
        k = ease((f - s0) / max(s1 - s0, 1))
        cam.location = Vector(p0).lerp(Vector(p1), k)
        cam.rotation_euler = (Vector((0, 0, lz)) - cam.location).to_track_quat("-Z", "Y").to_euler()
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
        pose(f, n, actor, rig)
        actor.keyframe_insert("location", frame=f)
        actor.keyframe_insert("rotation_euler", frame=f)
        if rig:
            for pb in arm.pose.bones:
                pb.keyframe_insert("rotation_quaternion", frame=f)

    # --- self-checks (the workflow fails on any False) ---
    def cam_at(f):
        sc.frame_set(f)
        return cam.matrix_world.translation.copy()
    mids = [cam_at((s[0] + s[1]) // 2) for s in shots]
    checks = {
        "model_imported": len(meshes) > 0,
        "camera": sc.camera is not None,
        "lights": sum(o.type == "LIGHT" for o in sc.objects) >= 2,
        "floor_shadow_catcher": floor.is_shadow_catcher,
        "frame_count": sc.frame_end - sc.frame_start + 1 == n,
        "camera_changes_between_shots": all((x - y).length > 0.3 for x, y in zip(mids, mids[1:])),
        "captions": len(timeline.caption_words(a.caption, a.duration)) > 0,
    }
    info = {"checks": checks, "frames": n, "fps": a.fps, "meshes": len(meshes),
            "rig": f"{len(arm.pose.bones)} bones (skeletal animation)" if rig else "none (object animation only)",
            "shots": shots, "captions": timeline.caption_words(a.caption, a.duration),
            "blender": bpy.app.version_string}
    return checks, info


def background(path, w, h):
    """Blue radial gradient as a binary PPM (FFmpeg reads it directly)."""
    import numpy as np
    y, x = np.mgrid[0:h, 0:w]
    r = np.clip(np.hypot((x - w / 2) / w, (y - h * 0.42) / h) / 0.75, 0, 1)[..., None]
    c0, c1, c2 = np.array([191, 226, 245.]), np.array([90, 169, 214.]), np.array([40, 120, 180.])
    img = np.where(r < 0.45, c0 + (c1 - c0) * (r / 0.45), c1 + (c2 - c1) * ((r - 0.45) / 0.55))
    with open(path, "wb") as fh:
        fh.write(f"P6 {w} {h} 255\n".encode())
        fh.write(img.astype(np.uint8).tobytes())


def main():
    a = parse_args()
    os.makedirs(os.path.join(a.out, "frames"), exist_ok=True)
    finish(a, *build_scene(a))


def finish(a, checks, info):
    """Write scene_check.json, fail on any False check, write the backdrop and render the frames."""
    with open(os.path.join(a.out, "scene_check.json"), "w") as fh:
        json.dump(info, fh, indent=1)
    for k, v in checks.items():
        print(f"[{'PASS' if v else 'FAIL'}] {k}")
    print("rig:", info["rig"])
    if not all(checks.values()):
        sys.exit("[FAIL] scene checks failed")
    background(os.path.join(a.out, "background.ppm"), a.width, a.height)
    if a.check_only:
        return
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = a.samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces, sc.cycles.diffuse_bounces, sc.cycles.glossy_bounces = 4, 2, 2
    sc.cycles.transmission_bounces = sc.cycles.transparent_max_bounces = 4
    sc.render.use_persistent_data = True  # keep BVH between frames
    sc.render.film_transparent = True
    if a.frames:  # render only this chunk (the workflow splits frames across parallel jobs)
        lo, hi = (int(x) for x in a.frames.split("-"))
        sc.frame_start, sc.frame_end = max(lo, 1), min(hi, sc.frame_end)
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.filepath = os.path.join(os.path.abspath(a.out), "frames", "")
    bpy.ops.render.render(animation=True)  # writes one PNG per frame; nothing kept in memory


if __name__ == "__main__":
    main()
