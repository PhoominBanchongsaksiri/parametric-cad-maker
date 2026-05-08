"""CadQuery geometry builder. Backend owns all geometry."""
from __future__ import annotations
import cadquery as cq
from .resolver import resolve_expr
from .schema import (
    AnyFeature, EnclosureFeature, BoxPrimitive, CylinderPrimitive, SpherePrimitive,
    CutoutSpec, BossSpec, ScrewHoleSpec,
)


# ---------------------------------------------------------------------------
# Face selection helpers
# ---------------------------------------------------------------------------

_FACE_DIR: dict[str, cq.Vector] = {
    "top":    cq.Vector(0,  0,  1),
    "bottom": cq.Vector(0,  0, -1),
    "front":  cq.Vector(0, -1,  0),
    "back":   cq.Vector(0,  1,  0),
    "left":   cq.Vector(-1, 0,  0),
    "right":  cq.Vector(1,  0,  0),
}


def _pick_face(solid: cq.Workplane, face: str) -> cq.Workplane:
    """Return a workplane containing the single outermost planar face in *face* direction.

    After boolean operations (cuts, extrudes) CadQuery can select multiple faces
    including curved end-cap faces.  Filtering to only PLANE geometry and taking
    the single maximum avoids the "multiple objects selected" workplane error.
    """
    direction = _FACE_DIR[face]
    planar = [f for f in solid.faces().vals() if f.geomType() == "PLANE"]
    best = max(planar, key=lambda f: f.Center().dot(direction))
    return solid.newObject([best])


# ---------------------------------------------------------------------------
# Cutout workers
# ---------------------------------------------------------------------------

def _face_dims(face: str, L: float, W: float, H: float, wall: float) -> tuple[float, float, float]:
    """Return (plane_u, plane_v, cut_depth) for a face given enclosure dims."""
    if face in ("top", "bottom"):
        return L, W, wall
    if face in ("front", "back"):
        return L, H, wall
    # left, right
    return W, H, wall


def _apply_cutout(
    solid: cq.Workplane,
    cut: CutoutSpec,
    env: dict[str, float],
    L: float, W: float, H: float, wall: float,
) -> cq.Workplane:
    face = cut.face
    cx = resolve_expr(cut.x, env)
    cy = resolve_expr(cut.y, env)
    depth_val = resolve_expr(cut.depth, env) if cut.depth is not None else None

    wp = _pick_face(solid, face).workplane()

    _, _, face_wall = _face_dims(face, L, W, H, wall)
    depth = depth_val if depth_val is not None else face_wall + 1.0

    if cut.shape == "rect":
        w = resolve_expr(cut.width, env)
        h = resolve_expr(cut.height, env)
        solid = wp.center(cx, cy).rect(w, h).cutBlind(-depth)
    elif cut.shape == "circle":
        d = resolve_expr(cut.diameter, env)
        solid = wp.center(cx, cy).circle(d / 2).cutBlind(-depth)
    elif cut.shape == "slot":
        slot_len = resolve_expr(cut.slot_length, env)
        d = resolve_expr(cut.diameter, env)
        solid = (
            wp.center(cx, cy)
            .slot2D(slot_len + d, d)
            .cutBlind(-depth)
        )

    return solid


# ---------------------------------------------------------------------------
# Boss worker
# ---------------------------------------------------------------------------

def _apply_boss(
    solid: cq.Workplane,
    boss: BossSpec,
    env: dict[str, float],
    L: float, W: float, H: float,
) -> cq.Workplane:
    face = boss.face
    bx = resolve_expr(boss.x, env)
    by = resolve_expr(boss.y, env)
    od = resolve_expr(boss.od, env)
    bh = resolve_expr(boss.height, env)

    wp = _pick_face(solid, face).workplane().center(bx, by)
    solid = wp.circle(od / 2).extrude(bh)

    if boss.hole_diameter is not None:
        hd = resolve_expr(boss.hole_diameter, env)
        solid = (
            _pick_face(solid, face)
            .workplane()
            .center(bx, by)
            .circle(hd / 2)
            .cutBlind(-bh)
        )

    return solid


# ---------------------------------------------------------------------------
# Screw hole worker
# ---------------------------------------------------------------------------

def _apply_screw_hole(
    solid: cq.Workplane,
    sh: ScrewHoleSpec,
    env: dict[str, float],
    L: float, W: float, H: float, wall: float,
) -> cq.Workplane:
    face = sh.face
    sx = resolve_expr(sh.x, env)
    sy = resolve_expr(sh.y, env)
    sd = resolve_expr(sh.diameter, env)

    _, _, face_wall = _face_dims(face, L, W, H, wall)
    depth = resolve_expr(sh.depth, env) if sh.depth is not None else face_wall + 1.0

    # Countersink (before the through hole so geometry is clean)
    if sh.countersink_diameter is not None:
        csd = resolve_expr(sh.countersink_diameter, env)
        angle = resolve_expr(sh.countersink_angle, env)
        cs_depth = (csd - sd) / 2 / (1 if angle == 90 else __import__("math").tan(__import__("math").radians(angle / 2)))
        solid = (
            _pick_face(solid, face).workplane().center(sx, sy)
            .circle(csd / 2).cutBlind(-cs_depth)
        )

    # Counterbore
    if sh.counterbore_diameter is not None:
        cbd = resolve_expr(sh.counterbore_diameter, env)
        cbd_depth = resolve_expr(sh.counterbore_depth, env) if sh.counterbore_depth is not None else sd
        solid = (
            _pick_face(solid, face).workplane().center(sx, sy)
            .circle(cbd / 2).cutBlind(-cbd_depth)
        )

    # Through or blind hole
    solid = (
        _pick_face(solid, face).workplane().center(sx, sy)
        .circle(sd / 2).cutBlind(-depth)
    )

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
        solid = _apply_boss(solid, boss, env, L, W, H)

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
