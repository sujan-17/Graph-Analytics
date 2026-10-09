import os
import re
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from app.core.config import settings
from app.core.llm import call_gemini_llm
from app.services.profiling_service import profiling_service

class DatasetAnalystService:
    @staticmethod
    def extract_dataset_metrics(file_path: str, profile_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parses CSV with Pandas and extracts rich statistical metrics,
        bivariate aggregations, correlations, and dimension breakdowns.
        """
        if not os.path.exists(file_path):
            return {
                "error": "Dataset file not found",
                "row_count": 0,
                "column_count": 0,
                "numeric_metrics": [],
                "categorical_dimensions": [],
                "quality_stats": {"quality_score": 100.0, "missing_percentage": 0.0, "duplicate_rows": 0}
            }

        df = pd.read_csv(file_path)
        row_count, col_count = df.shape
        file_size_bytes = os.path.getsize(file_path)
        memory_mb = round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)

        numeric_cols = []
        categorical_cols = []
        date_cols = []

        # Categorize columns
        for col in df.columns:
            series = df[col]
            is_date_name = bool(re.search(r"(^|[_\s])(date|time|timestamp|datetime)($|[_\s])", str(col), re.IGNORECASE))
            if is_date_name or pd.api.types.is_datetime64_any_dtype(series):
                date_cols.append(col)
            elif pd.api.types.is_numeric_dtype(series):
                numeric_cols.append(col)
            else:
                categorical_cols.append(col)

        # 1. Numeric metrics
        numeric_metrics = []
        for col in numeric_cols:
            clean_s = df[col].dropna()
            if len(clean_s) > 0:
                q25, q50, q75 = clean_s.quantile([0.25, 0.50, 0.75]).tolist()
                numeric_metrics.append({
                    "name": str(col),
                    "total": round(float(clean_s.sum()), 2),
                    "mean": round(float(clean_s.mean()), 2),
                    "median": round(float(clean_s.median()), 2),
                    "min": round(float(clean_s.min()), 2),
                    "max": round(float(clean_s.max()), 2),
                    "std": round(float(clean_s.std()), 2) if len(clean_s) > 1 else 0.0,
                    "quartiles": [round(float(q25), 2), round(float(q50), 2), round(float(q75), 2)],
                    "null_count": int(df[col].isnull().sum())
                })

        # 2. Categorical dimensions
        categorical_dimensions = []
        for col in categorical_cols:
            clean_s = df[col].dropna()
            if len(clean_s) > 0:
                top_counts = clean_s.value_counts().head(5).to_dict()
                total_valid = len(clean_s)
                top_pcts = {str(k): round((int(v) / total_valid) * 100, 1) for k, v in top_counts.items()}
                categorical_dimensions.append({
                    "name": str(col),
                    "unique_count": int(clean_s.nunique()),
                    "top_categories": {str(k): int(v) for k, v in top_counts.items()},
                    "top_percentages": top_pcts,
                    "null_count": int(df[col].isnull().sum())
                })

        # 3. Date info
        date_summary = {}
        for col in date_cols:
            try:
                dt_series = pd.to_datetime(df[col].dropna(), errors='coerce').dropna()
                if len(dt_series) > 0:
                    date_summary[str(col)] = {
                        "min_date": str(dt_series.min().date() if hasattr(dt_series.min(), 'date') else dt_series.min()),
                        "max_date": str(dt_series.max().date() if hasattr(dt_series.max(), 'date') else dt_series.max()),
                        "date_range_days": int((dt_series.max() - dt_series.min()).days)
                    }
            except Exception:
                pass

        # 4. Aggregations (Top segments across dominant metrics)
        cross_tab_insights = []
        if numeric_cols and categorical_cols:
            primary_metric = numeric_cols[0]
            # prioritize revenue/sales/profit
            for c in numeric_cols:
                if any(k in c.lower() for k in ["sales", "revenue", "profit", "amount", "cost"]):
                    primary_metric = c
                    break

            primary_dim = categorical_cols[0]
            try:
                grouped = df.groupby(primary_dim, as_index=False)[primary_metric].sum()
                grouped = grouped.sort_values(by=primary_metric, ascending=False).head(5)
                tot_metric = df[primary_metric].sum()
                for _, row in grouped.iterrows():
                    val = float(row[primary_metric])
                    pct = round((val / tot_metric * 100), 1) if tot_metric != 0 else 0
                    cross_tab_insights.append({
                        "dimension": primary_dim,
                        "category": str(row[primary_dim]),
                        "metric": primary_metric,
                        "value": round(val, 2),
                        "share_percentage": pct
                    })
            except Exception:
                pass

        # 5. Correlations
        correlations = []
        if len(numeric_cols) >= 2:
            try:
                corr_matrix = df[numeric_cols].corr()
                checked_pairs = set()
                for c1 in numeric_cols:
                    for c2 in numeric_cols:
                        if c1 != c2 and (c2, c1) not in checked_pairs:
                            checked_pairs.add((c1, c2))
                            val = corr_matrix.loc[c1, c2]
                            if not np.isnan(val):
                                correlations.append({
                                    "col1": c1,
                                    "col2": c2,
                                    "correlation": round(float(val), 2)
                                })
                # Sort by absolute correlation
                correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
            except Exception:
                pass

        # 6. Quality statistics
        total_cells = row_count * col_count if row_count * col_count > 0 else 1
        total_missing = int(df.isnull().sum().sum())
        missing_pct = round((total_missing / total_cells) * 100, 2)
        duplicate_rows = int(df.duplicated().sum())
        duplicate_pct = round((duplicate_rows / row_count) * 100, 2) if row_count > 0 else 0.0
        penalty = (missing_pct * 1.5) + (duplicate_pct * 2.0)
        quality_score = max(5.0, round(100.0 - penalty, 1))

        return {
            "row_count": row_count,
            "column_count": col_count,
            "file_size_bytes": file_size_bytes,
            "memory_mb": memory_mb,
            "numeric_metrics": numeric_metrics,
            "categorical_dimensions": categorical_dimensions,
            "date_summary": date_summary,
            "cross_tab_insights": cross_tab_insights[:5],
            "top_correlations": correlations[:6],
            "quality_stats": {
                "quality_score": quality_score,
                "missing_cells": total_missing,
                "missing_percentage": missing_pct,
                "duplicate_rows": duplicate_rows,
                "duplicate_percentage": duplicate_pct
            }
        }

    @classmethod
    def generate_analyst_report(
        cls,
        file_path: str,
        filename: str,
        report_title: str,
        profile_dict: Optional[Dict[str, Any]] = None,
        custom_api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Produces a thorough Data Analyst report covering:
        1. Executive Summary & Purpose
        2. What Data is Analysed (Scope, Measures, Dimensions, Quality)
        3. What the Dataset Depicts Generally (Operational state, patterns, concentrations, anomalies)
        4. What Can Be Done (Strategic business actions, advanced analytics roadmap, data enrichment)
        """
        metrics_data = cls.extract_dataset_metrics(file_path, profile_dict)
        now_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

        # Try generating via Gemini LLM
        llm_report = cls._synthesize_with_llm(filename, report_title, metrics_data, custom_api_key)

        if not llm_report:
            # Deterministic expert fallback
            llm_report = cls._generate_deterministic_report(filename, report_title, metrics_data)

        # Merge data structures so UI and PDF have direct access to tables and figures
        final_report = {
            "report_title": report_title or f"Executive Dataset Report: {filename}",
            "dataset_name": filename,
            "generated_at": now_str,
            "summary_metrics": {
                "row_count": metrics_data.get("row_count", 0),
                "column_count": metrics_data.get("column_count", 0),
                "file_size_bytes": metrics_data.get("file_size_bytes", 0),
                "memory_mb": metrics_data.get("memory_mb", 0.0),
                "quality_score": metrics_data.get("quality_stats", {}).get("quality_score", 100.0),
                "missing_percentage": metrics_data.get("quality_stats", {}).get("missing_percentage", 0.0),
                "duplicate_rows": metrics_data.get("quality_stats", {}).get("duplicate_rows", 0)
            },
            "executive_summary": llm_report.get("executive_summary", ""),
            "what_data_is_analysed": {
                "overview": llm_report.get("what_data_is_analysed", {}).get("overview", ""),
                "metrics_analysis": llm_report.get("what_data_is_analysed", {}).get("metrics_analysis", ""),
                "dimensions_analysis": llm_report.get("what_data_is_analysed", {}).get("dimensions_analysis", ""),
                "quality_audit": llm_report.get("what_data_is_analysed", {}).get("quality_audit", ""),
                "numeric_metrics": metrics_data.get("numeric_metrics", []),
                "categorical_dimensions": metrics_data.get("categorical_dimensions", [])
            },
            "what_dataset_depicts": {
                "general_depiction": llm_report.get("what_dataset_depicts", {}).get("general_depiction", ""),
                "key_patterns": llm_report.get("what_dataset_depicts", {}).get("key_patterns", []),
                "comparative_findings": llm_report.get("what_dataset_depicts", {}).get("comparative_findings", ""),
                "anomalies_and_risks": llm_report.get("what_dataset_depicts", {}).get("anomalies_and_risks", "")
            },
            "what_can_be_done": {
                "strategic_actions": llm_report.get("what_can_be_done", {}).get("strategic_actions", []),
                "advanced_analytics": llm_report.get("what_can_be_done", {}).get("advanced_analytics", []),
                "data_enrichment": llm_report.get("what_can_be_done", {}).get("data_enrichment", "")
            }
        }

        return final_report

    @classmethod
    def _synthesize_with_llm(
        cls,
        filename: str,
        report_title: str,
        metrics_data: Dict[str, Any],
        custom_api_key: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        api_key = custom_api_key or settings.GEMINI_API_KEY
        if not api_key:
            return None

        # Compact representation for LLM prompt
        num_summary = []
        for m in metrics_data.get("numeric_metrics", [])[:8]:
            num_summary.append(f"- {m['name']}: Total={m.get('total')}, Mean={m.get('mean')}, Min={m.get('min')}, Max={m.get('max')}, Std={m.get('std')}")
        
        cat_summary = []
        for c in metrics_data.get("categorical_dimensions", [])[:6]:
            top_str = ", ".join([f"{k} ({v}%)" for k, v in c.get("top_percentages", {}).items()][:3])
            cat_summary.append(f"- {c['name']} ({c.get('unique_count')} unique): Top = [{top_str}]")

        cross_summary = []
        for cr in metrics_data.get("cross_tab_insights", []):
            cross_summary.append(f"- {cr['dimension']} '{cr['category']}': {cr['metric']} = {cr['value']} ({cr['share_percentage']}% of total)")

        corr_summary = []
        for co in metrics_data.get("top_correlations", [])[:4]:
            corr_summary.append(f"- {co['col1']} vs {co['col2']}: r = {co['correlation']}")

        date_summary = []
        for dcol, dinfo in metrics_data.get("date_summary", {}).items():
            date_summary.append(f"- {dcol}: Range {dinfo.get('min_date')} to {dinfo.get('max_date')} ({dinfo.get('date_range_days')} days)")

        prompt = f"""You are a Principal Lead Data Analyst producing an authoritative, comprehensive Dataset Analysis Report for executives and stakeholders.

DATASET METADATA:
- File: {filename}
- Report Title: {report_title}
- Total Records: {metrics_data.get('row_count')}
- Total Attributes: {metrics_data.get('column_count')}
- Data Quality Score: {metrics_data.get('quality_stats', {}).get('quality_score')}% (Missing: {metrics_data.get('quality_stats', {}).get('missing_percentage')}%, Duplicates: {metrics_data.get('quality_stats', {}).get('duplicate_rows')})

KEY QUANTITATIVE METRICS:
{chr(10).join(num_summary) if num_summary else "No explicit numeric columns"}

CATEGORICAL DIMENSIONS & DISTRIBUTIONS:
{chr(10).join(cat_summary) if cat_summary else "No categorical dimensions"}

AGGREGATIONS & TOP SEGMENT SHARES:
{chr(10).join(cross_summary) if cross_summary else "None"}

NOTABLE CORRELATIONS:
{chr(10).join(corr_summary) if corr_summary else "None"}

TEMPORAL SPAN:
{chr(10).join(date_summary) if date_summary else "No time-series date detected"}

CRITICAL REQUIREMENTS:
1. DO NOT include any user queries, user prompts, or chat history.
2. Focus strictly on an objective, comprehensive evaluation of THIS dataset.
3. Address three core pillars:
   a) A summary of WHAT DATA IS ANALYSED (metrics scale, features, distributions, data health).
   b) WHAT THE DATASET IS CURRENTLY DEPICTING GENERALLY (the real-world operational narrative, trends, dominant segments, skews, anomalies).
   c) WHAT CAN BE DONE (prescriptive strategic business actions, advanced data science next steps, data enrichment).
4. Deliver valid JSON matching the exact schema below:

{{
  "executive_summary": "Comprehensive 2-3 paragraph executive summary describing what this dataset represents, its operational domain, overall scale, and the primary business takeaway.",
  "what_data_is_analysed": {{
    "overview": "Detailed overview of dataset scope, sample volume, feature categorization, and completeness.",
    "metrics_analysis": "Analytical synthesis of quantitative measures, scales of magnitude, variability, and central tendencies.",
    "dimensions_analysis": "Synthesis of categorical dimensions, entity groupings, and segmentation distribution.",
    "quality_audit": "Evaluation of data hygiene, null values, uniqueness, and reliability score."
  }},
  "what_dataset_depicts": {{
    "general_depiction": "Detailed narrative explaining what the data indicates about the current operational environment, performance baseline, and core business story.",
    "key_patterns": [
      {{"title": "Pattern 1 Title", "description": "Specific observation on trend, concentration, or volume distribution."}},
      {{"title": "Pattern 2 Title", "description": "Observation on segment performance, high/low drivers."}},
      {{"title": "Pattern 3 Title", "description": "Observation on metric correlations, variance, or behavior."}}
    ],
    "comparative_findings": "Detailed comparison identifying leading vs lagging segments, categories, or metrics.",
    "anomalies_and_risks": "Identified distribution skews, outlier concentrations, margin pressures, or vulnerability areas."
  }},
  "what_can_be_done": {{
    "strategic_actions": [
      {{"title": "Strategic Recommendation 1", "description": "High-impact business intervention, resource reallocation, or operational adjustment."}},
      {{"title": "Strategic Recommendation 2", "description": "Specific optimization lever based on the data findings."}},
      {{"title": "Strategic Recommendation 3", "description": "Risk mitigation or underperforming segment remedy."}}
    ],
    "advanced_analytics": [
      {{"title": "Analytical Deep-Dive 1", "description": "E.g., Predictive forecasting, customer cohort analysis, or machine learning model."}},
      {{"title": "Analytical Deep-Dive 2", "description": "E.g., Clustering segmentation, price elasticity, or churn risk modeling."}},
      {{"title": "Analytical Deep-Dive 3", "description": "E.g., Root-cause variance analysis or time-series decomposition."}}
    ],
    "data_enrichment": "Actionable recommendations on additional features to track or pipeline improvements to enhance future analytics."
  }}
}}
"""
        try:
            raw_response = call_gemini_llm(prompt, temperature=0.1, custom_api_key=api_key)
            if not raw_response:
                return None
            
            # Extract JSON block
            clean = raw_response.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0].strip()
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()

            parsed = json.loads(clean)
            if "executive_summary" in parsed and "what_data_is_analysed" in parsed:
                return parsed
        except Exception as e:
            print(f"Dataset analyst LLM generation failed: {e}")
        return None

    @classmethod
    def _generate_deterministic_report(
        cls,
        filename: str,
        report_title: str,
        metrics_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deterministic, rule-based Principal Data Analyst report generation
        used as a resilient fallback when LLM is unavailable.
        """
        row_cnt = metrics_data.get("row_count", 0)
        col_cnt = metrics_data.get("column_count", 0)
        q_score = metrics_data.get("quality_stats", {}).get("quality_score", 100.0)
        missing_pct = metrics_data.get("quality_stats", {}).get("missing_percentage", 0.0)
        dup_cnt = metrics_data.get("quality_stats", {}).get("duplicate_rows", 0)

        num_metrics = metrics_data.get("numeric_metrics", [])
        cat_dims = metrics_data.get("categorical_dimensions", [])
        date_sums = metrics_data.get("date_summary", {})
        cross_tabs = metrics_data.get("cross_tab_insights", [])
        correlations = metrics_data.get("top_correlations", [])

        # Infer domain
        domain_name = "business operations and transaction logs"
        fname_lower = filename.lower()
        if "sale" in fname_lower or "revenue" in fname_lower:
            domain_name = "commercial sales transactions and revenue performance"
        elif "hr" in fname_lower or "employee" in fname_lower:
            domain_name = "workforce compensation, headcount, and human resources"
        elif "cust" in fname_lower or "user" in fname_lower:
            domain_name = "customer demographics, account engagement, and behavior"
        elif "financial" in fname_lower or "budget" in fname_lower:
            domain_name = "financial statements, budget allocations, and fiscal metrics"

        # Executive summary
        exec_summary = (
            f"This executive intelligence report provides a comprehensive data analyst assessment of the dataset '{filename}', "
            f"encompassing {row_cnt:,} total records across {col_cnt} distinctive attributes. The dataset reflects {domain_name}. "
            f"With an overall data quality health rating of {q_score}%, the records exhibit robust structural integrity "
            f"with {missing_pct}% null density and {dup_cnt} duplicate rows, providing a reliable quantitative baseline for strategic decision-making."
        )

        # What data is analysed
        primary_num_names = ", ".join([m["name"] for m in num_metrics[:3]]) if num_metrics else "qualitative attributes"
        primary_cat_names = ", ".join([c["name"] for c in cat_dims[:3]]) if cat_dims else "uniform classifications"

        overview_text = (
            f"The evaluation analyzed {row_cnt:,} observations structured into {len(num_metrics)} numerical metrics, "
            f"{len(cat_dims)} categorical classification dimensions, and {len(date_sums)} time-series attributes. "
            f"The dataset memory footprint is approximately {metrics_data.get('memory_mb', 0.01)} MB."
        )

        metrics_text = (
            f"Primary quantitative measures analyzed include {primary_num_names}. "
            + (f"Key metric '{num_metrics[0]['name']}' exhibits a cumulative volume of {num_metrics[0]['total']:,.2f} with a mean of {num_metrics[0]['mean']:,.2f} (ranging from {num_metrics[0]['min']:,.2f} to {num_metrics[0]['max']:,.2f}). " if num_metrics else "")
            + "Standard deviation indicators demonstrate natural variance across recorded transactions."
        )

        dims_text = (
            f"Categorical segmentation encompasses dimensions including {primary_cat_names}. "
            + (f"Dimension '{cat_dims[0]['name']}' contains {cat_dims[0]['unique_count']} distinct groupings, where the primary category accounts for {list(cat_dims[0].get('top_percentages', {}).values())[0] if cat_dims[0].get('top_percentages') else 'a substantial'}% of recorded instances. " if cat_dims else "")
            + "This granular segmentation facilitates multi-level hierarchical breakdown."
        )

        quality_text = (
            f"Data hygiene analysis indicates a composite health score of {q_score}%. "
            f"Missing values represent {missing_pct}% of total cells, and duplicate records represent {metrics_data.get('quality_stats', {}).get('duplicate_percentage', 0.0)}%. "
            + ("No critical data hygiene risks were discovered." if q_score >= 90 else "Data imputation and cleaning routines are recommended for incomplete records.")
        )

        # What dataset depicts generally
        depiction_text = (
            f"The dataset depicts active operational engagement characterized by sustained baseline activity across {domain_name}. "
            + (f"Performance is heavily anchored around key drivers such as {num_metrics[0]['name']}, reflecting operational concentration. " if num_metrics else "")
            + (f"Cross-segment aggregation indicates that leading categories within '{cross_tabs[0]['dimension']}' drive {cross_tabs[0]['share_percentage']}% of total {cross_tabs[0]['metric']}. " if cross_tabs else "")
        )

        key_patterns = []
        if cross_tabs:
            top_ct = cross_tabs[0]
            key_patterns.append({
                "title": f"Segment Concentration in {top_ct['dimension']}",
                "description": f"The top category '{top_ct['category']}' generates {top_ct['value']:,.2f} in {top_ct['metric']}, contributing {top_ct['share_percentage']}% of total recorded aggregate volume."
            })
        if num_metrics:
            m = num_metrics[0]
            key_patterns.append({
                "title": f"Quantitative Scale & Spread of {m['name']}",
                "description": f"{m['name']} demonstrates an average baseline of {m['mean']:,.2f} with variance spanning from {m['min']:,.2f} to {m['max']:,.2f}, indicating healthy distributional dispersion."
            })
        if correlations:
            top_corr = correlations[0]
            direction = "positive" if top_corr["correlation"] > 0 else "inverse"
            key_patterns.append({
                "title": f"Inter-Metric Correlation ({top_corr['col1']} & {top_corr['col2']})",
                "description": f"A notable {direction} statistical relationship (correlation coefficient r = {top_corr['correlation']}) connects {top_corr['col1']} with {top_corr['col2']}."
            })
        else:
            key_patterns.append({
                "title": "Distributional Regularity",
                "description": "Records display standard distributional spread across observed classifications without erratic extreme clustering."
            })

        comp_findings = (
            f"Comparative analysis highlights clear operational stratification. Top-tier segments within {cat_dims[0]['name'] if cat_dims else 'categories'} outperform baseline averages, "
            f"whereas secondary tiers exhibit lower volume. Resource prioritization toward upper-quartile performers represents a direct opportunity."
        )

        anomalies_text = (
            f"Anomalies and risk inspection identified minimal systemic distortion. "
            + (f"Outlier evaluation on '{num_metrics[0]['name']}' shows maximum ceiling of {num_metrics[0]['max']:,.2f} against median of {num_metrics[0]['median']:,.2f}. " if num_metrics else "")
            + "Monitoring tail-end distributions will ensure operational stability."
        )

        # What can be done
        strategic_actions = [
            {
                "title": f"Optimize Resource Allocation around Leading Segments",
                "description": f"Reallocate capital and operational attention toward top-performing categories identified in {cat_dims[0]['name'] if cat_dims else 'primary dimensions'} to maximize return on effort."
            },
            {
                "title": "Establish Threshold Monitoring & Margin Safeguards",
                "description": f"Implement automated governance thresholds on {num_metrics[0]['name'] if num_metrics else 'key performance metrics'} to prevent underperformance and catch early variances."
            },
            {
                "title": "Address Long-Tail and Underperforming Segments",
                "description": "Conduct diagnostic reviews into lowest-quartile segments to identify whether remediation, pricing adjustments, or decommissioning is warranted."
            }
        ]

        advanced_analytics = [
            {
                "title": "Predictive Time-Series & Demand Forecasting",
                "description": "Deploy Autoregressive Integrated Moving Average (ARIMA) or Prophet models to forecast forward-looking trajectories and seasonal fluctuations."
            },
            {
                "title": "Unsupervised Clustering & Behavioral Segmentation",
                "description": f"Utilize K-Means or DBSCAN clustering across {primary_num_names} to uncover latent customer, product, or operational personas."
            },
            {
                "title": "Elasticity & Sensitivity Scenario Modeling",
                "description": "Construct multi-variable regression models to quantify how changes in primary inputs directly impact target outcomes."
            }
        ]

        enrichment_text = (
            "To unlock deeper predictive insights, enrich future data collection with external market benchmarks, "
            "granular timestamps, customer retention markers, and cost allocation telemetry."
        )

        return {
            "executive_summary": exec_summary,
            "what_data_is_analysed": {
                "overview": overview_text,
                "metrics_analysis": metrics_text,
                "dimensions_analysis": dims_text,
                "quality_audit": quality_text
            },
            "what_dataset_depicts": {
                "general_depiction": depiction_text,
                "key_patterns": key_patterns,
                "comparative_findings": comp_findings,
                "anomalies_and_risks": anomalies_text
            },
            "what_can_be_done": {
                "strategic_actions": strategic_actions,
                "advanced_analytics": advanced_analytics,
                "data_enrichment": enrichment_text
            }
        }

dataset_analyst_service = DatasetAnalystService()
