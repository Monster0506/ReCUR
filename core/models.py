from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass(slots=True)
class Response:
    text: str
    score: float = 0.0
    provenance: Dict[str, Any] | None = None
