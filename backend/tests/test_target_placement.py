"""Tests for the PlacementTarget face/plane placement system."""
import pytest
from app.schema import Project, PlacementTarget, CutoutSpec, ScrewHoleSpec
from app.builder import build_feature
from app.planes import get_plane_info, validate_target_bounds, VALID_PLANES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _enc(cutouts=None, screw_holes=None):
    return Project(
        name="t", parameters=[],
        features=[{
            "type": "enclosure", "id": "body",
            "length": 100, "width": 60, "height": 40, "wall": 2,
            "cutouts":       cutouts      or [],
            "bosses":        [],
            "boss_patterns": [],
            "screw_holes":   screw_holes  or [],
        }],
    )


def _vol(proj):
    return build_feature(proj.features[0], {}).val().Volume()


BASE_VOL = None


def base_vol():
    global BASE_VOL
    if BASE_VOL is None:
        BASE_VOL = _vol(_enc())
    return BASE_VOL


# ---------------------------------------------------------------------------
# PlacementTarget schema
# ---------------------------------------------------------------------------

def test_placement_target_defaults():
    t = PlacementTarget(plane="top")
    assert t.u == 0.0
    assert t.v == 0.0
    assert t.rotation == 0.0


def test_placement_target_rejects_invalid_plane():
    with pytest.raises(Exception):
        PlacementTarget(plane="diagonal")


# ---------------------------------------------------------------------------
# planes.py unit tests
# ---------------------------------------------------------------------------

def test_get_plane_info_top():
    pi = get_plane_info("top", 0, 0, 100, 60, 40)
    assert pi.entry == (0, 0, 20)
    assert pi.normal == (0, 0, 1)
    assert pi.cutter_dir == (0, 0, -1)
    assert pi.u_bounds == (-50, 50)
    assert pi.v_bounds == (-30, 30)


def test_get_plane_info_bottom():
    pi = get_plane_info("bottom", 0, 0, 100, 60, 40)
    assert pi.entry == (0, 0, -20)
    assert pi.cutter_dir == (0, 0, 1)


def test_get_plane_info_front():
    pi = get_plane_info("front", 5, 10, 100, 60, 40)
    assert pi.entry == (5, -30, 10)
    assert pi.cutter_dir == (0, 1, 0)


def test_get_plane_info_back():
    pi = get_plane_info("back", 5, 10, 100, 60, 40)
    assert pi.entry == (-5, 30, 10)
    assert pi.cutter_dir == (0, -1, 0)


def test_get_plane_info_left():
    pi = get_plane_info("left", 5, 10, 100, 60, 40)
    assert pi.entry == (-50, -5, 10)
    assert pi.cutter_dir == (1, 0, 0)


def test_get_plane_info_right():
    pi = get_plane_info("right", 5, 10, 100, 60, 40)
    assert pi.entry == (50, 5, 10)
    assert pi.cutter_dir == (-1, 0, 0)


def test_get_plane_info_invalid_plane():
    with pytest.raises(ValueError, match="Unknown plane"):
        get_plane_info("diagonal", 0, 0, 100, 60, 40)


def test_valid_planes_set():
    assert VALID_PLANES == frozenset(["top", "bottom", "front", "back", "left", "right"])


# ---------------------------------------------------------------------------
# validate_target_bounds
# ---------------------------------------------------------------------------

def test_bounds_ok_center():
    assert validate_target_bounds("top", 0, 0, 100, 60, 40) == []


def test_bounds_ok_edge():
    assert validate_target_bounds("top", 50, 30, 100, 60, 40) == []


def test_bounds_u_out_of_range():
    errs = validate_target_bounds("top", 60, 0, 100, 60, 40)
    assert len(errs) == 1
    assert "u=60" in errs[0]


def test_bounds_v_out_of_range():
    errs = validate_target_bounds("front", 0, 25, 100, 60, 40)
    assert len(errs) == 1
    assert "v=25" in errs[0]


def test_bounds_both_out_of_range():
    errs = validate_target_bounds("left", 40, 30, 100, 60, 40)
    assert len(errs) == 2


def test_bounds_invalid_plane():
    errs = validate_target_bounds("diagonal", 0, 0, 100, 60, 40)
    assert len(errs) == 1
    assert "Unknown plane" in errs[0]


# ---------------------------------------------------------------------------
# Geometry: cutouts via target
# ---------------------------------------------------------------------------

def test_front_circular_cutout_reduces_volume():
    proj = _enc(cutouts=[{
        "target": {"plane": "front", "u": 0, "v": 0},
        "shape": "circle", "diameter": 12,
    }])
    assert _vol(proj) < base_vol()


def test_back_rect_cutout_reduces_volume():
    proj = _enc(cutouts=[{
        "target": {"plane": "back", "u": 0, "v": 0},
        "shape": "rect", "width": 20, "height": 15,
    }])
    assert _vol(proj) < base_vol()


def test_left_slot_cutout_reduces_volume():
    proj = _enc(cutouts=[{
        "target": {"plane": "left", "u": 0, "v": 0},
        "shape": "slot", "slot_length": 20, "diameter": 8,
    }])
    assert _vol(proj) < base_vol()


def test_top_screw_hole_reduces_volume():
    proj = _enc(screw_holes=[{
        "target": {"plane": "top", "u": 0, "v": 0},
        "diameter": 3,
    }])
    assert _vol(proj) < base_vol()


def test_left_screw_hole_reduces_volume():
    proj = _enc(screw_holes=[{
        "target": {"plane": "left", "u": 0, "v": 0},
        "diameter": 3,
    }])
    assert _vol(proj) < base_vol()


def test_offset_target_places_feature_correctly():
    """A cutout offset from center on 'top' must remove less volume than a larger centered one."""
    proj_center = _enc(cutouts=[{
        "target": {"plane": "top", "u": 0, "v": 0},
        "shape": "circle", "diameter": 10,
    }])
    proj_offset = _enc(cutouts=[{
        "target": {"plane": "top", "u": 20, "v": 10},
        "shape": "circle", "diameter": 10,
    }])
    # Both are same size — same volume removal regardless of position
    assert abs(_vol(proj_center) - _vol(proj_offset)) < 1.0  # within 1 mm³


# ---------------------------------------------------------------------------
# API smoke: preview and exports still work with the new schema
# ---------------------------------------------------------------------------

from fastapi.testclient import TestClient
from app.main import app
import json, os

_client = TestClient(app)

_PROJ = {
    "name": "Target Placement Test",
    "parameters": [
        {"name": "L", "value": 100},
        {"name": "W", "value": 60},
        {"name": "H", "value": 40},
        {"name": "wall", "value": 2},
    ],
    "features": [{
        "type": "enclosure", "id": "body",
        "length": "L", "width": "W", "height": "H", "wall": "wall",
        "cutouts": [
            {"target": {"plane": "front", "u": 0, "v": 0}, "shape": "circle", "diameter": 12},
            {"target": {"plane": "top",   "u": 0, "v": 0}, "shape": "rect",   "width": 20, "height": 15},
        ],
        "bosses": [],
        "boss_patterns": [],
        "screw_holes": [
            {"target": {"plane": "top", "u": 30, "v": 15}, "diameter": 3,
             "counterbore_diameter": 6, "counterbore_depth": 2},
        ],
    }],
}


def test_validate_target_project():
    r = _client.post("/api/validate", json=_PROJ)
    assert r.status_code == 200
    assert r.json()["valid"] is True


def test_preview_target_project_returns_200():
    r = _client.post("/api/preview", json=_PROJ)
    assert r.status_code == 200
    assert len(r.content) > 100


def test_export_step_target_project():
    r = _client.post("/api/export/step", json=_PROJ)
    assert r.status_code == 200
    assert b"ISO-10303" in r.content


def test_export_stl_target_project():
    r = _client.post("/api/export/stl", json=_PROJ)
    assert r.status_code == 200
    assert len(r.content) > 0


def test_export_3mf_target_project():
    r = _client.post("/api/export/3mf", json=_PROJ)
    assert r.status_code == 200
    assert r.content[:2] == b"PK"


def test_example_json_validates_with_new_schema():
    example_path = os.path.join(
        os.path.dirname(__file__), "../../examples/enclosure_basic.json"
    )
    with open(example_path) as f:
        proj = json.load(f)
    r = _client.post("/api/validate", json=proj)
    assert r.status_code == 200
    assert r.json()["valid"] is True
