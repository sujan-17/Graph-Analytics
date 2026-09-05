import React, { useState, useRef, useEffect } from 'react';
import Plot from '../common/Plot';
import { Send, Bot, User as UserIcon, Code2, ChevronDown, ChevronUp, Sparkles, Download, Bookmark, AlertCircle, HelpCircle, ArrowRight, Table as TableIcon } from 'lucide-react';
import { AnalysisResponse, DatasetProfile } from '../../types';

interface AIAnalystChatProps {
  analyses: AnalysisResponse[];
  profile: DatasetProfile | null;
  initialQuestion?: string;
  onSendQuestion: (question: string) => Promise<void>;
  onSaveInsight: (content: string, analysisId?: string) => Promise<void>;
}

export const AIAnalystChat: React.FC<AIAnalystChatProps> = ({
  analyses,
  profile,
  initialQuestion,
  onSendQuestion,
  onSaveInsight,
}) => {
  const [inputQuestion, setInputQuestion] = useState(initialQuestion || '');
  const [loading, setLoading] = useState(false);
  const [openCodeId, setOpenCodeId] = useState<string | null>(null);
  const [openPlanId, setOpenPlanId] = useState<string | null>(null);
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

  const downloadCSV = (tableData: Record<string, any>[], filename: string) => {
    if (!tableData || tableData.length === 0) return;
    const keys = Object.keys(tableData[0]);
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [keys.join(','), ...tableData.map((row) => keys.map((k) => `"${row[k]}"`).join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${filename}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Health Score:</span>
            <span className="font-bold text-emerald-400">{profile.profile.data_quality.quality_score}%</span>
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

        {analyses.map((a) => (
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
                      {a.intent?.metric && (
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                          Metric: {a.intent.metric}
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

                {/* 4. Result Data Table */}
                {a.result_table && a.result_table.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-slate-300 flex items-center gap-1.5">
                        <TableIcon className="w-4 h-4 text-indigo-400" />
                        <span>Execution Output Result Table ({a.result_table.length} rows)</span>
                      </span>
                      <button
                        onClick={() => downloadCSV(a.result_table!, `analysis_${a.id}`)}
                        className="text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 text-[11px]"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Export CSV</span>
                      </button>
                    </div>

                    <div className="overflow-x-auto max-h-60 rounded-xl border border-slate-800">
                      <table className="w-full text-left text-xs text-slate-300">
                        <thead className="bg-slate-950 text-slate-300 font-semibold sticky top-0">
                          <tr>
                            {Object.keys(a.result_table[0]).map((k, kIdx) => (
                              <th key={kIdx} className="p-2.5 border-b border-slate-800 whitespace-nowrap">{k}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          {a.result_table.slice(0, 20).map((row, rIdx) => (
                            <tr key={rIdx} className="hover:bg-slate-900/60 font-mono text-[11px]">
                              {Object.keys(row).map((k, cIdx) => (
                                <td key={cIdx} className="p-2.5 whitespace-nowrap">{String(row[k])}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* 5. Business Insights & Recommendations */}
                {a.insights && (
                  <div className="p-4 bg-indigo-950/30 border border-indigo-500/20 rounded-xl space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
                        <Sparkles className="w-4 h-4" />
                        <span>AI Executive Business Insights</span>
                      </h4>
                      <button
                        onClick={() => onSaveInsight(a.insights!, a.id)}
                        className="px-2.5 py-1 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 text-[11px] font-medium flex items-center gap-1 transition-colors border border-indigo-500/30"
                      >
                        <Bookmark className="w-3.5 h-3.5" />
                        <span>Save Insight</span>
                      </button>
                    </div>
                    <p className="text-xs text-slate-200 leading-relaxed font-medium">{a.insights}</p>

                    {a.recommendations && a.recommendations.length > 0 && (
                      <div className="space-y-1 pt-2 border-t border-indigo-500/20">
                        <p className="text-[11px] font-bold text-indigo-300">Actionable Recommendations:</p>
                        <ul className="space-y-1 text-xs text-slate-300">
                          {a.recommendations.map((rec, rIdx) => (
                            <li key={rIdx} className="flex items-start gap-1.5">
                              <span className="text-indigo-400 font-bold">•</span>
                              <span>{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

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
              <span>LangGraph Multi-Agent Workflow Executing (Understanding Intent $\rightarrow$ Planning $\rightarrow$ AST Code Gen $\rightarrow$ Sandbox Execution)...</span>
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
