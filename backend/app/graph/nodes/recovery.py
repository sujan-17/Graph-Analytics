import re
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from app.graph.state import AnalysisState
from app.graph.prompts.recovery import RECOVERY_PROMPT

def recovery_node(state: AnalysisState) -> Dict[str, Any]:
    user_query = state.get("user_query", "")
    profile_summary = state.get("dataset_profile_summary", "")
    failed_code = state.get("generated_code", "")
    err_msg = state.get("execution_error", "Unknown error")
    
    corrected_code = ""
    from app.core.llm import call_gemini_llm
    prompt = RECOVERY_PROMPT.format(
        dataset_profile_summary=profile_summary,
        failed_code=failed_code,
        error_message=err_msg,
        user_query=user_query
    )
    llm_output = call_gemini_llm(prompt, temperature=0.1, custom_api_key=state.get("gemini_api_key"))
    if llm_output:
        code_match = re.search(r"```python\s*(.*?)\s*```", llm_output, re.DOTALL)
        if code_match:
            corrected_code = code_match.group(1).strip()
        else:
            corrected_code = llm_output.strip()

    if not corrected_code:
        # Check for common Pandas indexing mistake: df.groupby(...)['A', 'B'] -> df.groupby(...)[['A', 'B']]
        if failed_code and "KeyError" in err_msg:
            repaired = re.sub(r"(\)\s*\[)(?!\s*\[)(['\"][^\]]+,\s*['\"][^\]]+)(\])", r"\1[\2]\3", failed_code)
            if repaired != failed_code:
                corrected_code = repaired
        
        if not corrected_code:
            corrected_code = "result = df.head(50)"

    return {
        "generated_code": corrected_code
    }
