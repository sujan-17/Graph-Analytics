from typing import Dict, Any
from langchain_core.tools import tool
from app.execution.sandbox import execute_pandas_code_safely
from app.execution.validator import validate_code_ast

@tool("sandbox_python_executor")
def sandbox_python_executor(csv_path: str, code_str: str, timeout_seconds: int = 15) -> Dict[str, Any]:
    """
    Executes Python Pandas code in an isolated subprocess worker sandbox with strict AST validation and timeout.
    Returns a dictionary containing 'success' (bool), 'result' (dict), and 'error' (str).
    """
    success, result_dict, err_msg = execute_pandas_code_safely(
        csv_path=csv_path,
        code_str=code_str,
        timeout_seconds=timeout_seconds
    )
    return {
        "success": success,
        "result": result_dict,
        "error": err_msg
    }

@tool("ast_security_scanner")
def ast_security_scanner(code_str: str) -> Dict[str, Any]:
    """
    Statically analyzes Python code using the Python AST (Abstract Syntax Tree)
    to detect and block dangerous module imports (os, sys, subprocess, etc.),
    builtins (eval, exec, open), and unauthorized operations.
    """
    is_valid, validation_errors = validate_code_ast(code_str)
    return {
        "is_valid": is_valid,
        "errors": validation_errors
    }
