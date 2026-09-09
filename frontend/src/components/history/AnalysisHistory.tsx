import React, { useState, useMemo } from 'react';
import {
  History,
  CheckCircle,
  AlertTriangle,
  Code2,
  Sparkles,
  ChevronDown,
  ChevronUp,
  MessageSquare,
  ArrowRight,
  Table as TableIcon,
  HelpCircle,
  Bot,
  User as UserIcon,
  ArrowUpRight
} from 'lucide-react';
import { AnalysisResponse } from '../../types';
import { AnalysisResultTable } from '../chat/AnalysisResultTable';
import Plot from '../common/Plot';

interface AnalysisHistoryProps {
  analyses: AnalysisResponse[];
  onOpenInChat?: (conversationId: string) => void;
}

export const AnalysisHistory: React.FC<AnalysisHistoryProps> = ({ analyses, onOpenInChat }) => {
  const [expandedThreadId, setExpandedThreadId] = useState<string | null>(null);
  const [openCodeId, setOpenCodeId] = useState<string | null>(null);
  const [openPlanId, setOpenPlanId] = useState<string | null>(null);

  // Group analyses by conversation thread / specific prompt
  const threads = useMemo(() => {
    const threadMap: Record<string, AnalysisResponse[]> = {};
    const sorted = [...analyses].sort(
      (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );

    for (const a of sorted) {
      const key = a.conversation_id || a.id;
      if (!threadMap[key]) {
        threadMap[key] = [];
      }
      threadMap[key].push(a);
    }

    return Object.entries(threadMap)
      .map(([convId, threadAnalyses]) => ({
        conversationId: convId,
        rootQuestion: threadAnalyses[0].question,
        createdAt: threadAnalyses[0].created_at,
        updatedAt: threadAnalyses[threadAnalyses.length - 1].created_at,
        analyses: threadAnalyses,
        latestStatus: threadAnalyses[threadAnalyses.length - 1].execution_status,
      }))
      .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
  }, [analyses]);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-6 rounded-2xl glass-panel border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
            <History className="w-5 h-5 text-indigo-400" />
            <span>Analysis History & Prompt Sessions</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Complete audit trail of past conversational prompts, execution outputs, data tables, and AI insights.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-3 py-1 rounded-lg bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-medium">
            {threads.length} {threads.length === 1 ? 'Prompt Session' : 'Prompt Sessions'} ({analyses.length} total queries)
          </span>
        </div>
      </div>

      {/* Empty State */}
      {threads.length === 0 ? (
        <div className="p-16 text-center border border-dashed border-slate-800 rounded-2xl text-slate-400 space-y-3">
          <div className="w-12 h-12 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500">
            <History className="w-6 h-6" />
          </div>
          <p className="text-sm font-medium text-slate-300">No analysis history in this workspace yet.</p>
          <p className="text-xs text-slate-500">Ask a question in the AI Analyst tab to start your first analysis!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {threads.map((thread) => {
            const isExpanded = expandedThreadId === thread.conversationId;
            const isSuccess = thread.latestStatus === 'SUCCESS';

            return (
              <div
                key={thread.conversationId}
                className="rounded-2xl glass-card border border-slate-800/90 overflow-hidden transition-all duration-200"
              >
                {/* Specific Prompt Header Row */}
                <div
                  onClick={() => setExpandedThreadId(isExpanded ? null : thread.conversationId)}
                  className="p-5 flex items-center justify-between cursor-pointer hover:bg-slate-900/50 transition-colors select-none"
                >
                  <div className="space-y-1.5 flex-1 pr-4">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <span className="font-bold text-sm text-slate-100 leading-snug">
                        {thread.rootQuestion}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          isSuccess
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}
                      >
                        {thread.latestStatus}
                      </span>
                      {thread.analyses.length > 1 && (
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 flex items-center gap-1">
                          <MessageSquare className="w-3 h-3" />
                          <span>{thread.analyses.length} turns in conversation</span>
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400">
                      Executed: {new Date(thread.createdAt).toLocaleString()}
                      {thread.analyses.length > 1 && ` (last active: ${new Date(thread.updatedAt).toLocaleTimeString()})`}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {onOpenInChat && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenInChat(thread.conversationId);
                        }}
                        className="px-3 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 hover:text-white border border-indigo-500/30 text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm"
                        title="Resume this conversation in the AI Analyst Chat tab"
                      >
                        <Bot className="w-3.5 h-3.5" />
                        <span>Open in Chat</span>
                        <ArrowUpRight className="w-3.5 h-3.5 opacity-70" />
                      </button>
                    )}
                    <button
                      className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                      title={isExpanded ? 'Collapse prompt details' : 'Expand conversation history'}
                    >
                      {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                {/* Expanded Conversation Details Inside This Specific Prompt */}
                {isExpanded && (
                  <div className="p-5 pt-3 border-t border-slate-800/80 bg-slate-950/40 space-y-6">
                    <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 pb-1 border-b border-slate-800/60">
                      <MessageSquare className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Conversation Thread History ({thread.analyses.length} {thread.analyses.length === 1 ? 'Turn' : 'Turns'})</span>
                    </div>

                    {thread.analyses.map((a, idx) => (
                      <div
                        key={a.id}
                        className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/90 space-y-4 shadow-lg"
                      >
                        {/* Turn Header / Question */}
                        <div className="flex items-center justify-between gap-3 border-b border-slate-800 pb-3">
                          <div className="flex items-center gap-2.5">
                            <span className="w-6 h-6 rounded-lg bg-indigo-600/20 text-indigo-300 flex items-center justify-center font-bold text-xs border border-indigo-500/30">
                              {idx + 1}
                            </span>
                            <span className="font-bold text-sm text-white">{a.question}</span>
                          </div>
                          <span className="text-[11px] text-slate-500 font-mono">
                            {new Date(a.created_at).toLocaleTimeString()}
                          </span>
                        </div>

                        {/* Intent Badges */}
                        {a.intent && (
                          <div className="flex flex-wrap items-center gap-2 text-[10px]">
                            <span className="font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                              Intent: {a.intent.intent}
                            </span>
                            {a.intent.group_by && a.intent.group_by.length > 0 && (
                              <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 font-medium">
                                By: {a.intent.group_by.join(', ')}
                              </span>
                            )}
                            {a.intent.metrics && a.intent.metrics.length > 0 && (
                              <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 font-medium">
                                Metrics: {a.intent.metrics.join(', ')}
                              </span>
                            )}
                            {a.intent.filters && Object.keys(a.intent.filters).length > 0 && (
                              <span className="px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30 font-medium">
                                Filters: {Object.entries(a.intent.filters).map(([k, v]) => `${k}=${v}`).join(', ')}
                              </span>
                            )}
                          </div>
                        )}

                        {/* Interactive Result Table */}
                        {a.result_table && a.result_table.length > 0 && (
                          <div className="pt-1">
                            <AnalysisResultTable data={a.result_table} analysisId={a.id} />
                          </div>
                        )}

                        {/* Interactive Plotly Chart if Present */}
                        {a.chart_spec && a.chart_spec.spec && (
                          <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 space-y-2">
                            <div className="w-full h-72 rounded-lg overflow-hidden">
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

                        {/* Executive Insights & Intelligence */}
                        {(a.key_findings || a.data_interpretation || a.strategic_recommendations || a.insights) && (
                          <div className="p-4 bg-slate-950/80 border border-slate-800/90 rounded-xl space-y-3">
                            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
                              <Sparkles className="w-3.5 h-3.5" />
                              <span>Executive Intelligence</span>
                            </span>

                            {a.key_findings && a.key_findings.length > 0 && (
                              <div className="space-y-1.5">
                                <h4 className="text-xs font-bold text-slate-200">Key Findings:</h4>
                                <ul className="space-y-1 pl-2">
                                  {a.key_findings.map((kf, kIdx) => (
                                    <li key={kIdx} className="text-xs text-slate-300 flex items-start gap-2">
                                      <span className="text-indigo-400">•</span>
                                      <div>
                                        {kf.title && <strong className="text-slate-100">{kf.title}: </strong>}
                                        <span>{kf.description}</span>
                                      </div>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {a.data_interpretation && (
                              <div className="space-y-1 pt-1">
                                <h4 className="text-xs font-bold text-slate-200">Data Interpretation:</h4>
                                <p className="text-xs text-slate-300 leading-relaxed pl-2">
                                  {a.data_interpretation}
                                </p>
                              </div>
                            )}

                            {a.strategic_recommendations && a.strategic_recommendations.length > 0 && (
                              <div className="space-y-1.5 pt-1">
                                <h4 className="text-xs font-bold text-slate-200">Strategic Recommendations:</h4>
                                <ol className="space-y-1 pl-2">
                                  {a.strategic_recommendations.map((rec, rIdx) => (
                                    <li key={rIdx} className="text-xs text-slate-300 flex items-start gap-2">
                                      <span className="text-slate-400">{rIdx + 1}.</span>
                                      <div>
                                        {rec.title && <strong className="text-slate-100">{rec.title}: </strong>}
                                        <span>{rec.description}</span>
                                      </div>
                                    </li>
                                  ))}
                                </ol>
                              </div>
                            )}

                            {!a.key_findings && !a.data_interpretation && !a.strategic_recommendations && a.insights && (
                              <p className="text-xs text-slate-300 leading-relaxed">{a.insights}</p>
                            )}
                          </div>
                        )}

                        {/* Accordions: Plan & Inspect Code */}
                        <div className="flex items-center gap-4 text-xs pt-1">
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

                        {openPlanId === a.id && a.plan && (
                          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs text-slate-300 font-mono space-y-1">
                            {a.plan.map((step, sIdx) => (
                              <div key={sIdx}>{step}</div>
                            ))}
                          </div>
                        )}

                        {openCodeId === a.id && a.generated_code && (
                          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs font-mono text-emerald-400 overflow-x-auto">
                            <pre>{a.generated_code}</pre>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
