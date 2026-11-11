import React from 'react';
import { useStore } from '../store/useStore';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

export const ErrorPage: React.FC = () => {
  const { navigate } = useStore();

  return (
    <div className="w-full min-h-[calc(100vh-120px)] flex items-center justify-center px-4 py-16 text-center">
      <div className="max-w-md w-full bg-slate-900/90 border border-slate-800 rounded-3xl p-8 shadow-2xl flex flex-col items-center">
        <div className="w-20 h-20 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center mb-6">
          <AlertTriangle className="w-10 h-10" />
        </div>

        <span className="text-4xl font-extrabold font-mono text-white mb-2">500</span>
        <h2 className="text-xl font-bold text-slate-100 mb-2">Pipeline Synthesis Interrupted</h2>
        <p className="text-xs sm:text-sm text-slate-400 mb-6 leading-relaxed">
          An unexpected exception occurred during execution of the neural geometry or material binding pipeline.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-3 w-full">
          <button
            onClick={() => window.location.reload()}
            className="w-full flex items-center justify-center gap-2 py-3 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-rose-500/20 transition-all"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Reload Pipeline</span>
          </button>
          <button
            onClick={() => navigate('dashboard')}
            className="w-full flex items-center justify-center gap-2 py-3 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition-all"
          >
            <Home className="w-4 h-4" />
            <span>Return to Safety</span>
          </button>
        </div>
      </div>
    </div>
  );
};

