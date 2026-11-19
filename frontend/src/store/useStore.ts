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

export interface PBRSettings {
  name: string;
  materialClass: string;
  baseColor: string;
  baseColorOpacity: number;
  metallic: number;
  roughness: number;
  normalScale: number;
  aoIntensity: number;
  emissiveColor: string;
  emissiveIntensity: number;
  alphaMode: 'OPAQUE' | 'MASK' | 'BLEND';
  alphaCutoff: number;
  doubleSided: boolean;
}

export const DEFAULT_PBR_SETTINGS: PBRSettings = {
  name: 'Standard PBR',
  materialClass: 'dielectric_mineral',
  baseColor: '#ffffff',
  baseColorOpacity: 1.0,
  metallic: 0.1,
  roughness: 0.45,
  normalScale: 1.0,
  aoIntensity: 1.0,
  emissiveColor: '#000000',
  emissiveIntensity: 0.0,
  alphaMode: 'OPAQUE',
  alphaCutoff: 0.5,
  doubleSided: false,
};

export const PBR_PRESETS: Record<string, PBRSettings> = {
  rusted_sword: {
    name: 'Rusted Broadsword',
    materialClass: 'oxidized_metal',
    baseColor: '#8a7968',
    baseColorOpacity: 1.0,
    metallic: 0.82,
    roughness: 0.48,
    normalScale: 1.4,
    aoIntensity: 1.0,
    emissiveColor: '#1e3a8a',
    emissiveIntensity: 0.35,
    alphaMode: 'OPAQUE',
    alphaCutoff: 0.5,
    doubleSided: false,
  },
  glowing_sapphire: {
    name: 'Glowing Sapphire Gem',
    materialClass: 'emissive_gemstone',
    baseColor: '#1d4ed8',
    baseColorOpacity: 0.85,
    metallic: 0.0,
    roughness: 0.08,
    normalScale: 0.3,
    aoIntensity: 0.2,
    emissiveColor: '#38bdf8',
    emissiveIntensity: 2.8,
    alphaMode: 'BLEND',
    alphaCutoff: 0.5,
    doubleSided: true,
  },
  carved_wood: {
    name: 'Carved Oak Wood',
    materialClass: 'dielectric_organic',
    baseColor: '#78350f',
    baseColorOpacity: 1.0,
    metallic: 0.0,
    roughness: 0.72,
    normalScale: 1.1,
    aoIntensity: 1.0,
    emissiveColor: '#000000',
    emissiveIntensity: 0.0,
    alphaMode: 'OPAQUE',
    alphaCutoff: 0.5,
    doubleSided: false,
  },
  granite_stone: {
    name: 'Ancient Granite Stone',
    materialClass: 'dielectric_mineral',
    baseColor: '#64748b',
    baseColorOpacity: 1.0,
    metallic: 0.02,
    roughness: 0.88,
    normalScale: 1.6,
    aoIntensity: 1.0,
    emissiveColor: '#000000',
    emissiveIntensity: 0.0,
    alphaMode: 'OPAQUE',
    alphaCutoff: 0.5,
    doubleSided: false,
  },
  translucent_glass: {
    name: 'Translucent Glass',
    materialClass: 'glass_optical',
    baseColor: '#e0f2fe',
    baseColorOpacity: 0.35,
    metallic: 0.02,
    roughness: 0.05,
    normalScale: 0.2,
    aoIntensity: 0.1,
    emissiveColor: '#000000',
    emissiveIntensity: 0.0,
    alphaMode: 'BLEND',
    alphaCutoff: 0.5,
    doubleSided: true,
  },
  polished_gold: {
    name: 'Polished Noble Gold',
    materialClass: 'conductor_pure',
    baseColor: '#fbbf24',
    baseColorOpacity: 1.0,
    metallic: 1.0,
    roughness: 0.14,
    normalScale: 0.5,
    aoIntensity: 0.8,
    emissiveColor: '#000000',
    emissiveIntensity: 0.0,
    alphaMode: 'OPAQUE',
    alphaCutoff: 0.5,
    doubleSided: false,
  },
};

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
  refreshToken: string | null;
  isAuthChecking: boolean;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  setRefreshToken: (refreshToken: string | null) => void;
  setIsAuthChecking: (checking: boolean) => void;
  setSession: (token: string, refreshToken: string | null, user: User) => void;
  updateUser: (partial: Partial<User>) => void;
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
  renderMode: 'textured' | 'wireframe' | 'solid' | 'normals' | 'unlit';
  setRenderMode: (mode: 'textured' | 'wireframe' | 'solid' | 'normals' | 'unlit') => void;
  showGrid: boolean;
  setShowGrid: (show: boolean) => void;
  showAxes: boolean;
  setShowAxes: (show: boolean) => void;
  showBoundingBox: boolean;
  setShowBoundingBox: (show: boolean) => void;
  showWireframeOverlay: boolean;
  setShowWireframeOverlay: (show: boolean) => void;
  autoRotate: boolean;
  setAutoRotate: (rotate: boolean) => void;
  environmentPreset: 'city' | 'sunset' | 'studio' | 'warehouse' | 'night' | 'forest' | 'dawn';
  setEnvironmentPreset: (preset: 'city' | 'sunset' | 'studio' | 'warehouse' | 'night' | 'forest' | 'dawn') => void;
  environmentIntensity: number;
  setEnvironmentIntensity: (intensity: number) => void;
  showEnvironmentBackground: boolean;
  setShowEnvironmentBackground: (show: boolean) => void;
  ambientIntensity: number;
  setAmbientIntensity: (intensity: number) => void;
  directionalIntensity: number;
  setDirectionalIntensity: (intensity: number) => void;
  viewportBgColor: string;
  setViewportBgColor: (color: string) => void;
  cameraFov: number;
  setCameraFov: (fov: number) => void;
  shadowsEnabled: boolean;
  setShadowsEnabled: (enabled: boolean) => void;
  doubleSidedRendering: boolean;
  setDoubleSidedRendering: (doubleSided: boolean) => void;
  viewerPropertiesTab: 'shading' | 'lighting' | 'camera';
  setViewerPropertiesTab: (tab: 'shading' | 'lighting' | 'camera') => void;
  isPropertiesPanelOpen: boolean;
  setIsPropertiesPanelOpen: (open: boolean) => void;

  // PBR Material System State
  pbrSettings: PBRSettings;
  isMaterialPanelOpen: boolean;
  setIsMaterialPanelOpen: (open: boolean) => void;
  updatePBRSettings: (patch: Partial<PBRSettings>) => void;
  applyPBRPreset: (presetKey: string) => void;

  // Mesh Optimizer State
  polygonBudgetSetting: 'low' | 'medium' | 'high' | 'custom';
  customPolygonBudget: number;
  lastOptimizationReport: any | null;
  isOptimizerPanelOpen: boolean;
  setPolygonBudgetSetting: (preset: 'low' | 'medium' | 'high' | 'custom') => void;
  setCustomPolygonBudget: (budget: number) => void;
  setLastOptimizationReport: (report: any | null) => void;
  setIsOptimizerPanelOpen: (open: boolean) => void;

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
  refreshToken: localStorage.getItem('polygen_refresh_token'),
  isAuthChecking: !!localStorage.getItem('polygen_token'),
  setUser: (user) => set({ user }),
  setToken: (token) => {
    if (token) localStorage.setItem('polygen_token', token);
    else localStorage.removeItem('polygen_token');
    set({ token });
  },
  setRefreshToken: (refreshToken) => {
    if (refreshToken) localStorage.setItem('polygen_refresh_token', refreshToken);
    else localStorage.removeItem('polygen_refresh_token');
    set({ refreshToken });
  },
  setIsAuthChecking: (isAuthChecking) => set({ isAuthChecking }),
  setSession: (token, refreshToken, user) => {
    localStorage.setItem('polygen_token', token);
    if (refreshToken) {
      localStorage.setItem('polygen_refresh_token', refreshToken);
    }
    set({ token, refreshToken, user, isAuthChecking: false });
  },
  updateUser: (partial) =>
    set((state) => ({
      user: state.user ? { ...state.user, ...partial } : null,
    })),
  logout: () => {
    localStorage.removeItem('polygen_token');
    localStorage.removeItem('polygen_refresh_token');
    set({
      user: null,
      token: null,
      refreshToken: null,
      assets: [],
      jobs: [],
      activeAsset: null,
      currentRoute: 'login',
    });
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
  showBoundingBox: false,
  setShowBoundingBox: (showBoundingBox) => set({ showBoundingBox }),
  showWireframeOverlay: false,
  setShowWireframeOverlay: (showWireframeOverlay) => set({ showWireframeOverlay }),
  autoRotate: false,
  setAutoRotate: (autoRotate) => set({ autoRotate }),
  environmentPreset: 'city',
  setEnvironmentPreset: (environmentPreset) => set({ environmentPreset }),
  environmentIntensity: 1.0,
  setEnvironmentIntensity: (environmentIntensity) => set({ environmentIntensity }),
  showEnvironmentBackground: false,
  setShowEnvironmentBackground: (showEnvironmentBackground) => set({ showEnvironmentBackground }),
  ambientIntensity: 0.7,
  setAmbientIntensity: (ambientIntensity) => set({ ambientIntensity }),
  directionalIntensity: 1.4,
  setDirectionalIntensity: (directionalIntensity) => set({ directionalIntensity }),
  viewportBgColor: '#090d16',
  setViewportBgColor: (viewportBgColor) => set({ viewportBgColor }),
  cameraFov: 45,
  setCameraFov: (cameraFov) => set({ cameraFov }),
  shadowsEnabled: true,
  setShadowsEnabled: (shadowsEnabled) => set({ shadowsEnabled }),
  doubleSidedRendering: true,
  setDoubleSidedRendering: (doubleSidedRendering) => set({ doubleSidedRendering }),
  viewerPropertiesTab: 'shading',
  setViewerPropertiesTab: (viewerPropertiesTab) => set({ viewerPropertiesTab }),
  isPropertiesPanelOpen: false,
  setIsPropertiesPanelOpen: (isPropertiesPanelOpen) => set({ isPropertiesPanelOpen }),

  // PBR Material System State & Actions
  pbrSettings: DEFAULT_PBR_SETTINGS,
  isMaterialPanelOpen: false,
  setIsMaterialPanelOpen: (isMaterialPanelOpen) => set({ isMaterialPanelOpen }),
  updatePBRSettings: (patch) =>
    set((state) => ({
      pbrSettings: { ...state.pbrSettings, ...patch },
    })),
  applyPBRPreset: (presetKey) => {
    const preset = PBR_PRESETS[presetKey];
    if (preset) {
      set({ pbrSettings: { ...preset } });
    }
  },

  // Mesh Optimizer Defaults & Actions
  polygonBudgetSetting: 'medium',
  customPolygonBudget: 10000,
  lastOptimizationReport: null,
  isOptimizerPanelOpen: false,
  setPolygonBudgetSetting: (polygonBudgetSetting) => set({ polygonBudgetSetting }),
  setCustomPolygonBudget: (customPolygonBudget) => set({ customPolygonBudget }),
  setLastOptimizationReport: (lastOptimizationReport) => set({ lastOptimizationReport }),
  setIsOptimizerPanelOpen: (isOptimizerPanelOpen) => set({ isOptimizerPanelOpen }),

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
