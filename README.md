# Parametric CAD Maker

Browser-based parametric CAD system. CadQuery/OpenCascade generates all geometry on the backend. The React frontend is a preview and editor only — it never generates or exports production geometry.

## Core rules

- **Backend owns all geometry.** CadQuery/OpenCascade generates every solid.
- **Three.js is display only.** Never create, modify, or export production geometry in Three.js.
- **Never export from the Three.js scene.** STEP/STL/3MF/GLB always come from the backend.
- **Project JSON is the editable source of truth.**

---

## How to run the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API is available at http://localhost:8000

- `GET  /api/health`           — health check
- `POST /api/validate`         — validate project JSON, returns errors + warnings
- `POST /api/preview`          — returns GLB/STL binary for 3D display
- `POST /api/export/step`      — returns STEP file
- `POST /api/export/stl`       — returns STL file
- `POST /api/export/3mf`       — returns 3MF file

---

## How to run the frontend

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

Open http://localhost:5173

To point at a non-default backend URL, set `VITE_API_URL` before starting:

```bash
VITE_API_URL=http://localhost:8000 npm run dev
```

---

## What works

- **3D viewport** — loads GLB/STL from backend, orbit controls, grid, axis gizmo
- **Auto-preview** — loads example enclosure on first page load
- **Feature tree** — lists parameters and features; expand enclosure to see cutouts, bosses, screw holes
- **Parameter editor** — edit any named parameter (L, W, H, wall, …); auto-syncs to JSON editor
- **JSON editor** — full project JSON editable in textarea; Apply JSON button updates state
- **Regenerate Preview** — POSTs current project JSON to `/api/preview`, displays result
- **Validate** — POSTs to `/api/validate`, shows errors and warnings inline
- **Export STEP, STL, 3MF** — downloads backend-generated files
- **Export JSON** — downloads current project JSON directly from frontend state
- **Reset Example** — restores the built-in example enclosure
- **Backend status** — live polling dot in toolbar

## What is still pending

- Fillet / chamfer support (backend and UI)
- Lid/split-body enclosure
- Per-feature enable/disable toggle in tree
- Undo/redo
- Multiple simultaneous features in viewport (currently merges all)
- OBJ export
- Authentication / multi-user

---

## Architecture

```
frontend/    React + TypeScript + Vite
             Three.js / React Three Fiber — display only
             Zustand state
             POSTs project JSON to backend for geometry
             Downloads exports from backend endpoints

backend/     Python FastAPI
             CadQuery / OpenCascade — all geometry
             Pydantic project schema
             Exports: STEP, STL, 3MF, GLB (STL fallback)

examples/    Reference project JSON files
```
