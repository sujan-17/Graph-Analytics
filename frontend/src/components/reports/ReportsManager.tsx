import React, { useState, useEffect } from 'react';
import {
  FileText,
  Sparkles,
  Download,
  Trash2,
  Database,
  BarChart3,
  TrendingUp,
  PieChart,
  Layers,
  ShieldCheck,
  AlertTriangle,
  Lightbulb,
  Cpu,
  Eye,
  CheckCircle2,
  Table,
  Clock,
  ArrowRight
} from 'lucide-react';
import { SavedInsight, Report, Dataset } from '../../types';

interface ReportsManagerProps {
  savedInsights?: SavedInsight[];
  reports: Report[];
  datasets?: Dataset[];
  selectedDataset?: Dataset | null;
  onDeleteInsight?: (id: string) => Promise<void>;
  onCreateReport: (name: string, datasetId?: string) => Promise<Report | void>;
  onDeleteReport?: (id: string) => Promise<void>;
}

export const ReportsManager: React.FC<ReportsManagerProps> = ({
  savedInsights = [],
  reports = [],
  datasets = [],
  selectedDataset,
  onDeleteInsight,
  onCreateReport,
  onDeleteReport,
}) => {
  // Determine initially selected dataset
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(
    selectedDataset?.id || (datasets.length > 0 ? datasets[0].id : '')
  );

  const activeDataset = datasets.find((d) => d.id === selectedDatasetId) || selectedDataset || datasets[0];

  const [reportName, setReportName] = useState<string>(
    activeDataset ? `Executive Data Analysis: ${activeDataset.filename}` : 'Executive Dataset Intelligence Report'
  );

  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generationStage, setGenerationStage] = useState<string>('');
  const [activeReport, setActiveReport] = useState<Report | null>(null);
  const [activeSection, setActiveSection] = useState<'all' | 'summary' | 'data_analysed' | 'depiction' | 'recommendations'>('all');

  // Sync active report if none selected
  useEffect(() => {
    if (!activeReport && reports.length > 0) {
      setActiveReport(reports[0]);
    }
  }, [reports, activeReport]);

  // Sync report title when dataset changes
  const handleDatasetChange = (dsId: string) => {
    setSelectedDatasetId(dsId);
    const chosen = datasets.find((d) => d.id === dsId);
    if (chosen) {
      setReportName(`Executive Data Analysis: ${chosen.filename}`);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportName.trim() || isGenerating) return;

    setIsGenerating(true);
    setGenerationStage('Profiling dataset distributions and dimensions...');

    const timer1 = setTimeout(() => {
      setGenerationStage('Evaluating operational patterns and segment behaviors...');
    }, 1800);

    const timer2 = setTimeout(() => {
      setGenerationStage('Synthesizing prescriptive recommendations and compiling PDF...');
    }, 3800);

    try {
      const generated = await onCreateReport(reportName.trim(), selectedDatasetId || undefined);
      clearTimeout(timer1);
      clearTimeout(timer2);
      if (generated && 'id' in generated) {
        setActiveReport(generated as Report);
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to generate report.';
      alert(msg);
    } finally {
      clearTimeout(timer1);
      clearTimeout(timer2);
      setIsGenerating(false);
      setGenerationStage('');
    }
  };

  const getDownloadUrl = (r: Report) => {
    const token = localStorage.getItem('token');
    return `${r.download_url}${token ? `?token=${token}` : ''}`;
  };

  const reportData = activeReport?.report_data;

  return (
    <div className="space-y-6 pb-12">
      {/* 1. White Theme Header Banner */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-100">
              <FileText className="w-5 h-5" />
            </span>
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
              Executive Dataset Report Generator
            </h2>
          </div>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
            Generate thorough, executive-grade data analyst reports for any dataset in this workspace — summarizing data scope,
            current operational depictions, and prescriptive next steps without user query history.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 text-xs font-semibold">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>100% Query-Free</span>
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-50 border border-indigo-200/70 text-indigo-700 text-xs font-semibold">
            <BarChart3 className="w-4 h-4 text-indigo-600" />
            <span>Autonomous Profiling</span>
          </span>
        </div>
      </div>

      {/* 2. Configure & Run Dataset Analysis (White Theme Card) */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-600" />
              <span>Configure & Run Dataset Analysis</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Select any dataset in your workspace to generate an authoritative executive dossier.
            </p>
          </div>

          {activeDataset && (
            <div className="flex items-center gap-2 text-xs">
              <span className="bg-slate-100 text-slate-700 px-2.5 py-1 rounded-lg font-semibold border border-slate-200">
                {activeDataset.row_count.toLocaleString()} Records
              </span>
              <span className="bg-slate-100 text-slate-700 px-2.5 py-1 rounded-lg font-semibold border border-slate-200">
                {activeDataset.column_count} Columns
              </span>
            </div>
          )}
        </div>

        {datasets.length === 0 ? (
          <div className="p-8 text-center bg-slate-50 border border-dashed border-slate-300 rounded-xl space-y-2">
            <Database className="w-8 h-8 text-slate-400 mx-auto" />
            <h4 className="text-sm font-semibold text-slate-700">No Datasets Found in Workspace</h4>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              Please upload a dataset in the <b>Datasets & Quality</b> tab first to generate comprehensive data analyst reports.
            </p>
          </div>
        ) : (
          <form onSubmit={handleGenerate} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Dataset Picker */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Target Dataset
                </label>
                <select
                  value={selectedDatasetId}
                  onChange={(e) => handleDatasetChange(e.target.value)}
                  className="w-full bg-slate-50 hover:bg-white border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 font-medium outline-none focus:bg-white focus:border-indigo-600 transition-colors"
                >
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.filename} ({d.row_count.toLocaleString()} rows, {d.column_count} cols)
                    </option>
                  ))}
                </select>
              </div>

              {/* Report Title */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Report Title
                </label>
                <input
                  type="text"
                  value={reportName}
                  onChange={(e) => setReportName(e.target.value)}
                  placeholder="E.g., Comprehensive Sales & Revenue Report"
                  className="w-full bg-slate-50 hover:bg-white border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 font-medium outline-none focus:bg-white focus:border-indigo-600 transition-colors"
                />
              </div>
            </div>

            {/* Submit Button & Progress Indicator */}
            <div className="flex flex-col sm:flex-row items-center gap-4 pt-1">
              <button
                type="submit"
                disabled={isGenerating || !reportName.trim()}
                className="w-full sm:w-auto px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-sm shadow-indigo-600/20 flex items-center justify-center gap-2 transition-all cursor-pointer"
              >
                <Sparkles className="w-4 h-4" />
                <span>{isGenerating ? 'Analyzing Dataset...' : 'Generate Data Analyst Report'}</span>
              </button>

              {isGenerating && (
                <div className="flex items-center gap-2 text-xs text-indigo-700 bg-indigo-50 px-3.5 py-2 rounded-xl border border-indigo-200 animate-pulse">
                  <div className="w-2 h-2 rounded-full bg-indigo-600 animate-ping" />
                  <span className="font-medium">{generationStage}</span>
                </div>
              )}
            </div>
          </form>
        )}
      </div>

      {/* 3. Active Report Viewer (White Theme) */}
      {activeReport ? (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden space-y-6">
          {/* Report Top Action Bar */}
          <div className="p-6 bg-slate-50/60 border-b border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full bg-indigo-100 text-indigo-800 text-[11px] font-bold">
                  Data Analyst Dossier
                </span>
                <span className="text-xs text-slate-500">
                  Dataset: <b className="text-slate-800">{reportData?.dataset_name || activeReport.name}</b>
                </span>
                <span className="text-xs text-slate-400">•</span>
                <span className="text-xs text-slate-500">
                  Generated: {reportData?.generated_at || new Date(activeReport.created_at).toLocaleDateString()}
                </span>
              </div>
              <h2 className="text-xl font-black text-slate-900 tracking-tight">
                {activeReport.name}
              </h2>
            </div>

            <a
              href={getDownloadUrl(activeReport)}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-all shrink-0 cursor-pointer"
            >
              <Download className="w-4 h-4" />
              <span>Download Executive PDF</span>
            </a>
          </div>

          {/* Section Navigation Tabs */}
          <div className="px-6 border-b border-slate-200 flex items-center gap-2 overflow-x-auto pb-3">
            <button
              onClick={() => setActiveSection('all')}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
                activeSection === 'all'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              All Sections
            </button>
            <button
              onClick={() => setActiveSection('summary')}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
                activeSection === 'summary'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              1. Executive Summary
            </button>
            <button
              onClick={() => setActiveSection('data_analysed')}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
                activeSection === 'data_analysed'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              2. What Data Is Analysed
            </button>
            <button
              onClick={() => setActiveSection('depiction')}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
                activeSection === 'depiction'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              3. What Dataset Depicts
            </button>
            <button
              onClick={() => setActiveSection('recommendations')}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
                activeSection === 'recommendations'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              4. What Can Be Done
            </button>
          </div>

          {/* Report Detailed Content */}
          <div className="p-6 md:p-8 space-y-8">
            {reportData ? (
              <>
                {/* SECTION 1: Executive Summary */}
                {(activeSection === 'all' || activeSection === 'summary') && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
                      <span className="w-5 h-5 rounded-md bg-indigo-50 text-indigo-700 flex items-center justify-center text-xs font-black border border-indigo-100">
                        1
                      </span>
                      <h4 className="text-sm font-extrabold text-slate-900">
                        Executive Dataset Summary & Purpose
                      </h4>
                    </div>

                    <div className="p-5 bg-slate-50/70 rounded-xl border border-slate-200 text-slate-800 text-xs md:text-sm leading-relaxed space-y-2.5 font-normal">
                      {reportData.executive_summary.split('\n\n').map((paragraph, idx) => (
                        <p key={idx}>{paragraph}</p>
                      ))}
                    </div>
                  </div>
                )}

                {/* SECTION 2: What Data Was Analysed */}
                {(activeSection === 'all' || activeSection === 'data_analysed') && (
                  <div className="space-y-5">
                    <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
                      <span className="w-5 h-5 rounded-md bg-indigo-50 text-indigo-700 flex items-center justify-center text-xs font-black border border-indigo-100">
                        2
                      </span>
                      <h4 className="text-sm font-extrabold text-slate-900">
                        Summary of What Data Is Analysed
                      </h4>
                    </div>

                    {/* Scope Scorecard */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div className="p-3.5 rounded-xl bg-slate-50/70 border border-slate-200">
                        <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                          Total Records
                        </span>
                        <span className="text-lg font-black text-slate-900 mt-0.5 block">
                          {reportData.summary_metrics.row_count.toLocaleString()}
                        </span>
                      </div>
                      <div className="p-3.5 rounded-xl bg-slate-50/70 border border-slate-200">
                        <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                          Features / Columns
                        </span>
                        <span className="text-lg font-black text-slate-900 mt-0.5 block">
                          {reportData.summary_metrics.column_count}
                        </span>
                      </div>
                      <div className="p-3.5 rounded-xl bg-slate-50/70 border border-slate-200">
                        <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                          Data Health Score
                        </span>
                        <span className="text-lg font-black text-emerald-600 mt-0.5 block">
                          {reportData.summary_metrics.quality_score}%
                        </span>
                      </div>
                      <div className="p-3.5 rounded-xl bg-slate-50/70 border border-slate-200">
                        <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                          Missing Cell Density
                        </span>
                        <span className="text-lg font-black text-slate-900 mt-0.5 block">
                          {reportData.summary_metrics.missing_percentage}%
                        </span>
                      </div>
                    </div>

                    {reportData.what_data_is_analysed.overview && (
                      <p className="text-xs text-slate-700 leading-relaxed">
                        {reportData.what_data_is_analysed.overview}
                      </p>
                    )}

                    {/* Numerical Measures Table */}
                    {reportData.what_data_is_analysed.numeric_metrics &&
                      reportData.what_data_is_analysed.numeric_metrics.length > 0 && (
                        <div className="space-y-2">
                          <h5 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                            <Table className="w-3.5 h-3.5 text-indigo-600" />
                            <span>Primary Quantitative Measures</span>
                          </h5>
                          <div className="overflow-x-auto rounded-xl border border-slate-200">
                            <table className="w-full text-left text-xs">
                              <thead className="bg-slate-100 text-slate-800 font-bold border-b border-slate-200">
                                <tr>
                                  <th className="py-2.5 px-3">Measure Name</th>
                                  <th className="py-2.5 px-3 text-right">Total Volume</th>
                                  <th className="py-2.5 px-3 text-right">Average / Mean</th>
                                  <th className="py-2.5 px-3 text-right">Min</th>
                                  <th className="py-2.5 px-3 text-right">Max</th>
                                  <th className="py-2.5 px-3 text-right">Std Dev</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-100 text-slate-700 bg-white">
                                {reportData.what_data_is_analysed.numeric_metrics.map((m, idx) => (
                                  <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                                    <td className="py-2.5 px-3 font-semibold text-slate-900">{m.name}</td>
                                    <td className="py-2.5 px-3 text-right font-mono">
                                      {m.total !== undefined ? m.total.toLocaleString() : 'N/A'}
                                    </td>
                                    <td className="py-2.5 px-3 text-right font-mono">
                                      {m.mean !== undefined ? m.mean.toLocaleString() : 'N/A'}
                                    </td>
                                    <td className="py-2.5 px-3 text-right font-mono">
                                      {m.min !== undefined ? m.min.toLocaleString() : 'N/A'}
                                    </td>
                                    <td className="py-2.5 px-3 text-right font-mono">
                                      {m.max !== undefined ? m.max.toLocaleString() : 'N/A'}
                                    </td>
                                    <td className="py-2.5 px-3 text-right font-mono text-slate-500">
                                      {m.std !== undefined ? m.std.toLocaleString() : '0.0'}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}

                    {/* Categorical Dimensions Breakdown */}
                    {reportData.what_data_is_analysed.categorical_dimensions &&
                      reportData.what_data_is_analysed.categorical_dimensions.length > 0 && (
                        <div className="space-y-2">
                          <h5 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                            <Layers className="w-3.5 h-3.5 text-indigo-600" />
                            <span>Categorical Dimensions & Dominant Segments</span>
                          </h5>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {reportData.what_data_is_analysed.categorical_dimensions.map((dim, idx) => (
                              <div key={idx} className="p-3.5 rounded-xl bg-slate-50/70 border border-slate-200 space-y-2">
                                <div className="flex items-center justify-between text-xs">
                                  <span className="font-bold text-slate-900">{dim.name}</span>
                                  <span className="text-slate-500 text-[11px]">
                                    {dim.unique_count} distinct groupings
                                  </span>
                                </div>
                                <div className="flex flex-wrap gap-1.5">
                                  {Object.entries(dim.top_percentages || {}).map(([cat, pct]) => (
                                    <span
                                      key={cat}
                                      className="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-[11px] text-slate-700 font-medium"
                                    >
                                      {cat}: <b className="text-indigo-600">{pct}%</b>
                                    </span>
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                    {/* Quality Assessment Text */}
                    {reportData.what_data_is_analysed.quality_audit && (
                      <div className="p-3.5 rounded-xl bg-emerald-50/70 border border-emerald-200 text-xs text-emerald-950 flex items-start gap-2.5">
                        <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <div>
                          <span className="font-bold block mb-0.5">Data Hygiene & Integrity Audit</span>
                          <span className="text-slate-700 leading-relaxed">
                            {reportData.what_data_is_analysed.quality_audit}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* SECTION 3: What the Dataset Depicts Generally */}
                {(activeSection === 'all' || activeSection === 'depiction') && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
                      <span className="w-5 h-5 rounded-md bg-indigo-50 text-indigo-700 flex items-center justify-center text-xs font-black border border-indigo-100">
                        3
                      </span>
                      <h4 className="text-sm font-extrabold text-slate-900">
                        What Is Currently This Dataset Depicting Generally
                      </h4>
                    </div>

                    {reportData.what_dataset_depicts.general_depiction && (
                      <div className="p-4 rounded-xl bg-slate-50/70 border border-slate-200 text-xs md:text-sm text-slate-800 leading-relaxed font-normal">
                        {reportData.what_dataset_depicts.general_depiction}
                      </div>
                    )}

                    {/* Key Patterns & Findings */}
                    {reportData.what_dataset_depicts.key_patterns &&
                      reportData.what_dataset_depicts.key_patterns.length > 0 && (
                        <div className="space-y-2">
                          <h5 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                            <TrendingUp className="w-3.5 h-3.5 text-indigo-600" />
                            <span>Key Operational & Distributional Patterns</span>
                          </h5>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            {reportData.what_dataset_depicts.key_patterns.map((pat, idx) => (
                              <div
                                key={idx}
                                className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-sm hover:border-slate-300 transition-colors space-y-1.5"
                              >
                                <span className="inline-block px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 text-[10px] font-bold border border-indigo-100">
                                  Pattern #{idx + 1}
                                </span>
                                <h6 className="text-xs font-bold text-slate-900">{pat.title}</h6>
                                <p className="text-xs text-slate-600 leading-relaxed">{pat.description}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                    {/* Comparative Findings */}
                    {reportData.what_dataset_depicts.comparative_findings && (
                      <div className="p-3.5 rounded-xl bg-slate-50/70 border border-slate-200 text-xs space-y-1">
                        <span className="font-bold text-slate-900 block flex items-center gap-1.5">
                          <PieChart className="w-3.5 h-3.5 text-indigo-600" />
                          Comparative Segmentation Findings
                        </span>
                        <p className="text-slate-700 leading-relaxed">
                          {reportData.what_dataset_depicts.comparative_findings}
                        </p>
                      </div>
                    )}

                    {/* Anomalies & Risks */}
                    {reportData.what_dataset_depicts.anomalies_and_risks && (
                      <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200 text-xs text-amber-950 flex items-start gap-2.5">
                        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                        <div>
                          <span className="font-bold block mb-0.5">Identified Vulnerabilities & Anomaly Notes</span>
                          <span className="text-slate-700 leading-relaxed">
                            {reportData.what_dataset_depicts.anomalies_and_risks}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* SECTION 4: What Can Be Done */}
                {(activeSection === 'all' || activeSection === 'recommendations') && (
                  <div className="space-y-5">
                    <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
                      <span className="w-5 h-5 rounded-md bg-indigo-50 text-indigo-700 flex items-center justify-center text-xs font-black border border-indigo-100">
                        4
                      </span>
                      <h4 className="text-sm font-extrabold text-slate-900">
                        What Can Be Done (Strategic & Analytical Action Plan)
                      </h4>
                    </div>

                    {/* Strategic Interventions */}
                    {reportData.what_can_be_done.strategic_actions &&
                      reportData.what_can_be_done.strategic_actions.length > 0 && (
                        <div className="space-y-2">
                          <h5 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                            <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
                            <span>A. Immediate Strategic Interventions</span>
                          </h5>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            {reportData.what_can_be_done.strategic_actions.map((act, idx) => (
                              <div
                                key={idx}
                                className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-sm hover:border-slate-300 space-y-1.5"
                              >
                                <span className="inline-block px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 text-[10px] font-bold border border-indigo-100">
                                  Action Lever #{idx + 1}
                                </span>
                                <h6 className="text-xs font-bold text-slate-900">{act.title}</h6>
                                <p className="text-xs text-slate-600 leading-relaxed">{act.description}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                    {/* Advanced Analytics Roadmap */}
                    {reportData.what_can_be_done.advanced_analytics &&
                      reportData.what_can_be_done.advanced_analytics.length > 0 && (
                        <div className="space-y-2">
                          <h5 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                            <Cpu className="w-3.5 h-3.5 text-indigo-600" />
                            <span>B. Advanced Analytics & Machine Learning Roadmap</span>
                          </h5>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            {reportData.what_can_be_done.advanced_analytics.map((mod, idx) => (
                              <div
                                key={idx}
                                className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-sm hover:border-slate-300 space-y-1.5"
                              >
                                <span className="inline-block px-2 py-0.5 rounded bg-violet-50 text-violet-700 text-[10px] font-bold border border-violet-100">
                                  Data Science #{idx + 1}
                                </span>
                                <h6 className="text-xs font-bold text-slate-900">{mod.title}</h6>
                                <p className="text-xs text-slate-600 leading-relaxed">{mod.description}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                    {/* Data Enrichment Guidance */}
                    {reportData.what_can_be_done.data_enrichment && (
                      <div className="p-3.5 rounded-xl bg-slate-50/70 border border-slate-200 text-xs space-y-1">
                        <span className="font-bold text-slate-900 block">
                          C. Future Tracking & Data Feature Enrichment
                        </span>
                        <p className="text-slate-700 leading-relaxed">
                          {reportData.what_can_be_done.data_enrichment}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </>
            ) : (
              <div className="p-8 text-center text-xs text-slate-500 bg-slate-50 rounded-xl border border-slate-200">
                This report can be downloaded directly as an Executive PDF below.
              </div>
            )}
          </div>
        </div>
      ) : null}

      {/* 4. Generated Reports Archive (White Theme) */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-600" />
            <span>Generated Reports Archive ({reports.length})</span>
          </h3>
        </div>

        {reports.length === 0 ? (
          <div className="p-8 text-center border border-dashed border-slate-300 rounded-xl text-xs text-slate-500">
            No reports generated yet. Click "Generate Data Analyst Report" above!
          </div>
        ) : (
          <div className="space-y-2.5">
            {reports.map((r) => (
              <div
                key={r.id}
                className={`p-3.5 rounded-xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs ${
                  activeReport?.id === r.id
                    ? 'bg-indigo-50/40 border-indigo-300 ring-1 ring-indigo-200'
                    : 'bg-slate-50/60 border-slate-200 hover:bg-slate-50'
                }`}
              >
                <div className="space-y-0.5">
                  <div className="font-bold text-slate-900 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-indigo-600 shrink-0" />
                    <span>{r.name}</span>
                  </div>
                  <div className="flex items-center gap-2.5 text-[11px] text-slate-500">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3 text-slate-400" />
                      {new Date(r.created_at).toLocaleString()}
                    </span>
                    {r.report_data?.dataset_name && (
                      <span className="bg-slate-200/80 px-2 py-0.5 rounded text-slate-700 font-medium">
                        {r.report_data.dataset_name}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => setActiveReport(r)}
                    className="px-3 py-1.5 rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 font-medium flex items-center gap-1.5 transition-colors cursor-pointer shadow-2xs"
                  >
                    <Eye className="w-3.5 h-3.5 text-slate-500" />
                    <span>View Report</span>
                  </button>

                  <a
                    href={getDownloadUrl(r)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium flex items-center gap-1.5 shadow-sm transition-colors cursor-pointer"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download PDF</span>
                  </a>

                  {onDeleteReport && (
                    <button
                      onClick={() => onDeleteReport(r.id)}
                      className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition-colors cursor-pointer"
                      title="Delete Report"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
