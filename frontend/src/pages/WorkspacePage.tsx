import React, { useState, useEffect, useMemo } from 'react';
import { User, Workspace, Dataset, DatasetProfile, AnalysisResponse, SavedInsight, Report } from '../types';
import { Navbar } from '../components/layout/Navbar';
import { Sidebar, TabType } from '../components/layout/Sidebar';
import { OverviewDashboard } from '../components/dashboard/OverviewDashboard';
import { DatasetManager } from '../components/datasets/DatasetManager';
import { AIAnalystChat } from '../components/chat/AIAnalystChat';
import { AnalysisHistory } from '../components/history/AnalysisHistory';
import { ReportsManager } from '../components/reports/ReportsManager';
import { workspaceService } from '../services/workspace';
import { analysisService } from '../services/analysis';

interface WorkspacePageProps {
  user: User;
  workspaces: Workspace[];
  currentWorkspace: Workspace;
  onSelectWorkspace: (ws: Workspace) => void;
  onCreateWorkspace: () => void;
  onLogout: () => void;
}

export const WorkspacePage: React.FC<WorkspacePageProps> = ({
  user,
  workspaces,
  currentWorkspace,
  onSelectWorkspace,
  onCreateWorkspace,
  onLogout,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [previewData, setPreviewData] = useState<{ columns: string[]; total_rows: number; preview_rows: any[] } | null>(null);
  const [analyses, setAnalyses] = useState<AnalysisResponse[]>([]);
  const [savedInsights, setSavedInsights] = useState<SavedInsight[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [initialQuestion, setInitialQuestion] = useState<string | undefined>(undefined);
  const [activeConversationId, setActiveConversationId] = useState<string | undefined>(undefined);

  // Load workspace data
  useEffect(() => {
    loadWorkspaceData();
  }, [currentWorkspace.id]);

  const loadWorkspaceData = async () => {
    try {
      const dsList = await workspaceService.listDatasets(currentWorkspace.id);
      setDatasets(dsList);

      if (dsList.length > 0) {
        // Keep active dataset if still present, or prefer combined dataset, or first
        const combinedDs = dsList.find((d) => d.filename.startsWith('Combined_'));
        const activeDs =
          (selectedDataset && dsList.find((d) => d.id === selectedDataset.id)) ||
          combinedDs ||
          dsList[0];
        setSelectedDataset(activeDs);
        await loadDatasetProfileAndPreview(activeDs.id);
      } else {
        setSelectedDataset(null);
        setProfile(null);
        setPreviewData(null);
      }

      const anList = await analysisService.listAnalyses(currentWorkspace.id);
      setAnalyses(anList);
      // Previous conversations reside in Analysis History. Active chat starts fresh unless explicitly opened.

      const insList = await analysisService.listSavedInsights(currentWorkspace.id);
      setSavedInsights(insList);

      const repList = await analysisService.listReports(currentWorkspace.id);
      setReports(repList);
    } catch (err) {
      console.error('Failed to load workspace data:', err);
    }
  };

  const loadDatasetProfileAndPreview = async (datasetId: string) => {
    try {
      const prof = await workspaceService.getDatasetProfile(datasetId);
      setProfile(prof);
      const prev = await workspaceService.getDatasetPreview(datasetId);
      setPreviewData(prev);
    } catch (err) {
      console.error('Failed to load dataset profile:', err);
    }
  };

  const handleUploadCSV = async (file: File) => {
    const newDs = await workspaceService.uploadDataset(currentWorkspace.id, file);
    await loadWorkspaceData();
    setSelectedDataset(newDs);
    await loadDatasetProfileAndPreview(newDs.id);
  };

  const handleSelectDataset = async (ds: Dataset) => {
    setSelectedDataset(ds);
    await loadDatasetProfileAndPreview(ds.id);
  };

  const handleCombineDatasets = async (params?: { dataset_ids?: string[]; combined_name?: string; merge_strategy?: string }) => {
    try {
      const combined = await workspaceService.combineDatasets(currentWorkspace.id, params);
      await loadWorkspaceData();
      setSelectedDataset(combined);
      await loadDatasetProfileAndPreview(combined.id);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to combine datasets.';
      alert(msg);
      throw err;
    }
  };

  const handleDeleteDataset = async (datasetId: string) => {
    try {
      await workspaceService.deleteDataset(datasetId);
      await loadWorkspaceData();
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to delete dataset.';
      alert(msg);
    }
  };

  const handleSendQuestion = async (question: string) => {
    const response = await analysisService.runAnalysis(
      currentWorkspace.id,
      question,
      selectedDataset?.id,
      activeConversationId
    );
    if (response.conversation_id) {
      setActiveConversationId(response.conversation_id);
    }
    setAnalyses((prev) => [...prev, response]);
  };

  const handleNewSession = () => {
    setActiveConversationId(undefined);
  };

  const handleSaveInsight = async (content: string, analysisId?: string) => {
    await analysisService.saveInsight(currentWorkspace.id, content, analysisId);
    const insList = await analysisService.listSavedInsights(currentWorkspace.id);
    setSavedInsights(insList);
    alert('Insight saved to report builder!');
  };

  const handleDeleteInsight = async (id: string) => {
    await analysisService.deleteInsight(id);
    setSavedInsights((prev) => prev.filter((i) => i.id !== id));
  };

  const handleCreateReport = async (name: string) => {
    await analysisService.createReport(currentWorkspace.id, name);
    const repList = await analysisService.listReports(currentWorkspace.id);
    setReports(repList);
  };

  // Filter analyses for the active conversational session in chat
  const currentSessionAnalyses = useMemo(() => {
    if (!activeConversationId) return [];
    return analyses.filter((a) => a.conversation_id === activeConversationId);
  }, [analyses, activeConversationId]);

  // Count distinct past prompt sessions
  const totalPastSessions = useMemo(() => {
    const sessionIds = new Set<string>();
    for (const a of analyses) {
      const key = a.conversation_id || a.id;
      if (key) sessionIds.add(key);
    }
    return sessionIds.size;
  }, [analyses]);

  const handleOpenConversationInChat = (conversationId: string) => {
    setActiveConversationId(conversationId);
    setActiveTab('analyst');
  };

  const handleNavigateToAnalyst = (question?: string) => {
    if (question) {
      setInitialQuestion(question);
      setActiveConversationId(undefined); // Start fresh session for the new prompt
    }
    setActiveTab('analyst');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar
        user={user}
        workspaces={workspaces}
        currentWorkspace={currentWorkspace}
        onSelectWorkspace={onSelectWorkspace}
        onCreateWorkspace={onCreateWorkspace}
        onLogout={onLogout}
      />

      <div className="flex flex-1">
        <Sidebar
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          datasetCount={datasets.length}
        />

        <main className="flex-1 p-6 overflow-y-auto max-w-7xl mx-auto w-full">
          {activeTab === 'overview' && (
            <OverviewDashboard
              workspaceName={currentWorkspace.name}
              profile={profile}
              onNavigateToAnalyst={handleNavigateToAnalyst}
              onNavigateToUpload={() => setActiveTab('datasets')}
              datasets={datasets}
              selectedDataset={selectedDataset}
              onSelectDataset={handleSelectDataset}
            />
          )}

          {activeTab === 'datasets' && (
            <DatasetManager
              datasets={datasets}
              selectedDataset={selectedDataset}
              profile={profile}
              previewData={previewData}
              onSelectDataset={handleSelectDataset}
              onUploadCSV={handleUploadCSV}
              onCombineDatasets={handleCombineDatasets}
              onDeleteDataset={handleDeleteDataset}
              onNavigateToAnalyst={() => setActiveTab('analyst')}
            />
          )}

          {activeTab === 'analyst' && (
            <AIAnalystChat
              analyses={currentSessionAnalyses}
              profile={profile}
              initialQuestion={initialQuestion}
              onSendQuestion={handleSendQuestion}
              onSaveInsight={handleSaveInsight}
              onNewSession={handleNewSession}
              activeConversationId={activeConversationId}
              totalPastSessions={totalPastSessions}
              onNavigateToHistory={() => setActiveTab('history')}
              datasets={datasets}
              selectedDataset={selectedDataset}
              onSelectDataset={handleSelectDataset}
              onCombineDatasets={handleCombineDatasets}
            />
          )}

          {activeTab === 'history' && (
            <AnalysisHistory
              analyses={analyses}
              activeConversationId={activeConversationId}
              onOpenInChat={handleOpenConversationInChat}
            />
          )}

          {activeTab === 'reports' && (
            <ReportsManager
              savedInsights={savedInsights}
              reports={reports}
              onDeleteInsight={handleDeleteInsight}
              onCreateReport={handleCreateReport}
            />
          )}
        </main>
      </div>
    </div>
  );
};
