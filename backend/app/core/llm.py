from typing import Optional, List, Dict, Any, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.config import settings

# Global connection-pooled cache for initialized ChatGoogleGenerativeAI instances
_chat_model_cache: Dict[Tuple[str, float, str], ChatGoogleGenerativeAI] = {}

def get_gemini_chat_model(
    temperature: float = 0.1,
    custom_api_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> Optional[ChatGoogleGenerativeAI]:
    """
    Returns a cached, warm LangChain ChatGoogleGenerativeAI instance to reuse
    persistent HTTP/2 connections and avoid TLS re-handshakes.
    """
    api_key = custom_api_key or settings.GEMINI_API_KEY
    if not api_key:
        return None

    primary_model = model_name or settings.LLM_MODEL or "gemini-2.5-flash"
    cache_key = (primary_model, float(temperature), api_key)
    if cache_key not in _chat_model_cache:
        _chat_model_cache[cache_key] = ChatGoogleGenerativeAI(
            model=primary_model,
            google_api_key=api_key,
            temperature=temperature,
            max_retries=1
        )
    return _chat_model_cache[cache_key]

def call_gemini_llm(prompt: str, temperature: float = 0.1, custom_api_key: Optional[str] = None) -> Optional[str]:
    """
    Invokes Gemini using warm connection-pooled client with fast fallback
    and extracts string response robustly.
    """
    api_key = custom_api_key or settings.GEMINI_API_KEY
    if not api_key:
        return None

    primary_model = settings.LLM_MODEL or "gemini-2.5-flash"
    candidates = [primary_model, "gemini-2.5-flash", "gemini-3.5-flash", "gemini-flash-latest"]
    seen = set()
    models_to_try = [m for m in candidates if not (m in seen or seen.add(m))]

    last_error = None
    for model_name in models_to_try:
        try:
            llm = get_gemini_chat_model(temperature=temperature, custom_api_key=api_key, model_name=model_name)
            if not llm:
                continue

            response = llm.invoke(prompt)
            content = getattr(response, "content", response)
            if isinstance(content, str):
                clean_text = content.strip()
            elif isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, str):
                        parts.append(item)
                    elif isinstance(item, dict) and "text" in item:
                        parts.append(item["text"])
                clean_text = "".join(parts).strip()
            else:
                clean_text = str(content).strip()

            if clean_text:
                return clean_text
        except Exception as e:
            last_error = e
            continue

    if last_error:
        print(f"All Gemini model candidates failed. Last error: {last_error}")
    return None
