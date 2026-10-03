import json
import re
from typing import Dict, Any, List, Optional
from app.core.llm import call_gemini_llm
from app.graph.state import AnalysisState
from app.graph.prompts.query import QUERY_UNDERSTANDING_PROMPT

def is_col_id(name: str) -> bool:
    n = name.lower()
    return n.endswith("_id") or n.endswith("id") or n == "id" or "uuid" in n or n.endswith("_no") or "code" in n

def resolve_group_by_columns(group_by_list: List[str], available_columns: List[str]) -> List[str]:
    """
    Resolves group_by items (e.g. 'customer') to actual dataset columns (e.g. ['customer_id', 'customer']).
    Ensures that when an entity is requested, its ID column is included.
    """
    resolved = []
    avail_lower_map = {c.lower(): c for c in available_columns}

    for item in group_by_list:
        if not item:
            continue
        item_str = str(item).strip()
        item_lower = item_str.lower()

        # 1. Exact match
        if item_str in available_columns:
            if item_str not in resolved:
                resolved.append(item_str)
            continue

        # 2. Case-insensitive exact match
        if item_lower in avail_lower_map:
            c = avail_lower_map[item_lower]
            if c not in resolved:
                resolved.append(c)
            continue

        # 3. Entity semantic match (e.g. "customer" -> find customer_id and customer / customer_name)
        id_candidates = [
            c for c in available_columns
            if (item_lower in c.lower() or c.lower() in item_lower) and is_col_id(c)
        ]
        dim_candidates = [
            c for c in available_columns
            if (item_lower in c.lower() or c.lower() in item_lower) and not is_col_id(c)
        ]

        if id_candidates or dim_candidates:
            for c in id_candidates + dim_candidates:
                if c not in resolved:
                    resolved.append(c)
        else:
            sub_matches = [c for c in available_columns if item_lower in c.lower() or c.lower() in item_lower]
            for c in sub_matches:
                if c not in resolved:
                    resolved.append(c)

    return resolved if resolved else group_by_list

def query_understanding_node(state: AnalysisState) -> Dict[str, Any]:
    user_query = state.get("user_query", "")
    profile_summary = state.get("dataset_profile_summary", "")
    hist_summary = state.get("conversation_history_summary", "")
    
    profile = state.get("dataset_profile", {})
    columns = profile.get("columns", [])
    all_col_names = [c.get("name") for c in columns]

    intent_data = None
    prompt = QUERY_UNDERSTANDING_PROMPT.format(
        dataset_profile_summary=profile_summary,
        conversation_history=hist_summary,
        user_query=user_query
    )
    llm_output = call_gemini_llm(prompt, temperature=0.1, custom_api_key=state.get("gemini_api_key"))
    if llm_output:
        try:
            json_match = re.search(r"\{.*\}", llm_output, re.DOTALL)
            if json_match:
                intent_data = json.loads(json_match.group(0))
                if intent_data.get("metrics") and not intent_data.get("metric"):
                    intent_data["metric"] = intent_data["metrics"][0]
                elif intent_data.get("metric") and not intent_data.get("metrics"):
                    intent_data["metrics"] = [intent_data["metric"]]

                gb = intent_data.get("group_by")
                if isinstance(gb, str):
                    gb = [gb]
                if gb:
                    intent_data["group_by"] = resolve_group_by_columns(gb, all_col_names)

                if intent_data.get("needs_clarification"):
                    if intent_data.get("filters") or any(w in user_query.lower() for w in ["who", "detail", "person", "customer", "buyer", "order", "list"]):
                        intent_data["needs_clarification"] = False
                        if not intent_data.get("intent") or intent_data.get("intent") == "unknown":
                            intent_data["intent"] = "filtering"
        except Exception as e:
            print(f"Query Understanding JSON Parse Error: {e}")

    # Fallback heuristic query parser if LLM unavailable or failed
    if not intent_data:
        num_cols = [
            c.get("name") for c in columns
            if not is_col_id(c.get("name", "")) and any(t in c.get("data_type", "").lower() for t in ["int", "float", "double", "decimal", "numeric"])
        ]
        cat_cols = [
            c.get("name") for c in columns
            if any(t in c.get("data_type", "").lower() for t in ["str", "object", "string", "category", "text"])
        ]
        id_cols = [c.get("name") for c in columns if is_col_id(c.get("name", ""))]
        
        # Check entity matches (e.g. customer -> customer_id, customer)
        entity_terms = ["customer", "product", "order", "invoice", "rep", "employee", "store", "segment", "region"]
        matched_group_by = []
        for term in entity_terms:
            if term in user_query.lower():
                matching_ids = [c for c in id_cols if term in c.lower() or "id" in c.lower()]
                matching_dims = [c for c in cat_cols if term in c.lower()]
                for c in (matching_ids + matching_dims):
                    if c not in matched_group_by:
                        matched_group_by.append(c)

        matched_cat = [c for c in cat_cols if c.lower() in user_query.lower()]
        for c in matched_cat:
            if c not in matched_group_by:
                matched_group_by.append(c)

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

        # Check for numerical comparison in user query (e.g. "more than 10 quantity", "quantity > 10")
        q_low = user_query.lower()
        comp_match = re.search(r"(?:more than|greater than|>|>=)\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z_]+)", q_low)
        if not comp_match:
            comp_match = re.search(r"([a-zA-Z_]+)\s*(?:more than|greater than|>|>=)\s*([0-9]+(?:\.[0-9]+)?)", q_low)
        if comp_match:
            g1, g2 = comp_match.group(1), comp_match.group(2)
            col_cand = g2 if any(ch.isdigit() for ch in g1) else g1
            num_cand = g1 if any(ch.isdigit() for ch in g1) else g2
            m_cols = [c for c in all_col_names if col_cand in c.lower() or c.lower() in col_cand]
            if m_cols:
                detected_filters[m_cols[0]] = f">{num_cand}"

        less_match = re.search(r"(?:less than|under|<|<=)\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z_]+)", q_low)
        if not less_match:
            less_match = re.search(r"([a-zA-Z_]+)\s*(?:less than|under|<|<=)\s*([0-9]+(?:\.[0-9]+)?)", q_low)
        if less_match:
            g1, g2 = less_match.group(1), less_match.group(2)
            col_cand = g2 if any(ch.isdigit() for ch in g1) else g1
            num_cand = g1 if any(ch.isdigit() for ch in g1) else g2
            m_cols = [c for c in all_col_names if col_cand in c.lower() or c.lower() in col_cand]
            if m_cols:
                detected_filters[m_cols[0]] = f"<{num_cand}"

        is_detail_query = any(w in user_query.lower() for w in ["detail of", "details of", "who bought", "who buys", "show records", "show rows", "raw data"])
        if is_detail_query and detected_filters:
            intent_type = "filtering"
        elif len(matched_group_by) > 0 or "by" in user_query.lower() or "per" in user_query.lower():
            intent_type = "grouping"
        else:
            intent_type = "aggregation"

        intent_data = {
            "intent": intent_type,
            "metric": matched_num[0] if matched_num else (num_cols[0] if num_cols else None),
            "metrics": matched_num if matched_num else (num_cols[:2] if num_cols else None),
            "group_by": matched_group_by if matched_group_by else (cat_cols[:1] if cat_cols else None),
            "filters": detected_filters,
            "time_range": None,
            "refers_to_previous": any(word in user_query.lower() for word in ["only", "now", "compare", "that", "it"]),
            "needs_clarification": False if user_query.strip() else True,
            "clarification_message": None,
            "clarification_options": None
        }

    # Determine/normalize presentation_type: visualization vs table vs kpi
    table_keywords = ["show table", "output table", "tabular", "as a table", "raw table", "list all rows", "show records", "show rows", "raw data", "details of", "give me details"]
    is_table_query = any(k in user_query.lower() for k in table_keywords)

    pres_type = intent_data.get("presentation_type")
    if is_table_query:
        intent_data["presentation_type"] = "table"
    elif not pres_type or pres_type not in ["visualization", "table", "kpi"]:
        if intent_data.get("intent") in ["filtering", "lookup", "detail"] and not intent_data.get("group_by"):
            intent_data["presentation_type"] = "table"
        elif intent_data.get("intent") == "aggregation" and not intent_data.get("group_by") and not any(k in user_query.lower() for k in ["by", "per", "across", "compare", "how many"]):
            intent_data["presentation_type"] = "kpi"
        else:
            intent_data["presentation_type"] = "visualization"

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
