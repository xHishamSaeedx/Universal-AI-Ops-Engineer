import axios from "axios";

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.DEV ? "/api" : "http://localhost:8000/api",
  timeout: 10000,
});

// Create separate instance for root endpoints
const rootApi = axios.create({
  baseURL: import.meta.env.DEV ? "" : "http://localhost:8000",
  timeout: 10000,
});

// Request interceptors for both APIs
const setupInterceptors = (apiInstance) => {
  apiInstance.interceptors.request.use(
    (config) => {
      // Add any auth headers here if needed
      // const token = localStorage.getItem('token');
      // if (token) {
      //   config.headers.Authorization = `Bearer ${token}`;
      // }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor for error handling
  apiInstance.interceptors.response.use(
    (response) => {
      return response;
    },
    (error) => {
      console.error("API Error:", error);
      return Promise.reject(error);
    }
  );
};

// Setup interceptors for both API instances
setupInterceptors(api);
setupInterceptors(rootApi);

// Legacy interceptors (keeping for backward compatibility)
api.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error("API Error:", error);
    return Promise.reject(error);
  }
);

// API endpoints
export const healthAPI = {
  // Get detailed health status
  getHealth: () => api.get("/v1/health"),

  // Simple health check (root endpoint)
  getHealthz: () => rootApi.get("/healthz"),
};

export default api;
