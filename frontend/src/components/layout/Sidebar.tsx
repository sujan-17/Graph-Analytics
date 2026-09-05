import React from 'react';
import { LayoutDashboard, Database, Bot, History, FileText } from 'lucide-react';

export type TabType = 'overview' | 'datasets' | 'analyst' | 'history' | 'reports';

interface SidebarProps {
  activeTab: TabType;
  onSelectTab: (tab: TabType) => void;
  datasetCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab, datasetCount }) => {
  const menuItems = [
    { id: 'overview' as TabType, label: 'Overview', icon: LayoutDashboard, badge: null },
    { id: 'datasets' as TabType, label: 'Datasets & Quality', icon: Database, badge: datasetCount ? `${datasetCount}` : null },
    { id: 'analyst' as TabType, label: 'AI Analyst Chat', icon: Bot, badge: 'LangGraph' },
    { id: 'history' as TabType, label: 'Analysis History', icon: History, badge: null },
    { id: 'reports' as TabType, label: 'Reports & Insights', icon: FileText, badge: null },
  ];

  return (
    <aside className="w-64 border-r border-slate-800/80 bg-slate-950/60 flex flex-col p-4 space-y-6 shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="space-y-1">
        <p className="px-3 text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">
          Workspace Navigation
        </p>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/25 border border-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/80'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span
                  className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                    isActive
                      ? 'bg-indigo-800 text-indigo-100'
                      : item.badge === 'LangGraph'
                      ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Info Card */}
      <div className="mt-auto p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-2">
        <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400">
          <Bot className="w-4 h-4" />
          <span>Multi-Agent Engine</span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Powered by LangChain & LangGraph with AST-isolated execution worker and safe state machine.
        </p>
      </div>
    </aside>
  );
};
