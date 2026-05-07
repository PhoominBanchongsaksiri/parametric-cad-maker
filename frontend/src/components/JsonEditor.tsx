import { useState, useEffect } from 'react'
import { useProjectStore } from '../state/projectStore'
import type { Project } from '../types/project'

export function JsonEditor() {
  const { project, setProject } = useProjectStore()
  const [text, setText] = useState(() => JSON.stringify(project, null, 2))
  const [err, setErr] = useState<string | null>(null)

  // Sync when project changes externally (e.g. param edits)
  useEffect(() => {
    setText(JSON.stringify(project, null, 2))
    setErr(null)
  }, [project])

  function apply() {
    try {
      const parsed: Project = JSON.parse(text)
      setProject(parsed)
      setErr(null)
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Invalid JSON')
    }
  }

  return (
    <>
      <div className="section-label">Project JSON</div>
      <textarea
        className="json-textarea"
        value={text}
        onChange={(e) => { setText(e.target.value); setErr(null) }}
        spellCheck={false}
        rows={16}
      />
      {err && <div className="json-err">⚠ {err}</div>}
      <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
        <button className="btn-primary btn-sm" onClick={apply}>Apply JSON</button>
      </div>
    </>
  )
}
