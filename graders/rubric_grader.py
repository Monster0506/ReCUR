from __future__ import annotations

from typing import Optional

from core.llm import LLM
from core.models import Response


class RubricGrader:
    """
    Scores responses on a 0‑100 scale.

    *If an LLM instance is supplied,* we ask it to grade; otherwise we fall back
    to a heuristic that considers length *and* lexical richness.
    """

    def __init__(
        self,
        rubric: str | None = None,
        llm: Optional[LLM] = None,
        temperature: float = 0.4,
    ):
        self.rubric = (
            rubric
            or (
                "You are a strict grader. Score the answer from 0‑100 where "
                "clarity and structure are 40 points, relevance is 40 points, "
                "and factual correctness is 20 points. "
            )
        ) + "\nReturn ONLY the number."
        self.llm = llm
        self.temperature = temperature

    # --------------------------------------------------------------------- #
    # Public helpers
    # --------------------------------------------------------------------- #
    async def score(self, answer: str, prompt: str) -> float:
        print("Grading...")
        """Return a numeric score for *answer*."""
        if self.llm is None:  # offline heuristic
            print("Grading with heuristic...")
            return self._heuristic(answer)
        print("Grading with LLM...")

        ask = (
            f"User prompt:\n{prompt}\n\nAnswer to grade:\n{answer}\n\n" f"{self.rubric}"
        )
        text = await self.llm.generate(ask, temperature=self.temperature)
        # keep first integer found
        for tok in text.split():
            if tok.isdigit():
                return float(tok)
        # fallback
        return self._heuristic(answer)

    async def compare(
        self, current: Response, challenger: Response, prompt: str
    ) -> bool:
        """Return True if *challenger* beats *current*."""
        if current.score == 0:  # score lazily
            current.score = await self.score(current.text, prompt)
        challenger.score = await self.score(challenger.text, prompt)
        return challenger.score > current.score

    # --------------------------------------------------------------------- #
    # Private
    # --------------------------------------------------------------------- #
    @staticmethod
    def _heuristic(text: str) -> float:
        words = text.split()
        unique = len(set(words))
        return min(100.0, 0.6 * len(words) ** 0.5 + 0.4 * unique**0.5)
