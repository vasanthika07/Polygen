import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT access token from localStorage to every outgoing request
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('polygen_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Automatic token refresh interceptor for handling expired sessions (401)
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (reason?: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 Unauthorized responses
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      // Don't attempt to refresh on login/register/refresh endpoints themselves
      if (
        originalRequest.url?.includes('/auth/login') ||
        originalRequest.url?.includes('/auth/register') ||
        originalRequest.url?.includes('/auth/refresh')
      ) {
        return Promise.reject(error);
      }

      const refreshToken = localStorage.getItem('polygen_refresh_token');
      if (!refreshToken) {
        // No refresh token available; clear session
        localStorage.removeItem('polygen_token');
        localStorage.removeItem('polygen_refresh_token');
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const response = await axios.post(`${BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token: newRefreshToken } = response.data;
        localStorage.setItem('polygen_token', access_token);
        if (newRefreshToken) {
          localStorage.setItem('polygen_refresh_token', newRefreshToken);
        }

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }
        processQueue(null, access_token);
        return api(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        localStorage.removeItem('polygen_token');
        localStorage.removeItem('polygen_refresh_token');
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export interface User {
  id: string;
  name?: string;
  username: string;
  email: string;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  user: User;
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
  id?: string;
  job_id?: string;
  user_id?: string;
  asset_name: string;
  prompt?: string;
  original_prompt?: string;
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
  id?: string;
  user_id?: string;
  prompt: string;
  status: 'pending' | 'queued' | 'processing' | 'completed' | 'failed' | string;
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
  register: (data: { name?: string; username?: string; email: string; password: string }) =>
    api.post<AuthResponse>('/auth/register', data),
  login: (data: { username_or_email: string; password: string }) =>
    api.post<AuthResponse>('/auth/login', data),
  refresh: (refreshToken: string) =>
    api.post<AuthResponse>('/auth/refresh', { refresh_token: refreshToken }),
  logout: () => api.post('/auth/logout'),
  me: () => api.get<User>('/auth/me'),
  updateProfile: (data: { name?: string; email?: string }) =>
    api.put<User>('/auth/me', data),
  changePassword: (data: { current_password: string; new_password: string }) =>
    api.post<{ message: string }>('/auth/change-password', data),
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
  getDownloadUrl: (assetId: string) => {
    const token = localStorage.getItem('polygen_token');
    return token
      ? `/api/assets/${assetId}/download?token=${encodeURIComponent(token)}`
      : `/api/assets/${assetId}/download`;
  },
  getPreviewUrl: (assetId: string) => {
    const token = localStorage.getItem('polygen_token');
    return token
      ? `/api/assets/${assetId}/preview?token=${encodeURIComponent(token)}`
      : `/api/assets/${assetId}/preview`;
  },
};

export const healthApi = {
  check: () => api.get('/health'),
};

export default api;
