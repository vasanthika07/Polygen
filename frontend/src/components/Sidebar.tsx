import React from 'react';
import { useStore, type AppRoute } from '../store/useStore';
import { 
  LayoutDashboard, 
  Wand2, 
  Sparkles, 
  Box, 
  FolderGit2, 
  Clock, 
  Settings, 
  ChevronLeft, 
  ChevronRight, 
  Cpu, 
  LogOut,
  User as UserIcon,
  HelpCircle
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { 
    currentRoute, 
    navigate, 
    sidebarCollapsed, 
    toggleSidebar, 
    user, 
    logout,
    assets
  } = useStore();

  const navItems: { route: AppRoute; label: string; icon: React.ComponentType<{ className?: string }>; badge?: string | number }[] = [
    { route: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { route: 'workspace', label: 'Studio Workspace', icon: Wand2 },
    { route: 'generate', label: 'Inspiration Hub', icon: Sparkles },
    { route: 'viewer', label: '3D Viewer', icon: Box },
    { route: 'library', label: 'Asset Library', icon: FolderGit2, badge: assets.length },
    { route: 'history', label: 'Generation History', icon: Clock },
    { route: 'settings', label: 'User Settings', icon: Settings },
  ];

  return (
    <aside
      className={`fixed top-0 left-0 bottom-0 z-40 bg-[#070a13] border-r border-slate-800/80 transition-all duration-300 flex flex-col justify-between ${
        sidebarCollapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Top Brand Logo */}
      <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
        <div 
          onClick={() => navigate('dashboard')}
          className="flex items-center gap-3 cursor-pointer group overflow-hidden"
        >
          <div className="w-10 h-10 shrink-0 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/25 group-hover:scale-105 transition-transform duration-200">
            <Box className="w-5 h-5" />
          </div>
          {!sidebarCollapsed && (
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-base tracking-tight text-white">PolyGen</span>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-blue-500/10 border border-blue-500/20 text-blue-400 font-semibold">
                  PRO
                </span>
              </div>
              <span className="text-[10px] text-slate-400 truncate">Text-to-3D Pipeline</span>
            </div>
          )}
        </div>

        {/* Sidebar Collapse Toggle Button */}
        <button
          onClick={toggleSidebar}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors"
          title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1.5 scrollbar-thin">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentRoute === item.route;

          return (
            <button
              key={item.route}
              onClick={() => navigate(item.route)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all group relative ${
                isActive
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/25 font-semibold'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900/80'
              }`}
              title={sidebarCollapsed ? item.label : undefined}
            >
              <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-white' : 'text-slate-400 group-hover:text-blue-400'}`} />
              {!sidebarCollapsed && <span className="truncate">{item.label}</span>}
              {!sidebarCollapsed && item.badge !== undefined && (
                <span className={`ml-auto text-[10px] px-2 py-0.5 rounded-full font-mono font-medium ${
                  isActive ? 'bg-white/20 text-white' : 'bg-slate-800 text-slate-300'
                }`}>
                  {item.badge}
                </span>
              )}

              {/* Collapsed Tooltip */}
              {sidebarCollapsed && (
                <div className="absolute left-full ml-3 px-2.5 py-1.5 bg-slate-900 text-slate-200 text-xs rounded-lg border border-slate-800 whitespace-nowrap shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50">
                  {item.label}
                </div>
              )}
            </button>
          );
        })}

        {/* Quick Launch Button when not collapsed */}
        {!sidebarCollapsed && (
          <div className="pt-4 mt-4 border-t border-slate-800/60">
            <button
              onClick={() => navigate('workspace')}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/20 text-xs font-semibold transition-all"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Quick Generate</span>
            </button>
          </div>
        )}
      </div>

      {/* Footer: Hardware Status & User Profile */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-950/40 space-y-3">
        {/* Pipeline Telemetry Badge */}
        {!sidebarCollapsed ? (
          <div className="p-2.5 bg-slate-900/80 rounded-xl border border-slate-800/80 text-[11px] space-y-1">
            <div className="flex items-center justify-between text-slate-400">
              <span className="flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-blue-400" />
                <span>AI Pipeline</span>
              </span>
              <span className="flex items-center gap-1 text-emerald-400 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Active
              </span>
            </div>
            <div className="text-[10px] text-slate-400 font-mono">Engine: Shap-E & PBR</div>
          </div>
        ) : (
          <div className="flex justify-center" title="Engine: Shap-E & PBR (Active)">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          </div>
        )}

        {/* User Card */}
        {user ? (
          <div className="flex items-center justify-between gap-2">
            <div 
              onClick={() => navigate('settings')}
              className="flex items-center gap-2 overflow-hidden cursor-pointer hover:opacity-80 transition-opacity"
            >
              <div className="w-8 h-8 shrink-0 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
                <UserIcon className="w-4 h-4" />
              </div>
              {!sidebarCollapsed && (
                <div className="truncate text-left">
                  <div className="text-xs font-semibold text-slate-200 truncate">{user.username}</div>
                  <div className="text-[10px] text-slate-400 truncate">{user.email}</div>
                </div>
              )}
            </div>
            {!sidebarCollapsed && (
              <button
                onClick={logout}
                className="p-1.5 text-slate-400 hover:text-rose-400 transition-colors"
                title="Log out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-1.5">
            <button
              onClick={() => navigate('login')}
              className="w-full py-2 px-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition-all text-center"
            >
              {sidebarCollapsed ? <UserIcon className="w-4 h-4 mx-auto" /> : 'Sign In'}
            </button>
          </div>
        )}

        {/* Public Landing Link */}
        {!sidebarCollapsed && (
          <button
            onClick={() => navigate('landing')}
            className="w-full flex items-center justify-center gap-1.5 text-[11px] text-slate-400 hover:text-slate-200 transition-colors pt-1"
          >
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Product Showcase</span>
          </button>
        )}
      </div>
    </aside>
  );
};

