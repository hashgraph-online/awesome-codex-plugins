"""
Project configuration and suppression matching for kicad-happy.

Loads .kicad-happy.json (JSONC with comment stripping) with cascading
config: files found closer to the project override those farther away,
and ~/.kicad-happy.json serves as a user-level base layer.

Merge rules:
  - Dicts: deep-merged recursively, closer keys win
  - "suppressions": concatenated across all layers (additive)
  - Other lists: closer layer wins entirely

Provides suppression matching with fnmatch globs and risk-scoring
utilities shared across all analyzers.

Zero external dependencies — stdlib only.
"""

from __future__ import annotations

import json
import os
import re
from fnmatch import fnmatch
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# JSONC loader (JSON with // and /* */ comments, trailing commas)
# ---------------------------------------------------------------------------

_TRAILING_COMMA = re.compile(r',\s*([}\]])')


def _strip_jsonc(text: str) -> str:
    """Strip JS-style comments and trailing commas from JSON text.

    Single-pass, string-aware scanner: comments are only recognized
    outside of JSON string literals, so `//` or `/* */` occurring
    inside a string value (e.g. a URL) survives intact.
    """
    out = []
    state = 'normal'  # normal | in_string | line_comment | block_comment
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if state == 'normal':
            if c == '"':
                state = 'in_string'
                out.append(c)
            elif c == '/' and text[i + 1:i + 2] == '/':
                state = 'line_comment'
                i += 1
            elif c == '/' and text[i + 1:i + 2] == '*':
                state = 'block_comment'
                i += 1
            else:
                out.append(c)
        elif state == 'in_string':
            out.append(c)
            if c == '\\':
                i += 1
                if i < n:
                    out.append(text[i])
            elif c == '"':
                state = 'normal'
        elif state == 'line_comment':
            if c == '\n':
                state = 'normal'
                out.append(c)
        elif state == 'block_comment':
            if c == '*' and text[i + 1:i + 2] == '/':
                state = 'normal'
                i += 1
        i += 1
    return _TRAILING_COMMA.sub(r'\1', ''.join(out))


def load_jsonc(path: str) -> dict:
    """Load a JSONC file, returning parsed dict."""
    with open(path, 'r', encoding='utf-8') as f:
        raw = f.read()
    return json.loads(_strip_jsonc(raw))


# ---------------------------------------------------------------------------
# Config discovery and loading
# ---------------------------------------------------------------------------

CONFIG_FILENAME = '.kicad-happy.json'

# Recognized values for validated fields
VALID_MARKETS = {'us', 'eu', 'automotive', 'medical', 'military'}
VALID_DERATING_PROFILES = {'hobby', 'commercial', 'conservative', 'automotive'}
VALID_BOARD_CLASSES = {'class_1', 'class_2', 'class_3'}
VALID_SUPPLIERS = {'digikey', 'mouser', 'lcsc', 'element14'}
VALID_BOM_GROUP_BY = {'value', 'mpn', 'value+footprint'}

# Top-level keys whose list values are concatenated across layers
# instead of replaced.  All other lists use closer-wins semantics.
_ADDITIVE_KEYS = {'suppressions'}

# Default project config (used when no file found)
DEFAULT_CONFIG: Dict[str, Any] = {
    'version': 1,
    'project': {},
    'suppressions': [],
    'preferred_suppliers': [],
    'bom': {},
    'analysis': {
        'output_dir': 'analysis',
        'retention': 5,
        'auto_diff': True,
        'track_in_git': False,
        'diff_threshold': 'major',
        'power_rails': {},
    },
}


# ---------------------------------------------------------------------------
# Deep merge
# ---------------------------------------------------------------------------

def _deep_merge(base: Dict[str, Any], override: Dict[str, Any],
                _path: str = '') -> Dict[str, Any]:
    """Recursively merge *override* into *base*, returning a new dict.

    - Dict values are merged recursively (override keys win on conflict).
    - List values under keys in _ADDITIVE_KEYS are concatenated
      (base items first, then override items).
    - All other values (including non-additive lists) from *override*
      replace the corresponding *base* value entirely.
    """
    merged: Dict[str, Any] = {}
    all_keys = set(base) | set(override)
    for key in all_keys:
        full_key = f'{_path}.{key}' if _path else key
        if key in override and key in base:
            bval = base[key]
            oval = override[key]
            if isinstance(bval, dict) and isinstance(oval, dict):
                merged[key] = _deep_merge(bval, oval, full_key)
            elif isinstance(bval, list) and isinstance(oval, list) \
                    and key in _ADDITIVE_KEYS:
                merged[key] = bval + oval
            else:
                merged[key] = oval
        elif key in override:
            merged[key] = override[key]
        else:
            merged[key] = base[key]
    return merged


# ---------------------------------------------------------------------------
# Discovery and cascading load
# ---------------------------------------------------------------------------

def _discover_config_paths(search_dir: str) -> List[str]:
    """Walk upward from *search_dir* collecting all .kicad-happy.json paths.

    Returns paths ordered from farthest (most general) to closest
    (most specific).  Also includes ~/.kicad-happy.json as the base
    layer if it exists and was not already found during the walk.
    """
    found: List[str] = []
    seen: set = set()
    d = os.path.abspath(search_dir)
    for _ in range(50):  # depth limit
        candidate = os.path.join(d, CONFIG_FILENAME)
        real = os.path.realpath(candidate)
        if os.path.isfile(candidate) and real not in seen:
            found.append(candidate)
            seen.add(real)
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent

    # Check ~/.kicad-happy.json as a user-level base layer
    home_cfg = os.path.join(os.path.expanduser('~'), CONFIG_FILENAME)
    if os.path.isfile(home_cfg) and os.path.realpath(home_cfg) not in seen:
        found.append(home_cfg)

    # Reverse: farthest first so closer layers override during merge
    found.reverse()
    return found


def load_config(search_dir: str) -> Dict[str, Any]:
    """Discover and merge all .kicad-happy.json files from *search_dir* upward.

    Config files are merged with cascading precedence: files closer to
    the project directory override those farther away.  The user-level
    ~/.kicad-happy.json is the base layer (lowest precedence).

    Merge rules:
      - Dict values: deep-merged recursively, closer keys win.
      - "suppressions": concatenated across all layers (additive).
      - Other lists: closer layer wins entirely.

    Returns the merged config dict, or DEFAULT_CONFIG if no files found.
    Prints warnings to stderr on parse errors (those files are skipped).
    """
    paths = _discover_config_paths(search_dir)
    if not paths:
        return dict(DEFAULT_CONFIG)

    merged = dict(DEFAULT_CONFIG)
    for path in paths:
        layer = _load_and_validate(path)
        if layer is not None:
            merged = _deep_merge(merged, layer)

    return merged


def load_config_from_path(path: str) -> Dict[str, Any]:
    """Load config from an explicit file path (for --config CLI arg).

    No cascading — loads only the specified file.
    """
    if not path or not os.path.isfile(path):
        return dict(DEFAULT_CONFIG)
    cfg = _load_and_validate(path)
    return cfg if cfg is not None else dict(DEFAULT_CONFIG)


def _load_and_validate(path: str) -> Optional[Dict[str, Any]]:
    """Load, validate, and return config from *path*.

    Returns None on parse errors (caller should skip this layer).
    """
    import sys
    try:
        cfg = load_jsonc(path)
    except (json.JSONDecodeError, OSError) as exc:
        print(f'Warning: failed to parse {path}: {exc}', file=sys.stderr)
        return None

    if not isinstance(cfg, dict):
        print(f'Warning: {path} root must be an object', file=sys.stderr)
        return None

    # Validate suppressions if present
    raw_suppressions = cfg.get('suppressions')
    if raw_suppressions is not None:
        valid_suppressions = []
        for i, s in enumerate(raw_suppressions):
            if not isinstance(s, dict):
                print(f'Warning: {path}: suppressions[{i}] is not an object, '
                      f'skipping', file=sys.stderr)
                continue
            if 'rule_id' not in s:
                print(f'Warning: {path}: suppressions[{i}] missing required '
                      f'"rule_id", skipping', file=sys.stderr)
                continue
            valid_suppressions.append(s)
        cfg['suppressions'] = valid_suppressions

    # Validate preferred_suppliers
    raw_suppliers = cfg.get('preferred_suppliers')
    if raw_suppliers is not None:
        if not isinstance(raw_suppliers, list):
            print(f'Warning: {path}: preferred_suppliers must be a list, '
                  f'ignoring', file=sys.stderr)
            del cfg['preferred_suppliers']
        else:
            valid = [s for s in raw_suppliers
                     if isinstance(s, str) and s in VALID_SUPPLIERS]
            invalid = [s for s in raw_suppliers
                       if not isinstance(s, str) or s not in VALID_SUPPLIERS]
            if invalid:
                print(f'Warning: {path}: preferred_suppliers: unknown '
                      f'suppliers {invalid}, ignoring them', file=sys.stderr)
            cfg['preferred_suppliers'] = valid

    # Validate bom section
    raw_bom = cfg.get('bom')
    if raw_bom is not None:
        if not isinstance(raw_bom, dict):
            print(f'Warning: {path}: bom must be an object, ignoring',
                  file=sys.stderr)
            del cfg['bom']
        else:
            group_by = raw_bom.get('group_by')
            if group_by is not None and group_by not in VALID_BOM_GROUP_BY:
                print(f'Warning: {path}: bom.group_by "{group_by}" invalid '
                      f'(expected {VALID_BOM_GROUP_BY}), ignoring',
                      file=sys.stderr)
                del raw_bom['group_by']

    # Validate analysis.power_rails
    raw_analysis = cfg.get('analysis')
    if isinstance(raw_analysis, dict):
        raw_pr = raw_analysis.get('power_rails')
        if raw_pr is not None:
            if not isinstance(raw_pr, dict):
                print(f'Warning: {path}: analysis.power_rails must be an '
                      f'object, ignoring', file=sys.stderr)
                del raw_analysis['power_rails']
            else:
                for list_key in ('ignore', 'flag'):
                    val = raw_pr.get(list_key)
                    if val is not None and not isinstance(val, list):
                        print(f'Warning: {path}: analysis.power_rails.'
                              f'{list_key} must be a list, ignoring',
                              file=sys.stderr)
                        del raw_pr[list_key]
                overrides = raw_pr.get('voltage_overrides')
                if overrides is not None:
                    if not isinstance(overrides, dict):
                        print(f'Warning: {path}: analysis.power_rails.'
                              f'voltage_overrides must be an object, '
                              f'ignoring', file=sys.stderr)
                        del raw_pr['voltage_overrides']
                    else:
                        bad = [k for k, v in overrides.items()
                               if not isinstance(v, (int, float))]
                        for k in bad:
                            print(f'Warning: {path}: analysis.power_rails.'
                                  f'voltage_overrides.{k} must be numeric, '
                                  f'ignoring', file=sys.stderr)
                            del overrides[k]

    return cfg


# ---------------------------------------------------------------------------
# Design intent resolution
# ---------------------------------------------------------------------------

_IPC_CLASS_PATTERNS = [
    re.compile(r'IPC.?6012.*Class\s*([123])', re.IGNORECASE),
    re.compile(r'IPC.?Class\s*([123])', re.IGNORECASE),
    re.compile(r'IPC.?6012E([MS])', re.IGNORECASE),  # EM=medical, ES=mil → Class 3
]

# Pattern that only matches "Class N" when near IPC context (avoid false matches)
_IPC_CONTEXT_PATTERN = re.compile(
    r'IPC.*?Class\s*([123])|Class\s*([123]).*?IPC', re.IGNORECASE | re.DOTALL
)

VALID_PRODUCT_CLASSES = {'prototype', 'production'}
VALID_TARGET_MARKETS = {'hobby', 'consumer', 'industrial', 'medical',
                        'automotive', 'aerospace'}
VALID_IPC_CLASSES = {1, 2, 3}
VALID_PASSIVE_SIZES = {'0201', '0402', '0603', '0805', '1206'}


def _detect_ipc_class_from_text(text: str) -> Optional[int]:
    """Try to extract IPC class from a block of text (fab notes, title block).

    Returns 1, 2, or 3 if found, None otherwise.
    """
    for pat in _IPC_CLASS_PATTERNS:
        m = pat.search(text)
        if m:
            val = m.group(1)
            if val in ('M', 'S'):  # IPC-6012EM or IPC-6012ES → Class 3
                return 3
            return int(val)
    # Broader context pattern
    m = _IPC_CONTEXT_PATTERN.search(text)
    if m:
        val = m.group(1) or m.group(2)
        if val:
            return int(val)
    return None


def resolve_design_intent(config: Dict[str, Any],
                          schematic_data: Optional[Dict[str, Any]] = None,
                          pcb_data: Optional[Dict[str, Any]] = None,
                          ) -> Dict[str, Any]:
    """Resolve design intent from explicit config + auto-detected signals.

    Merges explicit ``design_intent`` from ``.kicad-happy.json`` with
    heuristic auto-detection from raw schematic/PCB data.  Each field
    uses the highest-precedence source available:

    1. Explicit config (``source: "config"``)
    2. PCB fab notes text (``source: "pcb_fab_notes"``)
    3. Schematic title block (``source: "schematic_title"``)
    4. Auto-inference from design characteristics (``source: "auto"``)

    Args:
        config: Loaded ``.kicad-happy.json`` (may contain ``design_intent``).
        schematic_data: Optional dict with keys: ``components`` (list),
            ``title_block`` (dict with text fields).
        pcb_data: Optional dict with keys: ``layers`` (list), ``text_items``
            (list of dicts with ``text`` and ``layer``), ``net_classes``
            (list), ``footprints`` (list), ``metadata`` (dict),
            ``board_area_mm2`` (float).

    Returns:
        Resolved design intent dict with ``confidence``,
        ``detection_signals``, and ``source`` per field.
    """
    explicit = config.get('design_intent', {})
    sch = schematic_data or {}
    pcb = pcb_data or {}

    signals: List[str] = []
    source: Dict[str, str] = {}
    confidence = 0.3  # baseline — no signals either way

    # --- Resolve IPC class ---
    ipc_class = 2  # default
    ipc_source = 'auto'

    if 'ipc_class' in explicit and explicit['ipc_class'] in VALID_IPC_CLASSES:
        ipc_class = explicit['ipc_class']
        ipc_source = 'config'
        signals.append(f'IPC class {ipc_class} from config')
    else:
        # Try PCB fab notes / comments layer text
        pcb_texts = pcb.get('text_items', [])
        for item in pcb_texts:
            text = item.get('text', '')
            layer = item.get('layer', '')
            if not text:
                continue
            # Check fab, comments, and user layers
            if any(k in layer for k in ('Fab', 'User', 'Cmts', 'Comments')):
                detected = _detect_ipc_class_from_text(text)
                if detected is not None:
                    ipc_class = detected
                    ipc_source = 'pcb_fab_notes'
                    signals.append(
                        f'IPC Class {detected} detected in PCB text: '
                        f'"{text[:60]}"')
                    break

        # Try PCB title block
        if ipc_source == 'auto':
            tb = pcb.get('metadata', {})
            for field in ('title', 'rev', 'company'):
                val = tb.get(field, '')
                if val:
                    detected = _detect_ipc_class_from_text(val)
                    if detected is not None:
                        ipc_class = detected
                        ipc_source = 'pcb_title_block'
                        signals.append(
                            f'IPC Class {detected} in PCB title block '
                            f'{field}: "{val[:60]}"')
                        break
            # Check PCB title block comments
            if ipc_source == 'auto':
                for _, val in tb.get('comments', {}).items():
                    detected = _detect_ipc_class_from_text(str(val))
                    if detected is not None:
                        ipc_class = detected
                        ipc_source = 'pcb_title_block'
                        signals.append(
                            f'IPC Class {detected} in PCB title block '
                            f'comment: "{str(val)[:60]}"')
                        break

        # Try schematic title block
        if ipc_source == 'auto':
            sch_tb = sch.get('title_block', {})
            for field in ('title', 'rev', 'company', 'comment1',
                          'comment2', 'comment3', 'comment4'):
                val = sch_tb.get(field, '')
                if val:
                    detected = _detect_ipc_class_from_text(val)
                    if detected is not None:
                        ipc_class = detected
                        ipc_source = 'schematic_title'
                        signals.append(
                            f'IPC Class {detected} in schematic title '
                            f'block: "{val[:60]}"')
                        break

    source['ipc_class'] = ipc_source

    # --- Auto-detect product class ---
    product_class = 'prototype'  # default
    prod_source = 'auto'
    prod_confidence = 0.0

    if 'product_class' in explicit \
            and explicit['product_class'] in VALID_PRODUCT_CLASSES:
        product_class = explicit['product_class']
        prod_source = 'config'
        signals.append(f'Product class "{product_class}" from config')
    else:
        # Layer count
        layers = pcb.get('layers', [])
        copper_layers = [l for l in layers
                         if isinstance(l, dict) and 'Cu' in l.get('name', '')]
        if len(copper_layers) > 4:
            prod_confidence += 0.15
            signals.append(f'{len(copper_layers)}-layer board detected')

        # Component count
        components = sch.get('components', []) or pcb.get('footprints', [])
        if len(components) > 150:
            prod_confidence += 0.1
            signals.append(f'{len(components)} components')

        # Controlled impedance net classes
        net_classes = pcb.get('net_classes', [])
        non_default = [nc for nc in net_classes
                       if nc.get('name', '') != 'Default'
                       and nc.get('track_width') is not None]
        if non_default:
            prod_confidence += 0.1
            signals.append('controlled impedance net classes present')

        # Fab notes text present
        pcb_texts = pcb.get('text_items', [])
        fab_texts = [t for t in pcb_texts
                     if any(k in t.get('layer', '')
                            for k in ('Fab', 'User', 'Cmts'))]
        if fab_texts:
            prod_confidence += 0.15
            signals.append('fab notes text present on PCB')

        # Test points (TP* reference designators)
        fp_refs = [fp.get('reference', '')
                   for fp in pcb.get('footprints', [])]
        tp_count = sum(1 for r in fp_refs if r.startswith('TP'))
        if tp_count > 0:
            prod_confidence += 0.1
            signals.append(f'{tp_count} test points (TP*) detected')

        # Fiducials
        fid_count = sum(1 for r in fp_refs if r.startswith('FID'))
        if fid_count > 0:
            prod_confidence += 0.1
            signals.append(f'{fid_count} fiducials detected')

        # Multiple ground domains (heuristic: multiple GND-like net names)
        net_names = pcb.get('net_names', {})
        gnd_nets = [n for n in net_names.values()
                    if re.match(r'(?i)(A?GND|DGND|PGND|SGND|EARTH)',
                                n.replace('/', ''))]
        if len(gnd_nets) >= 2:
            prod_confidence += 0.05
            signals.append(f'{len(gnd_nets)} ground domains detected')

        # Board area
        board_area = pcb.get('board_area_mm2', 0)
        if board_area > 10000:  # > 100 cm²
            prod_confidence += 0.05
            signals.append(
                f'board area {board_area:.0f}mm² (>{100}cm²)')

        if prod_confidence >= 0.3:
            product_class = 'production'

    source['product_class'] = prod_source
    confidence = max(confidence,
                     prod_confidence + 0.3)  # baseline + accumulated
    confidence = min(confidence, 1.0)

    # --- Auto-detect target market ---
    target_market = 'hobby'  # default
    market_source = 'auto'

    if 'target_market' in explicit \
            and explicit['target_market'] in VALID_TARGET_MARKETS:
        target_market = explicit['target_market']
        market_source = 'config'
        signals.append(f'Target market "{target_market}" from config')
    else:
        # Check component characteristics for market signals
        components = sch.get('components', [])
        aec_q_count = 0
        mil_count = 0
        for comp in components:
            mpn = comp.get('mpn', '') or comp.get('MPN', '') or ''
            value = comp.get('value', '')
            fields_text = f'{mpn} {value}'
            if re.search(r'AEC.?Q', fields_text, re.IGNORECASE):
                aec_q_count += 1
            if re.search(r'MIL.?STD|MIL.?PRF|ITAR|QPL', fields_text,
                         re.IGNORECASE):
                mil_count += 1

        if mil_count >= 2:
            target_market = 'aerospace'
            confidence = min(confidence + 0.2, 1.0)
            signals.append(f'{mil_count} MIL-STD/military-grade parts')
        elif aec_q_count >= 3:
            target_market = 'automotive'
            confidence = min(confidence + 0.2, 1.0)
            signals.append(f'{aec_q_count} AEC-Q qualified parts')
        elif product_class == 'production':
            target_market = 'consumer'

        # IPC class can also inform market
        if ipc_class == 3 and target_market in ('hobby', 'consumer'):
            target_market = 'industrial'
            signals.append('IPC Class 3 suggests industrial or higher')

    source['target_market'] = market_source

    # --- IPC class fallback from market (if not detected from text) ---
    if ipc_source == 'auto':
        if target_market in ('aerospace',):
            ipc_class = 3
            confidence = max(0, confidence - 0.1)
            signals.append(
                f'IPC Class 3 inferred from {target_market} market')
        elif target_market == 'medical':
            ipc_class = 3
            confidence = max(0, confidence - 0.15)
            signals.append(
                'IPC Class 3 inferred from medical market '
                '(not all medical is Class 3)')

    # --- Resolve remaining fields from config or defaults ---
    defaults = {
        'expected_lifetime_years': 5,
        'operating_temp_range': [-10, 70],  # commercial default
        'preferred_passive_size': '0603',
        'test_coverage_target': 0.85,
        'approved_manufacturers': [],
    }

    # Adjust defaults based on market
    if target_market in ('industrial', 'medical'):
        defaults['operating_temp_range'] = [-40, 85]
        defaults['test_coverage_target'] = 0.90
        defaults['expected_lifetime_years'] = 10
    elif target_market == 'automotive':
        defaults['operating_temp_range'] = [-40, 125]
        defaults['test_coverage_target'] = 0.95
        defaults['expected_lifetime_years'] = 15
    elif target_market == 'aerospace':
        defaults['operating_temp_range'] = [-55, 125]
        defaults['test_coverage_target'] = 0.98
        defaults['expected_lifetime_years'] = 20

    result = {
        'product_class': product_class,
        'ipc_class': ipc_class,
        'target_market': target_market,
    }
    for key, default in defaults.items():
        if key in explicit:
            result[key] = explicit[key]
            source[key] = 'config'
        else:
            result[key] = default
            source[key] = 'auto'

    # Handle temp range from separate min/max config fields
    if 'operating_temp_min' in explicit or 'operating_temp_max' in explicit:
        t_range = result.get('operating_temp_range', defaults['operating_temp_range'])
        result['operating_temp_range'] = [
            explicit.get('operating_temp_min', t_range[0]),
            explicit.get('operating_temp_max', t_range[1]),
        ]
        source['operating_temp_range'] = 'config'

    result['confidence'] = round(confidence, 2)
    result['detection_signals'] = signals
    result['source'] = source

    return result


def apply_power_rails_config(
        rail_voltages: Dict[str, float],
        power_rails_list: list,
        config: Dict[str, Any],
) -> tuple:
    """Apply power_rails config to analysis output.

    Filters ignored rails, marks flagged rails, applies voltage overrides.

    Args:
        rail_voltages: {net_name: voltage} dict from signal analysis.
        power_rails_list: [{name, voltage}] list from statistics.
        config: Loaded .kicad-happy.json config.

    Returns:
        (filtered_rail_voltages, filtered_power_rails, flagged_rails)
        where flagged_rails is a list of net names matching flag patterns.
    """
    pr_cfg = config.get('analysis', {}).get('power_rails', {})
    if not pr_cfg:
        return rail_voltages, power_rails_list, []

    ignore_patterns = pr_cfg.get('ignore', [])
    flag_patterns = pr_cfg.get('flag', [])
    voltage_overrides = pr_cfg.get('voltage_overrides', {})

    def _is_ignored(name: str) -> bool:
        return any(fnmatch(name, pat) for pat in ignore_patterns)

    def _is_flagged(name: str) -> bool:
        return any(fnmatch(name, pat) for pat in flag_patterns)

    # Filter rail_voltages
    filtered_rv = {}
    for name, voltage in rail_voltages.items():
        if _is_ignored(name):
            continue
        v = voltage_overrides.get(name, voltage)
        filtered_rv[name] = v

    # Filter power_rails list
    filtered_pr = []
    for rail in power_rails_list:
        rname = rail.get('name', '')
        if _is_ignored(rname):
            continue
        entry = dict(rail)
        if rname in voltage_overrides:
            entry['voltage'] = voltage_overrides[rname]
        filtered_pr.append(entry)

    # Collect flagged rails
    flagged = [name for name in filtered_rv if _is_flagged(name)]

    return filtered_rv, filtered_pr, flagged


def get_preferred_suppliers(config: Dict[str, Any]) -> List[str]:
    """Return preferred_suppliers from config, or empty list."""
    return config.get('preferred_suppliers', [])


# ---------------------------------------------------------------------------
# Suppression matching
# ---------------------------------------------------------------------------

def matches_suppression(finding: Dict[str, Any],
                        suppression: Dict[str, Any]) -> bool:
    """Check whether *finding* matches a *suppression* entry.

    Matching rules:
    - rule_id: must match exactly (required).
    - components: if present, at least one finding component must match
      at least one suppression component pattern (fnmatch globs).
    - nets: if present, at least one finding net must match at least one
      suppression net pattern (fnmatch globs).
    """
    # rule_id must match
    if finding.get('rule_id', '') != suppression.get('rule_id', ''):
        return False

    # Component match (optional filter)
    sup_components = suppression.get('components')
    if sup_components:
        finding_components = finding.get('components', [])
        if not finding_components:
            return False
        if not any(fnmatch(fc, sp) for fc in finding_components
                   for sp in sup_components):
            return False

    # Net match (optional filter)
    sup_nets = suppression.get('nets')
    if sup_nets:
        finding_nets = finding.get('nets', [])
        if not finding_nets:
            return False
        # KH-359: finding nets may carry sheet-qualified keys
        # (/<sheet>/<name>); fall back to matching the bare tail so
        # existing suppression patterns written against bare names
        # still apply.
        def _net_candidates(fn: str) -> set:
            candidates = {fn}
            if fn.startswith("/") and fn.count("/") >= 2:
                candidates.add(fn.rsplit("/", 1)[-1])
            return candidates
        if not any(fnmatch(c, sp) for fn in finding_nets
                   for c in _net_candidates(fn) for sp in sup_nets):
            return False

    return True


def apply_suppressions(findings: List[Dict[str, Any]],
                       suppressions: List[Dict[str, Any]],
                       ) -> List[Dict[str, Any]]:
    """Mark findings that match any suppression entry.

    Adds to each finding:
    - "suppressed": bool
    - "suppression_reason": str (reason from matching suppression, or "")

    Findings are never removed — only marked. Returns the same list.
    """
    if not suppressions:
        for f in findings:
            f.setdefault('suppressed', False)
            f.setdefault('suppression_reason', '')
        return findings

    for f in findings:
        matched = False
        reason = ''
        for s in suppressions:
            if matches_suppression(f, s):
                matched = True
                reason = s.get('reason', '')
                break
        f['suppressed'] = matched
        f['suppression_reason'] = reason

    return findings


def count_by_severity(findings: List[Dict[str, Any]],
                      ) -> Dict[str, Dict[str, int]]:
    """Count findings by severity, split into active and suppressed.

    Returns::

        {
            "active": {"CRITICAL": 2, "HIGH": 3, ...},
            "suppressed": {"CRITICAL": 0, "HIGH": 1, ...},
            "total": {"CRITICAL": 2, "HIGH": 4, ...},
        }
    """
    active: Dict[str, int] = {}
    suppressed: Dict[str, int] = {}
    total: Dict[str, int] = {}

    for f in findings:
        sev = f.get('severity', 'INFO')
        total[sev] = total.get(sev, 0) + 1
        if f.get('suppressed'):
            suppressed[sev] = suppressed.get(sev, 0) + 1
        else:
            active[sev] = active.get(sev, 0) + 1

    return {'active': active, 'suppressed': suppressed, 'total': total}


# ---------------------------------------------------------------------------
# Risk scoring (used by top-risk summary, Feature 4)
# ---------------------------------------------------------------------------

SEVERITY_WEIGHTS = {
    'CRITICAL': 15, 'HIGH': 8, 'MEDIUM': 3, 'LOW': 1, 'INFO': 0,
}

CONFIDENCE_WEIGHTS = {
    'deterministic': 1.0,
    'datasheet-backed': 0.9,
    'heuristic': 0.7,
    'ai-inferred': 0.5,
}

# Category → risk bucket(s) with boost multiplier
RESPIN_CATEGORIES = {
    'ground_plane', 'stackup', 'diff_pair', 'board_edge',
    'pdn', 'via_stitching', 'return_path',
}
BRINGUP_CATEGORIES = {
    'thermal_safety', 'switching_emc', 'pdn', 'esd_path',
}
MANUFACTURING_CATEGORIES = {
    'dfm_violation', 'tombstoning', 'documentation', 'thermal_pad_vias',
}

BUCKET_BOOSTS = {
    'respin': 1.5,
    'bringup': 1.3,
    'manufacturing': 1.2,
}


def compute_finding_risk(finding: Dict[str, Any], bucket: str) -> float:
    """Compute risk score for a single finding in a specific bucket."""
    sev = SEVERITY_WEIGHTS.get(finding.get('severity', 'INFO'), 0)
    conf = CONFIDENCE_WEIGHTS.get(finding.get('confidence', 'heuristic'), 0.7)
    boost = BUCKET_BOOSTS.get(bucket, 1.0)
    return sev * conf * boost


def classify_finding_buckets(finding: Dict[str, Any]) -> List[str]:
    """Return which risk buckets a finding belongs to."""
    cat = finding.get('category', '')
    buckets = []
    if cat in RESPIN_CATEGORIES:
        buckets.append('respin')
    if cat in BRINGUP_CATEGORIES:
        buckets.append('bringup')
    if cat in MANUFACTURING_CATEGORIES:
        buckets.append('manufacturing')
    return buckets


def compute_top_risks(all_findings: List[Dict[str, Any]],
                      top_n: int = 3,
                      ) -> Dict[str, List[Dict[str, Any]]]:
    """Compute top-N findings per risk bucket across all analyzers.

    Each finding in *all_findings* should have: severity, confidence,
    category, rule_id, title, source (analyzer name).

    Returns::

        {
            "respin": [top 3 findings],
            "bringup": [top 3 findings],
            "manufacturing": [top 3 findings],
        }

    Only includes active (non-suppressed) findings.
    """
    buckets: Dict[str, List[tuple]] = {
        'respin': [], 'bringup': [], 'manufacturing': [],
    }

    for f in all_findings:
        if f.get('suppressed'):
            continue
        for bucket in classify_finding_buckets(f):
            score = compute_finding_risk(f, bucket)
            if score > 0:
                buckets[bucket].append((score, f))

    result: Dict[str, List[Dict[str, Any]]] = {}
    for bucket, scored in buckets.items():
        scored.sort(key=lambda x: x[0], reverse=True)
        result[bucket] = [f for _, f in scored[:top_n]]

    return result
