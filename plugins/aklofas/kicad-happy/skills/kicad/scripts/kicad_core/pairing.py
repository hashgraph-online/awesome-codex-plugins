"""Schematic part <-> PCB footprint pairing (kicad_core), as KiCad's Update PCB pairs them."""

from __future__ import annotations


def _part_ref(ref) -> bool:
    return isinstance(ref, str) and bool(ref) and not ref.startswith('#')


def pair_by_path(schematic: dict, pcb: dict) -> tuple[list[tuple[str, dict]], set, set]:
    """Pair PCB footprints with schematic references as KiCad's Update PCB does: a
    footprint whose (path) is a unit's instance path belongs to that symbol whatever its
    reference; a footprint with no such path pairs by reference (KiCad's relink mode).

    Returns (pairs sorted by schematic then PCB reference, schematic references with no
    footprint, references of footprints with no symbol)."""
    by_path: dict[str, str] = {}
    sch_refs = set()
    for c in schematic.get('components', []):
        ref = c.get('reference', '')
        if not _part_ref(ref):
            continue
        sch_refs.add(ref)
        path = c.get('instance_path')
        if isinstance(path, str) and path:
            by_path.setdefault(path.lower(), ref)
    pairs: list[tuple[str, dict]] = []
    unmatched: list[dict] = []
    for fp in pcb.get('footprints', []):
        if not _part_ref(fp.get('reference', '')):
            continue
        path = fp.get('sch_path')
        hit = by_path.get(path.lower()) if isinstance(path, str) and path else None
        if hit:
            pairs.append((hit, fp))
        else:
            unmatched.append(fp)
    path_paired = {ref for ref, _ in pairs}
    pcb_only = set()
    for fp in unmatched:
        ref = fp['reference']
        if ref in sch_refs and ref not in path_paired:
            pairs.append((ref, fp))
        else:
            pcb_only.add(ref)
    pairs.sort(key=lambda p: (p[0], p[1].get('reference', ''), str(p[1].get('sch_path') or '')))
    return pairs, sch_refs - {ref for ref, _ in pairs}, pcb_only
