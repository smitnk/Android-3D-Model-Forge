"""'gorilla' generator: stylised cartoon gorilla in T-pose (Blender, headless).

Built with the blender-kiln reference-fidelity method (skills/blender-kiln/references/reference-fidelity.md):
detail inventory first, proportions MEASURED from the reference silhouette (fractions of height H),
every part entering the part it joins.

Inventory (reference: front + back turnaround sheet)
- fur body: dome head with brow ridge, huge shoulders/traps, barrel chest, belly, glutes  -> Fur
- arms: very long (span 1.08 H), thick upper arm, muscular forearm, horizontal (T-pose)   -> Fur
- legs: short and thick (crotch at 0.32 H), slightly apart                                -> Fur
- light skin: big muzzle, eye mask, ears, pec plates + belly, hands with fingers, feet with toes -> Skin
- eyes: big white ovals, small black pupils looking forward                               -> Eye_*, Pupil_*
- nose: two nostrils on a soft bump; small pursed lips                                     -> Skin, Nostril_*
- hair tuft on top of the head                                                            -> HairTuft_*
- jagged fur tufts on the silhouette of shoulders, arms, thighs, calves (all views)            -> Tufts_*
Measured from the 360 turnaround (side view): body depth ~0.40 H with the belly pushed forward,
head depth ~0.24 H including a muzzle that sticks out past the face. Fur #4C4054, skin #8C8192 (rendered darker to match: #3E3447 / #7E7286).
Measured (H = 1.5 m): shoulder line 0.70 H, hand reach 0.52 H from centre, chest half-width 0.20 H,
waist half-width 0.10 H, hips 0.14 H, leg centres +-0.11 H, feet 0.23 H wide, head top 0.97 H.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from clay_chibi import Meta

SHOULDER_Z = 1.05


def bones():
    b = [("root", (0, 0, 0), (0, 0, 0.12), None),
         ("pelvis", (0, 0, 0.45), (0, 0, 0.62), "root"),
         ("spine", (0, 0, 0.62), (0, 0, SHOULDER_Z), "pelvis"),
         ("neck", (0, 0, SHOULDER_Z), (0, 0, 1.15), "spine"),
         ("head", (0, 0, 1.15), (0, 0, 1.48), "neck")]
    for s, x in (("L", 1), ("R", -1)):
        b += [(f"upper_arm.{s}", (0.22 * x, 0, SHOULDER_Z), (0.48 * x, 0, SHOULDER_Z), "spine"),
              (f"forearm.{s}", (0.48 * x, 0, SHOULDER_Z), (0.66 * x, 0, SHOULDER_Z), f"upper_arm.{s}"),
              (f"hand.{s}", (0.66 * x, 0, SHOULDER_Z), (0.79 * x, 0, SHOULDER_Z), f"forearm.{s}"),
              (f"thigh.{s}", (0.15 * x, 0, 0.50), (0.16 * x, 0, 0.28), "pelvis"),
              (f"shin.{s}", (0.16 * x, 0, 0.28), (0.17 * x, 0, 0.08), f"thigh.{s}"),
              (f"foot.{s}", (0.17 * x, 0, 0.08), (0.17 * x, -0.20, 0.03), f"shin.{s}")]
    return b


def tuft_ring(bm, a, b, radius, rings, per_ring, length, start=0.0, skip=None):
    """Add fur-tuft cones around the segment a->b: base sinks into the fur, tips point outward and
    lean toward b (fur hangs toward the extremity). `skip(theta)` leaves gaps, e.g. where skin shows."""
    a, b = Vector(a), Vector(b)
    axis = (b - a).normalized()
    u = axis.orthogonal().normalized()
    v = axis.cross(u)
    for i in range(rings):
        t = (i + 0.5) / rings
        c = a + (b - a) * t
        for j in range(per_ring):
            th = 2 * math.pi * (j + 0.5 * (i % 2)) / per_ring + start  # staggered rings
            if skip and skip(th, u, v):
                continue
            radial = u * math.cos(th) + v * math.sin(th)
            # a flat lock: lies close to the surface, leans toward b and hangs down (gravity in a T-pose)
            d = (radial * 0.45 + axis * 0.6 + Vector((0, 0, -0.45))).normalized()
            tangent = d.cross(radial).normalized()
            normal = tangent.cross(d)
            basis = Matrix((tangent, normal, d)).transposed().to_4x4()
            m = (Matrix.Translation(c + radial * radius * 0.86 + d * length * 0.45)
                 @ basis @ Matrix.Diagonal((0.075, 0.022, length, 1)))
            bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8,
                                  radius1=0.5, radius2=0.0, depth=1.0, matrix=m)


def tuft_object(name, bone, mat, fn):
    bm = bmesh.new()
    fn(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    for poly in me.polygons:
        poly.use_smooth = True
    me.materials.append(mat)
    obj["bone"] = bone
    return obj


def build(a, material, part):
    fur_m = material("Fur", a.hair or "#3E3447", 0.85)
    skin_m = material("Skin", a.skin or "#7E7286", 0.6)
    eye_m = material("EyeWhite", "#FFFFFF", 0.3)
    pupil_m = material("Pupil", "#121018", 0.15)
    dark_m = material("Nostril", "#2A2433", 0.6)

    fur = Meta("FurMeta", 0.011)
    fur.ellipsoid((0, 0.04, 1.28), 0.135, 0.15, 0.185)        # dome head, high at the back
    fur.capsule((-0.085, -0.10, 1.355), (0.085, -0.10, 1.355), 0.03)  # brow ridge
    fur.ellipsoid((0, 0.06, 1.12), 0.26, 0.2, 0.12)           # trapezius / hunched shoulder mass
    fur.ellipsoid((0, 0.0, 0.95), 0.29, 0.25, 0.18)           # barrel chest (side view: deep)
    fur.ellipsoid((0, -0.02, 0.74), 0.2, 0.25, 0.16)          # belly core, pushed forward
    fur.ellipsoid((0, 0.03, 0.55), 0.22, 0.2, 0.13)           # hips
    for x in (1, -1):
        fur.ellipsoid((0.10 * x, 0.15, 0.52), 0.115, 0.1, 0.13)        # glutes
        fur.ellipsoid((0.24 * x, 0.01, SHOULDER_Z + 0.03), 0.13, 0.12, 0.13)  # bulky deltoid
        fur.ellipsoid((0.38 * x, 0, SHOULDER_Z), 0.15, 0.09, 0.085)   # thick upper arm
        fur.ellipsoid((0.56 * x, 0, SHOULDER_Z - 0.005), 0.12, 0.075, 0.07)  # forearm
        fur.ellipsoid((0.15 * x, 0, 0.37), 0.13, 0.12, 0.14)          # thigh
        fur.ellipsoid((0.165 * x, 0, 0.20), 0.135, 0.125, 0.12)       # calf (enters the foot)
    fur_obj = fur.to_mesh_object("Fur", 0.3)

    skin = Meta("SkinMeta", 0.0075)
    skin.ellipsoid((0, -0.13, 1.17), 0.15, 0.13, 0.11)        # big muzzle, protruding (side view)
    skin.ellipsoid((0, -0.10, 1.30), 0.10, 0.06, 0.07)        # eye mask
    skin.ball((0, -0.235, 1.225), 0.035)                      # nose bump
    skin.ball((0.012, -0.255, 1.115), 0.024)                  # pursed lips
    for x in (1, -1):
        skin.ellipsoid((0.135 * x, 0.0, 1.28), 0.03, 0.05, 0.06)     # ears
        skin.ellipsoid((0.10 * x, -0.2, 0.965), 0.115, 0.07, 0.1)    # pec plates (touch the belly)
        # hand: palm entering the forearm, four fingers pointing outward, thumb forward
        skin.ellipsoid((0.695 * x, -0.005, SHOULDER_Z), 0.075, 0.065, 0.055)
        for z in (-0.036, -0.012, 0.012, 0.036):
            skin.capsule((0.74 * x, -0.012, SHOULDER_Z + z), (0.80 * x, -0.025, SHOULDER_Z + z * 1.1), 0.02)
        skin.capsule((0.68 * x, -0.055, SHOULDER_Z - 0.01), (0.72 * x, -0.1, SHOULDER_Z - 0.035), 0.024)
        # foot: wide sole with a row of toes at the front (toe toward -Y)
        skin.ellipsoid((0.19 * x, -0.05, 0.055), 0.12, 0.17, 0.06)     # inner edges stay apart
        for i, dx in enumerate((-0.075, -0.025, 0.025, 0.075)):
            skin.ball(((0.19 + dx) * x, -0.20 + 0.012 * abs(i - 1.5), 0.04), 0.034)
        skin.ball(((0.19 + 0.125) * x, -0.08, 0.045), 0.04)            # big toe on the outer side
    skin.ellipsoid((0, -0.2, 0.76), 0.17, 0.1, 0.17)          # round belly plate (blends with the pecs)
    skin_obj = skin.to_mesh_object("Skin", 0.35)

    parts = [fur_obj, skin_obj]
    for s, x in (("L", 1), ("R", -1)):
        parts.append(part(f"Eye_{s}", "sphere", (0.075, 0.035, 0.095), (0.045 * x, -0.157, 1.31), eye_m, "head",
                          segments=24))
        parts.append(part(f"Pupil_{s}", "sphere", (0.02, 0.012, 0.022), (0.04 * x, -0.174, 1.305), pupil_m, "head",
                          segments=12))
        parts.append(part(f"Nostril_{s}", "sphere", (0.022, 0.014, 0.016), (0.02 * x, -0.264, 1.222), dark_m, "head",
                          segments=12))
    # Fur tufts: one rigid mesh per bone (the jagged outline of the reference)
    for s, x in (("L", 1), ("R", -1)):
        z = SHOULDER_Z
        parts.append(tuft_object(f"Tufts_Shoulder_{s}", f"upper_arm.{s}", fur_m, lambda bm, x=x, z=z: tuft_ring(
            bm, (0.16 * x, 0.01, z + 0.03), (0.30 * x, 0.01, z + 0.03), 0.12, 2, 12, 0.07,
            skip=lambda th, u, v: math.sin(th) * v.z + math.cos(th) * u.z < -0.3)))  # not underneath
        parts.append(tuft_object(f"Tufts_UpperArm_{s}", f"upper_arm.{s}", fur_m, lambda bm, x=x, z=z: tuft_ring(
            bm, (0.30 * x, 0, z), (0.48 * x, 0, z), 0.085, 4, 13, 0.07)))
        parts.append(tuft_object(f"Tufts_Forearm_{s}", f"forearm.{s}", fur_m, lambda bm, x=x, z=z: tuft_ring(
            bm, (0.48 * x, 0, z - 0.005), (0.64 * x, 0, z - 0.005), 0.07, 4, 12, 0.065)))
        front = lambda th, u, v: (math.cos(th) * u.y + math.sin(th) * v.y) < -0.7  # keep legs' front clean
        parts.append(tuft_object(f"Tufts_Thigh_{s}", f"thigh.{s}", fur_m, lambda bm, x=x: tuft_ring(
            bm, (0.15 * x, 0, 0.47), (0.155 * x, 0, 0.29), 0.13, 3, 14, 0.065, skip=front)))
        parts.append(tuft_object(f"Tufts_Calf_{s}", f"shin.{s}", fur_m, lambda bm, x=x: tuft_ring(
            bm, (0.16 * x, 0, 0.29), (0.17 * x, 0, 0.13), 0.13, 3, 14, 0.065, skip=front)))
    for i, (dx, tilt) in enumerate(((0, 0), (0.035, 25), (-0.035, -25))):
        parts.append(part(f"HairTuft_{i}", "cone", (0.05, 0.05, 0.09), (dx, 0.03, 1.455), fur_m, "head",
                          rot=(0, tilt, 0), subsurf=1, segments=12))

    lo = min(v.co.z for o in parts for v in o.data.vertices)  # ground exactly at z = 0
    for o in parts:
        for v in o.data.vertices:
            v.co.z -= lo
    for o in (fur_obj, skin_obj):
        for poly in o.data.polygons:
            poly.use_smooth = True
        o["bone"] = ""  # blended distance weights
    fur_obj.data.materials.append(fur_m)
    skin_obj.data.materials.append(skin_m)
    return parts
