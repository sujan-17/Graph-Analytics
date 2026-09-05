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
    api_key = settings.GEMINI_API_KEY
    if api_key:
        try:
            llm = ChatGoogleGenerativeAI(
                model=settings.LLM_MODEL,
                google_api_key=api_key,
                temperature=0.1
            )
            prompt = RECOVERY_PROMPT.format(
                dataset_profile_summary=profile_summary,
                failed_code=failed_code,
                error_message=err_msg,
                user_query=user_query
            )
            response = llm.invoke(prompt)
            content = response.content
            code_match = re.search(r"```python\s*(.*?)\s*```", content, re.DOTALL)
            if code_match:
                corrected_code = code_match.group(1).strip()
            else:
                corrected_code = content.strip()
        except Exception as e:
            print(f"Recovery Node LLM Error: {e}")

    if not corrected_code:
        # Fallback simple repair
        corrected_code = "result = df.describe().reset_index()"

    return {
        "generated_code": corrected_code
    }
