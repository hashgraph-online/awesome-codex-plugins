"""Top-level DatasheetFacts + Source + ExtractionMeta + SchemaVersion.

Mirrors extraction.schema.json. DatasheetFacts is the facade Track 2.3
will return from lookup(mpn). Composes base + zero-or-more category
extensions.

lookup() itself is NOT in this module — Track 2.3 lands that alongside
cache-path resolution + staleness detection. Track 2.2 delivers only
the typed shape.

Field-ordering note (same rationale as BaseBlock in base_block.py):
Python dataclass syntax requires every required field (no default) to
precede every optional field (with default). The JSON schema property
order puts required fields interleaved with optionals — e.g. Source's
sha256 is required (position 7 in schema) but datasheet_revision /
datasheet_date / source_url / local_path at positions 3-6 are optional.
Python forbids sha256 appearing after them. Source and ExtractionMeta
therefore group all required fields first, then all optional fields
in schema order. to_dict output key ordering diverges from schema
property order but matches schema values — consumers should not rely
on JSON key order (dict equality is value-based, the round-trip tests
pass via value equality).

Category-sibling fields (DatasheetFacts.regulator today; v1.5 adds
mcu/opamp/diode/transistor/crystal) carry metadata={"omit_if_none":
True}. The codec skips these when None rather than emitting explicit
null — so "absent key" is canonical for "no category," and the JSON
cache doesn't carry null placeholders for inactive categories.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .base_block import BaseBlock
from .regulator import Regulator


@dataclass
class SchemaVersion:
    """Split schema versions — base evolves independently of each category."""
    base: str = field(metadata={
        "description": "Base block schema version (MAJOR.MINOR, e.g. '1.0')."})
    categories: dict[str, str] = field(default_factory=dict, metadata={
        "description": "Per-category schema versions, keyed by category name "
                       "(e.g. {'regulator': '0.3'})."})


@dataclass
class Source:
    """Facts about the source PDF — separate from extraction-act facts."""
    manufacturer: str = field(metadata={
        "description": "PDF manufacturer name."})
    mpn: str = field(metadata={
        "description": "Manufacturer part number."})
    sha256: str = field(metadata={
        "description": "PDF SHA-256 with 'sha256:' prefix. Staleness pivot — Track 2.3 "
                       "compares this against the PDF on disk to flag cache staleness."})
    datasheet_revision: Optional[str] = field(default=None, metadata={
        "description": "Datasheet revision label (e.g. 'Rev M')."})
    datasheet_date: Optional[str] = field(default=None, metadata={
        "description": "Datasheet publication date."})
    source_url: Optional[str] = field(default=None, metadata={
        "description": "Origin URL the PDF was downloaded from."})
    local_path: Optional[str] = field(default=None, metadata={
        "description": "Filesystem path relative to datasheets/ (e.g. 'LM2596-ADJ.pdf')."})
    page_count: Optional[int] = field(default=None, metadata={
        "description": "PDF page count."})
    family_ref: Optional[str] = field(default=None, metadata={
        "description": "Path to a _families/ file when this MPN is a variant. Reserved for "
                       "v1.5 Tier 2 dedup; always None in v1.4."})


@dataclass
class ExtractionMeta:
    """Facts about the extraction act itself.

    Separate from Source — a re-extraction updates ExtractionMeta without
    touching Source (unless the PDF itself changed, bumping the sha256).
    """
    extracted_at: str = field(metadata={
        "description": "ISO-8601 UTC timestamp of the extraction run."})
    extractor_schema_version: str = field(metadata={
        "description": "Version of the overall extraction pipeline (MAJOR.MINOR)."})
    extractor_scout: Optional[str] = field(default=None, metadata={
        "description": "Identifier of the scout subagent / model. Opaque string."})
    quality_score: Optional[int] = field(default=None, metadata={
        "description": "Overall extraction quality score (0–100). None when not yet scored."})
    plan_ref: Optional[str] = field(default=None, metadata={
        "description": "Relative path to the orchestration plan JSON."})


@dataclass
class DatasheetFacts:
    """Top-level per-MPN fact envelope.

    Composes SchemaVersion + Source + ExtractionMeta + BaseBlock + zero
    or more category extensions (currently just Regulator; v1.5 adds
    MCU, opamp, diode, transistor, crystal).

    Consumers obtain instances via Track 2.3's lookup(mpn) facade.

    v1.5 expansion note: adding a new category (e.g. `mcu: Optional[Mcu]
    = field(default=None, metadata={"omit_if_none": True, ...})`) works
    mechanically without any codec changes — the omit_if_none policy
    documented in codec.to_dict generalizes to any category sibling.
    A v1.4 consumer loading a v1.5 cache file will silently drop
    unknown category sibling keys; this is scoped behavior, not a bug.
    """
    schema_version: SchemaVersion = field(metadata={
        "description": "Per-section schema versions."})
    source: Source = field(metadata={
        "description": "PDF-level facts."})
    extraction: ExtractionMeta = field(metadata={
        "description": "Facts about this extraction run."})
    base: BaseBlock = field(metadata={
        "description": "Universal per-IC facts."})
    categories: list[str] = field(default_factory=list, metadata={
        "description": "List of active category extensions (e.g. ['regulator']). Each entry "
                       "should correspond to a sibling field carrying that category's payload."})
    regulator: Optional[Regulator] = field(default=None, metadata={
        "description": "Regulator category extension. None when 'regulator' not in categories.",
        "omit_if_none": True,
    })

    # ---- Computed attributes (NOT dataclass fields) ----
    # These properties read an optional _cache_context instance attribute
    # that lookup() attaches to DatasheetFacts instances it returns.
    # For instances constructed outside lookup() (e.g. Track 2.2 round-trip
    # tests), _cache_context is absent and properties fall back to defaults.

    @property
    def quality(self) -> Optional[int]:
        """Overall extraction quality score (0–100). Passthrough to
        extraction.quality_score — returns whatever the cached extraction
        stored there. None when the extraction wasn't scored.

        This property works identically regardless of whether _cache_context
        is populated — it does not read cache context at all.

        Spec §11 usage: `if ds.quality is not None and ds.quality < 60: ...`
        """
        return self.extraction.quality_score

    @property
    def stale(self) -> bool:
        """True when the PDF on disk has changed since this cache entry
        was extracted (sha256 mismatch) OR when the PDF is missing. False
        when PDF hash matches the cached source.sha256.

        Returns False when DatasheetFacts is constructed outside lookup()
        (no cache context available) — consumers that want staleness
        checking must go through lookup().

        Spec §11 usage: `if ds.stale: ...`
        """
        ctx = getattr(self, "_cache_context", None)
        if ctx is None:
            return False
        return ctx.is_stale

    @property
    def cache_path(self) -> "Optional[Path]":
        """Path to the cache JSON this DatasheetFacts was loaded from,
        or None if constructed outside lookup(). Useful for debugging
        and cache-management tooling.

        Return type expressed as a string-literal annotation so we don't
        need to import pathlib.Path at this module's load time — CacheContext
        (in datasheet_lookup.py) is the authoritative owner of the Path type.
        from __future__ import annotations (already in scope) makes the
        literal resolve at type-checker time only.
        """
        ctx = getattr(self, "_cache_context", None)
        if ctx is None:
            return None
        return ctx.cache_path
