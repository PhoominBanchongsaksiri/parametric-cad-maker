# TASK_NEXT.md — Next Tasks

## Immediate task

Set up the clean GitHub repository foundation first.

This is a fresh repository. The previous backend prototype was proven in an earlier session, but it has not yet been recreated in this repo.

Do not start the frontend yet.

## Step 1 — Repository foundation

Create:

- README.md
- CLAUDE.md
- PROJECT_STATUS.md
- TASK_NEXT.md
- .gitignore
- backend/
- frontend/
- examples/
- backend/README.md
- frontend/README.md

Do not implement backend CAD code yet.
Do not build frontend yet.

## Step 2 — Backend core recreation

After the repository foundation is committed, recreate the backend from the proven prototype.

Required backend features:

- FastAPI app
- Pydantic project schema
- Parameter/formula resolver
- Validation routing with separate errors and warnings
- CadQuery/OpenCascade model builder
- Enclosure generator
- Primitive generator
- Real cutouts on all supported faces
- bossPattern
- screw through-holes
- counterbore
- countersink
- STEP export
- STL export
- 3MF export
- GLB preview via POST /api/preview
- Probe-based regression tests
- Smoke test

## Step 3 — Frontend shell

Only after backend tests pass, build the minimal frontend shell:

- React + TypeScript + Vite
- Three.js / React Three Fiber viewport
- POST project JSON to backend /api/preview
- Display backend-generated GLB
- Export buttons for STEP, STL, 3MF, JSON
- Placeholder feature tree
- Placeholder property panel

Frontend must never generate production geometry.
Frontend must never export from the Three.js scene.

## Exact prompt for Claude Code — next task

Paste this first:

Follow CLAUDE.md, PROJECT_STATUS.md, and TASK_NEXT.md.

Task:
Set up the repository foundation only.

Create:
- .gitignore
- backend/
- frontend/
- examples/
- backend/README.md
- frontend/README.md

Do not implement backend CAD code yet.
Do not build frontend yet.
Do not start Phase 3 yet.

Report only:
1. changed files
2. blockers
