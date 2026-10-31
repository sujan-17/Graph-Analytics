import json
import re
from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate
from app.core.llm import call_gemini_llm
from app.graph.state import AnalysisState
from app.graph.agents.base import BaseAgent
from app.graph.prompts.planner import PLANNER_PROMPT

def synthesize_plan_from_intent(intent: Dict[str, Any], user_query: str) -> List[str]:
    """
    Deterministic zero-latency plan synthesizer.
    Translates structured query intent into an explainable, step-by-step
    analytical execution sequence in <1ms without an LLM round-trip.
    """
    if not intent:
        return []

    filters = intent.get("filters") or {}
    time_range = intent.get("time_range")
    group_by = intent.get("group_by") or []
    metrics = intent.get("metrics") or ([intent.get("metric")] if intent.get("metric") else [])
    intent_type = (intent.get("intent") or "").lower()

    if not (filters or group_by or metrics or intent_type):
        return []

    steps = ["1. Inspect pre-loaded dataset schema and verify requested columns."]
    step_num = 2

    if filters:
        filter_descs = [f"'{k}' == '{v}'" for k, v in filters.items()]
        steps.append(f"{step_num}. Filter DataFrame df where {', '.join(filter_descs)}.")
        step_num += 1

    if time_range:
        steps.append(f"{step_num}. Parse datetime column and filter for time horizon: {time_range}.")
        step_num += 1

    if group_by and metrics:
        steps.append(f"{step_num}. Group by dimension(s) {group_by} with as_index=False.")
        step_num += 1
        steps.append(f"{step_num}. Aggregate target metric(s) {metrics} using appropriate statistical aggregation.")
        step_num += 1
        steps.append(f"{step_num}. Sort results descending by primary metric and store final output in variable `result`.")
    elif group_by:
        steps.append(f"{step_num}. Group by {group_by} and calculate record frequencies.")
        step_num += 1
        steps.append(f"{step_num}. Sort results and store final output in variable `result`.")
    elif metrics:
        steps.append(f"{step_num}. Compute overall summary metric(s) for {metrics}.")
        step_num += 1
        steps.append(f"{step_num}. Format summary into a single-row DataFrame and assign to variable `result`.")
    elif intent_type in ["filtering", "lookup", "detail"]:
        steps.append(f"{step_num}. Select matching records satisfying filter criteria.")
        step_num += 1
        steps.append(f"{step_num}. Retain dimension columns and store top matching records in variable `result`.")
    else:
        steps.append(f"{step_num}. Execute data transformation for query '{user_query}'.")
        step_num += 1
        steps.append(f"{step_num}. Store final output table in variable `result`.")

    return steps

class PlannerAgent(BaseAgent):
    """
    Analysis Planner Agent: Decomposes complex user queries into an explainable,
    transparent sequence of logical execution steps (filtering, grouping,
    aggregations, sorting, and output formatting).
    """
    name = "PlannerAgent"
    role = "Analytical Strategy & Step-by-Step Planner Agent"
    description = "Formulates sequential analysis steps for data computation and explainability."

    def __init__(self):
        super().__init__(
            name="PlannerAgent",
            role="Analytical Strategy & Step-by-Step Planner Agent",
            description="Decomposes analytical questions into verifiable planning sequences using LangChain."
        )
        self.prompt_template = PromptTemplate(
            template=PLANNER_PROMPT,
            input_variables=["dataset_profile_summary", "query_intent", "user_query"]
        )

    def invoke(self, state: AnalysisState) -> Dict[str, Any]:
        user_query = state.get("user_query", "")
        profile_summary = state.get("dataset_profile_summary", "")
        intent = state.get("query_intent", {})

        # Zero-latency fast path: synthesize explainable plan directly from parsed intent
        plan_list = synthesize_plan_from_intent(intent, user_query)

        # Fallback to LLM only if intent is empty or ambiguous
        if not plan_list:
            prompt_text = self.prompt_template.format(
                dataset_profile_summary=profile_summary,
                query_intent=json.dumps(intent),
                user_query=user_query
            )
            llm_output = call_gemini_llm(prompt_text, temperature=0.1, custom_api_key=state.get("gemini_api_key"))
            if llm_output:
                try:
                    json_match = re.search(r"\{.*\}", llm_output, re.DOTALL)
                    if json_match:
                        plan_data = json.loads(json_match.group(0))
                        plan_list = plan_data.get("plan", [])
                except Exception as e:
                    print(f"Planner Agent JSON Parse Error: {e}")

        if not plan_list:
            plan_list = [
                "1. Inspect pre-loaded dataset columns and data types.",
                "2. Filter DataFrame based on query criteria.",
                "3. Perform grouping and metric aggregation.",
                "4. Sort results and store final output in variable `result`."
            ]

        return {
            "analysis_plan": plan_list
        }

# Agent instance for LangGraph StateGraph & backward-compatible node export
planner_agent = PlannerAgent()
planner_node = planner_agent
