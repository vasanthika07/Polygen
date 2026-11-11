import React, { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import { assetApi, type Asset } from '../services/api';
import { AssetCard } from '../components/AssetCard';
import {
  FolderGit2,
  Search,
  Wand2,
  RefreshCw,
  LayoutGrid,
  List,
  Download,
  Eye,
  Trash2
} from 'lucide-react';

export const AssetLibrary: React.FC = () => {
  const { assets, setAssets, navigate, setActiveAsset, removeAsset, addNotification } = useStore();
  const [search, setSearch] = useState('');
  const [styleFilter, setStyleFilter] = useState('all');
  const [sortBy, setSortBy] = useState<'newest' | 'polygons' | 'size'>('newest');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
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

  // Filter & sort logic
  const filteredAssets = assets
    .filter((a) => {
      const matchSearch =
        a.asset_name.toLowerCase().includes(search.toLowerCase()) ||
        (a.prompt && a.prompt.toLowerCase().includes(search.toLowerCase()));
      const matchStyle = styleFilter === 'all' || a.style === styleFilter;
      return matchSearch && matchStyle;
    })
    .sort((a, b) => {
      if (sortBy === 'polygons') return (b.polygon_count || 0) - (a.polygon_count || 0);
      if (sortBy === 'size') return (b.file_size || 0) - (a.file_size || 0);
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });

  const handleDelete = async (asset: Asset, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm(`Delete 3D model "${asset.asset_name}"?`)) return;

    try {
      await assetApi.deleteAsset(asset.asset_id);
      removeAsset(asset.asset_id);
      addNotification({
        title: 'Asset Deleted',
        message: `Removed "${asset.asset_name}" from repository.`,
        type: 'info',
      });
    } catch (err) {
      console.error('Delete error:', err);
      // Remove locally
      removeAsset(asset.asset_id);
    }
  };

  const handleInspect = (asset: Asset) => {
    setActiveAsset(asset);
    navigate('viewer');
  };

  const handleViewDetails = (asset: Asset) => {
    setActiveAsset(asset);
    navigate('asset-details', { assetId: asset.asset_id });
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 lg:px-8 py-8 flex flex-col gap-6">
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
            Browse, inspect, filter, and download production-ready 3D models with PBR textures.
          </p>
        </div>

        <button
          onClick={() => navigate('workspace')}
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-blue-500/25 transition-all self-start md:self-auto"
        >
          <Wand2 className="w-4 h-4" />
          <span>New Generation</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-2xl border border-slate-800/80">
        {/* Left: Search input */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by asset name or prompt..."
            className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Right: Controls & Toggles */}
        <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
          {/* Style Filter */}
          <select
            value={styleFilter}
            onChange={(e) => setStyleFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
          >
            <option value="all">All Styles</option>
            <option value="medieval fantasy">Medieval Fantasy</option>
            <option value="realistic">Realistic</option>
            <option value="stylized">Stylized</option>
            <option value="sci-fi">Sci-Fi</option>
            <option value="low-poly">Low-Poly</option>
          </select>

          {/* Sort By */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
          >
            <option value="newest">Sort: Newest First</option>
            <option value="polygons">Sort: Polygon Count</option>
            <option value="size">Sort: File Size</option>
          </select>

          {/* View Mode Toggle */}
          <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              title="Grid View"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              title="Table View"
            >
              <List className="w-4 h-4" />
            </button>
          </div>

          {/* Refresh */}
          <button
            onClick={fetchAssets}
            disabled={loading}
            className="p-2 bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white rounded-xl transition-colors"
            title="Refresh assets"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Assets Content Display */}
      {filteredAssets.length > 0 ? (
        viewMode === 'grid' ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredAssets.map((asset) => (
              <AssetCard key={asset.asset_id} asset={asset} />
            ))}
          </div>
        ) : (
          /* Table List View */
          <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase font-semibold text-[10px] tracking-wider">
                  <tr>
                    <th className="py-3.5 px-4">Asset Name</th>
                    <th className="py-3.5 px-4">Polygons</th>
                    <th className="py-3.5 px-4">File Size</th>
                    <th className="py-3.5 px-4">Style</th>
                    <th className="py-3.5 px-4">Created Date</th>
                    <th className="py-3.5 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-medium">
                  {filteredAssets.map((asset) => (
                    <tr
                      key={asset.asset_id}
                      onClick={() => handleViewDetails(asset)}
                      className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                    >
                      <td className="py-3.5 px-4 font-semibold text-white flex items-center gap-2">
                        <FolderGit2 className="w-4 h-4 text-blue-400 shrink-0" />
                        <span className="truncate max-w-xs">{asset.asset_name}</span>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-cyan-400">
                        {asset.polygon_count.toLocaleString()}
                      </td>
                      <td className="py-3.5 px-4 font-mono">
                        {(asset.file_size / (1024 * 1024)).toFixed(2)} MB
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="capitalize px-2 py-0.5 rounded-full bg-slate-800 text-[10px] text-slate-300">
                          {asset.style || 'Default'}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-400">
                        {new Date(asset.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => handleInspect(asset)}
                            className="p-1.5 rounded-lg bg-blue-600/20 text-blue-400 hover:bg-blue-600 hover:text-white transition-colors"
                            title="Inspect in 3D Viewport"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                          <a
                            href={asset.glb_url}
                            download
                            className="p-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
                            title="Download GLB"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </a>
                          <button
                            onClick={(e) => handleDelete(asset, e)}
                            className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                            title="Delete Asset"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )
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
              ? 'Try modifying your search query or clear the style filter.'
              : 'Generate your first 3D asset from a natural-language description.'}
          </p>
          <button
            onClick={() => navigate('workspace')}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-blue-500/25 transition-all"
          >
            <Wand2 className="w-4 h-4" />
            <span>Open Studio Workspace</span>
          </button>
        </div>
      )}
    </div>
  );
};
