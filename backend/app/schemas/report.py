from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class InsightCreate(BaseModel):
    analysis_id: Optional[str] = None
    content: str

class InsightResponse(BaseModel):
    id: str
    workspace_id: str
    analysis_id: Optional[str] = None
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReportCreate(BaseModel):
    name: str
    dataset_id: Optional[str] = None
    selected_insight_ids: Optional[List[str]] = None
    selected_analysis_ids: Optional[List[str]] = None

class ReportResponse(BaseModel):
    id: str
    workspace_id: str
    dataset_id: Optional[str] = None
    name: str
    file_path: str
    download_url: str
    created_at: datetime
    report_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
