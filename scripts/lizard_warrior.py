"""'lizard_warrior' generator: armoured lizard-folk warrior from the owner's 12-view turnaround sheet.

img2threejs method (skills/img2threejs): measure the reference, carve the shape from its silhouettes,
project the drawing as the texture, review renders against the sheet.
- Masks come from the sheet's light WIREFRAME row (the dark armour does not separate from the dark
  background in the textured row); colours come from the TEXTURED row, aligned to it (offset -484 px).
- Body: visual hull (scripts/hull.py) of the 0-degree silhouette with the hanging arms removed x the
  90-degree profile (dagger cut out), remeshed to even quads.
- Arms: the sheet shows them hanging; the T-pose policy rebuilds them horizontally at their measured
  length/thickness, and maps the drawn hanging arm onto them (drawn "down" -> model "outward").
- Daggers: curved bone blades held in the fists, pointing forward so the T-pose stays readable.

Inventory -> part (blender-kiln reference-fidelity)
  spiked reptile head + snout, scaled red-brown skin with tribal pattern  -> Body (texture)
  black plated shoulder pads + chest plate, leather belt                  -> Body (shape + texture)
  layered tattered loincloth/skirt with tassels                           -> Body (shape + texture)
  digitigrade scaled legs, clawed feet                                    -> Body
  arms with scaled skin, fists                                            -> Arms (texture from the drawn arms)
  two curved bone daggers                                                 -> Dagger_L / Dagger_R
Measured (front panel, 325 px = H = 1.9 m, 5.85 mm/px): shoulder joint z 1.44, shoulder pads half-width
0.36, waist half-width 0.19, arm root x 0.26, upper arm d 0.14, forearm d 0.10, fist d 0.12,
shoulder->wrist 0.55, crotch z 0.39, legs at x +-0.175, head top 1.90.
Reference images: assets/reference/lizard-warrior/ (owner-supplied).
"""
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

import hull
from clay_chibi import Meta
from gorilla import body_centre, symmetric, textured_material

H = 1.9
VOXEL = 0.012
REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "reference", "lizard-warrior")
SHOULDER_Z = 1.44
ARM_ROOT_X = 0.26
ELBOW_X, WRIST_X, FIST_X = 0.52, 0.78, 0.84
# arm band in the front panel, as fractions of the figure height from the top, and the body half-band
ARM_BAND = (0.286, 0.809)
BODY_HALF_BAND = 0.126


def load_rgba(name):
    img = bpy.data.images.load(os.path.join(REF, name), check_existing=True)
    w, h = img.size
    return img, np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]  # row 0 = top


def remove_hanging_arms(mask):
    """Inside the arm band keep only runs centred on the body; outside it keep everything (head, pads, feet)."""
    out = mask.copy()
    rows = np.where(mask.any(1))[0]
    top, bot = rows.min(), rows.max()
    c = body_centre(mask)
    half = BODY_HALF_BAND * (bot - top + 1)
    for r in range(int(top + ARM_BAND[0] * (bot - top)), int(top + ARM_BAND[1] * (bot - top)) + 1):
        xs = np.where(mask[r])[0]
        for run in np.split(xs, np.where(np.diff(xs) > 1)[0] + 1):
            if len(run) and abs((run.min() + run.max()) / 2 - c) > half:
                out[r, run] = False
    return out


def bones():
    sz = SHOULDER_Z
    b = [("root", (0, 0, 0), (0, 0, 0.15), None),
         ("pelvis", (0, 0, 0.42), (0, 0, 0.75), "root"),
         ("spine", (0, 0, 0.75), (0, 0, sz), "pelvis"),
         ("neck", (0, 0, sz), (0, 0, 1.56), "spine"),
         ("head", (0, 0, 1.56), (0, 0, H), "neck")]
    for s, x in (("L", 1), ("R", -1)):
        b += [(f"upper_arm.{s}", (ARM_ROOT_X * x, 0, sz), (ELBOW_X * x, 0, sz), "spine"),
              (f"forearm.{s}", (ELBOW_X * x, 0, sz), (WRIST_X * x, 0, sz), f"upper_arm.{s}"),
              (f"hand.{s}", (WRIST_X * x, 0, sz), (0.91 * x, 0, sz), f"forearm.{s}"),
              (f"thigh.{s}", (0.175 * x, 0, 0.45), (0.175 * x, 0, 0.24), "pelvis"),
              (f"shin.{s}", (0.175 * x, 0, 0.24), (0.175 * x, 0, 0.07), f"thigh.{s}"),
              (f"foot.{s}", (0.175 * x, 0, 0.07), (0.175 * x, -0.18, 0.03), f"shin.{s}")]
    return b


def bake(obj, *mods):
    for kind, settings in mods:
        m = obj.modifiers.new(kind.lower(), kind)
        for k, v in settings.items():
            setattr(m, k, v)
    dg = bpy.context.evaluated_depsgraph_get()
    baked = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    obj.modifiers.clear()
    old, obj.data = obj.data, baked
    bpy.data.meshes.remove(old)
    return obj


class Panel:
    """Pixel mapping of one reference panel: centre column, bottom row, metres per pixel, arm axes."""

    def __init__(self, px, s):
        self.mask = px[..., 3] > 0.5
        self.h, self.w = self.mask.shape
        rows = np.where(self.mask.any(1))[0]
        self.top, self.bottom = rows.min(), rows.max()
        self.cx = body_centre(self.mask)
        self.s = s
        self.shoulder_row = self.bottom - SHOULDER_Z / s
        # drawn arm axis per row, per image side, from the outer runs inside the arm band
        self.axis = {}
        r0 = int(self.top + ARM_BAND[0] * (self.bottom - self.top))
        r1 = int(self.top + 0.6 * (self.bottom - self.top))  # down to the fists
        for side in (-1, 1):
            pts = []
            for r in range(r0, r1):
                xs = np.where(self.mask[r])[0]
                xs = xs[(xs - self.cx) * side > BODY_HALF_BAND * (self.bottom - self.top + 1)]
                if len(xs):
                    run = xs[xs * side >= (xs * side).max() - 30]
                    pts.append((r, (run.min() + run.max()) / 2))
            self.axis[side] = pts

    def body_uv(self, p, mirrored):
        col = self.cx - p.x / self.s if mirrored else self.cx + p.x / self.s
        return col / self.w, 1.0 - (self.bottom - p.z / self.s) / self.h

    def arm_uv(self, p, image_side):
        """Drawn hanging arm -> T-pose arm: distance along the arm -> rows down; height above the arm axis -> outward."""
        d = abs(p.x) - ARM_ROOT_X
        row = self.shoulder_row + d / self.s + 15  # +15 px: the drawn arm emerges below the shoulder pad
        pts = self.axis[image_side]
        r, c = min(pts, key=lambda rc: abs(rc[0] - row))
        col = c + image_side * (p.z - SHOULDER_Z) / self.s
        return col / self.w, 1.0 - row / self.h


def build(a, material, part):
    front_img, front_px = load_rgba("front.png")
    back_img, back_px = load_rgba("back.png")
    _, side_px = load_rgba("side.png")
    front_mask = front_px[..., 3] > 0.5
    rows = np.where(front_mask.any(1))[0]
    s = H / (rows.max() - rows.min() + 1)

    body_mask = symmetric(remove_hanging_arms(front_mask))
    occ, origin, _ = hull.carve(body_mask, side_px[..., 3] > 0.5, H, VOXEL)
    verts, quads = hull.boundary_quads(occ, origin, VOXEL)
    me = bpy.data.meshes.new("Body")
    me.from_pydata(verts.tolist(), [], quads.tolist())
    body = bpy.data.objects.new("Body", me)
    bpy.context.scene.collection.objects.link(body)
    bake(body, ("REMESH", {"mode": "VOXEL", "voxel_size": 0.013}), ("SMOOTH", {"factor": 0.7, "iterations": 5}))

    arms = Meta("ArmsMeta", 0.012)
    for x in (1, -1):
        arms.capsule((0.2 * x, 0, SHOULDER_Z), (ELBOW_X * x, 0, SHOULDER_Z), 0.07)     # upper arm
        arms.capsule((ELBOW_X * x, 0, SHOULDER_Z), (WRIST_X * x, 0, SHOULDER_Z), 0.052)  # forearm
        arms.ellipsoid((FIST_X * x, -0.005, SHOULDER_Z), 0.075, 0.062, 0.062)            # fist
    arms_obj = arms.to_mesh_object("Arms", 1.0)

    # centre the body's depth and put its feet on the ground; arms are already in final coordinates
    co = np.array([v.co[:] for v in body.data.vertices])
    shift = Vector((0, -(co[:, 1].min() + co[:, 1].max()) / 2, -co[:, 2].min()))
    for v in body.data.vertices:
        v.co += shift

    pf = Panel(front_px, s)
    pb = Panel(back_px, s)
    mat_f = textured_material("DrawingFront", front_img)
    mat_b = textured_material("DrawingBack", back_img)
    for o in (body, arms_obj):
        o.data.materials.append(mat_f)
        o.data.materials.append(mat_b)
        uv = o.data.uv_layers.new(name="UVMap")
        for poly in o.data.polygons:
            is_back = poly.normal.y > 0
            poly.material_index = 1 if is_back else 0
            poly.use_smooth = True
            panel = pb if is_back else pf
            for li in poly.loop_indices:
                p = o.data.vertices[o.data.loops[li].vertex_index].co
                if o is arms_obj:
                    # front panel: character's left (+x) is image right; back panel mirrors it
                    image_side = (1 if p.x > 0 else -1) * (-1 if is_back else 1)
                    uv.data[li].uv = panel.arm_uv(p, image_side)
                else:
                    uv.data[li].uv = panel.body_uv(p, mirrored=is_back)
        o["bone"] = ""

    parts = [body, arms_obj]
    bone_m = material("Bone", "#D9B98C", 0.55)
    for s_, x in (("L", 1), ("R", -1)):
        bm = bmesh.new()
        # curved blade: a chain of tapering cones from the fist, pointing forward (-Y) and slightly down
        base = Vector((FIST_X * x, -0.05, SHOULDER_Z - 0.01))
        segs, length = 5, 0.29
        # grip + pommel through the fist, out the back of the hand
        m = Matrix.Translation(base + Vector((0, 0.07, 0))) @ Vector((0, -1, 0)).to_track_quat("Z", "Y").to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=10, radius1=0.018, radius2=0.018,
                              depth=0.16, matrix=m)
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.026,
                                  matrix=Matrix.Translation(base + Vector((0, 0.15, 0))))
        for i in range(segs):
            t0, t1 = i / segs, (i + 1) / segs
            p0 = base + Vector((0.03 * x * math.sin(t0 * 2.5), -length * t0, -0.06 * t0 ** 2))
            p1 = base + Vector((0.03 * x * math.sin(t1 * 2.5), -length * t1, -0.06 * t1 ** 2))
            d = p1 - p0
            r0, r1 = 0.026 * (1 - t0) + 0.004, 0.026 * (1 - t1) + 0.004 * (i < segs - 1)
            m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
            bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=10, radius1=r0,
                                  radius2=max(r1, 0.0), depth=d.length * 1.08, matrix=m)
        me = bpy.data.meshes.new(f"Dagger_{s_}")
        bm.to_mesh(me)
        bm.free()
        obj = bpy.data.objects.new(f"Dagger_{s_}", me)
        bpy.context.scene.collection.objects.link(obj)
        for poly in me.polygons:
            poly.use_smooth = True
        me.materials.append(bone_m)
        obj["bone"] = f"hand.{s_}"
        parts.append(obj)
    print(f"lizard_warrior: body {len(body.data.vertices)} verts, arms {len(arms_obj.data.vertices)} verts")
    return parts
