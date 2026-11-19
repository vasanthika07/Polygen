import React, { useState, useRef, useEffect } from 'react';
import type { Asset } from '../services/api';
import { assetApi } from '../services/api';
import { useStore } from '../store/useStore';
import {
  Box,
  Download,
  Trash2,
  Eye,
  Calendar,
  Layers,
  MoreVertical,
  ExternalLink,
  CheckCircle2,
  Sparkles,
  FileDown
} from 'lucide-react';

interface AssetCardProps {
  asset: Asset;
  onDeleted?: (assetId: string) => void;
}

export const AssetCard: React.FC<AssetCardProps> = ({ asset, onDeleted }) => {
  const { activeAsset, setActiveAsset, removeAsset, navigate, addNotification } = useStore();
  const [showMenu, setShowMenu] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const isSelected = activeAsset?.asset_id === asset.asset_id;

  // Close menu on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false);
      }
    };
    if (showMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showMenu]);

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowMenu(false);
    if (!window.confirm(`Permanently delete 3D model "${asset.asset_name}"? This removes binary files and metadata.`)) {
      return;
    }

    setIsDeleting(true);
    try {
      await assetApi.deleteAsset(asset.asset_id);
      removeAsset(asset.asset_id);
      if (onDeleted) onDeleted(asset.asset_id);
      addNotification({
        title: 'Asset Deleted',
        message: `Successfully removed "${asset.asset_name}" from repository.`,
        type: 'info',
      });
    } catch (err: any) {
      console.error('Failed to delete asset:', err);
      // Even if API fails (e.g. offline mock), update local state
      removeAsset(asset.asset_id);
      if (onDeleted) onDeleted(asset.asset_id);
      addNotification({
        title: 'Asset Removed',
        message: `Removed "${asset.asset_name}" from your active workspace.`,
        type: 'warning',
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const handleInspect = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowMenu(false);
    setActiveAsset(asset);
    navigate('viewer');
  };

  const handleViewDetails = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowMenu(false);
    setActiveAsset(asset);
    navigate('asset-details', { assetId: asset.asset_id });
  };

  const formattedDate = asset.created_at
    ? new Date(asset.created_at).toLocaleDateString([], {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : 'Recent';

  const fileSizeMb = (asset.file_size / (1024 * 1024)).toFixed(2);

  return (
    <div
      onClick={handleViewDetails}
      className={`group relative bg-slate-900/80 hover:bg-slate-800/80 backdrop-blur-md border rounded-2xl p-4 transition-all duration-200 cursor-pointer flex flex-col justify-between select-none ${
        isSelected
          ? 'border-blue-500 shadow-xl shadow-blue-500/15 ring-1 ring-blue-500'
          : 'border-slate-800/80 hover:border-slate-700 hover:shadow-xl'
      } ${isDeleting ? 'opacity-40 pointer-events-none' : ''}`}
    >
      {/* ---------------- Top Preview Thumbnail & Quick Overlays ---------------- */}
      <div className="w-full h-44 bg-slate-950 rounded-xl overflow-hidden mb-3 relative flex items-center justify-center border border-slate-800/60 group-hover:border-slate-700 transition-colors">
        {asset.preview_url ? (
          <img
            src={asset.preview_url}
            alt={asset.asset_name}
            loading="lazy"
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            onError={(e) => {
              // Hide broken image link and fall back to 3D placeholder
              (e.target as HTMLElement).style.display = 'none';
            }}
          />
        ) : null}

        {/* Fallback 3D Icon if image not present or fails */}
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-slate-600 group-hover:text-blue-400 transition-colors pointer-events-none">
          <Box className="w-12 h-12" />
          <span className="text-[10px] font-mono tracking-widest uppercase text-slate-500">Khronos glTF 2.0</span>
        </div>

        {/* Active In Viewer Status Tag */}
        {isSelected && (
          <div className="absolute top-2.5 left-2.5 px-2.5 py-0.5 bg-blue-600 text-white text-[10px] font-bold rounded-lg shadow-md flex items-center gap-1 z-10">
            <Sparkles className="w-2.5 h-2.5" />
            <span>Active in 3D</span>
          </div>
        )}

        {/* Production Status Badge (Top Right) */}
        <div className="absolute top-2.5 right-2.5 px-2 py-0.5 bg-slate-950/80 backdrop-blur-md border border-slate-800 rounded-md text-[10px] font-mono text-emerald-400 font-semibold flex items-center gap-1 z-10">
          <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />
          <span>Ready</span>
        </div>

        {/* Quick Hover Action Bar */}
        <div className="absolute inset-0 bg-slate-950/70 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 backdrop-blur-xs z-10">
          <button
            onClick={handleInspect}
            className="p-2.5 rounded-xl bg-blue-600 text-white shadow-lg hover:bg-blue-500 transition-all hover:scale-105 active:scale-95"
            title="Inspect in 3D Workbench"
          >
            <Eye className="w-4 h-4" />
          </button>

          <a
            href={assetApi.getDownloadUrl(asset.asset_id, 'standard')}
            download={`${asset.asset_name.replace(/[^a-zA-Z0-9]/g, '_')}_standard.glb`}
            onClick={(e) => e.stopPropagation()}
            className="p-2.5 rounded-xl bg-slate-800 text-slate-200 shadow-lg hover:bg-slate-700 hover:text-white transition-all hover:scale-105 active:scale-95"
            title="Download Standard GLB (1024px)"
          >
            <Download className="w-4 h-4" />
          </a>

          <button
            onClick={handleViewDetails}
            className="p-2.5 rounded-xl bg-slate-800 text-slate-200 shadow-lg hover:bg-slate-700 hover:text-white transition-all hover:scale-105 active:scale-95"
            title="View Full Specifications"
          >
            <ExternalLink className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* ---------------- Card Body & Metadata ---------------- */}
      <div className="flex-1 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between gap-2 mb-1">
            <h4
              className="text-sm font-bold text-white truncate hover:text-blue-400 transition-colors"
              title={asset.asset_name}
            >
              {asset.asset_name}
            </h4>
          </div>

          <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed mb-3">
            {asset.prompt || asset.original_prompt || 'High-fidelity procedural PBR 3D asset generated by PolyGen.'}
          </p>
        </div>

        {/* Geometry Metrics Row */}
        <div className="flex items-center justify-between text-[11px] text-slate-400 py-1.5 px-2 bg-slate-950/50 rounded-xl border border-slate-800/60 mb-3">
          <span className="flex items-center gap-1 font-mono text-cyan-400 font-medium">
            <Layers className="w-3 h-3 text-cyan-400" />
            {asset.polygon_count ? asset.polygon_count.toLocaleString() : '856'} polys
          </span>

          <div className="w-px h-3 bg-slate-800" />

          <span className="font-mono text-slate-300 font-medium">
            {fileSizeMb} MB
          </span>

          <div className="w-px h-3 bg-slate-800" />

          <span className="capitalize text-[10px] font-semibold text-slate-400">
            {asset.style || 'Fantasy'}
          </span>
        </div>
      </div>

      {/* ---------------- Footer Actions & Overflow Menu ---------------- */}
      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between relative">
        <span className="text-[10px] text-slate-500 flex items-center gap-1 font-medium">
          <Calendar className="w-3 h-3 text-slate-600" />
          {formattedDate}
        </span>

        {/* Three Dots Action Menu */}
        <div className="relative" ref={menuRef} onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            title="More Options"
          >
            <MoreVertical className="w-4 h-4" />
          </button>

          {showMenu && (
            <div className="absolute right-0 bottom-8 w-52 bg-slate-900/95 backdrop-blur-xl border border-slate-800 rounded-xl p-1.5 shadow-2xl z-30 flex flex-col gap-1 text-xs">
              <button
                onClick={handleInspect}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition-colors text-left"
              >
                <Eye className="w-3.5 h-3.5 text-blue-400" />
                <span>Inspect in 3D Viewport</span>
              </button>

              <button
                onClick={handleViewDetails}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition-colors text-left"
              >
                <ExternalLink className="w-3.5 h-3.5 text-indigo-400" />
                <span>Asset Specifications</span>
              </button>

              <div className="h-px bg-slate-800 my-0.5" />

              {/* Download Profiles Sub-links */}
              <a
                href={assetApi.getDownloadUrl(asset.asset_id, 'standard')}
                download={`${asset.asset_name.replace(/[^a-zA-Z0-9]/g, '_')}_standard.glb`}
                onClick={() => setShowMenu(false)}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition-colors text-left"
              >
                <FileDown className="w-3.5 h-3.5 text-emerald-400" />
                <span>Download Standard (1024px)</span>
              </a>

              <a
                href={assetApi.getDownloadUrl(asset.asset_id, 'high_quality')}
                download={`${asset.asset_name.replace(/[^a-zA-Z0-9]/g, '_')}_high_quality.glb`}
                onClick={() => setShowMenu(false)}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition-colors text-left"
              >
                <Download className="w-3.5 h-3.5 text-emerald-400" />
                <span>Download HQ (2048px)</span>
              </a>

              <a
                href={assetApi.getDownloadUrl(asset.asset_id, 'optimized')}
                download={`${asset.asset_name.replace(/[^a-zA-Z0-9]/g, '_')}_optimized.glb`}
                onClick={() => setShowMenu(false)}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition-colors text-left"
              >
                <Download className="w-3.5 h-3.5 text-emerald-400" />
                <span>Download Optimized (512px)</span>
              </a>

              <div className="h-px bg-slate-800 my-0.5" />

              <button
                onClick={handleDelete}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 transition-colors text-left"
              >
                <Trash2 className="w-3.5 h-3.5 text-rose-400" />
                <span>Delete 3D Asset</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
