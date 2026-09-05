from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.get("", response_model=List[WorkspaceResponse])
def list_workspaces(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Workspace).filter(Workspace.user_id == current_user.id).order_by(Workspace.updated_at.desc()).all()

@router.post("", response_model=WorkspaceResponse)
def create_workspace(ws_in: WorkspaceCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_ws = Workspace(
        user_id=current_user.id,
        name=ws_in.name,
        description=ws_in.description
    )
    db.add(new_ws)
    db.commit()
    db.refresh(new_ws)
    return new_ws

@router.get("/{id}", response_model=WorkspaceResponse)
def get_workspace(id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == id, Workspace.user_id == current_user.id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    return ws

@router.put("/{id}", response_model=WorkspaceResponse)
def update_workspace(id: str, ws_in: WorkspaceUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == id, Workspace.user_id == current_user.id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    if ws_in.name:
        ws.name = ws_in.name
    if ws_in.description is not None:
        ws.description = ws_in.description
    db.commit()
    db.refresh(ws)
    return ws

@router.delete("/{id}")
def delete_workspace(id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == id, Workspace.user_id == current_user.id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    db.delete(ws)
    db.commit()
    return {"status": "success", "message": "Workspace deleted."}
