import re
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from app.graph.state import AnalysisState
from app.graph.prompts.code import CODE_GENERATOR_PROMPT

def code_generator_node(state: AnalysisState) -> Dict[str, Any]:
    user_query = state.get("user_query", "")
    profile_summary = state.get("dataset_profile_summary", "")
    plan = state.get("analysis_plan", [])
    
    generated_code = ""
    api_key = state.get("gemini_api_key") or settings.GEMINI_API_KEY
    if api_key:
        try:
            llm = ChatGoogleGenerativeAI(
                model=settings.LLM_MODEL,
                google_api_key=api_key,
                temperature=0.1
            )
            prompt = CODE_GENERATOR_PROMPT.format(
                dataset_profile_summary=profile_summary,
                analysis_plan="\n".join(plan),
                user_query=user_query
            )
            response = llm.invoke(prompt)
            content = response.content
            # Extract code from ```python ... ```
            code_match = re.search(r"```python\s*(.*?)\s*```", content, re.DOTALL)
            if code_match:
                generated_code = code_match.group(1).strip()
            else:
                generated_code = content.strip()
        except Exception as e:
            print(f"Code Generator LLM Error: {e}")

    # Heuristic code generation fallback if no Gemini key or LLM error
    if not generated_code:
        profile = state.get("dataset_profile", {})
        columns = profile.get("columns", [])
        all_cols = [c["name"] for c in columns]
        num_cols = [c["name"] for c in columns if "int" in c.get("data_type", "") or "float" in c.get("data_type", "")]
        cat_cols = [c["name"] for c in columns if "object" in c.get("data_type", "") or "string" in c.get("data_type", "")]
        
        # Check query intent or user query for matched columns
        intent = state.get("query_intent") or {}
        intent_gb = intent.get("group_by") or []
        intent_metrics = intent.get("metrics") or ([intent.get("metric")] if intent.get("metric") else [])
        intent_filters = intent.get("filters") or {}
        
        # If filters were detected (e.g. "person who buys technology in west region")
        if intent_filters:
            conds = [f"(df[{repr(col)}].astype(str).str.lower() == {repr(val.lower())})" for col, val in intent_filters.items()]
            generated_code = f"result = df[{' & '.join(conds)}].head(50)"
        else:
            matched_cat = [c for c in cat_cols if c in intent_gb or c.lower() in user_query.lower()]
            matched_num = [c for c in num_cols if c in intent_metrics or c.lower() in user_query.lower()]
            
            target_cats = matched_cat if matched_cat else (cat_cols[:2] if len(cat_cols) >= 2 else cat_cols[:1])
            target_nums = matched_num if matched_num else (num_cols[:2] if len(num_cols) >= 2 else num_cols[:1])
            
            if target_cats and target_nums:
                if len(target_cats) > 1:
                    cat_repr = "[" + ", ".join(repr(c) for c in target_cats) + "]"
                else:
                    cat_repr = repr(target_cats[0])
                    
                if len(target_nums) > 1:
                    num_list = "[" + ", ".join(repr(c) for c in target_nums) + "]"
                    sort_col = target_nums[0]
                    generated_code = f"result = df.groupby({cat_repr}, as_index=False)[{num_list}].sum().sort_values('{sort_col}', ascending=False)"
                else:
                    sort_col = target_nums[0]
                    generated_code = f"result = df.groupby({cat_repr}, as_index=False)[{repr(sort_col)}].sum().sort_values('{sort_col}', ascending=False)"
            elif target_nums:
                num_repr = "[" + ", ".join(repr(c) for c in target_nums) + "]" if len(target_nums) > 1 else f"['{target_nums[0]}']"
                generated_code = f"result = df{num_repr}.head(50)"
            elif all_cols:
                first_col = all_cols[0]
                generated_code = f"result = df['{first_col}'].value_counts().reset_index().head(20)"
            else:
                generated_code = "result = df.head(50)"

    return {
        "generated_code": generated_code
    }
