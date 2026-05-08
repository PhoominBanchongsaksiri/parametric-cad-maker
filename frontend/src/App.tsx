import { useState, useEffect, useRef, CSSProperties } from 'react'
import type { Project } from './types/project'
import { EXAMPLE_PROJECT } from './types/project'
import { ApiError, checkHealth, postPreview, postValidate, postExport, downloadBlob } from './api/client'
import Header from './components/Header'
import FeatureTree from './components/FeatureTree'
import Viewport from './components/Viewport'
import PropertiesPanel from './components/PropertiesPanel'

const layout: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  height: '100vh',
  width: '100vw',
  background: '#0c0e14',
  color: '#e0e0e0',
  fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif",
  overflow: 'hidden',
}

const body: CSSProperties = {
  display: 'flex',
  flex: 1,
  overflow: 'hidden',
}

export default function App() {
  const [project, setProject] = useState<Project>(EXAMPLE_PROJECT)
  const [glbUrl, setGlbUrl] = useState<string | null>(null)
  const [errors, setErrors] = useState<string[]>([])
  const [warnings, setWarnings] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [backendOnline, setBackendOnline] = useState(false)
  const [validationResult, setValidationResult] = useState<{
    valid: boolean
    errors: string[]
    warnings: string[]
  } | null>(null)

  const prevGlbUrl = useRef<string | null>(null)

  useEffect(() => {
    checkHealth().then(setBackendOnline)
    const interval = setInterval(() => checkHealth().then(setBackendOnline), 10_000)
    return () => clearInterval(interval)
  }, [])

  async function handlePreview() {
    setLoading(true)
    setErrors([])
    setWarnings([])
    try {
      const blob = await postPreview(project)
      if (prevGlbUrl.current) URL.revokeObjectURL(prevGlbUrl.current)
      const url = URL.createObjectURL(blob)
      prevGlbUrl.current = url
      setGlbUrl(url)
    } catch (e) {
      if (e instanceof ApiError) {
        setErrors(e.errors)
        setWarnings(e.warnings)
      } else {
        setErrors([String(e)])
      }
      setGlbUrl(null)
    } finally {
      setLoading(false)
    }
  }

  async function handleValidate() {
    setLoading(true)
    try {
      const result = await postValidate(project)
      setValidationResult(result)
    } catch (e) {
      if (e instanceof ApiError) {
        setValidationResult({ valid: false, errors: e.errors, warnings: e.warnings })
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleExport(fmt: 'step' | 'stl' | '3mf') {
    setLoading(true)
    try {
      const blob = await postExport(project, fmt)
      downloadBlob(blob, `${project.name}.${fmt}`)
    } catch (e) {
      if (e instanceof ApiError) {
        setErrors(e.errors)
      } else {
        setErrors([String(e)])
      }
    } finally {
      setLoading(false)
    }
  }

  function handleExportJson() {
    const blob = new Blob([JSON.stringify(project, null, 2)], { type: 'application/json' })
    downloadBlob(blob, `${project.name}.json`)
  }

  function handleResetExample() {
    setProject(EXAMPLE_PROJECT)
    setGlbUrl(null)
    setErrors([])
    setWarnings([])
    setValidationResult(null)
  }

  function handleProjectChange(p: Project) {
    setProject(p)
    setErrors([])
    setWarnings([])
  }

  return (
    <div style={layout}>
      <Header
        backendOnline={backendOnline}
        loading={loading}
        previewActive={glbUrl !== null}
        onValidate={handleValidate}
        onPreview={handlePreview}
        onExport={handleExport}
        onExportJson={handleExportJson}
        onResetExample={handleResetExample}
      />
      <div style={body}>
        <FeatureTree project={project} />
        <Viewport
          glbUrl={glbUrl}
          errors={errors}
          warnings={warnings}
          onRegenerate={handlePreview}
          loading={loading}
        />
        <PropertiesPanel
          project={project}
          onProjectChange={handleProjectChange}
          validationResult={validationResult}
        />
      </div>
    </div>
  )
}
