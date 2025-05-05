from __future__ import annotations

from core.models import Response
from core.llm import LLM


class AlternativeResponder:
    def __init__(self, llm: LLM, temperature: float):
        self.llm = llm
        self.temperature = temperature

    async def generate(self, user_prompt: str, current_best: str, idx: int) -> Response:
        print(f"Generating alternative {idx+1}...")
        prompt = (
            f"{user_prompt}\n\nCurrent best answer:\n{current_best}\n\n"
            "Generate an alternative that may be better."
        )
        text = await self.llm.generate(prompt, self.temperature)
        return Response(text=text, provenance={"agent": f"alt_{idx}"})
