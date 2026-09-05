from typing import Dict, Any, List
from app.graph.state import AnalysisState

def visualization_node(state: AnalysisState) -> Dict[str, Any]:
    exec_result = state.get("execution_result", {})
    if not exec_result or exec_result.get("type") != "dataframe":
        return {"chart_config": None}

    columns = exec_result.get("columns", [])
    data = exec_result.get("data", [])
    if len(columns) < 2 or not data:
        return {"chart_config": None}

    # Inspect column types and values
    col1 = columns[0]
    col2 = columns[1]
    
    # Check if first column is date-like
    is_date = "date" in col1.lower() or "time" in col1.lower() or "month" in col1.lower() or "year" in col1.lower()
    
    chart_type = "bar"
    if is_date:
        chart_type = "line"
    elif len(columns) >= 2:
        val0 = data[0].get(col2)
        if isinstance(val0, (int, float)):
            chart_type = "bar"
        else:
            chart_type = "bar"

    x_vals = [d.get(col1) for d in data]
    y_vals = [d.get(col2) for d in data]

    plotly_spec = {
        "data": [{
            "x": x_vals,
            "y": y_vals,
            "type": "scatter" if chart_type == "line" else "bar",
            "mode": "lines+markers" if chart_type == "line" else None,
            "marker": {"color": "#6366f1"}
        }],
        "layout": {
            "title": f"{col2} by {col1}",
            "xaxis": {"title": col1},
            "yaxis": {"title": col2},
            "template": "plotly_dark",
            "margin": {"l": 40, "r": 40, "t": 40, "b": 40}
        }
    }

    return {
        "chart_config": {
            "type": chart_type,
            "spec": plotly_spec
        }
    }
