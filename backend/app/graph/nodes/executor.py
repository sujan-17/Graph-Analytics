from typing import Dict, Any, List
from app.graph.state import AnalysisState
from app.graph.agents.base import BaseAgent
from app.graph.tools import sandbox_python_executor, ast_security_scanner

class ExecutorAgent(BaseAgent):
    """
    Executor Agent: Tool-assisted execution agent that invokes the
    AST security validator and isolated subprocess sandbox to run
    generated Pandas snippets safely.
    """
    name = "ExecutorAgent"
    role = "Subprocess Sandbox Code Execution & Security Barrier Agent"
    description = "Executes validated Pandas code in an isolated worker subprocess with strict timeout."
    tools = [sandbox_python_executor, ast_security_scanner]

    def __init__(self):
        super().__init__(
            name="ExecutorAgent",
            role="Subprocess Sandbox Code Execution & Security Barrier Agent",
            description="Executes code in isolated worker subprocess via LangChain tools.",
            tools=[sandbox_python_executor, ast_security_scanner]
        )

    def invoke(self, state: AnalysisState) -> Dict[str, Any]:
        csv_file_path = state.get("csv_file_path", "")
        code_str = state.get("generated_code", "")

        # Execute via the LangChain tool
        tool_result = sandbox_python_executor.invoke({
            "csv_path": csv_file_path,
            "code_str": code_str,
            "timeout_seconds": 15
        })

        success = tool_result.get("success", False)
        result_dict = tool_result.get("result", {})
        err_msg = tool_result.get("error", "")

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

# Agent instance for LangGraph StateGraph & backward-compatible node export
executor_agent = ExecutorAgent()
executor_node = executor_agent
