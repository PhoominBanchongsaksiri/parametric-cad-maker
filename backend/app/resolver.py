"""Safe formula resolver for parameter expressions."""
from __future__ import annotations
import ast
import math
import operator as _op
from typing import Any

_SAFE_OPS = {
    ast.Add: _op.add,
    ast.Sub: _op.sub,
    ast.Mult: _op.mul,
    ast.Div: _op.truediv,
    ast.Pow: _op.pow,
    ast.USub: _op.neg,
    ast.UAdd: _op.pos,
    ast.Mod: _op.mod,
    ast.FloorDiv: _op.floordiv,
}

_SAFE_NAMES: dict[str, Any] = {
    "pi": math.pi,
    "e": math.e,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
}


def _eval_node(node: ast.AST, env: dict[str, float]) -> float:
    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise ValueError(f"Unsupported literal: {node.value!r}")
        return float(node.value)
    if isinstance(node, ast.Name):
        name = node.id
        if name in env:
            return env[name]
        if name in _SAFE_NAMES:
            return _SAFE_NAMES[name]  # type: ignore[return-value]
        raise ValueError(f"Unknown name: {name!r}")
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPS:
            raise ValueError(f"Unsupported operator: {op_type}")
        left = _eval_node(node.left, env)
        right = _eval_node(node.right, env)
        return _SAFE_OPS[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPS:
            raise ValueError(f"Unsupported unary operator: {op_type}")
        return _SAFE_OPS[op_type](_eval_node(node.operand, env))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls allowed")
        fname = node.func.id
        if fname not in _SAFE_NAMES:
            raise ValueError(f"Unknown function: {fname!r}")
        fn = _SAFE_NAMES[fname]
        args = [_eval_node(a, env) for a in node.args]
        return fn(*args)  # type: ignore[operator]
    raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def resolve_expr(expr: float | str, env: dict[str, float]) -> float:
    """Evaluate a parameter value or formula string to a float."""
    if isinstance(expr, (int, float)):
        return float(expr)
    try:
        tree = ast.parse(str(expr), mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Syntax error in expression {expr!r}: {exc}") from exc
    return _eval_node(tree.body, env)


def build_env(parameters: list, base: dict[str, float] | None = None) -> dict[str, float]:
    """Resolve all project parameters in declaration order."""
    env: dict[str, float] = dict(base or {})
    for param in parameters:
        env[param.name] = resolve_expr(param.value, env)
    return env
