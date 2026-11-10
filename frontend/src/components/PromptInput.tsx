import React, { useState } from 'react';
import { useStore } from '../store/useStore';
import { generationApi } from '../services/api';
import { JobWebSocket } from '../services/websocket';
import { 
  Sparkles, 
  Wand2, 
  Layers, 
  Palette, 
  Cpu, 
  Clock
} from 'lucide-react';

const PRESET_PROMPTS = [
  "A rusted medieval broadsword with a glowing blue sapphire in the hilt.",
  "A rustic oak wooden chair with carved armrests.",
  "A weathered pirate treasure chest reinforced with brass bands and padlock.",
  "A futuristic metallic battle robot with neon green visor.",
  "An ancient carved stone sculpture covered in moss."
];

export const PromptInput: React.FC = () => {
  const { isGenerating, setIsGenerating, setCurrentJob, updateGenerationProgress } = useStore();

  const [prompt, setPrompt] = useState('A rusted medieval broadsword with a glowing blue sapphire in the hilt.');
  const [style, setStyle] = useState('medieval fantasy');
  const [quality, setQuality] = useState('high');
  const [polygonBudget, setPolygonBudget] = useState(10000);
  const [targetFormat] = useState('glb');
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!prompt.trim() || isGenerating) return;

    setError(null);
    setIsGenerating(true);
    updateGenerationProgress({
      stage: 'queued',
      progress: 5,
      message: 'Sending prompt to PolyGen orchestrator...',
    });

    try {
      const res = await generationApi.createJob({
        prompt: prompt.trim(),
        style,
        quality,
        polygon_budget: polygonBudget,
        target_format: targetFormat,
      });

      const job = res.data;
      setCurrentJob(job);

      // Open live WebSocket stream for stage updates
      const ws = new JobWebSocket(job.job_id);
      ws.connect();
    } catch (err: any) {
      console.error('Failed to trigger generation:', err);
      setError(err.response?.data?.detail || 'Failed to submit generation job');
      setIsGenerating(false);
      updateGenerationProgress({
        stage: 'failed',
        progress: 0,
        message: 'Could not connect to generation service',
      });
    }
  };

  return (
    <div className="w-full bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-2xl flex flex-col gap-5">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-slate-100 font-semibold text-base">
          <Wand2 className="w-5 h-5 text-blue-400" />
          <span>Generative 3D Studio</span>
        </div>
        <div className="flex items-center gap-1.5 px-2.5 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full text-[11px] text-blue-400 font-medium">
          <Clock className="w-3 h-3" />
          <span>Est. 60–120s</span>
        </div>
      </div>

      {/* Natural Language Prompt Input */}
      <div className="flex flex-col gap-2">
        <label className="text-xs font-medium text-slate-300">Natural-Language Description</label>
        <div className="relative">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isGenerating}
            rows={3}
            className="w-full bg-slate-950/80 border border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 resize-none transition-all disabled:opacity-50"
            placeholder="Describe the 3D asset in detail (e.g., A rusted medieval broadsword with a glowing blue sapphire in the hilt...)"
          />
        </div>

        {/* Preset Prompt Inspiration Chips */}
        <div className="flex items-center gap-1.5 flex-wrap pt-1">
          <span className="text-[11px] text-slate-500 font-medium mr-1">Inspirations:</span>
          {PRESET_PROMPTS.map((p, idx) => (
            <button
              key={idx}
              type="button"
              disabled={isGenerating}
              onClick={() => setPrompt(p)}
              className="text-[11px] px-2.5 py-1 bg-slate-800/60 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700/60 rounded-lg transition-all truncate max-w-[200px]"
            >
              {p.split(' ')[1] || p.substring(0, 15)}...
            </button>
          ))}
        </div>
      </div>

      {/* Generation Hyperparameters Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Style Selector */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
            <Palette className="w-3.5 h-3.5 text-blue-400" />
            <span>Visual Style</span>
          </label>
          <select
            value={style}
            onChange={(e) => setStyle(e.target.value)}
            disabled={isGenerating}
            className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
          >
            <option value="medieval fantasy">Medieval Fantasy</option>
            <option value="realistic">Realistic</option>
            <option value="sci-fi">Sci-Fi / Cyberpunk</option>
            <option value="stylized">Stylized Hand-Painted</option>
            <option value="low-poly">Low-Poly</option>
            <option value="gothic">Gothic Ancient</option>
          </select>
        </div>

        {/* Quality Selector */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-indigo-400" />
            <span>PBR Quality Preset</span>
          </label>
          <select
            value={quality}
            onChange={(e) => setQuality(e.target.value)}
            disabled={isGenerating}
            className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
          >
            <option value="high">High (1024px PBR Maps)</option>
            <option value="standard">Standard (512px Maps, Faster)</option>
            <option value="ultra">Ultra (1024px + Emissive Multi-pass)</option>
          </select>
        </div>
      </div>

      {/* Polygon Budget Slider */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between text-xs">
          <span className="font-medium text-slate-400 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span>Target Polygon Budget</span>
          </span>
          <span className="font-mono font-semibold text-blue-400">
            {polygonBudget.toLocaleString()} polygons
          </span>
        </div>
        <input
          type="range"
          min="1000"
          max="50000"
          step="1000"
          value={polygonBudget}
          onChange={(e) => setPolygonBudget(parseInt(e.target.value))}
          disabled={isGenerating}
          className="w-full accent-blue-500 bg-slate-950 h-1.5 rounded-lg cursor-pointer"
        />
        <div className="flex justify-between text-[10px] text-slate-500">
          <span>1,000 (Mobile/VR)</span>
          <span>10,000 (Game Ready)</span>
          <span>50,000 (High Fidelity)</span>
        </div>
      </div>

      {/* Error alert */}
      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl">
          {error}
        </div>
      )}

      {/* Main Generate Action Button */}
      <button
        type="button"
        onClick={() => handleGenerate()}
        disabled={isGenerating || !prompt.trim()}
        className="w-full py-3.5 px-6 bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 hover:from-blue-500 hover:via-indigo-500 hover:to-violet-500 text-white font-semibold text-sm rounded-xl shadow-xl shadow-blue-600/25 transition-all duration-200 active:scale-[0.99] disabled:opacity-50 disabled:pointer-events-none flex items-center justify-center gap-2"
      >
        <Sparkles className="w-4 h-4" />
        <span>{isGenerating ? 'GENERATING 3D MODEL...' : 'GENERATE 3D MODEL'}</span>
      </button>
    </div>
  );
};
