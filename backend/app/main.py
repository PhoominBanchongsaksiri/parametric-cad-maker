"""FastAPI application entry point."""
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Literal

from .schema import Project
from .resolver import build_env
from .validator import validate_project
from .builder import build_all, build_feature
from .exporter import to_step, to_stl, to_3mf, to_glb, merge_workplanes

app = FastAPI(title="Parametric CAD Maker API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/validate")
def validate(project: Project):
    env = build_env(project.parameters)
    result = validate_project(project, env)
    return {"valid": result.ok, "errors": result.errors, "warnings": result.warnings}


@app.post("/api/preview")
def preview(project: Project):
    """Build all features and return GLB bytes for Three.js display."""
    env = build_env(project.parameters)
    result = validate_project(project, env)
    if not result.ok:
        raise HTTPException(status_code=422, detail={"errors": result.errors, "warnings": result.warnings})

    built = build_all(project, env)
    if not built:
        raise HTTPException(status_code=422, detail={"errors": ["Project has no features"], "warnings": []})

    wps = [wp for _, wp in built]
    merged = merge_workplanes(wps)
    data = to_glb(merged)
    is_glb = data[:4] == b'glTF'
    media_type = "model/gltf-binary" if is_glb else "model/stl"
    return Response(content=data, media_type=media_type)


@app.post("/api/export/{fmt}")
def export_model(project: Project, fmt: Literal["step", "stl", "3mf"]):
    env = build_env(project.parameters)
    result = validate_project(project, env)
    if not result.ok:
        raise HTTPException(status_code=422, detail={"errors": result.errors, "warnings": result.warnings})

    built = build_all(project, env)
    if not built:
        raise HTTPException(status_code=422, detail={"errors": ["Project has no features"], "warnings": []})

    wps = [wp for _, wp in built]
    merged = merge_workplanes(wps)

    if fmt == "step":
        data = to_step(merged)
        return Response(
            content=data,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{project.name}.step"'},
        )
    if fmt == "stl":
        data = to_stl(merged)
        return Response(
            content=data,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{project.name}.stl"'},
        )
    if fmt == "3mf":
        data = to_3mf(merged)
        return Response(
            content=data,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{project.name}.3mf"'},
        )
    raise HTTPException(status_code=400, detail=f"Unknown format: {fmt}")
