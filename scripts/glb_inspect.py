"""Pure-Python GLB (binary glTF 2.0) structural checker. No Blender, no dependencies.

Usage: python3 scripts/glb_inspect.py model.glb   -> prints a JSON summary, exits 1 if invalid
"""
import json
import struct
import sys

COMPONENT_SIZE = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
TYPE_COUNT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}


class GLBError(ValueError):
    pass


def parse_glb(data):
    """Validate the container and return (gltf_json, bin_chunk). Raises GLBError."""
    if len(data) < 20:
        raise GLBError("file too small to be a GLB")
    magic, version, length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF":
        raise GLBError("bad magic (not a GLB)")
    if version != 2:
        raise GLBError(f"unsupported glTF version {version}")
    if length != len(data):
        raise GLBError(f"header length {length} != file size {len(data)}")
    off, chunks = 12, []
    while off < length:
        if off + 8 > length:
            raise GLBError("truncated chunk header")
        clen, ctype = struct.unpack_from("<II", data, off)
        if off + 8 + clen > length:
            raise GLBError("chunk runs past end of file")
        chunks.append((ctype, data[off + 8: off + 8 + clen]))
        off += 8 + clen
    if not chunks or chunks[0][0] != 0x4E4F534A:
        raise GLBError("first chunk is not JSON")
    try:
        gltf = json.loads(chunks[0][1].decode("utf-8").rstrip(" \x00"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise GLBError(f"invalid JSON chunk: {e}") from e
    binchunk = next((c for t, c in chunks[1:] if t == 0x004E4942), b"")
    if gltf.get("asset", {}).get("version") != "2.0":
        raise GLBError("asset.version is not 2.0")
    return gltf, binchunk


def _check_accessor(gltf, binlen, idx):
    acc = gltf["accessors"][idx]
    bv = gltf["bufferViews"][acc["bufferView"]]
    elem = COMPONENT_SIZE[acc["componentType"]] * TYPE_COUNT[acc["type"]]
    stride = bv.get("byteStride", elem)
    end = bv.get("byteOffset", 0) + acc.get("byteOffset", 0) + stride * (acc["count"] - 1) + elem
    if acc["count"] > 0 and end > bv.get("byteOffset", 0) + bv["byteLength"]:
        raise GLBError(f"accessor {idx} overruns its bufferView")
    if bv.get("byteOffset", 0) + bv["byteLength"] > binlen:
        raise GLBError(f"bufferView {acc['bufferView']} overruns BIN chunk")
    return acc


def inspect(data):
    gltf, binchunk = parse_glb(data)
    meshes = gltf.get("meshes", [])
    if not meshes:
        raise GLBError("no meshes")
    verts = tris = 0
    prims_without_material = 0
    skinned_prims = 0
    for m in meshes:
        for p in m["primitives"]:
            attrs = p["attributes"]
            if "POSITION" not in attrs:
                raise GLBError(f"mesh '{m.get('name')}' primitive has no POSITION")
            pos = _check_accessor(gltf, len(binchunk), attrs["POSITION"])
            if "min" not in pos or "max" not in pos:
                raise GLBError("POSITION accessor missing min/max")
            verts += pos["count"]
            if p.get("mode", 4) != 4:
                raise GLBError("non-triangle primitive")
            if "indices" in p:
                tris += _check_accessor(gltf, len(binchunk), p["indices"])["count"] // 3
            else:
                tris += pos["count"] // 3
            if "material" not in p:
                prims_without_material += 1
            if "JOINTS_0" in attrs and "WEIGHTS_0" in attrs:
                _check_accessor(gltf, len(binchunk), attrs["JOINTS_0"])
                _check_accessor(gltf, len(binchunk), attrs["WEIGHTS_0"])
                skinned_prims += 1
    if verts == 0 or tris == 0:
        raise GLBError("mesh has no vertices or faces")
    nodes = gltf.get("nodes", [])
    skins = gltf.get("skins", [])
    return {
        "valid": True,
        "bytes": len(data),
        "meshes": len(meshes),
        "mesh_nodes": sorted(n["name"] for n in nodes if "mesh" in n and "name" in n),
        "vertices": verts,
        "triangles": tris,
        "materials": sorted(m.get("name", "?") for m in gltf.get("materials", [])),
        "primitives_without_material": prims_without_material,
        "skins": len(skins),
        "joints": sorted(nodes[j].get("name", "?") for j in skins[0]["joints"]) if skins else [],
        "skinned_primitives": skinned_prims,
        "generator": gltf.get("asset", {}).get("generator"),
    }


if __name__ == "__main__":
    try:
        with open(sys.argv[1], "rb") as f:
            print(json.dumps(inspect(f.read()), indent=2))
    except (GLBError, OSError, KeyError, IndexError) as e:
        print(json.dumps({"valid": False, "error": str(e)}))
        sys.exit(1)
