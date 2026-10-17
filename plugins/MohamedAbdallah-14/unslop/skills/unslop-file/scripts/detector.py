"""AI-text detector integration for the live humanize loop.

Loads a small AI-text detector (TMR by default — 125M-param RoBERTa, MIT
license, 99.28% AUROC on RAID) and exposes:

  score_ai_probability(text) -> float in [0, 1]
      Probability that the text is AI-generated, per the cached detector.

  feedback_loop(text, target_probability, max_iterations, ...) -> FeedbackResult
      Humanize, score, and re-humanize with escalating settings until the
      score drops below `target_probability` or the ladder is exhausted.
      Returns a FeedbackResult with final text and per-iteration audit trail.

Design constraints:
  - Heavy deps (torch/transformers) import lazily so the CLI stays fast for
    the 99% path that doesn't need scoring.
  - Graceful degradation: if the model can't be downloaded or the deps are
    missing, `score_ai_probability` raises RuntimeError with a message that
    points at the bootstrap script.
  - Model instance cached in a module-global dict so repeat calls in a single
    session don't pay the ~10-30s load cost twice.
  - Works offline if the HF cache is populated (no network on `score_ai_probability`
    after the first successful load).

Research basis: Cat 05 (detection arms race), Cat 15 (DAMAGE COLING 2025).
The DAMAGE audit showed commercial humanizers score 20-100 points apart from
their marketing claims. The feedback loop is a maintainer diagnostic, not a
release gate — deterministic passes move TMR ~0.0–0.2 pp on fixtures, so
treat scores as a signal, not a pass certificate. TMR ≠ GPTZero/Turnitin.

NOT a silver bullet. Nicks et al. (ICLR 2024): "we advise against continued
reliance on LLM-generated text detectors." Use this as a signal, not a gate.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable


@runtime_checkable
class SurprisalReadingLike(Protocol):
    """Duck type for surprisal readings returned by surprisal_fn."""

    surprisal_stdev: float

    def to_dict(self) -> dict: ...


SurprisalResult = SurprisalReadingLike | float | None

# Available detector backends. Keep this short — each one is a ~500MB-1.5GB
# download. TMR is the default because it's smaller and still competitive
# (99.28% AUROC on RAID). Desklib is optional for the release gate.
DetectorName = Literal["tmr", "desklib"]
DEFAULT_DETECTOR: DetectorName = "tmr"

_MODEL_IDS = {
    "tmr": "Oxidane/tmr-ai-text-detector",
    "desklib": "desklib/ai-text-detector-v1.01",
}

# Per-process cache of loaded scorers. Keys: detector name. Values: callables
# from text -> AI probability in [0, 1].
_SCORER_CACHE: dict[str, Callable[[str], float]] = {}


class DetectorUnavailable(RuntimeError):
    """Raised when the detector can't be loaded (missing deps, no network,
    model not in HF cache, etc.). Caller should catch and degrade gracefully."""


def _bootstrap_hint(model_id: str) -> str:
    return (
        f"\nTo fetch it: python3 -m unslop.scripts.fetch_detectors --detector {model_id}\n"
        "Or set ANTHROPIC_UNSLOP_SKIP_DETECTOR=1 to disable detector feedback."
    )


def _build_tmr_scorer(max_chunks: int = 4) -> Callable[[str], float]:
    """Load the TMR detector and return a text→probability callable."""
    try:
        import torch
        import torch.nn.functional as F
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError as exc:
        raise DetectorUnavailable(
            f"Missing dependency: {exc.name}. Install with:\n"
            "  pip install torch transformers huggingface_hub safetensors"
        ) from exc

    model_id = _MODEL_IDS["tmr"]
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForSequenceClassification.from_pretrained(model_id)
    except Exception as exc:
        raise DetectorUnavailable(
            f"Could not load {model_id}: {exc}.{_bootstrap_hint(model_id)}"
        ) from exc
    model.train(False)

    def score(text: str) -> float:
        tokens = tokenizer.encode(text, add_special_tokens=False)
        chunks: list[str] = []
        if len(tokens) <= 510:
            chunks = [text]
        else:
            for start in range(0, len(tokens), 256):
                chunk_tokens = tokens[start : start + 510]
                decoded = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
                chunks.append(str(decoded))
                if start + 510 >= len(tokens):
                    break
        if max_chunks > 0:
            chunks = chunks[:max_chunks]
        probs: list[float] = []
        for chunk in chunks:
            inputs = tokenizer(
                chunk, return_tensors="pt", truncation=True, max_length=512, padding=True
            )
            with torch.no_grad():
                logits = model(**inputs).logits
                p = F.softmax(logits, dim=-1)
            probs.append(p[0][1].item())
        return sum(probs) / max(len(probs), 1)

    return score


def _build_desklib_scorer(max_chunks: int = 4) -> Callable[[str], float]:
    """Load the Desklib detector (larger, slower, RAID top entry)."""
    try:
        import re

        import torch
        import torch.nn as nn
        from huggingface_hub import hf_hub_download
        from safetensors.torch import load_file as load_safetensors
        from transformers import AutoConfig, AutoModel, AutoTokenizer
    except ImportError as exc:
        raise DetectorUnavailable(
            f"Missing dependency: {exc.name}. Install with:\n"
            "  pip install torch transformers huggingface_hub safetensors"
        ) from exc

    model_id = _MODEL_IDS["desklib"]
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        config = AutoConfig.from_pretrained(model_id)
        encoder = AutoModel.from_config(config)

        class Detector(nn.Module):
            def __init__(self):
                super().__init__()
                self.encoder = encoder
                self.classifier = nn.Linear(config.hidden_size, 1)

            def forward(self, input_ids, attention_mask=None):
                outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
                token_embs = outputs.last_hidden_state
                mask = attention_mask.unsqueeze(-1).float()
                pooled = (token_embs * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
                return self.classifier(pooled)

        model = Detector()
        weights_path = hf_hub_download(model_id, "model.safetensors")
        state = load_safetensors(weights_path)
        renamed = {re.sub(r"^model\.", "encoder.", k): v for k, v in state.items()}
        model.load_state_dict(renamed, strict=False)
    except Exception as exc:
        raise DetectorUnavailable(
            f"Could not load {model_id}: {exc}.{_bootstrap_hint(model_id)}"
        ) from exc
    model.train(False)

    def score(text: str) -> float:
        tokens = tokenizer.encode(text, add_special_tokens=False)
        chunks: list[str] = []
        if len(tokens) <= 510:
            chunks = [text]
        else:
            for start in range(0, len(tokens), 256):
                chunk_tokens = tokens[start : start + 510]
                decoded = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
                chunks.append(str(decoded))
                if start + 510 >= len(tokens):
                    break
        if max_chunks > 0:
            chunks = chunks[:max_chunks]
        probs: list[float] = []
        for chunk in chunks:
            inputs = tokenizer(
                chunk, return_tensors="pt", truncation=True, max_length=512, padding=True
            )
            with torch.no_grad():
                logits = model(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                )
                p = torch.sigmoid(logits)
            probs.append(p[0][0].item())
        return sum(probs) / max(len(probs), 1)

    return score


_BUILDERS: dict[str, Callable[[int], Callable[[str], float]]] = {
    "tmr": _build_tmr_scorer,
    "desklib": _build_desklib_scorer,
}


def score_ai_probability(
    text: str,
    *,
    detector: DetectorName = DEFAULT_DETECTOR,
    max_chunks: int = 4,
) -> float:
    """Return the AI-probability score for `text` in [0, 1].

    Loads the chosen detector on first call; caches it for subsequent calls
    in the same process. Raises DetectorUnavailable on any load failure."""
    if os.environ.get("ANTHROPIC_UNSLOP_SKIP_DETECTOR") == "1":
        raise DetectorUnavailable("ANTHROPIC_UNSLOP_SKIP_DETECTOR=1 set in environment")
    if detector not in _BUILDERS:
        raise ValueError(f"unknown detector {detector!r}; choose from {list(_BUILDERS)}")
    if detector not in _SCORER_CACHE:
        _SCORER_CACHE[detector] = _BUILDERS[detector](max_chunks)
    return _SCORER_CACHE[detector](text)


@dataclass
class IterationRecord:
    """One turn of the feedback loop."""

    iteration: int
    intensity: str
    structural: bool
    ai_probability: float
    ai_isms_after: int
    soul: bool = False
    surprisal_stdev: float | None = None
    surprisal_reading: dict | None = None


@dataclass
class FeedbackResult:
    """Outcome of a full feedback loop."""

    final_text: str
    original_probability: float
    final_probability: float
    iterations: list[IterationRecord] = field(default_factory=list)
    reason_stopped: str = ""

    def to_dict(self) -> dict:
        return {
            "original_probability": round(self.original_probability, 4),
            "final_probability": round(self.final_probability, 4),
            "reduction_pct": (
                round((self.original_probability - self.final_probability) * 100, 1)
                if self.original_probability > 0
                else 0.0
            ),
            "reason_stopped": self.reason_stopped,
            "iterations": [
                {
                    "iteration": r.iteration,
                    "intensity": r.intensity,
                    "structural": r.structural,
                    "soul": r.soul,
                    "ai_probability": round(r.ai_probability, 4),
                    "ai_isms_after": r.ai_isms_after,
                    "surprisal_stdev": (
                        round(r.surprisal_stdev, 4)
                        if r.surprisal_stdev is not None
                        else None
                    ),
                    **({"surprisal_reading": r.surprisal_reading}
                       if r.surprisal_reading is not None else {}),
                }
                for r in self.iterations
            ],
        }


# Escalation ladder: each tuple is (intensity, structural-on, soul-on).
# Step 1: balanced, no structural, no soul — gentlest rewrite.
# Step 2: full, no structural, no soul — adds filler + negative-parallelism + superficial-ing.
# Step 3: full, structural, soul — strongest deterministic mode before anti-detector.
# Step 4: anti-detector — runs lexical_targets gap nudges (requires baseline JSON).
DEFAULT_LADDER: list[tuple[str, bool, bool]] = [
    ("balanced", False, False),
    ("full", False, False),
    ("full", True, True),
    ("anti-detector", True, True),
]

LADDER_AGGRESSIVE: list[tuple[str, bool, bool]] = [
    ("subtle", False, False),
    ("balanced", False, False),
    ("balanced", True, False),
    ("full", True, False),
    ("full", True, True),
    ("anti-detector", True, True),
]


def _resolve_target_probability(
    target_probability: float | dict[str, float], detector: DetectorName
) -> float:
    if isinstance(target_probability, dict):
        return float(target_probability.get(detector, 0.5))
    return float(target_probability)


def feedback_loop(
    text: str,
    *,
    target_probability: float | dict[str, float] = 0.5,
    max_iterations: int = 4,
    detector: DetectorName = DEFAULT_DETECTOR,
    ladder: list[tuple] | None = None,
    score_fn: Callable[[str], float] | None = None,
    humanize_fn: Callable | None = None,
    surprisal_fn: Callable[[str], SurprisalResult] | None = None,
) -> FeedbackResult:
    """Escalate humanize settings until the detector score drops below target.

    At each step the loop: (a) humanizes with the step's intensity and
    structural flag, (b) scores the result with the detector, (c) stops if
    the score is <= target or if the ladder is exhausted. The final text is
    the humanized output of the last step run, regardless of whether it hit
    the target — if the escalation can't fix it, the user still gets the
    best rewrite we could produce.

    `score_fn` and `humanize_fn` are injection points for tests. In
    production they default to `score_ai_probability(..., detector=...)` and
    `humanize_deterministic_with_report` (imported lazily to avoid circular
    import).
    """
    from .humanize import humanize_deterministic_with_report
    from .validate import _count_ai_isms

    if score_fn is None:
        def score_fn(t: str) -> float:  # noqa: E306
            return score_ai_probability(t, detector=detector)

    if humanize_fn is None:
        humanize_fn = humanize_deterministic_with_report

    if ladder is None:
        ladder = DEFAULT_LADDER

    target = _resolve_target_probability(target_probability, detector)
    original_prob = score_fn(text)
    iterations: list[IterationRecord] = []
    current_text = text
    steps = ladder[:max_iterations]

    for i, step in enumerate(steps, start=1):
        # Step tuples can be (intensity, structural) or (intensity, structural, soul).
        # Accept both for backward compatibility with tests that use the old 2-tuple form.
        if len(step) == 2:
            intensity, structural = step
            soul = False
        else:
            intensity, structural, soul = step
        current_text, _report = humanize_fn(
            text, intensity=intensity, structural=structural, soul=soul
        )
        prob = score_fn(current_text)
        surprisal_stdev = None
        surprisal_reading = None
        if surprisal_fn is not None:
            try:
                value = surprisal_fn(current_text)
                if isinstance(value, SurprisalReadingLike):
                    surprisal_stdev = float(value.surprisal_stdev)
                    surprisal_reading = value.to_dict()
                elif value is not None:
                    surprisal_stdev = float(value)
            except Exception:
                pass
        iterations.append(
            IterationRecord(
                iteration=i,
                intensity=intensity,
                structural=structural,
                soul=soul,
                ai_probability=prob,
                ai_isms_after=_count_ai_isms(current_text),
                surprisal_stdev=surprisal_stdev,
                surprisal_reading=surprisal_reading,
            )
        )
        if prob <= target:
            return FeedbackResult(
                final_text=current_text,
                original_probability=original_prob,
                final_probability=prob,
                iterations=iterations,
                reason_stopped=f"target hit at iteration {i} (p_ai={prob:.3f} <= {target})",
            )

    # Ladder exhausted without hitting the target. The deterministic layer
    # has done what it can; the remaining lever is cross-model paraphrase.
    # We surface this as a named recommendation so callers (CLI, skills)
    # can print it verbatim rather than inventing their own wording.
    #
    # Research basis: TempParaphraser (EMNLP 2025, HJJWorks/TempParaphraser)
    # reports ~82.5% average reduction in detector accuracy via LLM paraphrase
    # at elevated temperature — i.e. the next step is structural paraphrase by
    # a different model family, not more deterministic regex. Adversarial
    # Paraphrasing (NeurIPS 2025) and DIPPER (NeurIPS 2023) confirm this
    # pattern. Rewrites may incidentally degrade statistical watermarks.
    #
    # EU AI Act Article 50 (Dec 2025 Code of Practice, August 2026 effective)
    # prohibits watermark removal specifically — we do not recommend that.
    final_prob = iterations[-1].ai_probability if iterations else original_prob
    recommendation = (
        f"ladder exhausted after {len(iterations)} iteration(s); "
        f"target {target} not reached (final p_ai={final_prob:.3f}). "
        "Next step is outside this module: paraphrase the text through a "
        "different model family (e.g. if generated by GPT, rewrite via Claude "
        "or Gemini). TempParaphraser (EMNLP 2025) and Adversarial Paraphrasing "
        "(NeurIPS 2025) document cross-model paraphrase as the strongest "
        "deterministic-layer follow-up. Do NOT attempt watermark removal — EU AI Act Article 50 "
        "prohibits it."
    )
    return FeedbackResult(
        final_text=current_text,
        original_probability=original_prob,
        final_probability=final_prob,
        iterations=iterations,
        reason_stopped=recommendation,
    )


def feedback_loop_aggressive(
    text: str,
    *,
    target_probability: float | dict[str, float] = 0.5,
    max_iterations: int = 6,
    detector: DetectorName = DEFAULT_DETECTOR,
    score_fn: Callable[[str], float] | None = None,
    humanize_fn: Callable | None = None,
    surprisal_fn: Callable[[str], SurprisalResult] | None = None,
) -> FeedbackResult:
    return feedback_loop(
        text,
        target_probability=target_probability,
        max_iterations=max_iterations,
        detector=detector,
        ladder=LADDER_AGGRESSIVE,
        score_fn=score_fn,
        humanize_fn=humanize_fn,
        surprisal_fn=surprisal_fn,
    )
