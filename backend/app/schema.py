"""Pydantic project schema for the parametric CAD maker."""
from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


NumberExpr = float | int | str
FaceName = Literal["top", "bottom", "front", "back", "left", "right"]
BooleanOp = Literal["union", "cut", "subtract", "intersect"]


class Parameter(BaseModel):
    name: str
    value: NumberExpr


class Vec2(BaseModel):
    x: NumberExpr = 0.0
    y: NumberExpr = 0.0


class Vec3(BaseModel):
    x: NumberExpr = 0.0
    y: NumberExpr = 0.0
    z: NumberExpr = 0.0


class DisplayMetadata(BaseModel):
    name: str | None = None
    color: str | None = None
    opacity: float | None = None
    material: str | None = None


class PlaneSpec(BaseModel):
    """Custom construction plane for placing cuts, bosses, or features."""

    origin: Vec3 = Field(default_factory=Vec3)
    normal: Vec3 = Field(default_factory=lambda: Vec3(z=1))
    x_dir: Vec3 = Field(default_factory=lambda: Vec3(x=1))
    rotation: NumberExpr = 0.0


class Placement(BaseModel):
    position: Vec3 = Field(default_factory=Vec3)
    rotation: Vec3 = Field(default_factory=Vec3)


class PatternSpec(BaseModel):
    type: Literal["linear", "grid", "circular", "mirror"]
    count: int | None = None
    spacing: NumberExpr | None = None
    direction: Vec2 | Vec3 | None = None
    rows: int | None = None
    columns: int | None = None
    row_spacing: NumberExpr | None = None
    column_spacing: NumberExpr | None = None
    angle_step: NumberExpr | None = None
    radius: NumberExpr | None = None
    center: Vec2 | Vec3 | None = None
    axis: Literal["x", "y", "z"] | None = None


class BaseFeature(BaseModel):
    id: str
    operation: BooleanOp = "union"
    target: str | None = None
    position: Vec3 = Field(default_factory=Vec3)
    rotation: Vec3 = Field(default_factory=Vec3)
    display: DisplayMetadata | None = None


class BoxPrimitive(BaseFeature):
    type: Literal["box"]
    length: NumberExpr
    width: NumberExpr
    height: NumberExpr
    fillet_radius: NumberExpr | None = None
    chamfer_size: NumberExpr | None = None


class RoundedBoxPrimitive(BaseFeature):
    type: Literal["rounded_box"]
    length: NumberExpr
    width: NumberExpr
    height: NumberExpr
    fillet_radius: NumberExpr
    wall_thickness: NumberExpr | None = None


class CylinderPrimitive(BaseFeature):
    type: Literal["cylinder"]
    height: NumberExpr
    diameter: NumberExpr | None = None
    radius: NumberExpr | None = None
    wall_thickness: NumberExpr | None = None


class SpherePrimitive(BaseFeature):
    type: Literal["sphere"]
    diameter: NumberExpr | None = None
    radius: NumberExpr | None = None


class ConePrimitive(BaseFeature):
    type: Literal["cone"]
    height: NumberExpr
    radius1: NumberExpr
    radius2: NumberExpr = 0.0


class TorusPrimitive(BaseFeature):
    type: Literal["torus"]
    major_radius: NumberExpr
    minor_radius: NumberExpr


class WedgePrimitive(BaseFeature):
    type: Literal["wedge"]
    length: NumberExpr
    width: NumberExpr
    height: NumberExpr
    top_length: NumberExpr | None = None


class CapsulePrimitive(BaseFeature):
    type: Literal["capsule"]
    length: NumberExpr
    diameter: NumberExpr


class PolygonPrismPrimitive(BaseFeature):
    type: Literal["polygon_prism"]
    points: list[Vec2]
    height: NumberExpr


class ExtrudeFeature(BaseFeature):
    type: Literal["extrude"]
    profile: list[Vec2]
    height: NumberExpr


class RevolveFeature(BaseFeature):
    type: Literal["revolve"]
    profile: list[Vec2]
    angle: NumberExpr = 360.0


class SweepFeature(BaseFeature):
    type: Literal["sweep"]
    profile: list[Vec2]
    path: list[Vec3]


class LoftFeature(BaseFeature):
    type: Literal["loft"]
    sections: list[list[Vec2]]
    section_positions: list[Vec3] | None = None


class BooleanFeature(BaseModel):
    type: Literal["boolean"]
    id: str
    operation: BooleanOp
    target: str
    tool: str


class CutoutTarget(BaseModel):
    body: str | None = None
    face: FaceName | None = None
    plane: PlaneSpec | None = None
    u: NumberExpr = 0.0
    v: NumberExpr = 0.0


class CutoutSpec(BaseModel):
    """Legacy nested enclosure cutout, still accepted by the builder."""

    face: FaceName
    shape: Literal[
        "rect",
        "rectangle",
        "circle",
        "rounded_rect",
        "rounded_rectangle",
        "slot",
        "usb_a",
        "usb_c",
        "hdmi",
        "dc_jack",
    ]
    x: NumberExpr = 0.0
    y: NumberExpr = 0.0
    width: NumberExpr | None = None
    height: NumberExpr | None = None
    diameter: NumberExpr | None = None
    radius: NumberExpr | None = None
    corner_radius: NumberExpr | None = None
    slot_length: NumberExpr | None = None
    depth: NumberExpr | None = None
    rotation: NumberExpr = 0.0
    pattern: PatternSpec | None = None


class CutoutFeature(BaseModel):
    type: Literal["cutout"]
    id: str
    target: str
    shape: Literal[
        "rect",
        "rectangle",
        "circle",
        "rounded_rect",
        "rounded_rectangle",
        "slot",
        "usb_a",
        "usb_c",
        "hdmi",
        "dc_jack",
    ]
    placement: CutoutTarget = Field(default_factory=CutoutTarget)
    width: NumberExpr | None = None
    height: NumberExpr | None = None
    diameter: NumberExpr | None = None
    radius: NumberExpr | None = None
    corner_radius: NumberExpr | None = None
    slot_length: NumberExpr | None = None
    depth: NumberExpr | None = None
    through: bool = True
    rotation: NumberExpr = 0.0
    pattern: PatternSpec | None = None


class HoleFeature(BaseModel):
    type: Literal["hole"]
    id: str
    target: str
    placement: CutoutTarget = Field(default_factory=CutoutTarget)
    diameter: NumberExpr
    depth: NumberExpr | None = None
    through: bool = True
    counterbore_diameter: NumberExpr | None = None
    counterbore_depth: NumberExpr | None = None
    countersink_diameter: NumberExpr | None = None
    countersink_angle: NumberExpr = 90.0
    thread: str | None = None
    pattern: PatternSpec | None = None


class ScrewHoleSpec(BaseModel):
    x: NumberExpr
    y: NumberExpr
    face: FaceName = "top"
    diameter: NumberExpr
    depth: NumberExpr | None = None
    counterbore_diameter: NumberExpr | None = None
    counterbore_depth: NumberExpr | None = None
    countersink_diameter: NumberExpr | None = None
    countersink_angle: NumberExpr = 90.0
    thread: str | None = None
    pattern: PatternSpec | None = None


class ScrewHoleFeature(BaseModel):
    type: Literal["screw_hole"]
    id: str
    target: str
    placement: CutoutTarget = Field(default_factory=CutoutTarget)
    diameter: NumberExpr
    depth: NumberExpr | None = None
    through: bool = True
    counterbore_diameter: NumberExpr | None = None
    counterbore_depth: NumberExpr | None = None
    countersink_diameter: NumberExpr | None = None
    countersink_angle: NumberExpr = 90.0
    thread: str | None = None
    pattern: PatternSpec | None = None


class BossSpec(BaseModel):
    x: NumberExpr
    y: NumberExpr
    face: FaceName = "top"
    od: NumberExpr
    height: NumberExpr
    hole_diameter: NumberExpr | None = None
    fillet_radius: NumberExpr | None = None
    chamfer_size: NumberExpr | None = None
    pattern: PatternSpec | None = None


class BossFeature(BaseModel):
    type: Literal["boss"]
    id: str
    target: str
    placement: CutoutTarget = Field(default_factory=CutoutTarget)
    outer_diameter: NumberExpr
    height: NumberExpr
    inner_hole_diameter: NumberExpr | None = None
    fillet_radius: NumberExpr | None = None
    chamfer_size: NumberExpr | None = None
    counterbore_diameter: NumberExpr | None = None
    counterbore_depth: NumberExpr | None = None
    countersink_diameter: NumberExpr | None = None
    countersink_angle: NumberExpr = 90.0
    pattern: PatternSpec | None = None


class EnclosureFeature(BaseModel):
    type: Literal["enclosure"]
    id: str
    length: NumberExpr
    width: NumberExpr
    height: NumberExpr
    wall: NumberExpr = 2.0
    fillet_radius: NumberExpr | None = None
    chamfer_size: NumberExpr | None = None
    position: Vec3 = Field(default_factory=Vec3)
    rotation: Vec3 = Field(default_factory=Vec3)
    display: DisplayMetadata | None = None
    cutouts: list[CutoutSpec] = Field(default_factory=list)
    bosses: list[BossSpec] = Field(default_factory=list)
    screw_holes: list[ScrewHoleSpec] = Field(default_factory=list)


class VentFeature(BaseModel):
    """Grid of ventilation holes / slots on a named face."""

    type: Literal["vent"]
    id: str
    target: str
    face: FaceName = "top"
    shape: Literal["circle", "rect", "rounded_rect", "slot", "hex"] = "circle"
    # hole dimensions
    diameter: NumberExpr | None = None
    width: NumberExpr | None = None
    height: NumberExpr | None = None
    corner_radius: NumberExpr | None = None
    slot_length: NumberExpr | None = None
    # grid layout
    rows: int = 1
    columns: int = 1
    row_spacing: NumberExpr = 5.0
    col_spacing: NumberExpr = 5.0
    # centre offset on face
    offset_x: NumberExpr = 0.0
    offset_y: NumberExpr = 0.0
    # individual hole rotation (degrees)
    rotation: NumberExpr = 0.0
    depth: NumberExpr | None = None
    through: bool = True


AnyFeature = Annotated[
    Union[
        EnclosureFeature,
        BoxPrimitive,
        RoundedBoxPrimitive,
        CylinderPrimitive,
        SpherePrimitive,
        ConePrimitive,
        TorusPrimitive,
        WedgePrimitive,
        CapsulePrimitive,
        PolygonPrismPrimitive,
        ExtrudeFeature,
        RevolveFeature,
        SweepFeature,
        LoftFeature,
        BooleanFeature,
        CutoutFeature,
        HoleFeature,
        ScrewHoleFeature,
        BossFeature,
        VentFeature,
    ],
    Field(discriminator="type"),
]


class Project(BaseModel):
    name: str = "Untitled"
    parameters: list[Parameter] = Field(default_factory=list)
    features: list[AnyFeature] = Field(default_factory=list)
