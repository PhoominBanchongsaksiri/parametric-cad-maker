import { useProjectStore } from '../state/projectStore'
import type { AnyFeature } from '../types/project'

function featureIcon(type: string) {
  switch (type) {
    case 'enclosure': return '▣'
    case 'box':       return '□'
    case 'cylinder':  return '○'
    case 'sphere':    return '◉'
    default:          return '·'
  }
}

function EnclosureSubItems({ feat }: { feat: Extract<AnyFeature, { type: 'enclosure' }> }) {
  const cutouts = feat.cutouts ?? []
  const bosses = feat.bosses ?? []
  const bossPatterns = feat.boss_patterns ?? []
  const screwHoles = feat.screw_holes ?? []
  return (
    <div className="sub-items">
      {cutouts.map((c, i) => (
        <div key={i} className="sub-item">
          <span style={{ opacity: .5 }}>✂</span>
          {c.face} {c.shape}
        </div>
      ))}
      {bosses.map((b, i) => (
        <div key={i} className="sub-item">
          <span style={{ opacity: .5 }}>⬤</span>
          boss @ {String(b.x)}, {String(b.y)}
        </div>
      ))}
      {bossPatterns.map((bp, i) => (
        <div key={i} className="sub-item">
          <span style={{ opacity: .5 }}>⊞</span>
          boss pattern {bp.nx ?? 1}×{bp.ny ?? 1}
        </div>
      ))}
      {screwHoles.map((s, i) => (
        <div key={i} className="sub-item">
          <span style={{ opacity: .5 }}>◌</span>
          screw {s.face} ⌀{String(s.diameter)}
        </div>
      ))}
    </div>
  )
}

export function FeatureTree() {
  const { project, selectedFeatureId, setSelectedFeatureId } = useProjectStore()

  return (
    <>
      <div className="panel-header">Feature Tree</div>
      <div className="panel-body">
        <div className="section-label">Parameters ({project.parameters.length})</div>
        {project.parameters.map((p) => (
          <div key={p.name} className="sub-item" style={{ fontFamily: 'monospace' }}>
            <span style={{ color: 'var(--accent)' }}>{p.name}</span>
            <span style={{ opacity: .5 }}>=</span>
            {String(p.value)}
          </div>
        ))}

        <div className="section-label" style={{ marginTop: 12 }}>Features ({project.features.length})</div>
        {project.features.map((feat) => (
          <div key={feat.id}>
            <div
              className={`feature-item ${selectedFeatureId === feat.id ? 'selected' : ''}`}
              onClick={() => setSelectedFeatureId(feat.id === selectedFeatureId ? null : feat.id)}
            >
              <span>{featureIcon(feat.type)}</span>
              <span className={`feature-badge ${feat.type}`}>{feat.type}</span>
              <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{feat.id}</span>
            </div>
            {feat.type === 'enclosure' && selectedFeatureId === feat.id && (
              <EnclosureSubItems feat={feat} />
            )}
          </div>
        ))}

        {project.features.length === 0 && (
          <div style={{ color: 'var(--text2)', fontSize: 12, padding: '8px 4px' }}>
            No features. Edit the JSON to add features.
          </div>
        )}
      </div>
    </>
  )
}
