import API from './api';
import { User } from '../types';

export const authService = {
  async register(name: string, email: string, password: string): Promise<{ access_token: string; user: User }> {
    const res = await API.post('/auth/register', { name, email, password });
    return res.data;
  },

  async login(email: string, password: string): Promise<{ access_token: string; user: User }> {
    const res = await API.post('/auth/login', { email, password });
    return res.data;
  },

  async getMe(): Promise<User> {
    const res = await API.get('/auth/me');
    return res.data;
  }
};
