"""'gorilla' generator: carved from the owner's turnaround sheet and textured with the drawing itself.

Method (img2threejs, skills/img2threejs): reconstruct the object from the reference rather than by eye.
  1. Shape  - visual hull (scripts/hull.py): T-pose front silhouette x side-view depth profile, with
              rounded cross-sections per row and per column so limbs are round, at 1 cm voxels.
  2. Surface - voxel remesh + smoothing in Blender -> clean, evenly spaced quads (like the sheet's wireframe).
  3. Look   - the T-pose front and back panels are projected onto the faces that face them
              (front panel on -Y faces, mirrored back panel on +Y faces), so fur, face, chest and toes
              are the drawing's own pixels.
  4. Rig    - bones placed from measurements of the carved volume (shoulder line, reach, crotch, legs).
Inventory (blender-kiln reference-fidelity): dome head + tuft, ears, muzzle, eyes, nostrils, pursed mouth,
pec/belly plates, furry shoulders/arms/legs with jagged edges, hands with fingers, wide feet with toes.
Concavities no silhouette shows (eye sockets, mouth) are carried by the texture, not the geometry.
Reference images: assets/reference/gorilla/ (owner-supplied).
"""
import os

import bpy
import numpy as np
from mathutils import Vector

import hull

HEIGHT = 1.5
VOXEL = 0.01
REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "reference", "gorilla")
M = {}  # measurements of the carved volume, filled by build(), used by bones()


def load_rgba(name):
    img = bpy.data.images.load(os.path.join(REF, name), check_existing=True)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]  # row 0 = top
    return img, px


def body_centre(mask):
    """Centre column of the hips/thighs (rows 30-45% up the figure): arms are drawn unequal, the body is not."""
    rows = np.where(mask.any(1))[0]
    top, bot = rows.min(), rows.max()
    band = range(int(bot - 0.45 * (bot - top)), int(bot - 0.30 * (bot - top)))
    return float(np.mean([(np.where(mask[r])[0].min() + np.where(mask[r])[0].max()) / 2 for r in band]))


def symmetric(mask):
    """T-pose policy: mirror the drawn silhouette about the body centre; returns a mask centred in its width."""
    c = int(round(body_centre(mask)))
    half = max(c, mask.shape[1] - 1 - c)
    pad = np.zeros((mask.shape[0], 2 * half + 1), bool)
    pad[:, half - c:half - c + mask.shape[1]] = mask
    return pad | pad[:, ::-1]


def projector(mask):
    """Front-panel pixel coords for a world point: returns (cx, bottom_row, metres_per_px, w, h)."""
    rows = np.where(mask.any(1))[0]
    return body_centre(mask), rows.max(), HEIGHT / (rows.max() - rows.min() + 1), mask.shape[1], mask.shape[0]


def measure(occ, origin):
    nx, ny, nz = occ.shape
    xs = origin[0] + (np.arange(nx) + 0.5) * VOXEL
    zs = origin[2] + (np.arange(nz) + 0.5) * VOXEL
    width = np.array([np.ptp(xs[occ[:, :, k].any(1)]) if occ[:, :, k].any() else 0 for k in range(nz)])
    M["shoulder_z"] = float(zs[np.argmax(width)])
    M["reach"] = float(np.abs(xs[occ.any((1, 2))]).max())
    centre = np.argmin(np.abs(xs))
    col = occ[centre].any(0)
    k_sh = int(np.argmax(width))
    gap = [k for k in range(k_sh, -1, -1) if not col[k]]  # scan DOWN from the shoulders (toes may touch)
    M["crotch_z"] = float(zs[gap[0]] + VOXEL)
    k = int(gap[0] * 0.5)
    right = occ[:, :, k].any(1) & (xs > 0)
    M["leg_x"] = float(xs[right].mean())
    M["top_z"] = float(zs[np.where(occ.any((0, 1)))[0].max()])


def bones():
    sz, r, cz, lx, top = M["shoulder_z"], M["reach"], M["crotch_z"], M["leg_x"], M["top_z"]
    neck = sz + 0.08
    b = [("root", (0, 0, 0), (0, 0, 0.12), None),
         ("pelvis", (0, 0, cz), (0, 0, cz + 0.15), "root"),
         ("spine", (0, 0, cz + 0.15), (0, 0, sz), "pelvis"),
         ("neck", (0, 0, sz), (0, 0, neck), "spine"),
         ("head", (0, 0, neck), (0, 0, top), "neck")]
    for s, x in (("L", 1), ("R", -1)):
        b += [(f"upper_arm.{s}", (0.2 * x, 0, sz), (0.55 * r * x, 0, sz), "spine"),
              (f"forearm.{s}", (0.55 * r * x, 0, sz), (0.84 * r * x, 0, sz), f"upper_arm.{s}"),
              (f"hand.{s}", (0.84 * r * x, 0, sz), (r * x, 0, sz), f"forearm.{s}"),
              (f"thigh.{s}", (lx * x, 0, cz + 0.05), (lx * x, 0, cz * 0.5), "pelvis"),
              (f"shin.{s}", (lx * x, 0, cz * 0.5), (lx * x, 0, 0.08), f"thigh.{s}"),
              (f"foot.{s}", (lx * x, 0, 0.08), (lx * x, -0.18, 0.03), f"shin.{s}")]
    return b


def textured_material(name, img):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    bsdf = nt.nodes["Principled BSDF"]
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.85
    return m


def build(a, material, part):
    front_img, front_px = load_rgba("tpose-front.png")
    back_img, back_px = load_rgba("tpose-back.png")
    _, side_px = load_rgba("side-right.png")
    front = symmetric(front_px[..., 3] > 0.5)
    side = side_px[..., 3] > 0.5

    occ, origin, _ = hull.carve(front, side, HEIGHT, VOXEL)
    measure(occ, origin)
    verts, quads = hull.boundary_quads(occ, origin, VOXEL)

    me = bpy.data.meshes.new("Body")
    me.from_pydata(verts.tolist(), [], quads.tolist())
    obj = bpy.data.objects.new("Body", me)
    bpy.context.scene.collection.objects.link(obj)
    rem = obj.modifiers.new("remesh", "REMESH")  # voxel stairs -> even quads
    rem.mode, rem.voxel_size = "VOXEL", 0.012
    sm = obj.modifiers.new("smooth", "SMOOTH")
    sm.factor, sm.iterations = 0.8, 6
    dg = bpy.context.evaluated_depsgraph_get()
    baked = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    obj.modifiers.clear()
    old, obj.data = obj.data, baked
    bpy.data.meshes.remove(old)
    baked.name = "Body"
    me = obj.data

    # ground + centre depth
    co = np.array([v.co[:] for v in me.vertices])
    shift = Vector((0, -(co[:, 1].min() + co[:, 1].max()) / 2, -co[:, 2].min()))
    for v in me.vertices:
        v.co += shift

    # project the drawing: front panel on -Y faces, mirrored back panel on +Y faces
    mat_f = textured_material("DrawingFront", front_img)
    mat_b = textured_material("DrawingBack", back_img)
    me.materials.append(mat_f)
    me.materials.append(mat_b)
    pf = projector(front_px[..., 3] > 0.5)
    pb = projector(back_px[..., 3] > 0.5)
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        is_back = poly.normal.y > 0
        poly.material_index = 1 if is_back else 0
        poly.use_smooth = True
        cx, bottom, s, w, h = pb if is_back else pf
        for li in poly.loop_indices:
            p = me.vertices[me.loops[li].vertex_index].co
            col = cx - p.x / s if is_back else cx + p.x / s
            row = bottom - p.z / s
            uv.data[li].uv = (col / w, 1.0 - row / h)

    obj["bone"] = ""  # blended distance weights
    print(f"gorilla: {len(me.vertices)} verts, measurements {M}")
    return [obj]
