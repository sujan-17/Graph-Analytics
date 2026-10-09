export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
}

export interface Workspace {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Dataset {
  id: string;
  workspace_id: string;
  filename: string;
  row_count: number;
  column_count: number;
  created_at: string;
}

export interface ColumnInfo {
  name: string;
  data_type: string;
  unique_values: number;
  null_values: number;
  null_percentage: number;
  example_values: string[];
  numeric_stats?: {
    min: number;
    max: number;
    mean: number;
    median: number;
    std: number;
    quartiles: number[];
  };
  categorical_stats?: {
    num_categories: number;
    top_categories: Record<string, number>;
  };
  date_stats?: {
    min_date: string;
    max_date: string;
    date_range_days: number;
  };
}

export interface DatasetProfile {
  id: string;
  dataset_id: string;
  quality_score: number;
  profile: {
    basic_info: {
      filename: string;
      row_count: number;
      column_count: number;
      memory_usage_mb: number;
      file_size_bytes: number;
    };
    columns: ColumnInfo[];
    data_quality: {
      quality_score: number;
      missing_percentage: number;
      duplicate_rows: number;
      duplicate_percentage: number;
      recommendations: string[];
    };
    kpi_candidates: Array<{
      column: string;
      confidence: string;
      total?: number;
      mean?: number;
    }>;
    semantic_summary: {
      primary_metrics: string[];
      dimensions: string[];
      time_dimensions: string[];
      potential_analyses: string[];
    };
    dashboard?: {
      kpis: Array<{ title: string; value: string; subtext: string; column: string }>;
      charts: Array<{ id: string; title: string; type: string; spec: any }>;
    };
  };
  created_at: string;
}

export interface AnalysisResponse {
  id: string;
  workspace_id: string;
  dataset_id?: string;
  conversation_id?: string;
  question: string;
  intent?: Record<string, any>;
  plan?: string[];
  generated_code?: string;
  execution_status: 'SUCCESS' | 'FAILED' | 'CLARIFICATION_NEEDED';
  error_message?: string;
  needs_clarification: boolean;
  clarification_message?: string;
  clarification_options?: string[];
  result_table?: Record<string, any>[];
  chart_spec?: {
    type: string;
    spec: any;
  };
  presentation_type?: 'visualization' | 'table' | 'kpi';
  data_oversight?: {
    total_records: number;
    metric_totals?: Record<string, number>;
    dimensions?: string[];
    filters?: Record<string, string>;
  };
  insights?: string;
  recommendations?: string[];
  follow_up_questions?: string[];
  key_findings?: Array<{ title: string; description: string }>;
  data_interpretation?: string;
  strategic_recommendations?: Array<{ title: string; description: string }>;
  created_at: string;
}

export interface SavedInsight {
  id: string;
  workspace_id: string;
  analysis_id?: string;
  content: string;
  created_at: string;
}

export interface AnalystReportData {
  report_title: string;
  dataset_name: string;
  generated_at: string;
  summary_metrics: {
    row_count: number;
    column_count: number;
    file_size_bytes?: number;
    memory_mb?: number;
    quality_score: number;
    missing_percentage: number;
    duplicate_rows: number;
  };
  executive_summary: string;
  what_data_is_analysed: {
    overview: string;
    metrics_analysis?: string;
    dimensions_analysis?: string;
    quality_audit?: string;
    numeric_metrics?: Array<{
      name: string;
      total?: number;
      mean?: number;
      median?: number;
      min?: number;
      max?: number;
      std?: number;
      quartiles?: number[];
      null_count?: number;
    }>;
    categorical_dimensions?: Array<{
      name: string;
      unique_count: number;
      top_categories: Record<string, number>;
      top_percentages: Record<string, number>;
      null_count?: number;
    }>;
  };
  what_dataset_depicts: {
    general_depiction: string;
    key_patterns: Array<{
      title: string;
      description: string;
    }>;
    comparative_findings?: string;
    anomalies_and_risks?: string;
  };
  what_can_be_done: {
    strategic_actions: Array<{
      title: string;
      description: string;
    }>;
    advanced_analytics: Array<{
      title: string;
      description: string;
    }>;
    data_enrichment?: string;
  };
}

export interface Report {
  id: string;
  workspace_id: string;
  dataset_id?: string;
  name: string;
  file_path: string;
  download_url: string;
  created_at: string;
  report_data?: AnalystReportData;
}
