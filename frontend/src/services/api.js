import axios from 'axios';

// Create an axios instance with base configuration
const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000',
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
      // Only force logout if we're actually on a protected area.
      // This prevents redirect loops right after login while the UI is transitioning.
      const path = window.location?.pathname || '';
      const isAuthRoute = path.startsWith('/login') || path.startsWith('/forgot-password') || path.startsWith('/reset-password');

      if (!isAuthRoute) {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
    }
    
    // Handle LLM-specific errors
    if (error.response?.status === 429) {

      // Rate limit exceeded - add retry info to error
      error.isRateLimit = true;
      error.message = 'Rate limit exceeded. Please try again later.';
    }
    
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      // Timeout - could be LLM taking too long
      error.isTimeout = true;
      error.isLLMTimeout = true;
      error.message = 'Request timeout. The system may be using rule-based analysis as fallback.';
    }
    
    if (error.response?.status === 500 && error.response?.data?.detail?.includes('LLM')) {
      // LLM-specific server error
      error.isLLMError = true;
      error.message = 'AI analysis unavailable. Using rule-based fallback.';
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
    return apiClient.post('/api/auth/register', userData);
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
  getById: (id, cacheBust = false) => {
    let url = `/api/documents/${id}`;
    if (cacheBust) {
      // Use aggressive cache-busting with multiple parameters
      const timestamp = Date.now();
      const random = Math.random().toString(36).substring(7);
      const random2 = Math.random().toString(36).substring(7);
      const counter = Math.floor(Math.random() * 10000);
      url = `/api/documents/${id}?_t=${timestamp}&_r=${random}&_s=${random2}&_c=${counter}`;
    }
    return apiClient.get(url);
  },
  delete: (id) => apiClient.delete(`/api/documents/${id}`),
  addTraceabilityNote: (requirementId, noteData) => {
    return apiClient.post(`/api/documents/${requirementId}/traceability-notes`, noteData);
  },
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
  applySuggestion: (reqId, newText) => apiClient.post('/api/analysis/apply-suggestion', { req_id: reqId, new_text: newText }),
  undoSuggestion: (reqId) => apiClient.post('/api/analysis/undo', { req_id: reqId }),
};

// Diagrams API (Module 4 - Visualization)
export const diagramsAPI = {
  getUseCaseDiagram: (documentId) => apiClient.get(`/api/diagrams/usecase/${documentId}`),
  getScenarios: (documentId) => apiClient.get(`/api/diagrams/scenarios/${documentId}`),
  getSequenceDiagram: (documentId, scenarioId) => apiClient.get(`/api/diagrams/sequence/${documentId}`, {
    params: { scenario: scenarioId }
  }),
};

// Traceability API
export const traceabilityAPI = {
  getTraceability: (projectId) => {
    if (!projectId) {
      console.error('traceabilityAPI.getTraceability: projectId is required');
      return Promise.reject(new Error('Project ID is required'));
    }
    return apiClient.get(`/api/traceability/${projectId}`);
  },
  
  getDocumentTraceability: (docId) => {
    if (!docId) {
      console.error('traceabilityAPI.getDocumentTraceability: docId is required');
      return Promise.reject(new Error('Document ID is required'));
    }
    return apiClient.get(`/api/traceability/document/${docId}`);
  },
  
  saveNote: (noteData) => {
    if (!noteData.req_id || !noteData.content?.trim()) {
      console.error('traceabilityAPI.saveNote: Missing req_id or content');
      return Promise.reject(new Error('Requirement ID and content are required'));
    }
    console.log('API: Making POST request to /api/traceability/note');
    console.log('API: Request data:', JSON.stringify(noteData, null, 2));
    return apiClient.post('/api/traceability/note', noteData);
  },
  
  deleteNote: (noteId) => {
    if (!noteId) {
      console.error('traceabilityAPI.deleteNote: noteId is required');
      return Promise.reject(new Error('Note ID is required'));
    }
    return apiClient.delete(`/api/traceability/note/${noteId}`);
  },
};

// Notifications API
export const notificationsAPI = {
  getUnread: () => {
    return apiClient.get('/api/notifications/unread');
  },
  
  markRead: (notificationIds) => {
    if (!notificationIds || notificationIds.length === 0) {
      console.error('notificationsAPI.markRead: notificationIds is required');
      return Promise.reject(new Error('Notification IDs are required'));
    }
    return apiClient.post('/api/notifications/mark-read', { notification_ids: notificationIds });
  },
};

// IEEE-Compliant Diagram Generation API
export const ieeeDiagramsAPI = {
  generateDiagram: (documentId, diagramType, scenario = null) => {
    const payload = {
      document_id: documentId,
      diagram_type: diagramType,
      scenario: scenario
    };
    return apiClient.post('/api/ieee-diagrams/generate', payload);
  },
  
  renderPlantUMLToPNG: (plantumlSyntax) => {
    const payload = plantumlSyntax;
    return apiClient.post('/api/ieee-diagrams/render-plantuml-png', payload, {
      headers: { 'Content-Type': 'text/plain' }
    });
  },
  
  getProjectDiagrams: (projectId) => {
    return apiClient.get(`/api/ieee-diagrams/project/${projectId}/diagrams`);
  },
  
  getDiagramDetails: (diagramId) => {
    return apiClient.get(`/api/ieee-diagrams/diagram/${diagramId}`);
  },
};

// Legacy Visualization API (kept for backward compatibility)
export const visualizationAPI = {
  generate: (data) => apiClient.post('/api/visualization/', data),
  generateUseCase: (data) => apiClient.post('/api/visualization/usecase', data),
  generateSequence: (data) => apiClient.post('/api/visualization/sequence', data),
  // Updated to use new diagrams endpoints
  getUseCaseDiagram: (documentId) => apiClient.get(`/api/diagrams/usecase/${documentId}`),
  getScenarios: (documentId) => apiClient.get(`/api/diagrams/scenarios/${documentId}`),
  getSequenceDiagram: (documentId, scenarioId) => apiClient.get(`/api/diagrams/sequence/${documentId}`, {
    params: { scenario: scenarioId }
  }),
};

// Export apiClient for direct use in components
export { apiClient };

// Processing API (Hybrid Architecture)
export const processingAPI = {
  getStatus: () => apiClient.get('/api/processing/status'),
  getArchitecture: () => apiClient.get('/api/processing/architecture'),
};

// Users API
export const userAPI = {
  getAll: () => apiClient.get('/api/users'),
  getById: (id) => apiClient.get(`/users/${id}`),
  update: (id, data) => apiClient.put(`/users/${id}`, data),
  delete: (id) => apiClient.delete(`/users/${id}`),
};

export default apiClient;
