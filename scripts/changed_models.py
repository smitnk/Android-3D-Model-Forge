"""Decide which models a push should rebuild, so CI builds only the model you worked on.

A model is rebuilt when one of ITS OWN files changes (its generator script or its reference images).
Shared code (generate_model.py, validate_model.py, export_model.py, hull.py, clay_chibi.py's Meta,
the workflow) does not rebuild everything by itself; add a tag to the commit message instead:
  [build: gorilla, round_buddy]   rebuild the named models
  [build-all]                     rebuild every published model
Usage (CI): python3 scripts/changed_models.py "<commit messages>" < changed_paths.txt  -> JSON list
"""
import json
import re
import sys

# model type -> path prefixes that belong only to that model
OWN = {
    "gorilla": ("scripts/gorilla.py", "assets/reference/gorilla/"),
    "round_buddy": ("scripts/round_buddy.py", "assets/reference/round-buddy/"),
    "snow_buddy": ("scripts/snow_buddy.py",),
    "lizard_warrior": ("scripts/lizard_warrior.py", "assets/reference/lizard-warrior/"),
}
PUBLISHED = ["chibi_humanoid", "gorilla", "round_buddy", "snow_buddy", "lizard_warrior"]  # clay_chibi is an unpublished example


def models_to_build(paths, message):
    if "[build-all]" in message:
        return list(PUBLISHED)
    tagged = re.findall(r"\[build:\s*([a-z_,\s]+)\]", message)
    picked = {m.strip() for t in tagged for m in t.split(",") if m.strip() in PUBLISHED}
    picked |= {m for m, prefixes in OWN.items() if any(p.startswith(prefixes) for p in paths)}
    return [m for m in PUBLISHED if m in picked]


if __name__ == "__main__":
    changed = [line.strip() for line in sys.stdin if line.strip()]
    print(json.dumps(models_to_build(changed, sys.argv[1] if len(sys.argv) > 1 else "")))
