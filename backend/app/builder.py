"""CadQuery geometry builder. Backend owns all geometry."""
from __future__ import annotations
import cadquery as cq
from .resolver import resolve_expr
from .planes import get_plane_info
from .schema import (
    AnyFeature, EnclosureFeature, BoxPrimitive, CylinderPrimitive, SpherePrimitive,
    CutoutSpec, BossSpec, BossPatternSpec, ScrewHoleSpec,
)


# ---------------------------------------------------------------------------
# Cutout workers — world-space plane-based (no face selector)
# ---------------------------------------------------------------------------

def _apply_cutout(
    solid: cq.Workplane,
    cut: CutoutSpec,
    env: dict[str, float],
    L: float, W: float, H: float, wall: float,
) -> cq.Workplane:
    target = cut.target
    u = resolve_expr(target.u, env)
    v = resolve_expr(target.v, env)
    depth_val = resolve_expr(cut.depth, env) if cut.depth is not None else None
    depth = depth_val if depth_val is not None else wall + 1.0

    pi = get_plane_info(target.plane, u, v, L, W, H)
    wp = cq.Workplane(pi.cq_plane())

    if cut.shape == "rect":
        w = resolve_expr(cut.width, env)
        h = resolve_expr(cut.height, env)
        solid = solid.cut(wp.rect(w, h).extrude(depth))
    elif cut.shape == "circle":
        d = resolve_expr(cut.diameter, env)
        solid = solid.cut(wp.circle(d / 2).extrude(depth))
    elif cut.shape == "slot":
        slot_len = resolve_expr(cut.slot_length, env)
        d = resolve_expr(cut.diameter, env)
        solid = solid.cut(wp.slot2D(slot_len + d, d).extrude(depth))

    return solid


# ---------------------------------------------------------------------------
# Boss worker
# ---------------------------------------------------------------------------

def _apply_boss(
    solid: cq.Workplane,
    boss: BossSpec,
    env: dict[str, float],
    L: float, W: float, H: float,
    wall: float = 0.0,
) -> cq.Workplane:
    face = boss.face
    bx = resolve_expr(boss.x, env)
    by = resolve_expr(boss.y, env)
    od = resolve_expr(boss.od, env)
    bh = resolve_expr(boss.height, env)

    entry, axis = _FACE_ENTRY[face](bx, by, L, W, H)

    # Boss cylinder: enters from outer face and extends wall + boss_height inward.
    # The portion inside the wall (0..wall) merges with existing solid material;
    # the remainder (wall..wall+bh) is the boss protrusion inside the cavity.
    solid = solid.union(_cyl_cutter(entry, axis, od / 2, wall + bh))

    if boss.hole_diameter is not None:
        hd = resolve_expr(boss.hole_diameter, env)
        solid = solid.cut(_cyl_cutter(entry, axis, hd / 2, wall + bh))

    return solid


# ---------------------------------------------------------------------------
# World-space cylinder cutter (used by boss worker)
# ---------------------------------------------------------------------------

# Mapping used by boss placement only; cutouts/screw holes now use planes.py.
_FACE_ENTRY: dict[str, object] = {
    "top":    lambda sx, sy, L, W, H: ((sx,    sy,    H/2),  (0,  0, -1)),
    "bottom": lambda sx, sy, L, W, H: ((sx,   -sy,   -H/2),  (0,  0,  1)),
    "front":  lambda sx, sy, L, W, H: ((sx,   -W/2,   sy),   (0,  1,  0)),
    "back":   lambda sx, sy, L, W, H: ((-sx,   W/2,   sy),   (0, -1,  0)),
    "left":   lambda sx, sy, L, W, H: ((-L/2, -sx,    sy),   (1,  0,  0)),
    "right":  lambda sx, sy, L, W, H: (( L/2,  sx,    sy),   (-1, 0,  0)),
}


def _cyl_cutter(
    entry: tuple[float, float, float],
    axis: tuple[float, float, float],
    radius: float,
    depth: float,
) -> cq.Workplane:
    """Cylinder of given radius/depth starting at entry point, going along axis."""
    wx, wy, wz = entry
    ax, ay, az = axis
    cx = wx + ax * depth / 2
    cy = wy + ay * depth / 2
    cz = wz + az * depth / 2
    if az:
        return cq.Workplane("XY").cylinder(depth, radius).translate((cx, cy, cz))
    if ay:
        return cq.Workplane("XZ").cylinder(depth, radius).translate((cx, cy, cz))
    return cq.Workplane("YZ").cylinder(depth, radius).translate((cx, cy, cz))


# ---------------------------------------------------------------------------
# Screw hole worker  (world-space via planes.py — no face selector)
# ---------------------------------------------------------------------------

def _apply_screw_hole(
    solid: cq.Workplane,
    sh: ScrewHoleSpec,
    env: dict[str, float],
    L: float, W: float, H: float, wall: float,
) -> cq.Workplane:
    import math as _math

    target = sh.target
    sx = resolve_expr(target.u, env)
    sy = resolve_expr(target.v, env)
    sd = resolve_expr(sh.diameter, env)
    depth = resolve_expr(sh.depth, env) if sh.depth is not None else wall + 1.0

    pi = get_plane_info(target.plane, sx, sy, L, W, H)
    entry = pi.entry
    axis = pi.cutter_dir

    if sh.countersink_diameter is not None:
        csd = resolve_expr(sh.countersink_diameter, env)
        angle = resolve_expr(sh.countersink_angle, env)
        cs_depth = (csd - sd) / 2 / (
            1 if angle == 90 else _math.tan(_math.radians(angle / 2))
        )
        cs_depth = min(cs_depth, wall - 0.01)
        solid = solid.cut(_cyl_cutter(entry, axis, csd / 2, cs_depth))

    if sh.counterbore_diameter is not None:
        cbd = resolve_expr(sh.counterbore_diameter, env)
        cbd_depth = (
            resolve_expr(sh.counterbore_depth, env)
            if sh.counterbore_depth is not None
            else sd
        )
        solid = solid.cut(_cyl_cutter(entry, axis, cbd / 2, cbd_depth))

    solid = solid.cut(_cyl_cutter(entry, axis, sd / 2, depth))
    return solid


# ---------------------------------------------------------------------------
# Boss pattern worker
# ---------------------------------------------------------------------------

def _apply_boss_pattern(
    solid: cq.Workplane,
    bp: BossPatternSpec,
    env: dict[str, float],
    L: float, W: float, H: float,
    wall: float = 0.0,
) -> cq.Workplane:
    x0 = resolve_expr(bp.x0, env)
    y0 = resolve_expr(bp.y0, env)
    dx = resolve_expr(bp.dx, env)
    dy = resolve_expr(bp.dy, env)
    for i in range(bp.nx):
        for j in range(bp.ny):
            boss = BossSpec(
                x=x0 + i * dx,
                y=y0 + j * dy,
                face=bp.face,
                od=bp.od,
                height=bp.height,
                hole_diameter=bp.hole_diameter,
            )
            solid = _apply_boss(solid, boss, env, L, W, H, wall)
    return solid


# ---------------------------------------------------------------------------
# Enclosure builder
# ---------------------------------------------------------------------------

def _build_enclosure(feat: EnclosureFeature, env: dict[str, float]) -> cq.Workplane:
    L = resolve_expr(feat.length, env)
    W = resolve_expr(feat.width, env)
    H = resolve_expr(feat.height, env)
    wall = resolve_expr(feat.wall, env)

    # Shell: outer box minus inner cavity
    outer = cq.Workplane("XY").box(L, W, H)
    inner = cq.Workplane("XY").box(L - wall * 2, W - wall * 2, H - wall * 2)
    solid = outer.cut(inner)

    for cut in feat.cutouts:
        solid = _apply_cutout(solid, cut, env, L, W, H, wall)

    for boss in feat.bosses:
        solid = _apply_boss(solid, boss, env, L, W, H, wall)

    for bp in feat.boss_patterns:
        solid = _apply_boss_pattern(solid, bp, env, L, W, H, wall)

    for sh in feat.screw_holes:
        solid = _apply_screw_hole(solid, sh, env, L, W, H, wall)

    return solid


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def build_feature(feat: AnyFeature, env: dict[str, float]) -> cq.Workplane:
    if feat.type == "enclosure":
        return _build_enclosure(feat, env)
    if feat.type == "box":
        L = resolve_expr(feat.length, env)
        W = resolve_expr(feat.width, env)
        H = resolve_expr(feat.height, env)
        return cq.Workplane("XY").box(L, W, H)
    if feat.type == "cylinder":
        D = resolve_expr(feat.diameter, env)
        H = resolve_expr(feat.height, env)
        return cq.Workplane("XY").cylinder(H, D / 2)
    if feat.type == "sphere":
        D = resolve_expr(feat.diameter, env)
        return cq.Workplane("XY").sphere(D / 2)
    raise ValueError(f"Unknown feature type: {feat.type}")


def build_all(project, env: dict[str, float]) -> list[tuple[str, cq.Workplane]]:
    """Build all features; return list of (id, workplane) pairs."""
    results = []
    for feat in project.features:
        wp = build_feature(feat, env)
        results.append((feat.id, wp))
    return results
