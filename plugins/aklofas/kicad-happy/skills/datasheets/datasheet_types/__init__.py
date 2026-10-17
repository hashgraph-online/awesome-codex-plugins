"""Typed Python access layer for datasheet v2 extraction.

Mirrors the Track 2.1 JSON schemas under skills/datasheets/schemas/.
Dataclasses are ergonomic access; the JSON Schema remains source of truth.

Public API:
    DatasheetFacts — top-level per-MPN fact envelope
    SpecValue, Evidence — atomic primitives
    Pin, AltFunction, Pinout — pinout types
    BaseBlock, Package, ComplianceMark, PinRelationship — base block types
    Regulator, StabilityConditions, Sequencing — regulator category
    lookup — resolve MPN to DatasheetFacts (lazy re-export from scripts/)
    best, trusted, has_data — trust-gating helpers (Track 2.4)

Consumers import:
    from datasheet_types.extraction import DatasheetFacts
    from datasheet_types.codec import from_dict, to_dict
    facts = from_dict(DatasheetFacts, json.load(open('cache/LM2596-ADJ.json')))

    # Trust-gating pattern (spec §11/§12):
    from datasheet_types import best, trusted, has_data, lookup
    ds = lookup("LM2596-ADJ", cache_dir=...)
    if has_data(ds.regulator.vin_range):
        v = best(ds.regulator.vin_range, min_confidence="medium")
"""
from .spec_value import SpecValue, Evidence
from .pinout import Pin, AltFunction, Pinout
from .base_block import (
    BaseBlock,
    Package,
    BodyMm,
    MoistureSensitivity,
    ComplianceMark,
    PinRelationship,
)
from .regulator import Regulator, StabilityConditions, Sequencing
from .extraction import DatasheetFacts, Source, ExtractionMeta, SchemaVersion
from .trust_gating import best, trusted, has_data

__all__ = [
    "DatasheetFacts",
    "SchemaVersion",
    "Source",
    "ExtractionMeta",
    "BaseBlock",
    "Package",
    "BodyMm",
    "MoistureSensitivity",
    "ComplianceMark",
    "PinRelationship",
    "Pinout",
    "Pin",
    "AltFunction",
    "SpecValue",
    "Evidence",
    "Regulator",
    "StabilityConditions",
    "Sequencing",
    "lookup",
    "best",
    "trusted",
    "has_data",
]


# Lazy re-export of lookup() from the sibling scripts/ module. Kept lazy
# so `import datasheet_types` does not require skills/datasheets/scripts/
# on sys.path. Consumers that access datasheet_types.lookup get it on
# first touch.
def __getattr__(name: str):
    if name == "lookup":
        import sys
        from pathlib import Path
        scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        from datasheet_lookup import lookup  # noqa: E402
        globals()["lookup"] = lookup  # Cache so subsequent accesses skip __getattr__.
        return lookup
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
