import React from 'react';
import { useStore } from '../store/useStore';
import { 
  Sparkles, 
  Box, 
  Wrench,
  Layers, 
  Palette, 
  Sliders, 
  CheckCircle2, 
  AlertCircle, 
  Loader2,
  FileCheck
} from 'lucide-react';

interface StageConfig {
  key: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

const STAGES: StageConfig[] = [
  { key: 'prompt_analysis', name: 'Prompt Analysis', description: 'Extracting materials, semantics & geometry attributes', icon: Sparkles },
  { key: 'mesh_generation', name: '3D Generation', description: 'AI neural synthesis & polygonal surface extraction', icon: Box },
  { key: 'mesh_processing', name: 'Mesh Processing', description: 'Validating topology, non-manifold repair & normal recalculation', icon: Wrench },
  { key: 'uv_mapping', name: 'UV Mapping', description: 'Conformal parameterization & non-overlapping atlas packing', icon: Layers },
  { key: 'texture_generation', name: 'Texture Generation', description: 'Synthesizing PBR diffuse, normal, roughness, metallic, emissive maps', icon: Palette },
  { key: 'material_creation', name: 'PBR Material Creation', description: 'Compiling glTF 2.0 PBR material definitions & channel binding', icon: Sparkles },
  { key: 'mesh_optimization', name: 'Mesh Optimization', description: 'Target polygon budget decimation & LOD simplification', icon: Sliders },
  { key: 'glb_export', name: 'GLB Export', description: 'Compiling binary GLB container & rendering thumbnail preview', icon: FileCheck },
  { key: 'completed', name: 'Completed', description: 'Asset verified and ready for 3D inspection & download', icon: CheckCircle2 },
];

export const GenerationProgress: React.FC = () => {
  const { generationStage, generationProgress, generationMessage, isGenerating } = useStore();

  if (!isGenerating && generationStage === 'idle') {
    return null;
  }

  const isFailed = generationStage === 'failed';
  const isCompleted = generationStage === 'completed';

  const getCurrentStageIndex = () => {
    // Map backwards-compatible or transitional stage names
    let normalized = generationStage;
    if (normalized === 'prompt_processing') normalized = 'prompt_analysis';
    if (normalized === 'mesh_cleaning') normalized = 'mesh_processing';
    if (normalized === 'mesh_generation_validated') normalized = 'mesh_generation';
    if (normalized === 'material_assignment') normalized = 'material_creation';

    const idx = STAGES.findIndex((s) => s.key === normalized);
    return idx >= 0 ? idx : 0;
  };

  const currentIdx = getCurrentStageIndex();

  return (
    <div className="w-full bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-2xl">
      {/* Header & Status Indicator */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
            isFailed
              ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
              : isCompleted
              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
              : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
          }`}>
            {isFailed ? (
              <AlertCircle className="w-5 h-5" />
            ) : isCompleted ? (
              <CheckCircle2 className="w-5 h-5" />
            ) : (
              <Loader2 className="w-5 h-5 animate-spin" />
            )}
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100">
              {isFailed
                ? 'Generation Pipeline Error'
                : isCompleted
                ? 'Asset Successfully Generated!'
                : 'Generating 3D Asset...'}
            </h4>
            <p className="text-xs text-slate-400">
              {generationMessage || 'Orchestrating multi-stage AI pipeline...'}
            </p>
          </div>
        </div>

        {/* Progress Percentage Pill */}
        <div className="text-right">
          <span className={`text-xl font-bold font-mono ${
            isFailed ? 'text-rose-400' : isCompleted ? 'text-emerald-400' : 'text-blue-400'
          }`}>
            {generationProgress}%
          </span>
        </div>
      </div>

      {/* Animated Gradient Progress Bar */}
      <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden mb-6 relative">
        <div
          className={`h-full transition-all duration-500 ease-out rounded-full ${
            isFailed
              ? 'bg-rose-500'
              : 'bg-gradient-to-r from-blue-600 via-indigo-500 to-cyan-400'
          }`}
          style={{ width: `${generationProgress}%` }}
        />
      </div>

      {/* Stage Step Indicators (9 Pipeline Stages) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
        {STAGES.map((stage, idx) => {
          const Icon = stage.icon;
          const isPast = idx < currentIdx || isCompleted;
          const isCurrent = idx === currentIdx && !isCompleted && !isFailed;

          return (
            <div
              key={stage.key}
              className={`flex items-start gap-2.5 p-2.5 rounded-xl border transition-all ${
                isCurrent
                  ? 'bg-blue-950/40 border-blue-500/40 shadow-md shadow-blue-500/10 ring-1 ring-blue-500/30'
                  : isPast
                  ? 'bg-slate-900/40 border-slate-800 text-slate-300'
                  : 'bg-slate-950/40 border-slate-900 text-slate-500'
              }`}
            >
              <div
                className={`w-6 h-6 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                  isCurrent
                    ? 'bg-blue-600 text-white animate-pulse'
                    : isPast
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-slate-800 text-slate-500'
                }`}
              >
                {isPast ? (
                  <CheckCircle2 className="w-3.5 h-3.5" />
                ) : isCurrent ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Icon className="w-3.5 h-3.5" />
                )}
              </div>

              <div className="min-w-0">
                <div className={`text-xs font-medium truncate ${
                  isCurrent ? 'text-blue-300 font-semibold' : isPast ? 'text-slate-200' : 'text-slate-500'
                }`}>
                  {stage.name}
                </div>
                <div className="text-[10px] text-slate-400 truncate">
                  {stage.description}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
