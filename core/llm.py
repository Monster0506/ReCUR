from __future__ import annotations


import asyncio
import os
from abc import ABC, abstractmethod
from typing import Final, List

from google import (
    genai,
)

from google.genai import types

from .utils import async_backoff

DEFAULT_TEMP: Final = 0.4


"""
Async wrapper around the `google‑genai` SDK.

Docs: https://googleapis.github.io/python-genai/
"""


class LLM(ABC):
    """Abstract async LLM interface."""

    @abstractmethod
    async def generate(self, prompt: str, temperature: float = DEFAULT_TEMP) -> str: ...


class GoogleGenaiLLM(LLM):
    """
    Google Gen AI SDK implementation.

    * Uses the Gemini Developer API when `GOOGLE_API_KEY` is set.
    * Model defaults to `gemini-2.0-flash-001`, the public ID for Gemini 2 Flash.
    """

    def __init__(
        self,
        model: str = "gemini-2.0-flash-001",
        api_key: str | None = None,
        fragments: List[str] | None = None,
    ):
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Set GOOGLE_API_KEY env‑var or pass api_key explicitly for google‑genai"
            )

        self.client = genai.Client(api_key=api_key)
        self.fragments = fragments
        if fragments:
            print(f"Loaded large context of {len(fragments)} fragments")

        self.model_name = model

    async def generate(self, prompt: str, temperature: float = DEFAULT_TEMP) -> str:
        if self.fragments:
            prefix = (
                "\n\nThe user has asked that the following documents be considered:\n\n"
                "They may or may not be relevant.\n\n"
            )
            prefix += "\n\n".join(f"DOCUMENT FRAGMENT:\n{f}" for f in self.fragments)
            prompt = f"{prefix}\n\nUSER PROMPT:\n{prompt}"

        async def _inner() -> str:
            response = self.client.models.generate_content(  # sync → wrap
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                ),
            )
            return response.text

        return await async_backoff(_inner)


class EchoLLM(LLM):
    """A trivial stub LLM that simply echoes the prompt (used in tests)."""

    async def generate(self, prompt: str, temperature: float = DEFAULT_TEMP) -> str:
        await asyncio.sleep(0)
        return f"[echo] {prompt}"
