"""
HELIOS Backend — Multi-Provider LLM Proxy
Ports the provider dispatch logic from useAI.ts to Python.
Supports: OpenAI, Claude, Kimi (DeepInfra), GLM.
"""

import httpx
import json
from typing import Optional

from backend.config import PROVIDER_CONFIGS


async def call_llm(
    provider: str,
    api_key: str,
    system_prompt: str,
    messages: list[dict],
    model: Optional[str] = None,
) -> str:
    """
    Send a chat completion request to the user's chosen LLM provider.

    Args:
        provider: Provider ID ("openai", "claude", "kimi", "glm")
        api_key: User's decrypted API key for this provider
        system_prompt: Full system prompt with scientific KB + memories
        messages: Conversation history [{role, content}, ...]
        model: Optional model override

    Returns:
        Raw text response from the LLM.

    Raises:
        httpx.HTTPStatusError: On API errors
        ValueError: On unknown provider
    """
    config = PROVIDER_CONFIGS.get(provider)
    if not config:
        raise ValueError(f"Unknown provider: {provider}")

    base_url = config["base_url"]
    model_name = model or config["model"]

    async with httpx.AsyncClient(timeout=60.0) as client:
        if provider == "claude":
            return await _call_claude(client, base_url, api_key, model_name, system_prompt, messages)
        else:
            return await _call_openai_compatible(client, base_url, api_key, model_name, system_prompt, messages)


async def _call_claude(
    client: httpx.AsyncClient,
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    messages: list[dict],
) -> str:
    """Call Anthropic Claude API (non-OpenAI format)."""
    response = await client.post(
        base_url,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [
                {"role": m["role"], "content": m["content"]}
                for m in messages
            ],
        },
    )
    response.raise_for_status()
    data = response.json()
    return data["content"][0]["text"]


async def _call_openai_compatible(
    client: httpx.AsyncClient,
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    messages: list[dict],
) -> str:
    """Call OpenAI-compatible API (OpenAI, Kimi via DeepInfra, GLM)."""
    all_messages = [
        {"role": "system", "content": system_prompt},
        *[{"role": m["role"], "content": m["content"]} for m in messages],
    ]

    response = await client.post(
        base_url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": all_messages,
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def parse_ai_response(raw_text: str) -> dict:
    """
    Parse LLM response into message + visual cards.
    The LLM is instructed to return JSON: { message, visualCards }.
    Falls back to raw text if JSON parsing fails.

    Ported from useAI.ts parseAIResponse() (lines 269-292).
    """
    try:
        # Try direct JSON parse
        parsed = json.loads(raw_text)
        return {
            "message": parsed.get("message", raw_text),
            "visual_cards": parsed.get("visualCards", []),
        }
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code block
    if "```json" in raw_text:
        try:
            json_block = raw_text.split("```json")[1].split("```")[0].strip()
            parsed = json.loads(json_block)
            return {
                "message": parsed.get("message", raw_text),
                "visual_cards": parsed.get("visualCards", []),
            }
        except (json.JSONDecodeError, IndexError):
            pass

    # Fallback: treat entire response as message, no cards
    return {
        "message": raw_text,
        "visual_cards": [],
    }
