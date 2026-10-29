"""Snow Buddy: a white, round cartoon character reconstructed from the supplied turnaround sheet.

Procedural Blender geometry inspired by the img2threejs detail-first workflow.
The reference sheet's head/body proportions, tiny black eyes, open black smile, red tongue,
short separated legs, rounded feet, and horizontal T-pose arms are represented directly.
No external image texture is required, so the generator is deterministic in CI.
"""
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clay_chibi import Meta


HEIGHT = 1.18
SHOULDER_Z = 0.625


def bones():
    b = [
        ("root", (0, 0, 0), (0, 0, 0.10), None),
        ("pelvis", (0, 0, 0.31), (0, 0, 0.42), "root"),
        ("spine", (0, 0, 0.42), (0, 0, SHOULDER_Z), "pelvis"),
        ("neck", (0, 0, SHOULDER_Z), (0, 0, 0.76), "spine"),
        ("head", (0, 0, 0.76), (0, 0, 1.14), "neck"),
    ]
    for side, sign in (("L", 1), ("R", -1)):
        b += [
            (f"upper_arm.{side}", (0.08 * sign, 0, SHOULDER_Z), (0.27 * sign, 0, SHOULDER_Z), "spine"),
            (f"forearm.{side}", (0.27 * sign, 0, SHOULDER_Z), (0.42 * sign, 0, SHOULDER_Z), f"upper_arm.{side}"),
            (f"hand.{side}", (0.42 * sign, 0, SHOULDER_Z), (0.53 * sign, 0, SHOULDER_Z), f"forearm.{side}"),
            (f"thigh.{side}", (0.075 * sign, 0, 0.34), (0.075 * sign, 0, 0.20), "pelvis"),
            (f"shin.{side}", (0.075 * sign, 0, 0.20), (0.085 * sign, 0, 0.055), f"thigh.{side}"),
            (f"foot.{side}", (0.085 * sign, 0, 0.055), (0.085 * sign, -0.12, 0.025), f"shin.{side}"),
        ]
    return b


def build(a, material):
    white = material("SnowWhite", a.skin or "#F8FAFC", 0.38)
    black = material("FaceBlack", "#101116", 0.28)
    red = material("TongueRed", "#F0443E", 0.34)
    blue = material("CoolRim", "#BBD9F5", 0.5)

    # Unified soft body, including straight horizontal arms and rounded mitten-like hands.
    body = Meta("SnowBuddyBodyMeta", 0.006)
    body.ellipsoid((0, 0.005, 0.535), 0.145, 0.105, 0.145)  # upper torso
    body.ellipsoid((0, 0.008, 0.405), 0.145, 0.108, 0.105)  # lower torso
    body.ellipsoid((0, 0.0, 0.635), 0.105, 0.095, 0.095)   # shoulders
    for sign in (1, -1):
        body.capsule((0.075 * sign, 0, SHOULDER_Z), (0.425 * sign, 0, SHOULDER_Z), 0.038)
        body.ellipsoid((0.475 * sign, -0.002, SHOULDER_Z), 0.065, 0.045, 0.047)
        # legs stay distinct below the crotch; feet point toward the face (-Y)
        body.capsule((0.075 * sign, 0.005, 0.345), (0.082 * sign, 0.0, 0.075), 0.050)
        body.ellipsoid((0.088 * sign, -0.055, 0.047), 0.076, 0.135, 0.047)
    body_obj = body.to_mesh_object("Body", 1.0)
    body_obj.data.materials.append(white)
    body_obj["bone"] = ""

    # Big featureless white head. The face is built as real geometry rather than a flat decal.
    head = Meta("SnowBuddyHeadMeta", 0.0045)
    head.ellipsoid((0, 0.005, 0.925), 0.245, 0.218, 0.245)
    head_obj = head.to_mesh_object("Head", 1.0)
    head_obj.data.materials.append(white)
    head_obj["bone"] = "head"

    parts = [body_obj, head_obj]
    # Eyes are tiny round black dots placed on the forward (-Y) surface.
    for side, x in (("L", 0.105), ("R", -0.105)):
        eye = Meta(f"EyeMeta_{side}", 0.003)
        eye.ellipsoid((x, -0.203, 0.965), 0.018, 0.014, 0.019)
        obj = eye.to_mesh_object(f"Eye_{side}", 1.0)
        obj.data.materials.append(black)
        obj["bone"] = "head"
        parts.append(obj)

    # Open smiling mouth with a black cavity and a bright red tongue in its lower half.
    mouth = Meta("MouthMeta", 0.0035)
    mouth.ellipsoid((0, -0.211, 0.865), 0.091, 0.018, 0.061)
    mouth_obj = mouth.to_mesh_object("Mouth", 1.0)
    mouth_obj.data.materials.append(black)
    mouth_obj["bone"] = "head"
    parts.append(mouth_obj)

    tongue = Meta("TongueMeta", 0.003)
    tongue.ellipsoid((0, -0.231, 0.844), 0.052, 0.009, 0.028)
    tongue_obj = tongue.to_mesh_object("Tongue", 1.0)
    tongue_obj.data.materials.append(red)
    tongue_obj["bone"] = "head"
    parts.append(tongue_obj)

    # A subtle cool-blue rim is kept as small side accents, not a change to the white base colour.
    for side, sign in (("L", 1), ("R", -1)):
        rim = Meta(f"RimMeta_{side}", 0.004)
        rim.ellipsoid((0.224 * sign, -0.03, 0.925), 0.009, 0.014, 0.17)
        obj = rim.to_mesh_object(f"CoolRim_{side}", 1.0)
        obj.data.materials.append(blue)
        obj["bone"] = "head"
        parts.append(obj)

    for obj in parts:
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return parts
