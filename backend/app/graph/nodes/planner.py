import json
import re
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from app.graph.state import AnalysisState
from app.graph.prompts.planner import PLANNER_PROMPT

def planner_node(state: AnalysisState) -> Dict[str, Any]:
    user_query = state.get("user_query", "")
    profile_summary = state.get("dataset_profile_summary", "")
    intent = state.get("query_intent", {})
    
    plan_list = []
    api_key = state.get("gemini_api_key") or settings.GEMINI_API_KEY
    if api_key:
        try:
            llm = ChatGoogleGenerativeAI(
                model=settings.LLM_MODEL,
                google_api_key=api_key,
                temperature=0.1
            )
            prompt = PLANNER_PROMPT.format(
                dataset_profile_summary=profile_summary,
                query_intent=json.dumps(intent),
                user_query=user_query
            )
            response = llm.invoke(prompt)
            json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group(0))
                plan_list = plan_data.get("plan", [])
        except Exception as e:
            print(f"Planner Node LLM Error: {e}")

    if not plan_list:
        plan_list = [
            "1. Inspect pre-loaded dataset columns and data types.",
            "2. Filter DataFrame based on query criteria.",
            "3. Perform grouping and metric aggregation.",
            "4. Sort results and store final output in variable `result`."
        ]

    return {
        "analysis_plan": plan_list
    }
