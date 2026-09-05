import json
import re
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from app.graph.state import AnalysisState
from app.graph.prompts.insights import INSIGHTS_PROMPT

def insights_node(state: AnalysisState) -> Dict[str, Any]:
    user_query = state.get("user_query", "")
    result_summary = state.get("result_summary", "")
    
    insights_text = ""
    recommendations = []
    followups = []

    api_key = settings.GEMINI_API_KEY
    if api_key:
        try:
            llm = ChatGoogleGenerativeAI(
                model=settings.LLM_MODEL,
                google_api_key=api_key,
                temperature=0.2
            )
            prompt = INSIGHTS_PROMPT.format(
                user_query=user_query,
                result_summary=result_summary
            )
            response = llm.invoke(prompt)
            json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                insights_text = parsed.get("insights", "")
                recommendations = parsed.get("recommendations", [])
                followups = parsed.get("follow_up_questions", [])
        except Exception as e:
            print(f"Insights Node LLM Error: {e}")

    if not insights_text:
        insights_text = f"Analysis completed successfully. Derived results from query: '{user_query}'."
        recommendations = ["Review regional/category performance variances.", "Optimize inventory or resource allocation based on top performers."]
        followups = ["Show monthly trend for top performer", "Compare top 2 categories", "Analyze overall profit margin"]

    return {
        "insights": insights_text,
        "recommendations": recommendations,
        "follow_up_questions": followups,
        "final_status": "SUCCESS"
    }
