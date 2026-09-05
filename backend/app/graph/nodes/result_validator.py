from typing import Dict, Any
from app.graph.state import AnalysisState

def result_validator_node(state: AnalysisState) -> Dict[str, Any]:
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
        summary_str = f"DataFrame result with {len(data)} rows and columns: {exec_result.get('columns')}.\nTop rows: {data[:5]}"
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
