"""Two-character scene: Round Buddy trips and falls, the Gorilla walks up and pounds his chest at him.

    blender -b --factory-startup --python-exit-code 1 --python animation/rival_scene.py -- \
        --model round-buddy.glb --model2 gorilla.glb --out anim_out [--frames 1-48]

Same outputs and render settings as make_video.py (frames/, background.ppm, scene_check.json), no captions.
Both models must carry the Forge 17-bone rig; motion is a pure function of the frame number.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Euler, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_video as mv  # noqa: E402

X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)

# (first_s, last_s, cam_from, cam_to, look_from, look_to). Buddy falls near x=0, Gorilla stops at x=1.75.
SHOTS = [
    (0.0, 3.2, (0.0, -3.4, 0.55), (0.2, -2.9, 0.5), (-0.2, 0, 0.35), (0.2, 0, 0.25)),   # wide: walk, trip, fall
    (3.2, 5.4, (-0.6, -1.4, 0.3), (-0.3, -1.1, 0.35), (1.5, 0, 0.6), (1.7, 0, 0.7)),    # low over Buddy: Gorilla arrives
    (5.4, 9e9, (0.1, -1.6, 0.3), (0.3, -1.4, 0.35), (1.6, 0, 0.8), (1.7, 0, 0.85)),     # low hero shot: chest pounding
]


def import_actor(path, name, height):
    before = set(bpy.data.objects)
    if not path.lower().endswith(".glb") or not os.path.isfile(path):
        sys.exit(f"[FAIL] need an existing .glb: {path}")
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH" and o.visible_get()]
    arm = next((o for o in new if o.type == "ARMATURE"), None)
    if not meshes or arm is None:
        sys.exit(f"[FAIL] {path}: needs meshes and the Forge rig")
    lo, hi = mv.bbox(meshes)
    actor = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(actor)
    for o in new:
        if o.animation_data:
            o.animation_data_clear()
        if o.parent is None:
            mw = o.matrix_world.copy()
            o.parent = actor
            o.matrix_world = mw
            o.location -= Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    actor.scale = [height / max(hi.z - lo.z, 1e-6)] * 3
    return actor, mv.Rig(arm), meshes


def rots(rig, name, *turns):
    """Like Rig.rot but composes several armature-space turns (applied first to last)."""
    pb = rig.arm.pose.bones.get(name)
    if pb is None:
        return
    q = Quaternion()
    for axis, deg in turns:
        q = Quaternion(rig.to_arm @ Vector(axis), math.radians(deg)) @ q
    rest = pb.bone.matrix_local.to_quaternion()
    pb.rotation_quaternion = rest.inverted() @ q @ rest


def walk(rig, t, amp=28, speed=9.0):
    s = math.sin(t * speed)
    rig.rot("thigh.L", X, amp * s)
    rig.rot("thigh.R", X, -amp * s)
    rig.rot("shin.L", X, -abs(amp * s) * 0.6)
    rig.rot("shin.R", X, -abs(amp * s) * 0.6)


def buddy_pose(T, actor, rig):
    """Walk right from x=-0.9, trip at 1.9 s, fall flat on the face by 2.5 s, lie there with a twitch."""
    rig.reset()
    trip, land = 1.9, 2.5
    x = -0.9 + 0.42 * min(T, trip)
    fall = mv.ease((T - trip) / (land - trip))
    actor.location = (x + 0.35 * fall, 0, 0.12 * fall)
    # facing +X (Z 90), pitched forward about its own X axis as it falls
    actor.rotation_euler = Euler((math.radians(88 * fall), 0, math.radians(90)), "XYZ")
    if T < trip + 0.15:
        walk(rig, T, amp=30 * (1 - fall), speed=10)
        rig.rot("upper_arm.L", Y, 70 * (1 - fall))
        rig.rot("upper_arm.R", Y, -70 * (1 - fall))
    else:  # arms thrown forward, one leg kicked up, a small twitch on the floor
        tw = 6 * math.sin(T * 14) * max(0.0, 1 - (T - land) / 2.5) if T > land else 0
        rig.rot("upper_arm.L", Z, -70 * fall)
        rig.rot("upper_arm.R", Z, 70 * fall)
        rig.rot("thigh.R", X, -25 * fall + tw)
        rig.rot("head", X, -15 * fall)


def gorilla_pose(T, actor, rig):
    """Enter from the right at 3.0 s, stop facing Buddy at 4.6 s, lean back and pound the chest."""
    rig.reset()
    arrive = mv.ease((T - 3.0) / 1.6)
    actor.location = (3.1 - 1.35 * arrive, 0, 0)
    actor.rotation_euler = Euler((0, 0, math.radians(-90)), "XYZ")  # faces -X, towards Buddy
    if T < 4.6:
        walk(rig, T, amp=22 * (1 - mv.ease((T - 4.3) / 0.3)), speed=7)
        rig.rot("upper_arm.L", Y, 60)
        rig.rot("upper_arm.R", Y, -60)
        return
    k = mv.ease((T - 4.6) / 0.4)
    beat = max(0.0, math.sin((T - 5.0) * 2 * math.pi * 2.5)) if T > 5.0 else 0  # 2.5 hits per arm per second
    beat2 = max(0.0, -math.sin((T - 5.0) * 2 * math.pi * 2.5)) if T > 5.0 else 0
    rig.rot("spine", X, -12 * k)  # chest out
    rig.rot("head", X, 10 * k + 4 * (beat + beat2))  # chin down at the rival on each hit
    # upper arms swing to the front, forearms fold so the fists meet the chest, alternating
    # upper arms drop and swing forward, forearms fold in so the fists strike the chest, alternating
    rots(rig, "upper_arm.L", (Y, 45 * k), (Z, -(50 + 15 * beat) * k))
    rots(rig, "upper_arm.R", (Y, -45 * k), (Z, (50 + 15 * beat2) * k))
    rig.rot("forearm.L", Z, -(105 - 45 * beat) * k)
    rig.rot("forearm.R", Z, (105 - 45 * beat2) * k)


def main():
    a = mv.parse_args()
    os.makedirs(os.path.join(a.out, "frames"), exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    buddy, brig, m1 = import_actor(a.model, "Buddy", 0.85)
    gor, grig, m2 = import_actor(a.model2, "Gorilla", 1.2)
    sc = bpy.context.scene
    n = round(a.fps * a.duration)
    sc.render.fps, sc.frame_start, sc.frame_end = a.fps, 1, n
    sc.render.resolution_x, sc.render.resolution_y = a.width, a.height
    floor = mv.add_stage(sc)
    cam = sc.camera
    for f in range(1, n + 1):
        T = (f - 1) / a.fps
        s0, s1, p0, p1, l0, l1 = next(s for s in SHOTS if s[0] <= T < s[1])
        k = mv.ease((T - s0) / max(min(s1, a.duration) - s0, 1e-6))
        cam.location = Vector(p0).lerp(Vector(p1), k)
        cam.rotation_euler = (Vector(l0).lerp(Vector(l1), k) - cam.location).to_track_quat("-Z", "Y").to_euler()
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
        buddy_pose(T, buddy, brig)
        gorilla_pose(T, gor, grig)
        for act, rig in ((buddy, brig), (gor, grig)):
            act.keyframe_insert("location", frame=f)
            act.keyframe_insert("rotation_euler", frame=f)
            for pb in rig.arm.pose.bones:
                pb.keyframe_insert("rotation_quaternion", frame=f)

    def at(f, o):
        sc.frame_set(f)
        return o.matrix_world.translation.copy()
    checks = {
        "both_models_imported": bool(m1 and m2),
        "camera": sc.camera is not None,
        "lights": sum(o.type == "LIGHT" for o in sc.objects) >= 2,
        "floor_shadow_catcher": floor.is_shadow_catcher,
        "frame_count": sc.frame_end - sc.frame_start + 1 == n,
        "camera_changes_between_shots": (at(round(1.5 * a.fps), cam) - at(round(4 * a.fps), cam)).length > 0.3,
        "buddy_on_floor_after_fall": at(round(3 * a.fps), buddy).z < 0.2
            and abs(buddy.rotation_euler.x) > math.radians(80),
        "gorilla_in_front_of_buddy": 0.8 < at(n, gor).x - at(n, buddy).x < 1.8,
    }
    info = {"checks": checks, "frames": n, "fps": a.fps, "scene": "rival",
            "rig": f"{len(brig.arm.pose.bones)} + {len(grig.arm.pose.bones)} bones (skeletal animation)",
            "blender": bpy.app.version_string}
    mv.finish(a, checks, info)


if __name__ == "__main__":
    main()
