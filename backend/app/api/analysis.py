import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.models.dataset import Dataset, DatasetProfile
from app.models.conversation import Conversation, Message
from app.models.analysis import Analysis, AnalysisResult
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.api.auth import get_current_user
from app.graph.graph import analysis_graph

router = APIRouter(tags=["analysis"])

@router.post("/workspaces/{workspace_id}/analysis", response_model=AnalysisResponse)
def run_conversational_analysis(
    workspace_id: str,
    req: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id, Workspace.user_id == current_user.id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    # Select active dataset
    dataset_id = req.dataset_id
    if not dataset_id:
        latest_ds = db.query(Dataset).filter(Dataset.workspace_id == workspace_id).order_by(Dataset.created_at.desc()).first()
        if not latest_ds:
            raise HTTPException(status_code=400, detail="No CSV dataset uploaded in this workspace. Please upload a dataset first.")
        dataset_id = latest_ds.id

    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Selected dataset not found.")

    profile_rec = db.query(DatasetProfile).filter(DatasetProfile.dataset_id == dataset_id).first()
    profile_dict = json.loads(profile_rec.profile_json) if profile_rec else {}

    # Get conversation history if conversation_id provided or create conversation
    conv_id = req.conversation_id
    if not conv_id:
        new_conv = Conversation(workspace_id=workspace_id)
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        conv_id = new_conv.id

    # Record user message in DB
    user_msg = Message(conversation_id=conv_id, role="user", content=req.question)
    db.add(user_msg)
    db.commit()

    # Load history messages
    prev_messages = db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.created_at.asc()).all()
    history_list = [{"role": m.role, "content": m.content} for m in prev_messages]

    # Initialize LangGraph AnalysisState
    initial_state = {
        "user_id": current_user.id,
        "workspace_id": workspace_id,
        "dataset_id": dataset_id,
        "csv_file_path": ds.storage_path,
        "dataset_profile": profile_dict,
        "user_query": req.question,
        "conversation_history": history_list,
        "query_intent": None,
        "needs_clarification": False,
        "clarification_message": None,
        "clarification_options": None,
        "analysis_plan": None,
        "generated_code": None,
        "validation_result": False,
        "execution_result": None,
        "execution_error": None,
        "retry_count": 0,
        "result_table": None,
        "result_summary": None,
        "chart_config": None,
        "insights": None,
        "recommendations": None,
        "follow_up_questions": None,
        "final_status": "PROCESSING"
    }

    # Execute LangGraph Multi-Agent Workflow
    final_state = analysis_graph.invoke(initial_state)

    exec_status = final_state.get("final_status", "SUCCESS")
    err_msg = final_state.get("execution_error")

    # Save Analysis run in DB
    new_analysis = Analysis(
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        conversation_id=conv_id,
        question=req.question,
        intent_json=json.dumps(final_state.get("query_intent")) if final_state.get("query_intent") else None,
        plan_json=json.dumps(final_state.get("analysis_plan")) if final_state.get("analysis_plan") else None,
        generated_code=final_state.get("generated_code"),
        execution_status=exec_status,
        error_message=err_msg
    )
    db.add(new_analysis)
    db.commit()
    db.refresh(new_analysis)

    res_insights_dict = {
        "insights": final_state.get("insights"),
        "recommendations": final_state.get("recommendations"),
        "follow_up_questions": final_state.get("follow_up_questions")
    }

    new_result = AnalysisResult(
        analysis_id=new_analysis.id,
        result_json=json.dumps(final_state.get("result_table")) if final_state.get("result_table") is not None else None,
        chart_json=json.dumps(final_state.get("chart_config")) if final_state.get("chart_config") is not None else None,
        insights=json.dumps(res_insights_dict)
    )
    db.add(new_result)

    # Record Assistant message response in conversation
    ai_content = final_state.get("insights") or final_state.get("clarification_message") or err_msg or "Analysis executed."
    assistant_msg = Message(conversation_id=conv_id, role="assistant", content=ai_content)
    db.add(assistant_msg)
    db.commit()

    return {
        "id": new_analysis.id,
        "workspace_id": workspace_id,
        "dataset_id": dataset_id,
        "conversation_id": conv_id,
        "question": req.question,
        "intent": final_state.get("query_intent"),
        "plan": final_state.get("analysis_plan"),
        "generated_code": final_state.get("generated_code"),
        "execution_status": exec_status,
        "error_message": err_msg,
        "needs_clarification": final_state.get("needs_clarification", False),
        "clarification_message": final_state.get("clarification_message"),
        "clarification_options": final_state.get("clarification_options"),
        "result_table": final_state.get("result_table"),
        "chart_spec": final_state.get("chart_config"),
        "insights": final_state.get("insights"),
        "recommendations": final_state.get("recommendations"),
        "follow_up_questions": final_state.get("follow_up_questions"),
        "created_at": new_analysis.created_at
    }

@router.get("/workspaces/{workspace_id}/analysis", response_model=List[AnalysisResponse])
def list_workspace_analyses(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analyses = db.query(Analysis).filter(Analysis.workspace_id == workspace_id).order_by(Analysis.created_at.desc()).all()
    res_list = []
    for a in analyses:
        r = a.result
        res_table = json.loads(r.result_json) if r and r.result_json else None
        chart_spec = json.loads(r.chart_json) if r and r.chart_json else None
        ins_dict = json.loads(r.insights) if r and r.insights else {}

        res_list.append({
            "id": a.id,
            "workspace_id": a.workspace_id,
            "dataset_id": a.dataset_id,
            "conversation_id": a.conversation_id,
            "question": a.question,
            "intent": json.loads(a.intent_json) if a.intent_json else None,
            "plan": json.loads(a.plan_json) if a.plan_json else None,
            "generated_code": a.generated_code,
            "execution_status": a.execution_status,
            "error_message": a.error_message,
            "needs_clarification": False,
            "clarification_message": None,
            "clarification_options": None,
            "result_table": res_table,
            "chart_spec": chart_spec,
            "insights": ins_dict.get("insights"),
            "recommendations": ins_dict.get("recommendations"),
            "follow_up_questions": ins_dict.get("follow_up_questions"),
            "created_at": a.created_at
        })
    return res_list

@router.get("/analysis/{id}", response_model=AnalysisResponse)
def get_analysis_detail(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    a = db.query(Analysis).filter(Analysis.id == id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Analysis run not found.")
    r = a.result
    res_table = json.loads(r.result_json) if r and r.result_json else None
    chart_spec = json.loads(r.chart_json) if r and r.chart_json else None
    ins_dict = json.loads(r.insights) if r and r.insights else {}

    return {
        "id": a.id,
        "workspace_id": a.workspace_id,
        "dataset_id": a.dataset_id,
        "conversation_id": a.conversation_id,
        "question": a.question,
        "intent": json.loads(a.intent_json) if a.intent_json else None,
        "plan": json.loads(a.plan_json) if a.plan_json else None,
        "generated_code": a.generated_code,
        "execution_status": a.execution_status,
        "error_message": a.error_message,
        "needs_clarification": False,
        "clarification_message": None,
        "clarification_options": None,
        "result_table": res_table,
        "chart_spec": chart_spec,
        "insights": ins_dict.get("insights"),
        "recommendations": ins_dict.get("recommendations"),
        "follow_up_questions": ins_dict.get("follow_up_questions"),
        "created_at": a.created_at
    }
