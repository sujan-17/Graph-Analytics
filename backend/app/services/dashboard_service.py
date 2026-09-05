import pandas as pd
import numpy as np
from typing import Dict, Any, List

class DashboardService:
    @staticmethod
    def generate_initial_dashboard(file_path: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates automatic initial KPI overview cards and Plotly chart specifications.
        """
        df = pd.read_csv(file_path)
        kpis = []
        charts = []

        # 1. KPI Overview Cards
        kpi_candidates = profile.get("kpi_candidates", [])
        for k in kpi_candidates[:4]:
            col = k["column"]
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                total_val = float(df[col].sum())
                avg_val = float(df[col].mean())
                
                # Format friendly display
                formatted_val = f"${total_val:,.2f}" if any(c in col.lower() for c in ["revenue", "sales", "profit", "cost", "price", "amount"]) else f"{total_val:,.0f}"
                
                kpis.append({
                    "title": f"Total {col}",
                    "value": formatted_val,
                    "subtext": f"Average: {avg_val:,.2f}",
                    "column": col
                })

        if not kpis:
            kpis.append({
                "title": "Total Rows",
                "value": f"{len(df):,}",
                "subtext": f"Columns: {len(df.columns)}",
                "column": "rows"
            })

        # 2. Charts Generation
        date_cols = profile.get("semantic_summary", {}).get("time_dimensions", [])
        numeric_metrics = profile.get("semantic_summary", {}).get("primary_metrics", [])
        
        if not numeric_metrics:
            numeric_metrics = df.select_dtypes(include=[np.number]).columns.tolist()

        # Date trend chart
        if date_cols and numeric_metrics:
            try:
                date_col = date_cols[0]
                metric_col = numeric_metrics[0]
                
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                clean_df = df.dropna(subset=[date_col])
                if len(clean_df) > 0:
                    try:
                        trend_df = clean_df.groupby(pd.Grouper(key=date_col, freq='ME'))[metric_col].sum().reset_index()
                    except Exception:
                        trend_df = clean_df.groupby(pd.Grouper(key=date_col, freq='MS'))[metric_col].sum().reset_index()

                    trend_df = trend_df.sort_values(date_col)
                    x_vals = trend_df[date_col].dt.strftime('%Y-%m').tolist()
                    y_vals = trend_df[metric_col].round(2).tolist()
                    
                    charts.append({
                        "id": "trend_chart",
                        "title": f"{metric_col} Trend Over Time",
                        "type": "line",
                        "spec": {
                            "data": [{
                                "x": x_vals,
                                "y": y_vals,
                                "type": "scatter",
                                "mode": "lines+markers",
                                "marker": {"color": "#6366f1"},
                                "line": {"width": 3}
                            }],
                            "layout": {
                                "title": f"Monthly {metric_col}",
                                "xaxis": {"title": date_col},
                                "yaxis": {"title": metric_col},
                                "template": "plotly_dark",
                                "margin": {"l": 40, "r": 40, "t": 40, "b": 40}
                            }
                        }
                    })
            except Exception as e:
                print(f"Date trend chart generation skipped: {e}")

        # Category Bar Chart
        cat_cols = profile.get("semantic_summary", {}).get("dimensions", [])
        if cat_cols and numeric_metrics:
            try:
                cat_col = cat_cols[0]
                metric_col = numeric_metrics[0]
                
                bar_df = df.groupby(cat_col)[metric_col].sum().reset_index().sort_values(metric_col, ascending=False).head(10)
                
                charts.append({
                    "id": "category_chart",
                    "title": f"{metric_col} by {cat_col}",
                    "type": "bar",
                    "spec": {
                        "data": [{
                            "x": bar_df[cat_col].astype(str).tolist(),
                            "y": bar_df[metric_col].round(2).tolist(),
                            "type": "bar",
                            "marker": {"color": "#3b82f6"}
                        }],
                        "layout": {
                            "title": f"Top {cat_col} by {metric_col}",
                            "xaxis": {"title": cat_col},
                            "yaxis": {"title": metric_col},
                            "template": "plotly_dark",
                            "margin": {"l": 40, "r": 40, "t": 40, "b": 40}
                        }
                    }
                })
            except Exception as e:
                print(f"Category bar chart generation skipped: {e}")

        return {
            "kpis": kpis,
            "charts": charts
        }

dashboard_service = DashboardService()
