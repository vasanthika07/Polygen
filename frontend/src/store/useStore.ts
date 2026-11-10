import { create } from 'zustand';
import type { User, Asset, JobStatus } from '../services/api';

interface GenerationUpdate {
  stage: string;
  progress: number;
  message: string;
  data?: any;
}

interface AppState {
  // Authentication
  user: User | null;
  token: string | null;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  logout: () => void;

  // Navigation
  activeTab: 'generate' | 'library' | 'dashboard';
  setActiveTab: (tab: 'generate' | 'library' | 'dashboard') => void;

  // Active Generation Job
  currentJob: JobStatus | null;
  generationStage: string;
  generationProgress: number;
  generationMessage: string;
  generationData: any;
  isGenerating: boolean;
  setCurrentJob: (job: JobStatus | null) => void;
  updateGenerationProgress: (update: GenerationUpdate) => void;
  setIsGenerating: (isGenerating: boolean) => void;

  // Active Asset in 3D Viewer
  activeAsset: Asset | null;
  setActiveAsset: (asset: Asset | null) => void;

  // Asset Library
  assets: Asset[];
  setAssets: (assets: Asset[]) => void;
  addAsset: (asset: Asset) => void;
  removeAsset: (assetId: string) => void;

  // 3D Viewport Controls
  renderMode: 'textured' | 'wireframe' | 'solid';
  setRenderMode: (mode: 'textured' | 'wireframe' | 'solid') => void;
  autoRotate: boolean;
  setAutoRotate: (rotate: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
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
    set({ user: null, token: null });
  },

  activeTab: 'generate',
  setActiveTab: (activeTab) => set({ activeTab }),

  currentJob: null,
  generationStage: 'idle',
  generationProgress: 0,
  generationMessage: '',
  generationData: null,
  isGenerating: false,
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

  activeAsset: null,
  setActiveAsset: (activeAsset) => set({ activeAsset }),

  assets: [],
  setAssets: (assets) => set({ assets }),
  addAsset: (asset) => set((state) => ({ assets: [asset, ...state.assets] })),
  removeAsset: (assetId) =>
    set((state) => ({
      assets: state.assets.filter((a) => a.asset_id !== assetId),
      activeAsset: state.activeAsset?.asset_id === assetId ? null : state.activeAsset,
    })),

  renderMode: 'textured',
  setRenderMode: (renderMode) => set({ renderMode }),
  autoRotate: false,
  setAutoRotate: (autoRotate) => set({ autoRotate }),
}));
