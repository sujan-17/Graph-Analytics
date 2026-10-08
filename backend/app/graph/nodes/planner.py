import json
import re
from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from app.core.llm import call_gemini_llm
from app.graph.state import AnalysisState
from app.graph.agents.base import BaseAgent
from app.graph.prompts.planner import PLANNER_PROMPT

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
        
        plan_list = []
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
