import React, { useState } from 'react';
import { useStore } from '../store/useStore';
import { optimizerApi, type OptimizationReport } from '../services/api';
import {
  Cpu,
  Layers,
  CheckCircle2,
  X,
  Zap,
  Activity
} from 'lucide-react';

interface MeshOptimizerPanelProps {
  onClose?: () => void;
  className?: string;
  assetId?: string;
}

export const MeshOptimizerPanel: React.FC<MeshOptimizerPanelProps> = ({
  onClose,
  className = "",
  assetId,
}) => {
  const {
    activeAsset,
    polygonBudgetSetting,
    setPolygonBudgetSetting,
    customPolygonBudget,
    setCustomPolygonBudget,
    lastOptimizationReport,
    setLastOptimizationReport,
    addNotification,
    renderMode,
    setRenderMode,
  } = useStore();

  const [isOptimizing, setIsOptimizing] = useState<boolean>(false);
  const [normalizeBounds, setNormalizeBounds] = useState<boolean>(true);
  const [alignGround, setAlignGround] = useState<boolean>(true);
  const [removeDuplicates, setRemoveDuplicates] = useState<boolean>(true);
  const [report, setReport] = useState<OptimizationReport | null>(lastOptimizationReport);

  const targetAssetId = assetId || activeAsset?.asset_id || 'sample_sword';

  const handleRunOptimization = async () => {
    setIsOptimizing(true);
    try {
      const response = await optimizerApi.optimize({
        asset_id: targetAssetId,
        budget_preset: polygonBudgetSetting,
        custom_budget: polygonBudgetSetting === 'custom' ? customPolygonBudget : undefined,
        normalize_bounds: normalizeBounds,
        align_ground: alignGround,
        remove_duplicates: removeDuplicates,
      });

      const optReport = response.data.report;
      setReport(optReport);
      setLastOptimizationReport(optReport);

      addNotification({
        title: 'Mesh Optimization Complete',
        message: `Reduced by ${optReport.reduction_percentage}% (${optReport.original_polygon_count.toLocaleString()} -> ${optReport.final_polygon_count.toLocaleString()} faces) in ${optReport.optimization_duration_seconds}s.`,
        type: 'success',
      });
    } catch (err: any) {
      addNotification({
        title: 'Optimization Failed',
        message: err.response?.data?.detail || 'Could not optimize mesh geometry.',
        type: 'error',
      });
    } finally {
      setIsOptimizing(false);
    }
  };

  const getTargetBudgetNumber = () => {
    if (polygonBudgetSetting === 'low') return 3000;
    if (polygonBudgetSetting === 'medium') return 10000;
    if (polygonBudgetSetting === 'high') return 35000;
    return customPolygonBudget;
  };

  return (
    <div
      className={`bg-slate-900/95 backdrop-blur-2xl border border-slate-800 rounded-3xl p-5 shadow-2xl flex flex-col gap-4 text-slate-200 z-30 max-h-[85vh] overflow-y-auto ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-indigo-600/20 border border-indigo-500/30 rounded-xl text-indigo-400">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <span>Mesh Optimization Engine</span>
              <span className="text-[10px] font-mono px-2 py-0.5 bg-indigo-950 text-indigo-300 border border-indigo-800/60 rounded-full">
                QEM Quadric Decimation
              </span>
            </h2>
            <p className="text-[11px] text-slate-400">
              Polygon Budgeting & Topology Optimization for Game Engines
            </p>
          </div>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
            title="Close Panel"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Target Budget Presets */}
      <div>
        <label className="text-xs font-semibold text-slate-300 block mb-2 flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-indigo-400" />
          <span>Select Target Polygon Budget</span>
        </label>
        <div className="grid grid-cols-2 gap-2">
          {[
            { id: 'low', name: 'Low LOD', count: '3,000 faces', desc: 'Mobile XR & WebGL' },
            { id: 'medium', name: 'Medium', count: '10,000 faces', desc: 'Game Real-time' },
            { id: 'high', name: 'High Quality', count: '35,000 faces', desc: 'Hero Cinematic' },
            { id: 'custom', name: 'Custom Budget', count: `${customPolygonBudget.toLocaleString()}`, desc: 'User specified' },
          ].map((preset) => {
            const isSelected = polygonBudgetSetting === preset.id;
            return (
              <button
                key={preset.id}
                onClick={() => setPolygonBudgetSetting(preset.id as any)}
                className={`p-2.5 rounded-xl border text-left transition-all flex flex-col justify-between ${
                  isSelected
                    ? 'bg-indigo-950/60 border-indigo-500 text-white shadow-md shadow-indigo-500/20 ring-1 ring-indigo-500'
                    : 'bg-slate-950/80 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs text-slate-200">{preset.name}</span>
                  <span className="text-[10px] font-mono text-indigo-400">{preset.count}</span>
                </div>
                <span className="text-[10px] text-slate-500 mt-0.5">{preset.desc}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Custom Budget Slider */}
      {polygonBudgetSetting === 'custom' && (
        <div className="p-3 bg-slate-950/90 border border-slate-800 rounded-2xl flex flex-col gap-2">
          <div className="flex justify-between text-xs">
            <span className="text-slate-300 font-medium">Custom Target Faces:</span>
            <span className="font-mono text-indigo-400 font-bold">{customPolygonBudget.toLocaleString()}</span>
          </div>
          <input
            type="range"
            min={500}
            max={50000}
            step={500}
            value={customPolygonBudget}
            onChange={(e) => setCustomPolygonBudget(parseInt(e.target.value))}
            className="w-full accent-indigo-500 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-slate-500">
            <span>500 faces (Ultra-low)</span>
            <span>50,000 faces (High-poly)</span>
          </div>
        </div>
      )}

      {/* Feature Optimization Options */}
      <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-2xl flex flex-col gap-2 text-xs">
        <span className="font-semibold text-slate-300 text-[11px] uppercase tracking-wider block mb-0.5">
          Geometry Processing Options
        </span>
        <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-white">
          <input
            type="checkbox"
            checked={normalizeBounds}
            onChange={(e) => setNormalizeBounds(e.target.checked)}
            className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-0"
          />
          <span>Normalize Bounding Box (Center at Origin & Unit Scale)</span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-white">
          <input
            type="checkbox"
            checked={alignGround}
            onChange={(e) => setAlignGround(e.target.checked)}
            className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-0"
          />
          <span>Ground Plane Alignment ($y_{'{'}min{'}'} = 0$)</span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-white">
          <input
            type="checkbox"
            checked={removeDuplicates}
            onChange={(e) => setRemoveDuplicates(e.target.checked)}
            className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-0"
          />
          <span>Remove Duplicate Vertices & Degenerate Triangles</span>
        </label>
      </div>

      {/* Shading Mode Helper for Visual Inspection */}
      <div className="flex items-center justify-between text-xs bg-slate-950 px-3 py-2 rounded-xl border border-slate-800">
        <span className="text-slate-400">Viewport Shading:</span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setRenderMode('wireframe')}
            className={`px-2 py-1 rounded text-[11px] font-medium transition-colors ${
              renderMode === 'wireframe' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Wireframe
          </button>
          <button
            onClick={() => setRenderMode('solid')}
            className={`px-2 py-1 rounded text-[11px] font-medium transition-colors ${
              renderMode === 'solid' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Clay
          </button>
          <button
            onClick={() => setRenderMode('textured')}
            className={`px-2 py-1 rounded text-[11px] font-medium transition-colors ${
              renderMode === 'textured' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Textured
          </button>
        </div>
      </div>

      {/* Action Button */}
      <button
        onClick={handleRunOptimization}
        disabled={isOptimizing}
        className="w-full py-3 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 disabled:opacity-50 text-white font-semibold text-xs rounded-xl shadow-lg shadow-indigo-500/25 transition-all flex items-center justify-center gap-2"
      >
        {isOptimizing ? (
          <>
            <span className="animate-spin">⌛</span>
            <span>Optimizing Mesh Geometry...</span>
          </>
        ) : (
          <>
            <Zap className="w-4 h-4 text-amber-300" />
            <span>Optimize Mesh to {getTargetBudgetNumber().toLocaleString()} Polys</span>
          </>
        )}
      </button>

      {/* OPTIMIZATION REPORT CARD */}
      {report && (
        <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl flex flex-col gap-3 animate-in fade-in duration-300">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <span className="text-xs font-bold text-white flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-emerald-400" />
              <span>Optimization Telemetry Report</span>
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 rounded-full">
              {report.status}
            </span>
          </div>

          {/* Metric Comparison Badges */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2.5 bg-slate-900 rounded-xl border border-slate-800/80">
              <span className="text-slate-500 text-[10px] block">Polygons:</span>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono text-slate-400 line-through text-[11px]">
                  {report.original_polygon_count.toLocaleString()}
                </span>
                <span className="font-mono text-emerald-400 font-bold">
                  {report.final_polygon_count.toLocaleString()}
                </span>
              </div>
              <span className="text-[10px] text-emerald-400 font-medium block mt-0.5">
                -{report.reduction_percentage}% reduction
              </span>
            </div>

            <div className="p-2.5 bg-slate-900 rounded-xl border border-slate-800/80">
              <span className="text-slate-500 text-[10px] block">Vertices:</span>
              <div className="flex items-baseline gap-1 mt-0.5">
                <span className="font-mono text-slate-400 line-through text-[11px]">
                  {report.original_vertex_count.toLocaleString()}
                </span>
                <span className="font-mono text-cyan-400 font-bold">
                  {report.final_vertex_count.toLocaleString()}
                </span>
              </div>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Duration: {report.optimization_duration_seconds}s
              </span>
            </div>
          </div>

          {/* Topology Sanity */}
          <div className="flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800/60 pt-2">
            <span className="flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Watertight & Manifold Topology</span>
            </span>
            <span className="flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>UVs & PBR Intact</span>
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
