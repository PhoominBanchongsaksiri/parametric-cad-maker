# Parametric CAD Maker

CAD-backed web parametric model maker using FastAPI, CadQuery, React, and Three.js preview.

## Core Rule

The backend owns geometry. The frontend only previews and edits project JSON.

- JSON project file = editable source of truth
- STEP/STL/3MF/GLB = export outputs
- Three.js must never generate production geometry
- Exports must come from backend CadQuery/OpenCascade geometry
