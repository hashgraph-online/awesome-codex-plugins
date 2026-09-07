"""Standardized detector evaluation metrics — pure stdlib.

Implements the SHIELD framework metrics (arXiv:2507.15286) and
TPR@FPR point estimates used by RAID (NeurIPS 2024, arXiv:2405.07940)
for comparing AI-text detectors at fixed false-positive rates.

No runtime dependencies beyond the standard library.
"""

from __future__ import annotations

import math


def _build_roc_points(
    y_true: list[int], y_score: list[float]
) -> list[tuple[float, float]]:
    """Build ROC curve points by distinct score thresholds.

    Groups tied scores so label order within ties doesn't bias the curve.
    Returns list of (fpr, tpr) including the origin (0, 0).
    """
    n_pos = sum(y_true)
    n_neg = len(y_true) - n_pos

    paired = sorted(zip(y_score, y_true, strict=True), reverse=True)

    points: list[tuple[float, float]] = [(0.0, 0.0)]
    tp = 0
    fp = 0
    i = 0
    while i < len(paired):
        j = i
        while j < len(paired) and paired[j][0] == paired[i][0]:
            if paired[j][1] == 1:
                tp += 1
            else:
                fp += 1
            j += 1
        points.append((fp / n_neg, tp / n_pos))
        i = j

    return points


def tpr_at_fpr(
    y_true: list[int],
    y_score: list[float],
    target_fpr: float = 0.05,
) -> tuple[float, float]:
    """Compute TPR at a given FPR operating point.

    Args:
        y_true: Binary labels (1 = AI, 0 = human).
        y_score: Detector scores (higher = more AI-like).
        target_fpr: Target false-positive rate (default 5%).

    Returns:
        (tpr, actual_fpr) at the threshold closest to target_fpr
        without exceeding it. Returns (0.0, 0.0) when no threshold
        satisfies the constraint or when inputs are degenerate.
    """
    if len(y_true) != len(y_score) or not y_true:
        return 0.0, 0.0

    n_pos = sum(y_true)
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.0, 0.0

    points = _build_roc_points(y_true, y_score)

    best_tpr = 0.0
    best_fpr = 0.0
    for fpr, tpr in points:
        if fpr > target_fpr:
            break
        if tpr >= best_tpr:
            best_tpr = tpr
            best_fpr = fpr

    return best_tpr, best_fpr


def auroc(y_true: list[int], y_score: list[float]) -> float:
    """Area under the ROC curve via the trapezoidal rule.

    Groups tied scores so all-tied labels [0,1,0,1] produce AUROC 0.5.
    Returns 0.0 on degenerate inputs (empty, single-class).
    """
    if len(y_true) != len(y_score) or not y_true:
        return 0.0

    n_pos = sum(y_true)
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.0

    points = _build_roc_points(y_true, y_score)

    auc = 0.0
    for i in range(1, len(points)):
        fpr_prev, tpr_prev = points[i - 1]
        fpr_curr, tpr_curr = points[i]
        auc += (fpr_curr - fpr_prev) * (tpr_curr + tpr_prev) / 2

    if points[-1][0] < 1.0:
        fpr_last, tpr_last = points[-1]
        auc += (1.0 - fpr_last) * (1.0 + tpr_last) / 2

    return auc


def w_auroc(
    y_true: list[int],
    y_score: list[float],
    k: float | None = None,
) -> float:
    """Weighted AUROC that emphasizes low-FPR regions.

    Normalized exponential-weight integral of the piecewise-linear ROC curve:
      W-AUROC = (1/Z) * integral_0^1 TPR(t) * k*exp(-k*t) dt
    where Z = 1 - exp(-k).

    Default k = 20*ln(2) — 50% of weight in FPR in [0, 0.05].

    SHIELD framework (arXiv:2507.15286), Section 3.3.
    Returns value in [0, 1]. Perfect separation -> ~1.0.
    """
    if k is None:
        k = 20 * math.log(2)

    if len(y_true) != len(y_score) or not y_true:
        return 0.0

    n_pos = sum(y_true)
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.0

    points = _build_roc_points(y_true, y_score)

    if points[-1][0] < 1.0:
        points.append((1.0, 1.0))

    weighted_auc = 0.0
    for i in range(1, len(points)):
        fpr_a, tpr_a = points[i - 1]
        fpr_b, tpr_b = points[i]
        delta_fpr = fpr_b - fpr_a
        if delta_fpr <= 0:
            continue

        slope = (tpr_b - tpr_a) / delta_fpr

        exp_a = math.exp(-k * fpr_a)
        exp_b = math.exp(-k * fpr_b)

        integral_exp = (exp_a - exp_b) / k
        integral_t_exp = (fpr_a * exp_a - fpr_b * exp_b) / k + (exp_a - exp_b) / (k * k)

        segment = k * (
            (tpr_a - slope * fpr_a) * integral_exp + slope * integral_t_exp
        )
        weighted_auc += segment

    normalizer = 1.0 - math.exp(-k)
    if normalizer > 0:
        weighted_auc /= normalizer

    return max(0.0, min(1.0, weighted_auc))


def sfd(scenario_fprs: list[float], lambda_: float | None = None) -> float:
    """Scenario Fairness Deviation — SHIELD Section 3.3.

    SFD = exp(-lambda * sigma_FPR)

    Higher is better. Equal scenario FPRs -> 1.0 (perfect stability).
    sigma_FPR = 0.1 with lambda = 10*ln(2) -> SFD = 0.5.

    Args:
        scenario_fprs: Per-scenario FPRs.
        lambda_: Scaling factor. Default 10*ln(2).
    """
    if lambda_ is None:
        lambda_ = 10 * math.log(2)
    if len(scenario_fprs) < 2:
        return 1.0
    mean_fpr = sum(scenario_fprs) / len(scenario_fprs)
    variance = sum((f - mean_fpr) ** 2 for f in scenario_fprs) / len(scenario_fprs)
    sigma = math.sqrt(variance)
    return math.exp(-lambda_ * sigma)


def urss(w_aurocs: list[float], sfd_value: float) -> float:
    """Unified Robustness and Security Score — SHIELD Section 3.4.

    URSS = mean(W-AUROCs) * SFD

    Higher is better. Perfect fair system: URSS = 1.0.
    """
    if not w_aurocs:
        return 0.0
    return (sum(w_aurocs) / len(w_aurocs)) * sfd_value
