import { create } from 'zustand'
import type { Project, ValidationResult } from '../types/project'

const EXAMPLE_PROJECT: Project = {
  name: 'Basic Enclosure',
  parameters: [
    { name: 'L',       value: 100 },
    { name: 'W',       value: 60  },
    { name: 'H',       value: 40  },
    { name: 'wall',    value: 2   },
    { name: 'screw_d', value: 3   },
    { name: 'boss_od', value: 8   },
    { name: 'boss_h',  value: 6   },
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
        { face: 'front', shape: 'rect',   x: 0, y: 0, width: 20, height: 15 },
        { face: 'right', shape: 'circle', x: 0, y: 0, diameter: 10 },
        { face: 'top',   shape: 'slot',   x: 0, y: 0, slot_length: 30, diameter: 6 },
      ],
      bosses: [
        { face: 'bottom', x: 'L/2 - 10', y: 'W/2 - 10', od: 'boss_od', height: 'boss_h', hole_diameter: 3 },
      ],
      screw_holes: [
        { face: 'top',   x: 'L/2 - 8', y: 'W/2 - 8', diameter: 'screw_d', counterbore_diameter: 6, counterbore_depth: 2 },
        { face: 'front', x: 0,          y: 0,          diameter: 'screw_d', countersink_diameter: 6 },
      ],
    },
  ],
}

interface ProjectStore {
  project: Project
  selectedFeatureId: string | null
  glbUrl: string | null
  previewLoading: boolean
  previewError: string | null
  validation: ValidationResult | null
  backendOk: boolean

  setProject: (p: Project) => void
  setSelectedFeatureId: (id: string | null) => void
  setGlbUrl: (url: string | null) => void
  setPreviewLoading: (v: boolean) => void
  setPreviewError: (e: string | null) => void
  setValidation: (v: ValidationResult | null) => void
  setBackendOk: (v: boolean) => void

  updateParameter: (name: string, value: number | string) => void
  resetToExample: () => void
}

export const useProjectStore = create<ProjectStore>((set) => ({
  project: EXAMPLE_PROJECT,
  selectedFeatureId: null,
  glbUrl: null,
  previewLoading: false,
  previewError: null,
  validation: null,
  backendOk: false,

  setProject: (p) => set({ project: p }),
  setSelectedFeatureId: (id) => set({ selectedFeatureId: id }),
  setGlbUrl: (url) => set({ glbUrl: url }),
  setPreviewLoading: (v) => set({ previewLoading: v }),
  setPreviewError: (e) => set({ previewError: e }),
  setValidation: (v) => set({ validation: v }),
  setBackendOk: (v) => set({ backendOk: v }),

  updateParameter: (name, value) =>
    set((s) => ({
      project: {
        ...s.project,
        parameters: s.project.parameters.map((p) =>
          p.name === name ? { ...p, value } : p
        ),
      },
    })),

  resetToExample: () =>
    set({ project: EXAMPLE_PROJECT, glbUrl: null, validation: null, previewError: null }),
}))

export { EXAMPLE_PROJECT }
