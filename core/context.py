from pathlib import Path
from typing import List


def chunk_text(text: str, size: int) -> List[str]:
    return [text[i : i + size] for i in range(0, len(text), size)]


def load_file_fragments(paths: List[Path], chunk_size: int = 1000) -> List[str]:
    fragments: List[str] = []
    for p in paths:
        raw = p.read_text(encoding="utf-8")
        fragments.extend(chunk_text(raw, chunk_size))
    return fragments
