import json
import re
from typing import Dict, Any
from app.core.llm import call_gemini_llm
from app.graph.state import AnalysisState
from app.graph.prompts.planner import PLANNER_PROMPT

def planner_node(state: AnalysisState) -> Dict[str, Any]:
    user_query = state.get("user_query", "")
    profile_summary = state.get("dataset_profile_summary", "")
    intent = state.get("query_intent", {})
    
    plan_list = []
    prompt = PLANNER_PROMPT.format(
        dataset_profile_summary=profile_summary,
        query_intent=json.dumps(intent),
        user_query=user_query
    )
    llm_output = call_gemini_llm(prompt, temperature=0.1, custom_api_key=state.get("gemini_api_key"))
    if llm_output:
        try:
            json_match = re.search(r"\{.*\}", llm_output, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group(0))
                plan_list = plan_data.get("plan", [])
        except Exception as e:
            print(f"Planner JSON Parse Error: {e}")

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
