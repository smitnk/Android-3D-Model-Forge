"""'lizard_refined' generator: AI template (TripoSR) + 12-view refinement -> separate, textured, rigged parts.

Pipeline (img2threejs: reconstruct from the reference, verify against it):
  1. Template  - assets/reference/lizard-warrior/triposr.glb (made by the "AI Template (TripoSR, CPU)" workflow
                 from the front view): real volume, guessed depth, soft detail.
  2. Fit       - scale its width/depth so its silhouettes match the 0/90/180/270-degree views of the sheet.
  3. Trim      - voxelise it and keep only voxels inside ALL 12 sheet silhouettes (assets/.../views/, made by
                 scripts/prep_turnaround.py); mirror for T-pose symmetry; remesh to even quads.
  4. Texture   - every face takes the sheet pixels of the view that faces it best and actually sees it
                 (occlusion ray test): sharp drawing detail on all sides instead of blurred vertex colour.
  5. Parts     - faces are labelled by body region + sheet colour: Armour (dark desaturated plates on the
                 torso), Loincloth (belt..knees), dagger blobs (bone colour; removed), skin. Armour and
                 Loincloth become separate shell objects with thickness and their own metal / cloth shading.
  6. T-pose    - the sheet's hanging arms are rotated about the shoulder to horizontal (blended at the
                 armpit), clean procedural daggers go in the fists, the usual 17-bone rig follows.
Hanging-pose arm landmarks measured on the 0-degree view (|x|, z in metres, H = 1.9): shoulder (0.26, 1.44),
wrist (0.40, 0.88), fist centre (0.41, 0.82). Legs at x +-0.175, crotch z 0.39.
"""
import json
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import hull
from lizard_warrior import bake, daggers, remove_hanging_arms

H = 1.9
VOX = 0.01
REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "reference", "lizard-warrior")
SH = np.array([0.26, 1.44])
WR = np.array([0.40, 0.88])
FIST = np.array([0.41, 0.82])
ARMOUR_Z = (0.58 * H, 0.86 * H)
CLOTH_Z = (0.24 * H, 0.53 * H)


def bones():
    up = float(np.linalg.norm(WR - SH)) * 0.5
    reach = SH[0] + float(np.linalg.norm(FIST - SH)) + 0.06
    sz = SH[1]
    b = [("root", (0, 0, 0), (0, 0, 0.15), None),
         ("pelvis", (0, 0, 0.42), (0, 0, 0.8), "root"),
         ("spine", (0, 0, 0.8), (0, 0, sz), "pelvis"),
         ("neck", (0, 0, sz), (0, 0, 1.58), "spine"),
         ("head", (0, 0, 1.58), (0, 0, H), "neck")]
    for s, x in (("L", 1), ("R", -1)):
        b += [(f"upper_arm.{s}", (SH[0] * x, 0, sz), ((SH[0] + up) * x, 0, sz), "spine"),
              (f"forearm.{s}", ((SH[0] + up) * x, 0, sz), ((SH[0] + 2 * up) * x, 0, sz), f"upper_arm.{s}"),
              (f"hand.{s}", ((SH[0] + 2 * up) * x, 0, sz), (reach * x, 0, sz), f"forearm.{s}"),
              (f"thigh.{s}", (0.175 * x, 0, 0.45), (0.175 * x, 0, 0.24), "pelvis"),
              (f"shin.{s}", (0.175 * x, 0, 0.24), (0.175 * x, 0, 0.07), f"thigh.{s}"),
              (f"foot.{s}", (0.175 * x, 0, 0.07), (0.175 * x, -0.18, 0.03), f"shin.{s}")]
    return b


# ---------------------------------------------------------------- reference views
def load_views():
    meta = json.load(open(os.path.join(REF, "views", "views.json")))
    views = []
    for v in meta["views"]:
        img = bpy.data.images.load(os.path.join(REF, "views", v["file"]), check_existing=True)
        w, h = img.size
        px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]  # row 0 = top
        v.update(img=img, rgb=px[..., :3], mask=px[..., 3] > 0.5, w=w, h=h, s=v["m_per_px"],
                 cam=np.array([math.sin(math.radians(v["angle"])), -math.cos(math.radians(v["angle"])), 0.0]))
        views.append(v)
    return views


def dilate(m, n):
    for _ in range(n):
        m = m | np.roll(m, 1, 0) | np.roll(m, -1, 0) | np.roll(m, 1, 1) | np.roll(m, -1, 1)
    return m


def image_xy(pts, v, axis=None):
    """Sheet pixel (col, row) of world points in view v: the turntable shows the figure rotated by -angle."""
    a = math.radians(v["angle"])
    qx = pts[:, 0] * math.cos(a) + pts[:, 1] * math.sin(a)
    return (v["axis"] if axis is None else axis) + qx / v["s"], v["bottom_row"] - pts[:, 2] / v["s"]


def silhouette_iou(pts, v, axis):
    col, row = image_xy(pts, v, axis)
    ci, ri = np.round(col).astype(int), np.round(row).astype(int)
    ok = (ci >= 0) & (ci < v["w"]) & (ri >= 0) & (ri < v["h"])
    sil = np.zeros((v["h"], v["w"]), bool)
    sil[ri[ok], ci[ok]] = True
    sil = dilate(sil, 1)
    return (sil & v["mask"]).sum() / max(1, (sil | v["mask"]).sum())


def fit_axis(pts, v):
    """Column of the turntable axis: match silhouette centroids, then refine by IoU."""
    col, _ = image_xy(pts, v, 0.0)
    guess = np.where(v["mask"])[1].mean() - col.mean()
    return max((silhouette_iou(pts, v, guess + d), guess + d) for d in range(-6, 7))[1]


# ---------------------------------------------------------------- template -> trimmed volume
def load_template():
    bpy.ops.import_scene.gltf(filepath=os.path.join(REF, "triposr.glb"))
    verts, faces = [], []
    for o in [o for o in bpy.context.scene.objects if o.type == "MESH"]:
        off = len(verts)
        verts += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
        faces += [[off + i for i in p.vertices] for p in o.data.polygons]
    for o in list(bpy.context.scene.objects):
        bpy.data.objects.remove(o)
    v = np.array(verts)
    v[:, 2] -= v[:, 2].min()
    v *= H / v[:, 2].max()
    v[:, :2] -= (v[:, :2].min(0) + v[:, :2].max(0)) / 2
    return v, faces


def voxelise(v, faces):
    bvh = BVHTree.FromPolygons([Vector(p) for p in v], faces)
    half = np.abs(v[:, 0]).max() + 2 * VOX               # grid symmetric about x = 0 (for mirroring)
    lo = np.array([-half, v[:, 1].min() - 2 * VOX, -VOX])
    n = np.ceil((np.array([half, v[:, 1].max() + 2 * VOX, H + VOX]) - lo) / VOX).astype(int)
    occ = np.zeros(n, bool)
    zs = lo[2] + (np.arange(n[2]) + 0.5) * VOX
    up = Vector((0, 0, 1))
    for i in range(n[0]):
        x = lo[0] + (i + 0.5) * VOX
        for j in range(n[1]):
            y = lo[1] + (j + 0.5) * VOX
            hits, o = [], Vector((x, y, lo[2]))
            while len(hits) < 40:
                loc, _, _, _ = bvh.ray_cast(o, up)
                if loc is None:
                    break
                hits.append(loc.z)
                o = Vector((x, y, loc.z + 1e-4))
            for a, b in zip(hits[0::2], hits[1::2]):  # parity: inside between entry and exit
                occ[i, j, (zs > a) & (zs < b)] = True
    return occ, lo


def trim_and_symmetrise(occ, lo, views):
    idx = np.argwhere(occ)
    pts = lo + (idx + 0.5) * VOX
    keep = np.ones(len(pts), bool)
    for v in views:
        m = dilate(v["mask"], 2)                       # tolerance: masks are drawn, alignment is fitted
        col, row = image_xy(pts, v)
        ci, ri = np.round(col).astype(int), np.round(row).astype(int)
        ok = (ci >= 0) & (ci < v["w"]) & (ri >= 0) & (ri < v["h"])
        inside = np.zeros(len(pts), bool)
        inside[ok] = m[ri[ok], ci[ok]]
        keep &= inside
    out = np.zeros_like(occ)
    out[tuple(idx[keep].T)] = True
    print(f"lizard_refined: trim kept {keep.mean():.1%} of {len(pts)} voxels")
    return out | out[::-1]                             # T-pose policy: left/right symmetric


# ---------------------------------------------------------------- texture + labels
def torso_half_width(front):
    """Half-width (m) of the body WITHOUT the hanging arms, per front-view row."""
    body = remove_hanging_arms(front["mask"])
    hw = np.zeros(front["h"])
    for r in range(front["h"]):
        xs = np.where(body[r])[0]
        if len(xs):
            hw[r] = np.abs(xs - front["axis"]).max() * front["s"]
    return lambda z: hw[int(np.clip(round(front["bottom_row"] - z / front["s"]), 0, front["h"] - 1))]


def project_and_label(obj, views, hw):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bvh = BVHTree.FromBMesh(bm)
    bm.free()
    uv = me.uv_layers.new(name="UVMap")
    co = np.array([v.co[:] for v in me.vertices])
    labels, bone_like = [], []
    for poly in me.polygons:
        n, c = np.array(poly.normal[:]), np.array(poly.center[:])
        order = sorted(range(len(views)), key=lambda k: -float(n @ views[k]["cam"]))
        pick = order[0]
        for k in order[:4]:                             # best-facing view that actually sees this face
            if float(n @ views[k]["cam"]) < 0.1:
                break
            hit = bvh.ray_cast(Vector(c + n * 0.004), Vector(views[k]["cam"]), 3.0)
            if hit[0] is None:
                pick = k
                break
        v = views[pick]
        poly.material_index = pick
        col, row = image_xy(co[list(poly.vertices)], v)
        for li, cc, rr in zip(poly.loop_indices, col, row):
            uv.data[li].uv = (cc / v["w"], 1.0 - rr / v["h"])
        cc, rr = image_xy(c[None], v)
        r, g, b = v["rgb"][int(np.clip(rr[0], 0, v["h"] - 1)), int(np.clip(cc[0], 0, v["w"] - 1))] * 255
        luma, chroma, ax, z = 0.299 * r + 0.587 * g + 0.114 * b, max(r, g, b) - min(r, g, b), abs(c[0]), c[2]
        if luma > 125 and r - b > 30:
            bone_like.append((round(z, 2), round(ax, 2), round(hw(z), 2), v["angle"]))
        if luma > 125 and r - b > 30 and z < 0.62 * H and ax > hw(z) - 0.02:
            labels.append("dagger")
        elif ARMOUR_Z[0] < z < ARMOUR_Z[1] and ax <= hw(z) + 0.02 and chroma < 32:
            labels.append("armour")
        elif CLOTH_Z[0] < z < CLOTH_Z[1] and ax <= hw(z) + 0.02:
            labels.append("cloth")
        else:
            labels.append("skin")
    print(f"lizard_refined: {len(bone_like)} bone-coloured faces (z, |x|, torso half-width, view): {bone_like[:12]}")
    return smooth_labels(me, labels)


def smooth_labels(me, labels, passes=2):
    """Majority vote over edge-neighbours: removes speckles so parts have clean borders."""
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    nbrs = [[g.index for e in f.edges for g in e.link_faces if g.index != f.index] for f in bm.faces]
    bm.free()
    for _ in range(passes):
        new = []
        for i, lab in enumerate(labels):
            votes = [labels[j] for j in nbrs[i]] + [lab]
            new.append(max(set(votes), key=votes.count))
        labels = new
    return labels


def material_set(views, prefix, metallic, roughness):
    mats = []
    for v in views:
        m = bpy.data.materials.new(f"{prefix}{v['angle']:03d}")
        m.use_nodes = True
        nt = m.node_tree
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = v["img"]
        bsdf = nt.nodes["Principled BSDF"]
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        mats.append(m)
    return mats


def shell(src, labels, which, name, offset, thickness, mats):
    """Copy the labelled faces into their own object, lifted off the body and given thickness."""
    me = src.data.copy()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if labels[f.index] != which], context="FACES")
    bm.normal_update()
    for vtx in bm.verts:
        vtx.co += vtx.normal * offset
    bm.to_mesh(me)
    bm.free()
    bake(obj, ("SOLIDIFY", {"thickness": thickness, "offset": -1.0}))
    obj.data.materials.clear()
    for m in mats:
        obj.data.materials.append(m)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


# ---------------------------------------------------------------- pose
def raise_arms(objs, hw):
    """Rotate the hanging arms about the shoulder to horizontal; blend over 6 cm outside the torso."""
    d = WR - SH
    theta = -math.atan2(d[1], d[0])                    # angle that maps shoulder->wrist onto +x
    c, s = math.cos(theta), math.sin(theta)
    for o in objs:
        for vtx in o.data.vertices:
            x, y, z = vtx.co
            if z > SH[1] + 0.08 or z < 0.3:  # above the feet: the hanging dagger tips reach ~0.39 m
                continue
            w = min(1.0, max(0.0, (abs(x) - hw(z)) / 0.06))
            if w == 0:
                continue
            u, t = abs(x) - SH[0], z - SH[1]
            u2, t2 = u * c - t * s, u * s + t * c
            nx, nz = math.copysign(SH[0] + u2, x), SH[1] + t2
            vtx.co = (x + w * (nx - x), y, z + w * (nz - z))


def build(a, material, part):
    views = load_views()
    v, faces = load_template()

    # 2. fit width/depth of the guessed template to the 0/90/180/270 silhouettes
    sample = v[:: max(1, len(v) // 20000)]
    best = None
    for kx in np.arange(0.85, 1.16, 0.05):
        for ky in np.arange(0.6, 1.51, 0.05):
            p = sample * [kx, ky, 1]
            score = np.mean([silhouette_iou(p, views[i], fit_axis(p, views[i])) for i in (0, 3, 6, 9)])
            if best is None or score > best[0]:
                best = (score, kx, ky)
    print(f"lizard_refined: template fit IoU {best[0]:.3f} with width x{best[1]:.2f}, depth x{best[2]:.2f}")
    v = v * [best[1], best[2], 1]
    front = views[0]
    shift = (fit_axis(v[::10], front) - front["axis_col"]) * front["s"]  # put the body axis (hips) at x = 0
    v[:, 0] += shift
    for view in views:
        view["axis"] = fit_axis(v[::10], view)
    print("lizard_refined: view IoU " + " ".join(f"{view['angle']}:{silhouette_iou(v[::10], view, view['axis']):.2f}" for view in views))

    # 3. voxelise, trim with every view, mirror, remesh
    occ, lo = voxelise(v, faces)
    occ = trim_and_symmetrise(occ, lo, views)
    verts, quads = hull.boundary_quads(occ, lo, VOX)
    me = bpy.data.meshes.new("Body")
    me.from_pydata(verts.tolist(), [], quads.tolist())
    body = bpy.data.objects.new("Body", me)
    bpy.context.scene.collection.objects.link(body)
    bake(body, ("REMESH", {"mode": "VOXEL", "voxel_size": 0.011}), ("SMOOTH", {"factor": 0.6, "iterations": 4}))
    zmin = min(p.co.z for p in body.data.vertices)
    for vtx in body.data.vertices:
        vtx.co.z -= zmin

    # 4. textures + 5. labels
    hw = torso_half_width(front)
    labels = project_and_label(body, views, hw)
    for m in material_set(views, "Skin", 0.0, 0.8):
        body.data.materials.append(m)
    counts = {k: labels.count(k) for k in ("skin", "armour", "cloth", "dagger")}
    print(f"lizard_refined: face labels {counts}")
    armour = shell(body, labels, "armour", "Armour", 0.004, 0.008, material_set(views, "Armour", 0.55, 0.35))
    cloth = shell(body, labels, "cloth", "Loincloth", 0.003, 0.005, material_set(views, "Cloth", 0.0, 0.95))
    bm = bmesh.new()                                     # body: drop the blobby template daggers, close the holes
    bm.from_mesh(body.data)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if labels[f.index] == "dagger"], context="FACES")
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
    bm.to_mesh(body.data)
    bm.free()
    for p in body.data.polygons:
        p.use_smooth = True

    # 6. T-pose, clean daggers
    raise_arms([body, armour, cloth], hw)
    fist_x = SH[0] + float(np.linalg.norm(FIST - SH))
    parts = [body, armour, cloth] + daggers(material("Bone", "#D9B98C", 0.55), fist_x, SH[1])
    for o in (body, armour, cloth):
        o["bone"] = ""
    print(f"lizard_refined: body {len(body.data.vertices)} verts, armour {len(armour.data.vertices)}, "
          f"loincloth {len(cloth.data.vertices)}")
    return parts
