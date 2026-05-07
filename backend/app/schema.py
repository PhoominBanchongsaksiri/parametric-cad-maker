"""Pydantic project schema for parametric CAD maker."""
from __future__ import annotations
from typing import Annotated, Any, Literal, Union
from pydantic import BaseModel, Field


class Parameter(BaseModel):
    name: str
    value: float | str  # float or formula string


class CutoutSpec(BaseModel):
    face: Literal["top", "bottom", "front", "back", "left", "right"]
    shape: Literal["rect", "circle", "slot"]
    x: float | str = 0.0
    y: float | str = 0.0
    width: float | str | None = None   # rect / slot
    height: float | str | None = None  # rect / slot
    diameter: float | str | None = None  # circle
    slot_length: float | str | None = None  # slot (length along x)
    depth: float | str | None = None  # None = through


class BossSpec(BaseModel):
    x: float | str
    y: float | str
    face: Literal["top", "bottom"] = "top"
    od: float | str  # outer diameter
    height: float | str
    hole_diameter: float | str | None = None


class ScrewHoleSpec(BaseModel):
    x: float | str
    y: float | str
    face: Literal["top", "bottom", "front", "back", "left", "right"] = "top"
    diameter: float | str
    depth: float | str | None = None  # None = through
    counterbore_diameter: float | str | None = None
    counterbore_depth: float | str | None = None
    countersink_diameter: float | str | None = None
    countersink_angle: float | str = 90.0


class EnclosureFeature(BaseModel):
    type: Literal["enclosure"]
    id: str
    length: float | str
    width: float | str
    height: float | str
    wall: float | str = 2.0
    cutouts: list[CutoutSpec] = Field(default_factory=list)
    bosses: list[BossSpec] = Field(default_factory=list)
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
