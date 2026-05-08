export interface Parameter {
  name: string
  value: number | string
}

export interface CutoutSpec {
  face: 'top' | 'bottom' | 'front' | 'back' | 'left' | 'right'
  shape: 'rect' | 'circle' | 'slot'
  x?: number | string
  y?: number | string
  width?: number | string | null
  height?: number | string | null
  diameter?: number | string | null
  slot_length?: number | string | null
  depth?: number | string | null
}

export interface BossSpec {
  x: number | string
  y: number | string
  face?: 'top' | 'bottom'
  od: number | string
  height: number | string
  hole_diameter?: number | string | null
}

export interface ScrewHoleSpec {
  x: number | string
  y: number | string
  face?: 'top' | 'bottom' | 'front' | 'back' | 'left' | 'right'
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
    { name: 'L', value: 100 },
    { name: 'W', value: 60 },
    { name: 'H', value: 40 },
    { name: 'wall', value: 2 },
    { name: 'screw_d', value: 3 },
    { name: 'boss_od', value: 8 },
    { name: 'boss_h', value: 6 },
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
        { face: 'front', shape: 'rect', x: 0, y: 0, width: 20, height: 15 },
        { face: 'right', shape: 'circle', x: 0, y: 0, diameter: 10 },
        { face: 'top', shape: 'slot', x: 0, y: 0, slot_length: 30, diameter: 6 },
      ],
      bosses: [
        { face: 'bottom', x: 'L/2 - 10', y: 'W/2 - 10', od: 'boss_od', height: 'boss_h', hole_diameter: 3 },
      ],
      screw_holes: [
        { face: 'top', x: 'L/2 - 8', y: 'W/2 - 8', diameter: 'screw_d', counterbore_diameter: 6, counterbore_depth: 2 },
        { face: 'front', x: 0, y: 0, diameter: 'screw_d', countersink_diameter: 6 },
      ],
    },
  ],
}
