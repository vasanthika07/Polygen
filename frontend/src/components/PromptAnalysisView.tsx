import React, { useState } from 'react';
import type { PromptSpecification } from '../services/api';
import {
  Sparkles,
  Box,
  Palette,
  Layers,
  Sun,
  Flame,
  CheckCircle2,
  Copy,
  Check,
  Cpu,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  FileCode2,
  Sliders,
  X
} from 'lucide-react';

interface PromptAnalysisViewProps {
  spec: PromptSpecification | null;
  isLoading: boolean;
  onApplyStyle?: (style: string) => void;
  onClose?: () => void;
}

export const PromptAnalysisView: React.FC<PromptAnalysisViewProps> = ({
  spec,
  isLoading,
  onApplyStyle,
  onClose
}) => {
  const [activeModelTab, setActiveModelTab] = useState<'shap_e' | 'hunyuan3d' | 'stable_diffusion' | 'triposr'>('shap_e');
  const [copiedPrompt, setCopiedPrompt] = useState(false);
  const [showTechnicalSpecs, setShowTechnicalSpecs] = useState(false);

  if (isLoading) {
    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-2xl flex flex-col items-center justify-center gap-3 animate-pulse">
        <div className="w-10 h-10 rounded-xl bg-blue-600/30 text-blue-400 flex items-center justify-center">
          <Sparkles className="w-5 h-5 animate-spin" />
        </div>
        <div className="text-xs font-semibold text-slate-200">Analyzing Natural Language Prompt...</div>
        <div className="text-[11px] text-slate-500">Extracting entities, materials, lighting, and geometric constraints</div>
      </div>
    );
  }

  if (!spec) return null;

  const handleCopyModelPrompt = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedPrompt(true);
    setTimeout(() => setCopiedPrompt(false), 2000);
  };

  const getActivePrompt = () => {
    if (!spec.model_prompts) return '';
    return spec.model_prompts[activeModelTab] || '';
  };

  const getColorHex = (colorName: string): string => {
    const map: Record<string, string> = {
      'dark brown': '#4a2e18',
      'steel grey': '#71797E',
      'slate grey': '#708090',
      'blue': '#2563eb',
      'deep sapphire blue': '#0f52ba',
      'glowing cyan': '#06b6d4',
      'crimson red': '#dc2626',
      'emerald green': '#059669',
      'jet black': '#111827',
      'burnished gold': '#d97706',
      'pure white': '#f8fafc',
      'royal purple': '#7c3aed',
      'warm amber': '#d97706',
      'warm brass': '#b45309',
      'neon magenta': '#e11d48',
      'rust orange': '#c2410c'
    };
    return map[colorName.toLowerCase()] || '#64748b';
  };

  return (
    <div className="bg-slate-900/95 backdrop-blur-xl border border-blue-500/30 rounded-2xl p-6 shadow-2xl flex flex-col gap-5 relative overflow-hidden transition-all">
      {/* Decorative Glow */}
      <div className="absolute top-0 right-0 -mr-12 -mt-12 w-40 h-40 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white tracking-wide">3D Prompt Understanding Specification</h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold">
                {Math.round(spec.confidence * 100)}% Confidence
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Structured specification extracted via deterministic semantic NLP engine
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          {spec.category && (
            <span className="text-[11px] font-medium text-blue-300 bg-blue-500/10 border border-blue-500/20 px-2.5 py-1 rounded-lg uppercase tracking-wider">
              {spec.category}
            </span>
          )}
          {onApplyStyle && (
            <button
              onClick={() => onApplyStyle(spec.style)}
              className="text-xs px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-all shadow-sm"
            >
              Apply Style
            </button>
          )}
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              title="Close Specification View"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Core Specification Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Object & Style */}
        <div className="p-3.5 bg-slate-950/70 border border-slate-800/80 rounded-xl flex flex-col gap-2">
          <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1.5">
            <Box className="w-3.5 h-3.5 text-blue-400" />
            <span>Target Object & Style</span>
          </span>
          <div className="text-sm font-extrabold text-white capitalize">{spec.object}</div>
          <div className="flex items-center gap-2 mt-auto">
            <span className="text-[10px] text-slate-400">Classified Style:</span>
            <span className="text-xs font-semibold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-md border border-blue-500/20">
              {spec.style}
            </span>
          </div>
        </div>

        {/* Materials */}
        <div className="p-3.5 bg-slate-950/70 border border-slate-800/80 rounded-xl flex flex-col gap-2">
          <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-amber-400" />
            <span>Materials ({spec.materials.length})</span>
          </span>
          <div className="flex flex-wrap gap-1.5 mt-1">
            {spec.materials.map((mat, idx) => (
              <span
                key={idx}
                className="text-xs font-medium text-amber-200 bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded-lg capitalize"
              >
                {mat}
              </span>
            ))}
          </div>
        </div>

        {/* Color Palette */}
        <div className="p-3.5 bg-slate-950/70 border border-slate-800/80 rounded-xl flex flex-col gap-2">
          <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1.5">
            <Palette className="w-3.5 h-3.5 text-indigo-400" />
            <span>Color Palette ({spec.colors.length})</span>
          </span>
          <div className="flex flex-wrap gap-1.5 mt-1">
            {spec.colors.map((color, idx) => (
              <span
                key={idx}
                className="text-xs font-medium text-slate-200 bg-slate-900 border border-slate-700/80 px-2.5 py-1 rounded-lg flex items-center gap-1.5 capitalize"
              >
                <span
                  className="w-2.5 h-2.5 rounded-full border border-white/20 shrink-0"
                  style={{ backgroundColor: getColorHex(color) }}
                />
                <span>{color}</span>
              </span>
            ))}
          </div>
        </div>

        {/* Surface Details */}
        <div className="p-3.5 bg-slate-950/70 border border-slate-800/80 rounded-xl flex flex-col gap-2">
          <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-emerald-400" />
            <span>Surface Textures & Finish</span>
          </span>
          <div className="flex flex-wrap gap-1.5 mt-1">
            {spec.surface_details.map((detail, idx) => (
              <span
                key={idx}
                className="text-xs font-medium text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-md capitalize"
              >
                {detail}
              </span>
            ))}
          </div>
        </div>

        {/* Lighting & Atmosphere */}
        <div className="p-3.5 bg-slate-950/70 border border-slate-800/80 rounded-xl flex flex-col gap-2">
          <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1.5">
            <Sun className="w-3.5 h-3.5 text-yellow-400" />
            <span>Lighting & Illumination</span>
          </span>
          <div className="text-xs font-medium text-slate-200 mt-1 capitalize bg-slate-900 px-2.5 py-1.5 rounded-lg border border-slate-800">
            {spec.lighting}
          </div>
        </div>

        {/* Special Effects */}
        <div className="p-3.5 bg-slate-950/70 border border-slate-800/80 rounded-xl flex flex-col gap-2">
          <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1.5">
            <Flame className="w-3.5 h-3.5 text-cyan-400" />
            <span>Special Emissive Effects</span>
          </span>
          <div className="flex flex-wrap gap-1.5 mt-1">
            {spec.special_effects && spec.special_effects.length > 0 ? (
              spec.special_effects.map((fx, idx) => (
                <span
                  key={idx}
                  className="text-xs font-semibold text-cyan-300 bg-cyan-500/10 border border-cyan-500/30 px-2.5 py-1 rounded-lg animate-pulse"
                >
                  {fx}
                </span>
              ))
            ) : (
              <span className="text-xs text-slate-500 italic">None specified (Standard shading)</span>
            )}
          </div>
        </div>
      </div>

      {/* Model-Specific Adapted Prompts Viewer */}
      {spec.model_prompts && (
        <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl flex flex-col gap-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <span className="text-xs font-bold text-white flex items-center gap-2">
              <Cpu className="w-4 h-4 text-blue-400" />
              <span>Model-Specific Adapted Prompts</span>
            </span>

            {/* Model Tabs */}
            <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-xl border border-slate-800">
              {[
                { id: 'shap_e', label: 'OpenAI Shap-E' },
                { id: 'hunyuan3d', label: 'Hunyuan3D' },
                { id: 'stable_diffusion', label: 'Stable Diffusion (PBR)' },
                { id: 'triposr', label: 'TripoSR' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveModelTab(tab.id as any)}
                  className={`px-2.5 py-1 text-[11px] rounded-lg font-medium transition-all ${
                    activeModelTab === tab.id
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div className="relative p-3 bg-slate-900/90 border border-slate-800/80 rounded-xl font-mono text-[11px] text-slate-300 leading-relaxed">
            {getActivePrompt()}
            <button
              onClick={() => handleCopyModelPrompt(getActivePrompt())}
              className="absolute top-2.5 right-2.5 p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition-colors"
              title="Copy Adapted Prompt"
            >
              {copiedPrompt ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      )}

      {/* Collapsible Technical Specifications (Geometry, Textures, Negative Prompts) */}
      <div className="border border-slate-800/80 rounded-xl overflow-hidden bg-slate-950/40">
        <button
          onClick={() => setShowTechnicalSpecs(!showTechnicalSpecs)}
          className="w-full flex items-center justify-between p-3.5 text-xs font-semibold text-slate-300 hover:text-white transition-colors"
        >
          <span className="flex items-center gap-2">
            <FileCode2 className="w-4 h-4 text-indigo-400" />
            <span>Geometric Mesh & PBR Texture Requirements</span>
          </span>
          {showTechnicalSpecs ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showTechnicalSpecs && (
          <div className="p-4 border-t border-slate-800 space-y-4 text-xs">
            {/* Geometric Constraints */}
            <div>
              <div className="font-semibold text-slate-200 mb-2 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Geometry Requirements:</span>
              </div>
              <ul className="list-disc list-inside space-y-1 text-slate-400 pl-1">
                {spec.geometry_requirements.map((req, idx) => (
                  <li key={idx}>{req}</li>
                ))}
              </ul>
            </div>

            {/* Texture Requirements */}
            <div>
              <div className="font-semibold text-slate-200 mb-2 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-blue-400" />
                <span>PBR Texture Specifications:</span>
              </div>
              <ul className="list-disc list-inside space-y-1 text-slate-400 pl-1">
                {spec.texture_requirements.map((req, idx) => (
                  <li key={idx}>{req}</li>
                ))}
              </ul>
            </div>

            {/* Negative Prompt */}
            <div>
              <div className="font-semibold text-slate-200 mb-2 flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                <span>Negative Prompt Directives (Artifact Suppression):</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {spec.negative_prompt.map((neg, idx) => (
                  <span
                    key={idx}
                    className="text-[11px] font-mono text-rose-300 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded-md"
                  >
                    {neg}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
