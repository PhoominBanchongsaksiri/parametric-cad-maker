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
    assert any("greater than zero" in e for e in result.errors)


def test_wall_too_thick():
    proj = _make_enc(length=10, width=10, height=10, wall=6)
    result = validate_project(proj, build_env(proj.parameters))
    assert not result.ok
    assert any("wall thickness too large" in e for e in result.errors)


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
            "cutouts": [{"face": "top", "shape": "rect", "x": 0, "y": 0}],
        }],
    )
    result = validate_project(proj, {})
    assert not result.ok
    assert any("width" in e for e in result.errors)


def test_counterbore_too_small_is_error():
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
                "face": "top",
                "x": 0,
                "y": 0,
                "diameter": 4,
                "counterbore_diameter": 3,
            }],
        }],
    )
    result = validate_project(proj, {})
    assert not result.ok
    assert any("counterbore" in e for e in result.errors)


def test_duplicate_feature_ids():
    proj = Project(
        name="t",
        parameters=[],
        features=[
            {"type": "box", "id": "body", "length": 10, "width": 10, "height": 5},
            {"type": "cylinder", "id": "body", "diameter": 4, "height": 8},
        ],
    )
    result = validate_project(proj, {})
    assert not result.ok
    assert any("duplicate" in e for e in result.errors)


def test_invalid_target_body():
    proj = Project(
        name="t",
        parameters=[],
        features=[
            {
                "type": "hole",
                "id": "hole1",
                "target": "missing",
                "placement": {"face": "top", "u": 0, "v": 0},
                "diameter": 3,
            }
        ],
    )
    result = validate_project(proj, {})
    assert not result.ok
    assert any("invalid target body ID" in e for e in result.errors)


def test_invalid_plane_definition():
    proj = Project(
        name="t",
        parameters=[],
        features=[
            {"type": "box", "id": "body", "length": 20, "width": 20, "height": 10},
            {
                "type": "cutout",
                "id": "bad_plane_cut",
                "target": "body",
                "shape": "circle",
                "placement": {
                    "plane": {
                        "origin": {"x": 0, "y": 0, "z": 0},
                        "normal": {"x": 0, "y": 0, "z": 0},
                        "x_dir": {"x": 1, "y": 0, "z": 0}
                    }
                },
                "diameter": 4,
            }
        ],
    )
    result = validate_project(proj, {})
    assert not result.ok
    assert any("normal vector" in e for e in result.errors)


def test_hole_larger_than_body_face():
    proj = Project(
        name="t",
        parameters=[],
        features=[
            {"type": "box", "id": "body", "length": 20, "width": 20, "height": 10},
            {
                "type": "hole",
                "id": "huge_hole",
                "target": "body",
                "placement": {"face": "top", "u": 0, "v": 0},
                "diameter": 40,
            },
        ],
    )
    result = validate_project(proj, {})
    assert not result.ok
    assert any("larger than target face" in e for e in result.errors)


def test_invalid_cut_depth():
    proj = Project(
        name="t",
        parameters=[],
        features=[
            {"type": "box", "id": "body", "length": 20, "width": 20, "height": 10},
            {
                "type": "cutout",
                "id": "deep_cut",
                "target": "body",
                "shape": "rect",
                "placement": {"face": "top", "u": 0, "v": 0},
                "width": 4,
                "height": 4,
                "depth": 20,
                "through": False,
            },
        ],
    )
    result = validate_project(proj, {})
    assert not result.ok
    assert any("cut depth" in e for e in result.errors)
