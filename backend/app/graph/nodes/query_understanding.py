import json
import re
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from app.graph.state import AnalysisState
from app.graph.prompts.query import QUERY_UNDERSTANDING_PROMPT

def get_llm(custom_api_key: str = None):
    api_key = custom_api_key or settings.GEMINI_API_KEY
    if not api_key:
        return None
    return ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        google_api_key=api_key,
        temperature=0.1
    )

def query_understanding_node(state: AnalysisState) -> Dict[str, Any]:
    llm = get_llm(state.get("gemini_api_key"))
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
                # Normalize metrics and group_by for multi-column combinations
                if intent_data.get("metrics") and not intent_data.get("metric"):
                    intent_data["metric"] = intent_data["metrics"][0]
                elif intent_data.get("metric") and not intent_data.get("metrics"):
                    intent_data["metrics"] = [intent_data["metric"]]

                gb = intent_data.get("group_by")
                if isinstance(gb, str):
                    intent_data["group_by"] = [gb]

                # If the query contains filters or requests details/records, do not block with clarification
                if intent_data.get("needs_clarification"):
                    if intent_data.get("filters") or any(w in user_query.lower() for w in ["who", "detail", "person", "customer", "buyer", "order", "list"]):
                        intent_data["needs_clarification"] = False
                        if not intent_data.get("intent") or intent_data.get("intent") == "unknown":
                            intent_data["intent"] = "filtering"
        except Exception as e:
            print(f"LLM Query Understanding Error: {e}")

    # Fallback heuristic query parser if LLM unavailable or failed
    if not intent_data:
        profile = state.get("dataset_profile", {})
        columns = profile.get("columns", [])
        num_cols = [c.get("name") for c in columns if "int" in c.get("data_type", "") or "float" in c.get("data_type", "")]
        cat_cols = [c.get("name") for c in columns if "object" in c.get("data_type", "") or "string" in c.get("data_type", "")]
        
        # Detect query mentioned columns
        matched_cat = [c for c in cat_cols if c.lower() in user_query.lower()]
        matched_num = [c for c in num_cols if c.lower() in user_query.lower()]
        
        # Check for filter matches from column sample values
        detected_filters = {}
        for c in columns:
            col_name = c.get("name")
            sample_vals = c.get("example_values", [])
            top_cats = list(c.get("categorical_stats", {}).get("top_categories", {}).keys()) if c.get("categorical_stats") else []
            for val in (sample_vals + top_cats):
                val_str = str(val).strip()
                if val_str and len(val_str) > 2 and val_str.lower() in user_query.lower():
                    detected_filters[col_name] = val_str
                    break

        is_detail_query = any(w in user_query.lower() for w in ["detail", "who", "which", "list", "find", "show me", "person"])
        if is_detail_query and detected_filters:
            intent_type = "filtering"
        elif len(matched_cat) > 0 or "by" in user_query.lower() or "per" in user_query.lower():
            intent_type = "grouping"
        else:
            intent_type = "aggregation"

        intent_data = {
            "intent": intent_type,
            "metric": matched_num[0] if matched_num else (num_cols[0] if num_cols else None),
            "metrics": matched_num if matched_num else (num_cols[:2] if num_cols else None),
            "group_by": matched_cat if matched_cat else (cat_cols[:1] if cat_cols else None),
            "filters": detected_filters,
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
