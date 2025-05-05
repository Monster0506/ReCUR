from typing import Protocol

from core.models import Response
from core.llm import LLM


class _PromptProvider(Protocol):
    async def get_prompt(self) -> str: ...


class BaseResponder:
    def __init__(self, llm: LLM, temperature: float):
        self.llm = llm
        self.temperature = temperature

    async def __call__(self, user_prompt: str) -> Response:
        print("Generating base response...")
        text = await self.llm.generate(user_prompt, self.temperature)
        return Response(text=text, provenance={"agent": "base"})
