import json
import re
from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate
from app.core.llm import call_gemini_llm
from app.graph.state import AnalysisState
from app.graph.agents.base import BaseAgent

GENERAL_RESPONDER_PROMPT = """
You are a friendly, helpful, and concise AI Assistant in a data analytics workspace.
The user asked a general question, greeting, or casual query that is not a direct query on their dataset.

Active Dataset Name & Columns:
{dataset_profile_summary}

Conversation History:
{conversation_history}

User Question:
"{user_query}"

Instructions:
1. For greetings (e.g. "hi", "hello", "hey", "who are you"):
   - Respond simply, warmly, and naturally in 1 to 2 short sentences (e.g., "Hello! I am your AI Data Analyst assistant. How can I help you today? Feel free to ask about your dataset or any general questions.").
   - Do NOT output long summaries, bullet points of columns, or detailed feature lists for simple greetings.
2. For general questions (e.g. "What is machine learning?", "What is ROI?"):
   - Provide a clean, direct, and concise explanation in a natural conversational tone.
3. Keep the response simple and direct. Do NOT output "Key Findings", "Data Interpretation", or complex analytics sections.
4. Optionally suggest 1 to 2 short, relevant follow-up questions if helpful.

Return JSON strictly matching this schema:
{{
  "response": "Simple, clean conversational response",
  "follow_up_questions": ["Short question 1", "Short question 2"]
}}
"""

class GeneralResponderAgent(BaseAgent):
    """
    General Responder Agent: Handles general chit-chat, greetings, technical/statistical
    explanations, and non-dataset queries directly without executing Pandas code.
    """
    name = "GeneralResponderAgent"
    role = "Conversational AI Analyst & General Knowledge Specialist"
    description = "Answers non-dataset and general knowledge queries directly."

    def __init__(self):
        super().__init__(
            name="GeneralResponderAgent",
            role="Conversational AI Analyst & General Knowledge Specialist",
            description="Provides intelligent conversational answers for general inquiries."
        )
        self.prompt_template = PromptTemplate(
            template=GENERAL_RESPONDER_PROMPT,
            input_variables=["dataset_profile_summary", "conversation_history", "user_query"]
        )

    def invoke(self, state: AnalysisState) -> Dict[str, Any]:
        user_query = state.get("user_query", "")
        profile_summary = state.get("dataset_profile_summary") or "No dataset summary available."
        hist_summary = state.get("conversation_history_summary") or "No prior history."

        prompt_text = self.prompt_template.format(
            dataset_profile_summary=profile_summary,
            conversation_history=hist_summary,
            user_query=user_query
        )

        response_text = None
        follow_ups = []

        llm_output = call_gemini_llm(
            prompt_text,
            temperature=0.3,
            custom_api_key=state.get("gemini_api_key")
        )

        if llm_output:
            try:
                json_match = re.search(r"\{.*\}", llm_output, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    response_text = parsed.get("response")
                    follow_ups = parsed.get("follow_up_questions") or []
            except Exception as e:
                print(f"[GeneralResponder] JSON parse error: {e}")
                response_text = llm_output.strip()

        # Fallback if LLM was unavailable
        if not response_text:
            q_low = user_query.lower().strip()
            if any(g in q_low for g in ["hi", "hello", "hey", "who are you"]):
                response_text = (
                    "Hello! I am your AI Data Analyst assistant. How can I help you today? "
                    "Feel free to ask about your dataset or any general questions."
                )
                follow_ups = [
                    "What are the key metrics in this dataset?",
                    "Show an overview summary of the data"
                ]
            else:
                response_text = (
                    f"Thank you for your question. I am ready to assist you. If you have questions about your dataset "
                    f"or would like to run an analysis, feel free to ask!"
                )
                follow_ups = [
                    "Summarize this dataset",
                    "What columns are available?"
                ]

        query_intent = state.get("query_intent") or {}
        query_intent.update({
            "intent": "General Query",
            "is_dataset_related": False,
            "presentation_type": "conversational"
        })

        return {
            "insights": response_text,
            "data_interpretation": response_text,
            "key_findings": [],
            "strategic_recommendations": [],
            "follow_up_questions": follow_ups,
            "query_intent": query_intent,
            "chart_config": None,
            "result_table": None,
            "analysis_plan": None,
            "generated_code": None,
            "validation_result": True,
            "execution_error": None,
            "final_status": "SUCCESS"
        }

general_responder_agent = GeneralResponderAgent()
general_responder_node = general_responder_agent
