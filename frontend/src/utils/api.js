import axios from 'axios';

// Use absolute URL to bypass proxy issues, or relative if REACT_APP_API_URL is not set
// The proxy in package.json should handle this, but if it doesn't work, use absolute URL
// Note: Port 5000 is often used by macOS AirPlay, so we use 5001
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
});

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

// Handle 401 errors (unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname;
      // Only redirect to login if we're not already on a public page
      // Don't redirect from public pages like /, /login, /register, /verify-email
      const publicPaths = ['/', '/login', '/register', '/verify-email'];
      const isPublicPath = publicPaths.includes(currentPath);
      
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      // Only redirect if we're on a protected route
      if (!isPublicPath) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
export { API_BASE_URL };

