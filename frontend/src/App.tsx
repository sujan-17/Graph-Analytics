import React, { useState, useEffect } from 'react';
import { User, Workspace } from './types';
import { authService } from './services/auth';
import { workspaceService } from './services/workspace';
import { AuthPage } from './pages/AuthPage';
import { DashboardPage } from './pages/DashboardPage';
import { WorkspacePage } from './pages/WorkspacePage';

export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      authService
        .getMe()
        .then((u) => {
          setUser(u);
          loadWorkspaces();
        })
        .catch(() => {
          handleLogout();
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const loadWorkspaces = async () => {
    try {
      const wsList = await workspaceService.listWorkspaces();
      setWorkspaces(wsList);
    } catch (err) {
      console.error('Failed to load workspaces:', err);
    }
  };

  const handleLoginSuccess = (u: User, tok: string) => {
    localStorage.setItem('token', tok);
    setToken(tok);
    setUser(u);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setCurrentWorkspace(null);
  };

  const handleCreateWorkspace = async (name: string, description?: string) => {
    const newWs = await workspaceService.createWorkspace(name, description);
    await loadWorkspaces();
    setCurrentWorkspace(newWs);
  };

  const handleDeleteWorkspace = async (id: string) => {
    await workspaceService.deleteWorkspace(id);
    if (currentWorkspace?.id === id) {
      setCurrentWorkspace(null);
    }
    await loadWorkspaces();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-indigo-400">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
          <span className="font-semibold text-sm">Loading Graph Analytics...</span>
        </div>
      </div>
    );
  }

  if (!user || !token) {
    return <AuthPage onLoginSuccess={handleLoginSuccess} />;
  }

  if (!currentWorkspace) {
    return (
      <DashboardPage
        user={user}
        workspaces={workspaces}
        onSelectWorkspace={setCurrentWorkspace}
        onCreateWorkspace={handleCreateWorkspace}
        onDeleteWorkspace={handleDeleteWorkspace}
      />
    );
  }

  return (
    <WorkspacePage
      user={user}
      workspaces={workspaces}
      currentWorkspace={currentWorkspace}
      onSelectWorkspace={setCurrentWorkspace}
      onCreateWorkspace={() => setCurrentWorkspace(null)}
      onLogout={handleLogout}
    />
  );
}

export default App;
