import React from 'react';
import { PromptInput } from '../components/PromptInput';
import { GenerationProgress } from '../components/GenerationProgress';
import { ModelViewer } from '../components/ModelViewer';
import { useStore } from '../store/useStore';
import { Sparkles, Layers, Box, Cpu } from 'lucide-react';

export const Generate: React.FC = () => {
  const { activeAsset } = useStore();

  return (
    <div className="w-full max-w-7xl mx-auto px-4 lg:px-8 py-8 flex flex-col gap-8">
      {/* Hero Subheader */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI-Driven Spatial Synthesis</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Text-to-3D Asset Pipeline
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
            Transform natural language prompts into optimized, UV-unwrapped, PBR-textured 3D models ready for Unreal Engine, Unity, and Blender.
          </p>
        </div>

        {/* Feature Badges */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-300">
            <Box className="w-3.5 h-3.5 text-blue-400" />
            <span>glTF / GLB 2.0</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-300">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span>QEM Decimation</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-300">
            <Cpu className="w-3.5 h-3.5 text-indigo-400" />
            <span>PBR Materials</span>
          </div>
        </div>
      </div>

      {/* Main Workspace Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Generation Studio Controls & Live Progress (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          <PromptInput />
          <GenerationProgress />
        </div>

        {/* Right Column: Interactive 3D Model Viewport (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Box className="w-4 h-4 text-blue-400" />
              <span>Interactive 3D Viewport</span>
            </h3>
            {activeAsset && (
              <span className="text-xs text-slate-400 font-medium">
                Viewing: <span className="text-slate-100">{activeAsset.asset_name}</span>
              </span>
            )}
          </div>
          <ModelViewer />
        </div>
      </div>
    </div>
  );
};
