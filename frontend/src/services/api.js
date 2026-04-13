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
    // Login expects form URL-encoded data, not JSON
    const params = new URLSearchParams();
    params.append('username', credentials.username);
    params.append('password', credentials.password);
    return apiClient.post('/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      }
    });
  },
  register: (userData) => {
    // Mock registration response with valid JWT structure for development
    // Create a mock JWT token with proper base64 encoded parts
    const header = btoa(JSON.stringify({alg: 'HS256', typ: 'JWT'}));
    const payload = btoa(JSON.stringify({
      sub: userData.email,
      role: 'analyst',  // Default role for new registrants
      exp: Math.floor(Date.now() / 1000) + (60 * 60) // 1 hour from now
    }));
    // Pad the base64 strings if needed
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
  getProfile: () => apiClient.get('/auth/profile'),
  verifyResetToken: (tokenData) => apiClient.post('/auth/verify-reset-token', tokenData),
  resetPassword: (resetData) => apiClient.post('/auth/reset-password', resetData),
  forgotPassword: (email) => {
    const params = new URLSearchParams();
    params.append('email', email);
    return apiClient.post(`/auth/forgot-password?${params.toString()}`);
  },
};

// Analysis API
export const analysisAPI = {
  analyzeSemantic: (data) => apiClient.post('/analysis/semantic', data),
  analyzePredictive: (data) => apiClient.post('/analysis/predictive', data),
  analyzeFull: (semanticData, predictiveData) => 
    apiClient.post('/analysis/full', { semantic_request: semanticData, predictive_request: predictiveData }),
};

// Visualization API
export const visualizationAPI = {
  generate: (data) => apiClient.post('/visualization/', data),
  generateUseCase: (data) => apiClient.post('/visualization/usecase', data),
  generateSequence: (data) => apiClient.post('/visualization/sequence', data),
};

// Document API
export const documentAPI = {
  getAll: () => apiClient.get('/documents'),
  getById: (id) => apiClient.get(`/documents/${id}`),
  create: (data) => apiClient.post('/documents', data),
  update: (id, data) => apiClient.put(`/documents/${id}`, data),
  delete: (id) => apiClient.delete(`/documents/${id}`),
};

// Users API
export const userAPI = {
  getAll: () => apiClient.get('/users'),
  getById: (id) => apiClient.get(`/users/${id}`),
  update: (id, data) => apiClient.put(`/users/${id}`, data),
  delete: (id) => apiClient.delete(`/users/${id}`),
};

export default apiClient;