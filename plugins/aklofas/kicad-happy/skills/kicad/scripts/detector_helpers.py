"""Shared helper functions for signal and domain detectors.

Extracted from repeated patterns across signal_detectors.py and
domain_detectors.py to eliminate boilerplate and reduce copy-paste risk.
"""

from __future__ import annotations

from kicad_types import AnalysisContext


def index_two_pin_components(
    ctx: AnalysisContext,
    components: list[dict],
) -> tuple[dict[str, tuple[str, str]], dict[str, list[str]]]:
    """Index 2-pin components by their connected nets.

    Returns:
        comp_nets: ``{ref: (net1, net2)}`` for each valid component
        net_to_comps: ``{net_name: [ref, ...]}`` reverse index

    Skips components with missing nets, single-net connections, or
    same net on both pins (shorted).
    """
    comp_nets: dict[str, tuple[str, str]] = {}
    net_to_comps: dict[str, list[str]] = {}
    for comp in components:
        ref = comp["reference"]
        n1, n2 = ctx.get_two_pin_nets(ref)
        if not n1 or not n2 or n1 == n2:
            continue
        comp_nets[ref] = (n1, n2)
        net_to_comps.setdefault(n1, []).append(ref)
        net_to_comps.setdefault(n2, []).append(ref)
    return comp_nets, net_to_comps


def get_components_by_type(
    ctx: AnalysisContext,
    comp_type: str | tuple[str, ...],
    with_parsed_values: bool = False,
) -> list[dict]:
    """Filter ctx.components by type, optionally requiring a parsed value.

    Args:
        comp_type: Single type string or tuple of types.
        with_parsed_values: If True, only include components whose reference
            appears in ``ctx.parsed_values``.
    """
    if isinstance(comp_type, str):
        comp_type = (comp_type,)
    result = [c for c in ctx.components if c["type"] in comp_type]
    if with_parsed_values:
        result = [c for c in result if c["reference"] in ctx.parsed_values]
    return result


def get_unique_ics(ctx) -> list:
    """Return deduplicated list of IC components.

    Components with duplicate references are collapsed (keeps first seen).
    """
    return list({c["reference"]: c for c in ctx.components if c["type"] == "ic"}.values())


def match_ic_keywords(component: dict, keywords: list[str] | tuple[str, ...]) -> bool:
    """Check if an IC's value+lib_id contains any of the given keywords.

    Performs case-insensitive matching against the concatenation of the
    component's ``value`` and ``lib_id`` fields.  Only matches components
    with ``type == 'ic'``.
    """
    if component.get("type") != "ic":
        return False
    val_lib = (component.get("value", "") + " " + component.get("lib_id", "")).lower()
    return any(k in val_lib for k in keywords)
