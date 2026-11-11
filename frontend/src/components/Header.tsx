import React, { useState } from 'react';
import { useStore } from '../store/useStore';
import { 
  Bell, 
  Search, 
  Sparkles, 
  Cpu, 
  LogOut, 
  Menu,
  CheckCircle2,
  AlertTriangle,
  Info,
  X
} from 'lucide-react';

interface HeaderProps {
  onOpenAuth?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenAuth }) => {
  const { 
    currentRoute, 
    navigate, 
    toggleSidebar, 
    user, 
    logout, 
    notifications, 
    dismissNotification, 
    clearNotifications,
    setGenerationPrompt
  } = useStore();

  const [showNotifications, setShowNotifications] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setGenerationPrompt(searchQuery.trim());
    navigate('workspace');
    setSearchQuery('');
  };

  const getBreadcrumbTitle = () => {
    switch (currentRoute) {
      case 'dashboard': return 'Dashboard & Telemetry';
      case 'workspace': return 'Generation Studio Workspace';
      case 'generate': return 'Inspiration & Category Hub';
      case 'viewer': return 'Interactive 3D Viewport Workbench';
      case 'library': return 'Asset Library & Repository';
      case 'history': return 'Generation Audit History';
      case 'asset-details': return 'Asset Details & Engine Export';
      case 'settings': return 'System & Generation Settings';
      case 'landing': return 'Product Showcase';
      case 'login': return 'Authentication / Sign In';
      case 'register': return 'Create PolyGen Account';
      case 'not-found': return 'Page Not Found';
      default: return 'Overview';
    }
  };

  return (
    <header className="sticky top-0 z-30 w-full bg-[#070a13]/90 backdrop-blur-xl border-b border-slate-800/80 px-4 sm:px-6 py-3 transition-all flex items-center justify-between gap-4">
      {/* Left: Mobile Sidebar Toggle & Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={toggleSidebar}
          className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors md:hidden"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 text-xs">
          <span 
            onClick={() => navigate('dashboard')}
            className="text-slate-500 hover:text-slate-300 cursor-pointer font-medium"
          >
            PolyGen
          </span>
          <span className="text-slate-700">/</span>
          <span className="text-slate-200 font-semibold truncate max-w-[180px] sm:max-w-none">
            {getBreadcrumbTitle()}
          </span>
        </div>
      </div>

      {/* Middle: Universal Search / Prompt Bar */}
      <form onSubmit={handleSearchSubmit} className="hidden md:flex items-center max-w-md w-full relative">
        <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search models or type prompt and press Enter..."
          className="w-full bg-slate-900/90 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
        />
      </form>

      {/* Right Actions: Engine Pill, Notifications, Quick Launch, User */}
      <div className="flex items-center gap-3">
        {/* Hardware Status Pill */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-slate-900/80 border border-slate-800 rounded-xl text-xs text-slate-300">
          <Cpu className="w-3.5 h-3.5 text-blue-400" />
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-slate-400">Shap-E & PBR</span>
        </div>

        {/* Notifications Bell */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors relative"
            title="Notifications"
          >
            <Bell className="w-4 h-4" />
            {notifications.length > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-blue-600 text-[10px] font-bold text-white flex items-center justify-center">
                {notifications.length}
              </span>
            )}
          </button>

          {/* Notifications Dropdown Popover */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-slate-900/95 backdrop-blur-xl border border-slate-800 rounded-2xl shadow-2xl p-4 z-50 flex flex-col gap-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-xs font-bold text-slate-100 flex items-center gap-1.5">
                  <Bell className="w-3.5 h-3.5 text-blue-400" />
                  Notifications ({notifications.length})
                </span>
                {notifications.length > 0 && (
                  <button
                    onClick={clearNotifications}
                    className="text-[11px] text-slate-400 hover:text-rose-400 transition-colors"
                  >
                    Clear All
                  </button>
                )}
              </div>

              <div className="max-h-72 overflow-y-auto space-y-2 scrollbar-thin">
                {notifications.length > 0 ? (
                  notifications.map((notif) => (
                    <div
                      key={notif.id}
                      className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/60 flex items-start justify-between gap-3 text-xs"
                    >
                      <div className="flex items-start gap-2.5">
                        {notif.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />}
                        {notif.type === 'error' && <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />}
                        {notif.type === 'warning' && <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />}
                        {notif.type === 'info' && <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />}
                        <div>
                          <div className="font-semibold text-slate-200">{notif.title}</div>
                          <div className="text-slate-400 text-[11px] mt-0.5">{notif.message}</div>
                          <div className="text-[10px] text-slate-400 mt-1">{notif.timestamp}</div>
                        </div>
                      </div>
                      <button
                        onClick={() => dismissNotification(notif.id)}
                        className="text-slate-500 hover:text-slate-300"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))
                ) : (
                  <div className="py-6 text-center text-xs text-slate-500">
                    No new notifications
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Quick Launch CTA */}
        <button
          onClick={() => navigate('workspace')}
          className="hidden sm:flex items-center gap-1.5 px-3.5 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-blue-500/25 transition-all"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>New 3D Asset</span>
        </button>

        {/* User Account / Auth Button */}
        {user ? (
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('settings')}
              className="flex items-center gap-2 p-1.5 bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors"
            >
              <div className="w-7 h-7 rounded-lg bg-blue-600/30 text-blue-400 flex items-center justify-center font-bold text-xs">
                {user.username.charAt(0).toUpperCase()}
              </div>
            </button>
            <button
              onClick={logout}
              className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-rose-400 transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <button
              onClick={() => (onOpenAuth ? onOpenAuth() : navigate('login'))}
              className="px-3.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 text-xs font-medium transition-colors"
            >
              Sign In
            </button>
            <button
              onClick={() => navigate('register')}
              className="hidden sm:block px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-500/20 transition-all"
            >
              Sign Up
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
