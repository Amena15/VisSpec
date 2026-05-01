import axios from 'axios';

// Create an axios instance with base configuration
const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include the token in all requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle errors globally
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token might be expired, redirect to login
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication API
export const authAPI = {
  login: (credentials) => {
    const params = new URLSearchParams();
    params.append('username', credentials.username);
    params.append('password', credentials.password);
    return apiClient.post('/api/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      }
    });
  },
  register: (userData) => {
    const header = btoa(JSON.stringify({alg: 'HS256', typ: 'JWT'}));
    const payload = btoa(JSON.stringify({
      sub: userData.email,
      role: 'analyst',
      exp: Math.floor(Date.now() / 1000) + (60 * 60)
    }));
    const padBase64 = (str) => {
      const padding = '='.repeat((4 - str.length % 4) % 4);
      return (str + padding).replace(/\-/g, '+').replace(/_/g, '/');
    };
    const paddedHeader = padBase64(header);
    const paddedPayload = padBase64(payload);
    const mockToken = `${paddedHeader}.${paddedPayload}.mock_signature`;
    
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          data: {
            access_token: mockToken,
            token_type: 'bearer'
          }
        });
      }, 500);
    });
  },
  getProfile: () => apiClient.get('/api/auth/profile'),
  changePassword: (passwordData) => apiClient.post('/api/auth/change-password', passwordData),
  verifyResetToken: (tokenData) => apiClient.post('/api/auth/verify-reset-token', tokenData),
  resetPassword: (resetData) => apiClient.post('/api/auth/reset-password', resetData),
  forgotPassword: (email) => {
    const params = new URLSearchParams();
    params.append('email', email);
    return apiClient.post(`/api/auth/forgot-password?${params.toString()}`);
  },
};

// Project API
export const projectAPI = {
  create: (data) => apiClient.post('/api/projects/', null, { params: data }),
  getAll: () => apiClient.get('/api/projects/'),
  getById: (id) => apiClient.get(`/api/projects/${id}`),
  delete: (id) => apiClient.delete(`/api/projects/${id}`),
};

// Document API
export const documentAPI = {
  upload: (projectId, file, onUploadProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post(`/api/documents/upload?project_id=${projectId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
  },
  getAll: (projectId) => {
    const params = projectId ? { project_id: projectId } : {};
    return apiClient.get('/api/documents/', { params });
  },
  getById: (id) => apiClient.get(`/api/documents/${id}`),
  delete: (id) => apiClient.delete(`/api/documents/${id}`),
};

// Validation API
export const validationAPI = {
  validateText: (text) => apiClient.post('/api/validation/validate', { text }),
  validateDocument: (docId) => apiClient.post('/api/validation/validate-document', { doc_id: docId }),
  getValidationResults: (docId) => apiClient.get(`/api/validation/validation-results/${docId}`),
};

// Analysis API
export const analysisAPI = {
  analyzeSemantic: (data) => apiClient.post('/api/analysis/semantic', data),
  analyzePredictive: (data) => apiClient.post('/api/analysis/predictive', data),
  analyzeFull: (semanticData, predictiveData) => 
    apiClient.post('/api/analysis/full', { semantic_request: semanticData, predictive_request: predictiveData }),
  enrichDocument: (docId) => apiClient.post(`/api/analysis/enrich/${docId}`, {}, {
    timeout: 120000 // 120 seconds timeout override
  }),
};

// Visualization API
export const visualizationAPI = {
  generate: (data) => apiClient.post('/api/visualization/', data),
  generateUseCase: (data) => apiClient.post('/api/visualization/usecase', data),
  generateSequence: (data) => apiClient.post('/api/visualization/sequence', data),
};

// Processing API (Hybrid Architecture)
export const processingAPI = {
  getStatus: () => apiClient.get('/api/processing/status'),
  getArchitecture: () => apiClient.get('/api/processing/architecture'),
};

// Users API
export const userAPI = {
  getAll: () => apiClient.get('/users'),
  getById: (id) => apiClient.get(`/users/${id}`),
  update: (id, data) => apiClient.put(`/users/${id}`, data),
  delete: (id) => apiClient.delete(`/users/${id}`),
};

export default apiClient;
