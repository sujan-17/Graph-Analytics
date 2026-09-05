import React, { useState } from 'react';
import { History, CheckCircle, AlertTriangle, Code2, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
import { AnalysisResponse } from '../../types';

interface AnalysisHistoryProps {
  analyses: AnalysisResponse[];
}

export const AnalysisHistory: React.FC<AnalysisHistoryProps> = ({ analyses }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-2xl glass-panel border border-slate-800">
        <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
          <History className="w-5 h-5 text-indigo-400" />
          <span>Analysis History & Explainability Audit Log</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Complete transparent audit trail of past multi-agent queries, logical plans, generated AST code, and execution logs.
        </p>
      </div>

      {analyses.length === 0 ? (
        <div className="p-12 text-center border border-dashed border-slate-800 rounded-2xl text-slate-400">
          No analysis history found in this workspace yet. Ask a question in the AI Analyst tab!
        </div>
      ) : (
        <div className="space-y-4">
          {analyses.map((a) => {
            const isExpanded = expandedId === a.id;
            return (
              <div key={a.id} className="p-5 rounded-2xl glass-card border border-slate-800 space-y-4">
                <div
                  onClick={() => setExpandedId(isExpanded ? null : a.id)}
                  className="flex items-center justify-between cursor-pointer"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-sm text-white">{a.question}</span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          a.execution_status === 'SUCCESS'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}
                      >
                        {a.execution_status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400">
                      Executed: {new Date(a.created_at).toLocaleString()}
                    </p>
                  </div>

                  <button className="text-slate-400 hover:text-white">
                    {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                  </button>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="space-y-4 pt-4 border-t border-slate-800 text-xs">
                    {/* Intent */}
                    {a.intent && (
                      <div className="space-y-1">
                        <span className="font-bold text-indigo-400">Parsed Query Intent:</span>
                        <pre className="p-3 bg-slate-950 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-300">
                          {JSON.stringify(a.intent, null, 2)}
                        </pre>
                      </div>
                    )}

                    {/* Plan */}
                    {a.plan && (
                      <div className="space-y-1">
                        <span className="font-bold text-indigo-400">Logical Execution Plan:</span>
                        <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1 font-mono text-[11px] text-slate-300">
                          {a.plan.map((step, idx) => (
                            <div key={idx}>{step}</div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Generated Code */}
                    {a.generated_code && (
                      <div className="space-y-1">
                        <span className="font-bold text-indigo-400 flex items-center gap-1.5">
                          <Code2 className="w-3.5 h-3.5" />
                          <span>Generated Pandas Code:</span>
                        </span>
                        <pre className="p-3 bg-slate-950 rounded-xl border border-slate-800 font-mono text-[11px] text-emerald-400 overflow-x-auto">
                          {a.generated_code}
                        </pre>
                      </div>
                    )}

                    {/* Insights Summary */}
                    {a.insights && (
                      <div className="p-3 bg-indigo-950/40 border border-indigo-500/20 rounded-xl text-slate-200">
                        <span className="font-bold text-indigo-300 block mb-1">Synthesized Insight:</span>
                        <p>{a.insights}</p>
                      </div>
                    )}
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
