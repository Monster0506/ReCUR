def heuristic_rounds(prompt: str) -> int:
    words = len(prompt.split())
    if words < 50:
        return 1
    if words < 200:
        return 2
    return 3
