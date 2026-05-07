import { useState } from 'react'
import { useProjectStore } from '../state/projectStore'
import { apiExport, downloadBlob } from '../api/client'

export function ExportPanel() {
  const { project } = useProjectStore()
  const [busy, setBusy] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)

  async function doExport(fmt: 'step' | 'stl' | '3mf') {
    setBusy(fmt)
    setErr(null)
    try {
      const blob = await apiExport(project, fmt)
      downloadBlob(blob, `${project.name}.${fmt}`)
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(null)
    }
  }

  function exportJson() {
    const blob = new Blob([JSON.stringify(project, null, 2)], { type: 'application/json' })
    downloadBlob(blob, `${project.name}.json`)
  }

  return (
    <>
      <div className="section-label">Export</div>
      <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
        <button className="btn-secondary btn-sm" onClick={() => doExport('step')} disabled={!!busy}>
          {busy === 'step' ? '…' : 'STEP'}
        </button>
        <button className="btn-secondary btn-sm" onClick={() => doExport('stl')} disabled={!!busy}>
          {busy === 'stl' ? '…' : 'STL'}
        </button>
        <button className="btn-secondary btn-sm" onClick={() => doExport('3mf')} disabled={!!busy}>
          {busy === '3mf' ? '…' : '3MF'}
        </button>
        <button className="btn-secondary btn-sm" onClick={exportJson}>JSON</button>
      </div>
      {err && <div className="json-err" style={{ marginTop: 4 }}>⚠ {err}</div>}
    </>
  )
}
