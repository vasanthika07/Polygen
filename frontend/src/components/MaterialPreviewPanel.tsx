import React, { useState } from 'react';
import { useStore, PBR_PRESETS } from '../store/useStore';
import { materialsApi, type MaterialEvaluationResponse } from '../services/api';
import {
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Zap,
  ShieldCheck,
  X
} from 'lucide-react';

interface MaterialPreviewPanelProps {
  onClose?: () => void;
  className?: string;
}

export const MaterialPreviewPanel: React.FC<MaterialPreviewPanelProps> = ({
  onClose,
  className = "",
}) => {
  const { pbrSettings, updatePBRSettings, applyPBRPreset, addNotification } = useStore();
  const [evalPrompt, setEvalPrompt] = useState<string>('');
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [evaluationResult, setEvaluationResult] = useState<MaterialEvaluationResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'presets' | 'parameters' | 'ai_eval'>('presets');

  const handlePresetSelect = (presetKey: string) => {
    applyPBRPreset(presetKey);
    const preset = PBR_PRESETS[presetKey];
    addNotification({
      title: 'PBR Preset Applied',
      message: `Applied "${preset?.name || presetKey}" with glTF 2.0 physics parameters.`,
      type: 'info',
    });
  };

  const handleEvaluatePrompt = async () => {
    if (!evalPrompt.trim()) return;
    setIsEvaluating(true);
    try {
      const response = await materialsApi.evaluate({ prompt: evalPrompt });
      setEvaluationResult(response.data);

      const params = response.data.gltf_pbr_parameters;
      // Convert RGBA [r, g, b, a] to hex
      const r = Math.round(params.base_color_factor[0] * 255).toString(16).padStart(2, '0');
      const g = Math.round(params.base_color_factor[1] * 255).toString(16).padStart(2, '0');
      const b = Math.round(params.base_color_factor[2] * 255).toString(16).padStart(2, '0');
      const hexColor = `#${r}${g}${b}`;

      const er = Math.round(params.emissive_factor[0] * 255).toString(16).padStart(2, '0');
      const eg = Math.round(params.emissive_factor[1] * 255).toString(16).padStart(2, '0');
      const eb = Math.round(params.emissive_factor[2] * 255).toString(16).padStart(2, '0');
      const hexEmissive = `#${er}${eg}${eb}`;

      updatePBRSettings({
        name: params.name,
        materialClass: params.material_class,
        baseColor: hexColor,
        baseColorOpacity: params.base_color_factor[3] ?? 1.0,
        metallic: params.metallic_factor,
        roughness: params.roughness_factor,
        normalScale: params.normal_scale,
        aoIntensity: params.occlusion_strength,
        emissiveColor: hexEmissive,
        emissiveIntensity: params.emissive_intensity,
        alphaMode: params.alpha_mode,
        alphaCutoff: params.alpha_cutoff,
        doubleSided: params.double_sided,
      });

      addNotification({
        title: 'PBR Evaluated Successfully',
        message: `Classified as ${response.data.classification.material_class} (Confidence: ${Math.round(response.data.classification.confidence * 100)}%)`,
        type: 'success',
      });
    } catch (err: any) {
      addNotification({
        title: 'Evaluation Failed',
        message: err.response?.data?.detail || 'Could not evaluate material properties.',
        type: 'error',
      });
    } finally {
      setIsEvaluating(false);
    }
  };

  const isCompliant =
    pbrSettings.metallic >= 0 &&
    pbrSettings.metallic <= 1 &&
    pbrSettings.roughness >= 0 &&
    pbrSettings.roughness <= 1;

  return (
    <div
      className={`bg-slate-900/95 backdrop-blur-2xl border border-slate-800 rounded-3xl p-5 shadow-2xl flex flex-col gap-4 text-slate-200 z-30 max-h-[85vh] overflow-y-auto ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-blue-600/20 border border-blue-500/30 rounded-xl text-blue-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <span>PBR Material System</span>
              <span className="text-[10px] font-mono px-2 py-0.5 bg-blue-950 text-blue-300 border border-blue-800/60 rounded-full">
                glTF 2.0
              </span>
            </h2>
            <p className="text-[11px] text-slate-400">
              Physically Based Rendering (Metallic-Roughness Standard)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
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
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
        <button
          onClick={() => setActiveTab('presets')}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all ${
            activeTab === 'presets'
              ? 'bg-blue-600 text-white shadow-md'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Physical Presets
        </button>
        <button
          onClick={() => setActiveTab('parameters')}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all ${
            activeTab === 'parameters'
              ? 'bg-blue-600 text-white shadow-md'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          PBR Sliders
        </button>
        <button
          onClick={() => setActiveTab('ai_eval')}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all ${
            activeTab === 'ai_eval'
              ? 'bg-blue-600 text-white shadow-md'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Prompt Classifier
        </button>
      </div>

      {/* TAB 1: PRESETS */}
      {activeTab === 'presets' && (
        <div className="flex flex-col gap-3">
          <span className="text-[11px] text-slate-400 font-medium">
            Select calibrated physical materials:
          </span>
          <div className="grid grid-cols-2 gap-2.5">
            {Object.entries(PBR_PRESETS).map(([key, preset]) => {
              const isSelected = pbrSettings.name === preset.name;
              return (
                <button
                  key={key}
                  onClick={() => handlePresetSelect(key)}
                  className={`p-3 rounded-2xl border text-left transition-all relative overflow-hidden flex flex-col justify-between gap-2 ${
                    isSelected
                      ? 'bg-blue-900/30 border-blue-500 text-white shadow-lg shadow-blue-500/10 ring-1 ring-blue-500'
                      : 'bg-slate-950/70 border-slate-800/80 hover:border-slate-700 text-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div
                      className="w-4 h-4 rounded-full border border-white/20 shadow-inner"
                      style={{ backgroundColor: preset.baseColor }}
                    />
                    <span className="text-[10px] font-mono text-slate-400 uppercase">
                      {preset.materialClass.split('_')[0]}
                    </span>
                  </div>

                  <div>
                    <div className="font-semibold text-xs text-white">{preset.name}</div>
                    <div className="text-[10px] text-slate-400 flex items-center gap-2 mt-0.5">
                      <span>M: {preset.metallic.toFixed(2)}</span>
                      <span>•</span>
                      <span>R: {preset.roughness.toFixed(2)}</span>
                    </div>
                  </div>

                  {preset.emissiveIntensity > 0 && (
                    <div className="flex items-center gap-1 text-[9px] text-amber-400">
                      <Zap className="w-2.5 h-2.5" />
                      <span>Emissive {preset.emissiveIntensity}x</span>
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 2: PARAMETERS / SLIDERS */}
      {activeTab === 'parameters' && (
        <div className="flex flex-col gap-3.5">
          {/* Base Color Picker */}
          <div>
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="text-slate-300 font-medium">Base Color Factor (Albedo)</span>
              <span className="font-mono text-blue-400 text-[11px]">{pbrSettings.baseColor}</span>
            </div>
            <div className="flex items-center gap-3">
              <input
                type="color"
                value={pbrSettings.baseColor}
                onChange={(e) => updatePBRSettings({ baseColor: e.target.value })}
                className="w-10 h-9 rounded-xl border border-slate-700 bg-transparent cursor-pointer p-0.5"
              />
              <input
                type="text"
                value={pbrSettings.baseColor}
                onChange={(e) => updatePBRSettings({ baseColor: e.target.value })}
                className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          {/* Metallic Factor */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-300 font-medium">Metallic Factor (Conductor)</span>
              <span className="font-mono text-cyan-400 text-[11px]">
                {pbrSettings.metallic.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min={0.0}
              max={1.0}
              step={0.01}
              value={pbrSettings.metallic}
              onChange={(e) => updatePBRSettings({ metallic: parseFloat(e.target.value) })}
              className="w-full accent-cyan-500"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-0.5">
              <span>0.0 Dielectric</span>
              <span>1.0 Full Metal</span>
            </div>
          </div>

          {/* Roughness Factor */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-300 font-medium">Roughness Factor (GGX Microfacets)</span>
              <span className="font-mono text-cyan-400 text-[11px]">
                {pbrSettings.roughness.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min={0.0}
              max={1.0}
              step={0.01}
              value={pbrSettings.roughness}
              onChange={(e) => updatePBRSettings({ roughness: parseFloat(e.target.value) })}
              className="w-full accent-cyan-500"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-0.5">
              <span>0.0 Mirror Gloss</span>
              <span>1.0 Matte Diffuse</span>
            </div>
          </div>

          {/* Normal Map Scale */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-300 font-medium">Normal Map Tangent Scale</span>
              <span className="font-mono text-indigo-400 text-[11px]">
                {pbrSettings.normalScale.toFixed(2)}x
              </span>
            </div>
            <input
              type="range"
              min={0.0}
              max={2.0}
              step={0.05}
              value={pbrSettings.normalScale}
              onChange={(e) => updatePBRSettings({ normalScale: parseFloat(e.target.value) })}
              className="w-full accent-indigo-500"
            />
          </div>

          {/* Ambient Occlusion Strength */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-300 font-medium">Ambient Occlusion Strength (ORM)</span>
              <span className="font-mono text-slate-400 text-[11px]">
                {pbrSettings.aoIntensity.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min={0.0}
              max={1.0}
              step={0.05}
              value={pbrSettings.aoIntensity}
              onChange={(e) => updatePBRSettings({ aoIntensity: parseFloat(e.target.value) })}
              className="w-full accent-blue-500"
            />
          </div>

          {/* Emissive Controls */}
          <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-2xl flex flex-col gap-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-white flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                <span>Emissive Radiation</span>
              </span>
              <span className="text-[10px] font-mono text-amber-400">
                {pbrSettings.emissiveIntensity.toFixed(1)}x
              </span>
            </div>

            <div className="flex items-center gap-3">
              <input
                type="color"
                value={pbrSettings.emissiveColor}
                onChange={(e) => updatePBRSettings({ emissiveColor: e.target.value })}
                className="w-9 h-8 rounded-lg border border-slate-700 bg-transparent cursor-pointer p-0.5"
              />
              <input
                type="range"
                min={0.0}
                max={5.0}
                step={0.1}
                value={pbrSettings.emissiveIntensity}
                onChange={(e) =>
                  updatePBRSettings({ emissiveIntensity: parseFloat(e.target.value) })
                }
                className="flex-1 accent-amber-500"
              />
            </div>
          </div>

          {/* Alpha Mode & Cutoff */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] text-slate-400 block mb-1">Alpha Mode</label>
              <select
                value={pbrSettings.alphaMode}
                onChange={(e) => updatePBRSettings({ alphaMode: e.target.value as any })}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
              >
                <option value="OPAQUE">OPAQUE</option>
                <option value="MASK">MASK</option>
                <option value="BLEND">BLEND</option>
              </select>
            </div>

            <div className="flex items-center gap-2 pt-5">
              <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300">
                <input
                  type="checkbox"
                  checked={pbrSettings.doubleSided}
                  onChange={(e) => updatePBRSettings({ doubleSided: e.target.checked })}
                  className="rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-0"
                />
                <span>Double-Sided</span>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: AI EVALUATION & PROMPT CLASSIFIER */}
      {activeTab === 'ai_eval' && (
        <div className="flex flex-col gap-3">
          <p className="text-xs text-slate-400">
            Evaluate text descriptions into glTF 2.0 PBR materials:
          </p>

          <div className="flex gap-2">
            <input
              type="text"
              placeholder="e.g. A rusted broadsword with glowing sapphire..."
              value={evalPrompt}
              onChange={(e) => setEvalPrompt(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleEvaluatePrompt()}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
            />
            <button
              onClick={handleEvaluatePrompt}
              disabled={isEvaluating || !evalPrompt.trim()}
              className="px-3 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md shadow-blue-500/20"
            >
              {isEvaluating ? (
                <span className="animate-spin">⌛</span>
              ) : (
                <Sparkles className="w-3.5 h-3.5" />
              )}
              <span>Analyze</span>
            </button>
          </div>

          {/* Quick Examples */}
          <div className="flex flex-wrap gap-1.5">
            {[
              'Rusted medieval broadsword',
              'Glowing sapphire gem',
              'Carved rustic oak wood',
              'Ancient granite moss stone',
            ].map((ex) => (
              <button
                key={ex}
                onClick={() => setEvalPrompt(ex)}
                className="text-[10px] px-2 py-1 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-400 hover:text-slate-200 transition-colors"
              >
                {ex}
              </button>
            ))}
          </div>

          {/* AI Result Card */}
          {evaluationResult && (
            <div className="p-3 bg-slate-950 border border-slate-800 rounded-2xl flex flex-col gap-2 mt-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>{evaluationResult.classification.material_class}</span>
                </span>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-2 py-0.5 rounded-full">
                  Score: {Math.round(evaluationResult.classification.confidence * 100)}%
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-300">
                <div className="p-2 bg-slate-900 rounded-lg">
                  <span className="text-slate-500 block">Conductor Score:</span>
                  <span className="font-mono text-cyan-400 font-semibold">
                    {evaluationResult.classification.conductor_score.toFixed(2)}
                  </span>
                </div>
                <div className="p-2 bg-slate-900 rounded-lg">
                  <span className="text-slate-500 block">Dielectric Score:</span>
                  <span className="font-mono text-cyan-400 font-semibold">
                    {evaluationResult.classification.dielectric_score.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* glTF 2.0 Verification Badge */}
      <div className="border-t border-slate-800/80 pt-3 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          {isCompliant ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          )}
          <span className="text-[11px] text-slate-300 font-medium">
            {isCompliant ? 'Khronos glTF 2.0 Compliant' : 'Value Warning'}
          </span>
        </div>
        <span className="text-[10px] font-mono text-slate-500">ORM 3-Channel Packed</span>
      </div>
    </div>
  );
};
