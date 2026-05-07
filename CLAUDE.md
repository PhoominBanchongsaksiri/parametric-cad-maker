# CLAUDE.md — Parametric CAD Maker

## Core rules (non-negotiable)

- **Backend owns all geometry.** CadQuery/OpenCascade generates every solid.
- **Three.js is display only.** Never create, modify, or export production geometry in Three.js.
- **Never export from the Three.js scene.** STEP/STL/3MF/GLB always come from the backend.
- **Project JSON is the editable source of truth.** STEP/STL/OBJ/3MF/GLB are export outputs only.
- **Prefer surgical patches.** Read only the files relevant to the current task. Do not refactor unrelated modules.
- **After any edit:** report only changed files, test results, and blockers. No summaries of unchanged code.

## Coordinate system
