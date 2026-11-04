"""Property-field aliases and field selection (kicad_core).

Single source for the MPN / distributor part-number alias sets and the
file-order-stable field pickers (KH-414, KH-418). The names live here, in
kicad_core; callers import them from kicad_core.fields.
"""

# ---------------------------------------------------------------------------
# Part-number field aliases (KH-414, GitHub #46)
#
# KiCad lets users name fields however they like. Three alias lists used to
# live in analyze_schematic, analyze_pcb and bom_manager and drifted apart;
# this is the single source. Names are stored NORMALIZED (see
# normalize_field_name) and matched normalized. Deliberately excluded: the
# two/three-letter bom_manager extras "MP" and "MFN" — too ambiguous for the
# analyzers (bom_manager keeps them as bom-local extras).
# ---------------------------------------------------------------------------

def normalize_field_name(name: str) -> str:
    """Lowercase, trim, collapse internal whitespace.

    'Manufacturer  P/N' -> 'manufacturer p/n'; '  MPN ' -> 'mpn'.
    """
    return " ".join(str(name).split()).lower()


# KH-418: two tiers. A manufacturer-specific name always outranks a generic
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
    sexp_parser.get_property) and returns the first non-empty value whose
    normalized name is in *aliases*, else None.
    """
    for child in node:
        if isinstance(child, list) and len(child) >= 3 and child[0] == "property":
            off = 1 if child[1] == "private" else 0
            if len(child) >= 3 + off and normalize_field_name(child[1 + off]) in aliases:
                value = str(child[2 + off])
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
    part-number aliases second (KH-418). Whitespace-only values do not win a
    tier; if no alias has a non-blank value, fall back to the pre-KH-418 pick
    so blank-only symbols behave exactly as before (final wave fix)."""
    return (_pick_nonblank(props, MPN_FIELD_ALIASES_PRIMARY)
            or _pick_nonblank(props, MPN_FIELD_ALIASES_GENERIC)
            or pick_field(props, MPN_FIELD_ALIASES))


def _get_property_ci_nonblank(node: list, aliases: frozenset):
    """Case/whitespace-insensitive property lookup requiring a non-blank
    value (same walk as get_property_ci; final wave fix)."""
    for child in node:
        if isinstance(child, list) and len(child) >= 3 and child[0] == "property":
            off = 1 if child[1] == "private" else 0
            if len(child) >= 3 + off and normalize_field_name(child[1 + off]) in aliases:
                value = str(child[2 + off])
                if value.strip():
                    return value
    return None


def get_mpn_property(node: list):
    """S-expression counterpart of pick_mpn (KH-418)."""
    return (_get_property_ci_nonblank(node, MPN_FIELD_ALIASES_PRIMARY)
            or _get_property_ci_nonblank(node, MPN_FIELD_ALIASES_GENERIC)
            or get_property_ci(node, MPN_FIELD_ALIASES))
