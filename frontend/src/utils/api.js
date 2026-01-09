import axios from 'axios';

// Use absolute URL to bypass proxy issues, or relative if REACT_APP_API_URL is not set
// The proxy in package.json should handle this, but if it doesn't work, use absolute URL
// Note: Port 5000 is often used by macOS AirPlay, so we use 5001
let API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

// Ensure API_BASE_URL ends with /api (backend routes are under /api)
if (API_BASE_URL && !API_BASE_URL.endsWith('/api')) {
  // If it doesn't end with /api, append it
  API_BASE_URL = API_BASE_URL.endsWith('/') ? `${API_BASE_URL}api` : `${API_BASE_URL}/api`;
}

// Log API URL in production for debugging (remove in production after fixing)
if (process.env.NODE_ENV === 'production') {
  console.log('API_BASE_URL:', API_BASE_URL);
  console.log('REACT_APP_API_URL env var:', process.env.REACT_APP_API_URL);
}

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout (increased for cold starts on Render free tier)
});

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // Start with 1 second

// Helper function to delay execution
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Helper function to check if error is retryable
const isRetryableError = (error) => {
  // Retry on network errors or 5xx server errors
  if (!error.response) {
    return true; // Network error (timeout, connection error, etc.)
  }
  const status = error.response.status;
  return status >= 500 || status === 429; // Server errors or rate limit
};

// Add token to requests
api.interceptors.request.use(
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

// Handle responses with retry logic
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config || {};
    
    // Handle 401 errors (unauthorized) - don't retry these
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname;
      // Only redirect to login if we're not already on a public page
      // Don't redirect from public pages like /, /login, /register, /verify-email
      const publicPaths = ['/', '/login', '/register', '/verify-email'];
      const isPublicPath = publicPaths.includes(currentPath);
      
      // Special handling for /auth/me endpoint - this is used for token validation
      // If it fails, it might be a temporary server issue (e.g., Render spin-down)
      // Don't immediately remove token - let AuthContext handle it
      const isAuthMeEndpoint = config.url && config.url.includes('/auth/me');
      
      if (!isAuthMeEndpoint) {
        // For other endpoints, remove token on 401 (likely expired or invalid)
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        // Only redirect if we're on a protected route
        if (!isPublicPath) {
          window.location.href = '/login';
        }
      }
      // For /auth/me, let the error propagate to AuthContext which will handle it gracefully
      
      return Promise.reject(error);
    }
    
    // Retry logic for retryable errors
    if (!config.__retryCount) {
      config.__retryCount = 0;
    }
    
    if (config.__retryCount < MAX_RETRIES && isRetryableError(error)) {
      config.__retryCount += 1;
      // Exponential backoff: wait 1s, 2s, 4s
      const delayMs = RETRY_DELAY * Math.pow(2, config.__retryCount - 1);
      await delay(delayMs);
      return api(config);
    }
    
    return Promise.reject(error);
  }
);

export default api;
export { API_BASE_URL };

