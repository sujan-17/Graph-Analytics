import React from 'react';
import { Network, LogOut, User as UserIcon, Plus, FolderKanban } from 'lucide-react';
import { User, Workspace } from '../../types';

interface NavbarProps {
  user: User | null;
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  onSelectWorkspace: (ws: Workspace) => void;
  onCreateWorkspace: () => void;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  workspaces,
  currentWorkspace,
  onSelectWorkspace,
  onCreateWorkspace,
  onLogout,
}) => {
  return (
    <header className="h-16 border-b border-slate-200 bg-white/95 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40 shadow-sm">
      {/* Brand Logo & Name */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-500 p-0.5 flex items-center justify-center shadow-md shadow-indigo-500/20">
          <div className="w-full h-full bg-white rounded-[10px] flex items-center justify-center">
            <Network className="w-5 h-5 text-indigo-600" />
          </div>
        </div>
        <div>
          <h1 className="font-extrabold text-base tracking-tight text-slate-900 flex items-center gap-2">
            Graph Analytics <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">LangGraph Multi-Agent</span>
          </h1>
          <p className="text-xs text-slate-500 hidden sm:block">Stateful AI Conversational Analytics Platform</p>
        </div>
      </div>

      {/* Workspace Switcher & User Profile */}
      <div className="flex items-center gap-4">
        {/* Workspace Dropdown */}
        <div className="flex items-center gap-2 bg-slate-50 rounded-lg p-1 border border-slate-200">
          <FolderKanban className="w-4 h-4 text-indigo-600 ml-2" />
          <select
            className="bg-transparent text-sm font-medium text-slate-700 outline-none pr-2 py-1 cursor-pointer"
            value={currentWorkspace?.id || ''}
            onChange={(e) => {
              const selected = workspaces.find((w) => w.id === e.target.value);
              if (selected) onSelectWorkspace(selected);
            }}
          >
            {workspaces.map((w) => (
              <option key={w.id} value={w.id} className="bg-white text-slate-800">
                {w.name}
              </option>
            ))}
          </select>
          <button
            onClick={onCreateWorkspace}
            className="p-1 hover:bg-indigo-50 text-indigo-600 hover:text-indigo-700 rounded transition-colors"
            title="Create New Workspace"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        {/* User Pill & Logout */}
        <div className="flex items-center gap-3 pl-2 border-l border-slate-200">
          <div className="flex items-center gap-2 text-sm text-slate-700">
            <div className="w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center border border-slate-200">
              <UserIcon className="w-4 h-4 text-indigo-600" />
            </div>
            <span className="font-medium hidden md:inline">{user?.name || 'User'}</span>
          </div>
          <button
            onClick={onLogout}
            className="p-2 hover:bg-rose-50 text-slate-400 hover:text-rose-600 rounded-lg transition-colors"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
