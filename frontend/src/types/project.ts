export interface Parameter {
  name: string
  value: number | string
}

export interface PlacementTarget {
  plane: 'top' | 'bottom' | 'front' | 'back' | 'left' | 'right'
  u: number | string
  v: number | string
  rotation?: number | string
}

export interface CutoutSpec {
  target: PlacementTarget
  shape: 'rect' | 'circle' | 'slot'
  width?: number | string | null
  height?: number | string | null
  diameter?: number | string | null
  slot_length?: number | string | null
  depth?: number | string | null
}

export interface BossSpec {
  target: PlacementTarget
  od: number | string
  height: number | string
  hole_diameter?: number | string | null
}

export interface ScrewHoleSpec {
  target: PlacementTarget
  diameter: number | string
  depth?: number | string | null
  counterbore_diameter?: number | string | null
  counterbore_depth?: number | string | null
  countersink_diameter?: number | string | null
  countersink_angle?: number | string
}

export interface EnclosureFeature {
  type: 'enclosure'
  id: string
  length: number | string
  width: number | string
  height: number | string
  wall?: number | string
  cutouts?: CutoutSpec[]
  bosses?: BossSpec[]
  screw_holes?: ScrewHoleSpec[]
}

export interface BoxPrimitive {
  type: 'box'
  id: string
  length: number | string
  width: number | string
  height: number | string
}

export interface CylinderPrimitive {
  type: 'cylinder'
  id: string
  diameter: number | string
  height: number | string
}

export interface SpherePrimitive {
  type: 'sphere'
  id: string
  diameter: number | string
}

export type AnyFeature = EnclosureFeature | BoxPrimitive | CylinderPrimitive | SpherePrimitive

export interface Project {
  name: string
  parameters: Parameter[]
  features: AnyFeature[]
}

export const EXAMPLE_PROJECT: Project = {
  name: 'Basic Enclosure',
  parameters: [
    { name: 'L',       value: 100 },
    { name: 'W',       value: 60 },
    { name: 'H',       value: 40 },
    { name: 'wall',    value: 2 },
    { name: 'screw_d', value: 3 },
    { name: 'boss_od', value: 8 },
    { name: 'boss_h',  value: 6 },
  ],
  features: [
    {
      type: 'enclosure',
      id: 'body',
      length: 'L',
      width: 'W',
      height: 'H',
      wall: 'wall',
      cutouts: [
        { target: { plane: 'front', u: 0, v: 0 }, shape: 'rect',   width: 20, height: 15 },
        { target: { plane: 'right', u: 0, v: 0 }, shape: 'circle', diameter: 10 },
        { target: { plane: 'top',   u: 0, v: 0 }, shape: 'slot',   slot_length: 30, diameter: 6 },
      ],
      bosses: [
        { target: { plane: 'bottom', u: 'L/2 - 10', v: 'W/2 - 10' }, od: 'boss_od', height: 'boss_h', hole_diameter: 3 },
      ],
      screw_holes: [
        { target: { plane: 'top',   u: 'L/2 - 8', v: 'W/2 - 8' }, diameter: 'screw_d', counterbore_diameter: 6, counterbore_depth: 2 },
        { target: { plane: 'front', u: 0, v: 0 },                  diameter: 'screw_d', countersink_diameter: 6 },
      ],
    },
  ],
}
