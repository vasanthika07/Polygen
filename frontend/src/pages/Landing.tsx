import React, { useState } from 'react';
import { useStore } from '../store/useStore';
import { ModelViewer } from '../components/ModelViewer';
import { 
  Sparkles, 
  Wand2, 
  Box, 
  Layers, 
  Cpu, 
  Download, 
  Zap, 
  Flame
} from 'lucide-react';

export const Landing: React.FC = () => {
  const { navigate, setGenerationPrompt } = useStore();
  const [demoPrompt, setDemoPrompt] = useState('A rusted medieval broadsword with a glowing blue sapphire in the hilt.');

  const samplePrompts = [
    { label: 'Medieval Broadsword', prompt: 'A rusted medieval broadsword with a glowing blue sapphire in the hilt.' },
    { label: 'Rustic Oak Chair', prompt: 'A rustic oak wooden chair with carved armrests.' },
    { label: 'Battle Robot', prompt: 'A futuristic metallic battle robot with neon green visor.' },
    { label: 'Mossy Sculpture', prompt: 'An ancient carved stone sculpture covered in moss.' }
  ];

  const handleLaunchWithPrompt = (promptText: string) => {
    setGenerationPrompt(promptText);
    navigate('workspace');
  };

  return (
    <div className="w-full min-h-screen bg-[#070a13] text-slate-100 flex flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 px-4 sm:px-6 lg:px-8 border-b border-slate-800/80">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(59,130,246,0.15),rgba(255,255,255,0))] pointer-events-none" />

        <div className="max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-12 relative z-10">
          {/* Hero Left Copy */}
          <div className="flex-1 flex flex-col gap-6 text-center lg:text-left">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold self-center lg:self-start">
              <Sparkles className="w-4 h-4" />
              <span>Next-Gen Spatial Computing & Generative AI</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-tight">
              Turn Text into <span className="bg-gradient-to-r from-blue-400 via-indigo-400 to-violet-400 bg-clip-text text-transparent">Production 3D</span> Assets in Seconds
            </h1>

            <p className="text-base sm:text-lg text-slate-300 max-w-2xl leading-relaxed">
              PolyGen automatically turns natural-language descriptions into fully textured, UV-unwrapped, and decimated 3D meshes ready for Unreal Engine 5, Unity, and Blender.
            </p>

            {/* Quick Interactive Prompt Playground */}
            <div className="p-2 sm:p-2.5 bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl shadow-2xl flex flex-col sm:flex-row gap-2">
              <input
                type="text"
                value={demoPrompt}
                onChange={(e) => setDemoPrompt(e.target.value)}
                placeholder="Describe your 3D asset..."
                className="flex-1 bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
              <button
                onClick={() => handleLaunchWithPrompt(demoPrompt)}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 hover:opacity-90 text-white font-semibold text-sm rounded-xl shadow-lg shadow-blue-500/25 transition-all whitespace-nowrap"
              >
                <Wand2 className="w-4 h-4" />
                <span>Generate 3D</span>
              </button>
            </div>

            {/* Prompt presets */}
            <div className="flex items-center gap-2 flex-wrap justify-center lg:justify-start">
              <span className="text-xs text-slate-400 font-medium">Try:</span>
              {samplePrompts.map((item) => (
                <button
                  key={item.label}
                  onClick={() => {
                    setDemoPrompt(item.prompt);
                    handleLaunchWithPrompt(item.prompt);
                  }}
                  className="text-xs px-3 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition-colors"
                >
                  {item.label}
                </button>
              ))}
            </div>

            {/* Metrics Trust Badges */}
            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-800/60 max-w-lg mx-auto lg:mx-0 text-left">
              <div>
                <div className="text-2xl font-bold text-white font-mono">60–120s</div>
                <div className="text-xs text-slate-400">Target Generation</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-white font-mono">100%</div>
                <div className="text-xs text-slate-400">PBR Materials</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-white font-mono">GLB 2.0</div>
                <div className="text-xs text-slate-400">Game-Ready Export</div>
              </div>
            </div>
          </div>

          {/* Hero Right: Real Interactive 3D Model Viewport */}
          <div className="flex-1 w-full max-w-xl">
            <div className="relative">
              <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-violet-600 rounded-3xl blur-xl opacity-30 group-hover:opacity-100 transition duration-1000 group-hover:duration-200" />
              <div className="relative">
                <ModelViewer
                  assetUrl="/models/sample_sword.glb"
                  className="h-[460px] sm:h-[500px]"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Pillars */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-bold uppercase tracking-wider text-blue-400 mb-2">Engine Architecture</h2>
          <h3 className="text-3xl sm:text-4xl font-extrabold text-white">
            Built for Game Developers & 3D Artists
          </h3>
          <p className="text-slate-400 text-sm sm:text-base mt-3">
            Every step of PolyGen transforms raw neural representations into topologically sound, UV-parameterized, and game-engine-compliant models.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-2xl flex flex-col gap-3">
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center">
              <Wand2 className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-bold text-white">Prompt Understanding</h4>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              Extracts style, physical material types (steel, wood, stone, brass), and geometric characteristics from natural language inputs with deterministic semantic parsing.
            </p>
          </div>

          <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-2xl flex flex-col gap-3">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
              <Box className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-bold text-white">Neural 3D Synthesis</h4>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              Synthesizes implicit 3D representations using Shap-E diffusion fields or procedural volumetric meshes, extracting watertight polygonal geometry via marching cubes.
            </p>
          </div>

          <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-2xl flex flex-col gap-3">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center">
              <Layers className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-bold text-white">Conformal UV Unwrapping</h4>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              Deploys the industrial xatlas parameterizer to calculate non-overlapping UV atlas charts with minimal distortion and maximized texture density.
            </p>
          </div>

          <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-2xl flex flex-col gap-3">
            <div className="w-12 h-12 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400 flex items-center justify-center">
              <Flame className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-bold text-white">Complete PBR Material Synthesis</h4>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              Generates synchronized 5-channel PBR texture maps: Base Color (Albedo), Normal (Perturbation), Roughness (Microsurface), Metallic (Conductivity), and Emissive.
            </p>
          </div>

          <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-2xl flex flex-col gap-3">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
              <Cpu className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-bold text-white">Quadric Error Decimation</h4>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              Enforces your exact polygon budget using quadric error metric reduction, preserving silhouettes, sharp edges, and UV continuity for optimal game frame rates.
            </p>
          </div>

          <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-2xl flex flex-col gap-3">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center">
              <Download className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-bold text-white">Universal Engine Export</h4>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              Exports Khronos-standard GLB binary packages directly importable into Unreal Engine 5 Nanite/Lumen, Unity URP/HDRP, and Blender 4.x with zero manual hookups.
            </p>
          </div>
        </div>
      </section>

      {/* 8-Stage Pipeline Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-950/60 border-y border-slate-800/80">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h3 className="text-2xl sm:text-3xl font-extrabold text-white">
              Deterministic 8-Stage Pipeline
            </h3>
            <p className="text-slate-400 text-xs sm:text-sm mt-2">
              Every job is managed as a state machine streamed over WebSockets directly to your browser.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            {[
              { num: '01', title: 'Prompt Parsing', desc: 'Material & style extract' },
              { num: '02', title: 'Neural 3D', desc: 'Marching cubes mesh' },
              { num: '03', title: 'Mesh Cleaning', desc: 'Non-manifold repair' },
              { num: '04', title: 'UV Mapping', desc: 'xatlas chart packing' },
              { num: '05', title: 'Texture Synth', desc: '5 PBR texture maps' },
              { num: '06', title: 'QEM Decimation', desc: 'Poly budget enforce' },
              { num: '07', title: 'GLB Packing', desc: 'glTF 2.0 binary write' },
              { num: '08', title: '3D Verified', desc: 'Ready for viewport' },
            ].map((st) => (
              <div key={st.num} className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl flex flex-col items-center text-center">
                <span className="text-xs font-mono font-bold text-blue-400 mb-1">{st.num}</span>
                <span className="text-xs font-semibold text-slate-200">{st.title}</span>
                <span className="text-[10px] text-slate-400 mt-1">{st.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Interactive CTA */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto text-center">
        <div className="p-8 sm:p-12 rounded-3xl bg-gradient-to-r from-blue-900/30 via-indigo-900/30 to-violet-900/30 border border-blue-500/30 shadow-2xl flex flex-col items-center gap-6">
          <div className="w-14 h-14 rounded-2xl bg-blue-500/20 text-blue-400 flex items-center justify-center">
            <Zap className="w-7 h-7" />
          </div>

          <h2 className="text-3xl sm:text-4xl font-extrabold text-white">
            Ready to Accelerate Your 3D Workflow?
          </h2>

          <p className="text-slate-300 max-w-xl text-sm sm:text-base leading-relaxed">
            Experience next-generation text-to-3D asset generation today. Launch the studio workspace or explore the sample models library.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-4">
            <button
              onClick={() => navigate('workspace')}
              className="flex items-center gap-2 px-8 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-sm rounded-xl shadow-lg shadow-blue-500/30 transition-all"
            >
              <Wand2 className="w-4 h-4" />
              <span>Launch Generation Studio</span>
            </button>
            <button
              onClick={() => navigate('viewer')}
              className="flex items-center gap-2 px-6 py-3.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-sm rounded-xl transition-all"
            >
              <Box className="w-4 h-4 text-blue-400" />
              <span>Open 3D Model Viewer</span>
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};
