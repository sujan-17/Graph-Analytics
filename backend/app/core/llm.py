from typing import Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

def call_gemini_llm(prompt: str, temperature: float = 0.1, custom_api_key: Optional[str] = None) -> Optional[str]:
    """
    Invokes Gemini with automatic model fallback (gemini-flash-latest -> gemini-3.1-flash-lite -> gemini-2.5-flash)
    and handles content unpacking for both string and list response formats.
    """
    api_key = custom_api_key or settings.GEMINI_API_KEY
    if not api_key:
        return None

    # Priority list of model candidates
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
            response = llm.invoke(prompt)
            content = response.content

            if isinstance(content, list):
                text = "".join([c if isinstance(c, str) else str(c.get("text", c)) for c in content])
            else:
                text = str(content)

            clean_text = text.strip()
            if clean_text:
                return clean_text
        except Exception as e:
            last_error = e
            continue

    if last_error:
        print(f"All Gemini model candidates failed. Last error: {last_error}")
    return None
