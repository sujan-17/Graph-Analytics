from langgraph.graph import StateGraph, END
from app.graph.state import AnalysisState
from app.graph.nodes.context import context_node
from app.graph.nodes.query_understanding import query_understanding_node
from app.graph.nodes.planner import planner_node
from app.graph.nodes.code_generator import code_generator_node
from app.graph.nodes.executor import executor_node
from app.graph.nodes.recovery import recovery_node
from app.graph.nodes.result_validator import result_validator_node
from app.graph.nodes.visualization import visualization_node
from app.graph.nodes.insights import insights_node

def check_clarification_needed(state: AnalysisState) -> str:
    if state.get("needs_clarification", False):
        return "clarification_needed"
    return "proceed_to_planner"

def check_execution_status(state: AnalysisState) -> str:
    if state.get("validation_result", False):
        return "execution_success"
    if state.get("retry_count", 0) <= 2:
        return "retry_recovery"
    return "execution_failed"

def build_analysis_graph():
    workflow = StateGraph(AnalysisState)

    # Add agent nodes
    workflow.add_node("context", context_node)
    workflow.add_node("query_understanding", query_understanding_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("code_generator", code_generator_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("recovery", recovery_node)
    workflow.add_node("result_validator", result_validator_node)
    workflow.add_node("visualization", visualization_node)
    workflow.add_node("insights", insights_node)

    # Set entrypoint
    workflow.set_entry_point("context")

    # Edges
    workflow.add_edge("context", "query_understanding")

    # Conditional edge after query understanding
    workflow.add_conditional_edges(
        "query_understanding",
        check_clarification_needed,
        {
            "clarification_needed": END,
            "proceed_to_planner": "planner"
        }
    )

    workflow.add_edge("planner", "code_generator")
    workflow.add_edge("code_generator", "executor")

    # Conditional edge after code execution
    workflow.add_conditional_edges(
        "executor",
        check_execution_status,
        {
            "execution_success": "result_validator",
            "retry_recovery": "recovery",
            "execution_failed": END
        }
    )

    # Recovery loops back to code execution
    workflow.add_edge("recovery", "executor")

    workflow.add_edge("result_validator", "visualization")
    workflow.add_edge("visualization", "insights")
    workflow.add_edge("insights", END)

    return workflow.compile()

analysis_graph = build_analysis_graph()
