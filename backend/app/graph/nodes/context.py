import json
from typing import Dict, Any
from app.graph.state import AnalysisState

def context_node(state: AnalysisState) -> Dict[str, Any]:
    """
    Loads and formats dataset context and conversation history into readable text blocks for LLM nodes.
    """
    profile = state.get("dataset_profile", {})
    basic_info = profile.get("basic_info", {})
    columns = profile.get("columns", [])
    kpis = profile.get("kpi_candidates", [])
    
    col_summary_lines = []
    for c in columns:
        col_type = c.get("data_type", "unknown")
        null_pct = c.get("null_percentage", 0)
        ex = c.get("example_values", [])
        line = f"- Column: '{c.get('name')}' (type: {col_type}, nulls: {null_pct}%, samples: {ex})"
        col_summary_lines.append(line)

    summary_str = f"""
Filename: {basic_info.get('filename')}
Rows: {basic_info.get('row_count')}, Columns: {basic_info.get('column_count')}
Detected KPIs: {[k.get('column') for k in kpis]}

Column Definitions:
{chr(10).join(col_summary_lines)}
"""

    history = state.get("conversation_history", [])
    hist_lines = []
    for msg in history[-8:]: # Last 8 messages
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
