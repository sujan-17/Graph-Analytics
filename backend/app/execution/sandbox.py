import os
import sys
import tempfile
import json
import subprocess
from typing import Dict, Any, Tuple
from app.execution.validator import validate_code_ast

def execute_pandas_code_safely(csv_path: str, code_str: str, timeout_seconds: int = 15) -> Tuple[bool, Dict[str, Any], str]:
    """
    Executes Pandas code in a isolated subprocess worker.
    Returns (success, result_dict, error_message).
    """
    # 1. AST Validation
    is_valid, validation_errors = validate_code_ast(code_str)
    if not is_valid:
        error_msg = f"Security Validation Failed: {'; '.join(validation_errors)}"
        return False, {}, error_msg

    # 2. Prepare temporary code and output files
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as code_file:
        code_file.write(code_str)
        code_file_path = code_file.name

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as out_file:
        out_file_path = out_file.name

    worker_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "worker.py"))
    python_executable = sys.executable

    cmd = [
        python_executable,
        worker_script,
        "--csv", csv_path,
        "--code", code_file_path,
        "--output", out_file_path
    ]

    try:
        # Run isolated subprocess worker
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )

        if os.path.exists(out_file_path):
            with open(out_file_path, "r", encoding="utf-8") as f:
                res_json = json.load(f)

            if res_json.get("status") == "success":
                return True, res_json.get("result", {}), ""
            else:
                err_detail = res_json.get("error", "Execution failed")
                return False, {}, err_detail
        else:
            stderr_out = proc.stderr or "Worker process exited unexpectedly."
            return False, {}, f"Subprocess Error: {stderr_out}"

    except subprocess.TimeoutExpired:
        return False, {}, f"Execution Timeout: Code execution exceeded limit of {timeout_seconds} seconds."
    except Exception as e:
        return False, {}, f"Sandbox Execution Error: {str(e)}"
    finally:
        # Clean up temporary files
        if os.path.exists(code_file_path):
            try:
                os.remove(code_file_path)
            except Exception:
                pass
        if os.path.exists(out_file_path):
            try:
                os.remove(out_file_path)
            except Exception:
                pass
