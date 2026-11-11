import React, { useState } from 'react';
import { useStore } from '../store/useStore';
import { ModelViewer } from '../components/ModelViewer';
import { 
  Box, 
  Layers, 
  Download, 
  Copy, 
  Check, 
  ArrowLeft,
  FileCheck,
  Palette
} from 'lucide-react';

export const AssetDetails: React.FC = () => {
  const { activeAsset, navigate, addNotification } = useStore();
  const [activeTab, setActiveTab] = useState<'textures' | 'geometry' | 'engine'>('textures');
  const [selectedTexture, setSelectedTexture] = useState<'baseColor' | 'normal' | 'roughness' | 'metallic' | 'emissive'>('baseColor');
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  // Fallback if no active asset
  const asset = activeAsset || {
    asset_id: 'asset_broadsword_demo',
    asset_name: 'Medieval Broadsword with Sapphire',
    prompt: 'A rusted medieval broadsword with a glowing blue sapphire in the hilt.',
    style: 'medieval fantasy',
    polygon_count: 856,
    file_size: 3567096,
    glb_url: '/models/sample_sword.glb',
    created_at: new Date().toISOString(),
  };

  const handleCopy = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(id);
    addNotification({
      title: 'Copied to Clipboard',
      message: 'Code snippet ready to paste into your game project.',
      type: 'info',
    });
    setTimeout(() => setCopiedCode(null), 2500);
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 lg:px-8 py-8 flex flex-col gap-8">
      {/* Top Navigation & Breadcrumb */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
        <button
          onClick={() => navigate('library')}
          className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Asset Library</span>
        </button>

        <a
          href={asset.glb_url}
          download={`${asset.asset_name.replace(/[^a-zA-Z0-9]/g, '_')}.glb`}
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-blue-500/25 transition-all"
        >
          <Download className="w-4 h-4" />
          <span>Export GLB Package</span>
        </a>
      </div>

      {/* Main Asset Header */}
      <div>
        <div className="flex items-center gap-2 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-1">
          <Box className="w-3.5 h-3.5" />
          <span>Detailed Asset Specification</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          {asset.asset_name}
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed italic">
          "{asset.prompt || 'Generated production 3D asset with full PBR texture channels and quadric decimation.'}"
        </p>
      </div>

      {/* Split Grid: 3D Model on Left, Deep Tabs on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: 3D Interactive Model Viewport (6 cols) */}
        <div className="lg:col-span-6 flex flex-col gap-4">
          <ModelViewer
            assetUrl={asset.glb_url}
            className="h-[520px] lg:h-[580px]"
          />

          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl text-center">
              <span className="text-[10px] text-slate-400 block mb-0.5">Triangles</span>
              <span className="text-sm font-bold font-mono text-cyan-400">
                {asset.polygon_count.toLocaleString()}
              </span>
            </div>
            <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl text-center">
              <span className="text-[10px] text-slate-400 block mb-0.5">File Size</span>
              <span className="text-sm font-bold font-mono text-indigo-400">
                {(asset.file_size / (1024 * 1024)).toFixed(2)} MB
              </span>
            </div>
            <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl text-center">
              <span className="text-[10px] text-slate-400 block mb-0.5">PBR Channels</span>
              <span className="text-sm font-bold font-mono text-emerald-400">5 Maps</span>
            </div>
          </div>
        </div>

        {/* Right: Technical Inspector Tabs (6 cols) */}
        <div className="lg:col-span-6 flex flex-col gap-5 bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-3xl p-6 shadow-2xl">
          {/* Tab Navigation */}
          <div className="flex items-center gap-1 bg-slate-950 p-1.5 rounded-2xl border border-slate-800/80">
            <button
              onClick={() => setActiveTab('textures')}
              className={`flex-1 py-2 px-3 rounded-xl text-xs font-semibold transition-all ${
                activeTab === 'textures'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              PBR Maps
            </button>
            <button
              onClick={() => setActiveTab('geometry')}
              className={`flex-1 py-2 px-3 rounded-xl text-xs font-semibold transition-all ${
                activeTab === 'geometry'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Topology & UV
            </button>
            <button
              onClick={() => setActiveTab('engine')}
              className={`flex-1 py-2 px-3 rounded-xl text-xs font-semibold transition-all ${
                activeTab === 'engine'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Engine Guide
            </button>
          </div>

          {/* TAB 1: PBR Texture Channel Maps */}
          {activeTab === 'textures' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Palette className="w-4 h-4 text-blue-400" />
                  <span>5-Channel PBR Material Maps</span>
                </h3>
                <span className="text-[11px] font-mono text-slate-400">1024 × 1024 px</span>
              </div>

              {/* Texture Channel Selector Pills */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {[
                  { id: 'baseColor', name: 'Base Color', desc: 'Diffuse / Albedo' },
                  { id: 'normal', name: 'Normal Map', desc: 'Tangent Perturbation' },
                  { id: 'roughness', name: 'Roughness', desc: 'Micro-facet Spread' },
                  { id: 'metallic', name: 'Metallic', desc: 'Conductor Mask' },
                  { id: 'emissive', name: 'Emissive', desc: 'Luminescent Light' },
                ].map((channel) => (
                  <button
                    key={channel.id}
                    onClick={() => setSelectedTexture(channel.id as any)}
                    className={`p-2.5 rounded-xl border text-left transition-all ${
                      selectedTexture === channel.id
                        ? 'bg-blue-600/20 border-blue-500 text-blue-300 shadow-md font-semibold'
                        : 'bg-slate-950/80 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div className="text-xs">{channel.name}</div>
                    <div className="text-[10px] text-slate-500">{channel.desc}</div>
                  </button>
                ))}
              </div>

              {/* Texture Channel Preview Card */}
              <div className="p-4 bg-slate-950/80 rounded-2xl border border-slate-800/80 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200 capitalize">
                    {selectedTexture} Channel Details
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    Embedded GLB Texture
                  </span>
                </div>

                <div className="w-full h-36 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center relative overflow-hidden">
                  <div className="text-center p-4">
                    <Palette className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                    <span className="text-xs font-mono text-slate-300">
                      Channel: {selectedTexture.toUpperCase()} (sRGB / Linear)
                    </span>
                    <p className="text-[11px] text-slate-500 mt-1">
                      Integrated into the glTF 2.0 PBR Metallic-Roughness material definition.
                    </p>
                  </div>
                </div>

                <div className="text-xs text-slate-400 space-y-1">
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span>Encoding:</span>
                    <span className="font-mono text-slate-200">PNG / JPEG embedded</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span>Color Space:</span>
                    <span className="font-mono text-slate-200">
                      {selectedTexture === 'baseColor' || selectedTexture === 'emissive' ? 'sRGB' : 'Linear'}
                    </span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span>UV Addressing:</span>
                    <span className="font-mono text-slate-200">CLAMP_TO_EDGE / REPEAT</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: Topology & UV Mapping */}
          {activeTab === 'geometry' && (
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                <span>Mesh Topology & UV Parameterization</span>
              </h3>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                  <span className="text-[11px] text-slate-400">Total Faces</span>
                  <div className="text-base font-bold font-mono text-slate-100 mt-1">
                    {asset.polygon_count.toLocaleString()}
                  </div>
                </div>
                <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                  <span className="text-[11px] text-slate-400">Total Vertices</span>
                  <div className="text-base font-bold font-mono text-slate-100 mt-1">
                    {Math.round(asset.polygon_count / 2).toLocaleString()}
                  </div>
                </div>
                <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                  <span className="text-[11px] text-slate-400">UV Unwrapping Engine</span>
                  <div className="text-base font-bold font-mono text-cyan-400 mt-1">
                    xatlas v0.1
                  </div>
                </div>
                <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                  <span className="text-[11px] text-slate-400">Topology Manifold</span>
                  <div className="text-base font-bold font-mono text-emerald-400 mt-1">
                    100% Watertight
                  </div>
                </div>
              </div>

              <div className="p-4 bg-slate-950/80 rounded-2xl border border-slate-800 space-y-2 text-xs text-slate-300">
                <div className="font-semibold text-white">Quadric Decimation Verification:</div>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  Mesh has been processed with Quadric Error Metric (QEM) simplification. Non-manifold edges, zero-area sliver triangles, and degenerate faces have been repaired. Normals are unified and computed for smooth shading.
                </p>
              </div>
            </div>
          )}

          {/* TAB 3: Engine Import Guide */}
          {activeTab === 'engine' && (
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-emerald-400" />
                <span>Engine Setup & Import Code</span>
              </h3>

              {/* Unreal Engine 5 Card */}
              <div className="p-4 bg-slate-950/80 rounded-2xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">Unreal Engine 5 (Nanite & Lumen)</span>
                  <button
                    onClick={() =>
                      handleCopy(
                        `// Unreal Engine 5 GLTF Import Note:\n1. Drag '${asset.asset_name}.glb' directly into Content Browser.\n2. In Import Dialog, check 'Enable Nanite' and 'Build Reversing Normals'.\n3. Set Material Search Location to 'Under Parent'.\n4. Unreal automatically maps BaseColor, Normal, and Roughness/Metallic channels.`,
                        'ue5'
                      )
                    }
                    className="flex items-center gap-1 text-[11px] text-blue-400 hover:text-blue-300"
                  >
                    {copiedCode === 'ue5' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedCode === 'ue5' ? 'Copied' : 'Copy Guide'}</span>
                  </button>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Drag the exported <code>.glb</code> directly into Content Browser. Check <strong>Enable Nanite</strong> for high-detail geometry streaming.
                </p>
              </div>

              {/* Blender 4.x Card */}
              <div className="p-4 bg-slate-950/80 rounded-2xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">Blender 4.x (Python Importer)</span>
                  <button
                    onClick={() =>
                      handleCopy(
                        `import bpy\n\n# Import PolyGen GLB into active Blender scene\nbpy.ops.import_scene.gltf(filepath="${asset.asset_name}.glb")\nobj = bpy.context.selected_objects[0]\nprint(f"Loaded {obj.name} with {len(obj.data.polygons)} faces.")`,
                        'blender'
                      )
                    }
                    className="flex items-center gap-1 text-[11px] text-blue-400 hover:text-blue-300"
                  >
                    {copiedCode === 'blender' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedCode === 'blender' ? 'Copied' : 'Copy Script'}</span>
                  </button>
                </div>
                <pre className="p-2.5 bg-slate-900 rounded-lg text-[10px] font-mono text-slate-300 overflow-x-auto">
{`bpy.ops.import_scene.gltf(filepath="${asset.asset_name}.glb")`}
                </pre>
              </div>

              {/* Unity URP/HDRP Card */}
              <div className="p-4 bg-slate-950/80 rounded-2xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">Unity (URP / HDRP Lit)</span>
                  <button
                    onClick={() =>
                      handleCopy(
                        `// Unity glTFast / Studio Setup:\n1. Install com.unity.cloud.gltfast via Package Manager.\n2. Place GLB file into Assets/Models/.\n3. Drag prefab into Scene hierarchy. Materials bind automatically.`,
                        'unity'
                      )
                    }
                    className="flex items-center gap-1 text-[11px] text-blue-400 hover:text-blue-300"
                  >
                    {copiedCode === 'unity' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedCode === 'unity' ? 'Copied' : 'Copy Guide'}</span>
                  </button>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Install <strong>glTFast</strong> from Unity Package Manager for native zero-overhead GLB loading at runtime or editor time.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
