"""Property-field aliases and field selection (kicad_core).

Single source for the MPN / distributor part-number alias sets and the
file-order-stable field pickers. The names live here, in
kicad_core; callers import them from kicad_core.fields.
"""

from collections.abc import Iterable, Mapping

from kicad_core.sexp import _iter_properties

# ---------------------------------------------------------------------------
# Part-number field aliases
#
# KiCad lets users name fields however they like. This is the single alias
# source for the analyzers and bom_manager. Names are stored NORMALIZED (see
# normalize_field_name) and matched normalized. Deliberately excluded: the
# two/three-letter bom_manager extras "MP" and "MFN" — too ambiguous for the
# analyzers (bom_manager keeps them as bom-local extras).
# ---------------------------------------------------------------------------

# Characters KiCad's SCH_FIELD::SetText strips from both ends of a mandatory field
# (wxString::Strip tests wxSafeIsspace: space, \t \n \v \f \r).
MANDATORY_STRIP = " \t\n\v\f\r"


def normalize_field_name(name: str) -> str:
    """Lowercase, trim, collapse internal whitespace.

    'Manufacturer  P/N' -> 'manufacturer p/n'; '  MPN ' -> 'mpn'.
    """
    return " ".join(str(name).split()).lower()


# Two tiers. A manufacturer-specific name always outranks a generic
# part-number name (El-Luhb: `Part#` = LCSC code listed before `MPN`). File
# order breaks ties only WITHIN a tier.
MPN_FIELD_ALIASES_PRIMARY: frozenset = frozenset({
    "mpn", "mpn#", "mfpn", "mfg part", "mfgpart",
    "manufacturer_part_number", "manufacturerpartnumber", "mfr_part_number",
    "manufacturer part number", "manufacturer part #",
    "manufacturer p/n", "mfr p/n", "mfg p/n",
    "mfr no.", "mfr_no", "mfr no", "manf#",
})
MPN_FIELD_ALIASES_GENERIC: frozenset = frozenset({
    "partnumber", "part number", "part#", "partno", "partno.",
})
MPN_FIELD_ALIASES: frozenset = MPN_FIELD_ALIASES_PRIMARY | MPN_FIELD_ALIASES_GENERIC

DIGIKEY_FIELD_ALIASES: frozenset = frozenset({
    "digikey", "digi-key", "digi-key part number", "digi-key_pn",
    "digikey part", "digikey part number", "digikey_part_number",
    "digi-key pn", "dk",
    # GitHub #46
    "digikey p/n", "digi-key p/n",
})


def pick_field(props: dict, aliases: frozenset) -> str:
    """First non-empty value whose normalized key is in *aliases*.

    Iterates *props* in insertion (file) order so the result does not
    depend on the hash seed when a symbol carries two aliases.
    """
    for key, value in props.items():
        if value and normalize_field_name(key) in aliases:
            return value
    return ""


def get_property_ci(node: list, aliases: frozenset):
    """Case/whitespace-insensitive property lookup on an S-expression node.

    Walks ``(property ["private"] "Name" "Value" ...)`` children (the KiCad 9+
    ``private`` keyword shifts the indices by one, as in
    kicad_core.sexp.get_property) and returns the first non-empty value whose
    normalized name is in *aliases*, else None.
    """
    for name, value in _iter_properties(node):
        if normalize_field_name(name) in aliases:
            value = str(value)
            if value:
                return value
    return None


def _pick_nonblank(props: dict, aliases: frozenset) -> str:
    """First value whose normalized key is in *aliases* and whose .strip() is
    non-empty, returned RAW (unstripped, so existing output is unchanged)."""
    for key, value in props.items():
        if value and str(value).strip() and normalize_field_name(key) in aliases:
            return value
    return ""


def pick_mpn(props: dict) -> str:
    """Manufacturer part number: manufacturer-specific aliases first, generic
    part-number aliases second. Whitespace-only values do not win a
    tier; if no alias has a non-blank value, fall back to the plain
    pick_field over all aliases so blank-only symbols still resolve to a value."""
    return (_pick_nonblank(props, MPN_FIELD_ALIASES_PRIMARY)
            or _pick_nonblank(props, MPN_FIELD_ALIASES_GENERIC)
            or pick_field(props, MPN_FIELD_ALIASES))


def _get_property_ci_nonblank(node: list, aliases: frozenset):
    """Case/whitespace-insensitive property lookup requiring a non-blank
    value (same walk as get_property_ci)."""
    for name, value in _iter_properties(node):
        if normalize_field_name(name) in aliases:
            value = str(value)
            if value.strip():
                return value
    return None


def get_mpn_property(node: list):
    """S-expression counterpart of pick_mpn."""
    return (_get_property_ci_nonblank(node, MPN_FIELD_ALIASES_PRIMARY)
            or _get_property_ci_nonblank(node, MPN_FIELD_ALIASES_GENERIC)
            or get_property_ci(node, MPN_FIELD_ALIASES))


# KiCad's mandatory symbol fields: a blank one never hides another unit's text.
_MANDATORY_FIELDS = frozenset({"Value", "Footprint", "Datasheet", "Description"})


def merge_unit_fields(units: Iterable[tuple[int, Mapping[str, str]]]) -> dict[str, str]:
    """One field set for a multi-unit part, as KiCad's netlist builds it.

    *units* yields (unit number, fields) per placed unit, in file order. Value,
    Footprint, Datasheet and Description come from the lowest-numbered unit whose
    text is non-empty (blank when none is); every other field comes from the
    lowest-numbered unit that carries it, empty or not. Ties keep file order, so
    units with different non-blank text resolve to the lowest unit's.
    """
    picked: dict[str, tuple[float, str]] = {}
    for unit, fields in units:
        for name, text in fields.items():
            current = picked.get(name)
            if name in _MANDATORY_FIELDS and not text:
                if current is None:
                    picked[name] = (float("inf"), "")
                continue
            if current is None or unit < current[0]:
                picked[name] = (unit, text)
    return {name: text for name, (_, text) in picked.items()}
