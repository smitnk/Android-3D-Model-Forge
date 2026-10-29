"""Export and preview helpers used by generate_model.py (runs inside Blender)."""
import math
import os

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


def export_glb(path):
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_selection=False,
        export_yup=True,          # glTF is Y-up; Blender -Y front becomes glTF +Z front
        export_apply=False,       # modifiers are already baked; keep armature skinning live
        export_skins=True,
        export_animations=False,
        export_materials="EXPORT",
    )
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        raise SystemExit(f"GLB export failed: {path}")
    return os.path.basename(path)


def save_blend(path):
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(path), compress=True)
    return os.path.basename(path)


def _look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def _setup_scene():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 800
    scene.render.resolution_y = 800
    scene.render.image_settings.file_format = "PNG"
    try:
        scene.view_settings.view_transform = "Standard"
    except TypeError:
        pass
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.62, 0.70, 0.80, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    scene.world = world

    sun = bpy.data.objects.new("Key", bpy.data.lights.new("Key", "SUN"))
    sun.data.energy = 3.0
    sun.data.angle = math.radians(8)
    sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
    fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", "AREA"))
    fill.data.energy = 120
    fill.data.size = 2.0
    fill.location = (-2.0, -2.0, 1.6)
    _look_at(fill, (0, 0, 0.7))
    floor_me = bpy.data.meshes.new("Floor")
    floor_me.from_pydata([(-6, -6, 0), (6, -6, 0), (6, 6, 0), (-6, 6, 0)], [], [(0, 1, 2, 3)])
    floor = bpy.data.objects.new("Floor", floor_me)
    fm = bpy.data.materials.new("FloorMat")
    fm.use_nodes = True
    fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.75, 0.76, 0.78, 1)
    floor_me.materials.append(fm)
    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    cam.data.lens = 50
    for o in (sun, fill, floor, cam):
        scene.collection.objects.link(o)
    scene.camera = cam
    return scene, cam


def _framing(scene, cam, parts):
    """Return the min/max normalised screen coords of every part's bbox corners (0..1 = in frame)."""
    dg = bpy.context.evaluated_depsgraph_get()
    xs, ys = [], []
    for o in parts:
        ev = o.evaluated_get(dg)
        for corner in ev.bound_box:
            p = world_to_camera_view(scene, cam, ev.matrix_world @ Vector(corner))
            xs.append(p.x)
            ys.append(p.y)
    return min(xs), max(xs), min(ys), max(ys)


def render_previews(parts, out_dir, slug):
    scene, cam = _setup_scene()
    views = {
        "front": ((0, -2.9, 0.68), (0, 0, 0.64)),
        "three-quarter": ((1.9, -2.2, 1.15), (0, 0, 0.62)),
        "back": ((0, 2.9, 0.68), (0, 0, 0.64)),
    }
    results = []
    for view, (loc, target) in views.items():
        cam.location = loc
        _look_at(cam, target)
        bpy.context.view_layer.update()
        x0, x1, y0, y1 = _framing(scene, cam, parts)
        in_frame = x0 > 0.01 and x1 < 0.99 and y0 > 0.01 and y1 < 0.99
        if not in_frame:
            raise SystemExit(f"Preview '{view}' would clip the model: x={x0:.3f}..{x1:.3f} y={y0:.3f}..{y1:.3f}")
        path = os.path.abspath(os.path.join(out_dir, f"{slug}-{view}.png"))
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        if not os.path.isfile(path) or os.path.getsize(path) < 10_000:
            raise SystemExit(f"Preview render failed or is suspiciously small: {path}")
        results.append({"view": view, "file": os.path.basename(path),
                        "frame_extent": [round(v, 3) for v in (x0, x1, y0, y1)]})
    return results
