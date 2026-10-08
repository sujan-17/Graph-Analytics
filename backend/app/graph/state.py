from typing import Dict, Any, List, Optional, TypedDict

class AnalysisState(TypedDict):
    user_id: str
    workspace_id: str
    dataset_id: str
    csv_file_path: str
    dataset_profile: Dict[str, Any]
    user_query: str
    conversation_history: List[Dict[str, Any]]
    gemini_api_key: Optional[str]
    dataset_profile_summary: Optional[str]
    conversation_history_summary: Optional[str]
    
    # Node outputs
    query_intent: Optional[Dict[str, Any]]
    needs_clarification: bool
    clarification_message: Optional[str]
    clarification_options: Optional[List[str]]
    
    analysis_plan: Optional[List[str]]
    generated_code: Optional[str]
    validation_result: bool
    validation_error: Optional[str]
    
    execution_result: Optional[Dict[str, Any]]
    execution_error: Optional[str]
    retry_count: int
    
    result_table: Optional[List[Dict[str, Any]]]
    result_summary: Optional[str]
    
    chart_config: Optional[Dict[str, Any]]
    
    insights: Optional[str]
    recommendations: Optional[List[str]]
    follow_up_questions: Optional[List[str]]
    key_findings: Optional[List[Dict[str, str]]]
    data_interpretation: Optional[str]
    strategic_recommendations: Optional[List[Dict[str, str]]]
    
    final_status: str  # SUCCESS, FAILED, CLARIFICATION_NEEDED
