import React, { useEffect, useState, useMemo } from 'react';
import { useStore } from '../store/useStore';
import { assetApi, type Asset } from '../services/api';
import { AssetCard } from '../components/AssetCard';
import { ModelViewer } from '../components/ModelViewer';
import {
  FolderGit2,
  Search,
  Wand2,
  RefreshCw,
  LayoutGrid,
  List,
  Download,
  Eye,
  Trash2,
  Calendar,
  X,
  SlidersHorizontal,
  ArrowUpDown
} from 'lucide-react';

export const AssetLibrary: React.FC = () => {
  const { assets, setAssets, navigate, setActiveAsset, removeAsset, addNotification } = useStore();
  const [search, setSearch] = useState('');
  const [styleFilter, setStyleFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState<'all' | 'today' | 'week' | 'month'>('all');
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'polygons_desc' | 'polygons_asc' | 'size' | 'name'>('newest');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [loading, setLoading] = useState(false);
  const [previewModalAsset, setPreviewModalAsset] = useState<Asset | null>(null);

  const fetchAssets = async () => {
    setLoading(true);
    try {
      const res = await assetApi.listAssets({
        search: search.trim() || undefined,
        sort_by: sortBy === 'polygons_desc' ? 'polygons_desc' : sortBy === 'polygons_asc' ? 'polygons_asc' : sortBy === 'oldest' ? 'oldest' : sortBy === 'name' ? 'name_asc' : 'newest',
        date_filter: dateFilter,
      });
      if (res.data?.items) {
        setAssets(res.data.items);
      }
    } catch (err) {
      console.error('Failed to load asset library from API:', err);
    } finally {
      setLoading(false);
    }
  };

  // Re-fetch on filter or sort change
  useEffect(() => {
    fetchAssets();
  }, [dateFilter, sortBy]);

  // Client-side filtering & sorting for instant search feedback
  const filteredAssets = useMemo(() => {
    return assets
      .filter((a) => {
        const query = search.toLowerCase().trim();
        const matchSearch =
          !query ||
          a.asset_name.toLowerCase().includes(query) ||
          (a.prompt && a.prompt.toLowerCase().includes(query)) ||
          (a.original_prompt && a.original_prompt.toLowerCase().includes(query));

        const matchStyle = styleFilter === 'all' || (a.style && a.style.toLowerCase() === styleFilter.toLowerCase());

        // Date filter check
        let matchDate = true;
        if (dateFilter !== 'all' && a.created_at) {
          const createdTime = new Date(a.created_at).getTime();
          const now = Date.now();
          if (dateFilter === 'today') {
            const startOfToday = new Date().setHours(0, 0, 0, 0);
            matchDate = createdTime >= startOfToday;
          } else if (dateFilter === 'week') {
            matchDate = createdTime >= now - 7 * 24 * 3600 * 1000;
          } else if (dateFilter === 'month') {
            matchDate = createdTime >= now - 30 * 24 * 3600 * 1000;
          }
        }

        return matchSearch && matchStyle && matchDate;
      })
      .sort((a, b) => {
        if (sortBy === 'polygons_desc') return (b.polygon_count || 0) - (a.polygon_count || 0);
        if (sortBy === 'polygons_asc') return (a.polygon_count || 0) - (b.polygon_count || 0);
        if (sortBy === 'size') return (b.file_size || 0) - (a.file_size || 0);
        if (sortBy === 'name') return a.asset_name.localeCompare(b.asset_name);
        if (sortBy === 'oldest') return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
  }, [assets, search, styleFilter, dateFilter, sortBy]);

  const handleDelete = async (asset: Asset, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm(`Permanently delete 3D model "${asset.asset_name}"?`)) return;

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
      removeAsset(asset.asset_id);
      addNotification({
        title: 'Asset Removed',
        message: `Removed "${asset.asset_name}" from your workspace.`,
        type: 'warning',
      });
    }
  };

  const handleInspect = (asset: Asset, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setActiveAsset(asset);
    navigate('viewer');
  };

  const handleViewDetails = (asset: Asset) => {
    setActiveAsset(asset);
    navigate('asset-details', { assetId: asset.asset_id });
  };

  const handleOpenPreviewModal = (asset: Asset, e: React.MouseEvent) => {
    e.stopPropagation();
    setPreviewModalAsset(asset);
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 lg:px-8 py-8 flex flex-col gap-6">
      {/* ----------------- Top Header & Actions ----------------- */}
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
            Browse, inspect, filter, and download production-ready 3D models with physical PBR textures.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('workspace')}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-blue-500/25 transition-all self-start md:self-auto"
          >
            <Wand2 className="w-4 h-4" />
            <span>New Generation</span>
          </button>
        </div>
      </div>

      {/* ----------------- Search & Filter Controls Toolbar ----------------- */}
      <div className="flex flex-col gap-3 bg-slate-900/60 p-4 rounded-2xl border border-slate-800/80 shadow-xl">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by model name or original prompt keywords..."
              className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Right Filter & Sort Selectors */}
          <div className="flex items-center gap-2 flex-wrap">
            {/* Filter by Creation Date */}
            <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-300">
              <Calendar className="w-3.5 h-3.5 text-blue-400" />
              <select
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value as any)}
                className="bg-transparent text-xs text-slate-200 focus:outline-none font-medium cursor-pointer"
                title="Filter by Creation Date"
              >
                <option value="all">All Time</option>
                <option value="today">Created Today</option>
                <option value="week">Past 7 Days</option>
                <option value="month">Past 30 Days</option>
              </select>
            </div>

            {/* Filter by Style */}
            <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-300">
              <SlidersHorizontal className="w-3.5 h-3.5 text-indigo-400" />
              <select
                value={styleFilter}
                onChange={(e) => setStyleFilter(e.target.value)}
                className="bg-transparent text-xs text-slate-200 focus:outline-none font-medium cursor-pointer"
                title="Filter by Style Category"
              >
                <option value="all">All Styles</option>
                <option value="medieval fantasy">Medieval Fantasy</option>
                <option value="realistic">Realistic</option>
                <option value="stylized">Stylized</option>
                <option value="sci-fi">Sci-Fi</option>
                <option value="low-poly">Low-Poly</option>
              </select>
            </div>

            {/* Sort Order Selector */}
            <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-300">
              <ArrowUpDown className="w-3.5 h-3.5 text-amber-400" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="bg-transparent text-xs text-slate-200 focus:outline-none font-medium cursor-pointer"
                title="Sort Asset Order"
              >
                <option value="newest">Sort: Newest First</option>
                <option value="oldest">Sort: Oldest First</option>
                <option value="polygons_desc">Sort: Polygons (High to Low)</option>
                <option value="polygons_asc">Sort: Polygons (Low to High)</option>
                <option value="size">Sort: File Size</option>
                <option value="name">Sort: Name (A-Z)</option>
              </select>
            </div>

            {/* Grid / List View Toggle */}
            <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-1.5 rounded-lg transition-colors ${
                  viewMode === 'grid' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
                title="Grid View"
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-1.5 rounded-lg transition-colors ${
                  viewMode === 'list' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
                title="List Table View"
              >
                <List className="w-4 h-4" />
              </button>
            </div>

            {/* Refresh */}
            <button
              onClick={fetchAssets}
              disabled={loading}
              className="p-2 bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white rounded-xl transition-colors"
              title="Refresh Asset Library"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Status & Results Summary Bar */}
        <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/60">
          <span>
            Showing <strong className="text-white font-mono">{filteredAssets.length}</strong> of{' '}
            <strong className="text-white font-mono">{assets.length}</strong> total models
          </span>

          {(search || styleFilter !== 'all' || dateFilter !== 'all') && (
            <button
              onClick={() => {
                setSearch('');
                setStyleFilter('all');
                setDateFilter('all');
              }}
              className="text-blue-400 hover:text-blue-300 font-semibold"
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* ----------------- Assets Content Area ----------------- */}
      {filteredAssets.length > 0 ? (
        viewMode === 'grid' ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredAssets.map((asset) => (
              <AssetCard key={asset.asset_id} asset={asset} />
            ))}
          </div>
        ) : (
          /* Table List View */
          <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl overflow-hidden shadow-2xl">
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
                      <td className="py-3.5 px-4 font-semibold text-white flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-center text-blue-400 shrink-0">
                          <FolderGit2 className="w-4 h-4" />
                        </div>
                        <div className="truncate max-w-xs">
                          <div className="font-bold text-white">{asset.asset_name}</div>
                          <div className="text-[10px] text-slate-400 truncate max-w-xs">
                            {asset.prompt || asset.original_prompt || 'Generated 3D asset'}
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-cyan-400">
                        {asset.polygon_count ? asset.polygon_count.toLocaleString() : '856'}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-300">
                        {(asset.file_size / (1024 * 1024)).toFixed(2)} MB
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="capitalize px-2.5 py-1 rounded-full bg-slate-800/80 text-[10px] font-semibold text-slate-300 border border-slate-700/60">
                          {asset.style || 'Fantasy'}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-400">
                        {asset.created_at ? new Date(asset.created_at).toLocaleDateString() : 'Recent'}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={(e) => handleOpenPreviewModal(asset, e)}
                            className="p-1.5 rounded-lg bg-indigo-600/20 text-indigo-400 hover:bg-indigo-600 hover:text-white transition-colors"
                            title="Quick 3D Modal Preview"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                          <a
                            href={assetApi.getDownloadUrl(asset.asset_id, 'standard')}
                            download={`${asset.asset_name.replace(/[^a-zA-Z0-9]/g, '_')}_standard.glb`}
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
            {search || styleFilter !== 'all' || dateFilter !== 'all'
              ? 'No matching models found'
              : 'Your asset library is empty'}
          </h3>
          <p className="text-xs text-slate-400 max-w-sm mb-6">
            {search || styleFilter !== 'all' || dateFilter !== 'all'
              ? 'Try modifying your search query or clear the active date/style filters.'
              : 'Generate your first 3D asset from a natural-language description in the Studio.'}
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

      {/* ----------------- In-Library Quick 3D Preview Modal ----------------- */}
      {previewModalAsset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
          <div className="w-full max-w-4xl bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl flex flex-col">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Eye className="w-4 h-4 text-blue-400" />
                  <span>{previewModalAsset.asset_name}</span>
                </h3>
                <p className="text-xs text-slate-400 truncate max-w-md mt-0.5">
                  {previewModalAsset.prompt || previewModalAsset.original_prompt}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleInspect(previewModalAsset)}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl transition-all"
                >
                  Open in Full Workbench
                </button>
                <button
                  onClick={() => setPreviewModalAsset(null)}
                  className="p-1.5 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Body: Interactive Three.js Viewer */}
            <div className="w-full h-[480px]">
              <ModelViewer
                assetUrl={previewModalAsset.glb_url}
                className="h-full rounded-none border-0"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
