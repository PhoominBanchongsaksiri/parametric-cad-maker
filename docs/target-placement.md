# Target Placement System

Features such as cutouts and screw holes are positioned using a `PlacementTarget` object instead of raw `face`/`x`/`y` fields. This gives every feature a consistent, validated coordinate reference.

## PlacementTarget schema

```json
{
  "plane":    "top",   // required — one of the six named faces
  "u":        0,       // signed offset along the face's u-axis (mm)
  "v":        0,       // signed offset along the face's v-axis (mm)
  "rotation": 0        // reserved — in-plane rotation in degrees (future use)
}
```

`u` and `v` accept either a number or a parameter expression string (e.g. `"L/2 - 8"`).

## Coordinate convention

Each face has a fixed local (u, v) frame. The origin is the centre of the face; positive u and v point as shown below.

| face   | u direction | v direction | face centre (world)   |
|--------|-------------|-------------|-----------------------|
| top    | +world X    | +world Y    | (0, 0, +H/2)          |
| bottom | +world X    | −world Y    | (0, 0, −H/2)          |
| front  | +world X    | +world Z    | (0, −W/2, 0)          |
| back   | −world X    | +world Z    | (0, +W/2, 0)          |
| left   | −world Y    | +world Z    | (−L/2, 0, 0)          |
| right  | +world Y    | +world Z    | (+L/2, 0, 0)          |

`cutter_dir` always points **inward** (= −normal). The builder extrudes cutters along `cutter_dir` so geometry is removed from the outside surface toward the interior.

## Example usage

```json
"cutouts": [
  {
    "target": {"plane": "front", "u": 0, "v": 0},
    "shape": "rect",
    "width": 40,
    "height": 20
  },
  {
    "target": {"plane": "right", "u": 0, "v": 0},
    "shape": "circle",
    "diameter": 12
  }
],
"screw_holes": [
  {
    "target": {"plane": "top", "u": "L/2 - 8", "v": "W/2 - 8"},
    "diameter": "screw_d",
    "counterbore_diameter": 6,
    "counterbore_depth": 2
  }
]
```

## Validation

`validate_target_bounds` in `planes.py` checks that (u, v) falls within the half-extents of the named face. Out-of-bounds placements are reported as errors by the `/api/validate` endpoint before any geometry is built.

## Implementation details

- `backend/app/planes.py` — `PlaneInfo` dataclass and `get_plane_info()` / `validate_target_bounds()` API.
- `backend/app/schema.py` — `PlacementTarget` model; used by `CutoutSpec` and `ScrewHoleSpec`.
- `backend/app/builder.py` — `_apply_cutout` and `_apply_screw_hole` call `get_plane_info()` and construct world-space workplanes via `cq.Plane(origin, normal=cutter_dir, xDir=u_axis)`.

## Future: curved surfaces

When cylinder and sphere surface placement is added, it will live in a separate module (e.g. `curved_surfaces.py`) and introduce a new `surface` discriminator field alongside `plane`. The `PlacementTarget` schema will be extended at that point.
