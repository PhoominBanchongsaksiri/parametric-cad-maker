from app.schema import Project
from app.resolver import build_env
from app.validator import validate_project


def _make_enc(length=100, width=60, height=40, wall=2):
    return Project(
        name="t",
        parameters=[],
        features=[{
            "type": "enclosure",
            "id": "body",
            "length": length,
            "width": width,
            "height": height,
            "wall": wall,
        }],
    )


def test_valid_enclosure():
    proj = _make_enc()
    result = validate_project(proj, build_env(proj.parameters))
    assert result.ok
    assert result.errors == []


def test_zero_dimension():
    proj = _make_enc(length=0)
    result = validate_project(proj, build_env(proj.parameters))
    assert not result.ok
    assert any("positive" in e for e in result.errors)


def test_wall_too_thick():
    proj = _make_enc(length=10, width=10, height=10, wall=6)
    result = validate_project(proj, build_env(proj.parameters))
    assert not result.ok
    assert any("wall too thick" in e for e in result.errors)


def test_missing_rect_dims():
    proj = Project(
        name="t",
        parameters=[],
        features=[{
            "type": "enclosure",
            "id": "body",
            "length": 100,
            "width": 60,
            "height": 40,
            "wall": 2,
            "cutouts": [{"target": {"plane": "top", "u": 0, "v": 0}, "shape": "rect"}],
        }],
    )
    result = validate_project(proj, {})
    assert not result.ok
    assert any("width and height" in e for e in result.errors)


def test_counterbore_warning():
    proj = Project(
        name="t",
        parameters=[],
        features=[{
            "type": "enclosure",
            "id": "body",
            "length": 100,
            "width": 60,
            "height": 40,
            "wall": 2,
            "screw_holes": [{
                "target": {"plane": "top", "u": 0, "v": 0},
                "diameter": 4,
                "counterbore_diameter": 3,
            }],
        }],
    )
    result = validate_project(proj, {})
    assert any("counterbore" in w for w in result.warnings)
