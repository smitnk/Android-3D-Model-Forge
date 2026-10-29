"""Unit tests for the pure-Python GLB checker and report builder. Run: python3 -m unittest discover tests"""
import json
import os
import struct
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import glb_inspect  # noqa: E402
import make_report  # noqa: E402


def make_glb(with_material=True, corrupt_len=False):
    pos = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0)
    idx = struct.pack("<3H", 0, 1, 2) + b"\x00\x00"
    binc = pos + idx
    prim = {"attributes": {"POSITION": 0}, "indices": 1}
    if with_material:
        prim["material"] = 0
    gltf = {
        "asset": {"version": "2.0"},
        "buffers": [{"byteLength": len(binc)}],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 36},
                        {"buffer": 0, "byteOffset": 36, "byteLength": 6}],
        "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
                       "min": [0, 0, 0], "max": [1, 1, 0]},
                      {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"}],
        "meshes": [{"name": "Tri", "primitives": [prim]}],
        "nodes": [{"name": "Tri", "mesh": 0}],
        "materials": [{"name": "Mat"}],
    }
    js = json.dumps(gltf).encode()
    js += b" " * (-len(js) % 4)
    body = struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(binc), 0x004E4942) + binc
    total = 12 + len(body) + (4 if corrupt_len else 0)
    return struct.pack("<4sII", b"glTF", 2, total) + body


class TestGLBInspect(unittest.TestCase):
    def test_valid_triangle(self):
        s = glb_inspect.inspect(make_glb())
        self.assertEqual((s["vertices"], s["triangles"], s["mesh_nodes"]), (3, 1, ["Tri"]))
        self.assertEqual(s["primitives_without_material"], 0)

    def test_missing_material_counted(self):
        self.assertEqual(glb_inspect.inspect(make_glb(with_material=False))["primitives_without_material"], 1)

    def test_rejects_bad_magic(self):
        with self.assertRaises(glb_inspect.GLBError):
            glb_inspect.inspect(b"NOPE" + make_glb()[4:])

    def test_rejects_length_mismatch(self):
        with self.assertRaises(glb_inspect.GLBError):
            glb_inspect.inspect(make_glb(corrupt_len=True))

    def test_report_renders(self):
        gen = {"name": "T", "generator": "g", "generator_version": "1", "blender": "4.2", "parts": 1, "rig": None}
        val = {"overall": "PASS", "checks": [{"check": "x", "pass": True, "detail": ""}],
               "summary": glb_inspect.inspect(make_glb()), "dimensions_m": {"height": 1.0, "size_xyz": [1, 1, 1]}}
        md = make_report.render(gen, val)
        self.assertIn("Validation: PASS", md)
        self.assertIn("✅ `x`", md)


if __name__ == "__main__":
    unittest.main()
