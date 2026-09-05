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
    api_key = settings.GEMINI_API_KEY
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
        num_cols = [c["name"] for c in profile.get("columns", []) if "int" in c.get("data_type", "") or "float" in c.get("data_type", "")]
        cat_cols = [c["name"] for c in profile.get("columns", []) if "object" in c.get("data_type", "") or "string" in c.get("data_type", "")]
        
        num_col = num_cols[0] if num_cols else df.columns[0]
        if cat_cols:
            cat_col = cat_cols[0]
            generated_code = f"result = df.groupby('{cat_col}', as_index=False)['{num_col}'].sum().sort_values('{num_col}', ascending=False)"
        else:
            generated_code = f"result = df['{num_col}'].sum()"

    return {
        "generated_code": generated_code
    }
