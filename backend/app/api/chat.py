from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.schemas.analysis import ConversationResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/workspaces", tags=["chat"])

@router.get("/{workspace_id}/conversation", response_model=ConversationResponse)
def get_workspace_conversation(
    workspace_id: str,
    conversation_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if conversation_id:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.workspace_id == workspace_id).first()
    else:
        conv = db.query(Conversation).filter(Conversation.workspace_id == workspace_id).order_by(Conversation.created_at.desc()).first()

    if not conv:
        new_conv = Conversation(workspace_id=workspace_id)
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        conv = new_conv

    msgs = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at.asc()).all()
    msg_list = [{"id": m.id, "role": m.role, "content": m.content, "created_at": str(m.created_at)} for m in msgs]

    return {
        "id": conv.id,
        "workspace_id": workspace_id,
        "messages": msg_list,
        "created_at": conv.created_at
    }
