# android-3d-model-forge skill

A self-contained [Agent Skills](https://agentskills.io)-style skill (`SKILL.md` with `name` / `description`
frontmatter plus `references/`) that teaches an AI coding agent how to generate, validate and publish 3D
models with this repository.

## Install
- **Claude Code / other skill-aware agents:** copy this folder into the agent's skills directory
  (for Claude Code: `.claude/skills/android-3d-model-forge/` in your project or `~/.claude/skills/`).
- **Any other agent:** point it at `SKILL.md` and ask it to follow the instructions.

The skill needs no MCP server, API key or Claude-specific feature: it only describes the scripts and the
GitHub Actions workflow in this repository.

## Contents
- `SKILL.md` — workflow, T-pose policy, rigging, export, validation, troubleshooting, adding generators.
- `references/modeling-guidelines.md` — axes, part building, proportions, topology.
- `references/export-guidelines.md` — GLB/BLEND/preview settings and publishing.
