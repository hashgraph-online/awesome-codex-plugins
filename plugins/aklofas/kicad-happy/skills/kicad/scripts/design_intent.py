"""Design intent resolution for kicad-happy.

Merges the explicit ``design_intent`` block of ``.kicad-happy.json`` with
signals auto-detected from the schematic and PCB (IPC class, product class,
target market, operating environment). Pure computation, no file I/O.

Zero external dependencies - stdlib only.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

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
