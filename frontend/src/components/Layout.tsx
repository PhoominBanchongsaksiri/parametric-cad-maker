import { useProjectStore } from '../state/projectStore'
import { FeatureTree } from './FeatureTree'
import { Viewport3D } from './Viewport3D'
import { ParameterPanel } from './ParameterPanel'
import { JsonEditor } from './JsonEditor'
import { ExportPanel } from './ExportPanel'
import { StatusPanel } from './StatusPanel'
import { apiPreview } from '../api/client'

function Toolbar() {
  const { project, setGlbUrl, setPreviewLoading, setPreviewError, resetToExample } = useProjectStore()

  async function regenerate() {
    setPreviewLoading(true)
    setPreviewError(null)
    setGlbUrl(null)
    try {
      const blob = await apiPreview(project)
      const ext = blob.type.includes('gltf') ? '' : '#stl'
      setGlbUrl(URL.createObjectURL(blob) + ext)
    } catch (e: unknown) {
      setPreviewError(e instanceof Error ? e.message : String(e))
    } finally {
      setPreviewLoading(false)
    }
  }

  return (
    <div className="toolbar">
      <span className="toolbar-title">⬡ Parametric CAD</span>
      <StatusPanel />
      <div style={{ flex: 1 }} />
      <button className="btn-primary btn-sm" onClick={regenerate}>↺ Preview</button>
      <ExportPanel />
      <button className="btn-danger btn-sm" onClick={resetToExample}>Reset Example</button>
    </div>
  )
}

export function Layout() {
  return (
    <div className="app">
      <Toolbar />
      <div className="main-area">
        <div className="panel">
          <FeatureTree />
        </div>

        <Viewport3D />

        <div className="panel right">
          <div className="panel-header">Properties &amp; JSON</div>
          <div className="panel-body">
            <ParameterPanel />
            <hr className="divider" />
            <JsonEditor />
          </div>
        </div>
      </div>
    </div>
  )
}
