# TASK_NEXT.md — Next Tasks

## Status

Steps 1–3 are complete:

- [x] Step 1 — Repository foundation
- [x] Step 2 — Backend core (FastAPI, CadQuery builder, exporter, tests)
- [x] Step 3 — Frontend shell (React 19, Vite 7, Three.js viewer, plane operations editor)

---

## Step 4 — Multi-body and JSON import/export

The frontend currently hard-codes a single body (`shell`). Next tasks:

- Allow the user to add more than one base body (second enclosure, second primitive, etc.)
- Wire the `target` field in each operation block to a dropdown of existing body IDs
- **JSON export** — download the current project as a `.json` file
- **JSON import** — load a project JSON file and populate the UI

## Step 5 — 3MF export

Implement a real 3MF exporter in the backend and expose it via `POST /api/export/3mf`.
Add an **Export 3MF** button to the frontend toolbar.

## Step 6 — TypeScript migration (optional)

Migrate `frontend/src/main.jsx` to TypeScript + strict types.
Add `tsconfig.json`, rename file to `main.tsx`.

## Step 7 — Feature tree and property panel

Replace the flat block list with a proper tree view that shows the body hierarchy
(parent body → child operations). Add a dedicated property panel that appears on
the right when a feature is selected.

## Step 8 — Parameter editor

Expose the `parameters` array in the UI so users can define named parameters
(e.g. `L = 90`) and use them as expressions in dimension fields.
