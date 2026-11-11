import React from 'react';
import { useStore } from '../store/useStore';
import { Box, Home, Wand2 } from 'lucide-react';

export const NotFound: React.FC = () => {
  const { navigate } = useStore();

  return (
    <div className="w-full min-h-[calc(100vh-120px)] flex items-center justify-center px-4 py-16 text-center">
      <div className="max-w-md w-full bg-slate-900/90 border border-slate-800 rounded-3xl p-8 shadow-2xl flex flex-col items-center">
        <div className="w-20 h-20 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center mb-6">
          <Box className="w-10 h-10 animate-bounce" />
        </div>

        <span className="text-4xl font-extrabold font-mono text-white mb-2">404</span>
        <h2 className="text-xl font-bold text-slate-100 mb-2">Polygon Lost in Space</h2>
        <p className="text-xs sm:text-sm text-slate-400 mb-6 leading-relaxed">
          The 3D model, viewport scene, or route you requested cannot be located in the current coordinate space.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-3 w-full">
          <button
            onClick={() => navigate('dashboard')}
            className="w-full flex items-center justify-center gap-2 py-3 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-blue-500/20 transition-all"
          >
            <Home className="w-4 h-4" />
            <span>Go to Dashboard</span>
          </button>
          <button
            onClick={() => navigate('workspace')}
            className="w-full flex items-center justify-center gap-2 py-3 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition-all"
          >
            <Wand2 className="w-4 h-4 text-blue-400" />
            <span>Studio Workspace</span>
          </button>
        </div>
      </div>
    </div>
  );
};
