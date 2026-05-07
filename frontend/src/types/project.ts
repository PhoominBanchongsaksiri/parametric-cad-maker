export interface Parameter {
  name: string
  value: number | string
}

export interface CutoutSpec {
  face: 'top' | 'bottom' | 'front' | 'back' | 'left' | 'right'
  shape: 'rect' | 'circle' | 'slot'
  x?: number | string
  y?: number | string
  width?: number | string
  height?: number | string
  diameter?: number | string
  slot_length?: number | string
  depth?: number | string
}

export interface BossSpec {
  x: number | string
  y: number | string
  face?: 'top' | 'bottom'
  od: number | string
  height: number | string
  hole_diameter?: number | string
}

export interface BossPatternSpec {
  face?: 'top' | 'bottom'
  x0: number | string
  y0: number | string
  nx?: number
  ny?: number
  dx?: number | string
  dy?: number | string
  od: number | string
  height: number | string
  hole_diameter?: number | string
}

export interface ScrewHoleSpec {
  x: number | string
  y: number | string
  face?: string
  diameter: number | string
  depth?: number | string
  counterbore_diameter?: number | string
  counterbore_depth?: number | string
  countersink_diameter?: number | string
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
  boss_patterns?: BossPatternSpec[]
  screw_holes?: ScrewHoleSpec[]
}

export interface BoxFeature {
  type: 'box'
  id: string
  length: number | string
  width: number | string
  height: number | string
}

export interface CylinderFeature {
  type: 'cylinder'
  id: string
  diameter: number | string
  height: number | string
}

export interface SphereFeature {
  type: 'sphere'
  id: string
  diameter: number | string
}

export type AnyFeature = EnclosureFeature | BoxFeature | CylinderFeature | SphereFeature

export interface Project {
  name: string
  parameters: Parameter[]
  features: AnyFeature[]
}

export interface ValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
}
