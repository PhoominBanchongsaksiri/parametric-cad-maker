import { Suspense, useEffect, useRef } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Grid, GizmoHelper, GizmoViewport, useGLTF } from '@react-three/drei'
import { useProjectStore } from '../state/projectStore'
import { apiPreview } from '../api/client'
import * as THREE from 'three'

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

function StlFallbackModel({ url }: { url: string }) {
  const meshRef = useRef<THREE.Mesh>(null)
  useEffect(() => {
    import('three/addons/loaders/STLLoader.js').then(({ STLLoader }) => {
      const loader = new STLLoader()
      fetch(url)
        .then((r) => r.arrayBuffer())
        .then((buf) => {
          const geo = loader.parse(buf)
          geo.computeVertexNormals()
          if (meshRef.current) {
            meshRef.current.geometry = geo
          }
        })
    })
  }, [url])
  return (
    <mesh ref={meshRef}>
      <meshStandardMaterial color="#4f8ef7" metalness={0.25} roughness={0.6} />
    </mesh>
  )
}

function ModelLoader({ url, isStl }: { url: string; isStl: boolean }) {
  if (isStl) return <StlFallbackModel url={url} />
  return (
    <Suspense fallback={null}>
      <GlbModel url={url} />
    </Suspense>
  )
}

export function Viewport3D() {
  const { glbUrl, previewLoading, previewError, project, setGlbUrl, setPreviewLoading, setPreviewError } =
    useProjectStore()

  const isStl = glbUrl?.includes('stl') ?? false

  async function regenerate() {
    setPreviewLoading(true)
    setPreviewError(null)
    if (glbUrl) URL.revokeObjectURL(glbUrl)
    setGlbUrl(null)
    try {
      const blob = await apiPreview(project)
      const contentType = blob.type
      const ext = contentType.includes('gltf') ? 'glb' : 'stl'
      const url = URL.createObjectURL(new Blob([blob], { type: contentType }))
      // append ext hint so ModelLoader can branch
      setGlbUrl(url + (ext === 'stl' ? '#stl' : ''))
    } catch (e: unknown) {
      setPreviewError(e instanceof Error ? e.message : String(e))
    } finally {
      setPreviewLoading(false)
    }
  }

  // Auto-load on first mount
  useEffect(() => {
    regenerate()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const showOverlay = previewLoading || previewError || !glbUrl

  return (
    <div className="viewport-wrap">
      {showOverlay && (
        <div className="viewport-overlay">
          <div className={`viewport-msg ${previewError ? 'err' : ''}`}>
            {previewLoading && (
              <>
                <div className="spinner" />
                Generating preview…
              </>
            )}
            {!previewLoading && previewError && previewError}
            {!previewLoading && !previewError && !glbUrl && 'Click Regenerate to load preview'}
          </div>
        </div>
      )}

      <Canvas
        camera={{ position: [150, 120, 150], fov: 45 }}
        gl={{ antialias: true }}
        style={{ background: '#0d0f12' }}
      >
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
          <ModelLoader url={glbUrl.replace('#stl', '')} isStl={glbUrl.includes('#stl')} />
        )}

        <OrbitControls makeDefault />
        <GizmoHelper alignment="bottom-right" margin={[60, 60]}>
          <GizmoViewport labelColor="white" axisHeadScale={1} />
        </GizmoHelper>
      </Canvas>

      <div style={{ position: 'absolute', bottom: 10, right: 10 }}>
        <button className="btn-primary" onClick={regenerate} disabled={previewLoading}>
          {previewLoading ? 'Generating…' : '↺ Regenerate Preview'}
        </button>
      </div>
    </div>
  )
}
