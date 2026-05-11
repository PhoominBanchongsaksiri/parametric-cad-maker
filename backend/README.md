# Backend

Python/FastAPI service. All geometry is generated here using CadQuery/OpenCascade.

## Responsibilities

- Accept typed project JSON through `/api/validate`, `/api/preview`, and `/api/export/{fmt}`
- Resolve safe parameter expressions such as `L / 2 - 10`
- Validate IDs, targets, dimensions, planes, depths, walls, and patterns before building geometry
- Build primitives, booleans, cutouts, holes, screw holes, bosses, and patterns with CadQuery
- Return GLB preview bytes and STEP/STL/GLB exports

## Export Policy

Supported exports are:

- `step`
- `stl`
- `glb`

3MF is not exposed because CadQuery does not provide a real 3MF exporter in this project. The API must not return AMF data with a `.3mf` filename.

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Tests

```bash
cd backend
pytest
```
