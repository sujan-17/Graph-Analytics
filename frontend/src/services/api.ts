import axios from 'axios';

const API = axios.create({
  baseURL: '/api',
});

// Clear any legacy client-side runtime API key from browser storage
try {
  localStorage.removeItem('gemini_api_key');
} catch {
  // ignore storage errors
}

API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default API;
