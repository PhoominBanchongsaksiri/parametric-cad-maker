# Frontend

React + TypeScript + Vite display shell. To be built in Phase 3, after backend tests pass.

## Responsibilities

- POST project JSON to backend `/api/preview`
- Receive and display backend-generated GLB via Three.js / React Three Fiber
- Provide export buttons (STEP, STL, 3MF, JSON) that call the backend
- Feature tree and property panel (UI only)

## Rules

- Never generate production geometry in Three.js.
- Never export from the Three.js scene.
- All exports go through the backend.

## Setup (to be completed in Phase 3)

```bash
cd frontend
npm install
npm run dev
```
