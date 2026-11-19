import React, { Suspense, useState, useRef, useEffect, useMemo, Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, useGLTF, Environment, useProgress, ContactShadows } from '@react-three/drei';
import * as THREE from 'three';
import { useStore } from '../store/useStore';
import { assetApi } from '../services/api';
import { MaterialPreviewPanel } from './MaterialPreviewPanel';
import { MeshOptimizerPanel } from './MeshOptimizerPanel';
import {
  RotateCw,
  Maximize2,
  Minimize2,
  Download,
  Layers,
  Box,
  Activity,
  Sparkles,
  RefreshCw,
  Grid,
  Compass,
  Sliders,
  ChevronRight,
  ChevronLeft,
  Palette,
  Cpu,
  Camera,
  AlertCircle,
  X,
  SlidersHorizontal,
  Gauge
} from 'lucide-react';

/* -------------------------------------------------------------------------- */
/*                               Type Definitions                             */
/* -------------------------------------------------------------------------- */

export type RenderMode = 'textured' | 'wireframe' | 'solid' | 'normals' | 'unlit';

export interface ModelGeometryStats {
  vertices: number;
  triangles: number;
  meshes: number;
  materials: number;
  dimensions: [number, number, number];
  fileSizeEstimate?: string;
}

interface ModelProps {
  url: string;
  renderMode: RenderMode;
  showBoundingBox: boolean;
  showWireframeOverlay: boolean;
  doubleSided: boolean;
  onStatsCalculated: (stats: ModelGeometryStats) => void;
  onModelLoaded?: () => void;
}

/* -------------------------------------------------------------------------- */
/*                           Error Boundary Component                         */
/* -------------------------------------------------------------------------- */

interface ErrorBoundaryProps {
  children: ReactNode;
  fallbackUrl?: string;
  onRetry: () => void;
  onFallback: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  errorMessage: string;
}

class ViewerErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, errorMessage: '' };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, errorMessage: error.message || 'Failed to load 3D GLB model.' };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ModelViewer ErrorBoundary]', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="absolute inset-0 z-30 flex flex-col items-center justify-center p-6 bg-slate-950/95 backdrop-blur-md text-center">
          <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400 mb-4 shadow-xl shadow-red-500/10">
            <AlertCircle className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-white mb-2">3D Asset Loading Error</h3>
          <p className="text-xs text-slate-400 max-w-md mb-6 leading-relaxed">
            {this.state.errorMessage.length > 180
              ? `${this.state.errorMessage.slice(0, 180)}...`
              : this.state.errorMessage}
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <button
              onClick={() => {
                this.setState({ hasError: false, errorMessage: '' });
                this.props.onRetry();
              }}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-blue-500/25 transition-all flex items-center gap-2"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Load</span>
            </button>
            <button
              onClick={() => {
                this.setState({ hasError: false, errorMessage: '' });
                this.props.onFallback();
              }}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition-all flex items-center gap-2"
            >
              <Box className="w-3.5 h-3.5" />
              <span>Load Sample Broadsword</span>
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

/* -------------------------------------------------------------------------- */
/*                         In-Canvas FPS Tracker Hook                         */
/* -------------------------------------------------------------------------- */

const FpsTracker: React.FC<{ onFpsUpdate: (fps: number) => void }> = ({ onFpsUpdate }) => {
  const frameCount = useRef(0);
  const lastTime = useRef(performance.now());

  useFrame(() => {
    frameCount.current++;
    const now = performance.now();
    if (now - lastTime.current >= 500) {
      const currentFps = Math.round((frameCount.current * 1000) / (now - lastTime.current));
      onFpsUpdate(Math.min(currentFps, 144));
      frameCount.current = 0;
      lastTime.current = now;
    }
  });

  return null;
};

/* -------------------------------------------------------------------------- */
/*                         Camera Controller & Auto-Framer                    */
/* -------------------------------------------------------------------------- */

interface CameraControllerProps {
  fov: number;
}

const CameraController: React.FC<CameraControllerProps> = ({ fov }) => {
  const { camera } = useThree();

  useEffect(() => {
    if ((camera as THREE.PerspectiveCamera).isPerspectiveCamera) {
      const persCamera = camera as THREE.PerspectiveCamera;
      persCamera.fov = fov;
      persCamera.updateProjectionMatrix();
    }
  }, [camera, fov]);

  return null;
};

/* -------------------------------------------------------------------------- */
/*                            Resource Disposal Helper                        */
/* -------------------------------------------------------------------------- */

function disposeThreeObject(object: THREE.Object3D) {
  object.traverse((child) => {
    if ((child as THREE.Mesh).isMesh) {
      const mesh = child as THREE.Mesh;
      if (mesh.geometry) {
        mesh.geometry.dispose();
      }
      if (mesh.material) {
        if (Array.isArray(mesh.material)) {
          mesh.material.forEach(disposeMaterial);
        } else {
          disposeMaterial(mesh.material);
        }
      }
    }
  });
}

function disposeMaterial(mat: THREE.Material) {
  const m = mat as any;
  const textureFields = [
    'map', 'normalMap', 'roughnessMap', 'metalnessMap',
    'aoMap', 'emissiveMap', 'lightMap', 'bumpMap',
    'displacementMap', 'alphaMap', 'envMap'
  ];
  textureFields.forEach((field) => {
    if (m[field] && typeof m[field].dispose === 'function') {
      m[field].dispose();
    }
  });
  mat.dispose();
}

/* -------------------------------------------------------------------------- */
/*                         Real 3D GLB Model Mesh Scene                       */
/* -------------------------------------------------------------------------- */

const ModelMesh: React.FC<ModelProps> = ({
  url,
  renderMode,
  showBoundingBox,
  showWireframeOverlay,
  doubleSided,
  onStatsCalculated,
  onModelLoaded,
}) => {
  const { scene } = useGLTF(url);
  const { pbrSettings } = useStore();

  // Deep clone scene hierarchy so original cached model is preserved
  const clonedScene = useMemo(() => {
    return scene.clone(true);
  }, [scene]);

  // Clean up cloned Three.js memory when this model instance is disposed
  useEffect(() => {
    return () => {
      disposeThreeObject(clonedScene);
    };
  }, [clonedScene]);

  // Compute exact bounding dimensions, center, and geometry statistics
  const { bounds, boxHelper } = useMemo(() => {
    const box = new THREE.Box3().setFromObject(clonedScene);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);

    // Compute stats
    let totalVertices = 0;
    let totalTriangles = 0;
    let meshCount = 0;
    const materialSet = new Set<string>();

    clonedScene.traverse((child) => {
      if ((child as THREE.Mesh).isMesh) {
        meshCount++;
        const mesh = child as THREE.Mesh;
        mesh.castShadow = true;
        mesh.receiveShadow = true;

        const geom = mesh.geometry;
        if (geom) {
          if (geom.index) {
            totalTriangles += geom.index.count / 3;
          } else if (geom.attributes.position) {
            totalTriangles += geom.attributes.position.count / 3;
          }
          if (geom.attributes.position) {
            totalVertices += geom.attributes.position.count;
          }
        }

        if (mesh.material) {
          if (Array.isArray(mesh.material)) {
            mesh.material.forEach((m) => materialSet.add(m.uuid));
          } else {
            materialSet.add(mesh.material.uuid);
          }
        }
      }
    });

    onStatsCalculated({
      vertices: Math.round(totalVertices),
      triangles: Math.round(totalTriangles),
      meshes: meshCount,
      materials: Math.max(materialSet.size, 1),
      dimensions: [
        parseFloat(size.x.toFixed(2)),
        parseFloat(size.y.toFixed(2)),
        parseFloat(size.z.toFixed(2)),
      ],
    });

    if (onModelLoaded) {
      onModelLoaded();
    }

    // Visual bounding box helper
    const helper = new THREE.Box3Helper(box, new THREE.Color(0x38bdf8));

    return {
      bounds: { size, center, box },
      boxHelper: helper,
    };
  }, [clonedScene, onStatsCalculated, onModelLoaded]);

  // Apply render modes & PBR material tweaks
  useEffect(() => {
    clonedScene.traverse((child) => {
      if ((child as THREE.Mesh).isMesh) {
        const mesh = child as THREE.Mesh;
        const sideMode = doubleSided ? THREE.DoubleSide : THREE.FrontSide;

        if (renderMode === 'wireframe') {
          // Pure wireframe mode
          mesh.material = new THREE.MeshBasicMaterial({
            wireframe: true,
            color: 0x38bdf8,
            side: sideMode,
          });
        } else if (renderMode === 'solid') {
          // Studio Clay mode (Neutral studio sculpture shading)
          mesh.material = new THREE.MeshStandardMaterial({
            color: 0xd4d4d8,
            roughness: 0.65,
            metalness: 0.05,
            side: sideMode,
          });
        } else if (renderMode === 'normals') {
          // Surface Normal vectors mode (RGB Curvature & Tangency)
          mesh.material = new THREE.MeshNormalMaterial({
            side: sideMode,
          });
        } else if (renderMode === 'unlit') {
          // Unlit Base Color (flat diffuse without shading)
          const orig = mesh.material as any;
          mesh.material = new THREE.MeshBasicMaterial({
            map: orig?.map || null,
            color: orig?.color ? orig.color : 0xffffff,
            side: sideMode,
          });
        } else {
          // Textured PBR Mode: restore or update standard material with physical properties
          if (mesh.material && (mesh.material as any).isMeshStandardMaterial) {
            const mat = mesh.material as THREE.MeshStandardMaterial;
            mat.roughness = pbrSettings.roughness;
            mat.metalness = pbrSettings.metallic;
            if (mat.normalScale) {
              mat.normalScale.set(pbrSettings.normalScale, pbrSettings.normalScale);
            }
            if (mat.aoMap) {
              mat.aoMapIntensity = pbrSettings.aoIntensity;
            }
            if (mat.emissive) {
              mat.emissive.set(pbrSettings.emissiveColor);
              mat.emissiveIntensity = pbrSettings.emissiveIntensity;
            }
            if (pbrSettings.alphaMode === 'BLEND') {
              mat.transparent = true;
              mat.opacity = pbrSettings.baseColorOpacity;
            } else {
              mat.transparent = false;
              mat.opacity = 1.0;
            }
            if (pbrSettings.alphaMode === 'MASK') {
              mat.alphaTest = pbrSettings.alphaCutoff;
            } else {
              mat.alphaTest = 0.0;
            }
            mat.side = sideMode;
            mat.needsUpdate = true;
          }
        }
      }
    });
  }, [clonedScene, renderMode, doubleSided, pbrSettings]);

  // Center model so its base sits on Y=0 and center is at X=0, Z=0
  const yOffset = -bounds.box.min.y;
  const xOffset = -bounds.center.x;
  const zOffset = -bounds.center.z;

  return (
    <group position={[xOffset, yOffset, zOffset]}>
      <primitive object={clonedScene} />

      {/* Visual Bounding Box Helper */}
      {showBoundingBox && <primitive object={boxHelper} />}

      {/* Wireframe Edge Overlay Mode */}
      {showWireframeOverlay && renderMode !== 'wireframe' && (
        <group>
          {clonedScene.children.map((c, i) => (
            <primitive key={i} object={c.clone(true)}>
              <meshBasicMaterial wireframe color="#38bdf8" transparent opacity={0.35} />
            </primitive>
          ))}
        </group>
      )}
    </group>
  );
};

/* -------------------------------------------------------------------------- */
/*                       Loading Progress Overlay Indicator                   */
/* -------------------------------------------------------------------------- */

interface LoadingOverlayProps {
  progress: number;
  item: string;
}

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ progress, item }) => {
  const roundedProgress = Math.round(progress);
  let stageMessage = 'Connecting to 3D asset storage...';
  if (roundedProgress > 15 && roundedProgress < 50) {
    stageMessage = 'Downloading binary GLB geometry buffer...';
  } else if (roundedProgress >= 50 && roundedProgress < 85) {
    stageMessage = 'Parsing glTF 2.0 textures and materials...';
  } else if (roundedProgress >= 85) {
    stageMessage = 'Compiling WebGL shaders and initializing viewport...';
  }

  return (
    <div className="absolute inset-0 z-30 flex flex-col items-center justify-center bg-slate-950/80 backdrop-blur-md transition-all duration-300">
      <div className="w-72 max-w-[85vw] p-6 bg-slate-900/90 border border-slate-800 rounded-2xl shadow-2xl flex flex-col items-center text-center">
        {/* Animated Spin Ring */}
        <div className="relative w-16 h-16 mb-4 flex items-center justify-center">
          <div className="absolute inset-0 rounded-full border-4 border-slate-800" />
          <div
            className="absolute inset-0 rounded-full border-4 border-blue-500 border-t-transparent animate-spin"
            style={{ animationDuration: '1s' }}
          />
          <span className="font-mono text-xs font-bold text-white">{roundedProgress}%</span>
        </div>

        <h4 className="text-sm font-bold text-white mb-1">Loading 3D Asset</h4>
        <p className="text-[11px] text-blue-400 font-medium mb-3 h-8 flex items-center justify-center">
          {stageMessage}
        </p>

        {/* Progress Bar Track */}
        <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden border border-slate-800">
          <div
            className="h-full bg-gradient-to-r from-blue-600 via-indigo-500 to-cyan-400 transition-all duration-200"
            style={{ width: `${Math.max(roundedProgress, 5)}%` }}
          />
        </div>

        {item && (
          <div className="mt-2 text-[10px] text-slate-500 font-mono truncate max-w-full">
            {item.split('/').pop()}
          </div>
        )}
      </div>
    </div>
  );
};

/* -------------------------------------------------------------------------- */
/*                          Main ModelViewer Component                        */
/* -------------------------------------------------------------------------- */

interface ModelViewerProps {
  assetUrl?: string;
  showControlsBar?: boolean;
  className?: string;
}

export const ModelViewer: React.FC<ModelViewerProps> = ({
  assetUrl,
  showControlsBar = true,
  className = 'h-[580px] lg:h-[660px]',
}) => {
  const {
    activeAsset,
    renderMode,
    setRenderMode,
    showGrid,
    setShowGrid,
    showAxes,
    setShowAxes,
    showBoundingBox,
    setShowBoundingBox,
    showWireframeOverlay,
    setShowWireframeOverlay,
    autoRotate,
    setAutoRotate,
    environmentPreset,
    setEnvironmentPreset,
    environmentIntensity,
    setEnvironmentIntensity,
    showEnvironmentBackground,
    setShowEnvironmentBackground,
    ambientIntensity,
    setAmbientIntensity,
    directionalIntensity,
    setDirectionalIntensity,
    viewportBgColor,
    setViewportBgColor,
    cameraFov,
    setCameraFov,
    shadowsEnabled,
    setShadowsEnabled,
    doubleSidedRendering,
    setDoubleSidedRendering,
    viewerPropertiesTab,
    setViewerPropertiesTab,
    isPropertiesPanelOpen,
    setIsPropertiesPanelOpen,
    isMaterialPanelOpen,
    setIsMaterialPanelOpen,
    isOptimizerPanelOpen,
    setIsOptimizerPanelOpen,
  } = useStore();

  const [stats, setStats] = useState<ModelGeometryStats>({
    vertices: 0,
    triangles: 0,
    meshes: 0,
    materials: 0,
    dimensions: [0, 0, 0],
  });

  const [fps, setFps] = useState<number>(60);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedExportProfile, setSelectedExportProfile] = useState<'standard' | 'high_quality' | 'optimized'>('standard');
  const [retryKey, setRetryKey] = useState<number>(0);
  const [currentUrlOverride, setCurrentUrlOverride] = useState<string | null>(null);
  const [showBgColorMenu, setShowBgColorMenu] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const controlsRef = useRef<any>(null);

  // Drei useProgress hook for real-time asset streaming progress
  const { active: isDreiLoading, progress: dreiProgress, item: currentLoadingItem } = useProgress();

  // Resolve target asset URL: explicit prop -> current override -> active asset -> default sample
  const resolvedUrl = useMemo(() => {
    if (currentUrlOverride) return currentUrlOverride;
    if (assetUrl) return assetUrl;
    if (activeAsset?.asset_id) {
      return assetApi.getDownloadUrl(activeAsset.asset_id, selectedExportProfile);
    }
    if (activeAsset?.glb_url) return activeAsset.glb_url;
    return '/models/sample_sword.glb';
  }, [assetUrl, currentUrlOverride, activeAsset, selectedExportProfile]);

  // Fullscreen change listener
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

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
      // Target object center at half height
      const targetY = stats.dimensions[1] > 0 ? stats.dimensions[1] * 0.5 : 0.8;
      controlsRef.current.target.set(0, targetY, 0);
      controlsRef.current.update();
    }
  };

  const setCameraAngle = (view: 'front' | 'side' | 'top' | 'iso') => {
    if (!controlsRef.current) return;
    const maxDim = Math.max(...stats.dimensions, 1);
    const dist = maxDim * 2.2;
    const centerY = stats.dimensions[1] * 0.5;

    controlsRef.current.target.set(0, centerY, 0);

    if (view === 'front') {
      controlsRef.current.object.position.set(0, centerY, dist);
    } else if (view === 'side') {
      controlsRef.current.object.position.set(dist, centerY, 0);
    } else if (view === 'top') {
      controlsRef.current.object.position.set(0, dist * 1.5, 0.001);
    } else {
      controlsRef.current.object.position.set(dist * 0.7, centerY + dist * 0.6, dist * 0.7);
    }
    controlsRef.current.update();
  };

  const BG_COLOR_PRESETS = [
    { label: 'Slate Dark', value: '#090d16', border: 'border-slate-800' },
    { label: 'Pitch Black', value: '#000000', border: 'border-zinc-900' },
    { label: 'Studio Grey', value: '#1e293b', border: 'border-slate-700' },
    { label: 'Pure White', value: '#ffffff', border: 'border-slate-300' },
    { label: 'Cyber Navy', value: '#030712', border: 'border-blue-950' },
  ];

  return (
    <div
      ref={containerRef}
      style={{ backgroundColor: viewportBgColor }}
      className={`relative w-full ${className} rounded-2xl border border-slate-800/80 overflow-hidden shadow-2xl flex flex-col group select-none`}
    >
      {/* -------------------------------------------------------------------- */}
      {/* 1. TOP VIEWPORT HEADER & QUICK ACTIONS                                */}
      {/* -------------------------------------------------------------------- */}
      {showControlsBar && (
        <div className="absolute top-4 left-4 right-4 z-20 flex items-center justify-between gap-3 pointer-events-none">
          {/* Top Left: Quick Mode Tabs & Panels */}
          <div className="flex items-center gap-1.5 p-1 bg-slate-900/90 backdrop-blur-md rounded-xl border border-slate-800/80 shadow-lg pointer-events-auto">
            <button
              onClick={() => setRenderMode('textured')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                renderMode === 'textured'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
              title="Full PBR Textured Shading"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Textured</span>
            </button>

            <button
              onClick={() => setRenderMode('solid')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                renderMode === 'solid'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
              title="Studio Clay Neutral Shading"
            >
              <Box className="w-3.5 h-3.5" />
              <span>Clay</span>
            </button>

            <button
              onClick={() => setRenderMode('wireframe')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                renderMode === 'wireframe'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
              title="Pure Wireframe Topology"
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Wireframe</span>
            </button>

            <button
              onClick={() => setRenderMode('normals')}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                renderMode === 'normals'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
              title="Surface Tangent & Curvature Normals"
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>Normals</span>
            </button>

            <div className="w-px h-4 bg-slate-800 mx-0.5" />

            {/* PBR Material System Panel Toggle */}
            <button
              onClick={() => setIsMaterialPanelOpen(!isMaterialPanelOpen)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                isMaterialPanelOpen
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/25 ring-1 ring-blue-400'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
              title="Open PBR Material System Inspector"
            >
              <Palette className="w-3.5 h-3.5 text-amber-400" />
              <span className="hidden sm:inline">PBR Inspector</span>
            </button>

            {/* Mesh Decimation Optimizer Toggle */}
            <button
              onClick={() => setIsOptimizerPanelOpen(!isOptimizerPanelOpen)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                isOptimizerPanelOpen
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md shadow-indigo-500/25 ring-1 ring-indigo-400'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
              title="Open 3D Mesh Decimation Engine"
            >
              <Cpu className="w-3.5 h-3.5 text-indigo-400" />
              <span className="hidden sm:inline">Optimizer</span>
            </button>
          </div>

          {/* Top Right: Properties Inspector Toggle & Fullscreen */}
          <div className="flex items-center gap-2 pointer-events-auto">
            {/* Properties Panel Toggle */}
            <button
              onClick={() => setIsPropertiesPanelOpen(!isPropertiesPanelOpen)}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl backdrop-blur-md border text-xs font-semibold transition-all ${
                isPropertiesPanelOpen
                  ? 'bg-blue-600 border-blue-500 text-white shadow-lg shadow-blue-500/20'
                  : 'bg-slate-900/90 border-slate-800 text-slate-300 hover:bg-slate-800'
              }`}
              title="Toggle Properties Panel"
            >
              <SlidersHorizontal className="w-4 h-4" />
              <span className="hidden md:inline">Properties</span>
              {isPropertiesPanelOpen ? (
                <ChevronRight className="w-3.5 h-3.5" />
              ) : (
                <ChevronLeft className="w-3.5 h-3.5" />
              )}
            </button>

            {/* Fullscreen Toggle */}
            <button
              onClick={toggleFullscreen}
              className="p-2 rounded-xl bg-slate-900/90 backdrop-blur-md border border-slate-800 text-slate-300 hover:bg-slate-800 transition-all"
              title={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
          </div>
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* 2. LEFT-SIDE FLOATING ASSET CONTROLS TOOLBAR                         */}
      {/* -------------------------------------------------------------------- */}
      <div className="absolute top-20 left-4 z-20 flex flex-col gap-1.5 p-1.5 bg-slate-900/90 backdrop-blur-md rounded-2xl border border-slate-800/80 shadow-2xl">
        {/* Wireframe Overlay Toggle */}
        <button
          onClick={() => setShowWireframeOverlay(!showWireframeOverlay)}
          className={`p-2 rounded-xl border transition-all ${
            showWireframeOverlay
              ? 'bg-blue-600 border-blue-500 text-white shadow-md shadow-blue-500/25'
              : 'border-transparent text-slate-400 hover:bg-slate-800 hover:text-slate-200'
          }`}
          title="Toggle Wireframe Overlay on Shaded Mesh"
        >
          <Layers className="w-4 h-4" />
        </button>

        {/* Ground Grid Toggle */}
        <button
          onClick={() => setShowGrid(!showGrid)}
          className={`p-2 rounded-xl border transition-all ${
            showGrid
              ? 'bg-blue-600 border-blue-500 text-white shadow-md shadow-blue-500/25'
              : 'border-transparent text-slate-400 hover:bg-slate-800 hover:text-slate-200'
          }`}
          title="Toggle Ground Plane Grid"
        >
          <Grid className="w-4 h-4" />
        </button>

        {/* Axes Helper Toggle */}
        <button
          onClick={() => setShowAxes(!showAxes)}
          className={`p-2 rounded-xl border transition-all ${
            showAxes
              ? 'bg-blue-600 border-blue-500 text-white shadow-md shadow-blue-500/25'
              : 'border-transparent text-slate-400 hover:bg-slate-800 hover:text-slate-200'
          }`}
          title="Toggle XYZ Coordinate Axes"
        >
          <Compass className="w-4 h-4" />
        </button>

        {/* Bounding Box Toggle */}
        <button
          onClick={() => setShowBoundingBox(!showBoundingBox)}
          className={`p-2 rounded-xl border transition-all ${
            showBoundingBox
              ? 'bg-blue-600 border-blue-500 text-white shadow-md shadow-blue-500/25'
              : 'border-transparent text-slate-400 hover:bg-slate-800 hover:text-slate-200'
          }`}
          title="Toggle 3D Bounding Box Volume"
        >
          <Box className="w-4 h-4" />
        </button>

        <div className="w-full h-px bg-slate-800 my-0.5" />

        {/* Auto Rotation Toggle */}
        <button
          onClick={() => setAutoRotate(!autoRotate)}
          className={`p-2 rounded-xl border transition-all ${
            autoRotate
              ? 'bg-indigo-600 border-indigo-500 text-white shadow-md shadow-indigo-500/25'
              : 'border-transparent text-slate-400 hover:bg-slate-800 hover:text-slate-200'
          }`}
          title="Toggle 360° Turntable Auto Rotation"
        >
          <RotateCw className={`w-4 h-4 ${autoRotate ? 'animate-spin' : ''}`} />
        </button>

        {/* Reset Camera Button */}
        <button
          onClick={resetCamera}
          className="p-2 rounded-xl border border-transparent text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-all"
          title="Reset Camera Target and Position"
        >
          <RefreshCw className="w-4 h-4" />
        </button>

        <div className="w-full h-px bg-slate-800 my-0.5" />

        {/* Background Color Palette Popover Toggle */}
        <div className="relative">
          <button
            onClick={() => setShowBgColorMenu(!showBgColorMenu)}
            className="p-2 rounded-xl border border-transparent text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-all flex items-center justify-center"
            title="Customize Viewport Background"
          >
            <div
              className="w-4 h-4 rounded-full border border-slate-600 shadow-sm"
              style={{ backgroundColor: viewportBgColor }}
            />
          </button>

          {showBgColorMenu && (
            <div className="absolute left-12 top-0 bg-slate-900/95 backdrop-blur-xl border border-slate-800 rounded-xl p-3 shadow-2xl z-30 w-48 flex flex-col gap-2.5">
              <div className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">
                Viewport Color
              </div>
              <div className="grid grid-cols-5 gap-1.5">
                {BG_COLOR_PRESETS.map((preset) => (
                  <button
                    key={preset.value}
                    onClick={() => {
                      setViewportBgColor(preset.value);
                      setShowBgColorMenu(false);
                    }}
                    className={`w-7 h-7 rounded-lg border ${preset.border} transition-all hover:scale-110 flex items-center justify-center ${
                      viewportBgColor === preset.value ? 'ring-2 ring-blue-500' : ''
                    }`}
                    style={{ backgroundColor: preset.value }}
                    title={preset.label}
                  />
                ))}
              </div>
              <div className="flex items-center gap-2 pt-1 border-t border-slate-800">
                <label className="text-[10px] text-slate-400">Custom:</label>
                <input
                  type="color"
                  value={viewportBgColor.startsWith('#') ? viewportBgColor : '#090d16'}
                  onChange={(e) => setViewportBgColor(e.target.value)}
                  className="w-full h-6 rounded cursor-pointer bg-transparent border-0"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* 3. RIGHT-SIDE COLLAPSIBLE PROPERTIES PANEL                           */}
      {/* -------------------------------------------------------------------- */}
      {isPropertiesPanelOpen && (
        <div className="absolute top-20 right-4 w-80 max-w-[calc(100vw-2rem)] z-20 bg-slate-900/95 backdrop-blur-xl border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col animate-in fade-in slide-in-from-right-4 duration-200">
          {/* Header & Tabs */}
          <div className="p-3 border-b border-slate-800 flex items-center justify-between">
            <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <SlidersHorizontal className="w-3.5 h-3.5 text-blue-400" />
              <span>Properties</span>
            </span>
            <button
              onClick={() => setIsPropertiesPanelOpen(false)}
              className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Subtabs: Shading / Lighting / Camera */}
          <div className="grid grid-cols-3 border-b border-slate-800 p-1 bg-slate-950/60 text-xs">
            <button
              onClick={() => setViewerPropertiesTab('shading')}
              className={`py-1.5 font-semibold rounded-lg transition-all ${
                viewerPropertiesTab === 'shading'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Shading
            </button>
            <button
              onClick={() => setViewerPropertiesTab('lighting')}
              className={`py-1.5 font-semibold rounded-lg transition-all ${
                viewerPropertiesTab === 'lighting'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Lighting
            </button>
            <button
              onClick={() => setViewerPropertiesTab('camera')}
              className={`py-1.5 font-semibold rounded-lg transition-all ${
                viewerPropertiesTab === 'camera'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Camera
            </button>
          </div>

          {/* Tab Content Body */}
          <div className="p-4 max-h-[420px] overflow-y-auto space-y-4 text-xs">
            {viewerPropertiesTab === 'shading' && (
              <div className="space-y-3">
                <div>
                  <label className="text-[11px] font-semibold text-slate-300 block mb-1.5">
                    Material Shading Mode
                  </label>
                  <div className="grid grid-cols-2 gap-1.5">
                    {[
                      { id: 'textured', label: 'PBR Textured' },
                      { id: 'solid', label: 'Studio Clay' },
                      { id: 'wireframe', label: 'Wireframe' },
                      { id: 'normals', label: 'Normals' },
                      { id: 'unlit', label: 'Unlit Color' },
                    ].map((m) => (
                      <button
                        key={m.id}
                        onClick={() => setRenderMode(m.id as any)}
                        className={`py-1.5 px-2 rounded-lg border text-left font-medium text-[11px] transition-all ${
                          renderMode === m.id
                            ? 'bg-blue-600 border-blue-500 text-white'
                            : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        {m.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-300">Wireframe Overlay</span>
                    <button
                      onClick={() => setShowWireframeOverlay(!showWireframeOverlay)}
                      className={`w-8 h-4 rounded-full p-0.5 transition-colors ${
                        showWireframeOverlay ? 'bg-blue-600' : 'bg-slate-800'
                      }`}
                    >
                      <div
                        className={`w-3 h-3 rounded-full bg-white transition-transform ${
                          showWireframeOverlay ? 'translate-x-4' : 'translate-x-0'
                        }`}
                      />
                    </button>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-300">Double-Sided Shading</span>
                    <button
                      onClick={() => setDoubleSidedRendering(!doubleSidedRendering)}
                      className={`w-8 h-4 rounded-full p-0.5 transition-colors ${
                        doubleSidedRendering ? 'bg-blue-600' : 'bg-slate-800'
                      }`}
                    >
                      <div
                        className={`w-3 h-3 rounded-full bg-white transition-transform ${
                          doubleSidedRendering ? 'translate-x-4' : 'translate-x-0'
                        }`}
                      />
                    </button>
                  </div>
                </div>

                <button
                  onClick={() => setIsMaterialPanelOpen(true)}
                  className="w-full py-2 bg-gradient-to-r from-blue-600/20 to-indigo-600/20 hover:from-blue-600/30 hover:to-indigo-600/30 border border-blue-500/30 rounded-xl text-blue-300 font-semibold flex items-center justify-center gap-2 mt-2"
                >
                  <Palette className="w-3.5 h-3.5 text-amber-400" />
                  <span>Deep PBR Material Tweaks</span>
                </button>
              </div>
            )}

            {viewerPropertiesTab === 'lighting' && (
              <div className="space-y-3">
                <div>
                  <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                    HDR Environment Map
                  </label>
                  <select
                    value={environmentPreset}
                    onChange={(e) => setEnvironmentPreset(e.target.value as any)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                  >
                    <option value="city">City Daylight</option>
                    <option value="studio">Studio Neutral (Even)</option>
                    <option value="sunset">Sunset (Warm Golden)</option>
                    <option value="warehouse">Industrial Warehouse</option>
                    <option value="dawn">Dawn Horizon</option>
                    <option value="forest">Forest Woodland</option>
                    <option value="night">Dark Night Rim</option>
                  </select>
                </div>

                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>HDR Intensity</span>
                    <span className="font-mono text-blue-400">{environmentIntensity}x</span>
                  </div>
                  <input
                    type="range"
                    min={0.0}
                    max={2.5}
                    step={0.1}
                    value={environmentIntensity}
                    onChange={(e) => setEnvironmentIntensity(parseFloat(e.target.value))}
                    className="w-full accent-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between py-1">
                  <span className="text-slate-300">Show Skybox Backdrop</span>
                  <button
                    onClick={() => setShowEnvironmentBackground(!showEnvironmentBackground)}
                    className={`w-8 h-4 rounded-full p-0.5 transition-colors ${
                      showEnvironmentBackground ? 'bg-blue-600' : 'bg-slate-800'
                    }`}
                  >
                    <div
                      className={`w-3 h-3 rounded-full bg-white transition-transform ${
                        showEnvironmentBackground ? 'translate-x-4' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>

                <div className="pt-2 border-t border-slate-800">
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>Ambient Light</span>
                    <span className="font-mono text-blue-400">{ambientIntensity}</span>
                  </div>
                  <input
                    type="range"
                    min={0.1}
                    max={2.5}
                    step={0.1}
                    value={ambientIntensity}
                    onChange={(e) => setAmbientIntensity(parseFloat(e.target.value))}
                    className="w-full accent-blue-500"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>Key Light Intensity</span>
                    <span className="font-mono text-blue-400">{directionalIntensity}</span>
                  </div>
                  <input
                    type="range"
                    min={0.1}
                    max={4.0}
                    step={0.1}
                    value={directionalIntensity}
                    onChange={(e) => setDirectionalIntensity(parseFloat(e.target.value))}
                    className="w-full accent-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between pt-1">
                  <span className="text-slate-300">Ground Shadows</span>
                  <button
                    onClick={() => setShadowsEnabled(!shadowsEnabled)}
                    className={`w-8 h-4 rounded-full p-0.5 transition-colors ${
                      shadowsEnabled ? 'bg-blue-600' : 'bg-slate-800'
                    }`}
                  >
                    <div
                      className={`w-3 h-3 rounded-full bg-white transition-transform ${
                        shadowsEnabled ? 'translate-x-4' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>
              </div>
            )}

            {viewerPropertiesTab === 'camera' && (
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>Field of View (FOV)</span>
                    <span className="font-mono text-blue-400">{cameraFov}°</span>
                  </div>
                  <input
                    type="range"
                    min={25}
                    max={85}
                    step={1}
                    value={cameraFov}
                    onChange={(e) => setCameraFov(parseInt(e.target.value))}
                    className="w-full accent-blue-500"
                  />
                </div>

                <div className="pt-2 border-t border-slate-800">
                  <label className="text-[11px] font-semibold text-slate-300 block mb-1.5">
                    Camera Viewport Angles
                  </label>
                  <div className="grid grid-cols-2 gap-1.5">
                    <button
                      onClick={() => setCameraAngle('iso')}
                      className="py-1.5 px-2 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-300 text-left"
                    >
                      Isometric 3/4
                    </button>
                    <button
                      onClick={() => setCameraAngle('front')}
                      className="py-1.5 px-2 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-300 text-left"
                    >
                      Front (XZ)
                    </button>
                    <button
                      onClick={() => setCameraAngle('side')}
                      className="py-1.5 px-2 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-300 text-left"
                    >
                      Side (YZ)
                    </button>
                    <button
                      onClick={() => setCameraAngle('top')}
                      className="py-1.5 px-2 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-300 text-left"
                    >
                      Top (XY)
                    </button>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800">
                  <button
                    onClick={resetCamera}
                    className="w-full py-2 bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white rounded-xl font-semibold flex items-center justify-center gap-2"
                  >
                    <Camera className="w-3.5 h-3.5" />
                    <span>Center & Frame Model</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Floating Material Preview / Optimizer Sub-panels */}
      {isMaterialPanelOpen && (
        <div className="absolute top-16 right-4 w-96 max-w-[calc(100vw-2rem)] z-30 animate-in fade-in slide-in-from-right-4 duration-200">
          <MaterialPreviewPanel onClose={() => setIsMaterialPanelOpen(false)} />
        </div>
      )}

      {isOptimizerPanelOpen && (
        <div className="absolute top-16 right-4 w-96 max-w-[calc(100vw-2rem)] z-30 animate-in fade-in slide-in-from-right-4 duration-200">
          <MeshOptimizerPanel onClose={() => setIsOptimizerPanelOpen(false)} />
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* 4. MAIN THREE.JS 3D CANVAS VIEWPORT                                  */}
      {/* -------------------------------------------------------------------- */}
      <div className="flex-1 w-full h-full relative cursor-grab active:cursor-grabbing">
        {/* Real-time Loading Overlay Indicator */}
        {isDreiLoading && (
          <LoadingOverlay progress={dreiProgress} item={currentLoadingItem} />
        )}

        <ViewerErrorBoundary
          fallbackUrl="/models/sample_sword.glb"
          onRetry={() => setRetryKey((k) => k + 1)}
          onFallback={() => setCurrentUrlOverride('/models/sample_sword.glb')}
        >
          <Canvas
            key={retryKey}
            camera={{ position: [0, 1.2, 3.2], fov: cameraFov }}
            gl={{
              antialias: true,
              alpha: true,
              toneMapping: THREE.ACESFilmicToneMapping,
              toneMappingExposure: 1.0,
            }}
          >
            {/* Real-time FPS Monitoring */}
            <FpsTracker onFpsUpdate={setFps} />

            {/* Dynamic Camera Controller */}
            <CameraController fov={cameraFov} />

            {/* Studio Lighting System */}
            <ambientLight intensity={ambientIntensity} />
            <directionalLight
              position={[5, 8, 5]}
              intensity={directionalIntensity}
              castShadow={shadowsEnabled}
            />
            <directionalLight
              position={[-5, -2, -5]}
              intensity={directionalIntensity * 0.25}
            />
            <pointLight position={[0, 4, 2]} intensity={0.6} />

            {/* Ground Grid Helper */}
            {showGrid && (
              <gridHelper
                args={[12, 16, '#38bdf8', '#1e293b']}
                position={[0, -0.001, 0]}
              />
            )}

            {/* XYZ Axes Helper */}
            {showAxes && <axesHelper args={[2]} />}

            {/* Contact Shadows on Ground Grid */}
            {shadowsEnabled && (
              <ContactShadows
                position={[0, 0, 0]}
                opacity={0.65}
                scale={10}
                blur={2.5}
                far={4}
                resolution={512}
                color="#000000"
              />
            )}

            {/* 3D Model Loading Suspense */}
            <Suspense fallback={null}>
              <ModelMesh
                url={resolvedUrl}
                renderMode={renderMode}
                showBoundingBox={showBoundingBox}
                showWireframeOverlay={showWireframeOverlay}
                doubleSided={doubleSidedRendering}
                onStatsCalculated={setStats}
              />
              <Environment
                preset={environmentPreset}
                background={showEnvironmentBackground}
                environmentIntensity={environmentIntensity}
              />
            </Suspense>

            {/* Smooth OrbitControls with Damping and Auto-Rotation */}
            <OrbitControls
              ref={controlsRef}
              autoRotate={autoRotate}
              autoRotateSpeed={2.0}
              enableDamping
              dampingFactor={0.05}
              minDistance={0.2}
              maxDistance={25}
            />
          </Canvas>
        </ViewerErrorBoundary>
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* 5. BOTTOM MODEL STATISTICS TELEMETRY HUD & EXPORT BUTTON             */}
      {/* -------------------------------------------------------------------- */}
      <div className="absolute bottom-4 left-4 right-4 z-20 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
        {/* Real Geometry Statistics Card */}
        <div className="flex flex-wrap items-center gap-3 sm:gap-4 px-4 py-2.5 bg-slate-900/90 backdrop-blur-md rounded-xl border border-slate-800/80 shadow-2xl pointer-events-auto text-xs text-slate-300">
          {/* Polygons / Triangles */}
          <div className="flex items-center gap-1.5" title="Total Triangle Face Count">
            <Activity className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-slate-400">Polys:</span>
            <span className="font-semibold text-slate-100 font-mono">
              {(stats.triangles || activeAsset?.polygon_count || 856).toLocaleString()}
            </span>
          </div>

          <div className="w-px h-3.5 bg-slate-800 hidden sm:block" />

          {/* Vertices */}
          <div className="flex items-center gap-1.5" title="Total 3D Mesh Vertices">
            <span className="text-slate-400">Vertices:</span>
            <span className="font-semibold text-slate-100 font-mono">
              {(stats.vertices || 430).toLocaleString()}
            </span>
          </div>

          <div className="w-px h-3.5 bg-slate-800 hidden sm:block" />

          {/* Meshes & Materials */}
          <div className="hidden md:flex items-center gap-1.5" title="Sub-mesh Elements & Materials">
            <span className="text-slate-400">Meshes:</span>
            <span className="font-mono text-slate-200">{stats.meshes || 1}</span>
            <span className="text-slate-500">|</span>
            <span className="text-slate-400">Mats:</span>
            <span className="font-mono text-slate-200">{stats.materials || 1}</span>
          </div>

          <div className="w-px h-3.5 bg-slate-800 hidden sm:block" />

          {/* Bounding Box Dimensions */}
          <div className="hidden lg:flex items-center gap-1.5" title="Object Dimensions in Meters (X × Y × Z)">
            <Box className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-slate-400">Bounds:</span>
            <span className="font-semibold text-slate-100 font-mono">
              {stats.dimensions.join(' × ')} m
            </span>
          </div>

          <div className="w-px h-3.5 bg-slate-800 hidden sm:block" />

          {/* File Size */}
          <div className="flex items-center gap-1.5" title="Binary GLB File Size">
            <span className="text-slate-400">Size:</span>
            <span className="font-semibold text-slate-100 font-mono">
              {activeAsset?.file_size
                ? `${(activeAsset.file_size / (1024 * 1024)).toFixed(2)} MB`
                : '1.59 MB'}
            </span>
          </div>

          <div className="w-px h-3.5 bg-slate-800" />

          {/* Real-time FPS Badge */}
          <div className="flex items-center gap-1 text-[11px] font-mono" title="Viewport Frame Rate">
            <Gauge className="w-3.5 h-3.5 text-emerald-400" />
            <span
              className={`font-bold ${
                fps >= 50
                  ? 'text-emerald-400'
                  : fps >= 30
                  ? 'text-amber-400'
                  : 'text-red-400'
              }`}
            >
              {fps} FPS
            </span>
          </div>
        </div>

        {/* Integrated Download & Profile Selector Action */}
        <div className="flex items-center gap-2 pointer-events-auto">
          <select
            value={selectedExportProfile}
            onChange={(e) => setSelectedExportProfile(e.target.value as any)}
            className="bg-slate-900/95 backdrop-blur-md border border-slate-700/80 rounded-xl px-2.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-medium"
            title="Choose GLB Export Texture Resolution Profile"
          >
            <option value="standard">Standard (1024px)</option>
            <option value="high_quality">High-Quality (2048px)</option>
            <option value="optimized">Optimized (512px)</option>
          </select>

          <a
            href={
              activeAsset?.asset_id
                ? assetApi.getDownloadUrl(activeAsset.asset_id, selectedExportProfile)
                : resolvedUrl
            }
            download={`${(activeAsset?.asset_name || 'polygen_asset').replace(/[^a-zA-Z0-9]/g, '_')}_${selectedExportProfile}.glb`}
            className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-blue-500/25 transition-all active:scale-95"
            title="Download Khronos glTF 2.0 Binary Asset"
          >
            <Download className="w-4 h-4" />
            <span>Export GLB</span>
          </a>
        </div>
      </div>
    </div>
  );
};
