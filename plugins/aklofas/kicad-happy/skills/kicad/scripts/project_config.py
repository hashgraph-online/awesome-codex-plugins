"""
Project configuration and suppression matching for kicad-happy.

Loads .kicad-happy.json (JSONC with comment stripping) with cascading
config: files found closer to the project override those farther away,
and ~/.kicad-happy.json serves as a user-level base layer.

Merge rules:
  - Dicts: deep-merged recursively, closer keys win
  - "suppressions": concatenated across all layers (additive)
  - Other lists: closer layer wins entirely

Provides suppression matching with fnmatch globs, power-rail overrides
and supplier preferences shared across all analyzers.

Zero external dependencies — stdlib only.
"""

from __future__ import annotations

import json
import os
from fnmatch import fnmatch
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# standalone load by file path (harness spec_from_file_location, docs)
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))
from kicad_core.project import load_jsonc
from kicad_core.model import ResolvedConfig
from kicad_core.diagnostics import record
from kicad_core.sexp import unescape_string
from kicad_core.netnames import configured_rail_voltage, rail_matches


# ---------------------------------------------------------------------------
# Config discovery and loading
# ---------------------------------------------------------------------------

CONFIG_FILENAME = '.kicad-happy.json'

# Recognized values for validated fields
VALID_SUPPLIERS = {'digikey', 'mouser', 'lcsc', 'element14'}
VALID_BOM_GROUP_BY = {'value', 'mpn', 'value+footprint'}
VALID_DIFF_THRESHOLDS = {'all', 'minor', 'major', 'breaking'}

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
        'retention': 0,
        'auto_diff': True,
        'track_in_git': False,
        'diff_threshold': 'major',
        'power_rails': {},
    },
}


# ---------------------------------------------------------------------------
# Deep merge
# ---------------------------------------------------------------------------

def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge *override* into *base*, returning a new dict.

    - Dict values are merged recursively (override keys win on conflict).
    - List values under keys in _ADDITIVE_KEYS are concatenated
      (base items first, then override items).
    - All other values (including non-additive lists) from *override*
      replace the corresponding *base* value entirely.
    """
    merged: Dict[str, Any] = {}
    all_keys = list(base) + [k for k in override if k not in base]
    for key in all_keys:
        if key in override and key in base:
            bval = base[key]
            oval = override[key]
            if isinstance(bval, dict) and isinstance(oval, dict):
                merged[key] = _deep_merge(bval, oval)
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
    if not path:
        return dict(DEFAULT_CONFIG)
    if not os.path.isfile(path):
        print(f"Warning: config file not found: {path}; using built-in defaults", file=sys.stderr)
        return dict(DEFAULT_CONFIG)
    cfg = _load_and_validate(path)
    return cfg if cfg is not None else dict(DEFAULT_CONFIG)


def resolve_config(explicit_path: Optional[str], search_dir: str) -> ResolvedConfig:
    """The one place that decides which config applies and which file is hashed.

    Explicit (``--config PATH``): that file only, no cascade -- ``load_config_from_path``.
    Discovered: the cascade ``load_config`` performs from *search_dir*.
    ``hash_input`` reproduces the CLIs' historical rule: the explicit file when it exists,
    else ``<search_dir>/.kicad-happy.json`` when it exists, else None.
    """
    if explicit_path:
        exists = os.path.isfile(explicit_path)
        return ResolvedConfig(load_config_from_path(explicit_path),
                              (explicit_path,) if exists else (), explicit_path if exists else None)
    default = os.path.join(search_dir, CONFIG_FILENAME)
    return ResolvedConfig(load_config(search_dir),
                          tuple(_discover_config_paths(search_dir)),
                          default if os.path.isfile(default) else None)


def _load_and_validate(path: str) -> Optional[Dict[str, Any]]:
    """Load, validate, and return config from *path*.

    Returns None on parse errors (caller should skip this layer).
    """
    import sys
    try:
        cfg = load_jsonc(path)
    except (ValueError, RecursionError, OSError) as exc:
        print(f'Warning: failed to parse {path}: {exc}', file=sys.stderr)
        return None

    if not isinstance(cfg, dict):
        print(f'Warning: {path} root must be an object', file=sys.stderr)
        return None

    def _wrong_type(container: dict, key: str, label: str, expected: str) -> None:
        record(None, "project_config._load_and_validate",
               TypeError(f"{path}: {label} must be {expected}, got "
                         f"{type(container[key]).__name__}"),
               f"{label} ignored, default used")
        del container[key]

    # Validate suppressions if present
    raw_suppressions = cfg.get('suppressions')
    if raw_suppressions is not None and not isinstance(raw_suppressions, list):
        _wrong_type(cfg, 'suppressions', 'suppressions', 'a list')
        raw_suppressions = None
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
            # A pattern list given as one string is one pattern, not one per character.
            bad_patterns = False
            for list_key in ('components', 'nets'):
                val = s.get(list_key)
                if isinstance(val, str):
                    record(None, "project_config._load_and_validate",
                           TypeError(f"{path}: suppressions[{i}].{list_key} must be a list, got str"),
                           f"suppressions[{i}].{list_key} read as a one-element list")
                    s[list_key] = [val]
                elif val is not None and not isinstance(val, list):
                    record(None, "project_config._load_and_validate",
                           TypeError(f"{path}: suppressions[{i}].{list_key} must be a list, got "
                                     f"{type(val).__name__}"),
                           f"suppressions[{i}] ignored")
                    bad_patterns = True
                elif isinstance(val, list) and not all(isinstance(p, str) for p in val):
                    # Dropped whole: a list pruned to [] would match every finding of the rule.
                    record(None, "project_config._load_and_validate",
                           TypeError(f"{path}: suppressions[{i}].{list_key} must be a list of strings"),
                           f"suppressions[{i}] ignored")
                    bad_patterns = True
            if bad_patterns:
                continue
            valid_suppressions.append(s)
        cfg['suppressions'] = valid_suppressions

    # Validate project section (ambient temperature feeds thermal arithmetic)
    raw_project = cfg.get('project')
    if 'project' in cfg:
        if not isinstance(raw_project, dict):
            _wrong_type(cfg, 'project', 'project', 'an object')
        else:
            ambient = raw_project.get('ambient_temperature_c')
            if ambient is not None and (isinstance(ambient, bool)
                                        or not isinstance(ambient, (int, float))):
                _wrong_type(raw_project, 'ambient_temperature_c',
                            'project.ambient_temperature_c', 'a number')

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
            if group_by is not None and not isinstance(group_by, str):
                _wrong_type(raw_bom, 'group_by', 'bom.group_by', 'a string')
            elif group_by is not None and group_by not in VALID_BOM_GROUP_BY:
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

        # Analysis-cache knobs: an invalid value is warned and dropped (the default applies).
        retention = raw_analysis.get('retention')
        if retention is not None and (isinstance(retention, bool) or not isinstance(retention, int)
                                      or retention < 0):
            print(f'Warning: {path}: analysis.retention must be a non-negative '
                  f'integer, ignoring', file=sys.stderr)
            del raw_analysis['retention']
        threshold = raw_analysis.get('diff_threshold')
        if threshold is not None and (not isinstance(threshold, str)
                                      or threshold not in VALID_DIFF_THRESHOLDS):
            print(f'Warning: {path}: analysis.diff_threshold "{threshold}" invalid '
                  f'(expected {sorted(VALID_DIFF_THRESHOLDS)}), ignoring', file=sys.stderr)
            del raw_analysis['diff_threshold']
        output_dir = raw_analysis.get('output_dir')
        if output_dir is not None and (not isinstance(output_dir, str) or not output_dir):
            print(f'Warning: {path}: analysis.output_dir must be a non-empty '
                  f'string, ignoring', file=sys.stderr)
            del raw_analysis['output_dir']

    # Validate design_intent types (values outside the vocabularies already fall back to auto)
    if 'design_intent' in cfg:
        raw_intent = cfg['design_intent']
        if not isinstance(raw_intent, dict):
            _wrong_type(cfg, 'design_intent', 'design_intent', 'an object')
        else:
            def _is_number(v):
                return isinstance(v, (int, float)) and not isinstance(v, bool)
            checks = (
                ('product_class', lambda v: isinstance(v, str), 'a string'),
                ('target_market', lambda v: isinstance(v, str), 'a string'),
                ('ipc_class', _is_number, 'a number'),
                ('expected_lifetime_years', _is_number, 'a number'),
                ('test_coverage_target', _is_number, 'a number'),
                ('operating_temp_range',
                 lambda v: isinstance(v, list) and len(v) == 2 and all(_is_number(t) for t in v),
                 'a [min, max] list of numbers'),
                ('operating_temp_min', _is_number, 'a number'),
                ('operating_temp_max', _is_number, 'a number'),
            )
            for key, ok, expected in checks:
                if key in raw_intent and not ok(raw_intent[key]):
                    _wrong_type(raw_intent, key, f'design_intent.{key}', expected)

    return cfg


def apply_power_rails_config(
        rail_voltages: Dict[str, float],
        power_rails_list: list,
        config: Dict[str, Any],
) -> tuple:
    """Apply power_rails config to analysis output.

    Filters ignored rails, marks flagged rails, applies voltage overrides. The
    schematic pipeline already applies ``ignore`` and ``voltage_overrides`` before
    detection, so on its output this only adds what the summary lists need: an
    override for a listed rail that had no voltage, and ``source: "config"`` on
    overridden ``power_rails`` entries. ``ignore`` and overrides match a name by
    its full name or leaf; ``flag`` matches the name as written.

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

    # Filter rail_voltages
    filtered_rv = {}
    for name, voltage in rail_voltages.items():
        if rail_matches(ignore_patterns, name):
            continue
        v = configured_rail_voltage(voltage_overrides, name)
        filtered_rv[name] = voltage if v is None else v

    # Filter power_rails list
    filtered_pr = []
    for rail in power_rails_list:
        rname = rail.get('name', '')
        if rail_matches(ignore_patterns, rname):
            continue
        entry = dict(rail)
        v = configured_rail_voltage(voltage_overrides, rname)
        if v is not None:
            entry['voltage'] = v
            entry['source'] = 'config'
            filtered_rv.setdefault(rname, v)
        filtered_pr.append(entry)

    # Collect flagged rails
    flagged = [name for name in filtered_rv
               if any(fnmatch(name, pat) for pat in flag_patterns)]

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
    if isinstance(sup_components, str):
        sup_components = [sup_components]
    if sup_components:
        finding_components = finding.get('components', [])
        if not finding_components:
            return False
        if not any(fnmatch(fc, sp) for fc in finding_components
                   for sp in sup_components):
            return False

    # Net match (optional filter)
    sup_nets = suppression.get('nets')
    if isinstance(sup_nets, str):
        sup_nets = [sup_nets]
    if sup_nets:
        finding_nets = finding.get('nets', [])
        if not finding_nets:
            return False
        # finding nets may carry KiCad's sheet path (/<name> on the root
        # sheet, /<sheet>/<name> below it); fall back to matching the bare
        # tail so suppression patterns written against bare names apply.
        def _net_candidates(fn: str) -> set:
            candidates = {fn}
            if fn.startswith("/"):
                candidates.add(fn.rsplit("/", 1)[-1])
            # A pattern written against the shown name (D1/TX) still
            # matches the escaped net name (D1{slash}TX).
            return candidates | {unescape_string(c) for c in candidates}
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
