import type { CSSProperties } from 'react'
import type { Project } from '../types/project'

interface FeatureTreeProps {
  project: Project
}

const s: Record<string, CSSProperties> = {
  panel: {
    width: 220,
    flexShrink: 0,
    background: '#13151c',
    borderRight: '1px solid #2a2d3a',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  sectionHeader: {
    padding: '8px 12px 4px',
    fontSize: 10,
    fontWeight: 700,
    letterSpacing: '0.08em',
    color: '#6b7280',
    textTransform: 'uppercase',
  },
  paramRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '2px 12px',
    fontSize: 12,
    color: '#c0c8d8',
  },
  paramName: { color: '#a5b4fc' },
  paramVal: { color: '#e0e0e0' },
  featureRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    padding: '4px 12px',
    fontSize: 12,
    color: '#c0c8d8',
  },
  featureIcon: {
    fontSize: 10,
    background: '#1e2130',
    border: '1px solid #3a3d4a',
    borderRadius: 3,
    padding: '1px 4px',
    color: '#6b7280',
  },
  divider: {
    height: 1,
    background: '#2a2d3a',
    margin: '6px 0',
  },
}

export default function FeatureTree({ project }: FeatureTreeProps) {
  return (
    <div style={s.panel}>
      <div style={s.sectionHeader}>Feature Tree</div>
      <div style={s.divider} />
      <div style={s.sectionHeader}>Parameters ({project.parameters.length})</div>
      {project.parameters.map((p) => (
        <div key={p.name} style={s.paramRow}>
          <span style={s.paramName}>{p.name}</span>
          <span style={s.paramVal}>= {p.value}</span>
        </div>
      ))}
      <div style={s.divider} />
      <div style={s.sectionHeader}>Features ({project.features.length})</div>
      {project.features.map((f) => (
        <div key={f.id} style={s.featureRow}>
          <span style={s.featureIcon}>{f.type.slice(0, 3)}</span>
          <span style={{ color: '#60a5fa' }}>{f.id}</span>
          <span style={{ color: '#6b7280', fontSize: 11 }}>{f.type}</span>
        </div>
      ))}
    </div>
  )
}
