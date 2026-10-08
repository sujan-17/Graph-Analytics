import re
from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from app.core.llm import call_gemini_llm
from app.graph.state import AnalysisState
from app.graph.agents.base import BaseAgent
from app.graph.prompts.recovery import RECOVERY_PROMPT

class RecoveryAgent(BaseAgent):
    """
    Self-Correction & Recovery Agent: Autonomous error repair agent.
    When a Pandas execution raises an exception (KeyError, IndexError, SyntaxError),
    it inspects the runtime traceback, failed code, and dataset schema, reflects
    on the underlying bug, and regenerates corrected code.
    """
    name = "RecoveryAgent"
    role = "Self-Correction & Autonomous Code Repair Agent"
    description = "Analyzes runtime tracebacks and synthesizes repaired code to heal execution failures."

    def __init__(self):
        super().__init__(
            name="RecoveryAgent",
            role="Self-Correction & Autonomous Code Repair Agent",
            description="Reflects on execution errors and patches code using LangChain PromptTemplate."
        )
        self.prompt_template = PromptTemplate(
            template=RECOVERY_PROMPT,
            input_variables=["dataset_profile_summary", "failed_code", "error_message", "user_query"]
        )

    def invoke(self, state: AnalysisState) -> Dict[str, Any]:
        user_query = state.get("user_query", "")
        profile_summary = state.get("dataset_profile_summary", "")
        failed_code = state.get("generated_code", "")
        err_msg = state.get("execution_error", "Unknown error")
        
        corrected_code = ""
        prompt_text = self.prompt_template.format(
            dataset_profile_summary=profile_summary,
            failed_code=failed_code,
            error_message=err_msg,
            user_query=user_query
        )
        
        llm_output = call_gemini_llm(prompt_text, temperature=0.1, custom_api_key=state.get("gemini_api_key"))
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

# Agent instance for LangGraph StateGraph & backward-compatible node export
recovery_agent = RecoveryAgent()
recovery_node = recovery_agent
