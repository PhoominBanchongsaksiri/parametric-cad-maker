# Project Rules

This is a CAD-backed parametric model maker.

Rules:
- Backend owns all geometry.
- Frontend is preview/editor only.
- Never generate production geometry in Three.js.
- Never export from the Three.js scene.
- Project JSON is the editable source of truth.
- STEP/STL/3MF/GLB come from backend CadQuery/OpenCascade.
- Prefer surgical patches.
- Read only files relevant to the current task.
- Do not summarize the whole project unless asked.
- After edits, report only changed files, test result, and blockers.
