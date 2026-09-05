import json
import re
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from app.graph.state import AnalysisState
from app.graph.prompts.query import QUERY_UNDERSTANDING_PROMPT

def get_llm():
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return None
    return ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        google_api_key=api_key,
        temperature=0.1
    )

def query_understanding_node(state: AnalysisState) -> Dict[str, Any]:
    llm = get_llm()
    user_query = state.get("user_query", "")
    profile_summary = state.get("dataset_profile_summary", "")
    hist_summary = state.get("conversation_history_summary", "")
    
    intent_data = None
    if llm:
        try:
            prompt = QUERY_UNDERSTANDING_PROMPT.format(
                dataset_profile_summary=profile_summary,
                conversation_history=hist_summary,
                user_query=user_query
            )
            response = llm.invoke(prompt)
            content = response.content
            # Extract JSON block
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                intent_data = json.loads(json_match.group(0))
        except Exception as e:
            print(f"LLM Query Understanding Error: {e}")

    # Fallback heuristic query parser if LLM unavailable or failed
    if not intent_data:
        intent_type = "grouping" if "by" in user_query.lower() or "per" in user_query.lower() else "aggregation"
        intent_data = {
            "intent": intent_type,
            "metric": None,
            "group_by": None,
            "filters": {},
            "time_range": None,
            "refers_to_previous": any(word in user_query.lower() for word in ["only", "now", "compare", "that", "it"]),
            "needs_clarification": False if user_query.strip() else True,
            "clarification_message": None,
            "clarification_options": None
        }

    needs_clarification = intent_data.get("needs_clarification", False)
    clarification_msg = intent_data.get("clarification_message")
    clarification_opts = intent_data.get("clarification_options")

    return {
        "query_intent": intent_data,
        "needs_clarification": needs_clarification,
        "clarification_message": clarification_msg,
        "clarification_options": clarification_opts,
        "final_status": "CLARIFICATION_NEEDED" if needs_clarification else "PROCESSING"
    }
