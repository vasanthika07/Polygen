import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token from localStorage if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('polygen_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface User {
  id: string;
  username: string;
  email: string;
}

export interface GenerationRequest {
  prompt: string;
  style?: string;
  quality?: string;
  polygon_budget?: number;
  target_format?: string;
}

export interface Asset {
  asset_id: string;
  job_id?: string;
  user_id?: string;
  asset_name: string;
  prompt?: string;
  style?: string;
  glb_url: string;
  preview_url?: string;
  polygon_count: number;
  file_size: number;
  texture_resolution?: number;
  created_at: string;
}

export interface JobStatus {
  job_id: string;
  prompt: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | string;
  progress: number;
  current_stage?: string;
  stage?: string;
  error_message?: string;
  asset_id?: string;
  created_at?: string;
  completed_at?: string;
  asset?: Asset;
}

export const authApi = {
  register: (data: { username: string; email: string; password: string }) =>
    api.post('/auth/register', data),
  login: (data: { username_or_email: string; password: string }) =>
    api.post('/auth/login', data),
  me: () => api.get<User>('/auth/me'),
};

export const generationApi = {
  createJob: (data: GenerationRequest) =>
    api.post<JobStatus>('/generate', data),
  getJobStatus: (jobId: string) =>
    api.get<JobStatus>(`/jobs/${jobId}`),
  listJobs: (limit = 50, offset = 0) =>
    api.get<JobStatus[]>(`/jobs?limit=${limit}&offset=${offset}`),
};

export const assetApi = {
  listAssets: (limit = 50, offset = 0) =>
    api.get<{ items: Asset[]; total: number }>(`/assets?limit=${limit}&offset=${offset}`),
  getAsset: (assetId: string) =>
    api.get<Asset>(`/assets/${assetId}`),
  deleteAsset: (assetId: string) =>
    api.delete(`/assets/${assetId}`),
  getDownloadUrl: (assetId: string) => `/api/assets/${assetId}/download`,
};

export const healthApi = {
  check: () => api.get('/health'),
};

export default api;
