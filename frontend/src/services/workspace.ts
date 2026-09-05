import API from './api';
import { Workspace, Dataset, DatasetProfile } from '../types';

export const workspaceService = {
  async listWorkspaces(): Promise<Workspace[]> {
    const res = await API.get('/workspaces');
    return res.data;
  },

  async createWorkspace(name: string, description?: string): Promise<Workspace> {
    const res = await API.post('/workspaces', { name, description });
    return res.data;
  },

  async getWorkspace(id: string): Promise<Workspace> {
    const res = await API.get(`/workspaces/${id}`);
    return res.data;
  },

  async deleteWorkspace(id: string): Promise<void> {
    await API.delete(`/workspaces/${id}`);
  },

  async uploadDataset(workspaceId: string, file: File): Promise<Dataset> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await API.post(`/workspaces/${workspaceId}/datasets`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  },

  async listDatasets(workspaceId: string): Promise<Dataset[]> {
    const res = await API.get(`/workspaces/${workspaceId}/datasets`);
    return res.data;
  },

  async getDatasetProfile(datasetId: string): Promise<DatasetProfile> {
    const res = await API.get(`/datasets/${datasetId}/profile`);
    return res.data;
  },

  async getDatasetPreview(datasetId: string, limit: number = 50): Promise<{ columns: string[]; total_rows: number; preview_rows: any[] }> {
    const res = await API.get(`/datasets/${datasetId}/preview?limit=${limit}`);
    return res.data;
  },

  async deleteDataset(datasetId: string): Promise<void> {
    await API.delete(`/datasets/${datasetId}`);
  }
};
