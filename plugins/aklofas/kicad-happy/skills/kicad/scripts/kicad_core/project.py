"""KiCad project discovery and project-file readers (kicad_core): the project directory an analysis JSON names, .kicad_pro, .kicad_dru, lib tables, root-schematic resolution."""
import os
import re
from collections.abc import Iterable
from fnmatch import fnmatchcase
from pathlib import Path

from kicad_core.fileio import json_loads
from kicad_core.textvars import expand_text_vars
from kicad_core import sexp as _sexp
from kicad_core.sexp import parse as _sexp_parse, parse_file as _sexp_parse_file, find_all, find_first, get_value


def _recorded_source_file(analysis_json):
    if not isinstance(analysis_json, dict):
        return None
    source_file = analysis_json.get("file")
    if not (isinstance(source_file, str) and source_file):
        inputs = analysis_json.get("inputs")
        sources = inputs.get("source_files") if isinstance(inputs, dict) else None
        source_file = sources[0] if isinstance(sources, list) and sources else None
    return source_file if isinstance(source_file, str) and source_file else None


def existing_source_dir(source_file):
    """Absolute directory of a recorded source path, or None. A relative path
    counts only when that file exists from the cwd: otherwise the cwd (maybe a
    shared folder) would stand in for the project."""
    if not (isinstance(source_file, str) and source_file):
        return None
    if os.path.isabs(source_file):
        return Path(source_file).parent
    absolute = os.path.abspath(source_file)
    return Path(absolute).parent if os.path.isfile(absolute) else None


def extraction_project_dir(analysis_json):
    """Project directory of the first source file the analysis JSON names
    ("file", else inputs.source_files[0]), or None. Used by the datasheet
    extraction and SPICE model caches; a relative source path must exist."""
    return existing_source_dir(_recorded_source_file(analysis_json))


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
    # `}` or `]`, but never inside a string literal.
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
    with open(path, 'r', encoding='utf-8-sig') as f:
        raw = f.read()
    return json_loads(_strip_jsonc(raw))


def load_user_config() -> dict:
    """The user's own ``~/.kicad-happy.json`` and nothing else: a project file never
    reaches a setting read from here. ``{}`` when the file is missing, unreadable,
    invalid or not an object."""
    path = os.path.join(os.path.expanduser("~"), ".kicad-happy.json")
    try:
        data = load_jsonc(path)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def find_project_settings_file(file_path: str, ext: str, exact: bool = False) -> str | None:
    """Find the ``ext`` file (e.g. ``.kicad_pro``, ``.kicad_dru``) matching
    ``file_path``'s project, in ``file_path``'s directory.

    Shared discovery logic for `load_kicad_pro` / `load_kicad_dru`.
    Scans the directory for files ending in ``ext`` and prefers the one
    whose stem matches ``file_path``'s stem (KiCad names project/rules
    files after the board/schematic they belong to). Falls back to the
    sole candidate when there's only one; with multiple candidates and no
    stem match, deterministically picks the first (sorted) candidate and
    warns on stderr (a directory with several projects previously took
    whatever the OS listed first).

    With ``exact`` only a file whose stem equals ``file_path``'s stem (ignoring
    case, as on KiCad's case-insensitive platforms) qualifies: a board opens
    the project and rules files carrying its own name and no other. Linux
    KiCad needs the exact case, so it loads no file whose name differs from
    the board's only in case; here the first such file (sorted) loads.

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

    same_stem = [f for f in candidates if os.path.splitext(f)[0] == stem]
    if exact and not same_stem:
        same_stem = [f for f in candidates
                     if os.path.splitext(f)[0].lower() == stem.lower()]
    if same_stem:
        chosen = same_stem[0]
    elif exact:
        return None
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


def load_kicad_pro(file_path: str, *, exact: bool = False) -> dict | None:
    """Load .kicad_pro from the same directory as a .kicad_sch or .kicad_pcb file.

    Discovery is stem-matched via `find_project_settings_file` —
    in a multi-project directory, the ``.kicad_pro`` sharing this file's
    stem is preferred over whatever the OS lists first.
    With ``exact`` (a board: KiCad opens the project named like the board)
    only the ``.kicad_pro`` with the same stem is read.
    Returns the parsed JSON dict, or None if not found, not valid JSON, or a
    KiCad 5 ``.pro`` file (which uses a different, non-JSON format).
    Tolerates JS-style comments / trailing commas (JSONC).
    """
    pro_path = find_project_settings_file(file_path, '.kicad_pro', exact)
    if not pro_path:
        return None
    try:
        return load_jsonc(pro_path)
    except (ValueError, OSError):
        return None


def variant_names(pro: dict | None) -> list[str]:
    """The design variant names a KiCad 10 project declares (``schematic.variants``), in
    order."""
    sch = pro.get("schematic") if isinstance(pro, dict) else None
    entries = sch.get("variants") if isinstance(sch, dict) else None
    if not isinstance(entries, list):
        return []
    return [str(e["name"]) for e in entries if isinstance(e, dict) and e.get("name")]


def unknown_variant_error(variant: str, pro: dict | None) -> str | None:
    """The usage error for a ``--variant`` the project does not declare, else None."""
    names = variant_names(pro)
    if variant in names:
        return None
    if not names:
        return f"unknown variant {variant!r} (the project defines no variants)"
    return f"unknown variant {variant!r} (the project defines: {', '.join(names)})"


NIL_UUID = "00000000-0000-0000-0000-000000000000"


def declared_top_level_sheets(pro_path: str | None, pro: dict | None = None) -> list[dict]:
    """The top-level sheets a KiCad 10 project declares (``schematic.top_level_sheets``), in
    order, as ``{"path", "name", "uuid"}``: *path* absolute, *uuid* "" when nil or absent.
    A declared file that does not exist becomes ``<project>.kicad_sch`` when that exists
    (PROJECT_FILE::LoadFromFile), else it is left out; a file listed twice appears once.
    [] when the project declares none.  *pro* is the parsed project file when the caller
    already has it."""
    if not pro_path:
        return []
    if pro is None:
        try:
            pro = load_jsonc(pro_path)
        except (ValueError, OSError):
            return []
    sch = pro.get("schematic") if isinstance(pro, dict) else None
    tls = sch.get("top_level_sheets") if isinstance(sch, dict) else None
    if not isinstance(tls, list):
        return []
    project_dir = os.path.dirname(os.path.abspath(pro_path))
    project_name = os.path.basename(pro_path)[:-len('.kicad_pro')]
    sheets, seen = [], set()
    for entry in tls:
        if not isinstance(entry, dict) or not isinstance(entry.get("filename"), str):
            continue
        name = entry.get("name") if isinstance(entry.get("name"), str) else ""
        path = os.path.abspath(os.path.join(project_dir, entry["filename"]))
        if not os.path.isfile(path):
            path = os.path.join(project_dir, project_name + '.kicad_sch')
            name = project_name
            if not os.path.isfile(path):
                continue
        key = os.path.normcase(os.path.realpath(path))
        if key in seen:
            continue
        seen.add(key)
        uuid = entry.get("uuid") if isinstance(entry.get("uuid"), str) else ""
        sheets.append({"path": path, "name": name,
                       "uuid": "" if uuid.lower() == NIL_UUID else uuid})
    return sheets


def expand_sheet_file(name: str, sch_path: str, pro: dict | None = None) -> str:
    """A (sheet) block's file name with the project's text variables expanded, as KiCad opens
    it; an unknown ``${TOKEN}``, and ``${PROJECTNAME}`` when no project file is found, stays as
    written. *pro* defaults to the project of *sch_path*."""
    if "${" not in name:
        return name
    if pro is None:
        pro = load_kicad_pro(sch_path) or {}
    pro_file = find_project_settings_file(sch_path, '.kicad_pro')
    stem = os.path.basename(pro_file)[:-len('.kicad_pro')] if pro_file else None
    variables = pro.get('text_variables')
    variables = variables if isinstance(variables, dict) else {}

    def resolve(token):
        if token == "PROJECTNAME":
            return stem
        value = variables.get(token)
        return None if value is None else str(value)

    return expand_text_vars(name, resolve)


def is_referenced_as_child(file_path: str) -> bool:
    """Check if a .kicad_sch is referenced as a child sheet by a sibling.

    Scans sibling .kicad_sch files in the same directory for a Sheetfile
    property that names this file (whole path, project text variables expanded).
    Used by detect_sub_sheet() to distinguish intermediate hierarchy nodes from
    the root.

    Reads the full file because sheet blocks can appear after large
    lib_symbols sections (e.g. 680KB root with sheets at byte 681K).
    """
    abs_path = os.path.abspath(file_path)
    basename = os.path.basename(abs_path)
    parent_dir = os.path.dirname(abs_path)
    wanted = os.path.normcase(abs_path)

    try:
        for fname in os.listdir(parent_dir):
            if fname.endswith('.kicad_sch') and fname != basename:
                sibling = os.path.join(parent_dir, fname)
                try:
                    with open(sibling, 'r', encoding='utf-8',
                              errors='replace') as f:
                        content = f.read()
                    if wanted in _sheet_file_refs(sibling, content):
                        return True
                except OSError:
                    continue
    except OSError:
        pass
    return False


_SHEETFILE_ANY = re.compile(r'\(property\s+"Sheet ?file"\s+"([^"]*)"', re.IGNORECASE)


def _sheet_file_refs(sch_path: str, content: str) -> set[str]:
    """Normalised absolute path of every sheet file *content* (the text of *sch_path*) names,
    with project text variables expanded; a value that stays unresolved is dropped."""
    base = os.path.dirname(os.path.abspath(sch_path))
    refs = set()
    for m in _SHEETFILE_ANY.finditer(content):
        value = m.group(1)
        if "${" in value:
            value = expand_sheet_file(value, sch_path)
            if "${" in value:
                continue
        refs.add(os.path.normcase(os.path.abspath(os.path.join(base, value.replace("\\", "/")))))
    return refs


def _root_references_target(root_sch: str, target: str) -> bool:
    """Check if the sheet tree under root_sch reaches target through whole sheet-file paths,
    however many intermediate sheets lie between."""
    wanted = os.path.normcase(os.path.abspath(target))
    seen = set()
    todo = [os.path.abspath(root_sch)]
    while todo:
        sch = todo.pop()
        key = os.path.normcase(sch)
        if key in seen:
            continue
        seen.add(key)
        try:
            with open(sch, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except OSError:
            continue
        refs = _sheet_file_refs(sch, content)
        if wanted in refs:
            return True
        todo.extend(r for r in refs if r not in seen)
    return False


def _project_roots(pro_path: str) -> list[str]:
    """The existing root schematics of a project: its declared top-level sheets, else
    ``<project>.kicad_sch``; absolute paths."""
    declared = declared_top_level_sheets(pro_path)
    if declared:
        return [d["path"] for d in declared]
    candidate = os.path.abspath(pro_path[:-len('.kicad_pro')] + '.kicad_sch')
    return [candidate] if os.path.isfile(candidate) else []


def discover_root_schematic(target_path: str) -> str | None:
    """Find the root .kicad_sch for a sub-sheet file.

    Returns the root schematic path, or None if the target appears to be
    the root or no root can be found.

    Strategy:
    1. Same directory: look for .kicad_pro, take its declared top-level
       sheets (else <project>.kicad_sch) as root candidates.
       When multiple .kicad_pro exist, verify each candidate's
       sheet tree references the target.
    2. Same directory: scan sibling .kicad_sch files for references.
    3. Parent directories: walk up to 5 levels looking for
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
    # when multiple .kicad_pro exist, verify sheet-tree membership
    pro_files = [f for f in entries if f.endswith('.kicad_pro')]

    if len(pro_files) == 1:
        roots = _project_roots(os.path.join(parent_dir, pro_files[0]))
        if roots and target not in roots:
            return next((r for r in roots if _root_references_target(r, target)), roots[0])
    elif len(pro_files) > 1:
        # Multiple projects — check which one's sheet tree references us
        for pro in pro_files:
            for candidate in _project_roots(os.path.join(parent_dir, pro)):
                if candidate != target and _root_references_target(candidate, target):
                    return candidate

    # Tier 2: scan sibling .kicad_sch files for (sheet ...) blocks
    siblings = [f for f in entries
                if f.endswith('.kicad_sch') and f != target_basename]
    for fname in siblings:
        candidate = os.path.join(parent_dir, fname)
        try:
            with open(candidate, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            if os.path.normcase(target) in _sheet_file_refs(candidate, content):
                return candidate
        except OSError:
            continue

    # Tier 3: walk up parent directories looking for .kicad_pro
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
                for candidate in _project_roots(os.path.join(search_dir, fname)):
                    if _root_references_target(candidate, target):
                        return candidate

    return None


def _project_target(pro_path: str, target_ext: str) -> str:
    """The file a project opens: its first declared top-level sheet for a schematic, else
    ``<project><target_ext>`` beside the project file."""
    if target_ext == '.kicad_sch':
        declared = declared_top_level_sheets(pro_path)
        if declared:
            return declared[0]["path"]
    return pro_path[:-len('.kicad_pro')] + target_ext


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
        candidate = _project_target(os.path.join(path, pro_files[0]), target_ext)
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
        candidate = _project_target(path, target_ext)
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


# (effect when the file is not a KiCad file at all, effect when it parses only in part)
_INPUT_EFFECTS = {'kicad_sch': ('file not read as a schematic', 'partial sheet analyzed'),
                  'kicad_pcb': ('file not read as a board', 'partial board analyzed')}


def parse_input_problem(path: str, tree, problem: str | None,
                        expected: str) -> tuple[str, str] | None:
    """(message, effect) when a parsed file is not a whole KiCad schematic or board: its
    root is not (``expected`` ...), or the parser's *problem* (see sexp.parse_checked);
    None when it is.  *expected* is 'kicad_sch' or 'kicad_pcb'."""
    name = os.path.basename(path)
    not_kicad, partial = _INPUT_EFFECTS[expected]
    head = tree[0] if isinstance(tree, list) and tree else tree
    if head != expected:
        return f"{name} is not {_INPUT_KIND[expected]}: it starts with {str(head)[:40]!r}", not_kicad
    if problem:
        return f"{name}: {problem}", partial
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
    # nc_value can be a list when a net belongs to multiple
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


def ignored_drc_checks(pro: dict | None) -> frozenset[str]:
    """The DRC check keys .kicad_pro ``board.design_settings.rule_severities`` sets to
    ``ignore``; KiCad's DRC never reports those checks (drc_engine.cpp RunTests). Only the exact
    string ``ignore`` silences a check (SeverityFromString)."""
    severities = (((pro or {}).get('board') or {}).get('design_settings') or {}).get(
        'rule_severities')
    if not isinstance(severities, dict):
        return frozenset()
    return frozenset(k for k, v in severities.items() if v == 'ignore')


def extract_pro_default_netclass(pro: dict) -> dict | None:
    """The Default net class entry of .kicad_pro ``net_settings.classes`` as written, or None."""
    for c in (pro.get('net_settings') or {}).get('classes') or []:
        if isinstance(c, dict) and c.get('name') == 'Default':
            return c
    return None


def extract_pro_text_variables(pro: dict) -> dict:
    """Extract text variables from .kicad_pro.

    Text variables are user-defined key-value pairs used in schematic and
    PCB text fields via ``${VARIABLE_NAME}`` syntax.
    """
    return pro.get('text_variables', {}) or {}


# A .kicad_dru length: a number with one of KiCad's length units (pcbexpr_evaluator.cpp). A bare
# number is a "Missing units" error; arithmetic is an expression (`_dru_eval`).
_DRU_LENGTH = re.compile(r'\s*([-+]?(?:\d+\.?\d*|\.\d+))\s*(mm|mil|in)\s*')
_DRU_UNIT_MM = {'mm': 1.0, 'mil': 0.0254, 'in': 25.4}


def parse_dru_length(text: str) -> float | None:
    """mm value of a .kicad_dru length such as ``0.2mm``, ``5mil`` or ``6 mil``; None otherwise."""
    m = _DRU_LENGTH.fullmatch(text)
    return round(float(m[1]) * _DRU_UNIT_MM[m[2]], 6) if m else None


_DRU_SEVERITIES = frozenset(('ignore', 'warning', 'error', 'exclusion'))
# Constraint types whose values take no unit (drc_rule_parser.cpp parseConstraint).
_DRU_UNITLESS_CONSTRAINTS = frozenset(('via_count', 'min_resolved_spokes', 'track_angle',
                                       'via_dangling', 'bridged_mask'))
_DRU_EXPR_TOKEN = re.compile(r'\s*(?:(\d+\.?\d*|\.\d+)|([a-z]+)|([-+*/()]))')
_DRU_OTHER_UNITS = frozenset(('deg', 'fs', 'ps'))


def _dru_bound_text(node: list) -> str:
    """The text of a bound as KiCad reads it: every token after the keyword, a nested list
    in its parentheses (drc_rule_parser.cpp parseExpression)."""
    return ' '.join('( ' + _dru_bound_text([None] + t) + ' )' if isinstance(t, list) else str(t)
                    for t in node[1:])


def _dru_eval(text: str) -> tuple[str, float | None]:
    """A bound expression evaluated as KiCad's libeval does: ``('length', mm)``, ``('number', v)``,
    ``('other', None)`` for a result this reader does not judge (angle or time units, a mixed or
    squared dimension, division by zero, a character outside the expression grammar), or
    ``('error', None)`` for text KiCad cannot parse."""
    if re.search(r'[^0-9.+\-*/()a-z\s]', text):
        return 'other', None
    tokens = []
    pos = 0
    while pos < len(text):
        m = _DRU_EXPR_TOKEN.match(text, pos)
        if not m:
            if text[pos:].strip():
                return 'error', None
            break
        tokens.append(m.groups())
        pos = m.end()
    i = 0

    def peek(kind):
        return tokens[i][kind] if i < len(tokens) else None

    def combine(op, a, b):
        (ka, va), (kb, vb) = a, b
        if 'other' in (ka, kb):
            return 'other', None
        if op in '+-':
            return (ka, va + vb if op == '+' else va - vb) if ka == kb else ('other', None)
        if op == '*':
            return ('other', None) if ka == kb == 'length' else (
                'length' if 'length' in (ka, kb) else 'number', va * vb)
        if vb == 0 or kb == 'length':
            return 'other', None
        return ka, va / vb

    def unary():
        nonlocal i
        op = peek(2)
        if op in ('+', '-'):
            i += 1
            k, v = unary()
            return (k, -v if op == '-' and v is not None else v)
        if op == '(':
            i += 1
            r = expr()
            if peek(2) != ')':
                raise ValueError
            i += 1
            return r
        num = peek(0)
        if num is None:
            raise ValueError
        i += 1
        unit = peek(1)
        if unit is None:
            return 'number', float(num)
        i += 1
        if unit in _DRU_UNIT_MM:
            return 'length', float(num) * _DRU_UNIT_MM[unit]
        if unit in _DRU_OTHER_UNITS:
            return 'other', None
        raise ValueError

    def binary(sub, ops):
        nonlocal i
        r = sub()
        while peek(2) in ops:
            op = peek(2)
            i += 1
            r = combine(op, r, sub())
        return r

    def term():
        return binary(unary, ('*', '/'))

    def expr():
        return binary(term, ('+', '-'))

    try:
        kind, value = expr()
    except ValueError:
        return 'error', None
    if i != len(tokens):
        return 'error', None
    return kind, (round(value, 6) if value is not None else None)


def _dru_bound_error(constraint: list) -> str | None:
    """KiCad's message for an item of *constraint* it cannot read, or None: "Unrecognized
    item." for a list that is not a bound, "Missing units." for a unitless length, "Syntax
    error" for a length that is not an expression."""
    for bound in constraint[2:]:
        if not isinstance(bound, list):
            continue
        if not bound or not isinstance(bound[0], str) or bound[0] not in _DRU_BOUND_ITEMS:
            return "Unrecognized item."
        if (len(bound) > 1 and bound[0] in ('min', 'max', 'opt')
                and constraint[1] not in _DRU_UNITLESS_CONSTRAINTS):
            text = _dru_bound_text(bound)
            if parse_dru_length(text) is not None:
                continue
            kind = _dru_eval(text)[0]
            if kind == 'number':
                return "Missing units."
            if kind == 'error':
                return "Syntax error"
    return None


# drc_rule_parser.cpp parseConstraint: the constraint types, plus the deprecated names it maps.
_DRU_CONSTRAINT_TYPES = frozenset((
    'assertion', 'clearance', 'creepage', 'hole_clearance', 'edge_clearance', 'hole_size',
    'hole_to_hole', 'courtyard_clearance', 'silk_clearance', 'text_height', 'text_thickness',
    'track_width', 'track_angle', 'track_segment_length', 'connection_width', 'annular_width',
    'via_diameter', 'via_dangling', 'zone_connection', 'thermal_relief_gap',
    'thermal_spoke_width', 'min_resolved_spokes', 'solder_mask_expansion', 'solder_mask_sliver',
    'solder_paste_abs_margin', 'solder_paste_rel_margin', 'disallow', 'length', 'skew',
    'via_count', 'diff_pair_gap', 'diff_pair_uncoupled', 'physical_clearance',
    'physical_hole_clearance', 'bridged_mask',
    'hole', 'mechanical_clearance', 'mechanical_hole_clearance'))
# Deprecated constraint names KiCad still reads (drc_rule_parser.cpp parseConstraint).
_DRU_CONSTRAINT_ALIASES = {'hole': 'hole_size', 'mechanical_clearance': 'physical_clearance',
                           'mechanical_hole_clearance': 'physical_hole_clearance'}
_DRU_RULE_ITEMS = frozenset(('constraint', 'condition', 'layer', 'severity'))
_DRU_BOUND_ITEMS = frozenset(('min', 'max', 'opt', 'within_diff_pairs'))
# Constraint types that take bare argument tokens instead of bounds.
_DRU_ARGUMENT_CONSTRAINTS = frozenset(('disallow', 'zone_connection', 'assertion'))
# The layer names a rule can match: LSET::Name over every layer id (lset.cpp) and the standard
# names of LayerName (layer_id.cpp). The board's own names are added per file.
_KICAD_LAYER_NAMES = frozenset((
    'F.Cu', 'B.Cu', *(f'In{i}.Cu' for i in range(1, 63)),
    'B.Adhes', 'F.Adhes', 'B.Paste', 'F.Paste', 'B.SilkS', 'F.SilkS', 'B.Mask', 'F.Mask',
    'Dwgs.User', 'Cmts.User', 'Eco1.User', 'Eco2.User', 'Edge.Cuts', 'Margin',
    'F.CrtYd', 'B.CrtYd', 'F.Fab', 'B.Fab', 'Rescue', *(f'User.{i}' for i in range(1, 46)),
    'B.Adhesive', 'F.Adhesive', 'B.Silkscreen', 'F.Silkscreen', 'User.Drawings',
    'User.Comments', 'User.Eco1', 'User.Eco2', 'F.Courtyard', 'B.Courtyard'))


def _dru_layer_known(pattern: str, layer_names: frozenset[str]) -> bool:
    """True when a rule's layer is ``outer``/``inner`` or a wildcard pattern matching a layer
    name (wxString::Matches: ``*`` and ``?`` only, case-sensitive). A text variable is left to
    KiCad's own expansion."""
    if pattern in ('outer', 'inner') or '${' in pattern:
        return True
    pattern = pattern.replace('[', '[[]')
    return any(fnmatchcase(name, pattern) for name in layer_names)


def _dru_parse_error(tree: list, layer_names: frozenset[str] | None = None) -> str | None:
    """KiCad's message for a .kicad_dru it refuses to load, or None. A parse error drops every
    custom rule of the file (drc_rule_parser.cpp Parse, drc_engine.cpp InitEngine). Checked:
    the leading version statement, the top-level forms, rule names and items, severity names,
    conditions, constraint types and items (once per rule), length bounds that are not a
    length expression, and, given the board's *layer_names*, the rule's layer."""
    if any(not isinstance(f, list) for f in tree[1:]):
        return "Missing '('."
    forms = tree[1:]
    if forms and forms[0][:1] != ['version']:
        return "Missing version statement."
    for form in forms:
        if form[:1] == ['version']:
            if len(form) < 2 or not re.fullmatch(r'[-+]?\d+(\.\d*)?', str(form[1])):
                return "Missing version number."
        elif form[:1] == ['rule']:
            if len(form) < 2 or not isinstance(form[1], str):
                return "Missing rule name."
            constraint_types = set()
            has_layer = False
            for item in form[2:]:
                if not isinstance(item, list):
                    continue
                if not item or not isinstance(item[0], str) or item[0] not in _DRU_RULE_ITEMS:
                    return "Unrecognized item."
                if item[0] == 'severity' and (len(item) < 2 or not isinstance(item[1], str)
                                              or item[1] not in _DRU_SEVERITIES):
                    return "Unrecognized severity."
                if item[0] == 'condition':
                    if len(item) < 2:
                        return "Missing condition expression."
                    if isinstance(item[1], list):
                        return "Unrecognized item."
                    if len(item) > 2:
                        return "Missing ')'."
                if item[0] == 'constraint' and len(item) > 1:
                    ctype = item[1]
                    if not isinstance(ctype, str) or (ctype not in _DRU_CONSTRAINT_TYPES
                                                      and '${' not in ctype):
                        return "Unrecognized constraint type."
                    if ctype in constraint_types:
                        return f"Rule already has a '{ctype}' constraint."
                    constraint_types.add(ctype)
                    if ctype not in _DRU_ARGUMENT_CONSTRAINTS and (
                            bound_error := _dru_bound_error(item)):
                        return bound_error
                if item[0] == 'layer':
                    if has_layer:
                        return "'layer' keyword already present."
                    has_layer = True
                if item[0] == 'layer' and len(item) > 1:
                    if not isinstance(item[1], str) or (
                            layer_names is not None
                            and not _dru_layer_known(item[1], layer_names)):
                        return "Unrecognized layer."
        else:
            return "Expected rule or version."
    return None


def _dru_unbalanced(content: str) -> str | None:
    """KiCad's message when the parentheses of *content* do not balance, or None. Counted over
    the parser's own tokens, so a parenthesis in a quoted string or a comment line is not counted;
    the parser itself closes an open list at the end and stops at a stray ')' without error."""
    depth = 0
    for tok in _sexp._tokenize(content):
        if tok is _sexp._LPAREN:
            depth += 1
        elif tok is _sexp._RPAREN:
            depth -= 1
            if depth < 0:
                return "Missing '('."
    return "Missing ')'." if depth else None


def load_kicad_dru(file_path: str) -> list[dict] | None:
    """The custom rules of the board's ``.kicad_dru`` (`load_kicad_dru_checked`), or None."""
    return load_kicad_dru_checked(file_path)[0]


def load_kicad_dru_checked(file_path: str, *, layer_names: Iterable[str] | None = None
                           ) -> tuple[list[dict] | None, str | None]:
    """Load custom design rules from ``.kicad_dru`` adjacent to a KiCad file.

    Returns list of rule dicts::

        {"name": "Track width, outer",
         "layer": "outer",
         "condition": "A.Type == 'track'",
         "constraints": [{"type": "track_width", "min": 0.127}]}

    Bounds are mm (`parse_dru_length`, or `_dru_eval` for an expression); a bound that does not
    evaluate to a length stays its text.
    Conditions are kept as raw strings — not evaluated. ``severity`` is kept when set.
    Returns (None, None) if no ``.kicad_dru`` found. The second item is KiCad's parse error
    when KiCad would refuse the file (`_dru_parse_error`); the rules are still returned.
    The rule layers are checked only when the board's *layer_names* (names and user names)
    are given.

    Only the board reads rules, and KiCad takes the file named like the board,
    so discovery is exact-stem via `find_project_settings_file`.
    """
    dru_path = find_project_settings_file(file_path, '.kicad_dru', exact=True)
    if not dru_path:
        return None, None

    try:
        with open(dru_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except OSError:
        return None, None

    # .kicad_dru has multiple top-level forms — wrap in synthetic root. The newlines keep a
    # '#' comment on the first or last line a comment and off the closing parenthesis.
    try:
        tree = _sexp_parse(f'(dru_root\n{content}\n)')
    except (ValueError, IndexError) as e:
        return None, str(e)

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
            ctype = _DRU_CONSTRAINT_ALIASES.get(c[1], c[1]) if isinstance(c[1], str) else c[1]
            entry: dict = {'type': ctype}
            for key in ('min', 'max', 'opt'):
                node = find_first(c, key)
                if node is None or len(node) < 2:
                    continue
                text = _dru_bound_text(node)
                # KiCad reads a comma between digits as the decimal point ('0,1mm')
                number = re.sub(r'(?<=\d),(?=\d)', '.', text)
                value = parse_dru_length(number)
                if value is None and isinstance(ctype, str) and ctype not in _DRU_UNITLESS_CONSTRAINTS:
                    kind, mm = _dru_eval(number)
                    value = mm if kind == 'length' else None
                entry[key] = value if value is not None else text
            constraints.append(entry)

        rule_dict: dict = {'name': name}
        if layer:
            rule_dict['layer'] = layer
        if condition:
            rule_dict['condition'] = condition
        severity = get_value(r, 'severity')
        if severity:
            rule_dict['severity'] = severity
        if constraints:
            rule_dict['constraints'] = constraints
        rules.append(rule_dict)

    if not rules:
        return None, None
    known_layers = (None if layer_names is None
                    else _KICAD_LAYER_NAMES | frozenset(layer_names))
    return rules, _dru_parse_error(tree, known_layers) or _dru_unbalanced(content)


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
