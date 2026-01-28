"""LLM API client for generating mnemonic stories."""

import json
import urllib.request
import urllib.error


SYSTEM_PROMPT = (
    "You are a mnemonic story writer for learning Chinese/Japanese characters "
    "using the Heisig method. Given a character's keyword and its components, "
    "write a vivid, memorable 1-3 sentence story that connects the component "
    "meanings to the keyword. Be creative and use sensory details."
)


def _build_user_prompt(char: str, info: dict) -> str:
    keyword = info.get("keyword", char)
    components = info.get("components_detail", info.get("decomposition", ""))
    spatial = info.get("spatial", "")
    parts = [f"Character: {char}", f"Keyword: {keyword}"]
    if components:
        parts.append(f"Components: {components}")
    if spatial:
        parts.append(f"Layout: {spatial}")
    parts.append("Write a short mnemonic story.")
    return "\n".join(parts)


def generate_story(char: str, info: dict, provider: str, api_key: str, model: str) -> str:
    """Call LLM API and return the generated story text."""
    if not api_key:
        return ""

    user_prompt = _build_user_prompt(char, info)

    if provider == "openai":
        return _call_openai(api_key, model, user_prompt)
    elif provider == "gemini":
        return _call_gemini(api_key, model, user_prompt)
    else:
        return _call_anthropic(api_key, model, user_prompt)


def _call_anthropic(api_key: str, model: str, user_prompt: str) -> str:
    url = "https://api.anthropic.com/v1/messages"
    body = json.dumps({
        "model": model,
        "max_tokens": 256,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_prompt}],
    }).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["content"][0]["text"]
    except (urllib.error.URLError, KeyError, IndexError) as e:
        return f"(LLM error: {e})"


def _call_gemini(api_key: str, model: str, user_prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = json.dumps({
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"maxOutputTokens": 256},
    }).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except (urllib.error.URLError, KeyError, IndexError) as e:
        return f"(LLM error: {e})"


def _call_openai(api_key: str, model: str, user_prompt: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    body = json.dumps({
        "model": model,
        "max_tokens": 256,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except (urllib.error.URLError, KeyError, IndexError) as e:
        return f"(LLM error: {e})"
