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
from app.schemas.dataset import DatasetResponse, DatasetProfileResponse, CombineDatasetsRequest
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

@router.post("/workspaces/{workspace_id}/datasets/combine", response_model=DatasetResponse)
def combine_workspace_datasets(
    workspace_id: str,
    req: CombineDatasetsRequest = CombineDatasetsRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id, Workspace.user_id == current_user.id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found or access denied.")

    # Determine which datasets to combine
    if req.dataset_ids and len(req.dataset_ids) > 0:
        datasets = db.query(Dataset).filter(
            Dataset.workspace_id == workspace_id,
            Dataset.id.in_(req.dataset_ids)
        ).all()
        id_order = {did: idx for idx, did in enumerate(req.dataset_ids)}
        datasets.sort(key=lambda d: id_order.get(d.id, 999))
    else:
        datasets = db.query(Dataset).filter(Dataset.workspace_id == workspace_id).order_by(Dataset.created_at.asc()).all()

    if len(datasets) < 2:
        raise HTTPException(
            status_code=400,
            detail=f"At least 2 datasets are required to combine them into a single dataset. Found {len(datasets)} dataset(s)."
        )

    dfs = []
    for ds in datasets:
        if not ds.storage_path or not os.path.exists(ds.storage_path):
            raise HTTPException(status_code=400, detail=f"Dataset file '{ds.filename}' is missing from storage.")
        try:
            df = storage_service.load_dataset_dataframe(ds.storage_path)
            df.columns = [str(col).strip() for col in df.columns]
            dfs.append((ds.filename, df))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to load dataset '{ds.filename}': {str(e)}")

    strategy = (req.merge_strategy or "concat").lower()
    combined_df = None

    if strategy in ["merge", "join"]:
        common_cols = set(dfs[0][1].columns)
        for _, d in dfs[1:]:
            common_cols = common_cols.intersection(set(d.columns))
        common_cols = [c for c in common_cols if c != "_source_dataset"]

        if common_cols:
            combined_df = dfs[0][1]
            for fname, d in dfs[1:]:
                combined_df = pd.merge(combined_df, d, on=common_cols, how="outer", suffixes=("", f"_{fname[:8]}"))
        else:
            strategy = "concat"

    if strategy == "concat" or combined_df is None:
        tagged_dfs = []
        for fname, d in dfs:
            d_copy = d.copy()
            d_copy["_source_dataset"] = fname
            tagged_dfs.append(d_copy)
        combined_df = pd.concat(tagged_dfs, ignore_index=True, sort=False)

    clean_ws = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in ws.name)
    if req.combined_name and req.combined_name.strip():
        comb_fname = req.combined_name.strip()
        if not comb_fname.lower().endswith(".csv"):
            comb_fname += ".csv"
    else:
        comb_fname = f"Combined_{clean_ws}_{len(datasets)}_datasets.csv"

    csv_bytes = combined_df.to_csv(index=False).encode("utf-8")
    dataset_id, storage_path = storage_service.save_dataset_file(current_user.id, comb_fname, csv_bytes)

    try:
        profile_dict = profiling_service.profile_dataset(storage_path, comb_fname)
        dashboard_spec = dashboard_service.generate_initial_dashboard(storage_path, profile_dict)
        profile_dict["dashboard"] = dashboard_spec
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to profile combined dataset: {str(e)}")

    row_cnt = profile_dict["basic_info"]["row_count"]
    col_cnt = profile_dict["basic_info"]["column_count"]
    q_score = profile_dict["data_quality"]["quality_score"]

    new_dataset = Dataset(
        id=dataset_id,
        workspace_id=workspace_id,
        filename=comb_fname,
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

