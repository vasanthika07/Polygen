import { create } from 'zustand';
import type { User, Asset, JobStatus } from '../services/api';

export type AppRoute =
  | 'landing'
  | 'login'
  | 'register'
  | 'dashboard'
  | 'generate'
  | 'workspace'
  | 'viewer'
  | 'library'
  | 'history'
  | 'asset-details'
  | 'settings'
  | 'not-found'
  | 'error';

export interface GenerationUpdate {
  stage: string;
  progress: number;
  message: string;
  data?: any;
}

export interface UserSettings {
  defaultStyle: string;
  defaultQuality: string;
  defaultPolygonBudget: number;
  defaultTextureResolution: number;
  aiBackendPreference: string;
  theme: string;
  apiKey: string;
}

export interface AppNotification {
  id: string;
  title: string;
  message: string;
  type: 'success' | 'info' | 'warning' | 'error';
  timestamp: string;
}

interface AppState {
  // Navigation & Routing
  currentRoute: AppRoute;
  previousRoute: AppRoute | null;
  selectedAssetId: string | null;
  selectedJobId: string | null;
  navigate: (route: AppRoute, params?: { assetId?: string; jobId?: string }) => void;
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;

  // Authentication
  user: User | null;
  token: string | null;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  logout: () => void;

  // Active Generation Job & Real-time Progress
  currentJob: JobStatus | null;
  generationStage: string;
  generationProgress: number;
  generationMessage: string;
  generationData: any;
  isGenerating: boolean;
  generationPrompt: string;
  setGenerationPrompt: (prompt: string) => void;
  setCurrentJob: (job: JobStatus | null) => void;
  updateGenerationProgress: (update: GenerationUpdate) => void;
  setIsGenerating: (isGenerating: boolean) => void;

  // Active Asset in 3D Viewport
  activeAsset: Asset | null;
  setActiveAsset: (asset: Asset | null) => void;

  // Asset Library & History Lists
  assets: Asset[];
  setAssets: (assets: Asset[]) => void;
  addAsset: (asset: Asset) => void;
  removeAsset: (assetId: string) => void;

  jobs: JobStatus[];
  setJobs: (jobs: JobStatus[]) => void;
  addJob: (job: JobStatus) => void;

  // Interactive 3D Viewport Controls
  renderMode: 'textured' | 'wireframe' | 'solid' | 'normals';
  setRenderMode: (mode: 'textured' | 'wireframe' | 'solid' | 'normals') => void;
  showGrid: boolean;
  setShowGrid: (show: boolean) => void;
  showAxes: boolean;
  setShowAxes: (show: boolean) => void;
  autoRotate: boolean;
  setAutoRotate: (rotate: boolean) => void;
  environmentPreset: 'city' | 'sunset' | 'studio' | 'warehouse' | 'night';
  setEnvironmentPreset: (preset: 'city' | 'sunset' | 'studio' | 'warehouse' | 'night') => void;
  ambientIntensity: number;
  setAmbientIntensity: (intensity: number) => void;
  directionalIntensity: number;
  setDirectionalIntensity: (intensity: number) => void;

  // User Settings
  settings: UserSettings;
  updateSettings: (newSettings: Partial<UserSettings>) => void;

  // Notifications
  notifications: AppNotification[];
  addNotification: (notification: Omit<AppNotification, 'id' | 'timestamp'>) => void;
  dismissNotification: (id: string) => void;
  clearNotifications: () => void;
}

export const useStore = create<AppState>((set, get) => ({
  // Navigation Defaults
  currentRoute: 'dashboard',
  previousRoute: null,
  selectedAssetId: null,
  selectedJobId: null,
  navigate: (route, params) => {
    const prev = get().currentRoute;
    set({
      previousRoute: prev,
      currentRoute: route,
      selectedAssetId: params?.assetId || null,
      selectedJobId: params?.jobId || null,
    });
    // Scroll window to top on navigation
    window.scrollTo({ top: 0, behavior: 'smooth' });
  },
  sidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),

  // Authentication
  user: null,
  token: localStorage.getItem('polygen_token'),
  setUser: (user) => set({ user }),
  setToken: (token) => {
    if (token) localStorage.setItem('polygen_token', token);
    else localStorage.removeItem('polygen_token');
    set({ token });
  },
  logout: () => {
    localStorage.removeItem('polygen_token');
    set({ user: null, token: null, currentRoute: 'landing' });
  },

  // Active Job State
  currentJob: null,
  generationStage: 'idle',
  generationProgress: 0,
  generationMessage: '',
  generationData: null,
  isGenerating: false,
  generationPrompt: 'A rusted medieval broadsword with a glowing blue sapphire in the hilt.',
  setGenerationPrompt: (generationPrompt) => set({ generationPrompt }),
  setCurrentJob: (currentJob) => set({ currentJob }),
  updateGenerationProgress: (update) =>
    set({
      generationStage: update.stage,
      generationProgress: update.progress,
      generationMessage: update.message,
      generationData: update.data || null,
      isGenerating: update.progress < 100 && update.stage !== 'failed',
    }),
  setIsGenerating: (isGenerating) => set({ isGenerating }),

  // Active Asset
  activeAsset: null,
  setActiveAsset: (activeAsset) => set({ activeAsset }),

  // Lists
  assets: [],
  setAssets: (assets) => set({ assets }),
  addAsset: (asset) => set((state) => ({ assets: [asset, ...state.assets] })),
  removeAsset: (assetId) =>
    set((state) => ({
      assets: state.assets.filter((a) => a.asset_id !== assetId),
      activeAsset: state.activeAsset?.asset_id === assetId ? null : state.activeAsset,
    })),

  jobs: [],
  setJobs: (jobs) => set({ jobs }),
  addJob: (job) => set((state) => ({ jobs: [job, ...state.jobs] })),

  // 3D Viewport Controls
  renderMode: 'textured',
  setRenderMode: (renderMode) => set({ renderMode }),
  showGrid: true,
  setShowGrid: (showGrid) => set({ showGrid }),
  showAxes: false,
  setShowAxes: (showAxes) => set({ showAxes }),
  autoRotate: false,
  setAutoRotate: (autoRotate) => set({ autoRotate }),
  environmentPreset: 'city',
  setEnvironmentPreset: (environmentPreset) => set({ environmentPreset }),
  ambientIntensity: 0.7,
  setAmbientIntensity: (ambientIntensity) => set({ ambientIntensity }),
  directionalIntensity: 1.4,
  setDirectionalIntensity: (directionalIntensity) => set({ directionalIntensity }),

  // Settings
  settings: {
    defaultStyle: 'medieval fantasy',
    defaultQuality: 'high',
    defaultPolygonBudget: 10000,
    defaultTextureResolution: 1024,
    aiBackendPreference: 'local_shape',
    theme: 'dark',
    apiKey: 'poly_live_sec_8f9104bd39',
  },
  updateSettings: (newSettings) =>
    set((state) => ({
      settings: { ...state.settings, ...newSettings },
    })),

  // Notifications
  notifications: [
    {
      id: 'welcome_1',
      title: 'PolyGen Ready',
      message: 'Spatial computing generative pipeline initialized successfully.',
      type: 'info',
      timestamp: new Date().toLocaleTimeString(),
    },
  ],
  addNotification: (notif) => {
    const item: AppNotification = {
      ...notif,
      id: `notif_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    set((state) => ({ notifications: [item, ...state.notifications] }));
  },
  dismissNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
  clearNotifications: () => set({ notifications: [] }),
}));
