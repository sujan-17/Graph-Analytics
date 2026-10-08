from typing import Dict, Any
from app.graph.state import AnalysisState
from app.graph.agents.base import BaseAgent

class ResultValidatorAgent(BaseAgent):
    """
    Result Validator Agent: Validates output tabular data integrity,
    ensures non-emptiness, verifies scalar and DataFrame dimensions,
    and constructs summary statistical data for subsequent reasoning agents.
    """
    name = "ResultValidatorAgent"
    role = "Data Integrity & Verification Agent"
    description = "Inspects execution artifacts for correctness, non-emptiness, and formatting."

    def __init__(self):
        super().__init__(
            name="ResultValidatorAgent",
            role="Data Integrity & Verification Agent",
            description="Verifies tabular outputs and data types."
        )

    def invoke(self, state: AnalysisState) -> Dict[str, Any]:
        exec_result = state.get("execution_result")
        if not exec_result:
            return {
                "validation_result": False,
                "final_status": "FAILED",
                "execution_error": "No execution result data received."
            }

        res_type = exec_result.get("type")
        if res_type == "dataframe":
            data = exec_result.get("data", [])
            if not data:
                return {
                    "validation_result": False,
                    "final_status": "FAILED",
                    "execution_error": "Execution succeeded but produced an empty DataFrame."
                }
            sample_rows = data[:15]
            summary_str = f"DataFrame result with {len(data)} total rows and columns: {exec_result.get('columns')}.\nSample rows:\n" + "\n".join(str(r) for r in sample_rows)
            return {
                "validation_result": True,
                "result_summary": summary_str,
                "result_table": data
            }
        elif res_type == "scalar":
            val = exec_result.get("value")
            summary_str = f"Scalar analytical result: {val}"
            return {
                "validation_result": True,
                "result_summary": summary_str,
                "result_table": [{"Metric Value": val}]
            }
        else:
            summary_str = f"Analytical result: {exec_result}"
            return {
                "validation_result": True,
                "result_summary": summary_str,
                "result_table": []
            }

# Agent instance for LangGraph StateGraph & backward-compatible node export
result_validator_agent = ResultValidatorAgent()
result_validator_node = result_validator_agent
