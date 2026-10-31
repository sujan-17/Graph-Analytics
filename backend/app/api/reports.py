import os
import json
import uuid
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
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportResponse
from app.api.auth import get_current_user
from app.services.report_service import report_service
from app.services.dataset_analyst_service import dataset_analyst_service

router = APIRouter(tags=["reports"])

def _load_report_data(r: Report) -> Optional[dict]:
    if getattr(r, "content_json", None):
        try:
            return json.loads(r.content_json)
        except Exception:
            pass
    if r.file_path:
        json_path = os.path.splitext(r.file_path)[0] + ".json"
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return None

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

    # Target dataset for analysis
    target_ds = None
    if rep_in.dataset_id:
        target_ds = db.query(Dataset).filter(Dataset.id == rep_in.dataset_id, Dataset.workspace_id == workspace_id).first()
        if not target_ds:
            raise HTTPException(status_code=404, detail="Specified dataset not found in this workspace.")
    else:
        # Fallback to latest dataset in workspace
        target_ds = db.query(Dataset).filter(Dataset.workspace_id == workspace_id).order_by(Dataset.created_at.desc()).first()

    if not target_ds:
        raise HTTPException(status_code=400, detail="No dataset found in this workspace. Please upload a dataset first to generate a report.")

    if not target_ds.storage_path or not os.path.exists(target_ds.storage_path):
        raise HTTPException(status_code=404, detail=f"Dataset file '{target_ds.filename}' not found on storage.")

    # Extract dataset profile metadata if already computed
    prof = db.query(DatasetProfile).filter(DatasetProfile.dataset_id == target_ds.id).first()
    profile_dict = None
    if prof and prof.profile_json:
        try:
            profile_dict = json.loads(prof.profile_json)
        except Exception:
            pass

    # Generate Data Analyst report (What Data is Analysed, Current Depiction, What Can Be Done)
    analyst_report = dataset_analyst_service.generate_analyst_report(
        file_path=target_ds.storage_path,
        filename=target_ds.filename,
        report_title=rep_in.name,
        profile_dict=profile_dict
    )

    report_id = str(uuid.uuid4())
    dataset_info = {
        "filename": target_ds.filename,
        "row_count": target_ds.row_count,
        "column_count": target_ds.column_count,
        "quality_score": analyst_report.get("summary_metrics", {}).get("quality_score", 100.0)
    }

    # Generate PDF via ReportLab
    file_path = report_service.generate_pdf_report(
        workspace_name=ws.name,
        workspace_id=workspace_id,
        report_name=rep_in.name,
        dataset_info=dataset_info,
        analyst_report=analyst_report,
        report_id=report_id
    )

    # Save companion JSON
    json_path = os.path.splitext(file_path)[0] + ".json"
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(analyst_report, f, indent=2)
    except Exception as e:
        print(f"Failed to write companion report JSON: {e}")

    new_report = Report(
        id=report_id,
        workspace_id=workspace_id,
        dataset_id=target_ds.id,
        name=rep_in.name,
        file_path=file_path,
        content_json=json.dumps(analyst_report)
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    download_url = f"/api/reports/{new_report.id}/download"
    return {
        "id": new_report.id,
        "workspace_id": workspace_id,
        "dataset_id": new_report.dataset_id,
        "name": new_report.name,
        "file_path": new_report.file_path,
        "download_url": download_url,
        "created_at": new_report.created_at,
        "report_data": analyst_report
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
    results = []
    for r in reps:
        rep_data = _load_report_data(r)
        results.append({
            "id": r.id,
            "workspace_id": r.workspace_id,
            "dataset_id": getattr(r, "dataset_id", None),
            "name": r.name,
            "file_path": r.file_path,
            "download_url": f"/api/reports/{r.id}/download",
            "created_at": r.created_at,
            "report_data": rep_data
        })
    return results

@router.get("/reports/{id}", response_model=ReportResponse)
def get_single_report(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    r = db.query(Report).join(Workspace, Report.workspace_id == Workspace.id).filter(
        Report.id == id,
        Workspace.user_id == current_user.id
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found or access denied.")

    return {
        "id": r.id,
        "workspace_id": r.workspace_id,
        "dataset_id": getattr(r, "dataset_id", None),
        "name": r.name,
        "file_path": r.file_path,
        "download_url": f"/api/reports/{r.id}/download",
        "created_at": r.created_at,
        "report_data": _load_report_data(r)
    }

@router.delete("/reports/{id}")
def delete_report(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    r = db.query(Report).join(Workspace, Report.workspace_id == Workspace.id).filter(
        Report.id == id,
        Workspace.user_id == current_user.id
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found or access denied.")

    # Remove files if exist
    if r.file_path and os.path.exists(r.file_path):
        try:
            os.remove(r.file_path)
            json_path = os.path.splitext(r.file_path)[0] + ".json"
            if os.path.exists(json_path):
                os.remove(json_path)
        except Exception:
            pass

    db.delete(r)
    db.commit()
    return {"message": "Report deleted successfully.", "id": id}

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
    if not r:
        raise HTTPException(status_code=404, detail="Report not found or access denied.")

    # Check if report has the new Data Analyst content
    analyst_report = _load_report_data(r)
    if not analyst_report:
        # Find target dataset in workspace to regenerate
        target_ds = None
        if getattr(r, "dataset_id", None):
            target_ds = db.query(Dataset).filter(Dataset.id == r.dataset_id).first()
        if not target_ds:
            target_ds = db.query(Dataset).filter(Dataset.workspace_id == r.workspace_id).order_by(Dataset.created_at.desc()).first()

        if target_ds and target_ds.storage_path and os.path.exists(target_ds.storage_path):
            prof = db.query(DatasetProfile).filter(DatasetProfile.dataset_id == target_ds.id).first()
            p_dict = json.loads(prof.profile_json) if prof and prof.profile_json else None
            analyst_report = dataset_analyst_service.generate_analyst_report(
                file_path=target_ds.storage_path,
                filename=target_ds.filename,
                report_title=r.name,
                profile_dict=p_dict
            )
            # Re-compile PDF with new Data Analyst sections
            new_file_path = report_service.generate_pdf_report(
                workspace_name=r.workspace.name,
                workspace_id=r.workspace_id,
                report_name=r.name,
                dataset_info={
                    "filename": target_ds.filename,
                    "row_count": target_ds.row_count,
                    "column_count": target_ds.column_count,
                    "quality_score": analyst_report.get("summary_metrics", {}).get("quality_score", 100.0)
                },
                analyst_report=analyst_report,
                report_id=r.id
            )
            r.file_path = new_file_path
            r.content_json = json.dumps(analyst_report)
            r.dataset_id = target_ds.id
            db.commit()

            json_path = os.path.splitext(r.file_path)[0] + ".json"
            try:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(analyst_report, f, indent=2)
            except Exception:
                pass

    if not r.file_path or not os.path.exists(r.file_path):
        raise HTTPException(status_code=404, detail="Report file not found or access denied.")
    return FileResponse(path=r.file_path, filename=f"{r.name}.pdf", media_type="application/pdf")
