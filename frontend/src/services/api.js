import axios from 'axios';

// Backend API URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log('[API] Response:', response.data);
    return response;
  },
  (error) => {
    console.error('[API] Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ========== SCAN API ==========
export const scanAPI = {
  createScan: async (targetUrl) => {
    const response = await api.post('/scans', { target_url: targetUrl });
    return response.data;
  },

  listScans: async (skip = 0, limit = 100) => {
    const response = await api.get('/scans', { params: { skip, limit } });
    return response.data;
  },

  getScan: async (scanId) => {
    const response = await api.get(`/scans/${scanId}`);
    return response.data;
  },

  getScanSummary: async (scanId) => {
    const response = await api.get(`/scans/${scanId}/summary`);
    return response.data;
  },

  deleteScan: async (scanId) => {
    await api.delete(`/scans/${scanId}`);
  },

  downloadReport: async (scanId) => {
    const response = await api.get(`/reports/${scanId}`, {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `scan_${scanId}_report.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  resetAllData: async () => {
    const response = await api.delete('/reset');
    return response.data;
  },
};

// ========== VULNERABILITY API ==========
export const vulnerabilityAPI = {
  listVulnerabilities: async (scanId, severity = null) => {
    const response = await api.get(`/scans/${scanId}/vulnerabilities`, {
      params: severity ? { severity } : {},
    });
    return response.data;
  },

  getVulnerability: async (vulnerabilityId) => {
    const response = await api.get(`/vulnerabilities/${vulnerabilityId}`);
    return response.data;
  },

  // NEW: Get SHAP explanation for a vulnerability
  explainVulnerability: async (vulnerabilityId) => {
    const response = await api.get(`/explain/${vulnerabilityId}`);
    return response.data;
  },
};

// ========== HEALTH API ==========
export const healthAPI = {
  checkHealth: async () => {
    const rootURL = API_BASE_URL.replace(/\/api\/?$/, '') || 'http://localhost:8000';
    const response = await api.get('/health', { baseURL: rootURL });
    return response.data;
  },
};

export default api;