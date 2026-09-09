import React, { useState, useRef, useEffect } from 'react';
import Plot from '../common/Plot';
import { Send, Bot, User as UserIcon, Code2, ChevronDown, ChevronUp, Sparkles, Download, Bookmark, AlertCircle, HelpCircle, ArrowRight, Table as TableIcon, Link2, Check, RotateCcw } from 'lucide-react';
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
}

export const AIAnalystChat: React.FC<AIAnalystChatProps> = ({
  analyses,
  profile,
  initialQuestion,
  onSendQuestion,
  onSaveInsight,
  onNewSession,
}) => {
  const [inputQuestion, setInputQuestion] = useState(initialQuestion || '');
  const [loading, setLoading] = useState(false);
  const [openCodeId, setOpenCodeId] = useState<string | null>(null);
  const [openPlanId, setOpenPlanId] = useState<string | null>(null);
  const [copiedKeyFindingsId, setCopiedKeyFindingsId] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

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
    setInputQuestion('');
    setLoading(true);
    try {
      await onSendQuestion(q);
    } catch (err) {
      alert('Analysis execution failed. Please check backend logs or API key.');
    } finally {
      setLoading(false);
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
    <div className="flex flex-col h-[calc(100vh-6.5rem)] glass-panel rounded-2xl border border-slate-800 overflow-hidden">
      {/* Active Dataset Context Bar */}
      {profile && (
        <div className="bg-slate-900/90 border-b border-slate-800 px-6 py-2.5 flex items-center justify-between text-xs text-slate-300 shrink-0">
          <div className="flex items-center gap-2">
            <Bot className="w-4 h-4 text-indigo-400" />
            <span className="font-semibold text-white">Active Dataset:</span>
            <span className="font-mono text-indigo-300">{profile.profile.basic_info.filename}</span>
            <span className="text-slate-500">|</span>
            <span className="text-slate-400">{profile.profile.basic_info.row_count.toLocaleString()} rows</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="text-slate-400">Health Score:</span>
              <span className="font-bold text-emerald-400">{profile.profile.data_quality.quality_score}%</span>
            </div>
            {onNewSession && (
              <button
                onClick={onNewSession}
                className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] font-medium flex items-center gap-1.5 transition-colors border border-slate-700"
                title="Start a new conversational context session"
              >
                <RotateCcw className="w-3 h-3 text-indigo-400" />
                <span>New Session</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Main Conversational Thread Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {analyses.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-center max-w-md mx-auto space-y-4 text-slate-400">
            <div className="w-16 h-16 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shadow-xl">
              <Sparkles className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-white">Stateful AI Conversational Analyst</h3>
            <p className="text-xs leading-relaxed">
              Ask natural language business questions about your dataset. The multi-agent graph will understand intent, formulate an analysis plan, generate safe Pandas code, execute isolated analysis, and synthesize executive insights.
            </p>
            <div className="w-full space-y-2 pt-2">
              <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Example Questions:</p>
              {profile?.profile.semantic_summary?.potential_analyses.slice(0, 3).map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleFollowUp(q)}
                  className="w-full text-left p-2.5 rounded-xl bg-slate-900/60 hover:bg-indigo-950/40 text-xs text-indigo-300 border border-slate-800 hover:border-indigo-500/30 transition-all"
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
              <div className="bg-indigo-600 text-white rounded-2xl rounded-tr-none px-4 py-3 text-sm font-medium shadow-md shadow-indigo-600/20">
                {a.question}
              </div>
              <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0 border border-indigo-500/30">
                <UserIcon className="w-4 h-4" />
              </div>
            </div>

            {/* AI Multi-Agent Response Card */}
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-indigo-400 shrink-0 border border-slate-700">
                <Bot className="w-4 h-4" />
              </div>

              <div className="flex-1 bg-slate-900/90 border border-slate-800 rounded-2xl rounded-tl-none p-5 space-y-5 shadow-xl">
                {/* 1. Clarification Request if Ambiguous */}
                {a.needs_clarification && (
                  <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl space-y-3">
                    <div className="flex items-center gap-2 text-amber-400 text-xs font-bold uppercase tracking-wider">
                      <HelpCircle className="w-4 h-4" />
                      <span>Ambiguous Query Clarification Needed</span>
                    </div>
                    <p className="text-xs text-amber-200">{a.clarification_message}</p>
                    {a.clarification_options && (
                      <div className="flex flex-wrap gap-2 pt-1">
                        {a.clarification_options.map((opt, optIdx) => (
                          <button
                            key={optIdx}
                            onClick={() => handleFollowUp(opt)}
                            className="px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 text-xs font-medium transition-all"
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
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        Intent: {a.intent?.intent || 'Analysis'}
                      </span>
                      {a.intent?.group_by && a.intent.group_by.length > 0 && (
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                          By: {a.intent.group_by.join(', ')}
                        </span>
                      )}
                      {a.intent?.metrics && a.intent.metrics.length > 1 ? (
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                          Metrics: {a.intent.metrics.join(', ')}
                        </span>
                      ) : a.intent?.metric ? (
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                          Metric: {a.intent.metric}
                        </span>
                      ) : null}
                      {a.intent?.filters && Object.keys(a.intent.filters).length > 0 && (
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30">
                          Filters: {Object.entries(a.intent.filters).map(([k, v]) => `${k}=${v}`).join(', ')}
                        </span>
                      )}
                    </div>

                    {/* Step-by-Step Plan & Code Accordion Toggles */}
                    <div className="flex items-center gap-3 text-xs">
                      {a.plan && (
                        <button
                          onClick={() => setOpenPlanId(openPlanId === a.id ? null : a.id)}
                          className="text-slate-400 hover:text-slate-200 font-medium flex items-center gap-1"
                        >
                          <span>Plan ({a.plan.length} steps)</span>
                          {openPlanId === a.id ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </button>
                      )}
                      {a.generated_code && (
                        <button
                          onClick={() => setOpenCodeId(openCodeId === a.id ? null : a.id)}
                          className="text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1"
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
                  <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800 text-xs text-slate-300 space-y-1 font-mono">
                    <p className="font-sans font-bold text-slate-400 mb-1">Generated Analysis Plan:</p>
                    {a.plan.map((step, sIdx) => (
                      <div key={sIdx} className="text-slate-300">{step}</div>
                    ))}
                  </div>
                )}

                {/* Collapsible Code Accordion */}
                {openCodeId === a.id && a.generated_code && (
                  <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs font-mono overflow-x-auto text-emerald-400 space-y-1">
                    <div className="flex justify-between items-center text-[10px] text-slate-500 font-sans mb-1">
                      <span>AST-Validated Pandas Python Snippet</span>
                      <span className="text-emerald-500 font-bold">Executed Safely</span>
                    </div>
                    <pre>{a.generated_code}</pre>
                  </div>
                )}

                {/* Error Banner if Execution Failed or Had Errors */}
                {(a.execution_status === 'FAILED' || (a.error_message && (!a.result_table || a.result_table.length === 0))) && (
                  <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl space-y-2">
                    <div className="flex items-center gap-2 text-rose-400 text-xs font-bold uppercase tracking-wider">
                      <AlertCircle className="w-4 h-4" />
                      <span>Execution Error Notice</span>
                    </div>
                    <p className="text-xs text-rose-200 font-mono">
                      {a.error_message || 'The analysis query could not be executed.'}
                    </p>
                    <p className="text-[11px] text-slate-400">
                      Tip: Ensure you have configured a valid Google Gemini API Key in <code className="text-slate-300 font-mono">backend/.env</code>.
                    </p>
                  </div>
                )}

                {/* 3. Interactive Plotly Chart Widget */}
                {a.chart_spec && a.chart_spec.spec && (
                  <div className="p-4 bg-slate-950/50 rounded-xl border border-slate-800 space-y-2">
                    <div className="w-full h-80 rounded-lg overflow-hidden">
                      <Plot
                        data={a.chart_spec.spec.data}
                        layout={{
                          ...a.chart_spec.spec.layout,
                          autosize: true,
                          paper_bgcolor: 'rgba(0,0,0,0)',
                          plot_bgcolor: 'rgba(0,0,0,0)',
                          font: { color: '#cbd5e1', family: 'Inter' }
                        }}
                        useResizeHandler={true}
                        style={{ width: '100%', height: '100%' }}
                        config={{ responsive: true, displayModeBar: false }}
                      />
                    </div>
                  </div>
                )}

                {/* 4. Result Data Table with Sorting, Search Filtering, Pagination, and Multi-Format Exports */}
                {a.result_table && a.result_table.length > 0 && (
                  <AnalysisResultTable data={a.result_table} analysisId={a.id} />
                )}

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
                    <div className="p-5 bg-slate-950/80 border border-slate-800/90 rounded-2xl space-y-5">
                      {/* Top Header with Save Insight action */}
                      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>Executive Intelligence</span>
                        </span>
                        <button
                          onClick={() => onSaveInsight(fullInsightText, a.id)}
                          className="px-2.5 py-1 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 text-[11px] font-medium flex items-center gap-1 transition-colors border border-indigo-500/30"
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
                            <h3 className="text-base font-bold text-slate-100 tracking-tight">Key Findings</h3>
                            <button
                              type="button"
                              onClick={() => handleCopyKeyFindings(a.id, keyFindings)}
                              className="p-1 rounded-md text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors ml-0.5 group relative"
                              title="Copy Key Findings to clipboard"
                            >
                              {copiedKeyFindingsId === a.id ? (
                                <span className="flex items-center text-xs text-emerald-400 gap-1 font-sans">
                                  <Check className="w-3.5 h-3.5" />
                                  <span className="text-[10px]">Copied!</span>
                                </span>
                              ) : (
                                <Link2 className="w-4 h-4 text-slate-400 group-hover:text-indigo-400 transition-colors" />
                              )}
                            </button>
                          </div>
                          <ul className="space-y-2 pl-1">
                            {keyFindings.map((kf, kIdx) => (
                              <li key={kIdx} className="text-sm text-slate-300 leading-relaxed flex items-start gap-2.5">
                                <span className="text-slate-400 font-bold select-none leading-relaxed">•</span>
                                <div className="flex-1">
                                  {kf.title && (
                                    <strong className="font-semibold text-slate-100">
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
                            <h3 className="text-base font-bold text-slate-100 tracking-tight">Data Interpretation</h3>
                          </div>
                          <p className="text-sm text-slate-300 leading-relaxed pl-1">
                            {dataInterpretation}
                          </p>
                        </div>
                      )}

                      {/* 3. Strategic Recommendations */}
                      {strategicRecs.length > 0 && (
                        <div className="space-y-2.5 pt-1">
                          <div className="flex items-center gap-2">
                            <span className="text-lg select-none">🚀</span>
                            <h3 className="text-base font-bold text-slate-100 tracking-tight">Strategic Recommendations</h3>
                          </div>
                          <ol className="space-y-2.5 pl-1">
                            {strategicRecs.map((rec, rIdx) => (
                              <li key={rIdx} className="text-sm text-slate-300 leading-relaxed flex items-start gap-2.5">
                                <span className="text-slate-400 font-semibold select-none min-w-[1.2rem] text-sm leading-relaxed">
                                  {rIdx + 1}.
                                </span>
                                <div className="flex-1">
                                  {rec.title && (
                                    <strong className="font-semibold text-slate-100">
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
                    <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Suggested Next Questions:</p>
                    <div className="flex flex-wrap gap-2">
                      {a.follow_up_questions.map((fq, fIdx) => (
                        <button
                          key={fIdx}
                          onClick={() => handleFollowUp(fq)}
                          className="px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-indigo-600/20 text-slate-300 hover:text-indigo-200 border border-slate-700/80 text-xs font-medium flex items-center gap-1.5 transition-all group"
                        >
                          <span>{fq}</span>
                          <ArrowRight className="w-3 h-3 text-slate-500 group-hover:text-indigo-400 group-hover:translate-x-0.5 transition-all" />
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Loading Spinner Indicator */}
        {loading && (
          <div className="flex items-center gap-3 max-w-4xl mx-auto">
            <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-indigo-400 shrink-0 border border-slate-700 animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl rounded-tl-none text-xs text-indigo-400 flex items-center gap-3">
              <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
              <span>LangGraph Multi-Agent Workflow Executing (Understanding Intent → Planning → AST Code Gen → Sandbox Execution)...</span>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input Box Footer */}
      <form onSubmit={handleSubmit} className="p-4 bg-slate-900/90 border-t border-slate-800 flex items-center gap-3 shrink-0">
        <input
          type="text"
          placeholder="Ask a natural language data question (e.g. 'Show revenue by region', 'Only for 2025')..."
          className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 outline-none focus:border-indigo-500 transition-colors"
          value={inputQuestion}
          onChange={(e) => setInputQuestion(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !inputQuestion.trim()}
          className="px-5 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-sm rounded-xl shadow-lg shadow-indigo-600/30 flex items-center gap-2 transition-all shrink-0"
        >
          <span>Ask AI</span>
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
