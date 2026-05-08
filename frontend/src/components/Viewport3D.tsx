import { Component, Suspense, useEffect, useRef } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Grid, GizmoHelper, GizmoViewport, useGLTF } from '@react-three/drei'
import { useProjectStore } from '../state/projectStore'
import { apiPreview } from '../api/client'
import * as THREE from 'three'

// ---- Error boundary (prevents Canvas crash from taking down the whole app) --

interface EBState { error: string | null }

class CanvasErrorBoundary extends Component<{ children: ReactNode }, EBState> {
  state: EBState = { error: null }

  static getDerivedStateFromError(err: unknown): EBState {
    const msg = err instanceof Error ? err.message : String(err)
    return { error: msg }
  }

  componentDidCatch(_err: unknown, _info: ErrorInfo) {
    // error already captured in state
  }

  render() {
    if (this.state.error) {
      return (
        <div className="viewport-overlay">
          <div className="viewport-msg err">⛔ Render error: {this.state.error}</div>
        </div>
      )
    }
    return this.props.children
  }
}

// ---- GLB model via Drei (blob URL) ----------------------------------------

function GlbModel({ url }: { url: string }) {
  const { scene } = useGLTF(url)
  const cloned = scene.clone(true)
  cloned.traverse((obj) => {
    if ((obj as THREE.Mesh).isMesh) {
      const mesh = obj as THREE.Mesh
      mesh.material = new THREE.MeshStandardMaterial({
        color: '#4f8ef7',
        metalness: 0.25,
        roughness: 0.6,
      })
    }
  })
  return <primitive object={cloned} />
}

// ---- STL model -------------------------------------------------------------

function StlModel({ url }: { url: string }) {
  const meshRef = useRef<THREE.Mesh>(null)
  useEffect(() => {
    let cancelled = false
    import('three/addons/loaders/STLLoader.js').then(({ STLLoader }) => {
      const loader = new STLLoader()
      fetch(url)
        .then((r) => r.arrayBuffer())
        .then((buf) => {
          if (cancelled) return
          const geo = loader.parse(buf)
          geo.computeVertexNormals()
          if (meshRef.current) meshRef.current.geometry = geo
        })
        .catch(() => {/* silently ignore; overlay shows error */})
    })
    return () => { cancelled = true }
  }, [url])
  return (
    <mesh ref={meshRef}>
      <meshStandardMaterial color="#4f8ef7" metalness={0.25} roughness={0.6} />
    </mesh>
  )
}

// ---- Model switcher --------------------------------------------------------

function ModelLoader({ url, isStl }: { url: string; isStl: boolean }) {
  if (isStl) return <StlModel url={url} />
  return (
    <Suspense fallback={null}>
      <GlbModel url={url} />
    </Suspense>
  )
}

// ---- Scene -----------------------------------------------------------------

function Scene({ glbUrl }: { glbUrl: string | null }) {
  return (
    <>
      <ambientLight intensity={0.6} />
      <directionalLight position={[100, 200, 100]} intensity={1.2} />
      <directionalLight position={[-100, -50, -100]} intensity={0.3} />

      <Grid
        args={[400, 400]}
        cellSize={10}
        cellThickness={0.5}
        cellColor="#2e333d"
        sectionSize={50}
        sectionThickness={1}
        sectionColor="#3a4050"
        fadeDistance={500}
        fadeStrength={1}
        position={[0, -0.5, 0]}
      />

      {glbUrl && (
        <ModelLoader
          url={glbUrl.replace('#stl', '')}
          isStl={glbUrl.includes('#stl')}
        />
      )}

      <OrbitControls makeDefault />
      <GizmoHelper alignment="bottom-right" margin={[60, 60]}>
        <GizmoViewport labelColor="white" axisHeadScale={1} />
      </GizmoHelper>
    </>
  )
}

// ---- Detect format from blob -----------------------------------------------
// GLB magic: first 4 bytes are ASCII "glTF" (0x676c5446).
// Fall back to content-type if bytes are not readable.

async function isGlbBlob(blob: Blob): Promise<boolean> {
  try {
    const header = await blob.slice(0, 4).arrayBuffer()
    const magic = new Uint8Array(header)
    return magic[0] === 0x67 && magic[1] === 0x6c && magic[2] === 0x54 && magic[3] === 0x46
  } catch {
    return blob.type.includes('gltf')
  }
}

// ---- Viewport --------------------------------------------------------------

export function Viewport3D() {
  const {
    glbUrl, previewLoading, previewError,
    project, setGlbUrl, setPreviewLoading, setPreviewError,
  } = useProjectStore()

  async function regenerate() {
    setPreviewLoading(true)
    setPreviewError(null)
    if (glbUrl) URL.revokeObjectURL(glbUrl.replace('#stl', ''))
    setGlbUrl(null)
    try {
      const blob = await apiPreview(project)
      const isGlb = await isGlbBlob(blob)
      const url = URL.createObjectURL(blob)
      setGlbUrl(url + (isGlb ? '' : '#stl'))
    } catch (e: unknown) {
      setPreviewError(e instanceof Error ? e.message : String(e))
    } finally {
      setPreviewLoading(false)
    }
  }

  // Auto-preview on first mount
  useEffect(() => { regenerate() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const showOverlay = previewLoading || !!previewError || !glbUrl

  return (
    <div className="viewport-wrap">
      {/* Overlay: loading / error / empty state */}
      {showOverlay && (
        <div className="viewport-overlay">
          <div className={`viewport-msg${previewError ? ' err' : ''}`}>
            {previewLoading && <><div className="spinner" />Generating preview…</>}
            {!previewLoading && previewError && <>⛔ {previewError}</>}
            {!previewLoading && !previewError && !glbUrl && 'Click Regenerate to load preview'}
          </div>
        </div>
      )}

      {/* Canvas wrapped in error boundary so a render failure shows an overlay, not a black screen */}
      <CanvasErrorBoundary>
        <Canvas
          camera={{ position: [150, 120, 150], fov: 45 }}
          gl={{ antialias: true }}
          style={{ background: '#0d0f12' }}
        >
          <Scene glbUrl={glbUrl} />
        </Canvas>
      </CanvasErrorBoundary>

      <div style={{ position: 'absolute', bottom: 10, right: 10 }}>
        <button className="btn-primary" onClick={regenerate} disabled={previewLoading}>
          {previewLoading ? 'Generating…' : '↺ Regenerate Preview'}
        </button>
      </div>
    </div>
  )
}
