import pytest
from app.resolver import resolve_expr, build_env
from app.schema import Parameter


def test_literal_float():
    assert resolve_expr(3.14, {}) == pytest.approx(3.14)


def test_literal_int():
    assert resolve_expr(10, {}) == pytest.approx(10.0)


def test_simple_arithmetic():
    assert resolve_expr("2 + 3 * 4", {}) == pytest.approx(14.0)


def test_variable_substitution():
    assert resolve_expr("L * 2", {"L": 5.0}) == pytest.approx(10.0)


def test_nested_formula():
    env = {"L": 100.0, "wall": 2.0}
    assert resolve_expr("L - wall * 2", env) == pytest.approx(96.0)


def test_math_functions():
    import math
    assert resolve_expr("sqrt(4)", {}) == pytest.approx(2.0)
    assert resolve_expr("pi", {}) == pytest.approx(math.pi)


def test_build_env_ordered():
    params = [
        Parameter(name="L", value=100),
        Parameter(name="half", value="L / 2"),
    ]
    env = build_env(params)
    assert env["L"] == pytest.approx(100.0)
    assert env["half"] == pytest.approx(50.0)


def test_unknown_name_raises():
    with pytest.raises(ValueError, match="Unknown"):
        resolve_expr("__import__('os')", {})


def test_attribute_access_blocked():
    with pytest.raises((ValueError, AttributeError)):
        resolve_expr("x.__class__", {"x": 1.0})
