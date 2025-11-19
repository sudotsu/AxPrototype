"""
LLM client wrapper and utilities.
"""

import os
import sys
from typing import Optional
from openai import OpenAI


_client: Optional[OpenAI] = None


def get_llm_client() -> OpenAI:
    """
    Get or initialize OpenAI client.

    Returns:
        OpenAI client instance

    Raises:
        SystemExit: If client initialization fails
    """
    global _client
    if _client is None:
        if "--smoke-governance" in sys.argv:
            raise RuntimeError("LLM client not initialized (smoke mode)")
        try:
            _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        except Exception as e:
            raise SystemExit(f"[ERROR] OpenAI init failed: {e}")
    return _client


def call_llm(
    system_text: str,
    user_text: str,
    temperature: float = 0.4,
    max_tokens: int = 1600,
    model: Optional[str] = None
) -> str:
    """
    Call LLM with system and user prompts.

    Args:
        system_text: System prompt
        user_text: User prompt
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        model: Model name (uses TIER env var if not provided)

    Returns:
        Generated text

    Raises:
        RuntimeError: If client not initialized
    """
    client = get_llm_client()

    # Determine model from TIER if not provided
    if model is None:
        tier = os.getenv("TIER", "DEV").upper()
        model_map = {
            "DEV": os.getenv("MODEL_DEV", "gpt-4o-mini"),
            "PREP": os.getenv("MODEL_PREP", "gpt-4o-turbo"),
            "CLIENT": os.getenv("MODEL_CLIENT", "gpt-4o"),
        }
        model = model_map.get(tier, "gpt-4o-mini")

    r = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_text},
        ],
    )
    return r.choices[0].message.content

