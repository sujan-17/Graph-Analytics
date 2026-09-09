import os
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from jose import jwt

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.models.dataset import Dataset, DatasetProfile
from app.models.analysis import Analysis
from app.models.report import SavedInsight, Report
from app.schemas.report import ReportCreate, ReportResponse
from app.api.auth import get_current_user
from app.services.report_service import report_service

router = APIRouter(tags=["reports"])

@router.post("/workspaces/{workspace_id}/reports", response_model=ReportResponse)
def create_workspace_report(
    workspace_id: str,
    rep_in: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id, Workspace.user_id == current_user.id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    # Gather saved insights
    saved_insights_objs = db.query(SavedInsight).filter(SavedInsight.workspace_id == workspace_id).order_by(SavedInsight.created_at.desc()).all()
    insights_list = [{"content": i.content} for i in saved_insights_objs]

    # Gather analyses
    analyses_objs = db.query(Analysis).filter(Analysis.workspace_id == workspace_id).order_by(Analysis.created_at.desc()).limit(10).all()
    analyses_list = []
    for a in analyses_objs:
        insights_text = ""
        if a.result and a.result.insights:
            try:
                ins_dict = json.loads(a.result.insights)
                insights_text = ins_dict.get("insights", "")
            except Exception:
                pass
        analyses_list.append({
            "question": a.question,
            "insights": insights_text
        })

    # Dataset info
    latest_ds = db.query(Dataset).filter(Dataset.workspace_id == workspace_id).order_by(Dataset.created_at.desc()).first()
    ds_info = {}
    if latest_ds:
        prof = db.query(DatasetProfile).filter(DatasetProfile.dataset_id == latest_ds.id).first()
        ds_info = {
            "filename": latest_ds.filename,
            "row_count": latest_ds.row_count,
            "column_count": latest_ds.column_count,
            "quality_score": prof.quality_score if prof else 100.0
        }

    # Generate PDF via ReportLab
    file_path = report_service.generate_pdf_report(
        workspace_name=ws.name,
        workspace_id=workspace_id,
        report_name=rep_in.name,
        saved_insights=insights_list,
        analyses=analyses_list,
        dataset_info=ds_info
    )

    new_report = Report(
        workspace_id=workspace_id,
        name=rep_in.name,
        file_path=file_path
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    download_url = f"/api/reports/{new_report.id}/download"
    return {
        "id": new_report.id,
        "workspace_id": workspace_id,
        "name": new_report.name,
        "file_path": new_report.file_path,
        "download_url": download_url,
        "created_at": new_report.created_at
    }

@router.get("/workspaces/{workspace_id}/reports", response_model=List[ReportResponse])
def list_workspace_reports(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id, Workspace.user_id == current_user.id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found or access denied.")
    reps = db.query(Report).filter(Report.workspace_id == workspace_id).order_by(Report.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "workspace_id": r.workspace_id,
            "name": r.name,
            "file_path": r.file_path,
            "download_url": f"/api/reports/{r.id}/download",
            "created_at": r.created_at
        }
        for r in reps
    ]

@router.get("/reports/{id}/download")
def download_report(
    id: str,
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    jwt_token = None
    if authorization and authorization.startswith("Bearer "):
        jwt_token = authorization.split(" ")[1]
    elif token:
        jwt_token = token

    if not jwt_token:
        raise HTTPException(status_code=401, detail="Authentication token required to download report.")

    try:
        payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token.")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    r = db.query(Report).join(Workspace, Report.workspace_id == Workspace.id).filter(
        Report.id == id,
        Workspace.user_id == user_id
    ).first()
    if not r or not r.file_path or not os.path.exists(r.file_path):
        raise HTTPException(status_code=404, detail="Report file not found or access denied.")
    return FileResponse(path=r.file_path, filename=f"{r.name}.pdf", media_type="application/pdf")
