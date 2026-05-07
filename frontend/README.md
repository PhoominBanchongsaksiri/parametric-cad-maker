# Frontend

React + TypeScript + Vite display shell.

## Rules

- Never generate production geometry in Three.js.
- Never export from the Three.js scene.
- All geometry and exports go through the backend.

## Stack

- React 18 + TypeScript
- Vite 6
- React Three Fiber + Drei (Three.js viewport)
- Zustand (state)

## Setup

```bash
npm install --legacy-peer-deps
npm run dev        # dev server → http://localhost:5173
npm run build      # production build → dist/
```

Set `VITE_API_URL` to override the backend URL (default: same origin via Vite proxy to http://localhost:8000).

## API surface used

| Endpoint               | Usage                        |
|------------------------|------------------------------|
| GET  /api/health       | Backend status polling       |
| POST /api/validate     | Validate + show errors/warns |
| POST /api/preview      | Fetch GLB/STL for viewport   |
| POST /api/export/step  | Download STEP                |
| POST /api/export/stl   | Download STL                 |
| POST /api/export/3mf   | Download 3MF                 |
