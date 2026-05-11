"""Export solids to STEP, STL, and GLB (preview). All via file paths."""
from __future__ import annotations
import os
import tempfile
import cadquery as cq
from cadquery import exporters


def _with_tempfile(suffix: str, wp: cq.Workplane, export_type) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        path = f.name
    try:
        exporters.export(wp, path, exportType=export_type)
        with open(path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(path):
            os.unlink(path)


def to_step(wp: cq.Workplane) -> bytes:
    return _with_tempfile(".step", wp, exporters.ExportTypes.STEP)


def to_stl(wp: cq.Workplane) -> bytes:
    return _with_tempfile(".stl", wp, exporters.ExportTypes.STL)


def to_glb(wp: cq.Workplane) -> bytes:
    """Export to GLB/GLTF bytes when supported by CadQuery."""
    try:
        return _with_tempfile(".glb", wp, exporters.ExportTypes.GLTF)
    except AttributeError:
        raise RuntimeError("GLB/GLTF export is not supported by this CadQuery installation")


def merge_workplanes(wps: list[cq.Workplane]) -> cq.Workplane:
    if not wps:
        raise ValueError("No geometry to export")
    result = wps[0]
    for wp in wps[1:]:
        result = result.union(wp)
    return result
