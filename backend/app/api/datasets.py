import os
import json
import pandas as pd
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.models.dataset import Dataset, DatasetProfile
from app.schemas.dataset import DatasetResponse, DatasetProfileResponse
from app.api.auth import get_current_user
from app.services.storage_service import storage_service
from app.services.profiling_service import profiling_service
from app.services.dashboard_service import dashboard_service

router = APIRouter(tags=["datasets"])

@router.post("/workspaces/{workspace_id}/datasets", response_model=DatasetResponse)
async def upload_dataset(
    workspace_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id, Workspace.user_id == current_user.id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported in Version 1.")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Save to storage
    dataset_id, storage_path = storage_service.save_dataset_file(current_user.id, file.filename, content)

    # Perform automated dataset profiling
    try:
        profile_dict = profiling_service.profile_dataset(storage_path, file.filename)
        dashboard_spec = dashboard_service.generate_initial_dashboard(storage_path, profile_dict)
        profile_dict["dashboard"] = dashboard_spec
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse and profile CSV dataset: {str(e)}")

    row_cnt = profile_dict["basic_info"]["row_count"]
    col_cnt = profile_dict["basic_info"]["column_count"]
    q_score = profile_dict["data_quality"]["quality_score"]

    new_dataset = Dataset(
        id=dataset_id,
        workspace_id=workspace_id,
        filename=file.filename,
        storage_path=storage_path,
        row_count=row_cnt,
        column_count=col_cnt
    )
    db.add(new_dataset)
    db.commit()

    new_profile = DatasetProfile(
        dataset_id=dataset_id,
        profile_json=json.dumps(profile_dict),
        quality_score=q_score
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_dataset)

    return new_dataset

@router.get("/workspaces/{workspace_id}/datasets", response_model=List[DatasetResponse])
def list_workspace_datasets(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id, Workspace.user_id == current_user.id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found or access denied.")
    return db.query(Dataset).filter(Dataset.workspace_id == workspace_id).order_by(Dataset.created_at.desc()).all()

@router.get("/datasets/{dataset_id}/profile")
def get_dataset_profile(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ds = db.query(Dataset).join(Workspace, Dataset.workspace_id == Workspace.id).filter(
        Dataset.id == dataset_id,
        Workspace.user_id == current_user.id
    ).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found or access denied.")
    profile = db.query(DatasetProfile).filter(DatasetProfile.dataset_id == dataset_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Dataset profile not found.")
    return {
        "id": profile.id,
        "dataset_id": profile.dataset_id,
        "quality_score": profile.quality_score,
        "profile": json.loads(profile.profile_json),
        "created_at": profile.created_at
    }

@router.get("/datasets/{dataset_id}/preview")
def preview_dataset(
    dataset_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ds = db.query(Dataset).join(Workspace, Dataset.workspace_id == Workspace.id).filter(
        Dataset.id == dataset_id,
        Workspace.user_id == current_user.id
    ).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found or access denied.")
    
    try:
        df = storage_service.load_dataset_dataframe(ds.storage_path)
        preview_df = df.head(limit).fillna("").astype(str)
        return {
            "columns": list(df.columns),
            "total_rows": len(df),
            "preview_rows": preview_df.to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read dataset: {str(e)}")

@router.delete("/datasets/{dataset_id}")
def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ds = db.query(Dataset).join(Workspace, Dataset.workspace_id == Workspace.id).filter(
        Dataset.id == dataset_id,
        Workspace.user_id == current_user.id
    ).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found or access denied.")

    # Clean up physical storage file
    if ds.storage_path and os.path.exists(ds.storage_path):
        try:
            os.remove(ds.storage_path)
        except Exception:
            pass

    db.delete(ds)
    db.commit()
    return {"status": "success", "message": "Dataset deleted."}
