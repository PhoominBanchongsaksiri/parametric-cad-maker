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
            "cutouts": [{"target": {"plane": "front", "u": 0, "v": 0}, "shape": "rect", "width": 20, "height": 10}],
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
            "cutouts": [{"target": {"plane": "right", "u": 0, "v": 0}, "shape": "circle", "diameter": 10}],
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
            "cutouts": [{"target": {"plane": "top", "u": 0, "v": 0}, "shape": "slot", "slot_length": 20, "diameter": 6}],
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
            "screw_holes": [{"target": {"plane": "top", "u": 10, "v": 10}, "diameter": 3}],
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
            "screw_holes": [{"target": {"plane": "top", "u": 10, "v": 10}, "diameter": 3}],
        }],
    )
    proj_cb = Project(
        name="t", parameters=[],
        features=[{
            "type": "enclosure", "id": "body",
            "length": 100, "width": 60, "height": 40, "wall": 2,
            "screw_holes": [{
                "target": {"plane": "top", "u": 10, "v": 10}, "diameter": 3,
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
