from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    question: str
    dataset_id: Optional[str] = None
    conversation_id: Optional[str] = None

class AnalysisResponse(BaseModel):
    id: str
    workspace_id: str
    dataset_id: Optional[str] = None
    conversation_id: Optional[str] = None
    question: str
    intent: Optional[Dict[str, Any]] = None
    plan: Optional[List[str]] = None
    generated_code: Optional[str] = None
    execution_status: str
    error_message: Optional[str] = None
    needs_clarification: bool = False
    clarification_message: Optional[str] = None
    clarification_options: Optional[List[str]] = None
    result_table: Optional[List[Dict[str, Any]]] = None
    chart_spec: Optional[Dict[str, Any]] = None
    insights: Optional[str] = None
    recommendations: Optional[List[str]] = None
    follow_up_questions: Optional[List[str]] = None
    key_findings: Optional[List[Dict[str, Any]]] = None
    data_interpretation: Optional[str] = None
    strategic_recommendations: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: str
    workspace_id: str
    messages: List[Dict[str, Any]]
    created_at: datetime
