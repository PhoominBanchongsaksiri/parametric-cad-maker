"""Regression matrix: all-face cutouts, bossPattern, precise volume probes."""
import math
import pytest
from app.schema import Project
from app.builder import build_feature

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _enc(cutouts=None, bosses=None, boss_patterns=None, screw_holes=None):
    return Project(
        name="t", parameters=[],
        features=[{
            "type": "enclosure", "id": "body",
            "length": 100, "width": 60, "height": 40, "wall": 2,
            "cutouts":       cutouts       or [],
            "bosses":        bosses        or [],
            "boss_patterns": boss_patterns or [],
            "screw_holes":   screw_holes   or [],
        }],
    )

def _vol(proj):
    return build_feature(proj.features[0], {}).val().Volume()

_BASE_VOL = None

def base_vol():
    global _BASE_VOL
    if _BASE_VOL is None:
        _BASE_VOL = _vol(_enc())
    return _BASE_VOL


# ---------------------------------------------------------------------------
# All-face × all-shape cutout matrix
# 6 faces × 3 shapes = 18 cases; every case must reduce volume vs. baseline
# ---------------------------------------------------------------------------

ALL_FACES = ["top", "bottom", "front", "back", "left", "right"]

_RECT_CUT   = {"shape": "rect",   "x": 0, "y": 0, "width": 10, "height": 8}
_CIRCLE_CUT = {"shape": "circle", "x": 0, "y": 0, "diameter": 8}
_SLOT_CUT   = {"shape": "slot",   "x": 0, "y": 0, "slot_length": 10, "diameter": 6}


@pytest.mark.parametrize("face", ALL_FACES)
def test_rect_cutout_all_faces(face):
    proj = _enc(cutouts=[{"face": face, **_RECT_CUT}])
    assert _vol(proj) < base_vol(), f"rect cutout on {face} did not reduce volume"


@pytest.mark.parametrize("face", ALL_FACES)
def test_circle_cutout_all_faces(face):
    proj = _enc(cutouts=[{"face": face, **_CIRCLE_CUT}])
    assert _vol(proj) < base_vol(), f"circle cutout on {face} did not reduce volume"


@pytest.mark.parametrize("face", ALL_FACES)
def test_slot_cutout_all_faces(face):
    proj = _enc(cutouts=[{"face": face, **_SLOT_CUT}])
    assert _vol(proj) < base_vol(), f"slot cutout on {face} did not reduce volume"


# ---------------------------------------------------------------------------
# bossPattern regression
# ---------------------------------------------------------------------------

def test_boss_pattern_1x1_equals_single_boss():
    """1×1 bossPattern must produce same volume change as a single boss."""
    proj_single = _enc(bosses=[{"x": 0, "y": 0, "face": "top", "od": 8, "height": 5}])
    proj_pattern = _enc(boss_patterns=[{
        "face": "top", "x0": 0, "y0": 0,
        "nx": 1, "ny": 1, "dx": 0, "dy": 0,
        "od": 8, "height": 5,
    }])
    assert _vol(proj_pattern) == pytest.approx(_vol(proj_single), rel=1e-4)


def test_boss_pattern_2x2_adds_more_volume_than_1x1():
    proj_1x1 = _enc(boss_patterns=[{
        "face": "top", "x0": -15, "y0": -10,
        "nx": 1, "ny": 1, "dx": 30, "dy": 20,
        "od": 6, "height": 4,
    }])
    proj_2x2 = _enc(boss_patterns=[{
        "face": "top", "x0": -15, "y0": -10,
        "nx": 2, "ny": 2, "dx": 30, "dy": 20,
        "od": 6, "height": 4,
    }])
    assert _vol(proj_2x2) > _vol(proj_1x1)


def test_boss_pattern_2x2_volume_approx():
    """2×2 pattern adds 4× the volume of a single boss (no overlap)."""
    bv = base_vol()
    proj_single = _enc(bosses=[{"x": 0, "y": 0, "face": "bottom", "od": 6, "height": 4}])
    proj_2x2 = _enc(boss_patterns=[{
        "face": "bottom", "x0": -15, "y0": -10,
        "nx": 2, "ny": 2, "dx": 30, "dy": 20,
        "od": 6, "height": 4,
    }])
    single_delta = _vol(proj_single) - bv
    pattern_delta = _vol(proj_2x2) - bv
    assert pattern_delta == pytest.approx(4 * single_delta, rel=0.02)


def test_boss_pattern_with_hole_less_volume_than_without():
    proj_no_hole = _enc(boss_patterns=[{
        "face": "top", "x0": 0, "y0": 0,
        "nx": 2, "ny": 1, "dx": 25, "dy": 0,
        "od": 8, "height": 5,
    }])
    proj_hole = _enc(boss_patterns=[{
        "face": "top", "x0": 0, "y0": 0,
        "nx": 2, "ny": 1, "dx": 25, "dy": 0,
        "od": 8, "height": 5, "hole_diameter": 3,
    }])
    assert _vol(proj_hole) < _vol(proj_no_hole)


def test_boss_pattern_on_bottom_face():
    proj = _enc(boss_patterns=[{
        "face": "bottom", "x0": -20, "y0": -15,
        "nx": 3, "ny": 2, "dx": 20, "dy": 15,
        "od": 6, "height": 4,
    }])
    assert _vol(proj) > base_vol()


# ---------------------------------------------------------------------------
# Counterbore precise volume probe
# ---------------------------------------------------------------------------

def test_counterbore_volume_delta():
    """Counterbore removes an annular cylinder on top of the through-hole.
    delta = pi * cbd_depth * ((cbd/2)^2 - (hole_d/2)^2)
    """
    cbd = 6.0
    cbd_depth = 2.0
    hole_d = 3.0

    proj_plain = _enc(screw_holes=[{"face": "top", "x": 0, "y": 0, "diameter": hole_d}])
    proj_cb = _enc(screw_holes=[{
        "face": "top", "x": 0, "y": 0, "diameter": hole_d,
        "counterbore_diameter": cbd, "counterbore_depth": cbd_depth,
    }])

    delta = _vol(proj_plain) - _vol(proj_cb)
    expected = math.pi * cbd_depth * ((cbd / 2) ** 2 - (hole_d / 2) ** 2)
    assert delta == pytest.approx(expected, rel=0.02)


def test_counterbore_on_front_face():
    proj_plain = _enc(screw_holes=[{"face": "front", "x": 0, "y": 0, "diameter": 3}])
    proj_cb = _enc(screw_holes=[{
        "face": "front", "x": 0, "y": 0, "diameter": 3,
        "counterbore_diameter": 6, "counterbore_depth": 2,
    }])
    assert _vol(proj_cb) < _vol(proj_plain)


def test_counterbore_on_bottom_face():
    proj_plain = _enc(screw_holes=[{"face": "bottom", "x": 0, "y": 0, "diameter": 3}])
    proj_cb = _enc(screw_holes=[{
        "face": "bottom", "x": 0, "y": 0, "diameter": 3,
        "counterbore_diameter": 6, "counterbore_depth": 2,
    }])
    assert _vol(proj_cb) < _vol(proj_plain)


# ---------------------------------------------------------------------------
# Countersink volume probe
# ---------------------------------------------------------------------------

def test_countersink_reduces_volume_more_than_plain_hole():
    proj_plain = _enc(screw_holes=[{"face": "top", "x": 0, "y": 0, "diameter": 3}])
    proj_cs = _enc(screw_holes=[{
        "face": "top", "x": 0, "y": 0, "diameter": 3,
        "countersink_diameter": 7,
    }])
    assert _vol(proj_cs) < _vol(proj_plain)


def test_countersink_larger_diameter_removes_more():
    proj_cs_small = _enc(screw_holes=[{
        "face": "top", "x": 0, "y": 0, "diameter": 3,
        "countersink_diameter": 5,
    }])
    proj_cs_large = _enc(screw_holes=[{
        "face": "top", "x": 0, "y": 0, "diameter": 3,
        "countersink_diameter": 8,
    }])
    assert _vol(proj_cs_large) < _vol(proj_cs_small)


def test_countersink_on_front_face():
    proj_plain = _enc(screw_holes=[{"face": "front", "x": 0, "y": 0, "diameter": 3}])
    proj_cs = _enc(screw_holes=[{
        "face": "front", "x": 0, "y": 0, "diameter": 3,
        "countersink_diameter": 6,
    }])
    assert _vol(proj_cs) < _vol(proj_plain)


# ---------------------------------------------------------------------------
# Multiple simultaneous cutouts (stress)
# ---------------------------------------------------------------------------

def test_multiple_cutouts_cumulative():
    """Each additional cutout must further reduce volume."""
    v0 = base_vol()
    proj1 = _enc(cutouts=[{"face": "top",   "shape": "rect",   "x": 0, "y": 0, "width": 10, "height": 8}])
    proj2 = _enc(cutouts=[
        {"face": "top",   "shape": "rect",   "x": 0, "y": 0, "width": 10, "height": 8},
        {"face": "front", "shape": "circle", "x": 0, "y": 0, "diameter": 8},
    ])
    proj3 = _enc(cutouts=[
        {"face": "top",   "shape": "rect",   "x": 0, "y": 0, "width": 10, "height": 8},
        {"face": "front", "shape": "circle", "x": 0, "y": 0, "diameter": 8},
        {"face": "right", "shape": "slot",   "x": 0, "y": 0, "slot_length": 10, "diameter": 6},
    ])
    v1 = _vol(proj1)
    v2 = _vol(proj2)
    v3 = _vol(proj3)
    assert v1 < v0
    assert v2 < v1
    assert v3 < v2
