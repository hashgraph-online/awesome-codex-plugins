"""KiCad project discovery and project-file readers: .kicad_pro, .kicad_dru, lib tables, root-schematic resolution (kicad_core). Moved verbatim from kicad_utils.py."""
import json
import os

from kicad_core.sexp import parse as _sexp_parse, parse_file as _sexp_parse_file, find_all, find_first, get_value


# ======================================================================
# .kicad_pro project file parsing
# ======================================================================

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
    stripped = ''.join(out)
    # Second pass: drop a comma that is followed only by whitespace and then
    # `}` or `]`, but never inside a string literal (KH-400).
    res = []
    in_str = False
    i, n = 0, len(stripped)
    while i < n:
        c = stripped[i]
        if in_str:
            res.append(c)
            if c == '\\' and i + 1 < n:
                res.append(stripped[i + 1])
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
            res.append(c)
        elif c == ',':
            j = i + 1
            while j < n and stripped[j] in ' \t\r\n':
                j += 1
            if not (j < n and stripped[j] in '}]'):
                res.append(c)
        else:
            res.append(c)
        i += 1
    return ''.join(res)


def load_jsonc(path: str) -> dict:
    """Load a JSONC file, returning parsed dict."""
    with open(path, 'r', encoding='utf-8') as f:
        raw = f.read()
    return json.loads(_strip_jsonc(raw))


def find_project_settings_file(file_path: str, ext: str) -> str | None:
    """Find the ``ext`` file (e.g. ``.kicad_pro``, ``.kicad_dru``) matching
    ``file_path``'s project, in ``file_path``'s directory.

    Shared discovery logic for `load_kicad_pro` / `load_kicad_dru` (KH-362).
    Scans the directory for files ending in ``ext`` and prefers the one
    whose stem matches ``file_path``'s stem (KiCad names project/rules
    files after the board/schematic they belong to). Falls back to the
    sole candidate when there's only one; with multiple candidates and no
    stem match, deterministically picks the first (sorted) candidate and
    warns on stderr (a directory with several projects previously took
    whatever the OS listed first).

    Returns the chosen file's full path, or None if no candidate exists
    or the directory can't be listed.
    """
    import sys as _sys
    parent = os.path.dirname(os.path.abspath(file_path))
    stem = os.path.splitext(os.path.basename(file_path))[0]
    try:
        entries = os.listdir(parent)
    except OSError:
        return None
    candidates = sorted(f for f in entries if f.endswith(ext))
    if not candidates:
        return None

    exact = [f for f in candidates if os.path.splitext(f)[0] == stem]
    if exact:
        chosen = exact[0]
    elif len(candidates) == 1:
        chosen = candidates[0]
    else:
        chosen = candidates[0]
        print(
            "kicad_utils.find_project_settings_file: {0} {1} files in "
            "{2!r}, none match stem {3!r}; using {4!r}".format(
                len(candidates), ext, parent, stem, chosen),
            file=_sys.stderr,
        )

    return os.path.join(parent, chosen)


def load_kicad_pro(file_path: str) -> dict | None:
    """Load .kicad_pro from the same directory as a .kicad_sch or .kicad_pcb file.

    Discovery is stem-matched via `find_project_settings_file` (KH-362) —
    in a multi-project directory, the ``.kicad_pro`` sharing this file's
    stem is preferred over whatever the OS lists first.
    Returns the parsed JSON dict, or None if not found, not valid JSON, or a
    KiCad 5 ``.pro`` file (which uses a different, non-JSON format).
    Tolerates JS-style comments / trailing commas (KH-368-style JSONC).
    """
    pro_path = find_project_settings_file(file_path, '.kicad_pro')
    if not pro_path:
        return None
    try:
        return load_jsonc(pro_path)
    except (ValueError, OSError):
        return None


def is_referenced_as_child(file_path: str) -> bool:
    """Check if a .kicad_sch is referenced as a child sheet by a sibling.

    Scans sibling .kicad_sch files in the same directory for Sheetfile
    properties containing this file's basename.  Used by detect_sub_sheet()
    to distinguish intermediate hierarchy nodes from the root (KH-304).

    Reads the full file because sheet blocks can appear after large
    lib_symbols sections (e.g. 680KB root with sheets at byte 681K).
    """
    abs_path = os.path.abspath(file_path)
    basename = os.path.basename(abs_path)
    parent_dir = os.path.dirname(abs_path)

    try:
        for fname in os.listdir(parent_dir):
            if fname.endswith('.kicad_sch') and fname != basename:
                sibling = os.path.join(parent_dir, fname)
                try:
                    with open(sibling, 'r', encoding='utf-8',
                              errors='replace') as f:
                        content = f.read()
                    if basename in content:
                        return True
                except OSError:
                    continue
    except OSError:
        pass
    return False


def _root_references_target(root_sch: str, target: str) -> bool:
    """Check if root_sch's sheet tree references target (by relative path).

    Handles both same-directory and sub-directory layouts by computing the
    relative path from the root's directory to the target.  Reads the full
    file because sheet blocks can appear after large lib_symbols sections.
    """
    try:
        root_dir = os.path.dirname(os.path.abspath(root_sch))
        target_abs = os.path.abspath(target)
        # Compute the relative path the root would use in Sheetfile property
        rel_path = os.path.relpath(target_abs, root_dir)
        # Also try just the basename (same-directory case)
        basename = os.path.basename(target_abs)

        with open(root_sch, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # Check for relative path or basename in content
        # KiCad uses forward slashes in Sheetfile even on Windows
        for needle in (rel_path, rel_path.replace(os.sep, '/'), basename):
            if needle in content:
                return True
    except OSError:
        pass
    return False


def discover_root_schematic(target_path: str) -> str | None:
    """Find the root .kicad_sch for a sub-sheet file.

    Returns the root schematic path, or None if the target appears to be
    the root or no root can be found.

    Strategy (KH-305, KH-306 hardened):
    1. Same directory: look for .kicad_pro, derive root .kicad_sch.
       When multiple .kicad_pro exist (KH-306), verify each candidate's
       sheet tree references the target.
    2. Same directory: scan sibling .kicad_sch files for references.
    3. Parent directories (KH-305): walk up to 5 levels looking for
       .kicad_pro whose root .kicad_sch references the target via a
       relative path (handles sheets/ subdirectory layouts).
    4. Return None if nothing found.
    """
    target = os.path.abspath(target_path)
    parent_dir = os.path.dirname(target)
    target_basename = os.path.basename(target)

    try:
        entries = os.listdir(parent_dir)
    except OSError:
        entries = []

    # Tier 1: .kicad_pro stem match (same directory)
    # KH-306: when multiple .kicad_pro exist, verify sheet-tree membership
    pro_files = [f for f in entries if f.endswith('.kicad_pro')]

    if len(pro_files) == 1:
        stem = pro_files[0][:-len('.kicad_pro')]
        candidate = os.path.join(parent_dir, stem + '.kicad_sch')
        if os.path.isfile(candidate) and os.path.abspath(candidate) != target:
            return candidate
    elif len(pro_files) > 1:
        # Multiple projects — check which one's sheet tree references us
        for pro in pro_files:
            stem = pro[:-len('.kicad_pro')]
            candidate = os.path.join(parent_dir, stem + '.kicad_sch')
            if (os.path.isfile(candidate)
                    and os.path.abspath(candidate) != target
                    and _root_references_target(candidate, target)):
                return candidate

    # Tier 2: scan sibling .kicad_sch files for (sheet ...) blocks
    siblings = [f for f in entries
                if f.endswith('.kicad_sch') and f != target_basename]
    for fname in siblings:
        candidate = os.path.join(parent_dir, fname)
        try:
            with open(candidate, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            if target_basename in content:
                return candidate
        except OSError:
            continue

    # Tier 3 (KH-305): walk up parent directories looking for .kicad_pro
    # Handles sub-directory layouts (e.g., sheets/video.kicad_sch)
    search_dir = parent_dir
    for _ in range(5):
        search_dir = os.path.dirname(search_dir)
        if search_dir == os.path.dirname(search_dir):
            break  # Hit filesystem root
        try:
            parent_entries = os.listdir(search_dir)
        except OSError:
            continue
        for fname in parent_entries:
            if fname.endswith('.kicad_pro'):
                stem = fname[:-len('.kicad_pro')]
                candidate = os.path.join(search_dir, stem + '.kicad_sch')
                if (os.path.isfile(candidate)
                        and _root_references_target(candidate, target)):
                    return candidate

    return None


def resolve_project_input(path: str, target_ext: str = '.kicad_sch') -> tuple:
    """Resolve a CLI input path to the correct project file.

    Accepts:
      - A ``.kicad_sch`` / ``.kicad_pcb`` file (returned as-is)
      - A ``.kicad_pro`` file (derives the matching target_ext file)
      - A directory (finds ``.kicad_pro`` inside, then derives)

    Args:
        path: User-supplied path (file or directory).
        target_ext: The extension to resolve to (``.kicad_sch`` or
            ``.kicad_pcb``).

    Returns:
        ``(resolved_path, note)`` where *resolved_path* is the absolute
        path to the target file and *note* is a human-readable string
        describing any resolution that occurred (empty when the input
        was already the target type).

    Raises:
        FileNotFoundError: When the input cannot be resolved.
    """
    path = os.path.abspath(path)

    # --- Input is a directory: look for .kicad_pro inside ---
    if os.path.isdir(path):
        pro_files = [f for f in os.listdir(path) if f.endswith('.kicad_pro')]
        if not pro_files:
            raise FileNotFoundError(
                f"No .kicad_pro file found in directory: {path}")
        if len(pro_files) > 1:
            raise FileNotFoundError(
                f"Multiple .kicad_pro files in {path}: {pro_files}")
        pro_stem = pro_files[0][:-len('.kicad_pro')]
        candidate = os.path.join(path, pro_stem + target_ext)
        if not os.path.isfile(candidate):
            raise FileNotFoundError(
                f"Project '{pro_stem}' found but {pro_stem}{target_ext} "
                f"does not exist in {path}")
        return candidate, f"Resolved from directory via {pro_files[0]}"

    # --- Input is a .kicad_pro file ---
    if path.endswith('.kicad_pro'):
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Project file not found: {path}")
        pro_stem = os.path.basename(path)[:-len('.kicad_pro')]
        parent_dir = os.path.dirname(path)
        candidate = os.path.join(parent_dir, pro_stem + target_ext)
        if not os.path.isfile(candidate):
            raise FileNotFoundError(
                f"Project '{pro_stem}' found but {pro_stem}{target_ext} "
                f"does not exist in {parent_dir}")
        return candidate, f"Resolved from {os.path.basename(path)}"

    # --- Input is a KiCad 5 .pro file: the sibling .sch / .kicad_pcb ---
    if path.endswith('.pro'):
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Project file not found: {path}")
        pro_stem = os.path.basename(path)[:-len('.pro')]
        parent_dir = os.path.dirname(path)
        exts = ('.sch', '.kicad_sch') if target_ext == '.kicad_sch' else (target_ext,)
        for ext in exts:
            candidate = os.path.join(parent_dir, pro_stem + ext)
            if os.path.isfile(candidate):
                return candidate, f"Resolved from {os.path.basename(path)}"
        raise FileNotFoundError(
            f"Project '{pro_stem}' found but {' / '.join(pro_stem + e for e in exts)} "
            f"does not exist in {parent_dir}; pass the schematic or board file itself")

    # --- Input already has the target extension ---
    if path.endswith(target_ext):
        if not os.path.isfile(path):
            raise FileNotFoundError(f"File not found: {path}")
        return path, ""

    # --- Fallback: unrecognised extension ---
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")
    return path, ""


_INPUT_KIND = {'kicad_sch': 'a KiCad schematic (.kicad_sch or legacy .sch)',
               'kicad_pcb': 'a KiCad board (.kicad_pcb)'}


def empty_input_error(path: str, expected: str) -> str | None:
    """Return a usage-error message when *path* holds nothing but whitespace (the parser has
    nothing to read), else None. *expected* is 'kicad_sch' or 'kicad_pcb'."""
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                return f"{path}: file is empty; expected {_INPUT_KIND[expected]}"
            if chunk.strip():
                return None


def extract_pro_net_classes(pro: dict) -> list[dict]:
    """Extract net classes from .kicad_pro ``net_settings``.

    Returns list of dicts with: name, clearance, track_width, via_diameter,
    via_drill, diff_pair_width, diff_pair_gap.  Net assignments are merged
    from both ``netclass_patterns`` and ``netclass_assignments``.
    """
    ns = pro.get('net_settings', {})
    raw_classes = ns.get('classes', [])
    patterns = ns.get('netclass_patterns') or []
    assignments = ns.get('netclass_assignments') or {}

    # Build pattern-based net lists per class
    class_nets: dict[str, list[str]] = {}
    for p in patterns:
        nc_name = p.get('netclass', '')
        pattern = p.get('pattern', '')
        if nc_name and pattern:
            class_nets.setdefault(nc_name, []).append(pattern)

    # Add direct assignments.
    # KH-235: nc_value can be a list when a net belongs to multiple
    # classes (newer .kicad_pro format). Harness corpus audit confirmed
    # 139 files with list-valued netclass_assignments, 0 files with
    # list-valued netclass_patterns — so only the assignments loop
    # needs coercion. Two list-format variants observed: single-class
    # wrapped in a 1-element list ("+BATT": ["+BATT"]) and explicit
    # class-name-as-list ("Net-...": ["Power"]). Both crash the same
    # way via setdefault() hashing a list. Coerce to iterable and
    # register the net under each class.
    for net_name, nc_value in assignments.items():
        if not nc_value:
            continue
        nc_names = nc_value if isinstance(nc_value, list) else [nc_value]
        for nc_name in nc_names:
            if nc_name:
                class_nets.setdefault(nc_name, []).append(net_name)

    result = []
    for c in raw_classes:
        name = c.get('name', '')
        entry = {
            'name': name,
            'clearance': c.get('clearance'),
            'track_width': c.get('track_width'),
            'via_diameter': c.get('via_diameter'),
            'via_drill': c.get('via_drill'),
            'diff_pair_width': c.get('diff_pair_width'),
            'diff_pair_gap': c.get('diff_pair_gap'),
        }
        # Remove None values
        entry = {k: v for k, v in entry.items() if v is not None}
        nets = class_nets.get(name, [])
        if nets:
            entry['nets'] = nets
        result.append(entry)
    return result


def extract_pro_design_rules(pro: dict) -> dict:
    """Extract board design rules from .kicad_pro.

    Returns dict with min_clearance, min_track_width, min_via_diameter, etc.
    Values are in mm (KiCad native unit).
    """
    rules = pro.get('board', {}).get('design_settings', {}).get('rules', {})
    if not rules:
        return {}
    # Extract the most useful rules
    return {k: v for k, v in rules.items()
            if isinstance(v, (int, float)) and k.startswith('min_')}


def extract_pro_text_variables(pro: dict) -> dict:
    """Extract text variables from .kicad_pro.

    Text variables are user-defined key-value pairs used in schematic and
    PCB text fields via ``${VARIABLE_NAME}`` syntax.
    """
    return pro.get('text_variables', {}) or {}


def load_kicad_dru(file_path: str) -> list[dict] | None:
    """Load custom design rules from ``.kicad_dru`` adjacent to a KiCad file.

    Returns list of rule dicts::

        {"name": "Track width, outer",
         "layer": "outer",
         "condition": "A.Type == 'track'",
         "constraints": [{"type": "track_width", "min": 0.127}]}

    Conditions are kept as raw strings — not evaluated.
    Returns None if no ``.kicad_dru`` found.

    Discovery is stem-matched via `find_project_settings_file`, same rule
    as ``load_kicad_pro`` (KH-362).
    """
    dru_path = find_project_settings_file(file_path, '.kicad_dru')
    if not dru_path:
        return None

    try:
        with open(dru_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except OSError:
        return None

    # .kicad_dru has multiple top-level forms — wrap in synthetic root
    try:
        tree = _sexp_parse(f'(dru_root {content})')
    except (ValueError, IndexError):
        return None

    rules = []
    for r in find_all(tree, 'rule'):
        name = r[1] if len(r) > 1 and isinstance(r[1], str) else ''

        layer_node = find_first(r, 'layer')
        layer = (layer_node[1]
                 if layer_node and len(layer_node) > 1
                 else None)

        condition = get_value(r, 'condition')

        constraints = []
        for c in find_all(r, 'constraint'):
            if len(c) < 2:
                continue
            ctype = c[1]
            entry: dict = {'type': ctype}
            for key in ('min', 'max', 'opt'):
                val = get_value(c, key)
                if val is not None:
                    # Strip 'mm' suffix if present
                    val_str = str(val).rstrip('m').rstrip('m')
                    try:
                        entry[key] = float(val_str)
                    except ValueError:
                        entry[key] = val
            constraints.append(entry)

        rule_dict: dict = {'name': name}
        if layer:
            rule_dict['layer'] = layer
        if condition:
            rule_dict['condition'] = condition
        if constraints:
            rule_dict['constraints'] = constraints
        rules.append(rule_dict)

    return rules if rules else None


def load_lib_tables(file_path: str) -> dict:
    """Load ``fp-lib-table`` and ``sym-lib-table`` from a KiCad project directory.

    Scans the directory containing *file_path* for library table files.

    Returns ``{'symbol_libs': [...], 'footprint_libs': [...]}``.
    Each lib entry is ``{'name': str, 'type': str, 'uri': str, 'descr': str}``.
    """
    parent = os.path.dirname(os.path.abspath(file_path))
    result: dict = {'symbol_libs': [], 'footprint_libs': []}

    for table_file, key in (('sym-lib-table', 'symbol_libs'),
                             ('fp-lib-table', 'footprint_libs')):
        table_path = os.path.join(parent, table_file)
        if not os.path.isfile(table_path):
            continue
        try:
            tree = _sexp_parse_file(table_path)
        except (ValueError, OSError):
            continue

        for lib in find_all(tree, 'lib'):
            entry = {
                'name': get_value(lib, 'name') or '',
                'type': get_value(lib, 'type') or '',
                'uri': get_value(lib, 'uri') or '',
            }
            descr = get_value(lib, 'descr')
            if descr:
                entry['descr'] = descr
            result[key].append(entry)

    return result
