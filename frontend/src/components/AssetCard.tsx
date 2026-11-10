import React from 'react';
import type { Asset } from '../services/api';
import { assetApi } from '../services/api';
import { useStore } from '../store/useStore';
import { Box, Download, Trash2, Eye, Calendar, Layers } from 'lucide-react';

interface AssetCardProps {
  asset: Asset;
}

export const AssetCard: React.FC<AssetCardProps> = ({ asset }) => {
  const { activeAsset, setActiveAsset, removeAsset } = useStore();
  const isSelected = activeAsset?.asset_id === asset.asset_id;

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm(`Delete asset "${asset.asset_name}"?`)) return;

    try {
      await assetApi.deleteAsset(asset.asset_id);
      removeAsset(asset.asset_id);
    } catch (err) {
      console.error('Failed to delete asset:', err);
    }
  };

  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  return (
    <div
      onClick={() => setActiveAsset(asset)}
      className={`group relative bg-slate-900/80 hover:bg-slate-800/80 backdrop-blur-md border rounded-2xl p-4 transition-all duration-200 cursor-pointer flex flex-col justify-between ${
        isSelected
          ? 'border-blue-500 shadow-xl shadow-blue-500/10 ring-1 ring-blue-500'
          : 'border-slate-800/80 hover:border-slate-700'
      }`}
    >
      {/* Top Preview or Visual Placeholder */}
      <div className="w-full h-40 bg-slate-950 rounded-xl overflow-hidden mb-3 relative flex items-center justify-center border border-slate-800/50">
        {asset.preview_url ? (
          <img
            src={asset.preview_url}
            alt={asset.asset_name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="flex flex-col items-center gap-2 text-slate-600 group-hover:text-blue-400 transition-colors">
            <Box className="w-12 h-12" />
            <span className="text-[11px] font-mono">GLB 2.0</span>
          </div>
        )}

        {/* Selected badge */}
        {isSelected && (
          <div className="absolute top-2 left-2 px-2 py-0.5 bg-blue-600 text-white text-[10px] font-semibold rounded-md shadow-md">
            Active in Viewer
          </div>
        )}

        {/* Hover overlay quick action */}
        <div className="absolute inset-0 bg-slate-950/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 backdrop-blur-xs">
          <button
            onClick={() => setActiveAsset(asset)}
            className="p-2 rounded-xl bg-blue-600 text-white shadow-lg hover:bg-blue-500 transition-colors"
            title="Inspect 3D"
          >
            <Eye className="w-4 h-4" />
          </button>
          <a
            href={asset.glb_url}
            download
            onClick={handleDownload}
            className="p-2 rounded-xl bg-slate-800 text-slate-200 shadow-lg hover:bg-slate-700 transition-colors"
            title="Download GLB"
          >
            <Download className="w-4 h-4" />
          </a>
        </div>
      </div>

      {/* Meta Information */}
      <div>
        <h4 className="text-sm font-semibold text-slate-100 truncate mb-1" title={asset.asset_name}>
          {asset.asset_name}
        </h4>

        <div className="flex items-center justify-between text-[11px] text-slate-400 mb-3">
          <span className="flex items-center gap-1">
            <Layers className="w-3 h-3 text-cyan-400" />
            {asset.polygon_count.toLocaleString()} polys
          </span>
          <span>{(asset.file_size / (1024 * 1024)).toFixed(2)} MB</span>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
        <span className="text-[10px] text-slate-500 flex items-center gap-1">
          <Calendar className="w-2.5 h-2.5" />
          {new Date(asset.created_at).toLocaleDateString()}
        </span>

        <button
          onClick={handleDelete}
          className="text-slate-500 hover:text-rose-400 p-1 rounded transition-colors"
          title="Delete asset"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
