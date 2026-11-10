import React, { useEffect, useState } from 'react';
import { useStore } from './store/useStore';
import { authApi, assetApi } from './services/api';
import { Navbar } from './components/Navbar';
import { AuthModal } from './components/AuthModal';
import { Generate } from './pages/Generate';
import { AssetLibrary } from './pages/AssetLibrary';
import { Dashboard } from './pages/Dashboard';

export const App: React.FC = () => {
  const { activeTab, setUser, setAssets, setActiveAsset } = useStore();
  const [isAuthOpen, setIsAuthOpen] = useState(false);

  useEffect(() => {
    // 1. Restore authenticated user profile if token exists
    const token = localStorage.getItem('polygen_token');
    if (token) {
      authApi.me()
        .then((res) => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('polygen_token');
          setUser(null);
        });
    }

    // 2. Fetch existing generated assets
    assetApi.listAssets()
      .then((res) => {
        setAssets(res.data.items);
        if (res.data.items.length > 0) {
          setActiveAsset(res.data.items[0]);
        }
      })
      .catch((err) => console.error('Failed to prefetch assets:', err));
  }, []);

  return (
    <div className="min-h-screen bg-[#070a13] text-slate-100 flex flex-col font-sans selection:bg-blue-500/30 selection:text-blue-200">
      <Navbar onOpenAuth={() => setIsAuthOpen(true)} />

      <main className="flex-1 w-full">
        {activeTab === 'generate' && <Generate />}
        {activeTab === 'library' && <AssetLibrary />}
        {activeTab === 'dashboard' && <Dashboard />}
      </main>

      {/* Global Footer */}
      <footer className="w-full border-t border-slate-800/80 bg-slate-950/60 py-6 px-4 lg:px-8 mt-12">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div>
            <span className="font-semibold text-slate-400">PolyGen</span> – Generative Text-to-3D Asset Pipeline.
            PBR textured & decimation ready for gaming & spatial computing.
          </div>
          <div className="flex items-center gap-4">
            <span>FastAPI Backend</span>
            <span>•</span>
            <span>Three.js Viewer</span>
            <span>•</span>
            <span>GLB / glTF 2.0</span>
          </div>
        </div>
      </footer>

      {/* Auth Modal */}
      <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} />
    </div>
  );
};

export default App;
