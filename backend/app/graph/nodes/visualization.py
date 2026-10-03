from typing import Dict, Any, List
from app.graph.state import AnalysisState

def should_generate_visualization(state: AnalysisState, columns: List[str], data: List[Dict[str, Any]]) -> bool:
    """
    Determines whether generating a chart is analytically meaningful.
    Charts are generated for aggregations, groupings, comparisons, trends,
    or whenever an analytical metric/dimension breakdown is present.
    Detail/raw table queries (e.g. 'show raw records', 'details of order 123')
    must NOT generate a chart unless explicitly requested.
    """
    user_query = (state.get("user_query") or "").lower().strip()
    query_intent = state.get("query_intent") or {}
    intent_type = (query_intent.get("intent") or "").lower().strip()
    group_by = query_intent.get("group_by") or []

    # 1. User explicitly requested a chart/plot/visual
    chart_keywords = ["chart", "plot", "graph", "visualize", "visualization", "histogram", "pie", "trend", "scatter", "bar"]
    user_explicitly_wants_chart = any(k in user_query for k in chart_keywords)

    # 2. Detail / record lookup queries: NEVER generate chart unless explicitly requested
    detail_phrases = [
        "give me details", "give me the details", "show me details", "show details",
        "detail of", "details of", "list all rows", "list all records", "show records",
        "show rows", "raw data", "raw records", "dump data"
    ]
    is_detail_query = any(k in user_query for k in detail_phrases)
    if is_detail_query and not user_explicitly_wants_chart:
        return False

    # 3. If intent is filtering / lookup / detail without any group_by, do not generate chart
    if intent_type in ["filtering", "lookup", "detail", "records", "search"] and not group_by and not user_explicitly_wants_chart:
        return False

    # 4. Result size check: empty cannot be visualized
    if len(data) == 0:
        return False

    # 5. Analytical intents or grouping always warrant a visualization
    analytical_intents = ["aggregation", "grouping", "comparison", "trend", "distribution", "ranking"]
    if intent_type in analytical_intents or group_by or any(w in user_query for w in ["average", "avg", "mean", "per", "by", "total", "sum", "count", "distribution", "highest", "lowest", "top"]):
        return True

    return True

def is_col_id(name: str) -> bool:
    n = name.lower()
    return n.endswith("_id") or n.endswith("id") or n == "id" or "uuid" in n or n.endswith("_no") or "code" in n

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
    numeric_metric_cols = []
    dimension_cols = []
    id_cols = []

    for c in columns:
        val_sample = [d.get(c) for d in data if d.get(c) is not None]
        
        is_num = False
        if val_sample:
            try:
                for v in val_sample[:25]:
                    if isinstance(v, bool):
                        raise TypeError
                    float(v)
                is_num = True
            except (ValueError, TypeError):
                is_num = False

        if not is_col_id(c) and is_num:
            numeric_metric_cols.append(c)
        elif is_col_id(c):
            id_cols.append(c)
        else:
            dimension_cols.append(c)

    # If no non-ID dimension exists, fall back to id_cols
    if not dimension_cols and id_cols:
        dimension_cols = [id_cols[0]]

    # Case for single-row KPI aggregate
    if len(data) == 1 and numeric_metric_cols:
        m_col = numeric_metric_cols[0]
        val = data[0].get(m_col, 0)
        try:
            val_flt = float(val)
            formatted_val = f"${val_flt:,.2f}" if any(k in m_col.lower() for k in ["sales", "profit", "revenue", "price", "cost"]) else f"{val_flt:,.2f}"
        except Exception:
            formatted_val = str(val)
            val_flt = 0.0

        traces = [{
            "type": "indicator",
            "mode": "number",
            "value": val_flt,
            "title": {"text": f"{m_col}", "font": {"size": 16, "color": "#475569"}},
            "number": {"font": {"size": 42, "color": "#4f46e5"}, "valueformat": ",.2f"}
        }]
        layout = {
            "template": "plotly_white",
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
                "template": "plotly_white",
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
            subset = data[:30]
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
                "template": "plotly_white",
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
    # -------------------------------------------------------------
    if len(dimension_cols) >= 2 and len(numeric_metric_cols) >= 2:
        subset = data[:25]
        x_vals = [" - ".join(str(d.get(c, "")) for c in dimension_cols[:2]) for d in subset]
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
            "template": "plotly_white",
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
    # -------------------------------------------------------------
    if len(dimension_cols) >= 3 and len(numeric_metric_cols) == 1:
        m_col = numeric_metric_cols[0]
        subset = data[:25]
        x_vals = [" / ".join(str(d.get(c, "")) for c in dimension_cols[:3]) for d in subset]
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
            "template": "plotly_white",
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
    # Includes entity breakdowns like Customer, Product, etc.
    # -------------------------------------------------------------
    dim_col = dimension_cols[0]
    is_date = any(k in dim_col.lower() for k in ["date", "time", "month", "year", "quarter", "day"])
    chart_type = "line" if is_date else "bar"

    # Subset to Top 20 for non-date charts to ensure beautiful, uncluttered visualization
    is_subset = False
    chart_data = data
    if len(data) > 20 and not is_date:
        chart_data = data[:20]
        is_subset = True

    x_vals = [str(d.get(dim_col, "")) for d in chart_data]
    traces = []
    for idx, m_col in enumerate(numeric_metric_cols[:4]):
        y_vals = [d.get(m_col) for d in chart_data]
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
        
        # If an ID column exists and is not dim_col, add to hover text
        if id_cols and id_cols[0] != dim_col:
            id_col_name = id_cols[0]
            trace["hovertext"] = [
                f"{id_col_name}: {d.get(id_col_name)}<br>{dim_col}: {d.get(dim_col)}<br>{m_col}: {d.get(m_col)}"
                for d in chart_data
            ]
            trace["hoverinfo"] = "text"

        traces.append(trace)

    title_prefix = "Top 20 " if is_subset else ""
    metrics_str = ", ".join(numeric_metric_cols[:4])
    layout = {
        "title": f"{title_prefix}{metrics_str} by {dim_col}",
        "xaxis": {"title": dim_col},
        "yaxis": {"title": numeric_metric_cols[0] if len(numeric_metric_cols) == 1 else "Value"},
        "template": "plotly_white",
        "margin": {"l": 40, "r": 40, "t": 40, "b": 60},
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
