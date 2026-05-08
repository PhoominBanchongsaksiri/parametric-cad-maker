import { Suspense, useEffect, useState, CSSProperties, Component, ErrorInfo, ReactNode } from 'react'
import { Canvas, useLoader, useThree } from '@react-three/fiber'
import { OrbitControls, Grid, GizmoHelper, GizmoViewport } from '@react-three/drei'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
import * as THREE from 'three'

interface ViewportProps {
  glbUrl: string | null
  modelType: 'glb' | 'stl' | null
  errors: string[]
  warnings: string[]
  onRegenerate: () => void
  loading: boolean
}

// ---------------------------------------------------------------------------
// Model loaders
// ---------------------------------------------------------------------------

function GltfModel({ url }: { url: string }) {
  const gltf = useLoader(GLTFLoader, url)
  const { camera } = useThree()

  useEffect(() => {
    const box = new THREE.Box3().setFromObject(gltf.scene)
    const size = box.getSize(new THREE.Vector3())
    const center = box.getCenter(new THREE.Vector3())
    const maxDim = Math.max(size.x, size.y, size.z)
    if (camera instanceof THREE.PerspectiveCamera) {
      camera.position.set(center.x + maxDim * 1.5, center.y + maxDim * 1.2, center.z + maxDim * 1.5)
      camera.lookAt(center)
      camera.near = maxDim * 0.01
      camera.far = maxDim * 100
      camera.updateProjectionMatrix()
    }
  }, [gltf, camera])

  return <primitive object={gltf.scene} />
}

function StlModel({ url }: { url: string }) {
  const geometry = useLoader(STLLoader, url)
  const { camera } = useThree()

  useEffect(() => {
    geometry.computeBoundingBox()
    const box = geometry.boundingBox
    if (!box) return
    const size = new THREE.Vector3()
    box.getSize(size)
    const center = new THREE.Vector3()
    box.getCenter(center)
    const maxDim = Math.max(size.x, size.y, size.z)
    if (camera instanceof THREE.PerspectiveCamera) {
      camera.position.set(center.x + maxDim * 1.5, center.y + maxDim * 1.2, center.z + maxDim * 1.5)
      camera.lookAt(center)
      camera.near = maxDim * 0.01
      camera.far = maxDim * 100
      camera.updateProjectionMatrix()
    }
  }, [geometry, camera])

  return (
    <mesh geometry={geometry}>
      <meshStandardMaterial color="#5588cc" side={THREE.DoubleSide} />
    </mesh>
  )
}

// ---------------------------------------------------------------------------
// Error boundaries
// ---------------------------------------------------------------------------

// Catches errors from the model loader inside Canvas — renders nothing on
// failure so the Canvas/grid/controls stay intact.
class ModelErrorBoundary extends Component<
  { children: ReactNode; onError: (msg: string) => void },
  { hasError: boolean }
> {
  state = { hasError: false }

  static getDerivedStateFromError(): { hasError: boolean } {
    return { hasError: true }
  }

  componentDidCatch(error: Error, _info: ErrorInfo) {
    this.props.onError(error.message.slice(0, 400))
  }

  render() {
    return this.state.hasError ? null : this.props.children
  }
}

// Outer guard: if Canvas itself throws (very rare), show an inline error
// box instead of letting the crash propagate up and white-screen the page.
class CanvasErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean; message: string }
> {
  state = { hasError: false, message: '' }

  static getDerivedStateFromError(error: Error): { hasError: boolean; message: string } {
    return { hasError: true, message: error.message.slice(0, 400) }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0c0e14', color: '#fca5a5', padding: 24, fontSize: 13 }}>
          3D renderer error: {this.state.message}
        </div>
      )
    }
    return this.props.children
  }
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const s: Record<string, CSSProperties> = {
  container: {
    flex: 1,
    position: 'relative',
    background: '#0c0e14',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
  },
  errorOverlay: {
    position: 'absolute',
    inset: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
    pointerEvents: 'none',
  },
  errorBox: {
    background: 'rgba(127,29,29,0.9)',
    border: '1px solid #ef4444',
    borderRadius: 6,
    padding: '12px 20px',
    maxWidth: '70%',
    color: '#fca5a5',
    fontSize: 13,
    lineHeight: 1.6,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
  warningBox: {
    position: 'absolute',
    top: 8,
    left: '50%',
    transform: 'translateX(-50%)',
    background: 'rgba(120,53,15,0.9)',
    border: '1px solid #f59e0b',
    borderRadius: 6,
    padding: '6px 16px',
    color: '#fcd34d',
    fontSize: 12,
    zIndex: 10,
    pointerEvents: 'none',
    whiteSpace: 'pre-wrap',
  },
  regenBtn: {
    position: 'absolute',
    bottom: 16,
    left: '50%',
    transform: 'translateX(-50%)',
    padding: '6px 16px',
    background: '#1e2130',
    border: '1px solid #3a3d4a',
    borderRadius: 6,
    color: '#c0c8d8',
    fontSize: 12,
    cursor: 'pointer',
    zIndex: 10,
  },
}

// ---------------------------------------------------------------------------
// Viewport
// ---------------------------------------------------------------------------

export default function Viewport({ glbUrl, modelType, errors, warnings, onRegenerate, loading }: ViewportProps) {
  const [modelLoadError, setModelLoadError] = useState<string | null>(null)

  // Clear loader error whenever the URL changes (new preview attempt or reset).
  useEffect(() => { setModelLoadError(null) }, [glbUrl])

  const allErrors = modelLoadError
    ? [...errors, `3D load error: ${modelLoadError}`]
    : errors

  return (
    <div style={s.container}>
      {allErrors.length > 0 && (
        <div style={s.errorOverlay}>
          <div style={s.errorBox}>{allErrors.join('\n')}</div>
        </div>
      )}
      {warnings.length > 0 && allErrors.length === 0 && (
        <div style={s.warningBox}>{warnings.join('\n')}</div>
      )}

      <CanvasErrorBoundary>
        <Canvas
          camera={{ position: [150, 120, 150], fov: 45, near: 0.1, far: 10000 }}
          style={{ width: '100%', height: '100%' }}
          gl={{ antialias: true }}
        >
          <color attach="background" args={['#0c0e14']} />
          <ambientLight intensity={0.6} />
          <directionalLight position={[100, 200, 100]} intensity={1.2} castShadow />
          <directionalLight position={[-100, -50, -100]} intensity={0.3} />
          <OrbitControls makeDefault />
          <Grid
            args={[500, 500]}
            cellSize={10}
            cellThickness={0.5}
            cellColor="#1e2336"
            sectionSize={50}
            sectionThickness={1}
            sectionColor="#2a3050"
            fadeDistance={400}
            fadeStrength={1}
            infiniteGrid
          />
          <GizmoHelper alignment="bottom-left" margin={[60, 60]}>
            <GizmoViewport axisColors={['#ef4444', '#22c55e', '#3b82f6']} labelColor="white" />
          </GizmoHelper>
          {glbUrl && (
            <ModelErrorBoundary key={glbUrl} onError={setModelLoadError}>
              <Suspense fallback={null}>
                {modelType === 'stl'
                  ? <StlModel url={glbUrl} />
                  : <GltfModel url={glbUrl} />
                }
              </Suspense>
            </ModelErrorBoundary>
          )}
        </Canvas>
      </CanvasErrorBoundary>

      <button style={s.regenBtn} onClick={onRegenerate} disabled={loading}>
        {loading ? 'Building...' : '↺ Regenerate Preview'}
      </button>
    </div>
  )
}
