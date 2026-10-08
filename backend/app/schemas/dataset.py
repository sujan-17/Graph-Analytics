from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel

class DatasetResponse(BaseModel):
    id: str
    workspace_id: str
    filename: str
    row_count: int
    column_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class DatasetProfileResponse(BaseModel):
    id: str
    dataset_id: str
    quality_score: float
    profile: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

class CombineDatasetsRequest(BaseModel):
    dataset_ids: Optional[List[str]] = None
    combined_name: Optional[str] = None
    merge_strategy: Optional[str] = "concat"

