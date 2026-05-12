"""CadQuery geometry builder. Backend owns all production geometry."""
from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

import cadquery as cq

from .resolver import resolve_expr
from .schema import (
    AnyFeature,
    BossFeature,
    BossSpec,
    BooleanFeature,
    CapsulePrimitive,
    ConePrimitive,
    CutoutFeature,
    CutoutSpec,
    CutoutTarget,
    EnclosureFeature,
    ExtrudeFeature,
    HoleFeature,
    LoftFeature,
    PatternSpec,
    PlaneSpec,
    PolygonPrismPrimitive,
    RevolveFeature,
    ScrewHoleFeature,
    ScrewHoleSpec,
    SpherePrimitive,
    SweepFeature,
    TorusPrimitive,
    Vec2,
    Vec3,
    WedgePrimitive,
)


_FACE_NORMAL: dict[str, tuple[float, float, float]] = {
    "top": (0, 0, 1),
    "bottom": (0, 0, -1),
    "front": (0, -1, 0),
    "back": (0, 1, 0),
    "left": (-1, 0, 0),
    "right": (1, 0, 0),
}

_DEFAULT_CUTOUT_DIMS: dict[str, dict[str, float]] = {
    "usb_a": {"width": 14.0, "height": 6.5, "corner_radius": 0.5},
    "usb_c": {"width": 9.0, "height": 3.4, "corner_radius": 1.7},
    "hdmi": {"width": 14.0, "height": 6.0, "corner_radius": 0.6},
    "dc_jack": {"diameter": 8.0},
}


def _num(value: Any, env: dict[str, float], default: float | None = None) -> float:
    if value is None:
        if default is None:
            raise ValueError("Missing numeric value")
        return default
    return resolve_expr(value, env)


def _vec2(value: Vec2 | dict[str, Any] | None, env: dict[str, float]) -> tuple[float, float]:
    if value is None:
        return 0.0, 0.0
    return _num(value.x, env), _num(value.y, env)  # type: ignore[union-attr]


def _vec3(value: Vec3 | dict[str, Any] | None, env: dict[str, float]) -> tuple[float, float, float]:
    if value is None:
        return 0.0, 0.0, 0.0
    return _num(value.x, env), _num(value.y, env), _num(value.z, env)  # type: ignore[union-attr]


def _face_selector(face: str) -> cq.selectors.Selector:
    return cq.selectors.DirectionMinMaxSelector(cq.Vector(*_FACE_NORMAL[face]), directionMax=True)


def _face_workplane(solid: cq.Workplane, face: str) -> cq.Workplane:
    """Workplane for a named face whose origin is pinned to the bounding-box face-center.

    Using the live topology origin is unreliable after prior features modify the face
    (holes, pockets change the face centroid). The bounding-box center is stable for
    any subtractive operation because the outer envelope doesn't shrink.
    """
    bb = solid.val().BoundingBox()
    cx = (bb.xmin + bb.xmax) / 2
    cy = (bb.ymin + bb.ymax) / 2
    cz = (bb.zmin + bb.zmax) / 2
    origin_of: dict[str, cq.Vector] = {
        "top":    cq.Vector(cx, cy, bb.zmax),
        "bottom": cq.Vector(cx, cy, bb.zmin),
        "front":  cq.Vector(cx, bb.ymin, cz),
        "back":   cq.Vector(cx, bb.ymax, cz),
        "left":   cq.Vector(bb.xmin, cy, cz),
        "right":  cq.Vector(bb.xmax, cy, cz),
    }
    raw = solid.faces(_face_selector(face)).workplane()
    # Mutate plane origin only — keeps the parent-chain solid intact for cutBlind/extrude.
    raw.plane = cq.Plane(origin=origin_of[face], xDir=raw.plane.xDir, normal=raw.plane.zDir)
    return raw


def _face_dims(face: str, length: float, width: float, height: float) -> tuple[float, float, float]:
    if face in ("top", "bottom"):
        return length, width, height
    if face in ("front", "back"):
        return length, height, width
    return width, height, length


def _apply_transform(wp: cq.Workplane, feature: Any, env: dict[str, float]) -> cq.Workplane:
    rx, ry, rz = _vec3(getattr(feature, "rotation", None), env)
    px, py, pz = _vec3(getattr(feature, "position", None), env)
    if rx:
        wp = wp.rotate((0, 0, 0), (1, 0, 0), rx)
    if ry:
        wp = wp.rotate((0, 0, 0), (0, 1, 0), ry)
    if rz:
        wp = wp.rotate((0, 0, 0), (0, 0, 1), rz)
    if px or py or pz:
        wp = wp.translate((px, py, pz))
    return wp


def _profile_points(points: Iterable[Vec2], env: dict[str, float]) -> list[tuple[float, float]]:
    return [(_num(point.x, env), _num(point.y, env)) for point in points]


def _solid_from_profile(points: list[tuple[float, float]], height: float) -> cq.Workplane:
    return cq.Workplane("XY").polyline(points).close().extrude(height)


def _build_box(feat: Any, env: dict[str, float]) -> cq.Workplane:
    length = _num(feat.length, env)
    width = _num(feat.width, env)
    height = _num(feat.height, env)
    wp = cq.Workplane("XY").box(length, width, height)
    fillet = _num(getattr(feat, "fillet_radius", None), env, 0.0)
    chamfer = _num(getattr(feat, "chamfer_size", None), env, 0.0)
    if fillet > 0:
        wp = wp.edges().fillet(fillet)
    if chamfer > 0:
        wp = wp.edges().chamfer(chamfer)
    wall = _num(getattr(feat, "wall_thickness", None), env, 0.0)
    if wall > 0:
        inner = cq.Workplane("XY").box(length - 2 * wall, width - 2 * wall, height - 2 * wall)
        wp = wp.cut(inner)
    return _apply_transform(wp, feat, env)


def _build_cylinder(feat: Any, env: dict[str, float]) -> cq.Workplane:
    radius = _num(getattr(feat, "radius", None), env, 0.0)
    if radius <= 0:
        radius = _num(feat.diameter, env) / 2
    height = _num(feat.height, env)
    wp = cq.Workplane("XY").cylinder(height, radius)
    wall = _num(getattr(feat, "wall_thickness", None), env, 0.0)
    if wall > 0:
        wp = wp.cut(cq.Workplane("XY").cylinder(height + 0.2, radius - wall))
    return _apply_transform(wp, feat, env)


def _build_sphere(feat: SpherePrimitive, env: dict[str, float]) -> cq.Workplane:
    radius = _num(feat.radius, env, 0.0)
    if radius <= 0:
        radius = _num(feat.diameter, env) / 2
    return _apply_transform(cq.Workplane("XY").sphere(radius), feat, env)


def _build_cone(feat: ConePrimitive, env: dict[str, float]) -> cq.Workplane:
    height = _num(feat.height, env)
    radius1 = _num(feat.radius1, env)
    radius2 = _num(feat.radius2, env)
    solid = cq.Solid.makeCone(radius1, radius2, height, cq.Vector(0, 0, -height / 2), cq.Vector(0, 0, 1))
    return _apply_transform(cq.Workplane("XY").add(solid), feat, env)


def _build_torus(feat: TorusPrimitive, env: dict[str, float]) -> cq.Workplane:
    major = _num(feat.major_radius, env)
    minor = _num(feat.minor_radius, env)
    solid = cq.Solid.makeTorus(major, minor)
    return _apply_transform(cq.Workplane("XY").add(solid), feat, env)


def _build_wedge(feat: WedgePrimitive, env: dict[str, float]) -> cq.Workplane:
    length = _num(feat.length, env)
    width = _num(feat.width, env)
    height = _num(feat.height, env)
    top_length = _num(feat.top_length, env, 0.0)
    bottom = length / 2
    top = top_length / 2
    points = [(-bottom, -height / 2), (bottom, -height / 2), (top, height / 2), (-top, height / 2)]
    wp = cq.Workplane("XZ").polyline(points).close().extrude(width, both=True)
    return _apply_transform(wp, feat, env)


def _build_capsule(feat: CapsulePrimitive, env: dict[str, float]) -> cq.Workplane:
    length = _num(feat.length, env)
    diameter = _num(feat.diameter, env)
    cyl_len = max(length - diameter, 0.0)
    radius = diameter / 2
    if cyl_len <= 1e-6:
        return _apply_transform(cq.Workplane("XY").sphere(radius), feat, env)
    cyl = cq.Workplane("XY").cylinder(cyl_len, radius).rotate((0, 0, 0), (0, 1, 0), 90)
    left = cq.Workplane("XY").sphere(radius).translate((-cyl_len / 2, 0, 0))
    right = cq.Workplane("XY").sphere(radius).translate((cyl_len / 2, 0, 0))
    return _apply_transform(cyl.union(left).union(right), feat, env)


def _build_sweep(feat: SweepFeature, env: dict[str, float]) -> cq.Workplane:
    profile = _profile_points(feat.profile, env)
    path = [cq.Vector(*_vec3(point, env)) for point in feat.path]
    wire = cq.Workplane("XY").polyline([(p.x, p.y) for p in path]).wire()
    wp = cq.Workplane("YZ").polyline(profile).close().sweep(wire)
    return _apply_transform(wp, feat, env)


def _build_loft(feat: LoftFeature, env: dict[str, float]) -> cq.Workplane:
    wp = cq.Workplane("XY")
    positions = feat.section_positions or []
    for index, section in enumerate(feat.sections):
        z = _num(positions[index].z, env) if index < len(positions) else float(index)
        pts = _profile_points(section, env)
        wp = wp.workplane(offset=z).polyline(pts).close()
    return _apply_transform(wp.loft(combine=True), feat, env)


def _build_primitive(feat: AnyFeature, env: dict[str, float]) -> cq.Workplane:
    if feat.type in ("box", "rounded_box"):
        return _build_box(feat, env)
    if feat.type == "cylinder":
        return _build_cylinder(feat, env)
    if feat.type == "sphere":
        return _build_sphere(feat, env)
    if feat.type == "cone":
        return _build_cone(feat, env)
    if feat.type == "torus":
        return _build_torus(feat, env)
    if feat.type == "wedge":
        return _build_wedge(feat, env)
    if feat.type == "capsule":
        return _build_capsule(feat, env)
    if feat.type in ("polygon_prism", "extrude"):
        height = _num(feat.height, env)  # type: ignore[attr-defined]
        points = _profile_points(feat.points if isinstance(feat, PolygonPrismPrimitive) else feat.profile, env)
        return _apply_transform(_solid_from_profile(points, height), feat, env)
    if feat.type == "revolve":
        points = _profile_points(feat.profile, env)  # type: ignore[attr-defined]
        angle = _num(feat.angle, env)  # type: ignore[attr-defined]
        wp = cq.Workplane("XY").polyline(points).close().revolve(angle, (0, 0, 0), (0, 1, 0))
        return _apply_transform(wp, feat, env)
    if feat.type == "sweep":
        return _build_sweep(feat, env)  # type: ignore[arg-type]
    if feat.type == "loft":
        return _build_loft(feat, env)  # type: ignore[arg-type]
    raise ValueError(f"Unsupported primitive feature type: {feat.type}")


def _expand_pattern(
    base_u: float,
    base_v: float,
    rotation: float,
    pattern: PatternSpec | None,
    env: dict[str, float],
) -> list[tuple[float, float, float]]:
    if pattern is None:
        return [(base_u, base_v, rotation)]
    if pattern.type == "linear":
        count = int(pattern.count or 1)
        spacing = _num(pattern.spacing, env, 0.0)
        dx, dy = _vec2(pattern.direction, env) if pattern.direction else (1.0, 0.0)
        mag = math.hypot(dx, dy) or 1.0
        return [(base_u + dx / mag * spacing * i, base_v + dy / mag * spacing * i, rotation) for i in range(count)]
    if pattern.type == "grid":
        rows = int(pattern.rows or 1)
        cols = int(pattern.columns or 1)
        row_spacing = _num(pattern.row_spacing or pattern.spacing, env, 0.0)
        col_spacing = _num(pattern.column_spacing or pattern.spacing, env, 0.0)
        return [
            (base_u + (c - (cols - 1) / 2) * col_spacing, base_v + (r - (rows - 1) / 2) * row_spacing, rotation)
            for r in range(rows)
            for c in range(cols)
        ]
    if pattern.type == "circular":
        count = int(pattern.count or 1)
        radius = _num(pattern.radius, env, 0.0)
        angle_step = _num(pattern.angle_step, env, 360.0 / count if count else 0.0)
        cu, cv = _vec2(pattern.center, env) if pattern.center else (base_u, base_v)
        start = math.atan2(base_v - cv, base_u - cu) if radius == 0 else 0.0
        return [
            (
                cu + (radius or math.hypot(base_u - cu, base_v - cv)) * math.cos(start + math.radians(angle_step * i)),
                cv + (radius or math.hypot(base_u - cu, base_v - cv)) * math.sin(start + math.radians(angle_step * i)),
                rotation + angle_step * i,
            )
            for i in range(count)
        ]
    if pattern.type == "mirror":
        axis = pattern.axis or "x"
        mirrored = (base_u, -base_v, -rotation) if axis == "x" else (-base_u, base_v, -rotation)
        return [(base_u, base_v, rotation), mirrored]
    return [(base_u, base_v, rotation)]


def _workplane_from_plane(plane: PlaneSpec, env: dict[str, float]) -> cq.Workplane:
    origin = cq.Vector(*_vec3(plane.origin, env))
    normal = cq.Vector(*_vec3(plane.normal, env))
    x_dir = cq.Vector(*_vec3(plane.x_dir, env))
    cq_plane = cq.Plane(origin=origin, xDir=x_dir, normal=normal)
    rotation = _num(plane.rotation, env, 0.0)
    if rotation:
        cq_plane = cq_plane.rotated((0, 0, rotation))
    return cq.Workplane(cq_plane)


def _draw_cut_profile(wp: cq.Workplane, shape: str, spec: Any, env: dict[str, float]) -> cq.Workplane:
    defaults = _DEFAULT_CUTOUT_DIMS.get(shape, {})
    if shape in ("circle", "dc_jack"):
        diameter = _num(getattr(spec, "diameter", None), env, defaults.get("diameter"))
        return wp.circle(diameter / 2)
    if shape == "slot":
        length = _num(getattr(spec, "slot_length", None), env)
        diameter = _num(getattr(spec, "diameter", None), env)
        return wp.slot2D(length, diameter)
    width = _num(getattr(spec, "width", None), env, defaults.get("width"))
    height = _num(getattr(spec, "height", None), env, defaults.get("height"))
    corner = _num(getattr(spec, "corner_radius", None), env, defaults.get("corner_radius", 0.0))
    if shape in ("rounded_rect", "rounded_rectangle", "usb_a", "usb_c", "hdmi") and corner > 0:
        safe_corner = min(corner, width / 2 - 0.001, height / 2 - 0.001)
        if safe_corner > 0:
            w2 = width / 2
            h2 = height / 2
            r = safe_corner
            return (
                wp.moveTo(w2 - r, -h2)
                .lineTo(-w2 + r, -h2)
                .threePointArc((-w2, -h2), (-w2, -h2 + r))
                .lineTo(-w2, h2 - r)
                .threePointArc((-w2, h2), (-w2 + r, h2))
                .lineTo(w2 - r, h2)
                .threePointArc((w2, h2), (w2, h2 - r))
                .lineTo(w2, -h2 + r)
                .threePointArc((w2, -h2), (w2 - r, -h2))
                .close()
            )
    return wp.rect(width, height)


def _apply_cut_on_face(
    solid: cq.Workplane,
    face: str,
    u: float,
    v: float,
    rotation: float,
    depth: float,
    shape: str,
    spec: Any,
    env: dict[str, float],
) -> cq.Workplane:
    wp = _face_workplane(solid, face).center(u, v)
    if rotation:
        wp = wp.transformed(rotate=(0, 0, rotation))
    return _draw_cut_profile(wp, shape, spec, env).cutBlind(-depth)


def _apply_cut_on_plane(
    solid: cq.Workplane,
    plane: PlaneSpec,
    u: float,
    v: float,
    rotation: float,
    depth: float,
    through: bool,
    shape: str,
    spec: Any,
    env: dict[str, float],
) -> cq.Workplane:
    wp = _workplane_from_plane(plane, env).center(u, v)
    if rotation:
        wp = wp.transformed(rotate=(0, 0, rotation))
    cutter = _draw_cut_profile(wp, shape, spec, env).extrude(depth, both=through)
    return solid.cut(cutter)


def _apply_cutout_feature(solid: cq.Workplane, feat: CutoutFeature, env: dict[str, float]) -> cq.Workplane:
    placement = feat.placement
    through = feat.through or feat.depth is None
    depth = _num(feat.depth, env, _through_depth(solid) if through else 1.0)
    base_u = _num(placement.u, env)
    base_v = _num(placement.v, env)
    rotation = _num(feat.rotation, env, 0.0)
    for u, v, rot in _expand_pattern(base_u, base_v, rotation, feat.pattern, env):
        if placement.plane is not None:
            solid = _apply_cut_on_plane(solid, placement.plane, u, v, rot, depth, through, feat.shape, feat, env)
        else:
            face = placement.face or "top"
            solid = _apply_cut_on_face(solid, face, u, v, rot, depth, feat.shape, feat, env)
    return solid


def _apply_legacy_cutout(
    solid: cq.Workplane,
    cut: CutoutSpec,
    env: dict[str, float],
    length: float,
    width: float,
    height: float,
    wall: float,
) -> cq.Workplane:
    _, _, normal_span = _face_dims(cut.face, length, width, height)
    depth = _num(cut.depth, env, wall + 1.0 if cut.depth is None else None)
    rotation = _num(cut.rotation, env, 0.0)
    base_u = _num(cut.x, env)
    base_v = _num(cut.y, env)
    for u, v, rot in _expand_pattern(base_u, base_v, rotation, cut.pattern, env):
        solid = _apply_cut_on_face(solid, cut.face, u, v, rot, min(depth, normal_span + 1.0), cut.shape, cut, env)
    return solid


def _through_depth(solid: cq.Workplane) -> float:
    bb = solid.val().BoundingBox()
    return max(bb.xlen, bb.ylen, bb.zlen) * 2 + 10.0


def _apply_csk_cone(
    solid: cq.Workplane,
    placement,
    u: float,
    v: float,
    hole_diameter: float,
    csk_diameter: float,
    csk_angle: float,
    env: dict[str, float],
) -> cq.Workplane:
    half_angle = math.radians(csk_angle / 2)
    tan_a = math.tan(half_angle)
    if tan_a < 1e-6:
        return solid
    csk_r = csk_diameter / 2
    hole_r = hole_diameter / 2
    cone_depth = max((csk_r - hole_r) / tan_a, 0.01)
    if placement.plane is not None:
        wp = _workplane_from_plane(placement.plane, env).center(u, v)
    else:
        wp = _face_workplane(solid, placement.face or "top").center(u, v)
    plane = wp.plane
    origin = plane.origin
    inward = -plane.zDir
    cone = cq.Solid.makeCone(csk_r, hole_r, cone_depth, origin, inward)
    return solid.cut(cq.Workplane("XY").add(cone))


def _apply_hole_feature(solid: cq.Workplane, feat: HoleFeature | ScrewHoleFeature, env: dict[str, float]) -> cq.Workplane:
    as_cut = CutoutFeature(
        type="cutout",
        id=feat.id,
        target=feat.target,
        shape="circle",
        placement=feat.placement,
        diameter=feat.diameter,
        depth=feat.depth,
        through=feat.through,
        pattern=feat.pattern,
    )
    placement = feat.placement
    base_u = _num(placement.u, env)
    base_v = _num(placement.v, env)
    depth = _num(feat.depth, env, _through_depth(solid) if feat.through or feat.depth is None else 1.0)
    for u, v, _ in _expand_pattern(base_u, base_v, 0.0, feat.pattern, env):
        if feat.counterbore_diameter is not None:
            cb = CutoutFeature(
                type="cutout",
                id=f"{feat.id}_counterbore",
                target=feat.target,
                shape="circle",
                placement=placement.model_copy(update={"u": u, "v": v}),
                diameter=feat.counterbore_diameter,
                depth=feat.counterbore_depth if feat.counterbore_depth is not None else feat.diameter,
                through=False,
            )
            solid = _apply_cutout_feature(solid, cb, env)
        if feat.countersink_diameter is not None:
            csk_angle = _num(feat.countersink_angle, env, 90.0) if feat.countersink_angle is not None else 90.0
            solid = _apply_csk_cone(
                solid,
                placement.model_copy(update={"u": u, "v": v}),
                u, v,
                _num(feat.diameter, env),
                _num(feat.countersink_diameter, env),
                csk_angle,
                env,
            )
    return _apply_cutout_feature(solid, as_cut.model_copy(update={"depth": depth}), env)


def _apply_boss_on_face(
    solid: cq.Workplane,
    face: str,
    u: float,
    v: float,
    od: float,
    height: float,
    env: dict[str, float],
    feat: Any,
) -> cq.Workplane:
    wp = _face_workplane(solid, face).center(u, v)
    boss = wp.circle(od / 2).extrude(height)
    fillet = _num(getattr(feat, "fillet_radius", None), env, 0.0)
    chamfer = _num(getattr(feat, "chamfer_size", None), env, 0.0)
    if fillet > 0:
        boss = boss.edges().fillet(fillet)
    if chamfer > 0:
        boss = boss.edges().chamfer(chamfer)
    return boss


def _apply_boss_feature(solid: cq.Workplane, feat: BossFeature, env: dict[str, float]) -> cq.Workplane:
    placement = feat.placement
    od = _num(feat.outer_diameter, env)
    height = _num(feat.height, env)
    base_u = _num(placement.u, env)
    base_v = _num(placement.v, env)
    for u, v, _ in _expand_pattern(base_u, base_v, 0.0, feat.pattern, env):
        if placement.plane is not None:
            wp = _workplane_from_plane(placement.plane, env).center(u, v)
            boss = wp.circle(od / 2).extrude(height)
            solid = solid.union(boss)
        else:
            solid = _apply_boss_on_face(solid, placement.face or "top", u, v, od, height, env, feat)
        if feat.inner_hole_diameter is not None:
            hole = HoleFeature(
                type="hole",
                id=f"{feat.id}_hole",
                target=feat.target,
                placement=placement.model_copy(update={"u": u, "v": v}),
                diameter=feat.inner_hole_diameter,
                depth=height + 1.0,
                through=False,
            )
            solid = _apply_hole_feature(solid, hole, env)
    return solid


def _apply_legacy_boss(solid: cq.Workplane, boss: BossSpec, env: dict[str, float]) -> cq.Workplane:
    base_u = _num(boss.x, env)
    base_v = _num(boss.y, env)
    for u, v, _ in _expand_pattern(base_u, base_v, 0.0, boss.pattern, env):
        solid = _apply_boss_on_face(solid, boss.face, u, v, _num(boss.od, env), _num(boss.height, env), env, boss)
        if boss.hole_diameter is not None:
            hole = HoleFeature(
                type="hole",
                id="legacy_boss_hole",
                target="",
                placement=CutoutTarget(face=boss.face, u=u, v=v),
                diameter=boss.hole_diameter,
                depth=_num(boss.height, env) + 1.0,
                through=False,
            )
            solid = _apply_hole_feature(solid, hole, env)
    return solid


def _build_enclosure(feat: EnclosureFeature, env: dict[str, float]) -> cq.Workplane:
    length = _num(feat.length, env)
    width = _num(feat.width, env)
    height = _num(feat.height, env)
    wall = _num(feat.wall, env)
    outer = cq.Workplane("XY").box(length, width, height)
    fillet = _num(feat.fillet_radius, env, 0.0)
    chamfer = _num(feat.chamfer_size, env, 0.0)
    if fillet > 0:
        outer = outer.edges().fillet(fillet)
    if chamfer > 0:
        outer = outer.edges().chamfer(chamfer)
    inner = cq.Workplane("XY").box(length - 2 * wall, width - 2 * wall, height - 2 * wall)
    solid = outer.cut(inner)
    for cut in feat.cutouts:
        solid = _apply_legacy_cutout(solid, cut, env, length, width, height, wall)
    for boss in feat.bosses:
        solid = _apply_legacy_boss(solid, boss, env)
    for sh in feat.screw_holes:
        placement = CutoutTarget(face=sh.face, u=sh.x, v=sh.y)
        hole = ScrewHoleFeature(
            type="screw_hole",
            id="legacy_screw_hole",
            target=feat.id,
            placement=placement,
            diameter=sh.diameter,
            depth=sh.depth,
            counterbore_diameter=sh.counterbore_diameter,
            counterbore_depth=sh.counterbore_depth,
            countersink_diameter=sh.countersink_diameter,
            countersink_angle=sh.countersink_angle,
            thread=sh.thread,
            pattern=sh.pattern,
        )
        solid = _apply_hole_feature(solid, hole, env)
    return _apply_transform(solid, feat, env)


def _combine(target: cq.Workplane, tool: cq.Workplane, operation: str) -> cq.Workplane:
    if operation == "union":
        return target.union(tool)
    if operation in ("cut", "subtract"):
        return target.cut(tool)
    if operation == "intersect":
        return target.intersect(tool)
    raise ValueError(f"Unsupported operation: {operation}")


def build_feature(feat: AnyFeature, env: dict[str, float]) -> cq.Workplane:
    if feat.type == "enclosure":
        return _build_enclosure(feat, env)
    return _build_primitive(feat, env)


def build_all(project, env: dict[str, float]) -> list[tuple[str, cq.Workplane]]:
    """Build a project sequentially and return named final bodies."""

    bodies: dict[str, cq.Workplane] = {}
    order: list[str] = []

    for feat in project.features:
        if feat.type in ("cutout", "hole", "screw_hole", "boss"):
            target_id = feat.target
            if target_id not in bodies:
                raise ValueError(f"{feat.id}: target body {target_id!r} does not exist")
            if feat.type == "boss":
                bodies[target_id] = _apply_boss_feature(bodies[target_id], feat, env)
            elif feat.type in ("hole", "screw_hole"):
                bodies[target_id] = _apply_hole_feature(bodies[target_id], feat, env)
            else:
                bodies[target_id] = _apply_cutout_feature(bodies[target_id], feat, env)
            continue

        if feat.type == "boolean":
            bool_feat: BooleanFeature = feat
            if bool_feat.target not in bodies or bool_feat.tool not in bodies:
                missing = bool_feat.target if bool_feat.target not in bodies else bool_feat.tool
                raise ValueError(f"{bool_feat.id}: body {missing!r} does not exist")
            bodies[bool_feat.target] = _combine(bodies[bool_feat.target], bodies[bool_feat.tool], bool_feat.operation)
            bodies.pop(bool_feat.tool, None)
            order = [item for item in order if item != bool_feat.tool]
            continue

        wp = build_feature(feat, env)
        target_id = getattr(feat, "target", None)
        operation = getattr(feat, "operation", "union")
        if target_id:
            if target_id not in bodies:
                raise ValueError(f"{feat.id}: target body {target_id!r} does not exist")
            bodies[target_id] = _combine(bodies[target_id], wp, operation)
        else:
            bodies[feat.id] = wp
            order.append(feat.id)

    return [(feature_id, bodies[feature_id]) for feature_id in order if feature_id in bodies]
