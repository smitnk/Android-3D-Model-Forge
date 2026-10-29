"""'clay_chibi' generator: a one-piece, sculpt-style chibi base mesh (Blender, headless).

Built from metaballs (so limbs blend smoothly like clay), converted to meshes:
  Head - oversized egg head, pointed nose, carved angry almond eye sockets
  Body - slim neck/torso, glutes, thin arms, palm + four fingers + thumb, flared legs, block boots
Faces -Y, left side +X, T-pose by construction. Uses the same 17 bone names as chibi_humanoid.
"""
import math

import bmesh
import bpy
from mathutils import Vector

SHOULDER_Z = 0.70   # proportions measured from the reference sheet: shoulders at ~51% of height
FIELD = 0.575  # metaball surface sits at ~0.575 * radius for stiffness 2, threshold 0.6


def bones():
    b = [("root", (0, 0, 0), (0, 0, 0.10), None),
         ("pelvis", (0, 0, 0.33), (0, 0, 0.45), "root"),
         ("spine", (0, 0, 0.45), (0, 0, 0.70), "pelvis"),
         ("neck", (0, 0, 0.70), (0, 0, 0.80), "spine"),
         ("head", (0, 0, 0.80), (0, 0, 1.30), "neck")]
    for s, x in (("L", 1), ("R", -1)):
        b += [(f"upper_arm.{s}", (0.05 * x, 0, SHOULDER_Z), (0.20 * x, 0, SHOULDER_Z), "spine"),
              (f"forearm.{s}", (0.20 * x, 0, SHOULDER_Z), (0.36 * x, 0, SHOULDER_Z), f"upper_arm.{s}"),
              (f"hand.{s}", (0.36 * x, 0, SHOULDER_Z), (0.50 * x, 0, SHOULDER_Z), f"forearm.{s}"),
              (f"thigh.{s}", (0.05 * x, 0, 0.38), (0.065 * x, 0, 0.22), "pelvis"),
              (f"shin.{s}", (0.065 * x, 0, 0.22), (0.085 * x, 0, 0.08), f"thigh.{s}"),
              (f"foot.{s}", (0.085 * x, 0, 0.08), (0.085 * x, -0.12, 0.03), f"shin.{s}")]
    return b


class Meta:
    """Collects metaball elements; sizes are given as SURFACE radii in metres."""

    def __init__(self, name, resolution):
        self.mb = bpy.data.metaballs.new(name)
        self.mb.resolution = self.mb.render_resolution = resolution
        self.mb.threshold = 0.6
        self.obj = bpy.data.objects.new(name, self.mb)
        bpy.context.scene.collection.objects.link(self.obj)

    def _el(self, kind, co, r):
        e = self.mb.elements.new(type=kind)
        e.co, e.radius, e.stiffness = Vector(co), r / FIELD, 2.0
        return e

    def ball(self, co, r):
        self._el("BALL", co, r)

    def ellipsoid(self, co, rx, ry, rz):
        e = self._el("ELLIPSOID", co, 1.0)
        e.size_x, e.size_y, e.size_z = rx, ry, rz

    def capsule(self, a, b, r):
        a, b = Vector(a), Vector(b)
        e = self._el("CAPSULE", (a + b) / 2, r)
        e.size_x = (b - a).length / 2
        e.rotation = Vector((1, 0, 0)).rotation_difference((b - a).normalized())

    def box(self, co, hx, hy, hz, round_r):
        e = self._el("CUBE", co, round_r)
        e.size_x, e.size_y, e.size_z = hx, hy, hz

    def to_mesh_object(self, name, decimate, before_decimate=None):
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(self.obj.evaluated_get(dg))
        bpy.data.objects.remove(self.obj)
        bpy.data.metaballs.remove(self.mb)
        me.name = name
        obj = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(obj)
        if before_decimate:
            before_decimate(obj)
        if decimate < 1.0:  # metaball meshes are dense; collapse keeps the shape
            mod = obj.modifiers.new("dec", "DECIMATE")
            mod.ratio = decimate
            dg = bpy.context.evaluated_depsgraph_get()
            baked = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
            obj.modifiers.clear()
            old, obj.data = obj.data, baked
            bpy.data.meshes.remove(old)
            baked.name = name
        return obj


def carve_eye_sockets(obj, depth=0.026):
    """Push front-facing head vertices inward inside two angry almond shapes (inner corners low)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    cu, cv, a, b, tilt = 0.095, 0.94, 0.072, 0.04, math.radians(18)
    moves = []
    for v in bm.verts:
        if v.co.y > -0.05:
            continue
        du, dv = abs(v.co.x) - cu, v.co.z - cv
        # rotate into the eye's frame; positive tilt raises the outer corner
        pu = du * math.cos(tilt) + dv * math.sin(tilt)
        pv = -du * math.sin(tilt) + dv * math.cos(tilt)
        if pv < 0:  # flatter lower lid
            pv *= 1.35
        r = (abs(pu) / a) ** 2.4 + (abs(pv) / b) ** 2.4
        if r < 1.0:
            t = min(1.0, (1.0 - r) / 0.3)  # 0 at rim -> 1 inside: soft but defined edge
            moves.append((v, -v.normal * depth * (t * t * (3 - 2 * t))))
    for v, d in moves:
        v.co += d
    # relax the carved area plus a 2-ring border so the socket rim is smooth, not stair-stepped
    region = {v for v, _ in moves}
    for _ in range(2):
        region |= {e.other_vert(v) for v in list(region) for e in v.link_edges}
    for _ in range(4):  # smooth_vert has no repeat argument in 4.2
        bmesh.ops.smooth_vert(bm, verts=list(region), factor=0.5,
                              use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.to_mesh(obj.data)
    bm.free()
    return len(moves)


def build(a, material):
    clay = material("Clay", a.skin or "#8F8B86", 0.8)

    head = Meta("HeadMeta", 0.006)
    head.ellipsoid((0, 0.005, 1.08), 0.25, 0.23, 0.215)       # wide round cranium (~40% of height)
    head.ellipsoid((0, -0.01, 0.93), 0.175, 0.16, 0.145)      # jaw / cheeks, soft rounded chin
    head.capsule((0, -0.19, 0.905), (0, -0.235, 0.855), 0.026)  # pointed wedge nose between the eyes
    carved = []
    head_obj = head.to_mesh_object("Head", 0.3, lambda o: carved.append(carve_eye_sockets(o)))

    body = Meta("BodyMeta", 0.0065)
    body.capsule((0, 0, 0.66), (0, 0, 0.84), 0.03)             # short neck (top hidden inside head)
    body.ellipsoid((0, 0, 0.63), 0.085, 0.058, 0.08)           # chest, sloping into the shoulders
    body.ellipsoid((0, 0, 0.51), 0.05, 0.043, 0.06)            # narrow waist
    body.ellipsoid((0, 0.005, 0.41), 0.095, 0.068, 0.07)       # hips
    for x in (1, -1):
        body.ellipsoid((0.042 * x, 0.035, 0.39), 0.046, 0.042, 0.052)  # glutes
        # arm: horizontal along X (T-pose), thin with a forearm swell
        body.capsule((0.04 * x, 0, SHOULDER_Z), (0.20 * x, 0, SHOULDER_Z), 0.025)
        body.ellipsoid((0.265 * x, 0, SHOULDER_Z), 0.065, 0.031, 0.033)
        body.capsule((0.20 * x, 0, SHOULDER_Z), (0.36 * x, 0, SHOULDER_Z), 0.02)
        body.ellipsoid((0.395 * x, 0, SHOULDER_Z), 0.04, 0.036, 0.017)  # palm (faces down)
        for y in (-0.026, -0.009, 0.009, 0.026):
            body.capsule((0.425 * x, y, SHOULDER_Z), (0.48 * x, y * 1.15, SHOULDER_Z), 0.012)
        body.capsule((0.38 * x, -0.032, SHOULDER_Z + 0.002), (0.415 * x, -0.062, SHOULDER_Z + 0.002), 0.012)
        # leg: slim thigh flaring into a wide calf that fuses into a big block boot (toe toward -Y)
        body.capsule((0.05 * x, 0, 0.39), (0.06 * x, 0, 0.26), 0.036)
        body.ball((0.066 * x, 0, 0.24), 0.045)
        body.ball((0.072 * x, 0.005, 0.20), 0.055)
        body.ball((0.078 * x, 0.01, 0.16), 0.065)    # calf flares into the boot shaft
        body.box((0.085 * x, -0.035, 0.08), 0.052, 0.09, 0.055, 0.025)
    body_obj = body.to_mesh_object("Body", 0.35)

    parts = [head_obj, body_obj]
    # ground exactly at z = 0 (metaball blending can shift the lowest point slightly)
    lo = min(v.co.z for o in parts for v in o.data.vertices)
    for o in parts:
        for v in o.data.vertices:
            v.co.z -= lo
        for poly in o.data.polygons:
            poly.use_smooth = True
        o.data.materials.append(clay)
    head_obj["bone"] = "head"
    body_obj["bone"] = ""  # empty = blended distance weights, see generate_model.auto_weights
    print(f"clay_chibi: carved {carved[0]} eye-socket vertices")
    return parts
