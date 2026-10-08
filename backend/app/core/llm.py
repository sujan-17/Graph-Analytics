from typing import Optional, List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.config import settings

def get_gemini_chat_model(temperature: float = 0.1, custom_api_key: Optional[str] = None) -> Optional[ChatGoogleGenerativeAI]:
    """
    Returns an initialized LangChain ChatGoogleGenerativeAI model instance.
    """
    api_key = custom_api_key or settings.GEMINI_API_KEY
    if not api_key:
        return None

    primary_model = settings.LLM_MODEL or "gemini-flash-latest"
    return ChatGoogleGenerativeAI(
        model=primary_model,
        google_api_key=api_key,
        temperature=temperature,
        max_retries=1
    )

def call_gemini_llm(prompt: str, temperature: float = 0.1, custom_api_key: Optional[str] = None) -> Optional[str]:
    """
    Invokes Gemini with automatic model fallback (gemini-flash-latest -> gemini-3.1-flash-lite)
    via LangChain ChatGoogleGenerativeAI and extracts string response.
    """
    api_key = custom_api_key or settings.GEMINI_API_KEY
    if not api_key:
        return None

    primary_model = settings.LLM_MODEL or "gemini-flash-latest"
    candidates = ["gemini-flash-latest", primary_model, "gemini-3.1-flash-lite"]
    seen = set()
    models_to_try = [m for m in candidates if not (m in seen or seen.add(m))]

    last_error = None
    for model_name in models_to_try:
        try:
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=temperature,
                max_retries=1
            )
            # LCEL invocation: prompt string -> LLM -> StrOutputParser
            chain = llm | StrOutputParser()
            clean_text = chain.invoke(prompt).strip()
            if clean_text:
                return clean_text
        except Exception as e:
            last_error = e
            continue

    if last_error:
        print(f"All Gemini model candidates failed. Last error: {last_error}")
    return None
