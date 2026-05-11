"""Validation routing: collect user-facing errors and warnings from a project."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from .resolver import resolve_expr


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def _resolve(value: Any, env: dict[str, float], path: str, result: ValidationResult, default: float | None = None) -> float:
    if value is None:
        if default is not None:
            return default
        result.errors.append(f"{path}: missing required value")
        return 0.0
    try:
        return resolve_expr(value, env)
    except Exception as exc:
        result.errors.append(f"{path}: invalid expression ({exc})")
        return 0.0


def _positive(value: Any, env: dict[str, float], path: str, result: ValidationResult) -> float:
    resolved = _resolve(value, env, path, result)
    if resolved <= 0:
        result.errors.append(f"{path}: must be greater than zero")
    return resolved


def _non_negative(value: Any, env: dict[str, float], path: str, result: ValidationResult) -> float:
    resolved = _resolve(value, env, path, result)
    if resolved < 0:
        result.errors.append(f"{path}: must not be negative")
    return resolved


def _validate_vec3(vec, env: dict[str, float], path: str, result: ValidationResult) -> tuple[float, float, float]:
    return (
        _resolve(vec.x, env, f"{path}.x", result),
        _resolve(vec.y, env, f"{path}.y", result),
        _resolve(vec.z, env, f"{path}.z", result),
    )


def _validate_plane(plane, env: dict[str, float], path: str, result: ValidationResult) -> None:
    normal = _validate_vec3(plane.normal, env, f"{path}.normal", result)
    x_dir = _validate_vec3(plane.x_dir, env, f"{path}.x_dir", result)
    _validate_vec3(plane.origin, env, f"{path}.origin", result)
    _resolve(plane.rotation, env, f"{path}.rotation", result)
    if math.sqrt(sum(v * v for v in normal)) <= 1e-6:
        result.errors.append(f"{path}: normal vector must not be zero")
    if math.sqrt(sum(v * v for v in x_dir)) <= 1e-6:
        result.errors.append(f"{path}: x direction vector must not be zero")
    dot = sum(a * b for a, b in zip(normal, x_dir))
    if abs(dot) >= 0.999:
        result.errors.append(f"{path}: normal and x direction must not be parallel")


def _validate_pattern(pattern, env: dict[str, float], path: str, result: ValidationResult) -> None:
    if pattern is None:
        return
    if pattern.type == "linear":
        if pattern.count is None or pattern.count < 1:
            result.errors.append(f"{path}.count: linear pattern count must be at least 1")
        _positive(pattern.spacing, env, f"{path}.spacing", result)
    elif pattern.type == "grid":
        if pattern.rows is None or pattern.rows < 1:
            result.errors.append(f"{path}.rows: grid rows must be at least 1")
        if pattern.columns is None or pattern.columns < 1:
            result.errors.append(f"{path}.columns: grid columns must be at least 1")
        _positive(pattern.row_spacing or pattern.spacing, env, f"{path}.row_spacing", result)
        _positive(pattern.column_spacing or pattern.spacing, env, f"{path}.column_spacing", result)
    elif pattern.type == "circular":
        if pattern.count is None or pattern.count < 1:
            result.errors.append(f"{path}.count: circular pattern count must be at least 1")
        _non_negative(pattern.radius or 0, env, f"{path}.radius", result)
    elif pattern.type == "mirror" and pattern.axis not in (None, "x", "y", "z"):
        result.errors.append(f"{path}.axis: mirror axis must be x, y, or z")


def _target_exists(target: str, known: set[str], path: str, result: ValidationResult) -> None:
    if target not in known:
        result.errors.append(f"{path}: invalid target body ID {target!r}")


def _face_spans(face: str, dims: tuple[float, float, float]) -> tuple[float, float, float]:
    length, width, height = dims
    if face in ("top", "bottom"):
        return length, width, height
    if face in ("front", "back"):
        return length, height, width
    return width, height, length


def _cut_size(spec, env: dict[str, float], result: ValidationResult, path: str) -> tuple[float, float]:
    shape = spec.shape
    if shape in ("circle", "dc_jack"):
        diameter = _resolve(getattr(spec, "diameter", None), env, f"{path}.diameter", result, 8.0 if shape == "dc_jack" else None)
        return diameter, diameter
    if shape == "slot":
        length = _resolve(getattr(spec, "slot_length", None), env, f"{path}.slot_length", result)
        diameter = _resolve(getattr(spec, "diameter", None), env, f"{path}.diameter", result)
        return length, diameter
    defaults = {
        "usb_a": (14.0, 6.5),
        "usb_c": (9.0, 3.4),
        "hdmi": (14.0, 6.0),
    }
    default_w, default_h = defaults.get(shape, (None, None))
    width = _resolve(getattr(spec, "width", None), env, f"{path}.width", result, default_w)
    height = _resolve(getattr(spec, "height", None), env, f"{path}.height", result, default_h)
    return width, height


def _validate_against_target(
    spec,
    placement,
    target_dims: tuple[float, float, float] | None,
    env: dict[str, float],
    path: str,
    result: ValidationResult,
) -> None:
    if target_dims is None or placement.face is None:
        return
    span_u, span_v, span_n = _face_spans(placement.face, target_dims)
    if getattr(spec, "shape", None):
        size_u, size_v = _cut_size(spec, env, result, path)
    else:
        diameter = _resolve(getattr(spec, "diameter", None), env, f"{path}.diameter", result)
        size_u = size_v = diameter
    if size_u > span_u or size_v > span_v:
        result.errors.append(f"{path}: hole or cutout is larger than target face")
    depth_value = getattr(spec, "depth", None)
    through = getattr(spec, "through", True)
    if depth_value is not None and not through:
        depth = _resolve(depth_value, env, f"{path}.depth", result)
        if depth > span_n:
            result.errors.append(f"{path}: cut depth exceeds target body thickness")


def _body_dims(feat, env: dict[str, float], result: ValidationResult) -> tuple[float, float, float] | None:
    try:
        if feat.type in ("box", "rounded_box", "enclosure"):
            return (
                _resolve(feat.length, env, f"{feat.id}.length", result),
                _resolve(feat.width, env, f"{feat.id}.width", result),
                _resolve(feat.height, env, f"{feat.id}.height", result),
            )
        if feat.type == "cylinder":
            radius = _resolve(feat.radius, env, f"{feat.id}.radius", result, 0) or _resolve(feat.diameter, env, f"{feat.id}.diameter", result, 0) / 2
            height = _resolve(feat.height, env, f"{feat.id}.height", result)
            return radius * 2, radius * 2, height
        if feat.type == "sphere":
            radius = _resolve(feat.radius, env, f"{feat.id}.radius", result, 0) or _resolve(feat.diameter, env, f"{feat.id}.diameter", result, 0) / 2
            return radius * 2, radius * 2, radius * 2
    except Exception:
        return None
    return None


def _validate_cut_shape(spec, env: dict[str, float], path: str, result: ValidationResult) -> None:
    shape = spec.shape
    if shape in ("circle", "dc_jack"):
        _positive(getattr(spec, "diameter", None), env, f"{path}.diameter", result)
    elif shape == "slot":
        _positive(getattr(spec, "slot_length", None), env, f"{path}.slot_length", result)
        _positive(getattr(spec, "diameter", None), env, f"{path}.diameter", result)
    elif shape in ("usb_a", "usb_c", "hdmi"):
        if getattr(spec, "width", None) is not None:
            _positive(spec.width, env, f"{path}.width", result)
        if getattr(spec, "height", None) is not None:
            _positive(spec.height, env, f"{path}.height", result)
        if getattr(spec, "corner_radius", None) is not None:
            _non_negative(spec.corner_radius, env, f"{path}.corner_radius", result)
    else:
        width = _positive(getattr(spec, "width", None), env, f"{path}.width", result)
        height = _positive(getattr(spec, "height", None), env, f"{path}.height", result)
        if getattr(spec, "corner_radius", None) is not None:
            corner = _non_negative(spec.corner_radius, env, f"{path}.corner_radius", result)
            if corner > min(width, height) / 2:
                result.errors.append(f"{path}.corner_radius: must fit within the rectangle")
    if getattr(spec, "depth", None) is not None:
        _positive(spec.depth, env, f"{path}.depth", result)
    if getattr(spec, "rotation", None) is not None:
        _resolve(spec.rotation, env, f"{path}.rotation", result)
    _validate_pattern(getattr(spec, "pattern", None), env, f"{path}.pattern", result)


def _validate_placement(placement, env: dict[str, float], path: str, result: ValidationResult) -> None:
    if placement.face is None and placement.plane is None:
        result.errors.append(f"{path}: placement requires either face or plane")
    if placement.face is not None and placement.plane is not None:
        result.errors.append(f"{path}: use either face or plane, not both")
    _resolve(placement.u, env, f"{path}.u", result)
    _resolve(placement.v, env, f"{path}.v", result)
    if placement.plane is not None:
        _validate_plane(placement.plane, env, f"{path}.plane", result)


def _validate_primitive(feat, env: dict[str, float], result: ValidationResult) -> None:
    fid = feat.id
    if getattr(feat, "operation", "union") not in ("union", "cut", "subtract", "intersect"):
        result.errors.append(f"{fid}.operation: unsupported operation type")
    if feat.type in ("box", "rounded_box", "enclosure"):
        length = _positive(feat.length, env, f"{fid}.length", result)
        width = _positive(feat.width, env, f"{fid}.width", result)
        height = _positive(feat.height, env, f"{fid}.height", result)
        wall = getattr(feat, "wall", getattr(feat, "wall_thickness", None))
        if wall is not None:
            w = _positive(wall, env, f"{fid}.wall_thickness", result)
            if 2 * w >= min(length, width, height):
                result.errors.append(f"{fid}: wall thickness too large for body dimensions")
        for attr in ("fillet_radius", "chamfer_size"):
            if getattr(feat, attr, None) is not None:
                _non_negative(getattr(feat, attr), env, f"{fid}.{attr}", result)
    elif feat.type == "cylinder":
        _positive(feat.height, env, f"{fid}.height", result)
        if feat.radius is None and feat.diameter is None:
            result.errors.append(f"{fid}: cylinder requires radius or diameter")
        if feat.radius is not None:
            _positive(feat.radius, env, f"{fid}.radius", result)
        if feat.diameter is not None:
            _positive(feat.diameter, env, f"{fid}.diameter", result)
        if feat.wall_thickness is not None:
            wall = _positive(feat.wall_thickness, env, f"{fid}.wall_thickness", result)
            radius = _resolve(feat.radius, env, f"{fid}.radius", result, 0) or _resolve(feat.diameter, env, f"{fid}.diameter", result, 0) / 2
            if wall >= radius:
                result.errors.append(f"{fid}: wall thickness too large for cylinder radius")
    elif feat.type == "sphere":
        if feat.radius is None and feat.diameter is None:
            result.errors.append(f"{fid}: sphere requires radius or diameter")
        if feat.radius is not None:
            _positive(feat.radius, env, f"{fid}.radius", result)
        if feat.diameter is not None:
            _positive(feat.diameter, env, f"{fid}.diameter", result)
    elif feat.type == "cone":
        _positive(feat.height, env, f"{fid}.height", result)
        _non_negative(feat.radius1, env, f"{fid}.radius1", result)
        _non_negative(feat.radius2, env, f"{fid}.radius2", result)
        if _resolve(feat.radius1, env, f"{fid}.radius1", result) <= 0 and _resolve(feat.radius2, env, f"{fid}.radius2", result) <= 0:
            result.errors.append(f"{fid}: at least one cone radius must be positive")
    elif feat.type == "torus":
        major = _positive(feat.major_radius, env, f"{fid}.major_radius", result)
        minor = _positive(feat.minor_radius, env, f"{fid}.minor_radius", result)
        if minor >= major:
            result.errors.append(f"{fid}: minor radius must be smaller than major radius")
    elif feat.type == "wedge":
        _positive(feat.length, env, f"{fid}.length", result)
        _positive(feat.width, env, f"{fid}.width", result)
        _positive(feat.height, env, f"{fid}.height", result)
        if feat.top_length is not None:
            _non_negative(feat.top_length, env, f"{fid}.top_length", result)
    elif feat.type == "capsule":
        length = _positive(feat.length, env, f"{fid}.length", result)
        diameter = _positive(feat.diameter, env, f"{fid}.diameter", result)
        if length < diameter:
            result.errors.append(f"{fid}: capsule length must be at least diameter")
    elif feat.type in ("polygon_prism", "extrude"):
        points = feat.points if feat.type == "polygon_prism" else feat.profile
        if len(points) < 3:
            result.errors.append(f"{fid}: profile requires at least 3 points")
        _positive(feat.height, env, f"{fid}.height", result)
    elif feat.type == "revolve":
        if len(feat.profile) < 3:
            result.errors.append(f"{fid}: revolve profile requires at least 3 points")
        _positive(feat.angle, env, f"{fid}.angle", result)
    elif feat.type == "sweep":
        if len(feat.profile) < 3:
            result.errors.append(f"{fid}: sweep profile requires at least 3 points")
        if len(feat.path) < 2:
            result.errors.append(f"{fid}: sweep path requires at least 2 points")
    elif feat.type == "loft":
        if len(feat.sections) < 2:
            result.errors.append(f"{fid}: loft requires at least 2 sections")
        for index, section in enumerate(feat.sections):
            if len(section) < 3:
                result.errors.append(f"{fid}.sections[{index}]: section requires at least 3 points")


def validate_project(project, env: dict[str, float]) -> ValidationResult:
    result = ValidationResult()
    seen: set[str] = set()
    known_bodies: set[str] = set()
    body_dims: dict[str, tuple[float, float, float]] = {}

    for param in project.parameters:
        if not param.name:
            result.errors.append("parameters: parameter names must not be empty")

    for feat in project.features:
        if feat.id in seen:
            result.errors.append(f"{feat.id}: duplicate feature ID")
        seen.add(feat.id)

        if feat.type in ("cutout", "hole", "screw_hole", "boss"):
            _target_exists(feat.target, known_bodies, f"{feat.id}.target", result)
            _validate_placement(feat.placement, env, f"{feat.id}.placement", result)
            if feat.type == "boss":
                od = _positive(feat.outer_diameter, env, f"{feat.id}.outer_diameter", result)
                height = _positive(feat.height, env, f"{feat.id}.height", result)
                if feat.inner_hole_diameter is not None:
                    hd = _positive(feat.inner_hole_diameter, env, f"{feat.id}.inner_hole_diameter", result)
                    if hd >= od:
                        result.errors.append(f"{feat.id}: inner hole diameter must be smaller than boss outer diameter")
                if feat.counterbore_diameter is not None:
                    _positive(feat.counterbore_diameter, env, f"{feat.id}.counterbore_diameter", result)
                if feat.counterbore_depth is not None:
                    cb_depth = _positive(feat.counterbore_depth, env, f"{feat.id}.counterbore_depth", result)
                    if cb_depth >= height:
                        result.errors.append(f"{feat.id}: counterbore depth must be smaller than boss height")
                _validate_pattern(feat.pattern, env, f"{feat.id}.pattern", result)
            elif feat.type == "cutout":
                _validate_cut_shape(feat, env, feat.id, result)
                _validate_against_target(feat, feat.placement, body_dims.get(feat.target), env, feat.id, result)
            else:
                diameter = _positive(feat.diameter, env, f"{feat.id}.diameter", result)
                if feat.depth is not None:
                    _positive(feat.depth, env, f"{feat.id}.depth", result)
                if feat.counterbore_diameter is not None:
                    cbd = _positive(feat.counterbore_diameter, env, f"{feat.id}.counterbore_diameter", result)
                    if cbd <= diameter:
                        result.errors.append(f"{feat.id}: counterbore diameter must be larger than hole diameter")
                if feat.countersink_diameter is not None:
                    csd = _positive(feat.countersink_diameter, env, f"{feat.id}.countersink_diameter", result)
                    if csd <= diameter:
                        result.errors.append(f"{feat.id}: countersink diameter must be larger than hole diameter")
                _validate_pattern(feat.pattern, env, f"{feat.id}.pattern", result)
                _validate_against_target(feat, feat.placement, body_dims.get(feat.target), env, feat.id, result)
            continue

        if feat.type == "boolean":
            _target_exists(feat.target, known_bodies, f"{feat.id}.target", result)
            _target_exists(feat.tool, known_bodies, f"{feat.id}.tool", result)
            if feat.operation not in ("union", "cut", "subtract", "intersect"):
                result.errors.append(f"{feat.id}.operation: unsupported operation type")
            if feat.tool in known_bodies:
                known_bodies.remove(feat.tool)
                body_dims.pop(feat.tool, None)
            continue

        _validate_primitive(feat, env, result)
        target = getattr(feat, "target", None)
        if target:
            _target_exists(target, known_bodies, f"{feat.id}.target", result)
        else:
            known_bodies.add(feat.id)
            dims = _body_dims(feat, env, result)
            if dims is not None:
                body_dims[feat.id] = dims

        if feat.type == "enclosure":
            for index, cut in enumerate(feat.cutouts):
                _validate_cut_shape(cut, env, f"{feat.id}.cutouts[{index}]", result)
                placement = type("Placement", (), {"face": cut.face, "plane": None})()
                _validate_against_target(cut, placement, body_dims.get(feat.id), env, f"{feat.id}.cutouts[{index}]", result)
            for index, boss in enumerate(feat.bosses):
                od = _positive(boss.od, env, f"{feat.id}.bosses[{index}].od", result)
                _positive(boss.height, env, f"{feat.id}.bosses[{index}].height", result)
                if boss.hole_diameter is not None:
                    hd = _positive(boss.hole_diameter, env, f"{feat.id}.bosses[{index}].hole_diameter", result)
                    if hd >= od:
                        result.errors.append(f"{feat.id}.bosses[{index}]: hole diameter must be smaller than boss OD")
                _validate_pattern(boss.pattern, env, f"{feat.id}.bosses[{index}].pattern", result)
            for index, sh in enumerate(feat.screw_holes):
                diameter = _positive(sh.diameter, env, f"{feat.id}.screw_holes[{index}].diameter", result)
                if sh.depth is not None:
                    _positive(sh.depth, env, f"{feat.id}.screw_holes[{index}].depth", result)
                if sh.counterbore_diameter is not None:
                    cbd = _positive(sh.counterbore_diameter, env, f"{feat.id}.screw_holes[{index}].counterbore_diameter", result)
                    if cbd <= diameter:
                        result.errors.append(f"{feat.id}.screw_holes[{index}]: counterbore diameter must be larger than hole diameter")
                _validate_pattern(sh.pattern, env, f"{feat.id}.screw_holes[{index}].pattern", result)

    if not project.features:
        result.warnings.append("Project has no features")

    return result
