# Parametric CAD Maker

CAD-backed parametric model maker using FastAPI, CadQuery/OpenCascade, React, and Three.js preview.

## Core Rule

The backend owns all production geometry.

- JSON project file = editable source of truth
- CadQuery/OpenCascade = geometry generation and boolean operations
- STEP/STL/GLB = backend export outputs
- Three.js = preview only
- The frontend must never generate production CAD geometry or export from the preview scene
- 3MF is intentionally not exposed until a real 3MF exporter is implemented

## Feature System

Projects are a list of typed features. Primitive features create bodies. Cutouts, holes, screw holes, bosses, and boolean features target existing bodies by ID.

Supported primitive feature types:

- `box`, `rounded_box`
- `cylinder`, `sphere`, `cone`, `torus`
- `wedge`, `capsule`
- `polygon_prism`, `extrude`
- `revolve`
- `sweep`, `loft` where CadQuery can build the requested geometry

Supported target modifiers:

- `cutout`: circular, rectangular, rounded rectangle, slot, USB-A, USB-C, HDMI, DC jack
- `hole`: through or blind holes with optional counterbore/countersink/thread metadata
- `screw_hole`: hole alias for screw-specific metadata
- `boss`: configurable standoff/mounting boss with optional inner hole
- `boolean`: union, cut/subtract, and intersect between feature IDs

Placement supports six named faces (`top`, `bottom`, `front`, `back`, `left`, `right`) and custom planes with `origin`, `normal`, `x_dir`, and `rotation`.

Patterns can be attached to holes, cutouts, and bosses:

- `linear`
- `grid`
- `circular`
- `mirror`

## Minimal JSON

```json
{
  "name": "Box With USB-C",
  "parameters": [
    {"name": "L", "value": 90},
    {"name": "W", "value": 55},
    {"name": "H", "value": 28},
    {"name": "wall", "value": 2}
  ],
  "features": [
    {"type": "enclosure", "id": "shell", "length": "L", "width": "W", "height": "H", "wall": "wall"},
    {
      "type": "cutout",
      "id": "usb_c_port",
      "target": "shell",
      "shape": "usb_c",
      "placement": {"face": "front", "u": 0, "v": 0},
      "depth": "wall + 1",
      "through": false
    }
  ]
}
```

More examples live in `examples/`:

- `simple_box.json`
- `electronics_enclosure.json`
- `enclosure_usb_c.json`
- `enclosure_four_screw_holes.json`
- `enclosure_ventilation_grid.json`
- `multiple_primitive_shapes.json`
- `custom_planes.json`

## API

- `GET /api/health`
- `POST /api/validate`
- `POST /api/preview` returns backend-generated GLB bytes
- `POST /api/export/step`
- `POST /api/export/stl`
- `POST /api/export/glb`

Validation returns structured user-facing errors and warnings instead of raw CadQuery tracebacks.

## Run

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The frontend reads `VITE_API_BASE`; when unset it uses `http://localhost:8000`.
