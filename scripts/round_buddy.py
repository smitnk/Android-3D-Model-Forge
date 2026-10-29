"""'round_buddy' generator: soft cartoon figure from a 24-view turnaround sheet (owner-supplied, AI-generated).

img2threejs method: measure the reference first, build from the measurements, review renders against it.
The sheet has no T-pose view (arms hang down in every view), so the arms are rebuilt horizontally from
their measured length/thickness; everything else follows the 0 deg (front) and 90 deg (side) silhouettes.

Inventory -> part
- big round head (slightly wider than tall), two upright oval eyes, open smile with tongue  -> Head (+ face texture)
- short neck, soft pear torso, rounded shoulders                                         -> Body
- tube arms, mitten hands with a thumb                                                   -> Body
- straight legs with a small gap, rounded feet pointing forward                          -> Body
- cream skin with black ink outline                                                       -> Skin material
Measured (fractions of height H, from assets/reference/round-buddy/*-raw.png masks):
 head z 0.63-1.00, half-width 0.206, half-depth 0.193 | neck z 0.62, half-width 0.08
 torso half-width ~0.11 (0.15 at hips), depth half 0.11 | crotch z 0.27, legs at x +-0.075, half-width 0.065
 feet z 0-0.07, half-width 0.09, length 0.29 with the toe 0.16 ahead of the body | arm length 0.33, thickness 0.07
"""
import os

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from clay_chibi import Meta

H = 1.2
REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "reference", "round-buddy")
SHOULDER_Z = 0.565 * H
REACH = 0.56 * H


def h(v):
    return v * H


def bones():
    sz = SHOULDER_Z
    b = [("root", (0, 0, 0), (0, 0, h(0.08)), None),
         ("pelvis", (0, 0, h(0.27)), (0, 0, h(0.40)), "root"),
         ("spine", (0, 0, h(0.40)), (0, 0, h(0.60)), "pelvis"),
         ("neck", (0, 0, h(0.60)), (0, 0, h(0.66)), "spine"),
         ("head", (0, 0, h(0.66)), (0, 0, H), "neck")]
    for s, x in (("L", 1), ("R", -1)):
        b += [(f"upper_arm.{s}", (h(0.10) * x, 0, sz), (h(0.27) * x, 0, sz), "spine"),
              (f"forearm.{s}", (h(0.27) * x, 0, sz), (h(0.44) * x, 0, sz), f"upper_arm.{s}"),
              (f"hand.{s}", (h(0.44) * x, 0, sz), (REACH * x, 0, sz), f"forearm.{s}"),
              (f"thigh.{s}", (h(0.075) * x, 0, h(0.30)), (h(0.075) * x, 0, h(0.17)), "pelvis"),
              (f"shin.{s}", (h(0.075) * x, 0, h(0.17)), (h(0.09) * x, 0, h(0.05)), f"thigh.{s}"),
              (f"foot.{s}", (h(0.09) * x, 0, h(0.05)), (h(0.09) * x, -h(0.14), h(0.02)), f"shin.{s}")]
    return b


def face_texture():
    """Front-view pixels with the head outline replaced by fill colour, so only the eyes/mouth project."""
    img = bpy.data.images.load(os.path.join(REF, "front-raw.png"), check_existing=True)
    w, hh = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(hh, w, 4)       # row 0 = bottom (Blender order)
    m = px[..., 3] > 0.5
    core = m.copy()
    for _ in range(4):  # erode: the outer 4 px are the drawn outline
        core = core & np.roll(core, 1, 0) & np.roll(core, -1, 0) & np.roll(core, 1, 1) & np.roll(core, -1, 1)
    fill = np.median(px[core][:, :3], axis=0)
    rgb = px[..., :3].copy()
    rgb[~core] = fill
    out = bpy.data.images.new("FaceTexture", w, hh, alpha=False)
    out.pixels[:] = np.dstack([rgb, np.ones((hh, w))]).ravel()
    out.pack()
    rows = np.where(m.any(1))[0]
    bottom_row_from_top = hh - 1 - rows.min()
    top_row_from_top = hh - 1 - rows.max()
    cols = np.where(m[rows.min() + 2:rows.min() + 6].any(0))[0]  # feet row: body axis
    cx = (cols.min() + cols.max()) / 2.0
    s = H / (bottom_row_from_top - top_row_from_top + 1)
    return out, fill, (cx, bottom_row_from_top, s, w, hh)


def build(a, material, part):
    tex, fill, (cx, bottom, s, w, hh) = face_texture()
    hexfill = "#%02X%02X%02X" % tuple(int(round(c * 255)) for c in fill)
    skin = material("Skin", a.skin or hexfill, 0.7)

    head = Meta("HeadMeta", 0.008)
    head.ellipsoid((0, 0, h(0.815)), h(0.205), h(0.19), h(0.185))
    head_obj = head.to_mesh_object("Head", 0.45)

    body = Meta("BodyMeta", 0.008)
    body.capsule((0, 0, h(0.56)), (0, 0, h(0.68)), h(0.07))           # neck (enters the head)
    body.ellipsoid((0, 0.005, h(0.50)), h(0.11), h(0.10), h(0.11))    # chest / shoulders
    body.ellipsoid((0, 0.01, h(0.37)), h(0.145), h(0.11), h(0.10))    # soft pear hips
    for x in (1, -1):
        # arm, horizontal (T-pose), slightly thicker toward the shoulder
        body.capsule((h(0.08) * x, 0, SHOULDER_Z), (h(0.30) * x, 0, SHOULDER_Z), h(0.038))
        body.capsule((h(0.28) * x, 0, SHOULDER_Z), (h(0.45) * x, 0, SHOULDER_Z), h(0.034))
        body.ellipsoid((h(0.50) * x, 0, SHOULDER_Z), h(0.06), h(0.042), h(0.048))    # mitten
        body.ellipsoid((h(0.46) * x, -h(0.045), SHOULDER_Z), h(0.025), h(0.025), h(0.02))  # thumb, forward
        body.capsule((h(0.075) * x, 0, h(0.33)), (h(0.078) * x, 0, h(0.09)), h(0.062))  # leg
        body.ellipsoid((h(0.09) * x, -h(0.03), h(0.04)), h(0.085), h(0.14), h(0.045))  # foot, toe forward
    body_obj = body.to_mesh_object("Body", 0.4)

    parts = [head_obj, body_obj]
    lo = min(v.co.z for o in parts for v in o.data.vertices)
    for o in parts:
        for v in o.data.vertices:
            v.co.z -= lo
        for poly in o.data.polygons:
            poly.use_smooth = True
        o.data.materials.append(skin)
        o["bone"] = ""

    # face: project the 0-degree drawing onto the front of the head
    face = material("Face", hexfill, 0.7)
    nt = face.node_tree
    node = nt.nodes.new("ShaderNodeTexImage")
    node.image = tex
    nt.links.new(node.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    me = head_obj.data
    me.materials.append(face)
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        if poly.normal.y < -0.35:
            poly.material_index = 1
        for li in poly.loop_indices:
            p = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = ((cx + p.x / s) / w, 1.0 - (bottom - p.z / s) / hh)
    return parts
