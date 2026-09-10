from typing import Dict, Any, List
from app.graph.state import AnalysisState

def should_generate_visualization(state: AnalysisState, columns: List[str], data: List[Dict[str, Any]]) -> bool:
    """
    Determines whether generating a chart is analytically meaningful.
    Charts are generated ONLY for aggregations, groupings, comparisons, trends,
    or when explicitly requested by the user.
    Detail, lookup, and raw record filtering queries (e.g. 'give me the details of the person...')
    must NOT generate a chart.
    """
    user_query = (state.get("user_query") or "").lower().strip()
    query_intent = state.get("query_intent") or {}
    intent_type = (query_intent.get("intent") or "").lower().strip()
    group_by = query_intent.get("group_by") or []

    # 1. User explicitly requested a chart/plot/visual
    chart_keywords = ["chart", "plot", "graph", "visualize", "visualization", "histogram", "pie", "trend", "scatter"]
    user_explicitly_wants_chart = any(k in user_query for k in chart_keywords)

    # 2. Detail / record lookup queries: NEVER generate chart unless explicitly requested
    detail_keywords = [
        "detail", "details", "who", "which person", "which customer", "which buyer",
        "person", "customer", "buyer", "list of", "list all", "show records",
        "show rows", "raw data", "orders", "lookup", "give me the details",
        "find the person", "find the customer", "show me the details", "give me details"
    ]
    is_detail_query = any(k in user_query for k in detail_keywords)
    if is_detail_query and not user_explicitly_wants_chart:
        return False

    # 3. If intent is filtering / lookup / detail without any group_by, do not generate chart
    if intent_type in ["filtering", "lookup", "detail", "records", "search"] and not group_by and not user_explicitly_wants_chart:
        return False

    # 4. Result size check: empty cannot be visualized
    if len(data) == 0:
        return False

    # 5. Check if the table is solely individual records with only ID columns and no analytical intent
    valid_cols = [c for c in columns if c.lower() not in ["index", "level_0"]]
    non_numeric_cols = []
    genuine_dimension_cols = []
    for c in valid_cols:
        vals = [d.get(c) for d in data if d.get(c) is not None]
        if vals and not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals[:25]):
            non_numeric_cols.append(c)
            is_id = any(term in c.lower() for term in ["id", "uuid", "key", "code", "number"])
            if not is_id:
                genuine_dimension_cols.append(c)

    # If the only non-numeric column is an ID column and intent is not analytical, suppress chart
    if non_numeric_cols and not genuine_dimension_cols and intent_type not in ["aggregation", "grouping", "comparison", "trend", "distribution", "ranking"] and not user_explicitly_wants_chart:
        return False

    # 6. If intent is not an analytical intent and no grouping was requested
    analytical_intents = ["aggregation", "grouping", "comparison", "trend", "distribution", "ranking"]
    if intent_type not in analytical_intents and not group_by and not user_explicitly_wants_chart:
        return False

    return True

def visualization_node(state: AnalysisState) -> Dict[str, Any]:
    exec_result = state.get("execution_result", {})
    if not exec_result or exec_result.get("type") != "dataframe":
        return {"chart_config": None}

    raw_columns = exec_result.get("columns", [])
    data = exec_result.get("data", [])
    if len(raw_columns) < 1 or not data:
        return {"chart_config": None}

    # Filter out internal index columns
    columns = [c for c in raw_columns if c.lower() not in ["index", "level_0"]]
    if not columns:
        return {"chart_config": None}

    # Check whether generating a chart is appropriate for this query
    if not should_generate_visualization(state, columns, data):
        return {"chart_config": None}

    palette = ["#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#3b82f6", "#14b8a6", "#eab308", "#ef4444"]

    # 1. Classify columns into numeric metric columns vs categorical/dimension columns
    # Exclude ID columns from being chosen as primary plotting dimensions
    numeric_metric_cols = []
    dimension_cols = []
    id_cols = []

    for c in columns:
        c_lower = c.lower()
        is_id = c_lower.endswith("id") or c_lower == "id" or "uuid" in c_lower or "_id" in c_lower
        val_sample = [d.get(c) for d in data if d.get(c) is not None]
        if not is_id and val_sample and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in val_sample[:25]):
            numeric_metric_cols.append(c)
        elif is_id:
            id_cols.append(c)
        else:
            dimension_cols.append(c)

    # If no non-ID dimension exists, fall back to id_cols
    if not dimension_cols and id_cols:
        dimension_cols = id_cols

    # Case for single-row KPI aggregate
    if len(data) == 1 and numeric_metric_cols:
        m_col = numeric_metric_cols[0]
        val = data[0].get(m_col, 0)
        formatted_val = f"${val:,.2f}" if any(k in m_col.lower() for k in ["sales", "profit", "revenue", "price", "cost"]) else f"{val:,.2f}"
        traces = [{
            "type": "indicator",
            "mode": "number",
            "value": val,
            "title": {"text": f"Total {m_col}", "font": {"size": 16, "color": "#94a3b8"}},
            "number": {"font": {"size": 42, "color": "#818cf8"}, "valueformat": ",.2f"}
        }]
        layout = {
            "template": "plotly_dark",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "margin": {"l": 20, "r": 20, "t": 30, "b": 20},
            "height": 180
        }
        return {
            "chart_config": {
                "type": "indicator",
                "spec": {"data": traces, "layout": layout}
            }
        }

    # If there are no genuine numeric metric columns or no dimensions, skip visualization
    if not numeric_metric_cols or not dimension_cols:
        return {"chart_config": None}

    # Prioritize queried metric(s) first
    intent_m = (state.get("query_intent") or {}).get("metric")
    intent_ms = (state.get("query_intent") or {}).get("metrics") or ([intent_m] if intent_m else [])
    valid_intent_ms = [m for m in intent_ms if m and m in numeric_metric_cols]
    if valid_intent_ms:
        numeric_metric_cols.sort(key=lambda m: 0 if m in valid_intent_ms else 1)

    # Prioritize varying dimensions (not fixed by filters) and genuine categorical dimensions
    filters_dict = (state.get("query_intent") or {}).get("filters") or {}
    fixed_filter_keys = set(filters_dict.keys())
    dimension_cols.sort(key=lambda d: 2 if d in fixed_filter_keys else (1 if any(k in d.lower() for k in ["date", "time", "order", "id"]) else 0))

    # -------------------------------------------------------------
    # CASE A: 2 Dimensions + 1 Metric (e.g. Region, Category, Sales)
    # Grouped Bar Chart by secondary dimension
    # -------------------------------------------------------------
    if len(dimension_cols) == 2 and len(numeric_metric_cols) == 1:
        dim1, dim2 = dimension_cols[0], dimension_cols[1]
        m_col = numeric_metric_cols[0]

        # Extract unique ordered values for both dimensions
        unique_dim1 = []
        unique_dim2 = []
        for d in data:
            v1 = d.get(dim1)
            v2 = d.get(dim2)
            if v1 is not None and v1 not in unique_dim1:
                unique_dim1.append(v1)
            if v2 is not None and v2 not in unique_dim2:
                unique_dim2.append(v2)

        # If dim2 has <= 10 unique categories, build standard grouped bar chart traces
        if len(unique_dim2) <= 10:
            val_map = {}
            for d in data:
                val_map[(d.get(dim1), d.get(dim2))] = d.get(m_col)

            traces = []
            for idx, d2_val in enumerate(unique_dim2):
                y_vals = [val_map.get((d1_val, d2_val), 0) for d1_val in unique_dim1]
                color = palette[idx % len(palette)]
                traces.append({
                    "name": str(d2_val),
                    "x": [str(x) for x in unique_dim1],
                    "y": y_vals,
                    "type": "bar",
                    "marker": {"color": color}
                })

            layout = {
                "title": f"{m_col} by {dim1} and {dim2}",
                "xaxis": {"title": dim1},
                "yaxis": {"title": m_col},
                "barmode": "group",
                "template": "plotly_dark",
                "margin": {"l": 40, "r": 40, "t": 40, "b": 50},
                "legend": {"title": {"text": dim2}, "orientation": "h", "y": -0.2}
            }

            return {
                "chart_config": {
                    "type": "bar",
                    "spec": {"data": traces, "layout": layout}
                }
            }
        else:
            subset = data[:40]
            x_vals = [f"{d.get(dim1)} - {d.get(dim2)}" for d in subset]
            y_vals = [d.get(m_col) for d in subset]
            trace = {
                "name": m_col,
                "x": x_vals,
                "y": y_vals,
                "type": "bar",
                "marker": {"color": palette[0]}
            }
            layout = {
                "title": f"{m_col} by {dim1} & {dim2}",
                "xaxis": {"title": f"{dim1} & {dim2}"},
                "yaxis": {"title": m_col},
                "template": "plotly_dark",
                "margin": {"l": 40, "r": 40, "t": 40, "b": 60}
            }
            return {
                "chart_config": {
                    "type": "bar",
                    "spec": {"data": [trace], "layout": layout}
                }
            }

    # -------------------------------------------------------------
    # CASE B: 2+ Dimensions + Multiple Metrics
    # (e.g. Region, Category, Sales, Profit)
    # Composite category labels on x-axis, grouped metric bars
    # -------------------------------------------------------------
    if len(dimension_cols) >= 2 and len(numeric_metric_cols) >= 2:
        subset = data[:30]
        x_vals = [" - ".join(str(d.get(c, "")) for c in dimension_cols) for d in subset]
        traces = []
        for idx, m_col in enumerate(numeric_metric_cols[:4]):
            y_vals = [d.get(m_col) for d in subset]
            color = palette[idx % len(palette)]
            traces.append({
                "name": m_col,
                "x": x_vals,
                "y": y_vals,
                "type": "bar",
                "marker": {"color": color}
            })
        dim_title = " & ".join(dimension_cols[:2])
        metric_title = ", ".join(numeric_metric_cols[:3])
        layout = {
            "title": f"{metric_title} by {dim_title}",
            "xaxis": {"title": dim_title},
            "yaxis": {"title": "Value"},
            "barmode": "group",
            "template": "plotly_dark",
            "margin": {"l": 40, "r": 40, "t": 40, "b": 60},
            "legend": {"orientation": "h", "y": -0.2}
        }
        return {
            "chart_config": {
                "type": "bar",
                "spec": {"data": traces, "layout": layout}
            }
        }

    # -------------------------------------------------------------
    # CASE C: 3+ Dimensions + 1 Metric
    # Composite hierarchy labels on x-axis
    # -------------------------------------------------------------
    if len(dimension_cols) >= 3 and len(numeric_metric_cols) == 1:
        m_col = numeric_metric_cols[0]
        subset = data[:30]
        x_vals = [" / ".join(str(d.get(c, "")) for c in dimension_cols) for d in subset]
        trace = {
            "name": m_col,
            "x": x_vals,
            "y": [d.get(m_col) for d in subset],
            "type": "bar",
            "marker": {"color": palette[0]}
        }
        layout = {
            "title": f"{m_col} by {' & '.join(dimension_cols[:3])}",
            "xaxis": {"title": " / ".join(dimension_cols[:3])},
            "yaxis": {"title": m_col},
            "template": "plotly_dark",
            "margin": {"l": 40, "r": 40, "t": 40, "b": 60}
        }
        return {
            "chart_config": {
                "type": "bar",
                "spec": {"data": [trace], "layout": layout}
            }
        }

    # -------------------------------------------------------------
    # CASE D: 1 Dimension + 1 or More Metrics (Standard Case)
    # Single categorical or date dimension
    # -------------------------------------------------------------
    dim_col = dimension_cols[0]
    is_date = any(k in dim_col.lower() for k in ["date", "time", "month", "year", "quarter", "day"])
    chart_type = "line" if is_date else "bar"

    x_vals = [d.get(dim_col) for d in data]
    traces = []
    for idx, m_col in enumerate(numeric_metric_cols[:4]):
        y_vals = [d.get(m_col) for d in data]
        color = palette[idx % len(palette)]
        trace = {
            "name": m_col,
            "x": x_vals,
            "y": y_vals,
            "type": "scatter" if chart_type == "line" else "bar",
            "marker": {"color": color}
        }
        if chart_type == "line":
            trace["mode"] = "lines+markers"
            trace["line"] = {"width": 2.5}
        traces.append(trace)

    metrics_str = ", ".join(numeric_metric_cols[:4])
    layout = {
        "title": f"{metrics_str} by {dim_col}",
        "xaxis": {"title": dim_col},
        "yaxis": {"title": numeric_metric_cols[0] if len(numeric_metric_cols) == 1 else "Value"},
        "template": "plotly_dark",
        "margin": {"l": 40, "r": 40, "t": 40, "b": 40},
        "legend": {"orientation": "h", "y": -0.2} if len(traces) > 1 else {"visible": False}
    }
    if chart_type == "bar" and len(traces) > 1:
        layout["barmode"] = "group"

    return {
        "chart_config": {
            "type": chart_type,
            "spec": {
                "data": traces,
                "layout": layout
            }
        }
    }
