# Frontend

React + Vite + Three.js frontend for editing project JSON and previewing backend-generated geometry.

## Responsibilities

- Edit the model through dashboard controls, not a main-screen raw JSON editor
- Generate project JSON internally from base body settings and dynamic Plane Operation Blocks
- Offer controls for plane selection, custom planes, operation type, placement, depth, shape, size, and patterns
- POST project JSON to backend `/api/validate`
- POST project JSON to backend `/api/preview`
- Display only the backend-generated GLB in Three.js
- Export STEP, STL, and GLB through backend endpoints

## Rules

- Never generate production geometry in Three.js.
- Never export from the Three.js scene.
- All real CAD output must come from the backend.
- 3MF is not shown because the backend does not fake unsupported 3MF output.
- Raw project JSON is hidden by default and only appears behind the optional "Show JSON Debug" button.

## Setup

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_BASE` if the backend is not running at `http://localhost:8000`.
