from __future__ import annotations

from typing import List

from core.models import Response
from graders.rubric_grader import RubricGrader


class FinalSelector:
    def __init__(self, grader: RubricGrader):
        self.grader = grader

    async def select(self, candidates: List[Response]) -> Response:
        print("Selecting the best response...")
        best = max(candidates, key=lambda r: r.score)
        return best
