"""Probe-based geometry regression tests."""
import pytest
import cadquery as cq
from app.schema import Project
from app.resolver import build_env
from app.builder import build_feature, build_all


def _enc_project(**kwargs):
    defaults = dict(length=100, width=60, height=40, wall=2)
    defaults.update(kwargs)
    return Project(
        name="t",
        parameters=[],
        features=[{"type": "enclosure", "id": "body", **defaults}],
    )


# ---------------------------------------------------------------------------
# Basic enclosure geometry probes
# ---------------------------------------------------------------------------

def test_enclosure_bounding_box():
    proj = _enc_project(length=100, width=60, height=40)
    env = build_env(proj.parameters)
    wp = build_feature(proj.features[0], env)
    bb = wp.val().BoundingBox()
    assert bb.xlen == pytest.approx(100, abs=0.01)
    assert bb.ylen == pytest.approx(60, abs=0.01)
    assert bb.zlen == pytest.approx(40, abs=0.01)


def test_enclosure_is_hollow():
    """Volume of hollow shell should be less than solid box."""
    proj = _enc_project(length=100, width=60, height=40, wall=2)
    env = build_env(proj.parameters)
    wp = build_feature(proj.features[0], env)
    shell_vol = wp.val().Volume()
    solid_vol = 100 * 60 * 40
    assert shell_vol < solid_vol
    # Interior volume: (100-4)*(60-4)*(40-4) = 96*56*36 = 193536
    expected_shell = solid_vol - 96 * 56 * 36
    assert shell_vol == pytest.approx(expected_shell, rel=0.01)


def test_rect_cutout_reduces_volume():
    proj_no_cut = _enc_project()
    proj_cut = Project(
        name="t", parameters=[],
        features=[{
            "type": "enclosure", "id": "body",
            "length": 100, "width": 60, "height": 40, "wall": 2,
            "cutouts": [{"face": "front", "shape": "rect", "x": 0, "y": 0, "width": 20, "height": 10}],
        }],
    )
    env = {}
    vol_no = build_feature(proj_no_cut.features[0], env).val().Volume()
    vol_cut = build_feature(proj_cut.features[0], env).val().Volume()
    assert vol_cut < vol_no


def test_circle_cutout_reduces_volume():
    proj_cut = Project(
        name="t", parameters=[],
        features=[{
            "type": "enclosure", "id": "body",
            "length": 100, "width": 60, "height": 40, "wall": 2,
            "cutouts": [{"face": "right", "shape": "circle", "x": 0, "y": 0, "diameter": 10}],
        }],
    )
    proj_no = _enc_project()
    vol_no = build_feature(proj_no.features[0], {}).val().Volume()
    vol_cut = build_feature(proj_cut.features[0], {}).val().Volume()
    assert vol_cut < vol_no


def test_slot_cutout_reduces_volume():
    proj_cut = Project(
        name="t", parameters=[],
        features=[{
            "type": "enclosure", "id": "body",
            "length": 100, "width": 60, "height": 40, "wall": 2,
            "cutouts": [{"face": "top", "shape": "slot", "x": 0, "y": 0, "slot_length": 20, "diameter": 6}],
        }],
    )
    proj_no = _enc_project()
    vol_no = build_feature(proj_no.features[0], {}).val().Volume()
    vol_cut = build_feature(proj_cut.features[0], {}).val().Volume()
    assert vol_cut < vol_no


def test_boss_increases_volume():
    proj_boss = Project(
        name="t", parameters=[],
        features=[{
            "type": "enclosure", "id": "body",
            "length": 100, "width": 60, "height": 40, "wall": 2,
            "bosses": [{"face": "bottom", "x": 0, "y": 0, "od": 8, "height": 5}],
        }],
    )
    proj_no = _enc_project()
    vol_no = build_feature(proj_no.features[0], {}).val().Volume()
    vol_boss = build_feature(proj_boss.features[0], {}).val().Volume()
    assert vol_boss > vol_no


def test_boss_with_hole():
    proj = Project(
        name="t", parameters=[],
        features=[{
            "type": "enclosure", "id": "body",
            "length": 100, "width": 60, "height": 40, "wall": 2,
            "bosses": [{"face": "bottom", "x": 0, "y": 0, "od": 8, "height": 5, "hole_diameter": 3}],
        }],
    )
    proj_no_hole = Project(
        name="t", parameters=[],
        features=[{
            "type": "enclosure", "id": "body",
            "length": 100, "width": 60, "height": 40, "wall": 2,
            "bosses": [{"face": "bottom", "x": 0, "y": 0, "od": 8, "height": 5}],
        }],
    )
    vol_hole = build_feature(proj.features[0], {}).val().Volume()
    vol_no_hole = build_feature(proj_no_hole.features[0], {}).val().Volume()
    assert vol_hole < vol_no_hole


def test_screw_hole_reduces_volume():
    proj_sh = Project(
        name="t", parameters=[],
        features=[{
            "type": "enclosure", "id": "body",
            "length": 100, "width": 60, "height": 40, "wall": 2,
            "screw_holes": [{"face": "top", "x": 10, "y": 10, "diameter": 3}],
        }],
    )
    vol_no = _enc_project().features[0]
    wp_no = build_feature(vol_no, {})
    wp_sh = build_feature(proj_sh.features[0], {})
    assert wp_sh.val().Volume() < wp_no.val().Volume()


def test_counterbore_reduces_more():
    proj_plain = Project(
        name="t", parameters=[],
        features=[{
            "type": "enclosure", "id": "body",
            "length": 100, "width": 60, "height": 40, "wall": 2,
            "screw_holes": [{"face": "top", "x": 10, "y": 10, "diameter": 3}],
        }],
    )
    proj_cb = Project(
        name="t", parameters=[],
        features=[{
            "type": "enclosure", "id": "body",
            "length": 100, "width": 60, "height": 40, "wall": 2,
            "screw_holes": [{
                "face": "top", "x": 10, "y": 10, "diameter": 3,
                "counterbore_diameter": 6, "counterbore_depth": 1.5,
            }],
        }],
    )
    vol_plain = build_feature(proj_plain.features[0], {}).val().Volume()
    vol_cb = build_feature(proj_cb.features[0], {}).val().Volume()
    assert vol_cb < vol_plain


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

def test_box_primitive():
    proj = Project(
        name="t", parameters=[],
        features=[{"type": "box", "id": "b", "length": 10, "width": 5, "height": 3}],
    )
    wp = build_feature(proj.features[0], {})
    bb = wp.val().BoundingBox()
    assert bb.xlen == pytest.approx(10, abs=0.01)
    assert bb.ylen == pytest.approx(5, abs=0.01)
    assert bb.zlen == pytest.approx(3, abs=0.01)


def test_cylinder_primitive():
    import math
    proj = Project(
        name="t", parameters=[],
        features=[{"type": "cylinder", "id": "c", "diameter": 10, "height": 20}],
    )
    wp = build_feature(proj.features[0], {})
    vol = wp.val().Volume()
    expected = math.pi * 5**2 * 20
    assert vol == pytest.approx(expected, rel=0.01)


def test_sphere_primitive():
    import math
    proj = Project(
        name="t", parameters=[],
        features=[{"type": "sphere", "id": "s", "diameter": 10}],
    )
    wp = build_feature(proj.features[0], {})
    vol = wp.val().Volume()
    expected = (4/3) * math.pi * 5**3
    assert vol == pytest.approx(expected, rel=0.01)


# ---------------------------------------------------------------------------
# Parameter formulas through builder
# ---------------------------------------------------------------------------

def test_formula_parameters_in_builder():
    from app.schema import Parameter
    proj = Project(
        name="t",
        parameters=[
            Parameter(name="L", value=80),
            Parameter(name="half_L", value="L / 2"),
        ],
        features=[{"type": "box", "id": "b", "length": "half_L", "width": 10, "height": 5}],
    )
    env = build_env(proj.parameters)
    wp = build_feature(proj.features[0], env)
    bb = wp.val().BoundingBox()
    assert bb.xlen == pytest.approx(40, abs=0.01)


def test_multiple_primitives_boolean_cut():
    proj = Project(
        name="t",
        parameters=[],
        features=[
            {"type": "box", "id": "body", "length": 20, "width": 20, "height": 20},
            {"type": "cylinder", "id": "cutter", "target": "body", "operation": "cut", "diameter": 8, "height": 30},
        ],
    )
    solid = build_all(proj, {})[0][1]
    assert solid.val().Volume() < 20 * 20 * 20


@pytest.mark.parametrize("shape", ["rounded_box", "cone", "torus", "wedge", "capsule", "polygon_prism", "extrude", "revolve"])
def test_advanced_primitives_build(shape):
    feature_by_shape = {
        "rounded_box": {"type": "rounded_box", "id": "f", "length": 20, "width": 10, "height": 8, "fillet_radius": 1},
        "cone": {"type": "cone", "id": "f", "height": 10, "radius1": 5, "radius2": 2},
        "torus": {"type": "torus", "id": "f", "major_radius": 10, "minor_radius": 2},
        "wedge": {"type": "wedge", "id": "f", "length": 20, "width": 10, "height": 8, "top_length": 4},
        "capsule": {"type": "capsule", "id": "f", "length": 30, "diameter": 8},
        "polygon_prism": {
            "type": "polygon_prism",
            "id": "f",
            "height": 5,
            "points": [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 5, "y": 8}],
        },
        "extrude": {
            "type": "extrude",
            "id": "f",
            "height": 5,
            "profile": [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 10, "y": 5}, {"x": 0, "y": 5}],
        },
        "revolve": {
            "type": "revolve",
            "id": "f",
            "angle": 360,
            "profile": [{"x": 2, "y": 0}, {"x": 5, "y": 0}, {"x": 5, "y": 8}, {"x": 2, "y": 8}],
        },
    }
    proj = Project(name="t", parameters=[], features=[feature_by_shape[shape]])
    wp = build_feature(proj.features[0], {})
    assert wp.val().Volume() > 0


@pytest.mark.parametrize("face", ["top", "bottom", "front", "back", "left", "right"])
def test_hole_feature_on_all_six_faces(face):
    proj = Project(
        name="t",
        parameters=[],
        features=[
            {"type": "box", "id": "body", "length": 40, "width": 30, "height": 20},
            {
                "type": "hole",
                "id": f"hole_{face}",
                "target": "body",
                "placement": {"face": face, "u": 0, "v": 0},
                "diameter": 4,
            },
        ],
    )
    cut = build_all(proj, {})[0][1]
    assert cut.val().Volume() < 40 * 30 * 20


def test_usb_c_cutout_reduces_volume():
    proj = Project(
        name="t",
        parameters=[],
        features=[
            {"type": "box", "id": "body", "length": 50, "width": 30, "height": 20},
            {
                "type": "cutout",
                "id": "usb_c",
                "target": "body",
                "shape": "usb_c",
                "placement": {"face": "front", "u": 0, "v": 0},
                "depth": 5,
                "through": False,
            },
        ],
    )
    cut = build_all(proj, {})[0][1]
    assert cut.val().Volume() < 50 * 30 * 20


def test_grid_pattern_cuts_multiple_holes():
    base = Project(
        name="base",
        parameters=[],
        features=[
            {"type": "box", "id": "body", "length": 60, "width": 40, "height": 10},
            {
                "type": "hole",
                "id": "one_hole",
                "target": "body",
                "placement": {"face": "top", "u": 0, "v": 0},
                "diameter": 3,
            },
        ],
    )
    grid = Project(
        name="grid",
        parameters=[],
        features=[
            {"type": "box", "id": "body", "length": 60, "width": 40, "height": 10},
            {
                "type": "hole",
                "id": "vent_grid",
                "target": "body",
                "placement": {"face": "top", "u": 0, "v": 0},
                "diameter": 3,
                "pattern": {"type": "grid", "rows": 3, "columns": 4, "row_spacing": 8, "column_spacing": 8},
            },
        ],
    )
    assert build_all(grid, {})[0][1].val().Volume() < build_all(base, {})[0][1].val().Volume()


def test_custom_plane_cutout_reduces_volume():
    proj = Project(
        name="t",
        parameters=[],
        features=[
            {"type": "box", "id": "body", "length": 40, "width": 30, "height": 20},
            {
                "type": "cutout",
                "id": "plane_cut",
                "target": "body",
                "shape": "circle",
                "placement": {
                    "plane": {
                        "origin": {"x": 0, "y": 0, "z": 10},
                        "normal": {"x": 0, "y": 0, "z": 1},
                        "x_dir": {"x": 1, "y": 0, "z": 0}
                    },
                    "u": 0,
                    "v": 0
                },
                "diameter": 5,
            },
        ],
    )
    assert build_all(proj, {})[0][1].val().Volume() < 40 * 30 * 20


# ---------------------------------------------------------------------------
# Vent feature tests
# ---------------------------------------------------------------------------

def test_vent_circle_removes_volume():
    proj = Project(
        name="t",
        parameters=[],
        features=[
            {"type": "box", "id": "body", "length": 80, "width": 60, "height": 20},
            {
                "type": "vent",
                "id": "vents",
                "target": "body",
                "face": "top",
                "shape": "circle",
                "diameter": 4,
                "rows": 3,
                "columns": 4,
                "row_spacing": 10,
                "col_spacing": 10,
            },
        ],
    )
    env = build_env(proj.parameters)
    result = build_all(proj, env)
    solid_vol = 80 * 60 * 20
    assert result[0][1].val().Volume() < solid_vol


def test_vent_hex_removes_volume():
    proj = Project(
        name="t",
        parameters=[],
        features=[
            {"type": "box", "id": "body", "length": 60, "width": 40, "height": 15},
            {
                "type": "vent",
                "id": "vents",
                "target": "body",
                "face": "top",
                "shape": "hex",
                "diameter": 5,
                "rows": 2,
                "columns": 3,
                "row_spacing": 8,
                "col_spacing": 8,
            },
        ],
    )
    env = build_env(proj.parameters)
    result = build_all(proj, env)
    assert result[0][1].val().Volume() < 60 * 40 * 15


def test_vent_rect_blind():
    proj = Project(
        name="t",
        parameters=[],
        features=[
            {"type": "box", "id": "body", "length": 80, "width": 60, "height": 20},
            {
                "type": "vent",
                "id": "vents",
                "target": "body",
                "face": "top",
                "shape": "rect",
                "width": 6,
                "height": 3,
                "rows": 2,
                "columns": 3,
                "row_spacing": 10,
                "col_spacing": 12,
                "through": False,
                "depth": 5,
            },
        ],
    )
    env = build_env(proj.parameters)
    result = build_all(proj, env)
    assert result[0][1].val().Volume() < 80 * 60 * 20
