"""Plane mapping helpers for face-relative feature placement.

Coordinate convention
---------------------
Every named planar face of a rectangular enclosure has a local (u, v) frame:

  face   | u direction       | v direction       | origin
  -------|-------------------|-------------------|------------------
  top    | +world X          | +world Y          | (0, 0, +H/2)
  bottom | +world X          | -world Y          | (0, 0, -H/2)
  front  | +world X          | +world Z          | (0, -W/2, 0)
  back   | -world X          | +world Z          | (0, +W/2, 0)
  left   | -world Y          | +world Z          | (-L/2, 0, 0)
  right  | +world Y          | +world Z          | (+L/2, 0, 0)

The ``cutter_dir`` always points inward (from the outer surface toward the
interior of the solid) and equals ``-normal``.

Future surfaces (cylinder, sphere) will live in a separate module once the
planar system is proven.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
import cadquery as cq


# ---------------------------------------------------------------------------
# PlaneInfo dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PlaneInfo:
    """All geometric data needed to place a feature on a named planar face."""
    entry:       tuple[float, float, float]  # world point at (u, v) on outer surface
    normal:      tuple[float, float, float]  # outward face normal
    u_axis:      tuple[float, float, float]  # world direction of +U
    v_axis:      tuple[float, float, float]  # world direction of +V
    cutter_dir:  tuple[float, float, float]  # inward cutter direction (= -normal)
    u_bounds:    tuple[float, float]         # approximate valid U range
    v_bounds:    tuple[float, float]         # approximate valid V range

    def cq_plane(self) -> cq.Plane:
        """Return a CadQuery Plane whose Z points along cutter_dir and X along u_axis.

        Use this to build world-space cutters:
            cq.Workplane(plane_info.cq_plane()).rect(w, h).extrude(depth)
        """
        return cq.Plane(
            origin=cq.Vector(*self.entry),
            normal=cq.Vector(*self.cutter_dir),
            xDir=cq.Vector(*self.u_axis),
        )


# ---------------------------------------------------------------------------
# Internal plane definition table
# ---------------------------------------------------------------------------

_T = tuple[float, float, float]

@dataclass
class _PlaneDef:
    normal:      _T
    u_axis:      _T
    v_axis:      _T
    cutter_dir:  _T
    entry_fn:    Callable[[float, float, float, float, float], _T]
    u_bounds_fn: Callable[[float, float, float], tuple[float, float]]
    v_bounds_fn: Callable[[float, float, float], tuple[float, float]]


_PLANE_DEFS: dict[str, _PlaneDef] = {
    "top": _PlaneDef(
        normal     = (0,  0,  1),
        u_axis     = (1,  0,  0),
        v_axis     = (0,  1,  0),
        cutter_dir = (0,  0, -1),
        entry_fn   = lambda u, v, L, W, H: (u,  v,  H / 2),
        u_bounds_fn= lambda L, W, H: (-L / 2, L / 2),
        v_bounds_fn= lambda L, W, H: (-W / 2, W / 2),
    ),
    "bottom": _PlaneDef(
        normal     = (0,  0, -1),
        u_axis     = (1,  0,  0),
        v_axis     = (0, -1,  0),
        cutter_dir = (0,  0,  1),
        entry_fn   = lambda u, v, L, W, H: (u, -v, -H / 2),
        u_bounds_fn= lambda L, W, H: (-L / 2, L / 2),
        v_bounds_fn= lambda L, W, H: (-W / 2, W / 2),
    ),
    "front": _PlaneDef(
        normal     = (0, -1,  0),
        u_axis     = (1,  0,  0),
        v_axis     = (0,  0,  1),
        cutter_dir = (0,  1,  0),
        entry_fn   = lambda u, v, L, W, H: (u, -W / 2, v),
        u_bounds_fn= lambda L, W, H: (-L / 2, L / 2),
        v_bounds_fn= lambda L, W, H: (-H / 2, H / 2),
    ),
    "back": _PlaneDef(
        normal     = (0,  1,  0),
        u_axis     = (-1, 0,  0),
        v_axis     = (0,  0,  1),
        cutter_dir = (0, -1,  0),
        entry_fn   = lambda u, v, L, W, H: (-u,  W / 2, v),
        u_bounds_fn= lambda L, W, H: (-L / 2, L / 2),
        v_bounds_fn= lambda L, W, H: (-H / 2, H / 2),
    ),
    "left": _PlaneDef(
        normal     = (-1, 0,  0),
        u_axis     = (0, -1,  0),
        v_axis     = (0,  0,  1),
        cutter_dir = (1,  0,  0),
        entry_fn   = lambda u, v, L, W, H: (-L / 2, -u, v),
        u_bounds_fn= lambda L, W, H: (-W / 2, W / 2),
        v_bounds_fn= lambda L, W, H: (-H / 2, H / 2),
    ),
    "right": _PlaneDef(
        normal     = (1,  0,  0),
        u_axis     = (0,  1,  0),
        v_axis     = (0,  0,  1),
        cutter_dir = (-1, 0,  0),
        entry_fn   = lambda u, v, L, W, H: (L / 2, u, v),
        u_bounds_fn= lambda L, W, H: (-W / 2, W / 2),
        v_bounds_fn= lambda L, W, H: (-H / 2, H / 2),
    ),
}

VALID_PLANES: frozenset[str] = frozenset(_PLANE_DEFS)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_plane_info(plane: str, u: float, v: float, L: float, W: float, H: float) -> PlaneInfo:
    """Return all geometric data for feature placement at (u, v) on ``plane``.

    Parameters
    ----------
    plane : str
        One of "top", "bottom", "front", "back", "left", "right".
    u, v : float
        Signed face-local coordinates.  Centred at 0 (face midpoint) and
        measured in the same units as L/W/H (typically mm).
    L, W, H : float
        Enclosure outer dimensions (length, width, height).

    Raises
    ------
    ValueError
        If ``plane`` is not a recognised name.
    """
    if plane not in _PLANE_DEFS:
        raise ValueError(
            f"Unknown plane '{plane}'. Valid planes: {sorted(VALID_PLANES)}"
        )
    d = _PLANE_DEFS[plane]
    return PlaneInfo(
        entry      = d.entry_fn(u, v, L, W, H),
        normal     = d.normal,
        u_axis     = d.u_axis,
        v_axis     = d.v_axis,
        cutter_dir = d.cutter_dir,
        u_bounds   = d.u_bounds_fn(L, W, H),
        v_bounds   = d.v_bounds_fn(L, W, H),
    )


def validate_target_bounds(
    plane: str,
    u: float,
    v: float,
    L: float,
    W: float,
    H: float,
) -> list[str]:
    """Return a list of bound-check error strings (empty → OK)."""
    if plane not in _PLANE_DEFS:
        return [f"Unknown plane '{plane}'"]
    d = _PLANE_DEFS[plane]
    ub = d.u_bounds_fn(L, W, H)
    vb = d.v_bounds_fn(L, W, H)
    errors: list[str] = []
    if not (ub[0] <= u <= ub[1]):
        errors.append(f"u={u} out of bounds [{ub[0]}, {ub[1]}] for plane '{plane}'")
    if not (vb[0] <= v <= vb[1]):
        errors.append(f"v={v} out of bounds [{vb[0]}, {vb[1]}] for plane '{plane}'")
    return errors
