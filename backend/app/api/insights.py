from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.models.report import SavedInsight
from app.schemas.report import InsightCreate, InsightResponse
from app.api.auth import get_current_user

router = APIRouter(tags=["insights"])

@router.post("/insights", response_model=InsightResponse)
def save_insight(
    insight_in: InsightCreate,
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id, Workspace.user_id == current_user.id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    new_insight = SavedInsight(
        workspace_id=workspace_id,
        analysis_id=insight_in.analysis_id,
        content=insight_in.content
    )
    db.add(new_insight)
    db.commit()
    db.refresh(new_insight)
    return new_insight

@router.get("/workspaces/{workspace_id}/insights", response_model=List[InsightResponse])
def list_workspace_insights(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(SavedInsight).filter(SavedInsight.workspace_id == workspace_id).order_by(SavedInsight.created_at.desc()).all()

@router.delete("/insights/{id}")
def delete_insight(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ins = db.query(SavedInsight).filter(SavedInsight.id == id).first()
    if not ins:
        raise HTTPException(status_code=404, detail="Saved insight not found.")
    db.delete(ins)
    db.commit()
    return {"status": "success", "message": "Insight deleted."}
