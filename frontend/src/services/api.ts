import axios from 'axios';

const API = axios.create({
  baseURL: '/api',
});

API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const geminiKey = localStorage.getItem('gemini_api_key');
  if (geminiKey) {
    config.headers['X-Gemini-API-Key'] = geminiKey;
  }
  return config;
});

export default API;
