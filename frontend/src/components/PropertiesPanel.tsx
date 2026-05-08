import { Fragment, useState, useEffect, CSSProperties } from 'react'
import type { Project } from '../types/project'

interface PropertiesPanelProps {
  project: Project
  onProjectChange: (p: Project) => void
  validationResult: { valid: boolean; errors: string[]; warnings: string[] } | null
}

const s: Record<string, CSSProperties> = {
  panel: {
    width: 300,
    flexShrink: 0,
    background: '#13151c',
    borderLeft: '1px solid #2a2d3a',
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
    borderBottom: '1px solid #2a2d3a',
  },
  title: {
    padding: '8px 12px 4px',
    fontSize: 11,
    fontWeight: 600,
    color: '#9ca3af',
    letterSpacing: '0.06em',
    textTransform: 'uppercase',
  },
  paramTable: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 0,
  },
  paramCell: {
    padding: '5px 12px',
    fontSize: 12,
    borderBottom: '1px solid #1e2130',
  },
  paramInput: {
    width: '100%',
    background: 'transparent',
    border: 'none',
    outline: 'none',
    color: '#e0e0e0',
    fontSize: 12,
    fontFamily: 'monospace',
  },
  jsonArea: {
    flex: 1,
    resize: 'none',
    background: '#0c0e14',
    border: 'none',
    borderTop: '1px solid #2a2d3a',
    color: '#c0c8d8',
    fontSize: 11,
    fontFamily: 'monospace',
    padding: 12,
    outline: 'none',
    lineHeight: 1.5,
  },
  applyBtn: {
    margin: 8,
    padding: '6px 12px',
    background: '#1e2130',
    border: '1px solid #3a3d4a',
    borderRadius: 4,
    color: '#c0c8d8',
    fontSize: 12,
    cursor: 'pointer',
    flexShrink: 0,
  },
  validMsg: {
    padding: '4px 12px',
    fontSize: 11,
    flexShrink: 0,
  },
  divider: { height: 1, background: '#2a2d3a', flexShrink: 0 },
}

export default function PropertiesPanel({ project, onProjectChange, validationResult }: PropertiesPanelProps) {
  const [jsonText, setJsonText] = useState('')
  const [jsonError, setJsonError] = useState<string | null>(null)

  useEffect(() => {
    setJsonText(JSON.stringify(project, null, 2))
    setJsonError(null)
  }, [project])

  function handleParamChange(index: number, value: string) {
    const params = project.parameters.map((p, i) => {
      if (i !== index) return p
      const num = Number(value)
      return { ...p, value: isNaN(num) ? value : num }
    })
    onProjectChange({ ...project, parameters: params })
  }

  function applyJson() {
    try {
      const parsed = JSON.parse(jsonText) as Project
      setJsonError(null)
      onProjectChange(parsed)
    } catch (e) {
      setJsonError((e as Error).message)
    }
  }

  return (
    <div style={s.panel}>
      <div style={s.sectionHeader}>Properties &amp; JSON</div>

      <div style={s.title}>Parameters</div>
      <div style={s.paramTable}>
        {project.parameters.map((p, i) => (
          <Fragment key={p.name}>
            <div style={{ ...s.paramCell, color: '#a5b4fc' }}>{p.name}</div>
            <div style={{ ...s.paramCell, background: '#0f1117' }}>
              <input
                style={s.paramInput}
                value={String(p.value)}
                onChange={(e) => handleParamChange(i, e.target.value)}
              />
            </div>
          </Fragment>
        ))}
      </div>

      {validationResult && (
        <div
          style={{
            ...s.validMsg,
            color: validationResult.valid ? '#22c55e' : '#ef4444',
          }}
        >
          {validationResult.valid
            ? `Valid${validationResult.warnings.length ? ` (${validationResult.warnings.length} warning${validationResult.warnings.length > 1 ? 's' : ''})` : ''}`
            : validationResult.errors.join('; ')}
        </div>
      )}

      <div style={s.divider} />
      <div style={s.title}>Project JSON</div>

      <textarea
        style={s.jsonArea}
        value={jsonText}
        onChange={(e) => setJsonText(e.target.value)}
        spellCheck={false}
      />

      {jsonError && (
        <div style={{ ...s.validMsg, color: '#ef4444' }}>{jsonError}</div>
      )}

      <button style={s.applyBtn} onClick={applyJson}>
        Apply JSON
      </button>
    </div>
  )
}
