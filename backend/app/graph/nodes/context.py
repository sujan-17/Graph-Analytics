import json
from typing import Dict, Any
from app.graph.state import AnalysisState
from app.graph.agents.base import BaseAgent

class ContextAgent(BaseAgent):
    """
    Context Ingestion Agent: Formats dataset metadata, column definitions,
    statistical summaries, detected KPIs, and conversational history
    into structured context representations for downstream agents.
    """
    name = "ContextAgent"
    role = "Dataset Schema & Conversation Memory Ingestion Agent"
    description = "Parses dataset profiles and conversation history into LLM-ready context blocks."

    def invoke(self, state: AnalysisState) -> Dict[str, Any]:
        profile = state.get("dataset_profile", {})
        basic_info = profile.get("basic_info", {})
        columns = profile.get("columns", [])
        kpis = profile.get("kpi_candidates", [])
        
        col_summary_lines = []
        is_combined = False
        source_examples = []
        for c in columns:
            col_type = c.get("data_type", "unknown")
            null_pct = c.get("null_percentage", 0)
            ex = c.get("example_values", [])
            if c.get("name") == "_source_dataset":
                is_combined = True
                source_examples = ex
            line = f"- Column: '{c.get('name')}' (type: {col_type}, nulls: {null_pct}%, samples: {ex})"
            col_summary_lines.append(line)

        combined_notice = ""
        if is_combined or str(basic_info.get("filename", "")).startswith("Combined_"):
            sources_desc = f" ({', '.join(str(s) for s in source_examples)})" if source_examples else ""
            combined_notice = f"""
COMBINED MULTI-DATASET TABLE NOTICE:
This table is a unified combination of multiple datasets from this workbench{sources_desc}.
The column '_source_dataset' identifies the originating file of each row.
- When querying a specific dataset or file mentioned in the user query: filter `df[df['_source_dataset'] == '<filename>']`.
- When comparing or grouping across files: group by `_source_dataset` (e.g. `df.groupby('_source_dataset')`).
- When querying overall metrics: calculate across `df` normally.
"""

        summary_str = f"""
Filename: {basic_info.get('filename')}
Rows: {basic_info.get('row_count')}, Columns: {basic_info.get('column_count')}
Detected KPIs: {[k.get('column') for k in kpis]}
{combined_notice}
Column Definitions:
{chr(10).join(col_summary_lines)}
"""

        history = state.get("conversation_history", [])
        hist_lines = []
        for msg in history[-8:]:  # Last 8 messages
            role = msg.get("role", "user")
            content = (msg.get("content") or "").strip()
            if role == "assistant" and len(content) > 300:
                content = content[:300] + "..."
            hist_lines.append(f"{role.upper()}: {content}")

        hist_str = "\n".join(hist_lines) if hist_lines else "No previous conversation history."

        return {
            "dataset_profile_summary": summary_str,
            "conversation_history_summary": hist_str,
            "retry_count": state.get("retry_count", 0)
        }

# Agent instance for LangGraph StateGraph & backward-compatible node export
context_agent = ContextAgent()
context_node = context_agent
