import React, { useState } from 'react';
import { useStore } from '../store/useStore';
import { 
  Sparkles, 
  Wand2, 
  Box, 
  Shield, 
  Bot, 
  Home, 
  Trees, 
  Layers
} from 'lucide-react';

interface InspirationPrompt {
  id: string;
  category: 'weapons' | 'props' | 'scifi' | 'nature';
  title: string;
  prompt: string;
  style: string;
  polys: number;
  previewSampleUrl: string;
}

const INSPIRATION_ITEMS: InspirationPrompt[] = [
  {
    id: 'insp_1',
    category: 'weapons',
    title: 'Rusted Medieval Broadsword',
    prompt: 'A rusted medieval broadsword with a glowing blue sapphire in the hilt.',
    style: 'medieval fantasy',
    polys: 10000,
    previewSampleUrl: '/models/sample_sword.glb'
  },
  {
    id: 'insp_2',
    category: 'props',
    title: 'Rustic Oak Wooden Chair',
    prompt: 'A rustic oak wooden chair with carved armrests.',
    style: 'realistic',
    polys: 8000,
    previewSampleUrl: '/models/sample_chair.glb'
  },
  {
    id: 'insp_3',
    category: 'props',
    title: 'Weathered Pirate Treasure Chest',
    prompt: 'A weathered pirate treasure chest reinforced with brass bands and padlock.',
    style: 'stylized',
    polys: 12000,
    previewSampleUrl: '/models/sample_chair.glb'
  },
  {
    id: 'insp_4',
    category: 'scifi',
    title: 'Futuristic Battle Robot',
    prompt: 'A futuristic metallic battle robot with neon green visor.',
    style: 'sci-fi',
    polys: 15000,
    previewSampleUrl: '/models/sample_robot.glb'
  },
  {
    id: 'insp_5',
    category: 'nature',
    title: 'Ancient Mossy Stone Sculpture',
    prompt: 'An ancient carved stone sculpture covered in moss.',
    style: 'realistic',
    polys: 10000,
    previewSampleUrl: '/models/sample_sculpture.glb'
  },
  {
    id: 'insp_6',
    category: 'weapons',
    title: 'Damascus Steel Dagger',
    prompt: 'An ornate Damascus steel ceremonial dagger with gold inlays and leather scabbard.',
    style: 'realistic',
    polys: 8000,
    previewSampleUrl: '/models/sample_sword.glb'
  },
];

export const Generate: React.FC = () => {
  const { navigate, setGenerationPrompt, setActiveAsset } = useStore();
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'weapons' | 'props' | 'scifi' | 'nature'>('all');

  const filteredItems = selectedCategory === 'all'
    ? INSPIRATION_ITEMS
    : INSPIRATION_ITEMS.filter((item) => item.category === selectedCategory);

  const handleUsePrompt = (prompt: string) => {
    setGenerationPrompt(prompt);
    navigate('workspace');
  };

  const handlePreviewSample = (item: InspirationPrompt) => {
    setActiveAsset({
      asset_id: item.id,
      asset_name: item.title,
      glb_url: item.previewSampleUrl,
      polygon_count: item.polys,
      file_size: 3500000,
      created_at: new Date().toISOString()
    });
    navigate('viewer');
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 lg:px-8 py-8 flex flex-col gap-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Curated Prompts & Preset Vault</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Asset Inspiration Hub
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
            Explore battle-tested prompts tuned for optimal topology, clean UV islands, and realistic PBR texture synthesis.
          </p>
        </div>

        <button
          onClick={() => navigate('workspace')}
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-blue-500/25 transition-all self-start md:self-auto"
        >
          <Wand2 className="w-4 h-4" />
          <span>Custom Prompt Studio</span>
        </button>
      </div>

      {/* Category Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        {[
          { id: 'all', label: 'All Categories', icon: Sparkles },
          { id: 'weapons', label: 'Weapons & Armor', icon: Shield },
          { id: 'props', label: 'Props & Furniture', icon: Home },
          { id: 'scifi', label: 'Sci-Fi & Cyberpunk', icon: Bot },
          { id: 'nature', label: 'Nature & Sculptures', icon: Trees },
        ].map((cat) => {
          const Icon = cat.icon;
          const isActive = selectedCategory === cat.id;

          return (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium whitespace-nowrap transition-all ${
                isActive
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                  : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{cat.label}</span>
            </button>
          );
        })}
      </div>

      {/* Inspiration Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredItems.map((item) => (
          <div
            key={item.id}
            className="bg-slate-900/80 border border-slate-800/80 hover:border-slate-700 rounded-2xl p-5 shadow-xl flex flex-col justify-between group transition-all"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 font-semibold">
                  {item.style}
                </span>
                <span className="text-xs text-slate-500 flex items-center gap-1 font-mono">
                  <Layers className="w-3.5 h-3.5 text-cyan-400" />
                  {item.polys.toLocaleString()} polys
                </span>
              </div>

              <h3 className="text-base font-bold text-white mb-2 group-hover:text-blue-400 transition-colors">
                {item.title}
              </h3>

              <p className="text-xs text-slate-300 bg-slate-950/70 p-3 rounded-xl border border-slate-800/70 leading-relaxed italic mb-4">
                "{item.prompt}"
              </p>
            </div>

            <div className="flex items-center gap-2 pt-3 border-t border-slate-800/80">
              <button
                onClick={() => handleUsePrompt(item.prompt)}
                className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl shadow-md transition-all"
              >
                <Wand2 className="w-3.5 h-3.5" />
                <span>Use in Studio</span>
              </button>
              <button
                onClick={() => handlePreviewSample(item)}
                className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-xl text-xs font-medium transition-colors"
                title="Preview Sample in 3D"
              >
                <Box className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
