import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List

class ProfilingService:
    @staticmethod
    def profile_dataset(file_path: str, filename: str) -> Dict[str, Any]:
        df = pd.read_csv(file_path)
        row_count, col_count = df.shape
        file_size_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        # Memory usage
        memory_usage_mb = round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)

        column_profiles = []
        numeric_cols = []
        categorical_cols = []
        date_cols = []

        total_cells = row_count * col_count if row_count * col_count > 0 else 1
        total_missing = 0

        for col in df.columns:
            series = df[col]
            null_cnt = int(series.isnull().sum())
            total_missing += null_cnt
            null_pct = round((null_cnt / row_count) * 100, 2) if row_count > 0 else 0.0
            unique_cnt = int(series.nunique())
            sample_vals = series.dropna().unique()[:5].tolist()
            # Convert non-serializable types in sample_vals
            sample_vals = [str(v) for v in sample_vals]

            col_info = {
                "name": col,
                "data_type": str(series.dtype),
                "unique_values": unique_cnt,
                "null_values": null_cnt,
                "null_percentage": null_pct,
                "example_values": sample_vals
            }

            # Check if numeric
            if pd.api.types.is_numeric_dtype(series):
                numeric_cols.append(col)
                clean_s = series.dropna()
                if len(clean_s) > 0:
                    q25, q50, q75 = clean_s.quantile([0.25, 0.50, 0.75]).tolist()
                    col_info["numeric_stats"] = {
                        "min": float(clean_s.min()),
                        "max": float(clean_s.max()),
                        "mean": round(float(clean_s.mean()), 2),
                        "median": round(float(clean_s.median()), 2),
                        "std": round(float(clean_s.std()), 2) if len(clean_s) > 1 else 0.0,
                        "quartiles": [round(q25, 2), round(q50, 2), round(q75, 2)]
                    }

            # Check if date/time
            is_date = False
            if "date" in col.lower() or "time" in col.lower() or pd.api.types.is_datetime64_any_dtype(series):
                try:
                    dt_series = pd.to_datetime(series.dropna())
                    if len(dt_series) > 0:
                        date_cols.append(col)
                        is_date = True
                        min_dt = str(dt_series.min())
                        max_dt = str(dt_series.max())
                        col_info["date_stats"] = {
                            "min_date": min_dt,
                            "max_date": max_dt,
                            "date_range_days": (dt_series.max() - dt_series.min()).days
                        }
                except Exception:
                    pass

            if not is_date and not pd.api.types.is_numeric_dtype(series):
                categorical_cols.append(col)
                top_counts = series.value_counts().head(5).to_dict()
                col_info["categorical_stats"] = {
                    "num_categories": unique_cnt,
                    "top_categories": {str(k): int(v) for k, v in top_counts.items()}
                }

            column_profiles.append(col_info)

        # Quality analysis
        duplicate_rows = int(df.duplicated().sum())
        duplicate_pct = round((duplicate_rows / row_count) * 100, 2) if row_count > 0 else 0.0
        missing_pct = round((total_missing / total_cells) * 100, 2)

        # Health score calculation (100 - penalties)
        penalty = (missing_pct * 1.5) + (duplicate_pct * 2.0)
        quality_score = max(5.0, round(100.0 - penalty, 1))

        recommendations = []
        if total_missing > 0:
            recommendations.append(f"Found {total_missing} missing values ({missing_pct}% of cells). Consider imputing or removing null rows.")
        if duplicate_rows > 0:
            recommendations.append(f"Found {duplicate_rows} duplicate records ({duplicate_pct}%). Review and clean duplicated entries.")
        if not date_cols:
            recommendations.append("No explicit date column detected. Time-series analysis will be limited.")
        if quality_score > 90:
            recommendations.append("Dataset health is high! Ready for deep stateful analysis.")

        # KPI Detection
        kpi_candidates = []
        kpi_keywords = ["revenue", "sales", "profit", "cost", "orders", "customer", "quantity", "margin", "amount", "total", "price", "spending"]
        for col in numeric_cols:
            col_lower = col.lower()
            confidence = "LOW"
            if any(k in col_lower for k in kpi_keywords):
                confidence = "HIGH"
            elif df[col].min() >= 0 and df[col].nunique() > 10:
                confidence = "MEDIUM"

            if confidence in ["HIGH", "MEDIUM"]:
                kpi_candidates.append({
                    "column": col,
                    "confidence": confidence,
                    "total": round(float(df[col].sum()), 2) if pd.api.types.is_numeric_dtype(df[col]) else None,
                    "mean": round(float(df[col].mean()), 2) if pd.api.types.is_numeric_dtype(df[col]) else None
                })

        # Automatic Semantic Summary
        semantic_summary = {
            "primary_metrics": [k["column"] for k in kpi_candidates if k["confidence"] == "HIGH"],
            "dimensions": categorical_cols[:5],
            "time_dimensions": date_cols,
            "potential_analyses": [
                f"Performance analysis grouped by {categorical_cols[0]}" if categorical_cols else "Distribution of numerical metrics",
                f"Trend analysis over time using {date_cols[0]}" if date_cols else "Correlation between numeric metrics",
                "Top product/category revenue ranking"
            ]
        }

        return {
            "basic_info": {
                "filename": filename,
                "row_count": row_count,
                "column_count": col_count,
                "memory_usage_mb": memory_usage_mb,
                "file_size_bytes": file_size_bytes
            },
            "columns": column_profiles,
            "data_quality": {
                "quality_score": quality_score,
                "missing_percentage": missing_pct,
                "duplicate_rows": duplicate_rows,
                "duplicate_percentage": duplicate_pct,
                "recommendations": recommendations
            },
            "kpi_candidates": kpi_candidates,
            "semantic_summary": semantic_summary
        }

profiling_service = ProfilingService()
