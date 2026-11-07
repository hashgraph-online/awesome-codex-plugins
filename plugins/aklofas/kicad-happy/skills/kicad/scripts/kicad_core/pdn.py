"""PDN branch impedances and their parallel combination, shared by the EMC and schematic PDN models."""
from __future__ import annotations

import math


def cap_branch_z(f_hz: float, c_f: float, esr_ohm: float, esl_h: float) -> complex:
    """Series RLC impedance of a capacitor: ESR + j(ωL − 1/ωC)."""
    # EQ-013: Z = ESR + j(ωL - 1/ωC) (series RLC impedance)
    omega = 2 * math.pi * f_hz
    return complex(esr_ohm, omega * esl_h - 1.0 / (omega * c_f))


def parallel_impedance(branches: list[complex]) -> complex | None:
    """1 / Σ(1/Zᵢ) over complex branch impedances.

    Admittances add as complex numbers, so an inductive and a capacitive branch
    partly cancel (the anti-resonance). None when there is no branch or the
    admittances cancel exactly (only lossless branches can do that).
    """
    if not branches:
        return None
    y = 0j
    for z in branches:
        if z == 0:
            return 0j
        y += 1 / z
    if y == 0:
        return None
    return 1 / y
