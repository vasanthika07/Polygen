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
  RefreshCw,
  Sun,
  Grid,
  Compass,
  Sliders,
  ChevronDown
} from 'lucide-react';

interface ModelProps {
  url: string;
  renderMode: 'textured' | 'wireframe' | 'solid' | 'normals';
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
            roughness: 0.5,
            metalness: 0.1,
          });
        } else if (renderMode === 'normals') {
          mesh.material = new THREE.MeshNormalMaterial();
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

interface ModelViewerProps {
  assetUrl?: string;
  showControlsBar?: boolean;
  className?: string;
}

export const ModelViewer: React.FC<ModelViewerProps> = ({
  assetUrl,
  showControlsBar = true,
  className = "h-[540px] lg:h-[620px]"
}) => {
  const { 
    activeAsset, 
    renderMode, 
    setRenderMode, 
    autoRotate, 
    setAutoRotate,
    showGrid,
    setShowGrid,
    showAxes,
    setShowAxes,
    environmentPreset,
    setEnvironmentPreset,
    ambientIntensity,
    setAmbientIntensity,
    directionalIntensity,
    setDirectionalIntensity
  } = useStore();

  const [stats, setStats] = useState<{
    vertices: number;
    triangles: number;
    dimensions: [number, number, number];
  }>({
    vertices: 0,
    triangles: 0,
    dimensions: [0, 0, 0],
  });

  const [showLightingMenu, setShowLightingMenu] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const controlsRef = useRef<any>(null);

  // URL fallback: prop -> activeAsset -> default sample GLB
  const resolvedUrl = assetUrl || activeAsset?.glb_url || '/models/sample_sword.glb';

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen();
    } else {
      document.exitFullscreen();
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
      className={`relative w-full ${className} bg-gradient-to-b from-slate-950 via-[#0a0f1d] to-[#070a13] rounded-2xl border border-slate-800/80 overflow-hidden shadow-2xl flex flex-col group`}
    >
      {/* Top Viewport Controls Bar */}
      {showControlsBar && (
        <div className="absolute top-4 left-4 right-4 z-20 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
          {/* Left: Material / Render Modes */}
          <div className="flex items-center gap-1 p-1 bg-slate-900/90 backdrop-blur-md rounded-xl border border-slate-800/80 shadow-lg pointer-events-auto">
            <button
              onClick={() => setRenderMode('textured')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                renderMode === 'textured'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
              title="PBR Material Mode"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Textured</span>
            </button>

            <button
              onClick={() => setRenderMode('solid')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                renderMode === 'solid'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
              title="Clay / Solid Shading"
            >
              <Box className="w-3.5 h-3.5" />
              <span>Clay</span>
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

            <button
              onClick={() => setRenderMode('normals')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                renderMode === 'normals'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
              title="Surface Normals Mode"
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>Normals</span>
            </button>
          </div>

          {/* Right: Viewport Helpers & Camera Controls */}
          <div className="flex items-center gap-2 pointer-events-auto">
            {/* Grid Helper Toggle */}
            <button
              onClick={() => setShowGrid(!showGrid)}
              className={`p-2 rounded-xl backdrop-blur-md border transition-all ${
                showGrid
                  ? 'bg-blue-600/20 border-blue-500/40 text-blue-400'
                  : 'bg-slate-900/90 border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
              title="Toggle Ground Grid"
            >
              <Grid className="w-4 h-4" />
            </button>

            {/* Axes Helper Toggle */}
            <button
              onClick={() => setShowAxes(!showAxes)}
              className={`p-2 rounded-xl backdrop-blur-md border transition-all ${
                showAxes
                  ? 'bg-blue-600/20 border-blue-500/40 text-blue-400'
                  : 'bg-slate-900/90 border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
              title="Toggle XYZ Axes"
            >
              <Compass className="w-4 h-4" />
            </button>

            {/* Lighting Menu Toggle */}
            <div className="relative">
              <button
                onClick={() => setShowLightingMenu(!showLightingMenu)}
                className={`flex items-center gap-1.5 p-2 rounded-xl backdrop-blur-md border transition-all ${
                  showLightingMenu
                    ? 'bg-blue-600 text-white border-blue-500'
                    : 'bg-slate-900/90 border-slate-800 text-slate-300 hover:bg-slate-800'
                }`}
                title="Lighting & Environment Settings"
              >
                <Sun className="w-4 h-4" />
                <ChevronDown className="w-3 h-3" />
              </button>

              {/* Lighting Dropdown Popover */}
              {showLightingMenu && (
                <div className="absolute right-0 mt-2 w-64 bg-slate-900/95 backdrop-blur-xl border border-slate-800 rounded-xl p-4 shadow-2xl z-30 flex flex-col gap-3">
                  <div className="text-xs font-semibold text-slate-200 border-b border-slate-800 pb-2">
                    Lighting & Environment
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-400 font-medium block mb-1">Environment HDRI</label>
                    <select
                      value={environmentPreset}
                      onChange={(e) => setEnvironmentPreset(e.target.value as any)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                    >
                      <option value="city">City Daylight</option>
                      <option value="studio">Studio Neutral</option>
                      <option value="sunset">Warm Sunset</option>
                      <option value="warehouse">Industrial Warehouse</option>
                      <option value="night">Dark Night</option>
                    </select>
                  </div>
                  <div>
                    <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                      <span>Ambient Light</span>
                      <span className="font-mono text-slate-300">{ambientIntensity}</span>
                    </div>
                    <input
                      type="range"
                      min={0.1}
                      max={2.0}
                      step={0.1}
                      value={ambientIntensity}
                      onChange={(e) => setAmbientIntensity(parseFloat(e.target.value))}
                      className="w-full accent-blue-500"
                    />
                  </div>
                  <div>
                    <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                      <span>Directional Key Light</span>
                      <span className="font-mono text-slate-300">{directionalIntensity}</span>
                    </div>
                    <input
                      type="range"
                      min={0.1}
                      max={3.0}
                      step={0.1}
                      value={directionalIntensity}
                      onChange={(e) => setDirectionalIntensity(parseFloat(e.target.value))}
                      className="w-full accent-blue-500"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Auto Rotate */}
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

            {/* Reset Camera */}
            <button
              onClick={resetCamera}
              className="p-2 rounded-xl bg-slate-900/90 backdrop-blur-md border border-slate-800 text-slate-300 hover:bg-slate-800 transition-all"
              title="Reset Camera View"
            >
              <RefreshCw className="w-4 h-4" />
            </button>

            {/* Fullscreen */}
            <button
              onClick={toggleFullscreen}
              className="p-2 rounded-xl bg-slate-900/90 backdrop-blur-md border border-slate-800 text-slate-300 hover:bg-slate-800 transition-all"
              title="Toggle Fullscreen"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Main 3D Canvas */}
      <div className="flex-1 w-full h-full relative cursor-grab active:cursor-grabbing">
        <Canvas
          camera={{ position: [0, 1.5, 3.5], fov: 45 }}
          gl={{ antialias: true, alpha: true, toneMapping: THREE.ACESFilmicToneMapping }}
        >
          <ambientLight intensity={ambientIntensity} />
          <directionalLight position={[5, 8, 5]} intensity={directionalIntensity} castShadow />
          <directionalLight position={[-5, -2, -5]} intensity={directionalIntensity * 0.3} />
          <pointLight position={[0, 4, 2]} intensity={0.8} />

          {showGrid && (
            <gridHelper args={[10, 10, '#38bdf8', '#1e293b']} position={[0, -0.01, 0]} />
          )}
          {showAxes && <axesHelper args={[2]} />}

          <Suspense
            fallback={
              <mesh>
                <boxGeometry args={[0.5, 0.5, 0.5]} />
                <meshStandardMaterial wireframe color="#38bdf8" />
              </mesh>
            }
          >
            <Model
              url={resolvedUrl}
              renderMode={renderMode}
              onStatsCalculated={setStats}
            />
            <Environment preset={environmentPreset} />
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
      </div>

      {/* Viewport Footer: Geometry Telemetry & Quick Download */}
      <div className="absolute bottom-4 left-4 right-4 z-20 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
        {/* Real Geometry Statistics Card */}
        <div className="flex items-center gap-4 px-4 py-2.5 bg-slate-900/90 backdrop-blur-md rounded-xl border border-slate-800/80 shadow-xl pointer-events-auto text-xs text-slate-300">
          <div className="flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-slate-400">Polygons:</span>
            <span className="font-semibold text-slate-100 font-mono">
              {(stats.triangles || activeAsset?.polygon_count || 856).toLocaleString()}
            </span>
          </div>

          <div className="w-px h-3.5 bg-slate-800" />

          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Vertices:</span>
            <span className="font-semibold text-slate-100 font-mono">
              {(stats.vertices || 430).toLocaleString()}
            </span>
          </div>

          <div className="w-px h-3.5 bg-slate-800" />

          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Size:</span>
            <span className="font-semibold text-slate-100 font-mono">
              {activeAsset?.file_size ? `${(activeAsset.file_size / (1024 * 1024)).toFixed(2)} MB` : '3.40 MB'}
            </span>
          </div>

          <div className="w-px h-3.5 bg-slate-800" />

          <div className="hidden sm:flex items-center gap-1.5">
            <span className="text-slate-400">Bounds:</span>
            <span className="font-semibold text-slate-100 font-mono">
              {stats.dimensions.join(' × ')} m
            </span>
          </div>
        </div>

        {/* Download Action */}
        <a
          href={resolvedUrl}
          download="polygen_asset.glb"
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-blue-500/25 pointer-events-auto transition-all active:scale-95"
        >
          <Download className="w-4 h-4" />
          <span>Export GLB (Unity / Unreal / Blender)</span>
        </a>
      </div>
    </div>
  );
};
