import { useProjectStore } from '../state/projectStore'

const PARAM_LABELS: Record<string, string> = {
  L:              'Length (L)',
  W:              'Width (W)',
  H:              'Height (H)',
  wall:           'Wall',
  floor:          'Floor',
  cornerRadius:   'Corner radius',
  lidHeight:      'Lid height',
  lidLipDepth:    'Lid lip depth',
  lidTolerance:   'Lid tolerance',
  bossOuterDiameter: 'Boss OD',
  boss_od:        'Boss OD',
  screwDiameter:  'Screw ⌀',
  screw_d:        'Screw ⌀',
  boss_h:         'Boss height',
}

function label(name: string) {
  return PARAM_LABELS[name] ?? name
}

export function ParameterPanel() {
  const { project, updateParameter, selectedFeatureId } = useProjectStore()

  const selectedFeat = selectedFeatureId
    ? project.features.find((f) => f.id === selectedFeatureId)
    : null

  return (
    <>
      <div className="section-label">Parameters</div>
      {project.parameters.map((p) => (
        <div key={p.name} className="param-row">
          <span className="param-label">{label(p.name)}</span>
          <input
            className="param-input"
            value={String(p.value)}
            onChange={(e) => {
              const raw = e.target.value
              const num = Number(raw)
              updateParameter(p.name, isNaN(num) || raw.trim() === '' ? raw : num)
            }}
          />
        </div>
      ))}

      {selectedFeat && (
        <>
          <hr className="divider" />
          <div className="section-label">Selected: {selectedFeat.id}</div>
          <div style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--text2)', lineHeight: 1.8 }}>
            <div><b>type:</b> {selectedFeat.type}</div>
            {'length' in selectedFeat && <div><b>length:</b> {String(selectedFeat.length)}</div>}
            {'width'  in selectedFeat && <div><b>width:</b>  {String(selectedFeat.width)}</div>}
            {'height' in selectedFeat && <div><b>height:</b> {String(selectedFeat.height)}</div>}
            {'wall'   in selectedFeat && <div><b>wall:</b>   {String(selectedFeat.wall)}</div>}
            {'diameter' in selectedFeat && <div><b>diameter:</b> {String((selectedFeat as { diameter: unknown }).diameter)}</div>}
            {selectedFeat.type === 'enclosure' && (
              <>
                <div><b>cutouts:</b> {(selectedFeat.cutouts ?? []).length}</div>
                <div><b>bosses:</b>  {(selectedFeat.bosses ?? []).length}</div>
                <div><b>screw holes:</b> {(selectedFeat.screw_holes ?? []).length}</div>
              </>
            )}
          </div>
        </>
      )}
    </>
  )
}
