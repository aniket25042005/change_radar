import httpx
from typing import Any, Dict, List, Optional
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL

def check_ollama_status(base_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Checks if local Ollama daemon is reachable and lists installed models.
    """
    target_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
    try:
        with httpx.Client(timeout=1.5) as client:
            resp = client.get(f"{target_url}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", []) if "name" in m]
                return {
                    "online": True,
                    "base_url": target_url,
                    "default_model": OLLAMA_MODEL,
                    "available_models": models,
                    "message": f"Connected to local Ollama on {target_url}.",
                }
    except Exception as e:
        pass

    return {
        "online": False,
        "base_url": target_url,
        "default_model": OLLAMA_MODEL,
        "available_models": [],
        "message": f"Local Ollama is offline at {target_url}. Run 'ollama serve' or 'ollama run {OLLAMA_MODEL}' to activate local LLM.",
    }

def generate_with_ollama(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: float = 20.0,
) -> Optional[str]:
    """
    Invokes local Ollama inference via HTTP API.
    Returns generated response string, or None if Ollama is unreachable.
    """
    target_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
    target_model = model or OLLAMA_MODEL

    payload: Dict[str, Any] = {
        "model": target_model,
        "prompt": prompt,
        "stream": False,
    }
    if system_prompt:
        payload["system"] = system_prompt

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(f"{target_url}/api/generate", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data.get("response", "").strip()
                if text:
                    return text
    except Exception:
        # Fall back to deterministic AST reasoning
        return None

    return None
