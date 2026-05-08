import type { CSSProperties } from 'react'

interface HeaderProps {
  backendOnline: boolean
  loading: boolean
  previewActive: boolean
  onValidate: () => void
  onPreview: () => void
  onExport: (fmt: 'step' | 'stl' | '3mf') => void
  onExportJson: () => void
  onResetExample: () => void
}

const s: Record<string, CSSProperties> = {
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '0 12px',
    height: 44,
    background: '#13151c',
    borderBottom: '1px solid #2a2d3a',
    flexShrink: 0,
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 14,
    fontWeight: 600,
    color: '#e0e0e0',
    marginRight: 4,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
  },
  status: {
    display: 'flex',
    alignItems: 'center',
    gap: 5,
    fontSize: 12,
    color: '#9ca3af',
    marginRight: 8,
  },
  spacer: { flex: 1 },
  btn: {
    padding: '4px 10px',
    fontSize: 12,
    fontWeight: 500,
    borderRadius: 4,
    border: '1px solid #3a3d4a',
    background: '#1e2130',
    color: '#c0c8d8',
    cursor: 'pointer',
  },
  btnPrimary: {
    padding: '4px 10px',
    fontSize: 12,
    fontWeight: 500,
    borderRadius: 4,
    border: '1px solid #2563eb',
    background: '#1d4ed8',
    color: '#fff',
    cursor: 'pointer',
  },
  btnDanger: {
    padding: '4px 10px',
    fontSize: 12,
    fontWeight: 500,
    borderRadius: 4,
    border: '1px solid #7f1d1d',
    background: '#991b1b',
    color: '#fff',
    cursor: 'pointer',
  },
  sep: {
    width: 1,
    height: 20,
    background: '#2a2d3a',
    margin: '0 4px',
  },
}

export default function Header({
  backendOnline,
  loading,
  previewActive,
  onValidate,
  onPreview,
  onExport,
  onExportJson,
  onResetExample,
}: HeaderProps) {
  return (
    <div style={s.header}>
      <div style={s.logo}>
        <span style={{ color: '#3b82f6', fontSize: 16 }}>O</span> Parametric CAD
      </div>
      <div style={s.status}>
        <span
          style={{
            ...s.dot,
            background: backendOnline ? '#22c55e' : '#ef4444',
            boxShadow: backendOnline ? '0 0 4px #22c55e' : undefined,
          }}
        />
        {backendOnline ? 'Backend online' : 'Backend offline'}
      </div>
      <button style={s.btn} onClick={onValidate} disabled={loading}>
        Validate
      </button>
      <div style={s.sep} />
      <button
        style={previewActive ? s.btnPrimary : s.btn}
        onClick={onPreview}
        disabled={loading}
      >
        {loading ? 'Building...' : 'Preview'}
      </button>
      <span style={{ ...s.btn, background: 'transparent', border: 'none', color: '#6b7280', fontSize: 11 }}>
        EXPORT
      </span>
      {(['step', 'stl', '3mf'] as const).map((fmt) => (
        <button key={fmt} style={s.btn} onClick={() => onExport(fmt)} disabled={loading}>
          {fmt.toUpperCase()}
        </button>
      ))}
      <button style={s.btn} onClick={onExportJson} disabled={loading}>
        JSON
      </button>
      <div style={s.sep} />
      <button style={s.btnDanger} onClick={onResetExample}>
        Reset Example
      </button>
    </div>
  )
}
