# Parametric CAD Maker

Browser-based parametric CAD system built with FastAPI, CadQuery/OpenCascade, React, and Three.js.

## Core Rule

The backend owns all production geometry.

- JSON project file = editable source of truth
- CadQuery/OpenCascade = geometry generation and all boolean operations
- STEP/STL/GLB = backend export outputs only
- Three.js = display/preview only — never generates or exports production geometry
- 3MF is intentionally not exposed until a real 3MF exporter is implemented

## Feature System

Projects are a list of typed features. Primitive features create bodies. Cutouts, holes, screw holes, bosses, and boolean features target existing bodies by ID.

Supported primitive feature types:

- `box`, `rounded_box`
- `cylinder`, `sphere`, `cone`, `torus`
- `wedge`, `capsule`
- `polygon_prism`, `extrude`
- `revolve`
- `sweep`, `loft`

Supported enclosure/solid body type:

- `enclosure`: hollow shell with configurable wall thickness, optional fillet/chamfer

Supported target modifiers:

- `cutout`: circle, rect, rounded_rect, slot, USB-A, USB-C, HDMI, DC jack
- `hole`: through or blind holes with optional counterbore/countersink/thread metadata
- `screw_hole`: hole alias for screw-specific metadata (ISO M1–M10 specs built in)
- `boss`: configurable standoff/mounting boss with optional inner hole
- `boolean`: union, cut/subtract, intersect between feature IDs

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
      "depth": 4,
      "through": false
    }
  ]
}
```

More examples in `examples/`:

- `simple_box.json`
- `enclosure_basic.json`
- `electronics_enclosure.json`
- `enclosure_usb_c.json`
- `enclosure_four_screw_holes.json`
- `enclosure_ventilation_grid.json`
- `multiple_primitive_shapes.json`
- `custom_planes.json`

## API

- `GET  /api/health`
- `POST /api/validate` — returns structured errors and warnings
- `POST /api/preview` — returns backend-generated GLB bytes
- `POST /api/export/step`
- `POST /api/export/stl`
- `POST /api/export/glb`

## Frontend UI

The UI is a single-page React 19 app (plain JSX, no TypeScript) built with Vite 7 and Three.js 0.180.

- **Toolbar** — Validate, Preview/Update, Export STEP, Export STL
- **Base Body panel** — set dimensions, wall thickness, fillet; toggle solid vs hollow enclosure
- **Plane Operation blocks** — add/remove/reorder operations per face or custom plane
  - Operations: cut, screw hole (ISO M-series wizard), connector cutout, boss/standoff, add solid
  - Patterns: single, linear, grid, circular
  - Depth modes: through-all, blind, up-to-next, custom
- **Timeline bar** — Fusion 360-style strip for quick operation navigation
- **JSON debug** — toggle to inspect the project JSON sent to the backend

Preview renders backend-generated GLB. The Three.js scene is display-only.

## Run

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

The frontend reads `VITE_API_BASE`; when unset it defaults to `http://localhost:8000`.

## Tests

```bash
cd backend
source .venv/bin/activate
pytest tests/
```

Tests cover: API smoke (`test_api.py`), geometry builder (`test_builder.py`), formula resolver (`test_resolver.py`), and validator (`test_validator.py`).
