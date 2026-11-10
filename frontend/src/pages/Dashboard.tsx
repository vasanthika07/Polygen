import React, { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import { healthApi } from '../services/api';
import { 
  LayoutDashboard, 
  Box, 
  Activity, 
  HardDrive, 
  Wand2, 
  Layers, 
  Zap
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { assets, setActiveTab } = useStore();
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    healthApi.check()
      .then((res) => setHealth(res.data))
      .catch((err) => console.error('Health check failed:', err));
  }, []);

  const totalPolygons = assets.reduce((sum, a) => sum + a.polygon_count, 0);
  const totalStorageBytes = assets.reduce((sum, a) => sum + a.file_size, 0);
  const totalStorageMB = (totalStorageBytes / (1024 * 1024)).toFixed(2);

  return (
    <div className="w-full max-w-7xl mx-auto px-4 lg:px-8 py-8 flex flex-col gap-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <LayoutDashboard className="w-3.5 h-3.5" />
            <span>Platform Overview & Telemetry</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            PolyGen Dashboard
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Real-time pipeline metrics, hardware status, and generative asset statistics.
          </p>
        </div>

        <button
          onClick={() => setActiveTab('generate')}
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-blue-500/25 transition-all self-start md:self-auto"
        >
          <Wand2 className="w-4 h-4" />
          <span>Launch Studio</span>
        </button>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium">Total Assets</span>
            <Box className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">{assets.length}</div>
          <p className="text-[11px] text-slate-500 mt-1">Exported GLB models</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium">Polygons Generated</span>
            <Layers className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">{totalPolygons.toLocaleString()}</div>
          <p className="text-[11px] text-slate-500 mt-1">Optimized triangles</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium">Storage Consumed</span>
            <HardDrive className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">{totalStorageMB} MB</div>
          <p className="text-[11px] text-slate-500 mt-1">Binary assets & PBR maps</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium">Pipeline Status</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 flex items-center gap-2">
            <span>Online</span>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping" />
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Backend: {health?.ai_backend || 'local_shape'}</p>
        </div>
      </div>

      {/* Architecture Workflow Visualizer Card */}
      <div className="bg-slate-900/80 border border-slate-800/80 rounded-3xl p-6 sm:p-8 shadow-2xl">
        <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
          <Zap className="w-5 h-5 text-blue-400" />
          <span>The PolyGen Multi-Stage Pipeline</span>
        </h3>
        <p className="text-xs text-slate-400 max-w-2xl mb-6">
          Every prompt traverses an orchestrated 8-stage geometry, UV parameterization, and PBR texturing pipeline designed for gaming and XR standards.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800/60">
            <span className="text-[10px] font-mono font-bold text-blue-400 uppercase">Stage 01</span>
            <h4 className="text-sm font-semibold text-slate-200 mt-1">Prompt Decomposition</h4>
            <p className="text-xs text-slate-400 mt-1">NLP entity extraction parsing object, style, materials, and emissive cues.</p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800/60">
            <span className="text-[10px] font-mono font-bold text-blue-400 uppercase">Stage 02</span>
            <h4 className="text-sm font-semibold text-slate-200 mt-1">AI 3D Synthesis</h4>
            <p className="text-xs text-slate-400 mt-1">Implicit neural field generation and Marching Cubes polygonal surface extraction.</p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800/60">
            <span className="text-[10px] font-mono font-bold text-blue-400 uppercase">Stage 03 & 04</span>
            <h4 className="text-sm font-semibold text-slate-200 mt-1">UVs & PBR Textures</h4>
            <p className="text-xs text-slate-400 mt-1">xatlas chart parameterization and multi-channel PBR texture map baking.</p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800/60">
            <span className="text-[10px] font-mono font-bold text-blue-400 uppercase">Stage 05 & 06</span>
            <h4 className="text-sm font-semibold text-slate-200 mt-1">QEM Decimation & GLB</h4>
            <p className="text-xs text-slate-400 mt-1">Quadric error polygon budgeting, PBR material binding, and GLB verification.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
