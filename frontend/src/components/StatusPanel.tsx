import { useEffect } from 'react'
import { useProjectStore } from '../state/projectStore'
import { apiHealth, apiValidate } from '../api/client'

export function StatusPanel() {
  const { backendOk, setBackendOk, project, validation, setValidation } = useProjectStore()

  useEffect(() => {
    let alive = true
    async function poll() {
      const ok = await apiHealth()
      if (alive) setBackendOk(ok)
    }
    poll()
    const t = setInterval(poll, 5000)
    return () => { alive = false; clearInterval(t) }
  }, [setBackendOk])

  async function validate() {
    try {
      const v = await apiValidate(project)
      setValidation(v)
    } catch (e: unknown) {
      setValidation({ valid: false, errors: [e instanceof Error ? e.message : String(e)], warnings: [] })
    }
  }

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <div className={`status-dot ${backendOk ? 'ok' : 'err'}`} />
        <span style={{ fontSize: 11, color: 'var(--text2)' }}>
          Backend {backendOk ? 'online' : 'offline'}
        </span>
        <button className="btn-secondary btn-sm" onClick={validate} style={{ marginLeft: 4 }}>
          Validate
        </button>
      </div>

      {validation && (
        <div className="val-section">
          {validation.errors.map((e, i) => (
            <div key={i} className="val-item val-err">⛔ {e}</div>
          ))}
          {validation.warnings.map((w, i) => (
            <div key={i} className="val-item val-warn">⚠ {w}</div>
          ))}
          {validation.valid && validation.warnings.length === 0 && (
            <div className="val-item" style={{ borderColor: 'var(--accent2)', color: 'var(--accent2)', background: '#0f1e14' }}>
              ✓ Valid — no errors or warnings
            </div>
          )}
        </div>
      )}
    </>
  )
}
