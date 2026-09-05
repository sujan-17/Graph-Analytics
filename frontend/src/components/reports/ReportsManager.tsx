import React, { useState } from 'react';
import { FileText, Bookmark, Download, Plus, Trash2, CheckCircle, Sparkles } from 'lucide-react';
import { SavedInsight, Report } from '../../types';

interface ReportsManagerProps {
  savedInsights: SavedInsight[];
  reports: Report[];
  onDeleteInsight: (id: string) => Promise<void>;
  onCreateReport: (name: string) => Promise<void>;
}

export const ReportsManager: React.FC<ReportsManagerProps> = ({
  savedInsights,
  reports,
  onDeleteInsight,
  onCreateReport,
}) => {
  const [reportName, setReportName] = useState('Executive Analytics Summary');
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportName.trim() || isGenerating) return;
    setIsGenerating(true);
    try {
      await onCreateReport(reportName);
      alert('PDF Report generated and saved successfully!');
    } catch (err) {
      alert('Failed to generate PDF report.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-6 rounded-2xl glass-panel border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-400" />
            <span>Saved Insights & Executive Report Generator</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Compile bookmarked business insights and quantitative analyses into professional executive PDF reports.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Bookmarked Insights */}
        <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Bookmark className="w-4 h-4 text-indigo-400" />
              <span>Bookmarked Insights ({savedInsights.length})</span>
            </h3>
          </div>

          {savedInsights.length === 0 ? (
            <div className="p-8 text-center border border-dashed border-slate-800 rounded-xl text-xs text-slate-400">
              No insights saved yet. Click "Save Insight" on any conversational response in the AI Analyst tab!
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
              {savedInsights.map((ins) => (
                <div key={ins.id} className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 flex items-start justify-between gap-3 text-xs">
                  <div className="space-y-1">
                    <p className="text-slate-200 font-medium leading-relaxed">{ins.content}</p>
                    <span className="text-[10px] text-slate-500 block">Saved on: {new Date(ins.created_at).toLocaleDateString()}</span>
                  </div>
                  <button
                    onClick={() => onDeleteInsight(ins.id)}
                    className="p-1.5 text-slate-500 hover:text-rose-400 rounded-lg hover:bg-rose-500/10 transition-colors shrink-0"
                    title="Remove Insight"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: PDF Report Generator & Reports List */}
        <div className="space-y-6">
          {/* Create Report Form */}
          <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              <span>Compile Executive PDF Report</span>
            </h3>

            <form onSubmit={handleGenerate} className="space-y-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1 font-medium">Report Title</label>
                <input
                  type="text"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-200 outline-none focus:border-indigo-500 transition-colors"
                  value={reportName}
                  onChange={(e) => setReportName(e.target.value)}
                  placeholder="E.g., Q1 Revenue & Sales Strategy Report"
                />
              </div>

              <button
                type="submit"
                disabled={isGenerating || !reportName.trim()}
                className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 transition-all"
              >
                <FileText className="w-4 h-4" />
                <span>{isGenerating ? 'Generating PDF Engine...' : 'Generate PDF Report'}</span>
              </button>
            </form>
          </div>

          {/* Generated Reports List */}
          <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white">Generated Reports Archive ({reports.length})</h3>

            {reports.length === 0 ? (
              <div className="p-6 text-center border border-dashed border-slate-800 rounded-xl text-xs text-slate-400">
                No PDF reports generated yet.
              </div>
            ) : (
              <div className="space-y-3">
                {reports.map((r) => (
                  <div key={r.id} className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 flex items-center justify-between gap-3 text-xs">
                    <div className="space-y-0.5">
                      <div className="font-bold text-white flex items-center gap-2">
                        <FileText className="w-4 h-4 text-indigo-400" />
                        <span>{r.name}</span>
                      </div>
                      <span className="text-[10px] text-slate-500 block">Created: {new Date(r.created_at).toLocaleString()}</span>
                    </div>

                    <a
                      href={r.download_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 text-xs font-semibold flex items-center gap-1.5 transition-colors border border-indigo-500/30 shrink-0"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download PDF</span>
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
