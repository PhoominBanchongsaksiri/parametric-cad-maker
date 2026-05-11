"""FastAPI application entry point."""
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Literal

from .schema import Project
from .resolver import build_env
from .validator import validate_project
from .builder import build_all
from .exporter import to_step, to_stl, to_glb, merge_workplanes

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


def _env_or_422(project: Project) -> dict[str, float]:
    try:
        return build_env(project.parameters)
    except Exception as exc:
        raise HTTPException(status_code=422, detail={"errors": [f"parameters: {exc}"], "warnings": []}) from exc


def _build_or_422(project: Project, env: dict[str, float]):
    try:
        return build_all(project, env)
    except Exception as exc:
        raise HTTPException(status_code=422, detail={"errors": [str(exc)], "warnings": []}) from exc


@app.post("/api/validate")
def validate(project: Project):
    try:
        env = build_env(project.parameters)
    except Exception as exc:
        return {"valid": False, "errors": [f"parameters: {exc}"], "warnings": []}
    result = validate_project(project, env)
    return {"valid": result.ok, "errors": result.errors, "warnings": result.warnings}


@app.post("/api/preview")
def preview(project: Project):
    """Build all features and return GLB bytes for Three.js display."""
    env = _env_or_422(project)
    result = validate_project(project, env)
    if not result.ok:
        raise HTTPException(status_code=422, detail={"errors": result.errors, "warnings": result.warnings})

    built = _build_or_422(project, env)
    if not built:
        raise HTTPException(status_code=422, detail={"errors": ["Project has no features"], "warnings": []})

    wps = [wp for _, wp in built]
    merged = merge_workplanes(wps)
    try:
        data = to_glb(merged)
        return Response(content=data, media_type="model/gltf-binary")
    except RuntimeError:
        data = to_stl(merged)
        return Response(content=data, media_type="model/stl")


@app.post("/api/export/{fmt}")
def export_model(project: Project, fmt: Literal["step", "stl", "glb"]):
    env = _env_or_422(project)
    result = validate_project(project, env)
    if not result.ok:
        raise HTTPException(status_code=422, detail={"errors": result.errors, "warnings": result.warnings})

    built = _build_or_422(project, env)
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
    if fmt == "glb":
        try:
            data = to_glb(merged)
        except RuntimeError as exc:
            raise HTTPException(status_code=501, detail={"errors": [str(exc)], "warnings": []}) from exc
        return Response(
            content=data,
            media_type="model/gltf-binary",
            headers={"Content-Disposition": f'attachment; filename="{project.name}.glb"'},
        )
    raise HTTPException(status_code=400, detail=f"Unknown format: {fmt}")
