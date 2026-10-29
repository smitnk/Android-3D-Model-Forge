"""Combine generation.json + validation.json into a short Markdown report. Pure Python.

Usage: python3 scripts/make_report.py out/generation.json out/validation.json > out/REPORT.md
"""
import json
import sys


def render(gen, val):
    L = [f"# Model report: {gen['name']}", ""]
    L.append(f"**Validation: {val['overall']}** — "
             f"{sum(c['pass'] for c in val['checks'])}/{len(val['checks'])} checks passed")
    L.append("")
    d = val.get("dimensions_m") or {}
    s = val.get("summary") or {}
    rig = gen.get("rig")
    L += [
        "| Property | Value |", "|---|---|",
        f"| Generator | `{gen['generator']}` v{gen['generator_version']} |",
        f"| Blender | {gen['blender']} |",
        f"| Pose | T-pose (verified) |" if val["overall"] == "PASS" else "| Pose | not verified |",
        f"| Height | {d.get('height', '?')} m |",
        f"| Size (x, y, z) | {d.get('size_xyz', '?')} m |",
        f"| Mesh parts | {gen['parts']} |",
        f"| Vertices / triangles (GLB) | {s.get('vertices', '?')} / {s.get('triangles', '?')} |",
        f"| Materials | {', '.join(s.get('materials', []))} |",
        f"| Rig | {rig['bones']} bones, {rig['skinning']} skinning |" if rig else "| Rig | none |",
        f"| GLB size | {s.get('bytes', 0) / 1024:.0f} KB |",
        "", "## Checks", "",
    ]
    L += [f"- {'✅' if c['pass'] else '❌'} `{c['check']}` {c['detail']}" for c in val["checks"]]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    with open(sys.argv[1]) as f1, open(sys.argv[2]) as f2:
        print(render(json.load(f1), json.load(f2)), end="")
