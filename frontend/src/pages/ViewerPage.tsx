import React, { useState } from 'react';
import { useStore } from '../store/useStore';
import { ModelViewer } from '../components/ModelViewer';
import {
  Box,
  Download,
  Sun,
  Sparkles
} from 'lucide-react';

const SAMPLE_MODELS = [
  {
    id: 'sample_sword',
    name: 'Medieval Broadsword',
    description: 'A rusted medieval broadsword with a glowing blue sapphire in the hilt.',
    url: '/models/sample_sword.glb',
    polys: 856,
    vertices: 430,
    size: '3.40 MB',
  },
  {
    id: 'sample_chair',
    name: 'Rustic Oak Wooden Chair',
    description: 'A rustic oak wooden chair with carved armrests.',
    url: '/models/sample_chair.glb',
    polys: 536,
    vertices: 270,
    size: '3.33 MB',
  },
  {
    id: 'sample_robot',
    name: 'Futuristic Battle Robot',
    description: 'A futuristic metallic battle robot with neon green visor.',
    url: '/models/sample_robot.glb',
    polys: 548,
    vertices: 280,
    size: '3.84 MB',
  },
  {
    id: 'sample_sculpture',
    name: 'Ancient Mossy Stone Sculpture',
    description: 'An ancient carved stone sculpture covered in moss.',
    url: '/models/sample_sculpture.glb',
    polys: 5120,
    vertices: 2562,
    size: '3.55 MB',
  },
];

export const ViewerPage: React.FC = () => {
  const {
    activeAsset,
    setActiveAsset,
    assets,
    renderMode,
    setRenderMode,
    environmentPreset,
    setEnvironmentPreset,
    ambientIntensity,
    setAmbientIntensity,
    directionalIntensity,
    setDirectionalIntensity,
    navigate
  } = useStore();

  const [selectedModelId, setSelectedModelId] = useState(
    activeAsset?.asset_id || SAMPLE_MODELS[0].id
  );

  // Combine user assets with sample models for switching
  const allSelectableModels = [
    ...SAMPLE_MODELS.map((m) => ({
      id: m.id,
      name: `[Sample] ${m.name}`,
      url: m.url,
      polys: m.polys,
      size: m.size,
      isSample: true,
    })),
    ...assets.map((a) => ({
      id: a.asset_id,
      name: a.asset_name,
      url: a.glb_url,
      polys: a.polygon_count,
      size: `${(a.file_size / (1024 * 1024)).toFixed(2)} MB`,
      isSample: false,
    })),
  ];

  const currentSelection = allSelectableModels.find((m) => m.id === selectedModelId) || allSelectableModels[0];

  const handleSelectModel = (modelId: string) => {
    setSelectedModelId(modelId);
    const chosen = allSelectableModels.find((m) => m.id === modelId);
    if (chosen) {
      setActiveAsset({
        asset_id: chosen.id,
        asset_name: chosen.name,
        glb_url: chosen.url,
        polygon_count: chosen.polys,
        file_size: 3500000,
        created_at: new Date().toISOString(),
      });
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 lg:px-8 py-8 flex flex-col gap-6">
      {/* Viewport Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Box className="w-3.5 h-3.5" />
            <span>Real-time Interactive 3D Inspection</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            3D Asset Workbench
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Inspect geometry topology, evaluate UV texture maps, adjust lighting environments, and export for game engines.
          </p>
        </div>

        {/* Model Switcher Dropdown */}
        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-400 font-medium whitespace-nowrap">Active Model:</label>
          <select
            value={selectedModelId}
            onChange={(e) => handleSelectModel(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-medium"
          >
            {allSelectableModels.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.polys.toLocaleString()} polys)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Interactive 3D Model Canvas Viewport */}
      <div className="w-full">
        <ModelViewer
          assetUrl={currentSelection.url}
          className="h-[580px] lg:h-[660px]"
        />
      </div>

      {/* Inspection Control Panels Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Panel 1: Material Shading Modes */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col gap-3">
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span>Material & Shading Mode</span>
          </h3>
          <p className="text-xs text-slate-400">
            Switch between full PBR rendering, unlit clay surface, or wireframe wire-mesh:
          </p>
          <div className="grid grid-cols-2 gap-2 mt-1">
            {[
              { id: 'textured', label: 'PBR Textured', desc: 'Diffuse + Normals' },
              { id: 'solid', label: 'Clay Solid', desc: 'Neutral Lambert' },
              { id: 'wireframe', label: 'Wireframe', desc: 'Mesh Edges' },
              { id: 'normals', label: 'Surface Normals', desc: 'RGB Vector Field' },
            ].map((mode) => (
              <button
                key={mode.id}
                onClick={() => setRenderMode(mode.id as any)}
                className={`p-3 rounded-xl border text-left transition-all ${renderMode === mode.id
                    ? 'bg-blue-600 border-blue-500 text-white shadow-md'
                    : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
              >
                <div className="font-semibold text-xs">{mode.label}</div>
                <div className={`text-[10px] mt-0.5 ${renderMode === mode.id ? 'text-blue-100' : 'text-slate-500'}`}>
                  {mode.desc}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Panel 2: Environment & Lighting */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col gap-4">
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Sun className="w-4 h-4 text-amber-400" />
            <span>Lighting & HDRI</span>
          </h3>

          <div>
            <label className="text-[11px] text-slate-400 block mb-1 font-medium">Environment HDRI Map</label>
            <select
              value={environmentPreset}
              onChange={(e) => setEnvironmentPreset(e.target.value as any)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="city">City Daylight</option>
              <option value="studio">Studio Neutral (Even)</option>
              <option value="sunset">Warm Sunset (Golden Hour)</option>
              <option value="warehouse">Industrial Warehouse</option>
              <option value="night">Night Rim Light</option>
            </select>
          </div>

          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs text-slate-300 mb-1">
                <span>Ambient Intensity</span>
                <span className="font-mono text-blue-400">{ambientIntensity}</span>
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
              <div className="flex justify-between text-xs text-slate-300 mb-1">
                <span>Key Light Intensity</span>
                <span className="font-mono text-blue-400">{directionalIntensity}</span>
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
        </div>

        {/* Panel 3: Engine Export & Telemetry */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col justify-between gap-4">
          <div>
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2 mb-3">
              <Download className="w-4 h-4 text-emerald-400" />
              <span>Engine Export Package</span>
            </h3>

            <div className="space-y-2 text-xs text-slate-300 mb-4">
              <div className="flex justify-between py-1 border-b border-slate-800/80">
                <span className="text-slate-400">File Format:</span>
                <span className="font-semibold text-white">GLB (glTF 2.0 Binary)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/80">
                <span className="text-slate-400">Target Polygons:</span>
                <span className="font-mono text-white">{currentSelection.polys.toLocaleString()}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/80">
                <span className="text-slate-400">File Weight:</span>
                <span className="font-mono text-white">{currentSelection.size}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Engine Support:</span>
                <span className="text-emerald-400 font-medium">Unreal / Unity / Blender</span>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <a
              href={currentSelection.url}
              download={`${currentSelection.name.replace(/[^a-zA-Z0-9]/g, '_')}.glb`}
              className="w-full flex items-center justify-center gap-2 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-blue-500/25 transition-all text-center"
            >
              <Download className="w-4 h-4" />
              <span>Download GLB Package</span>
            </a>

            <button
              onClick={() => navigate('asset-details')}
              className="w-full py-2 bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white rounded-xl text-xs font-medium transition-colors"
            >
              View Detailed Asset Specs & PBR Maps
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
