import React from 'react';
import Plot from '../common/Plot';
import { TrendingUp, Award, BarChart3, ArrowRight, ShieldCheck, Sparkles, MessageSquare } from 'lucide-react';
import { DatasetProfile } from '../../types';

interface OverviewDashboardProps {
  workspaceName: string;
  profile: DatasetProfile | null;
  onNavigateToAnalyst: (question?: string) => void;
  onNavigateToUpload: () => void;
}

export const OverviewDashboard: React.FC<OverviewDashboardProps> = ({
  workspaceName,
  profile,
  onNavigateToAnalyst,
  onNavigateToUpload,
}) => {
  if (!profile) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border border-dashed border-slate-300 rounded-3xl bg-white my-8 shadow-sm">
        <div className="w-16 h-16 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mb-4 shadow-sm">
          <BarChart3 className="w-8 h-8" />
        </div>
        <h3 className="text-xl font-bold text-slate-900 mb-2">No Active Dataset in Workspace</h3>
        <p className="text-sm text-slate-500 max-w-md mb-6 leading-relaxed">
          Upload a CSV business dataset to automatically trigger dataset profiling, data quality analysis, and initial dashboard generation.
        </p>
        <button
          onClick={onNavigateToUpload}
          className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-xl shadow-md shadow-indigo-600/20 flex items-center gap-2 transition-all"
        >
          <span>Upload Business CSV</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    );
  }

  const kpis = profile.profile.dashboard?.kpis || [];
  const charts = profile.profile.dashboard?.charts || [];
  const suggestions = profile.profile.semantic_summary?.potential_analyses || [];
  const quality = profile.profile.data_quality;

  return (
    <div className="space-y-6">
      {/* Header Overview Banner */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-indigo-600 text-xs font-bold uppercase tracking-wider mb-1">
            <Sparkles className="w-4 h-4" />
            <span>Workspace Analytical Overview</span>
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900">{workspaceName}</h2>
          <p className="text-xs text-slate-500 mt-1">
            Filename: <span className="text-slate-800 font-medium">{profile.profile.basic_info.filename}</span> | {profile.profile.basic_info.row_count.toLocaleString()} rows | {profile.profile.basic_info.column_count} columns
          </p>
        </div>
        <button
          onClick={() => onNavigateToAnalyst()}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-md shadow-indigo-600/20 flex items-center gap-2 transition-all shrink-0"
        >
          <MessageSquare className="w-4 h-4" />
          <span>Ask Conversational Question</span>
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, idx) => (
          <div key={idx} className="p-5 rounded-2xl bg-white border border-slate-200 space-y-2 hover:border-indigo-400 transition-colors shadow-sm">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-medium uppercase tracking-wider">{kpi.title}</span>
              <TrendingUp className="w-4 h-4 text-indigo-600" />
            </div>
            <div className="text-2xl font-extrabold text-slate-900 tracking-tight">{kpi.value}</div>
            <p className="text-[11px] text-slate-400">{kpi.subtext}</p>
          </div>
        ))}

        {/* Dataset Quality Score Card */}
        <div className="p-5 rounded-2xl bg-white border border-slate-200 space-y-2 shadow-sm">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-medium uppercase tracking-wider">Dataset Quality</span>
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-emerald-600">{quality.quality_score}%</span>
            <span className="text-xs text-slate-400">Health Score</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-emerald-500 h-full rounded-full"
              style={{ width: `${quality.quality_score}%` }}
            />
          </div>
        </div>
      </div>

      {/* Initial Plotly Charts Grid */}
      {charts.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {charts.map((c) => (
            <div key={c.id} className="p-5 rounded-2xl bg-white border border-slate-200 space-y-3 shadow-sm">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-indigo-600" />
                <span>{c.title}</span>
              </h4>
              <div className="w-full h-72 rounded-xl overflow-hidden bg-slate-50/60 border border-slate-100 p-2">
                <Plot
                  data={c.spec.data}
                  layout={{
                    ...c.spec.layout,
                    autosize: true,
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: { color: '#334155', family: 'Inter' }
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '100%' }}
                  config={{ responsive: true, displayModeBar: false }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Proactive Suggested Analyses */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-3 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <Award className="w-4 h-4 text-indigo-600" />
          <span>Proactive Suggested Analysis Questions</span>
        </h3>
        <p className="text-xs text-slate-500">
          The AI dataset profiling engine detected key business entities and dimensions. Click any question below to launch analysis:
        </p>
        <div className="flex flex-wrap gap-2.5 pt-1">
          {suggestions.map((q, idx) => (
            <button
              key={idx}
              onClick={() => onNavigateToAnalyst(q)}
              className="px-3.5 py-2 rounded-xl bg-slate-50 hover:bg-indigo-50 text-slate-700 hover:text-indigo-700 border border-slate-200 text-xs font-medium flex items-center gap-2 transition-all group"
            >
              <span>{q}</span>
              <ArrowRight className="w-3.5 h-3.5 opacity-60 group-hover:translate-x-0.5 transition-transform text-indigo-600" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
