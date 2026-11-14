import React, { useEffect, useState } from 'react';
import { useStore, type AppRoute } from './store/useStore';
import { authApi, assetApi } from './services/api';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { NotificationToast } from './components/NotificationToast';
import { AuthModal } from './components/AuthModal';
import { Box, Loader2 } from 'lucide-react';

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

const PROTECTED_ROUTES: AppRoute[] = [
  'dashboard',
  'generate',
  'workspace',
  'viewer',
  'library',
  'history',
  'asset-details',
  'settings',
];

export const App: React.FC = () => {
  const { 
    currentRoute, 
    navigate,
    sidebarCollapsed, 
    user,
    setUser, 
    setAssets, 
    setActiveAsset,
    isAuthChecking,
    setIsAuthChecking,
    logout,
    addNotification
  } = useStore();

  const [isAuthOpen, setIsAuthOpen] = useState(false);

  // 1. Session initialization on mount
  useEffect(() => {
    const token = localStorage.getItem('polygen_token');
    if (token) {
      setIsAuthChecking(true);
      authApi.me()
        .then((res) => {
          setUser(res.data);
          // Prefetch user's personal generated assets
          return assetApi.listAssets();
        })
        .then((res) => {
          if (res?.data?.items) {
            setAssets(res.data.items);
            if (res.data.items.length > 0) {
              setActiveAsset(res.data.items[0]);
            }
          }
        })
        .catch((err) => {
          console.warn('Session verification failed on mount:', err);
          logout();
        })
        .finally(() => {
          setIsAuthChecking(false);
        });
    } else {
      setIsAuthChecking(false);
    }
  }, []);

  // 2. Protected Route Guard
  useEffect(() => {
    if (isAuthChecking) return;

    const token = localStorage.getItem('polygen_token');
    const isAuthenticated = !!user || !!token;

    if (PROTECTED_ROUTES.includes(currentRoute) && !isAuthenticated) {
      addNotification({
        title: 'Authentication Required',
        message: 'Please sign in to access your generative 3D studio.',
        type: 'warning',
      });
      navigate('login');
    } else if ((currentRoute === 'login' || currentRoute === 'register') && isAuthenticated) {
      navigate('dashboard');
    }
  }, [currentRoute, user, isAuthChecking]);

  // Full-width pages that hide sidebar
  const isFullBleedPage = currentRoute === 'landing' || currentRoute === 'login' || currentRoute === 'register';

  if (isAuthChecking && localStorage.getItem('polygen_token')) {
    return (
      <div className="min-h-screen bg-[#070a13] flex flex-col items-center justify-center text-slate-200">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 flex items-center justify-center text-white mb-4 shadow-xl shadow-blue-500/25 animate-pulse">
          <Box className="w-7 h-7" />
        </div>
        <div className="flex items-center gap-2 text-sm font-semibold tracking-wide text-slate-100">
          <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
          <span>Restoring PolyGen Studio Session...</span>
        </div>
        <p className="text-xs text-slate-500 mt-1">Verifying cryptographic authentication tokens</p>
      </div>
    );
  }

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
      {/* Collapsible Professional Sidebar (hidden on public/auth pages) */}
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
        {!isFullBleedPage && <Header onOpenAuth={() => setIsAuthOpen(true)} />}

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
