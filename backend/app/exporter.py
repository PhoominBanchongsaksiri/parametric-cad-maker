"""Export solids to STEP, STL, 3MF, and GLB (preview). All via file paths."""
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


def to_3mf(wp: cq.Workplane) -> bytes:
    # CadQuery 2.7 does not have a 3MF exporter; fall back to AMF
    try:
        return _with_tempfile(".3mf", wp, exporters.ExportTypes.AMF)
    except AttributeError:
        return _with_tempfile(".amf", wp, exporters.ExportTypes.AMF)


def to_glb(wp: cq.Workplane) -> bytes:
    """Export to GLB. Falls back to STL if GLTF exporter is unavailable."""
    try:
        return _with_tempfile(".glb", wp, exporters.ExportTypes.GLTF)
    except AttributeError:
        return to_stl(wp)


def merge_workplanes(wps: list[cq.Workplane]) -> cq.Workplane:
    if not wps:
        raise ValueError("No geometry to export")
    result = wps[0]
    for wp in wps[1:]:
        result = result.union(wp)
    return result
