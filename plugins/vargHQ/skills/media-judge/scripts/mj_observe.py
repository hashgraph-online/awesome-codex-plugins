"""Turn a judge's observations into a verdict. The model reports what it sees, code decides."""
from __future__ import annotations

import json
from pathlib import Path

CHECKS = ["misspelled", "hard_to_read", "most_words", "equal_elements", "no_subject", "covered", "broken", "melted"]


def fails(o: dict, word_limit: int = 18) -> list[str]:
    out = [k for k in ("misspelled", "hard_to_read", "equal_elements", "no_subject", "covered", "broken", "melted") if o.get(k)]
    try:
        if float((o.get("most_words") or {}).get("words", 0) or 0) > word_limit:
            out.append("most_words")
    except (TypeError, ValueError):
        pass
    return sorted(out)


def tally(paths: list[str]) -> dict:
    """Several runs of one take: a failure counts when most runs report it."""
    runs = [fails(json.loads(Path(p).read_text())) for p in paths]
    n = len(runs)
    return {"runs": n, "fails": sorted(k for k in CHECKS if sum(k in r for r in runs) * 2 > n), "per_run": runs}


def compare(a: dict, b: dict, margin: int = 2) -> dict:
    """A take wins only by a clear margin. Anything closer is a tie, and a tie is an honest answer."""
    na, nb = len(a["fails"]), len(b["fails"])
    winner = "A" if nb - na >= margin else ("B" if na - nb >= margin else "tie")
    return {"A": a["fails"], "B": b["fails"], "margin": margin, "winner": winner}
