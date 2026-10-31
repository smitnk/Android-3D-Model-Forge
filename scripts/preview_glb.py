"""Render front / three-quarter / back previews of any GLB (e.g. an AI-generated mesh) with the repo's preview setup.

Usage: blender -b --factory-startup --python-exit-code 1 --python scripts/preview_glb.py -- \
           --glb mesh.glb --out out --slug name [--height 1.8] [--rotate-x 90] [--rotate-z 0] [--save-glb fixed.glb]
TripoSR meshes are Z-up with the camera on +X: use --rotate-x -90 --rotate-z -90.
Vertex colours (COLOR_0) are wired into the material so meshes without textures render in colour.
Prints the mesh's size before normalising, so orientation problems are visible in the log.
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Euler, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import export_model  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--glb", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--height", type=float, default=1.8)
    p.add_argument("--rotate-x", type=float, default=0.0)
    p.add_argument("--rotate-z", type=float, default=0.0)
    p.add_argument("--save-glb", default="", help="also write the re-oriented, scaled mesh here")
    a = p.parse_args(sys.argv[sys.argv.index("--") + 1:])
    os.makedirs(a.out, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(a.glb))
    parts = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    rot = Euler((math.radians(a.rotate_x), 0, math.radians(a.rotate_z))).to_matrix().to_4x4()
    for o in parts:
        o.data.transform(rot @ o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        o.parent = None
    pts = [v.co for o in parts for v in o.data.vertices]
    lo = [min(c[i] for c in pts) for i in range(3)]
    hi = [max(c[i] for c in pts) for i in range(3)]
    raw = [round(hi[i] - lo[i], 4) for i in range(3)]
    k = a.height / (hi[2] - lo[2])
    centre = [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]]
    for o in parts:
        for v in o.data.vertices:
            v.co = ((v.co.x - centre[0]) * k, (v.co.y - centre[1]) * k, (v.co.z - centre[2]) * k)
        me = o.data
        if me.color_attributes:
            mat = bpy.data.materials.new("VertexColour")
            mat.use_nodes = True
            nt = mat.node_tree
            attr = nt.nodes.new("ShaderNodeVertexColor")
            attr.layer_name = me.color_attributes[0].name
            nt.links.new(attr.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
            nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
            me.materials.clear()
            me.materials.append(mat)
        for poly in me.polygons:
            poly.use_smooth = True

    if a.save_glb:  # the upright, metre-scaled copy, for viewers and as a modelling template
        bpy.ops.export_scene.gltf(filepath=os.path.abspath(a.save_glb), export_format="GLB", export_yup=True)
    files = export_model.render_previews(parts, a.out, a.slug)
    info = {"raw_size_xyz": raw, "vertices": len(pts),
            "triangles": sum(len(f.vertices) - 2 for o in parts for f in o.data.polygons),
            "vertex_colours": any(o.data.color_attributes for o in parts), "previews": files}
    with open(os.path.join(a.out, f"{a.slug}-preview.json"), "w") as f:
        json.dump(info, f, indent=2)
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
