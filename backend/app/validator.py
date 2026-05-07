"""Validation routing: collect errors and warnings from a project."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def validate_project(project, env: dict[str, float]) -> ValidationResult:
    from .resolver import resolve_expr
    result = ValidationResult()

    for feat in project.features:
        fid = feat.id

        if feat.type == "enclosure":
            L = resolve_expr(feat.length, env)
            W = resolve_expr(feat.width, env)
            H = resolve_expr(feat.height, env)
            wall = resolve_expr(feat.wall, env)

            if L <= 0 or W <= 0 or H <= 0:
                result.errors.append(f"{fid}: enclosure dimensions must be positive")
            if wall <= 0:
                result.errors.append(f"{fid}: wall thickness must be positive")
            if wall * 2 >= L or wall * 2 >= W or wall * 2 >= H:
                result.errors.append(f"{fid}: wall too thick — interior would be non-positive")

            for i, cut in enumerate(feat.cutouts):
                cid = f"{fid}.cutouts[{i}]"
                depth_raw = cut.depth
                depth = resolve_expr(depth_raw, env) if depth_raw is not None else None
                if cut.shape == "rect":
                    if cut.width is None or cut.height is None:
                        result.errors.append(f"{cid}: rect cutout requires width and height")
                    else:
                        cw = resolve_expr(cut.width, env)
                        ch = resolve_expr(cut.height, env)
                        if cw <= 0 or ch <= 0:
                            result.errors.append(f"{cid}: cutout dimensions must be positive")
                elif cut.shape == "circle":
                    if cut.diameter is None:
                        result.errors.append(f"{cid}: circle cutout requires diameter")
                    else:
                        d = resolve_expr(cut.diameter, env)
                        if d <= 0:
                            result.errors.append(f"{cid}: diameter must be positive")
                elif cut.shape == "slot":
                    if cut.slot_length is None or cut.diameter is None:
                        result.errors.append(f"{cid}: slot cutout requires slot_length and diameter")
                    else:
                        sl = resolve_expr(cut.slot_length, env)
                        sd = resolve_expr(cut.diameter, env)
                        if sl <= 0 or sd <= 0:
                            result.errors.append(f"{cid}: slot dimensions must be positive")
                if depth is not None and depth <= 0:
                    result.errors.append(f"{cid}: depth must be positive")

            for i, boss in enumerate(feat.bosses):
                bid = f"{fid}.bosses[{i}]"
                od = resolve_expr(boss.od, env)
                bh = resolve_expr(boss.height, env)
                if od <= 0:
                    result.errors.append(f"{bid}: boss OD must be positive")
                if bh <= 0:
                    result.errors.append(f"{bid}: boss height must be positive")
                if boss.hole_diameter is not None:
                    hd = resolve_expr(boss.hole_diameter, env)
                    if hd >= od:
                        result.errors.append(f"{bid}: hole_diameter must be smaller than OD")

            for i, sh in enumerate(feat.screw_holes):
                sid = f"{fid}.screw_holes[{i}]"
                sd = resolve_expr(sh.diameter, env)
                if sd <= 0:
                    result.errors.append(f"{sid}: screw hole diameter must be positive")
                if sh.counterbore_diameter is not None:
                    cbd = resolve_expr(sh.counterbore_diameter, env)
                    if cbd <= sd:
                        result.warnings.append(f"{sid}: counterbore_diameter should be larger than hole diameter")

        elif feat.type == "box":
            L = resolve_expr(feat.length, env)
            W = resolve_expr(feat.width, env)
            H = resolve_expr(feat.height, env)
            if L <= 0 or W <= 0 or H <= 0:
                result.errors.append(f"{fid}: box dimensions must be positive")

        elif feat.type == "cylinder":
            D = resolve_expr(feat.diameter, env)
            H = resolve_expr(feat.height, env)
            if D <= 0 or H <= 0:
                result.errors.append(f"{fid}: cylinder dimensions must be positive")

        elif feat.type == "sphere":
            D = resolve_expr(feat.diameter, env)
            if D <= 0:
                result.errors.append(f"{fid}: sphere diameter must be positive")

    return result
