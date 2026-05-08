"""Pydantic project schema for parametric CAD maker."""
from __future__ import annotations
from typing import Annotated, Any, Literal, Union
from pydantic import BaseModel, Field


class Parameter(BaseModel):
    name: str
    value: float | str  # float or formula string


class PlacementTarget(BaseModel):
    """Face-local coordinate target for placing a feature on a named plane."""
    plane: Literal["top", "bottom", "front", "back", "left", "right"]
    u: float | str = 0.0  # signed offset along u_axis (face-local)
    v: float | str = 0.0  # signed offset along v_axis (face-local)
    rotation: float = 0.0  # reserved — in-plane rotation (degrees, future use)


class CutoutSpec(BaseModel):
    target: PlacementTarget
    shape: Literal["rect", "circle", "slot"]
    width: float | str | None = None      # rect
    height: float | str | None = None     # rect
    diameter: float | str | None = None   # circle / slot
    slot_length: float | str | None = None  # slot (length along u)
    depth: float | str | None = None      # None = through-wall


class BossSpec(BaseModel):
    x: float | str
    y: float | str
    face: Literal["top", "bottom"] = "top"
    od: float | str  # outer diameter
    height: float | str
    hole_diameter: float | str | None = None


class ScrewHoleSpec(BaseModel):
    target: PlacementTarget
    diameter: float | str
    depth: float | str | None = None  # None = through-wall
    counterbore_diameter: float | str | None = None
    counterbore_depth: float | str | None = None
    countersink_diameter: float | str | None = None
    countersink_angle: float | str = 90.0


class BossPatternSpec(BaseModel):
    face: Literal["top", "bottom"] = "top"
    x0: float | str        # x center of first boss
    y0: float | str        # y center of first boss
    nx: int = 1            # columns
    ny: int = 1            # rows
    dx: float | str = 0.0  # x step between columns
    dy: float | str = 0.0  # y step between rows
    od: float | str
    height: float | str
    hole_diameter: float | str | None = None


class EnclosureFeature(BaseModel):
    type: Literal["enclosure"]
    id: str
    length: float | str
    width: float | str
    height: float | str
    wall: float | str = 2.0
    cutouts: list[CutoutSpec] = Field(default_factory=list)
    bosses: list[BossSpec] = Field(default_factory=list)
    boss_patterns: list[BossPatternSpec] = Field(default_factory=list)
    screw_holes: list[ScrewHoleSpec] = Field(default_factory=list)


class BoxPrimitive(BaseModel):
    type: Literal["box"]
    id: str
    length: float | str
    width: float | str
    height: float | str


class CylinderPrimitive(BaseModel):
    type: Literal["cylinder"]
    id: str
    diameter: float | str
    height: float | str


class SpherePrimitive(BaseModel):
    type: Literal["sphere"]
    id: str
    diameter: float | str


AnyFeature = Annotated[
    Union[EnclosureFeature, BoxPrimitive, CylinderPrimitive, SpherePrimitive],
    Field(discriminator="type"),
]


class Project(BaseModel):
    name: str = "Untitled"
    parameters: list[Parameter] = Field(default_factory=list)
    features: list[AnyFeature] = Field(default_factory=list)
