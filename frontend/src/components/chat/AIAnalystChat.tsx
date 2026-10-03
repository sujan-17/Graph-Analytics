import React, { useState, useRef, useEffect } from 'react';
import Plot from '../common/Plot';
import { Send, Bot, User as UserIcon, Code2, ChevronDown, ChevronUp, Sparkles, Download, Bookmark, AlertCircle, HelpCircle, ArrowRight, Table as TableIcon, Link2, Check, RotateCcw, History, BarChart3, Eye, Layers } from 'lucide-react';
import { AnalysisResponse, DatasetProfile } from '../../types';
import { AnalysisResultTable } from './AnalysisResultTable';

interface InsightItem {
  title: string;
  description: string;
}

const parseInsightItem = (raw: string): InsightItem => {
  const clean = raw.replace(/^\s*(\d+[\.\)]|\*|-|•)\s*/, '').trim();
  const boldMatch = clean.match(/^\*\*([^*]+)\*\*[:\s-]*(.*)$/);
  if (boldMatch) {
    return { title: boldMatch[1].trim(), description: boldMatch[2].trim() };
  }
  const colonIdx = clean.indexOf(':');
  if (colonIdx > 0 && colonIdx < 55) {
    return {
      title: clean.substring(0, colonIdx).replace(/\*\*/g, '').trim(),
      description: clean.substring(colonIdx + 1).trim()
    };
  }
  return { title: '', description: clean };
};

const getKeyFindings = (a: AnalysisResponse): InsightItem[] => {
  if (a.key_findings && a.key_findings.length > 0) {
    return a.key_findings;
  }
  if (a.insights) {
    const lines = a.insights.split('\n').map(l => l.trim()).filter(Boolean);
    const bullets = lines.filter(l => l.startsWith('•') || l.startsWith('-') || l.startsWith('*') || /^\d+[\.\)]/.test(l));
    if (bullets.length > 0) {
      return bullets.map(parseInsightItem);
    }
  }
  return [];
};

const getDataInterpretation = (a: AnalysisResponse): string => {
  if (a.data_interpretation) {
    return a.data_interpretation;
  }
  if (a.insights) {
    const lines = a.insights.split('\n').map(l => l.trim()).filter(Boolean);
    const nonBullets = lines.filter(l => !l.startsWith('•') && !l.startsWith('-') && !l.startsWith('*') && !/^\d+[\.\)]/.test(l));
    return nonBullets.join(' ') || a.insights;
  }
  return '';
};

const getStrategicRecommendations = (a: AnalysisResponse): InsightItem[] => {
  if (a.strategic_recommendations && a.strategic_recommendations.length > 0) {
    return a.strategic_recommendations;
  }
  if (a.recommendations && a.recommendations.length > 0) {
    return a.recommendations.map(r => parseInsightItem(r));
  }
  return [];
};

interface AIAnalystChatProps {
  analyses: AnalysisResponse[];
  profile: DatasetProfile | null;
  initialQuestion?: string;
  onSendQuestion: (question: string) => Promise<void>;
  onSaveInsight: (content: string, analysisId?: string) => Promise<void>;
  onNewSession?: () => void;
  activeConversationId?: string;
  totalPastSessions?: number;
  onNavigateToHistory?: () => void;
}

export const AIAnalystChat: React.FC<AIAnalystChatProps> = ({
  analyses,
  profile,
  initialQuestion,
  onSendQuestion,
  onSaveInsight,
  onNewSession,
  activeConversationId,
  totalPastSessions,
  onNavigateToHistory,
}) => {
  const [inputQuestion, setInputQuestion] = useState(initialQuestion || '');
  const [loading, setLoading] = useState(false);
  const [openCodeId, setOpenCodeId] = useState<string | null>(null);
  const [openPlanId, setOpenPlanId] = useState<string | null>(null);
  const [copiedKeyFindingsId, setCopiedKeyFindingsId] = useState<string | null>(null);
  const [activeTabs, setActiveTabs] = useState<Record<string, 'visualization' | 'table'>>({});
  const [pendingQuestion, setPendingQuestion] = useState<string>('');
  const chatEndRef = useRef<HTMLDivElement>(null);

  const getActiveTab = (a: AnalysisResponse): 'visualization' | 'table' => {
    if (activeTabs[a.id]) {
      return activeTabs[a.id];
    }
    const hasChart = !!(a.chart_spec && a.chart_spec.spec);
    if (a.presentation_type === 'table' || !hasChart) {
      return 'table';
    }
    return 'visualization';
  };

  useEffect(() => {
    if (initialQuestion) {
      setInputQuestion(initialQuestion);
    }
  }, [initialQuestion]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [analyses, loading]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputQuestion.trim() || loading) return;

    const q = inputQuestion;
    setPendingQuestion(q);
    setInputQuestion('');
    setLoading(true);
    try {
      await onSendQuestion(q);
    } catch (err) {
      alert('Analysis execution failed. Please check backend logs or try rephrasing your question.');
    } finally {
      setLoading(false);
      setPendingQuestion('');
    }
  };

  const handleFollowUp = (suggestedQ: string) => {
    setInputQuestion(suggestedQ);
  };


  const handleCopyKeyFindings = (id: string, items: InsightItem[]) => {
    const text = items.map((it) => `• ${it.title ? `${it.title}: ` : ''}${it.description}`).join('\n');
    navigator.clipboard.writeText(text);
    setCopiedKeyFindingsId(id);
    setTimeout(() => {
      setCopiedKeyFindingsId(null);
    }, 2000);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-6.5rem)] bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Active Dataset Context Bar & Conversational Session Controls */}
      {profile && (
        <div className="bg-slate-50 border-b border-slate-200 px-6 py-2.5 flex items-center justify-between text-xs text-slate-600 shrink-0">
          <div className="flex items-center gap-2">
            <Bot className="w-4 h-4 text-indigo-600" />
            <span className="font-semibold text-slate-800">Active Dataset:</span>
            <span className="font-mono text-indigo-600 font-semibold">{profile.profile.basic_info.filename}</span>
            <span className="text-slate-300">|</span>
            <span className="text-slate-500">{profile.profile.basic_info.row_count.toLocaleString()} rows</span>
            {analyses.length > 0 && (
              <>
                <span className="text-slate-300">|</span>
                <span className="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200 text-[11px] font-medium">
                  {analyses.length} {analyses.length === 1 ? 'turn in session' : 'turns in session'}
                </span>
              </>
            )}
          </div>
          <div className="flex items-center gap-2.5">
            <div className="flex items-center gap-1.5 mr-1 hidden sm:flex">
              <span className="text-slate-500">Health Score:</span>
              <span className="font-bold text-emerald-600">{profile.profile.data_quality.quality_score}%</span>
            </div>
            {onNavigateToHistory && (totalPastSessions ?? 0) > 0 && (
              <button
                type="button"
                onClick={onNavigateToHistory}
                className="px-2.5 py-1 rounded-lg bg-white hover:bg-slate-100 text-slate-700 hover:text-slate-900 text-[11px] font-medium flex items-center gap-1.5 transition-colors border border-slate-200 shadow-xs"
                title="View all past conversations in Analysis History"
              >
                <History className="w-3.5 h-3.5 text-indigo-600" />
                <span>History ({totalPastSessions})</span>
              </button>
            )}
            {onNewSession && (
              <button
                type="button"
                onClick={onNewSession}
                className="px-2.5 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 hover:text-indigo-800 text-[11px] font-medium flex items-center gap-1.5 transition-colors border border-indigo-200 shadow-xs"
                title="Start a fresh prompt session (previous conversation remains in Analysis History)"
              >
                <RotateCcw className="w-3.5 h-3.5 text-indigo-600" />
                <span>New Session</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Main Conversational Thread Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/40">
        {analyses.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-center max-w-md mx-auto space-y-4 text-slate-500">
            <div className="w-16 h-16 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shadow-sm">
              <Sparkles className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Stateful AI Conversational Analyst</h3>
            <p className="text-xs leading-relaxed">
              Ask natural language business questions about your dataset. The multi-agent graph will understand intent, formulate an analysis plan, generate safe Pandas code, execute isolated analysis, and synthesize executive insights.
            </p>
            {onNavigateToHistory && (totalPastSessions ?? 0) > 0 && (
              <div className="pt-1">
                <button
                  type="button"
                  onClick={onNavigateToHistory}
                  className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white hover:bg-slate-50 text-indigo-600 hover:text-indigo-700 text-xs font-semibold border border-slate-200 shadow-sm transition-all"
                >
                  <History className="w-3.5 h-3.5 text-indigo-600" />
                  <span>View {totalPastSessions} Past Prompt {totalPastSessions === 1 ? 'Session' : 'Sessions'} in Analysis History</span>
                </button>
              </div>
            )}
            <div className="w-full space-y-2 pt-2">
              <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Example Questions:</p>
              {profile?.profile.semantic_summary?.potential_analyses.slice(0, 3).map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleFollowUp(q)}
                  className="w-full text-left p-2.5 rounded-xl bg-white hover:bg-indigo-50/50 text-xs text-indigo-700 border border-slate-200 hover:border-indigo-300 shadow-xs transition-all"
                >
                  "{q}"
                </button>
              ))}
            </div>
          </div>
        )}

        {[...analyses]
          .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
          .map((a) => (
          <div key={a.id} className="space-y-4 max-w-4xl mx-auto">
            {/* User Question Bubble */}
            <div className="flex items-start gap-3 justify-end">
              <div className="bg-indigo-600 text-white rounded-2xl rounded-tr-none px-4 py-3 text-sm font-medium shadow-sm shadow-indigo-600/20">
                {a.question}
              </div>
              <div className="w-8 h-8 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600 shrink-0 border border-indigo-200">
                <UserIcon className="w-4 h-4" />
              </div>
            </div>

            {/* AI Multi-Agent Response Card */}
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600 shrink-0 border border-indigo-200">
                <Bot className="w-4 h-4" />
              </div>

              <div className="flex-1 bg-white border border-slate-200 rounded-2xl rounded-tl-none p-5 space-y-5 shadow-sm">
                {/* 1. Clarification Request if Ambiguous */}
                {a.needs_clarification && (
                  <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl space-y-3">
                    <div className="flex items-center gap-2 text-amber-700 text-xs font-bold uppercase tracking-wider">
                      <HelpCircle className="w-4 h-4" />
                      <span>Ambiguous Query Clarification Needed</span>
                    </div>
                    <p className="text-xs text-amber-900">{a.clarification_message}</p>
                    {a.clarification_options && (
                      <div className="flex flex-wrap gap-2 pt-1">
                        {a.clarification_options.map((opt, optIdx) => (
                          <button
                            key={optIdx}
                            onClick={() => handleFollowUp(opt)}
                            className="px-3 py-1.5 rounded-lg bg-white hover:bg-amber-100 text-amber-800 text-xs font-medium transition-all border border-amber-300"
                          >
                            {opt}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* 2. Structured Query Intent Tag & Plan Header */}
                {!a.needs_clarification && (
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                        Intent: {a.intent?.intent || 'Analysis'}
                      </span>
                      {a.intent?.group_by && a.intent.group_by.length > 0 && (
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                          By: {a.intent.group_by.join(', ')}
                        </span>
                      )}
                      {a.intent?.metrics && a.intent.metrics.length > 1 ? (
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                          Metrics: {a.intent.metrics.join(', ')}
                        </span>
                      ) : a.intent?.metric ? (
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                          Metric: {a.intent.metric}
                        </span>
                      ) : null}
                      {a.intent?.filters && Object.keys(a.intent.filters).length > 0 && (
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                          Filters: {Object.entries(a.intent.filters).map(([k, v]) => `${k}=${v}`).join(', ')}
                        </span>
                      )}
                    </div>

                    {/* Step-by-Step Plan & Code Accordion Toggles */}
                    <div className="flex items-center gap-3 text-xs">
                      {a.plan && (
                        <button
                          onClick={() => setOpenPlanId(openPlanId === a.id ? null : a.id)}
                          className="text-slate-500 hover:text-slate-800 font-medium flex items-center gap-1"
                        >
                          <span>Plan ({a.plan.length} steps)</span>
                          {openPlanId === a.id ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </button>
                      )}
                      {a.generated_code && (
                        <button
                          onClick={() => setOpenCodeId(openCodeId === a.id ? null : a.id)}
                          className="text-indigo-600 hover:text-indigo-700 font-medium flex items-center gap-1"
                        >
                          <Code2 className="w-3.5 h-3.5" />
                          <span>Inspect Code</span>
                          {openCodeId === a.id ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {/* Collapsible Plan Accordion */}
                {openPlanId === a.id && a.plan && (
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 space-y-1 font-mono">
                    <p className="font-sans font-bold text-slate-800 mb-1">Generated Analysis Plan:</p>
                    {a.plan.map((step, sIdx) => (
                      <div key={sIdx} className="text-slate-700">{step}</div>
                    ))}
                  </div>
                )}

                {/* Collapsible Code Accordion */}
                {openCodeId === a.id && a.generated_code && (
                  <div className="p-3 bg-slate-900 rounded-xl border border-slate-800 text-xs font-mono overflow-x-auto text-emerald-400 space-y-1">
                    <div className="flex justify-between items-center text-[10px] text-slate-400 font-sans mb-1">
                      <span>AST-Validated Pandas Python Snippet</span>
                      <span className="text-emerald-400 font-bold">Executed Safely</span>
                    </div>
                    <pre>{a.generated_code}</pre>
                  </div>
                )}

                {/* Error Banner if Execution Failed or Had Errors */}
                {(a.execution_status === 'FAILED' || (a.error_message && (!a.result_table || a.result_table.length === 0))) && (
                  <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl space-y-2">
                    <div className="flex items-center gap-2 text-rose-700 text-xs font-bold uppercase tracking-wider">
                      <AlertCircle className="w-4 h-4" />
                      <span>Execution Error Notice</span>
                    </div>
                    <p className="text-xs text-rose-800 font-mono">
                      {a.error_message || 'The analysis query could not be executed.'}
                    </p>
                    <p className="text-[11px] text-slate-500">
                      Tip: The system is powered by Google Gemini via server configuration in <code className="text-slate-700 font-mono">backend/.env</code>.
                    </p>
                  </div>
                )}

                {/* 3 & 4. Intelligent Presentation Layer: Visualization vs Data Table & Oversight */}
                {(() => {
                  const hasChart = !!(a.chart_spec && a.chart_spec.spec);
                  const hasTable = !!(a.result_table && a.result_table.length > 0);
                  if (!hasChart && !hasTable) return null;

                  const currentTab = getActiveTab(a);

                  return (
                    <div className="space-y-3">
                      {/* View Switcher Header (when both chart and table exist) */}
                      {hasChart && hasTable && (
                        <div className="flex items-center justify-between pb-1 pt-1 border-b border-slate-100">
                          <div className="flex items-center gap-1.5 p-1 bg-slate-100 border border-slate-200 rounded-xl text-xs">
                            <button
                              type="button"
                              onClick={() => setActiveTabs(prev => ({ ...prev, [a.id]: 'visualization' }))}
                              className={`px-3 py-1.5 rounded-lg font-medium flex items-center gap-1.5 transition-all ${
                                currentTab === 'visualization'
                                  ? 'bg-white text-indigo-700 shadow-sm font-semibold border border-slate-200/80'
                                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
                              }`}
                            >
                              <BarChart3 className="w-3.5 h-3.5" />
                              <span>Visualization</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => setActiveTabs(prev => ({ ...prev, [a.id]: 'table' }))}
                              className={`px-3 py-1.5 rounded-lg font-medium flex items-center gap-1.5 transition-all ${
                                currentTab === 'table'
                                  ? 'bg-white text-indigo-700 shadow-sm font-semibold border border-slate-200/80'
                                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
                              }`}
                            >
                              <TableIcon className="w-3.5 h-3.5" />
                              <span>Data Table & Oversight</span>
                              <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
                                currentTab === 'table' ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-slate-200 text-slate-600'
                              }`}>
                                {a.result_table?.length}
                              </span>
                            </button>
                          </div>

                          <div className="text-[11px] text-slate-500 hidden sm:flex items-center gap-2">
                            {currentTab === 'visualization' ? (
                              <span className="flex items-center gap-1 text-indigo-600 font-medium">
                                <Eye className="w-3.5 h-3.5" /> Interactive Chart Mode
                              </span>
                            ) : (
                              <span className="flex items-center gap-1 text-slate-500 font-medium">
                                <Layers className="w-3.5 h-3.5" /> Underlying Records & Export
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Presentation View: Visualization Hero */}
                      {currentTab === 'visualization' && hasChart && (
                        <div className="space-y-3">
                          <div className="p-4 bg-slate-50/60 rounded-2xl border border-slate-200 space-y-2">
                            <div className="w-full h-80 rounded-lg overflow-hidden">
                              <Plot
                                data={a.chart_spec!.spec.data}
                                layout={{
                                  ...a.chart_spec!.spec.layout,
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

                          {/* Executive Data Oversight Bar (Compact Summary without table clutter) */}
                          <div className="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl flex flex-wrap items-center justify-between gap-3 text-xs">
                            <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-slate-700">
                              <div className="flex items-center gap-1.5">
                                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                                <span className="text-slate-500">Data Oversight:</span>
                                <span className="font-semibold text-slate-800">{a.result_table?.length || 0} records analyzed</span>
                              </div>
                              {a.data_oversight?.metric_totals && Object.entries(a.data_oversight.metric_totals).slice(0, 3).map(([metric, total]) => (
                                <div key={metric} className="flex items-center gap-1">
                                  <span className="text-slate-500">{metric}:</span>
                                  <span className="font-semibold text-indigo-700">
                                    {metric.toLowerCase().includes('profit') || metric.toLowerCase().includes('sales') || metric.toLowerCase().includes('revenue')
                                      ? `$${Number(total).toLocaleString()}`
                                      : Number(total).toLocaleString()}
                                  </span>
                                </div>
                              ))}
                            </div>

                            {hasTable && (
                              <button
                                type="button"
                                onClick={() => setActiveTabs(prev => ({ ...prev, [a.id]: 'table' }))}
                                className="text-[11px] font-medium text-indigo-600 hover:text-indigo-800 flex items-center gap-1 hover:underline group ml-auto"
                              >
                                <span>Inspect Full Table & Exports</span>
                                <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                              </button>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Presentation View: Data Table & Oversight */}
                      {(currentTab === 'table' || !hasChart) && hasTable && (
                        <div className="space-y-2">
                          {hasChart && (
                            <div className="flex justify-end">
                              <button
                                type="button"
                                onClick={() => setActiveTabs(prev => ({ ...prev, [a.id]: 'visualization' }))}
                                className="text-[11px] font-medium text-indigo-600 hover:text-indigo-800 flex items-center gap-1 hover:underline"
                              >
                                <BarChart3 className="w-3 h-3" />
                                <span>Switch back to Visualization</span>
                              </button>
                            </div>
                          )}
                          <AnalysisResultTable data={a.result_table!} analysisId={a.id} />
                        </div>
                      )}
                    </div>
                  );
                })()}

                {/* 5. Executive Insights: Key Findings, Data Interpretation & Strategic Recommendations */}
                {(() => {
                  const keyFindings = getKeyFindings(a);
                  const dataInterpretation = getDataInterpretation(a);
                  const strategicRecs = getStrategicRecommendations(a);
                  const hasExecutiveInsights = keyFindings.length > 0 || !!dataInterpretation || strategicRecs.length > 0;

                  if (!hasExecutiveInsights) return null;

                  const fullInsightText = [
                    keyFindings.length ? `Key Findings:\n` + keyFindings.map((k) => `• ${k.title ? `${k.title}: ` : ''}${k.description}`).join('\n') : '',
                    dataInterpretation ? `\nData Interpretation:\n${dataInterpretation}` : '',
                    strategicRecs.length ? `\nStrategic Recommendations:\n` + strategicRecs.map((r, i) => `${i + 1}. ${r.title ? `${r.title}: ` : ''}${r.description}`).join('\n') : ''
                  ].filter(Boolean).join('\n') || a.insights || '';

                  return (
                    <div className="p-5 bg-slate-50/70 border border-slate-200 rounded-2xl space-y-5">
                      {/* Top Header with Save Insight action */}
                      <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-600 flex items-center gap-1.5">
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>Executive Intelligence</span>
                        </span>
                        <button
                          onClick={() => onSaveInsight(fullInsightText, a.id)}
                          className="px-2.5 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-[11px] font-medium flex items-center gap-1 transition-colors border border-indigo-200"
                        >
                          <Bookmark className="w-3.5 h-3.5" />
                          <span>Save Insight</span>
                        </button>
                      </div>

                      {/* 1. Key Findings */}
                      {keyFindings.length > 0 && (
                        <div className="space-y-2.5">
                          <div className="flex items-center gap-2">
                            <span className="text-lg select-none">🎯</span>
                            <h3 className="text-base font-bold text-slate-900 tracking-tight">Key Findings</h3>
                            <button
                              type="button"
                              onClick={() => handleCopyKeyFindings(a.id, keyFindings)}
                              className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-200/50 transition-colors ml-0.5 group relative"
                              title="Copy Key Findings to clipboard"
                            >
                              {copiedKeyFindingsId === a.id ? (
                                <span className="flex items-center text-xs text-emerald-600 gap-1 font-sans">
                                  <Check className="w-3.5 h-3.5" />
                                  <span className="text-[10px]">Copied!</span>
                                </span>
                              ) : (
                                <Link2 className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 transition-colors" />
                              )}
                            </button>
                          </div>
                          <ul className="space-y-2 pl-1">
                            {keyFindings.map((kf, kIdx) => (
                              <li key={kIdx} className="text-sm text-slate-700 leading-relaxed flex items-start gap-2.5">
                                <span className="text-slate-400 font-bold select-none leading-relaxed">•</span>
                                <div className="flex-1">
                                  {kf.title && (
                                    <strong className="font-semibold text-slate-900">
                                      {kf.title}{!kf.title.trim().endsWith(':') ? ':' : ''}{' '}
                                    </strong>
                                  )}
                                  <span>{kf.description}</span>
                                </div>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* 2. Data Interpretation */}
                      {dataInterpretation && (
                        <div className="space-y-2.5 pt-1">
                          <div className="flex items-center gap-2">
                            <span className="text-lg select-none">📊</span>
                            <h3 className="text-base font-bold text-slate-900 tracking-tight">Data Interpretation</h3>
                          </div>
                          <p className="text-sm text-slate-700 leading-relaxed pl-1">
                            {dataInterpretation}
                          </p>
                        </div>
                      )}

                      {/* 3. Strategic Recommendations */}
                      {strategicRecs.length > 0 && (
                        <div className="space-y-2.5 pt-1">
                          <div className="flex items-center gap-2">
                            <span className="text-lg select-none">🚀</span>
                            <h3 className="text-base font-bold text-slate-900 tracking-tight">Strategic Recommendations</h3>
                          </div>
                          <ol className="space-y-2.5 pl-1">
                            {strategicRecs.map((rec, rIdx) => (
                              <li key={rIdx} className="text-sm text-slate-700 leading-relaxed flex items-start gap-2.5">
                                <span className="text-slate-400 font-semibold select-none min-w-[1.2rem] text-sm leading-relaxed">
                                  {rIdx + 1}.
                                </span>
                                <div className="flex-1">
                                  {rec.title && (
                                    <strong className="font-semibold text-slate-900">
                                      {rec.title}{!rec.title.trim().endsWith(':') ? ':' : ''}{' '}
                                    </strong>
                                  )}
                                  <span>{rec.description}</span>
                                </div>
                              </li>
                            ))}
                          </ol>
                        </div>
                      )}
                    </div>
                  );
                })()}

                {/* 6. Context-Aware Suggested Follow-Up Questions */}
                {a.follow_up_questions && a.follow_up_questions.length > 0 && (
                  <div className="space-y-2 pt-2">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Suggested Next Questions:</p>
                    <div className="flex flex-wrap gap-2">
                      {a.follow_up_questions.map((fq, fIdx) => (
                        <button
                          key={fIdx}
                          onClick={() => handleFollowUp(fq)}
                          className="px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-indigo-50 text-slate-700 hover:text-indigo-700 border border-slate-200 text-xs font-medium flex items-center gap-1.5 transition-all group"
                        >
                          <span>{fq}</span>
                          <ArrowRight className="w-3 h-3 text-slate-400 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition-all" />
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Loading Spinner Indicator showing user query */}
        {loading && (
          <div className="space-y-4 max-w-4xl mx-auto">
            {/* Optimistic User Question Bubble while waiting */}
            {pendingQuestion && (
              <div className="flex items-start gap-3 justify-end">
                <div className="bg-indigo-600 text-white rounded-2xl rounded-tr-none px-4 py-3 text-sm font-medium shadow-sm shadow-indigo-600/20">
                  {pendingQuestion}
                </div>
                <div className="w-8 h-8 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600 shrink-0 border border-indigo-200">
                  <UserIcon className="w-4 h-4" />
                </div>
              </div>
            )}

            {/* AI Agent Analyzing Box displaying user query */}
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600 shrink-0 border border-indigo-200 animate-pulse">
                <Bot className="w-4 h-4" />
              </div>
              <div className="p-4 bg-white border border-slate-200 rounded-2xl rounded-tl-none text-xs text-indigo-600 flex items-center gap-3 shadow-sm">
                <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin shrink-0" />
                <span className="font-medium text-slate-800">
                  {pendingQuestion || 'Analyzing query...'}
                </span>
              </div>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input Box Footer */}
      <form onSubmit={handleSubmit} className="p-4 bg-white border-t border-slate-200 flex items-center gap-3 shrink-0">
        <input
          type="text"
          placeholder="Ask a natural language data question (e.g. 'Show revenue by region', 'Only for 2025')..."
          className="flex-1 bg-slate-50 border border-slate-300 rounded-xl px-4 py-3 text-sm text-slate-900 outline-none focus:bg-white focus:border-indigo-600 transition-colors placeholder:text-slate-400"
          value={inputQuestion}
          onChange={(e) => setInputQuestion(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !inputQuestion.trim()}
          className="px-5 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold text-sm rounded-xl shadow-md shadow-indigo-600/20 flex items-center gap-2 transition-all shrink-0"
        >
          <span>Ask AI</span>
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
