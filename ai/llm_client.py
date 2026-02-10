import json
import re
from typing import Any, AsyncIterator, Dict, List, Optional, Union
import httpx
from ai.config import (
    OLLAMA_URL_GENERATE,
    OLLAMA_URL_CHAT,
    DEFAULT_MODEL as MODEL,
    SAFE_FALLBACK
)


class LLMResponse:
    """Mock-like class for consistent response handling across LLM interfaces."""
    def __init__(self, content: str):
        self.content = content

class LLMChunk:
    """Mock-like class for consistent streaming chunk handling."""
    def __init__(self, content: str):
        self.content = content


class LocalChatOllama:
    """
    A minimal wrapper around Ollama to mimic ChatOpenAI's interface
    used in the LangGraph agent and streaming endpoints.
    """

    def __init__(self, model: str = None, temperature: float = 0, streaming: bool = False):
        self.model = model if model else MODEL  # Use provided model or fallback to default
        self.temperature = temperature
        self.streaming = streaming

    def invoke(self, messages: List[Any], **kwargs) -> Any:
        """
        Synchronous call to Ollama (mimics ChatOpenAI.invoke)
        """
        prompt = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature or 0.1,
                "repeat_penalty": 1.2,
                "top_k": 40,
                "top_p": 0.9,
                "num_predict": 1024
            },
            "stop": ["User:", "QUESTION:", "ANSWER:"]
        }
        
        try:
            with httpx.Client() as client:
                response = client.post(OLLAMA_URL_GENERATE, json=payload, timeout=60)
                response.raise_for_status()
                content = response.json().get("response", "")
                return LLMResponse(content)
        except Exception as e:
            print(f"Error in LocalChatOllama.invoke: {e}")
            return LLMResponse(SAFE_FALLBACK)

    async def astream(self, messages: List[Any], **kwargs) -> AsyncIterator[Any]:
        """
        Asynchronous streaming call to Ollama (mimics ChatOpenAI.astream)
        """
        prompt = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": self.temperature or 0.1,
                "repeat_penalty": 1.2,
                "top_k": 40,
                "top_p": 0.9,
                "num_predict": 1024
            },
            "stop": ["User:", "QUESTION:", "ANSWER:"]
        }
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", OLLAMA_URL_GENERATE, json=payload, timeout=180) as response:
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        chunk = json.loads(line)
                        if "response" in chunk:
                            yield LLMChunk(chunk["response"])
                        if chunk.get("done"):
                            break
        except Exception as e:
            print(f"Error in LocalChatOllama.astream: {e}")
            yield LLMChunk(" Error connecting to local LLM.")


def _clean_text(text: str) -> str:
    """
    Normalize LLM output safely:
    - normalize whitespace
    - soften unsafe phrasing
    - ensure sentence completeness
    """

    if not text:
        return SAFE_FALLBACK

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Soften unsafe medical phrasing
    replacements = {
        "you have": "the results suggest",
        "you might have": "there may be",
        "this indicates": "this may suggest",
        "diagnosis": "interpretation",
        "disease": "condition",
        "treatment": "clinical management",
        "medication": "medical therapy",
    }

    for bad, safe in replacements.items():
        text = re.sub(bad, safe, text, flags=re.IGNORECASE)

    # ✅ Ensure sentence completeness
    if text and text[-1] not in ".!?":
        text += " Further clinical review is advised."

    return text


def generate_ai_summary(lab_results: list[dict]) -> str:
    """
    Generate a safe, non-diagnostic AI summary.
    """

    if not lab_results:
        return "No abnormal or critical lab findings were detected."

    findings = "\n".join(
        f"- {lab['test_name']} is {lab['status']} "
        f"(value: {lab['value']} {lab['unit']})"
        for lab in lab_results
    )

    prompt = f"""
You are a clinical explanation assistant.

STRICT RULES:
- Do NOT diagnose diseases
- Do NOT name specific medical conditions
- Do NOT recommend treatments
- Use cautious, observational language
- Always advise clinician review
- Do Not Involve the above mentioned rules in your answer

LAB FINDINGS:
{findings}

Provide a concise explanation in 2–3 complete sentences.
"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 180,
            "temperature": 0.2,
            "top_p": 0.9
        },
        "stop": ["\n\n", "###"]
    }

    try:
        with httpx.Client() as client:
            response = client.post(
                OLLAMA_URL_GENERATE,
                json=payload,
                timeout=90
            )
            response.raise_for_status()

            raw_text = response.json().get("response", "")
            return _clean_text(raw_text)

    except Exception:
        return SAFE_FALLBACK



