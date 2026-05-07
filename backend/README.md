# Backend

Python/FastAPI service. All geometry is generated here using CadQuery/OpenCascade.

## Responsibilities

- Accept project JSON via POST `/api/preview` and POST `/api/export`
- Resolve parameters and formulas
- Build solids with CadQuery
- Return GLB for preview; STEP/STL/3MF for export

## Rules

- Backend owns all geometry. No geometry is ever created in the frontend.
- STEP/STL/3MF/GLB always come from here, never from the Three.js scene.

## Setup (to be completed in Phase 2)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
