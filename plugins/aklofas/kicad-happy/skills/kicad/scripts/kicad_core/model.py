"""Typed records over the reader dict shapes (kicad_core.model).

TypedDicts describe what the readers already emit, so serialisation does not
change (spec §4.1). Open boundaries stay plain dicts (D3): finding ``extra``
fields, manufacturer payloads, datasheet category extensions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict


class _PinRequired(TypedDict):
    number: str
    name: str
    type: str
    x: float
    y: float


class Pin(_PinRequired, total=False):
    """A placed-symbol pin as ``compute_pin_positions`` emits it (``Component['pins']``)."""
    hidden: bool


class NetPin(TypedDict):
    """One pin connection on a net (``Net['pins']``), as ``build_net_map`` emits it."""
    component: str
    pin_number: str
    pin_name: str
    pin_type: str


class NetLabel(TypedDict):
    name: str
    type: str


class _NetRequired(TypedDict):
    name: str
    pins: list[NetPin]
    point_count: int
    no_connect: bool
    has_pwr_flag: bool
    labels: list[NetLabel]


class Net(_NetRequired, total=False):
    """A net record (``nets[key]``). ``display_name`` appears on ``/<sheet>/<name>`` collision
    keys (KH-359) and on ``__unnamed_N`` nets with exactly one named IC pin."""
    display_name: str


class _ComponentRequired(TypedDict):
    reference: str
    value: str
    lib_id: str
    footprint: str
    datasheet: str
    description: str
    mpn: str
    manufacturer: str
    digikey: str
    mouser: str
    lcsc: str
    element14: str
    x: float
    y: float
    angle: float
    mirror_x: bool
    mirror_y: bool
    unit: str | int | None
    uuid: str
    in_bom: bool
    dnp: bool
    on_board: bool
    pin_uuids: dict
    type: str


class Component(_ComponentRequired, total=False):
    """A placed component. Required keys are those BOTH readers (``extract_components`` and the
    legacy ``.sch`` reader) always set; everything else is optional. ``pins`` is stripped and
    ``category``/``parsed_value``/``pin_nets`` are added by result assembly; ``_sheet`` is set
    by multi-sheet assembly; ``_unit_pins`` is a set popped before output."""
    lib_name: str
    pins: list[Pin]
    keywords: str
    functional_class: str
    is_external_connector: bool
    connector_layout: str
    transform_matrix: tuple
    category: str
    parsed_value: float
    pin_nets: dict[str, str]
    _unit_pins: set
    _sheet: int
    _power_scope: str
    _pin_source: str


PinNetEntry = tuple[str, Net]
"""What ``AnalysisContext.pin_net`` holds: ``(net_name, net_record)`` — the record, not a pin name."""


@dataclass
class SheetData:
    """What ``parse_single_sheet`` returns for one ``.kicad_sch`` file (field order = the pre-v3 tuple)."""
    root: list
    components: list[Component]
    wires: list[dict]
    labels: list[dict]
    junctions: list[dict]
    no_connects: list[dict]
    sub_sheet_paths: list[tuple[str, str]]
    lib_symbols: dict
    text_annotations: list[dict]
    bus_elements: dict
    title_block: dict


@dataclass(frozen=True)
class ResolvedConfig:
    """The one resolved project configuration (S6). Built by ``project_config.resolve_config``.

    effective:  the merged mapping consumers read (today's ``config``)
    mode:       "explicit" (``--config PATH``) or "discovered" (cascade from the project dir)
    paths:      files that contributed, in merge order (lowest precedence first); () when none
    hash_input: the single file ``inputs.config_hash`` is computed from, or None
    """
    effective: dict
    mode: str
    paths: tuple[str, ...]
    hash_input: str | None


@dataclass
class PcbReaderState:
    """Per-run PCB reader state (B1): the KiCad-10 net-name → synthetic-ID map.

    Built by ``_build_net_mapping`` after extraction (sorted names, IDs from 1); consulted only by
    the backfill in ``read_board``. One instance per ``analyze_pcb()`` call — nothing module-level.
    """
    net_name_to_id: dict[str, int] = field(default_factory=lambda: {"": 0})

    def net_id(self, val: str | None) -> int:
        if not val:
            return 0
        try:
            return int(val)
        except (ValueError, TypeError):
            return self.net_name_to_id.get(val, 0)
