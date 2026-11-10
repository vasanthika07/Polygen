import React, { Suspense, useState, useRef, useEffect, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Center, useGLTF, Environment } from '@react-three/drei';
import * as THREE from 'three';
import { useStore } from '../store/useStore';
import { 
  RotateCw, 
  Maximize2, 
  Download, 
  Layers, 
  Box, 
  Activity, 
  Sparkles,
  RefreshCw
} from 'lucide-react';

interface ModelProps {
  url: string;
  renderMode: 'textured' | 'wireframe' | 'solid';
  onStatsCalculated: (stats: { vertices: number; triangles: number; dimensions: [number, number, number] }) => void;
}

const Model: React.FC<ModelProps> = ({ url, renderMode, onStatsCalculated }) => {
  const { scene } = useGLTF(url);
  const clonedScene = useMemo(() => scene.clone(true), [scene]);

  useEffect(() => {
    let vertices = 0;
    let triangles = 0;

    const box = new THREE.Box3().setFromObject(clonedScene);
    const size = new THREE.Vector3();
    box.getSize(size);

    clonedScene.traverse((child) => {
      if ((child as THREE.Mesh).isMesh) {
        const mesh = child as THREE.Mesh;
        const geom = mesh.geometry;
        if (geom) {
          if (geom.index) {
            triangles += geom.index.count / 3;
          } else if (geom.attributes.position) {
            triangles += geom.attributes.position.count / 3;
          }
          if (geom.attributes.position) {
            vertices += geom.attributes.position.count;
          }
        }

        // Apply render modes
        if (renderMode === 'wireframe') {
          mesh.material = new THREE.MeshBasicMaterial({
            wireframe: true,
            color: 0x38bdf8,
          });
        } else if (renderMode === 'solid') {
          mesh.material = new THREE.MeshStandardMaterial({
            color: 0x94a3b8,
            roughness: 0.4,
            metalness: 0.1,
          });
        }
      }
    });

    onStatsCalculated({
      vertices: Math.round(vertices),
      triangles: Math.round(triangles),
      dimensions: [
        parseFloat(size.x.toFixed(2)),
        parseFloat(size.y.toFixed(2)),
        parseFloat(size.z.toFixed(2)),
      ],
    });
  }, [clonedScene, renderMode, onStatsCalculated]);

  return (
    <Center>
      <primitive object={clonedScene} />
    </Center>
  );
};

export const ModelViewer: React.FC = () => {
  const { activeAsset, renderMode, setRenderMode, autoRotate, setAutoRotate } = useStore();
  const [stats, setStats] = useState<{
    vertices: number;
    triangles: number;
    dimensions: [number, number, number];
  }>({
    vertices: 0,
    triangles: 0,
    dimensions: [0, 0, 0],
  });
  const [, setIsFullscreen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const controlsRef = useRef<any>(null);

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const resetCamera = () => {
    if (controlsRef.current) {
      controlsRef.current.reset();
    }
  };

  return (
    <div
      ref={containerRef}
      className="relative w-full h-[540px] lg:h-[620px] bg-gradient-to-b from-slate-950 via-slate-900 to-[#070a13] rounded-2xl border border-slate-800 overflow-hidden shadow-2xl flex flex-col"
    >
      {/* Viewport Header Controls */}
      <div className="absolute top-4 left-4 right-4 z-20 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
        {/* Left: Render Mode Toggles */}
        <div className="flex items-center gap-1.5 p-1.5 bg-slate-900/90 backdrop-blur-md rounded-xl border border-slate-800/80 shadow-lg pointer-events-auto">
          <button
            onClick={() => setRenderMode('textured')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              renderMode === 'textured'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
            title="Textured PBR Render"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>PBR Texture</span>
          </button>

          <button
            onClick={() => setRenderMode('solid')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              renderMode === 'solid'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
            title="Clay / Solid Render"
          >
            <Box className="w-3.5 h-3.5" />
            <span>Clay Solid</span>
          </button>

          <button
            onClick={() => setRenderMode('wireframe')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              renderMode === 'wireframe'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
            title="Topology Wireframe"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Wireframe</span>
          </button>
        </div>

        {/* Right: Camera & Viewport Tools */}
        <div className="flex items-center gap-2 pointer-events-auto">
          <button
            onClick={() => setAutoRotate(!autoRotate)}
            className={`p-2 rounded-xl backdrop-blur-md border transition-all ${
              autoRotate
                ? 'bg-blue-600 border-blue-500 text-white shadow-lg shadow-blue-500/30'
                : 'bg-slate-900/90 border-slate-800 text-slate-300 hover:bg-slate-800'
            }`}
            title="Toggle Auto Rotation"
          >
            <RotateCw className={`w-4 h-4 ${autoRotate ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={resetCamera}
            className="p-2 rounded-xl bg-slate-900/90 backdrop-blur-md border border-slate-800 text-slate-300 hover:bg-slate-800 transition-all"
            title="Reset View"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <button
            onClick={toggleFullscreen}
            className="p-2 rounded-xl bg-slate-900/90 backdrop-blur-md border border-slate-800 text-slate-300 hover:bg-slate-800 transition-all"
            title="Toggle Fullscreen"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main 3D Canvas Viewport */}
      <div className="flex-1 w-full h-full relative cursor-grab active:cursor-grabbing">
        {activeAsset ? (
          <Canvas
            camera={{ position: [0, 1.5, 3.5], fov: 45 }}
            gl={{ antialias: true, alpha: true, toneMapping: THREE.ACESFilmicToneMapping }}
          >
            <ambientLight intensity={0.7} />
            <directionalLight position={[5, 8, 5]} intensity={1.4} castShadow />
            <directionalLight position={[-5, -2, -5]} intensity={0.4} />
            <pointLight position={[0, 4, 2]} intensity={0.8} />

            <Suspense
              fallback={
                <mesh>
                  <boxGeometry args={[0.5, 0.5, 0.5]} />
                  <meshStandardMaterial wireframe color="#38bdf8" />
                </mesh>
              }
            >
              <Model
                url={activeAsset.glb_url}
                renderMode={renderMode}
                onStatsCalculated={setStats}
              />
              <Environment preset="city" />
            </Suspense>

            <OrbitControls
              ref={controlsRef}
              autoRotate={autoRotate}
              autoRotateSpeed={2.0}
              enableDamping
              dampingFactor={0.05}
              minDistance={0.5}
              maxDistance={12}
            />
          </Canvas>
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center text-center p-8">
            <div className="w-20 h-20 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-4 animate-pulse">
              <Box className="w-10 h-10" />
            </div>
            <h3 className="text-xl font-semibold text-slate-200 mb-2">No Model Selected</h3>
            <p className="text-sm text-slate-400 max-w-md">
              Enter a prompt on the left and click <span className="text-blue-400 font-medium">Generate 3D Model</span> or select an asset from your library to inspect it in full 3D.
            </p>
          </div>
        )}
      </div>

      {/* Viewport Footer: Geometry Telemetry & Quick Download */}
      {activeAsset && (
        <div className="absolute bottom-4 left-4 right-4 z-20 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
          {/* Real Geometry Statistics Card */}
          <div className="flex items-center gap-4 px-4 py-2.5 bg-slate-900/90 backdrop-blur-md rounded-xl border border-slate-800/80 shadow-xl pointer-events-auto text-xs text-slate-300">
            <div className="flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-blue-400" />
              <span className="text-slate-400">Polygons:</span>
              <span className="font-semibold text-slate-100">
                {(stats.triangles || activeAsset.polygon_count).toLocaleString()}
              </span>
            </div>

            <div className="w-px h-3.5 bg-slate-800" />

            <div className="flex items-center gap-1.5">
              <span className="text-slate-400">Vertices:</span>
              <span className="font-semibold text-slate-100">
                {stats.vertices.toLocaleString()}
              </span>
            </div>

            <div className="w-px h-3.5 bg-slate-800" />

            <div className="flex items-center gap-1.5">
              <span className="text-slate-400">Size:</span>
              <span className="font-semibold text-slate-100">
                {(activeAsset.file_size / (1024 * 1024)).toFixed(2)} MB
              </span>
            </div>

            <div className="w-px h-3.5 bg-slate-800" />

            <div className="hidden sm:flex items-center gap-1.5">
              <span className="text-slate-400">Bounds (m):</span>
              <span className="font-semibold text-slate-100">
                {stats.dimensions.join(' × ')}
              </span>
            </div>
          </div>

          {/* Download Action */}
          <a
            href={activeAsset.glb_url}
            download
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-blue-500/25 pointer-events-auto transition-all active:scale-95"
          >
            <Download className="w-4 h-4" />
            <span>Download GLB (Unity / Unreal / Blender)</span>
          </a>
        </div>
      )}
    </div>
  );
};
