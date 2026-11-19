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
  duration_seconds?: number;
  configuration?: {
    style?: string;
    quality?: string;
    polygon_budget?: number;
    target_format?: string;
  };
  asset?: Asset;
}

/**
 * Safely extracts human-readable error messages from any backend failure response,
 * preventing React runtime crashes on FastAPI 422 arrays or nested error objects.
 */
export const extractErrorMessage = (err: any, fallback = 'An unexpected error occurred. Please try again.'): string => {
  if (!err) return fallback;

  // 0. Specific HTTP Gateway & Server Availability status codes
  if (err.response?.status === 502) {
    return 'PolyGen backend service is unreachable (502 Bad Gateway). Please ensure the backend server is running on port 8000.';
  }
  if (err.response?.status === 503) {
    return 'PolyGen service is temporarily unavailable (503). Please try again in a few moments.';
  }
  if (err.response?.status === 504) {
    return 'Gateway timeout (504). The AI generation or request took too long to respond.';
  }

  // 1. Custom structured domain error payload with detailed field validation messages
  const errorObj = err.response?.data?.error;
  if (errorObj) {
    if (Array.isArray(errorObj.details) && errorObj.details.length > 0) {
      const messages = errorObj.details
        .map((d: any) => d.message || d.msg || `${d.field}: invalid value`)
        .filter(Boolean);
      if (messages.length > 0) return messages.join('. ');
    }
    if (typeof errorObj.message === 'string' && errorObj.message.trim()) {
      return errorObj.message.trim();
    }
  }

  // 2. FastAPI default detail field
  const detail = err.response?.data?.detail;
  if (typeof detail === 'string' && detail.trim()) {
    return detail.trim();
  }
  if (Array.isArray(detail) && detail.length > 0) {
    const messages = detail
      .map((d: any) => d.msg || d.message || JSON.stringify(d))
      .filter(Boolean);
    if (messages.length > 0) return messages.join('. ');
  }
  if (typeof detail === 'object' && detail !== null) {
    if (typeof detail.message === 'string') return detail.message;
    if (typeof detail.msg === 'string') return detail.msg;
  }

  // 3. Top-level response message
  if (typeof err.response?.data?.message === 'string' && err.response.data.message.trim()) {
    return err.response.data.message.trim();
  }

  // 4. Axios standard network error
  if (err.message === 'Network Error' || err.code === 'ERR_NETWORK') {
    return 'Unable to connect to PolyGen server. Please check your network connection or server status.';
  }
  if (typeof err.message === 'string' && err.message.trim()) {
    return err.message.trim();
  }

  return fallback;
};

export const authApi = {
  register: (data: { name?: string; username?: string; email: string; password: string }) =>
    api.post<AuthResponse>('/auth/register', data),
  login: (data: { username_or_email?: string; email?: string; username?: string; password: string }) =>
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
  listJobs: (params?: { limit?: number; offset?: number; status?: string; search?: string } | number, offset: number = 0) => {
    if (typeof params === 'number') {
      return api.get<JobStatus[]>(`/jobs?limit=${params}&offset=${offset}`);
    }
    const q = new URLSearchParams();
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.offset) q.set('offset', String(params.offset));
    if (params?.status && params.status !== 'all') q.set('status', params.status);
    if (params?.search) q.set('search', params.search);
    const queryString = q.toString();
    return api.get<JobStatus[]>(queryString ? `/jobs?${queryString}` : '/jobs');
  },
};

export const assetApi = {
  listAssets: (params?: { limit?: number; offset?: number; search?: string; sort_by?: string; date_filter?: string } | number, offset: number = 0) => {
    if (typeof params === 'number') {
      return api.get<{ items: Asset[]; total: number }>(`/assets?limit=${params}&offset=${offset}`);
    }
    const q = new URLSearchParams();
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.offset) q.set('offset', String(params.offset));
    if (params?.search) q.set('search', params.search);
    if (params?.sort_by) q.set('sort_by', params.sort_by);
    if (params?.date_filter) q.set('date_filter', params.date_filter);
    const queryString = q.toString();
    return api.get<{ items: Asset[]; total: number }>(queryString ? `/assets?${queryString}` : '/assets');
  },
  getAsset: (assetId: string) =>
    api.get<Asset>(`/assets/${assetId}`),
  deleteAsset: (assetId: string) =>
    api.delete(`/assets/${assetId}`),
  getDownloadUrl: (assetId: string, exportOption: string = 'standard') => {
    const token = localStorage.getItem('polygen_token');
    const params = new URLSearchParams();
    if (exportOption && exportOption !== 'standard') {
      params.set('export_option', exportOption);
    }
    if (token) {
      params.set('token', token);
    }
    const query = params.toString();
    return query ? `/api/assets/${assetId}/download?${query}` : `/api/assets/${assetId}/download`;
  },
  getPreviewUrl: (assetId: string) => {
    const token = localStorage.getItem('polygen_token');
    return token
      ? `/api/assets/${assetId}/preview?token=${encodeURIComponent(token)}`
      : `/api/assets/${assetId}/preview`;
  },
};

export interface PromptSpecification {
  object: string;
  style: string;
  materials: string[];
  colors: string[];
  surface_details: string[];
  lighting: string;
  special_effects: string[];
  geometry_requirements: string[];
  texture_requirements: string[];
  negative_prompt: string[];
  category?: string;
  shape_and_geometry?: {
    primary_shape: string;
    symmetry: string;
    proportions: string;
    topology: string;
  };
  model_prompts?: {
    shap_e: string;
    hunyuan3d: string;
    stable_diffusion: string;
    triposr: string;
  };
  inferred_details?: string[];
  confidence: number;
  raw_prompt?: string;
}

export const promptApi = {
  analyze: (data: {
    prompt: string;
    style_override?: string;
    quality?: string;
    polygon_budget?: number;
    target_format?: string;
  }) => api.post<PromptSpecification>('/prompt/analyze', data),
};

export const healthApi = {
  check: () => api.get('/health'),
};

export interface MaterialEvaluationResponse {
  classification: {
    material_class: string;
    conductor_score: number;
    dielectric_score: number;
    transparency_score: number;
    emissive_score: number;
    confidence: number;
  };
  gltf_pbr_parameters: {
    name: string;
    material_class: string;
    base_color_factor: [number, number, number, number];
    metallic_factor: number;
    roughness_factor: number;
    normal_scale: number;
    occlusion_strength: number;
    emissive_factor: [number, number, number];
    emissive_intensity: number;
    alpha_mode: 'OPAQUE' | 'MASK' | 'BLEND';
    alpha_cutoff: number;
    double_sided: boolean;
  };
  gltf_validation: {
    is_valid: boolean;
    errors: string[];
    warnings: string[];
    gltf_compliance_score: number;
    status: string;
  };
}

export const materialsApi = {
  getPresets: () => api.get<{ count: number; presets: Record<string, any> }>('/materials/presets'),
  evaluate: (data: {
    prompt?: string;
    material_type?: string;
    details?: string[];
    custom_overrides?: Record<string, any>;
  }) => api.post<MaterialEvaluationResponse>('/materials/evaluate', data),
};

export interface MeshAnalysisResponse {
  polygon_count: number;
  vertex_count: number;
  triangle_density: number;
  surface_area: number;
  volume: number;
  is_watertight: boolean;
  is_manifold: boolean;
  boundary_edges_count: number;
  has_uv: boolean;
  has_normals: boolean;
  has_material: boolean;
  bounding_box: {
    min: [number, number, number];
    max: [number, number, number];
    extents: [number, number, number];
    max_dimension: number;
  };
  recommended_preset: string;
  file_path?: string;
  file_size_bytes?: number;
}

export interface OptimizationReport {
  original_polygon_count: number;
  final_polygon_count: number;
  reduction_percentage: number;
  original_vertex_count: number;
  final_vertex_count: number;
  original_file_size_bytes: number;
  final_file_size_bytes: number;
  file_size_reduction_percentage: number;
  optimization_duration_seconds: number;
  budget_preset: string;
  target_budget: number;
  bounds_before: {
    min: [number, number, number];
    max: [number, number, number];
    extents: [number, number, number];
    max_dimension: number;
  };
  bounds_after: {
    min: [number, number, number];
    max: [number, number, number];
    extents: [number, number, number];
    max_dimension: number;
  };
  validation: {
    status: string;
    is_valid: boolean;
    is_watertight: boolean;
    is_manifold: boolean;
    degenerate_faces: number;
    uv_valid: boolean;
    errors: string[];
    warnings: string[];
  };
  status: string;
}

export interface OptimizationResponse {
  status: string;
  optimized_file_path: string;
  optimized_file_name: string;
  report: OptimizationReport;
}

export const optimizerApi = {
  getPresets: () => api.get<{ presets: Record<string, any> }>('/optimizer/presets'),
  analyze: (data: { asset_id?: string; mesh_path?: string }) =>
    api.post<MeshAnalysisResponse>('/optimizer/analyze', data),
  optimize: (data: {
    asset_id?: string;
    mesh_path?: string;
    budget_preset?: string;
    custom_budget?: number;
    normalize_bounds?: boolean;
    align_ground?: boolean;
    target_scale?: number;
    remove_duplicates?: boolean;
  }) => api.post<OptimizationResponse>('/optimizer/optimize', data),
};

export default api;
