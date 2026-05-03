# adapters/ollama_client.py
import json
import re
import requests
from typing import Any, Dict, Optional

OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama3"


class OllamaError(Exception):
    pass


def ollama_generate(prompt: str, model: str = DEFAULT_MODEL, timeout: int = 300) -> Dict[str, Any]:

    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "num_predict": 2048,  # 🔥 Increase output tokens
            "num_ctx": 4096
        },
    }

    try:
        r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise OllamaError(f"Ollama generate failed: {e}")


def extract_text(raw: Dict[str, Any]) -> str:

    text = raw.get("response", "")
    if not text:
        raise OllamaError("Empty response from Ollama")
    return text.strip()


def _extract_first_json_object(text: str) -> Optional[str]:


    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    return m.group(0).strip() if m else None


def parse_structured(text: str) -> Dict[str, Any]:

    try:
        return json.loads(text)
    except Exception:
        maybe = _extract_first_json_object(text)
        if not maybe:
            raise OllamaError("Could not parse JSON from model output")
        try:
            return json.loads(maybe)
        except Exception as e:
            raise OllamaError(f"Could not parse JSON from extracted block: {e}")


def force_json_prompt(event_text: str) -> str:
    return (
        "You are a highly detailed AI operations assistant.\n\n"
        "You MUST respond in STRICT JSON only. No markdown. No extra text. No explanations outside JSON.\n\n"
        "VERY IMPORTANT RULES:\n"
        "- Always provide a COMPLETE and DETAILED answer.\n"
        "- Never shorten explanations.\n"
        "- Never summarize unless explicitly asked.\n"
        "- Do NOT use '...', 'etc', 'and so on', or incomplete endings.\n"
        "- If the user asks for a list (e.g., Top 20, Top 10), you MUST return ALL requested items completely.\n"
        "- If 20 items are requested, return exactly 20 complete items.\n"
        "- Each item must contain a full explanation when appropriate.\n"
        "- Do not stop early.\n"
        "- Ensure the answer is fully finished before ending.\n\n"
        "If the request is a simple informational question:\n"
        "- Provide a detailed multi-paragraph explanation in 'answer_to_user'.\n"
        "- Set next_action to 'NONE'.\n"
        "- steps must be [].\n"
        "- risks must be [].\n\n"
        "If the request requires workflow handling:\n"
        "- Provide structured workflow steps in 'steps'.\n"
        "- Provide realistic risks in 'risks'.\n"
        "- Provide a meaningful 'next_action'.\n\n"
        "Return EXACTLY this JSON structure:\n"
        "{\n"
        '  "summary": "Detailed 1-2 sentence summary of the response",\n'
        '  "answer_to_user": "Very detailed and complete answer here",\n'
        '  "answer_items": [],\n'
        '  "next_action": "NONE or actionable next step",\n'
        '  "steps": [],\n'
        '  "risks": []\n'
        "}\n\n"
        "User Request:\n"
        + event_text
    )


