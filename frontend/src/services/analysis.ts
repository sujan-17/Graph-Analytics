import API from './api';
import { AnalysisResponse, SavedInsight, Report } from '../types';

export const analysisService = {
  async runAnalysis(workspaceId: string, question: string, datasetId?: string, conversationId?: string): Promise<AnalysisResponse> {
    const res = await API.post(`/workspaces/${workspaceId}/analysis`, {
      question,
      dataset_id: datasetId,
      conversation_id: conversationId
    });
    return res.data;
  },

  async listAnalyses(workspaceId: string): Promise<AnalysisResponse[]> {
    const res = await API.get(`/workspaces/${workspaceId}/analysis`);
    return res.data;
  },

  async getAnalysis(analysisId: string): Promise<AnalysisResponse> {
    const res = await API.get(`/analysis/${analysisId}`);
    return res.data;
  },

  async saveInsight(workspaceId: string, content: string, analysisId?: string): Promise<SavedInsight> {
    const res = await API.post(`/insights?workspace_id=${workspaceId}`, {
      analysis_id: analysisId,
      content
    });
    return res.data;
  },

  async listSavedInsights(workspaceId: string): Promise<SavedInsight[]> {
    const res = await API.get(`/workspaces/${workspaceId}/insights`);
    return res.data;
  },

  async deleteInsight(id: string): Promise<void> {
    await API.delete(`/insights/${id}`);
  },

  async createReport(workspaceId: string, name: string, datasetId?: string): Promise<Report> {
    const res = await API.post(`/workspaces/${workspaceId}/reports`, {
      name,
      dataset_id: datasetId
    });
    return res.data;
  },

  async listReports(workspaceId: string): Promise<Report[]> {
    const res = await API.get(`/workspaces/${workspaceId}/reports`);
    return res.data;
  },

  async getReport(reportId: string): Promise<Report> {
    const res = await API.get(`/reports/${reportId}`);
    return res.data;
  },

  async deleteReport(reportId: string): Promise<void> {
    await API.delete(`/reports/${reportId}`);
  }
};
