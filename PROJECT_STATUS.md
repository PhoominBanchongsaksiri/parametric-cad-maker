# Project Status

Goal:
CAD-backed web parametric model maker using FastAPI, CadQuery, React, and Three.js preview.

Architecture:
- Backend: FastAPI + CadQuery/OpenCascade
- Frontend: React + TypeScript + Three.js/R3F
- Editable source of truth: JSON project file
- Export outputs: STEP, STL, 3MF, GLB, OBJ later

Implemented in previous prototype:
- enclosure
- primitive
- real cutouts on all supported faces
- bossPattern
- screw through-holes
- counterbore
- countersink
- validation routing
- STEP export
- STL export
- 3MF export
- GLB preview via POST /api/preview
- all-face cutout regression matrix
- backend tests passed in previous prototype

Current repo status:
Fresh GitHub repo. Need to recreate clean project structure.

Next task:
Set up repository foundation, then backend core, then frontend shell.
