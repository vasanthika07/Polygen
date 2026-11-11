import React, { useEffect, useState } from 'react';
import { useStore } from './store/useStore';
import { authApi, assetApi } from './services/api';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { NotificationToast } from './components/NotificationToast';
import { AuthModal } from './components/AuthModal';

// All 12 required Pages
import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { Generate } from './pages/Generate';
import { Workspace } from './pages/Workspace';
import { ViewerPage } from './pages/ViewerPage';
import { AssetLibrary } from './pages/AssetLibrary';
import { GenerationHistory } from './pages/GenerationHistory';
import { AssetDetails } from './pages/AssetDetails';
import { UserSettings } from './pages/UserSettings';
import { NotFound } from './pages/NotFound';
import { ErrorPage } from './pages/ErrorPage';

export const App: React.FC = () => {
  const { 
    currentRoute, 
    sidebarCollapsed, 
    setUser, 
    setAssets, 
    setActiveAsset 
  } = useStore();

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

  // Full-width pages that hide sidebar (Landing, Login, Register)
  const isFullBleedPage = currentRoute === 'landing';

  const renderActiveRoute = () => {
    switch (currentRoute) {
      case 'landing':
        return <Landing />;
      case 'login':
        return <Login />;
      case 'register':
        return <Register />;
      case 'dashboard':
        return <Dashboard />;
      case 'generate':
        return <Generate />;
      case 'workspace':
        return <Workspace />;
      case 'viewer':
        return <ViewerPage />;
      case 'library':
        return <AssetLibrary />;
      case 'history':
        return <GenerationHistory />;
      case 'asset-details':
        return <AssetDetails />;
      case 'settings':
        return <UserSettings />;
      case 'not-found':
        return <NotFound />;
      case 'error':
        return <ErrorPage />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-[#070a13] text-slate-100 flex font-sans selection:bg-blue-500/30 selection:text-blue-200">
      {/* Collapsible Professional Sidebar (hidden on public Landing) */}
      {!isFullBleedPage && <Sidebar />}

      {/* Main Content Area */}
      <div
        className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ${
          isFullBleedPage
            ? 'ml-0'
            : sidebarCollapsed
            ? 'md:ml-20 ml-0'
            : 'md:ml-64 ml-0'
        }`}
      >
        {/* Top Header with Breadcrumbs, Search, Engine Pill, Notifications */}
        <Header onOpenAuth={() => setIsAuthOpen(true)} />

        {/* Dynamic Route View */}
        <main className="flex-1 w-full pb-12">
          {renderActiveRoute()}
        </main>

        {/* Global Footer */}
        <footer className="w-full border-t border-slate-800/80 bg-slate-950/60 py-6 px-4 lg:px-8 mt-auto">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
            <div>
              <span className="font-semibold text-slate-400">PolyGen</span> – Generative Text-to-3D Asset Pipeline.
              PBR textured & decimation ready for gaming & spatial computing.
            </div>
            <div className="flex items-center gap-4">
              <span>FastAPI Backend</span>
              <span>•</span>
              <span>Three.js Viewport</span>
              <span>•</span>
              <span>GLB / glTF 2.0</span>
            </div>
          </div>
        </footer>
      </div>

      {/* Floating System Notifications */}
      <NotificationToast />

      {/* Optional Quick Auth Modal */}
      <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} />
    </div>
  );
};

export default App;
