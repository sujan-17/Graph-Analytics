from typing import Dict, Any
from app.graph.state import AnalysisState
from app.execution.sandbox import execute_pandas_code_safely

def executor_node(state: AnalysisState) -> Dict[str, Any]:
    csv_file_path = state.get("csv_file_path", "")
    code_str = state.get("generated_code", "")
    
    success, result_dict, err_msg = execute_pandas_code_safely(
        csv_path=csv_file_path,
        code_str=code_str,
        timeout_seconds=15
    )

    if success:
        return {
            "validation_result": True,
            "execution_result": result_dict,
            "execution_error": None,
            "result_table": result_dict.get("data") if result_dict.get("type") == "dataframe" else None
        }
    else:
        retry_cnt = state.get("retry_count", 0)
        return {
            "validation_result": False,
            "execution_result": None,
            "execution_error": err_msg,
            "retry_count": retry_cnt + 1
        }
