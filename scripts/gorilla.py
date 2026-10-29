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
Measured (H = 1.5 m): shoulder line 0.70 H, hand reach 0.52 H from centre, chest half-width 0.20 H,
waist half-width 0.10 H, hips 0.14 H, leg centres +-0.11 H, feet 0.23 H wide, head top 0.97 H.
"""
import math

from mathutils import Vector

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


def build(a, material, part):
    fur_m = material("Fur", a.hair or "#4B4260", 0.85)
    skin_m = material("Skin", a.skin or "#8A7E9C", 0.6)
    eye_m = material("EyeWhite", "#FFFFFF", 0.3)
    pupil_m = material("Pupil", "#121018", 0.15)
    dark_m = material("Nostril", "#2A2433", 0.6)

    fur = Meta("FurMeta", 0.011)
    fur.ellipsoid((0, 0.03, 1.27), 0.13, 0.13, 0.18)          # dome head (sits low and forward)
    fur.capsule((-0.085, -0.10, 1.355), (0.085, -0.10, 1.355), 0.03)  # brow ridge
    fur.ellipsoid((0, 0.04, 1.10), 0.25, 0.17, 0.09)          # trapezius / shoulder mass
    fur.ellipsoid((0, 0, 0.95), 0.29, 0.19, 0.17)             # barrel chest
    fur.ellipsoid((0, 0, 0.73), 0.19, 0.17, 0.15)             # waist / belly core
    fur.ellipsoid((0, 0.02, 0.55), 0.22, 0.17, 0.13)          # hips
    for x in (1, -1):
        fur.ellipsoid((0.10 * x, 0.11, 0.52), 0.11, 0.09, 0.12)        # glutes
        fur.ellipsoid((0.25 * x, 0, SHOULDER_Z), 0.11, 0.11, 0.10)    # deltoid
        fur.ellipsoid((0.38 * x, 0, SHOULDER_Z), 0.15, 0.09, 0.085)   # thick upper arm
        fur.ellipsoid((0.56 * x, 0, SHOULDER_Z - 0.005), 0.12, 0.075, 0.07)  # forearm
        fur.ellipsoid((0.15 * x, 0, 0.37), 0.13, 0.12, 0.14)          # thigh
        fur.ellipsoid((0.165 * x, 0, 0.20), 0.135, 0.125, 0.12)       # calf (enters the foot)
    fur_obj = fur.to_mesh_object("Fur", 0.3)

    skin = Meta("SkinMeta", 0.0075)
    skin.ellipsoid((0, -0.10, 1.17), 0.145, 0.11, 0.105)      # big muzzle
    skin.ellipsoid((0, -0.085, 1.30), 0.10, 0.06, 0.07)       # eye mask
    skin.ball((0, -0.185, 1.225), 0.035)                      # nose bump
    skin.ball((0.012, -0.2, 1.115), 0.024)                    # pursed lips
    for x in (1, -1):
        skin.ellipsoid((0.135 * x, 0.0, 1.28), 0.03, 0.05, 0.06)     # ears
        skin.ellipsoid((0.10 * x, -0.145, 0.98), 0.11, 0.06, 0.09)   # pec plates
        # hand: palm entering the forearm, four fingers pointing outward, thumb forward
        skin.ellipsoid((0.69 * x, -0.005, SHOULDER_Z), 0.065, 0.055, 0.045)
        for z in (-0.03, -0.01, 0.01, 0.03):
            skin.capsule((0.73 * x, -0.01, SHOULDER_Z + z), (0.775 * x, -0.02, SHOULDER_Z + z * 1.1), 0.017)
        skin.capsule((0.68 * x, -0.05, SHOULDER_Z - 0.01), (0.71 * x, -0.085, SHOULDER_Z - 0.03), 0.02)
        # foot: wide sole with a row of toes at the front (toe toward -Y)
        skin.ellipsoid((0.17 * x, -0.05, 0.055), 0.15, 0.17, 0.06)
        for i, dx in enumerate((-0.09, -0.03, 0.03, 0.09)):
            skin.ball(((0.17 + dx * 1.0) * x, -0.20 + 0.012 * abs(i - 1.5), 0.04), 0.036)
        skin.ball(((0.17 + 0.155) * x, -0.08, 0.045), 0.04)            # big toe on the outer side
    skin.ellipsoid((0, -0.13, 0.74), 0.17, 0.08, 0.15)        # belly plate (blends with the pecs)
    skin_obj = skin.to_mesh_object("Skin", 0.35)

    parts = [fur_obj, skin_obj]
    for s, x in (("L", 1), ("R", -1)):
        parts.append(part(f"Eye_{s}", "sphere", (0.075, 0.035, 0.095), (0.045 * x, -0.142, 1.31), eye_m, "head",
                          segments=24))
        parts.append(part(f"Pupil_{s}", "sphere", (0.02, 0.012, 0.022), (0.04 * x, -0.159, 1.305), pupil_m, "head",
                          segments=12))
        parts.append(part(f"Nostril_{s}", "sphere", (0.022, 0.014, 0.016), (0.02 * x, -0.214, 1.222), dark_m, "head",
                          segments=12))
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
