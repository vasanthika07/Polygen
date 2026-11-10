import React, { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import { assetApi } from '../services/api';
import { AssetCard } from '../components/AssetCard';
import { FolderGit2, Search, Wand2, RefreshCw } from 'lucide-react';

export const AssetLibrary: React.FC = () => {
  const { assets, setAssets, setActiveTab } = useStore();
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchAssets = async () => {
    setLoading(true);
    try {
      const res = await assetApi.listAssets();
      setAssets(res.data.items);
    } catch (err) {
      console.error('Failed to load asset library:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, []);

  const filteredAssets = assets.filter((a) =>
    a.asset_name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="w-full max-w-7xl mx-auto px-4 lg:px-8 py-8 flex flex-col gap-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <FolderGit2 className="w-3.5 h-3.5" />
            <span>Generated Asset Repository</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Asset Library
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Browse, inspect, and export your production-ready 3D models with PBR textures.
          </p>
        </div>

        {/* Search & Refresh */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search assets..."
              className="bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 focus:border-blue-500 focus:outline-none w-56 sm:w-64"
            />
          </div>

          <button
            onClick={fetchAssets}
            disabled={loading}
            className="p-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-xl text-slate-300 hover:text-white transition-colors"
            title="Refresh assets"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Grid of Assets */}
      {filteredAssets.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredAssets.map((asset) => (
            <AssetCard key={asset.asset_id} asset={asset} />
          ))}
        </div>
      ) : (
        <div className="w-full py-20 flex flex-col items-center justify-center text-center p-8 bg-slate-900/40 rounded-3xl border border-slate-800/60">
          <div className="w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-4">
            <FolderGit2 className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-semibold text-slate-200 mb-1">
            {search ? 'No matching models found' : 'Your asset library is empty'}
          </h3>
          <p className="text-xs text-slate-400 max-w-sm mb-6">
            {search
              ? 'Try modifying your search query or clear the filter.'
              : 'Generate your first 3D asset from a natural-language description.'}
          </p>
          <button
            onClick={() => setActiveTab('generate')}
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-blue-500/25 transition-all"
          >
            <Wand2 className="w-4 h-4" />
            <span>Generate 3D Asset</span>
          </button>
        </div>
      )}
    </div>
  );
};
