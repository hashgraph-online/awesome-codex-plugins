"""Real surprisal-variance reading via a small local language model.

DivEye (Ganapathi et al., arXiv 2509.18880, TMLR 2026) found that the
primary AI-vs-human signal surviving paraphrase attacks is *intra-document
surprisal variance* — not absolute perplexity. Human prose swings between
predictable "glue" spans and unpredictable lexical choices; AI prose is
uniformly smooth.

Reference implementation: https://github.com/IBM/diveye

The `stylometry` module ships two deterministic proxies for this signal
(`sentence_length_cv`, `word_length_stdev`) that approximate variance
without needing a language model. This module provides the real thing:
it loads a small open-weight LM (distilgpt2 by default, 82M params,
~330MB download) and computes the standard deviation of per-token log-
probabilities across the document.

Design constraints mirror `detector.py`:

  - Heavy deps (torch, transformers) import lazily.
  - Module-global scorer cache (first call pays the ~5s load cost, rest
    are fast).
  - Raises `SurprisalUnavailable` (a RuntimeError subclass) on missing
    deps / failed load, with a message pointing at the fix.
  - Offline-friendly: works once the HF cache is populated.

Output `SurprisalReading`:

  mean_log_prob      mean per-token log-probability (nats)
  surprisal_stdev    sigma of per-token surprisal (-log p); the DivEye signal
  surprisal_variance variance of per-token surprisal
  surprisal_skewness / surprisal_kurtosis
  delta_surprisal_mean / delta_surprisal_stdev
  delta2_surprisal_variance / entropy / autocorr
  surprisal_cv       sigma divided by |mean_surprisal|; scale-invariant
  token_count        tokens scored
  model              model id used

Higher stdev and higher cv both indicate more bursty, human-like token
rhythm. Flat AI prose typically lands around 0.6-0.9 stdev on distilgpt2;
literary human prose often exceeds 1.5. Treat those as rough field
readings, not calibrated thresholds -- calibration is per-model.

Not a silver bullet. DivEye itself is one detector among many, and
detector arms races move fast (Nicks et al. ICLR 2024, Chakraborty et al.
arXiv 2304.04736 ICML 2024). Use the reading as a voice-match target, not a gate."""

from __future__ import annotations

import math
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

_DEFAULT_MODEL = "distilgpt2"

_LM_CACHE: dict[str, tuple[Any, Any]] = {}


class SurprisalUnavailable(RuntimeError):
    """Raised when the surprisal scorer can't load (missing deps, no cache).

    Catch this to degrade to the stylometry proxies (`sentence_length_cv`,
    `word_length_stdev`) which run without a model."""


@dataclass
class SurprisalReading:
    """Result of a surprisal-variance pass.

    All fields are in nats (natural log). `token_count` is the number of
    tokens actually scored -- may be less than the raw tokenization when
    we truncate to the model's context window."""

    mean_log_prob: float
    surprisal_stdev: float
    surprisal_cv: float
    token_count: int
    model: str = _DEFAULT_MODEL
    surprisal_variance: float = 0.0
    surprisal_skewness: float = 0.0
    surprisal_kurtosis: float = 0.0
    delta_surprisal_mean: float = 0.0
    delta_surprisal_stdev: float = 0.0
    delta2_surprisal_variance: float = 0.0
    delta2_surprisal_entropy: float = 0.0
    delta2_surprisal_autocorr: float = 0.0

    def to_dict(self) -> dict:
        return {
            "mean_log_prob": round(self.mean_log_prob, 4),
            "surprisal_stdev": round(self.surprisal_stdev, 4),
            "surprisal_variance": round(self.surprisal_variance, 4),
            "surprisal_skewness": round(self.surprisal_skewness, 4),
            "surprisal_kurtosis": round(self.surprisal_kurtosis, 4),
            "delta_surprisal_mean": round(self.delta_surprisal_mean, 4),
            "delta_surprisal_stdev": round(self.delta_surprisal_stdev, 4),
            "delta2_surprisal_variance": round(self.delta2_surprisal_variance, 4),
            "delta2_surprisal_entropy": round(self.delta2_surprisal_entropy, 4),
            "delta2_surprisal_autocorr": round(self.delta2_surprisal_autocorr, 4),
            "surprisal_cv": round(self.surprisal_cv, 4),
            "token_count": self.token_count,
            "model": self.model,
        }

    def to_diveye_vector(self) -> list[float]:
        return [
            -self.mean_log_prob,
            self.surprisal_stdev,
            self.surprisal_variance,
            self.surprisal_skewness,
            self.surprisal_kurtosis,
            self.delta_surprisal_mean,
            self.delta_surprisal_stdev,
            self.delta2_surprisal_variance,
            self.delta2_surprisal_entropy,
            self.delta2_surprisal_autocorr,
        ]


def _bootstrap_hint(model_id: str) -> str:
    return (
        f"\nTo fetch the model: pip install torch transformers and run once "
        f"with network access to populate the HuggingFace cache for "
        f"{model_id!r}. Set UNSLOP_SKIP_SURPRISAL=1 to disable."
    )


def _load_scorer(model_id: str) -> tuple[Any, Any]:
    """Load (tokenizer, model) for `model_id`. Cached across calls."""
    if model_id in _LM_CACHE:
        return _LM_CACHE[model_id]

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise SurprisalUnavailable(
            f"Missing dependency: {exc.name}. Install with:\n"
            "  pip install torch transformers"
        ) from exc

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(model_id)
    except Exception as exc:
        raise SurprisalUnavailable(
            f"Could not load {model_id}: {exc}.{_bootstrap_hint(model_id)}"
        ) from exc

    model.train(False)
    _LM_CACHE[model_id] = (tokenizer, model)
    return tokenizer, model


def _finite(value: float) -> float:
    return value if math.isfinite(value) else 0.0


def _stats_from_sequence(values: list[float]) -> tuple[float, float, float, float, float]:
    if not values:
        return (0.0, 0.0, 0.0, 0.0, 0.0)
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    stdev = math.sqrt(variance)
    if stdev <= 1e-12:
        return (mean, stdev, variance, 0.0, 0.0)
    skewness = sum(((x - mean) / stdev) ** 3 for x in values) / n
    kurtosis = sum(((x - mean) / stdev) ** 4 for x in values) / n - 3.0
    return (_finite(mean), _finite(stdev), _finite(variance), _finite(skewness), _finite(kurtosis))


def _entropy_20_bins(values: list[float]) -> float:
    if not values:
        return 0.0
    lo = min(values)
    hi = max(values)
    if hi <= lo:
        return 0.0
    bins = [0] * 20
    span = hi - lo
    for value in values:
        idx = min(19, int(((value - lo) / span) * 20))
        bins[idx] += 1
    total = sum(bins)
    entropy = 0.0
    for count in bins:
        if count == 0:
            continue
        p = count / total
        entropy -= p * math.log(p)
    return _finite(entropy)


def _lag1_autocorr(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    xs = values[:-1]
    ys = values[1:]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=False))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if den_x <= 1e-12 or den_y <= 1e-12:
        return 0.0
    return _finite(num / (den_x * den_y))


def compute_surprisal_variance(
    text: str,
    *,
    model: str = _DEFAULT_MODEL,
    max_tokens: int = 1024,
) -> SurprisalReading:
    """Score `text` with a local causal LM and return surprisal stats.

    `max_tokens` truncates overly long inputs to keep the pass fast on
    CPU. 1024 is ~4-5 paragraphs; beyond that, surprisal stdev stabilizes
    and further tokens don't move the reading much.

    Raises `SurprisalUnavailable` if the LM can't be loaded. Callers who
    want a best-effort reading should catch that and fall back to the
    stylometry proxies."""
    if os.environ.get("UNSLOP_SKIP_SURPRISAL") == "1":
        raise SurprisalUnavailable("UNSLOP_SKIP_SURPRISAL=1 set in environment")

    if not text or not text.strip():
        return SurprisalReading(
            mean_log_prob=0.0,
            surprisal_stdev=0.0,
            surprisal_cv=0.0,
            token_count=0,
            model=model,
        )

    tokenizer, lm = _load_scorer(model)

    try:
        import torch
        import torch.nn.functional as F
    except ImportError as exc:
        raise SurprisalUnavailable(f"Missing dependency: {exc.name}") from exc

    ids = tokenizer.encode(text, return_tensors="pt")
    if ids.shape[1] > max_tokens:
        ids = ids[:, :max_tokens]

    if ids.shape[1] < 2:
        return SurprisalReading(
            mean_log_prob=0.0,
            surprisal_stdev=0.0,
            surprisal_cv=0.0,
            token_count=int(ids.shape[1]),
            model=model,
        )

    with torch.no_grad():
        logits = lm(ids).logits
        log_probs = F.log_softmax(logits, dim=-1)

        # Shift-by-one teacher-forcing: at position t, read log-prob of the
        # token that actually appears at position t+1.
        targets = ids[0, 1:]
        target_log_probs = log_probs[0, :-1, :].gather(
            -1, targets.unsqueeze(-1)
        ).squeeze(-1)

        surprisal = (-target_log_probs).float()
        mean_lp = float(target_log_probs.mean().item())
        surprisals = [float(x) for x in surprisal.detach().cpu().tolist()]
        _mean_s, std, variance, skewness, kurtosis = _stats_from_sequence(surprisals)
        mean_s = float(surprisal.mean().item())
        cv = std / mean_s if mean_s > 1e-9 else 0.0
        delta = [b - a for a, b in zip(surprisals, surprisals[1:], strict=False)]
        _delta_mean, delta_stdev, _delta_var, _delta_skew, _delta_kurt = _stats_from_sequence(delta)
        delta2 = [b - a for a, b in zip(delta, delta[1:], strict=False)]
        _delta2_mean, _delta2_stdev, delta2_var, _delta2_skew, _delta2_kurt = _stats_from_sequence(delta2)
        delta2_entropy = _entropy_20_bins(delta2)
        delta2_autocorr = _lag1_autocorr(delta2)

    return SurprisalReading(
        mean_log_prob=_finite(mean_lp),
        surprisal_stdev=_finite(std),
        surprisal_cv=_finite(cv),
        token_count=int(targets.shape[0]),
        model=model,
        surprisal_variance=_finite(variance),
        surprisal_skewness=_finite(skewness),
        surprisal_kurtosis=_finite(kurtosis),
        delta_surprisal_mean=_finite(_delta_mean),
        delta_surprisal_stdev=_finite(delta_stdev),
        delta2_surprisal_variance=_finite(delta2_var),
        delta2_surprisal_entropy=_finite(delta2_entropy),
        delta2_surprisal_autocorr=_finite(delta2_autocorr),
    )


def is_available(model: str = _DEFAULT_MODEL) -> bool:
    """Best-effort check -- returns True if `compute_surprisal_variance`
    would work today. False on missing deps or model-not-in-cache."""
    if os.environ.get("UNSLOP_SKIP_SURPRISAL") == "1":
        return False
    try:
        _load_scorer(model)
        return True
    except SurprisalUnavailable:
        return False


ScorerBuilder = Callable[[str], Any]
