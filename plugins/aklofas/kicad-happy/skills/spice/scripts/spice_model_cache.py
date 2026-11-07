"""
Project-local SPICE model cache.

Models are cached in a `spice/` directory at the same level as `datasheets/`,
next to the KiCad schematic and layout files. This keeps model data co-located
with the design — the project can be shared with model files included.

Directory structure:
    <project>/
      design.kicad_sch
      datasheets/         # existing — PDF datasheets
      spice/
        models/
          manifest.json   # MPN → file + metadata (legacy name: index.json)
          LM358.sub       # .subckt OPAMP_LM358 ...
          AMS1117_3_3.sub # .subckt LDO_AMS1117_3_3 ...

The model resolution cascade (get_model_for_part):
    1. Project cache (spice/models/) — previously resolved
    2. Distributor API parametric data (spice_spec_fetcher.py)
    3. Structured datasheet extraction (datasheets/extracted/)
    4. Heuristic PDF regex extraction — pdftotext + regex patterns
    5. Built-in lookup table (spice_part_library.py) — offline
    6. Ideal/generic model fallback — always available
Offline mode skips tiers 2-4.
"""

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import _core_path  # noqa: F401
from datasheet_types.cache_reader import read_json_object, read_regular_bytes
from distributor_core.manifest import DEFAULT_FILE_MODE, manifest_file_path
from kicad_core.diagnostics import record
from kicad_core.project import extraction_project_dir, project_dir_from_analysis  # noqa: F401  (re-exported)
from spice_part_library import lookup_part_specs
from spice_spec_fetcher import _read_spice_specs
from spice_model_generator import (
    generate_opamp_model,
    generate_ldo_model,
    generate_comparator_model,
    generate_vref_model,
    sanitize_mpn,
)


_PROCESS_CACHE_DIR = None  # per-process fallback root, created lazily


def resolve_cache_dir(analysis_json, override_dir=None):
    """Determine the spice/models/ directory for this project.

    Resolution, first match wins:
        1. override_dir, when given
        2. beside the first source file the analysis JSON names
           ("file", or "inputs.source_files[0]")
        3. one per-process temp directory, created on first use, so two
           processes never share a manifest and no model leaks across projects

    simulate_subcircuits passes its workdir as override_dir when the analysis
    names no source file, so step 3 is reached only by other callers.

    Args:
        analysis_json: Parsed analyzer JSON dict ("file" / "inputs" optional)
        override_dir: If set, use this directory instead of deriving

    Returns:
        Path to spice/models/ directory (may not exist yet)
    """
    global _PROCESS_CACHE_DIR
    if override_dir:
        return Path(override_dir) / "spice" / "models"

    project_dir = project_dir_from_analysis(analysis_json)
    if project_dir is not None:
        return project_dir / "spice" / "models"

    if _PROCESS_CACHE_DIR is None:
        _PROCESS_CACHE_DIR = Path(tempfile.mkdtemp(prefix="kicad-happy-spice-"))
    return _PROCESS_CACHE_DIR / "spice" / "models"


# In-memory cache for manifest.json to avoid re-reading on every call.
# Legacy name index.json still read for backward compat.
MANIFEST_FILENAME = "manifest.json"
LEGACY_MANIFEST_FILENAME = "index.json"

_index_cache = {}  # cache_dir_str → (mtime, parsed_index)


def _cache_manifest_path(cache_dir):
    d = Path(cache_dir)
    new = d / MANIFEST_FILENAME
    if new.exists():
        return new
    old = d / LEGACY_MANIFEST_FILENAME
    if old.exists():
        return old
    return new  # does not exist — return target path for write


def get_cached_model(cache_dir, mpn, diagnostics=None):
    """Retrieve a cached model by MPN.

    Args:
        cache_dir: Path to spice/models/ directory
        mpn: Manufacturer part number

    Returns:
        (subckt_string, specs_dict) or (None, None) if not cached
    """
    return _lookup_cached_model(cache_dir, mpn, diagnostics)[:2]


def _lookup_cached_model(cache_dir, mpn, diagnostics=None):
    """(subckt, specs, refused): ``refused`` is True when the manifest names a model file
    that was not used (link, oversize, undecodable), so the caller must not overwrite it."""
    index_path = _cache_manifest_path(cache_dir)
    if not index_path.exists():
        return None, None, False

    # Use in-memory cache keyed on file mtime to avoid re-parsing
    cache_key = str(cache_dir)
    try:
        mtime = index_path.stat().st_mtime
        cached = _index_cache.get(cache_key)
        if cached and cached[0] == mtime:
            index = cached[1]
        else:
            index = read_json_object(index_path)
            if index is None:
                return None, None, False
            _index_cache[cache_key] = (mtime, index)
    except OSError:
        return None, None, False

    key = sanitize_mpn(mpn)
    entry = index.get(key) if isinstance(index, dict) else None
    if not isinstance(entry, dict):
        return None, None, False

    name = entry.get("file")
    model_file = manifest_file_path(Path(cache_dir), name)
    if model_file is None or not name.endswith(".sub") or not model_file.is_file():
        if model_file is None and isinstance(name, str) and (Path(cache_dir) / name).is_symlink():
            record(diagnostics, "spice_model_cache.get_cached_model",
                   ValueError(f"{name} is a symlink"), "project model skipped")
            return None, None, True
        if model_file is not None and name.endswith(".sub") and os.path.lexists(model_file):
            record(diagnostics, "spice_model_cache.get_cached_model",
                   ValueError(f"{name} is not a regular file"), "project model skipped")
            return None, None, True
        return None, None, False

    raw = read_regular_bytes(model_file)
    try:
        subckt = None if raw is None else raw.decode("utf-8")
    except UnicodeDecodeError:
        subckt = None
    if subckt is None:
        record(diagnostics, "spice_model_cache.get_cached_model",
               ValueError(f"{name} is oversized or unreadable"), "project model skipped")
        return None, None, True
    return subckt, _read_spice_specs(entry.get("specs")), False


# ngspice recognises dot-cards by prefix, so ".controlx" opens a control block and
# ".incx" includes a file; shell/source only matter as whole words (inside a control
# block), which keeps element names like SOURCE1 usable.
_CONTROL_CARD_PREFIXES = (".control", ".endc")
_INCLUDE_CARD_PREFIXES = (".inc", ".lib")
_CONTROL_WORDS = ("shell", "source")


def _logical_lines(text):
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("+") and lines:
            lines[-1] += " " + line[1:].strip()
        else:
            lines.append(line)
    return lines


def model_text_problem(text):
    """Why a cached model is unsafe to paste into a netlist, or None.

    Unsafe: a line that opens or closes a simulator control block, runs ``shell`` or
    ``source``, or includes any file (``.inc``/``.include``/``.lib``). Included files
    resolve from the simulation directory and are never scanned, so none is allowed.
    """
    for line in _logical_lines(text):
        card = line.lower().split(None, 1)[0] if line else ""
        if card.startswith(_INCLUDE_CARD_PREFIXES):
            return f"model includes a file: {line[:60]}"
        if card.startswith(_CONTROL_CARD_PREFIXES) or card in _CONTROL_WORDS:
            return f"model contains a simulator control command: {line[:60]}"
    return None


def cache_model(cache_dir, mpn, subckt, specs, source, component_type):
    """Save a model to the project cache.

    Args:
        cache_dir: Path to spice/models/ directory
        mpn: Manufacturer part number
        subckt: The .subckt string content
        specs: Specs dict used to generate the model
        source: Source tier ("lookup", "api:digikey", "api:lcsc", "ai")
        component_type: "opamp", "ldo", "comparator", "vref"
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    key = sanitize_mpn(mpn)
    filename = f"{key}.sub"
    model_path = cache_dir / filename

    # A temp file swapped in replaces a planted symlink instead of writing through it
    tmp = tempfile.NamedTemporaryFile(dir=cache_dir, prefix=f"{key}.", suffix=".tmp",
                                      delete=False, mode="w", encoding="utf-8", newline="\n")
    try:
        with tmp:
            tmp.write(subckt)
        os.chmod(tmp.name, DEFAULT_FILE_MODE)
        os.replace(tmp.name, model_path)
    except BaseException:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
        raise

    # Update manifest (prefer existing file; always write to manifest.json)
    read_path = _cache_manifest_path(cache_dir)
    index = read_json_object(read_path) or {}

    import datetime
    index[key] = {
        "file": filename,
        "mpn": mpn,
        "type": component_type,
        "source": source,
        "specs": _serialize_specs(specs),
        "created": datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
    }

    # Write beside the target and swap it in, so a reader never sees a half-written manifest
    write_path = cache_dir / MANIFEST_FILENAME
    tmp = tempfile.NamedTemporaryFile(dir=cache_dir, prefix="manifest.", suffix=".tmp",
                                      delete=False, mode="w", encoding="utf-8", newline="\n")
    try:
        with tmp:
            json.dump(index, tmp, indent=2)
        os.chmod(tmp.name, DEFAULT_FILE_MODE)
        os.replace(tmp.name, write_path)
    except BaseException:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
        raise

    # Remove legacy file after successful migration
    old_path = cache_dir / LEGACY_MANIFEST_FILENAME
    if old_path.exists() and old_path != write_path:
        try:
            old_path.unlink()
        except OSError:
            pass

    # Invalidate in-memory cache so next read picks up the new entry
    _index_cache.pop(str(cache_dir), None)


def _serialize_specs(specs):
    """Make specs dict JSON-serializable (handle any non-standard types)."""
    result = {}
    for k, v in specs.items():
        if isinstance(v, (int, float, str, bool, type(None))):
            result[k] = v
        elif isinstance(v, dict):
            result[k] = _serialize_specs(v)
        else:
            result[k] = str(v)
    return result


# ---------------------------------------------------------------------------
# Model generators per component type
# ---------------------------------------------------------------------------

_GENERATORS = {
    "opamp": generate_opamp_model,
    "ldo": generate_ldo_model,
    "comparator": generate_comparator_model,
    "vref": generate_vref_model,
}


@dataclass(frozen=True)
class ModelOptions:
    """CLI-level model resolution options.

    cache_dir: directory under which spice/models/ is read and written
               (default: beside the first source file the analysis JSON names,
               "file" or "inputs.source_files[0]")
    offline:   never query distributor APIs or datasheets; cache + lookup table only
    trust_project_models: paste cached models verbatim, even ones with simulator
               control commands or includes outside the models folder
    """
    cache_dir: str | None = None
    offline: bool = False
    trust_project_models: bool = False


def get_model_for_part(mpn, component_type=None, context=None, options=None, *, diagnostics=None):
    """Resolve a SPICE model for a component, using the full cascade.

    Resolution order:
        1. Project cache — previously resolved models (instant)
        2. Distributor API parametric data — LCSC, DigiKey, element14, Mouser
           (skipped when options.offline)
        3. Structured datasheet extraction — from datasheets/extracted/ cache
        4. Heuristic PDF regex extraction — from datasheets/ PDFs
        5. Built-in lookup table — common op-amps, LDOs, comparators and
           references with verified specs
        6. Ideal/generic model fallback

    Real data (APIs, datasheets) takes priority over the lookup table.
    The lookup table is the offline safety net when no network/datasheet
    is available.

    Args:
        mpn: Manufacturer part number (from det["value"])
        component_type: Hint — "opamp", "ldo", "comparator", "vref"
        context: Analysis JSON dict (for cache dir and project dir)
        options: Optional ModelOptions; cache_dir overrides the cache location,
                 offline skips the API/datasheet tier (cache + lookup table only)
        diagnostics: Optional list sink; a failed API/datasheet tier is recorded there

    Returns:
        (subckt_string, source_note, specs_or_None)
        source_note examples: "cache:LM358", "api:lcsc", "datasheet:LM358",
                              "lookup:LM358", "ideal"
    """
    if not mpn or len(mpn) < 2:
        return None, "ideal", None

    opts = options or ModelOptions()
    use_cache = bool(context or opts.cache_dir)

    # --- Tier 0: Project cache ---
    if use_cache:
        cache_dir = resolve_cache_dir(context or {}, override_dir=opts.cache_dir)
        cached_subckt, cached_specs, refused = _lookup_cached_model(cache_dir, mpn, diagnostics)
        if refused:
            use_cache = False
        problem = None
        if cached_subckt and not opts.trust_project_models:
            problem = model_text_problem(cached_subckt)
            if problem:
                record(diagnostics, "spice_model_cache.get_cached_model", ValueError(problem),
                       "project model skipped")
                # The fallback model is used but never replaces the user's file
                use_cache = False
        if cached_subckt and not problem:
            return cached_subckt, f"cache:{mpn}", cached_specs

    # --- Tier 1: Distributor API parametric specs ---
    if not opts.offline:
        try:
            from spice_spec_fetcher import fetch_specs
            # Datasheet fallback: only a project the analysis really names, never the cwd
            project_dir = extraction_project_dir(context)
            if project_dir is not None:
                project_dir = str(project_dir)

            api_specs, api_source = fetch_specs(mpn, component_type, project_dir,
                                                diagnostics=diagnostics)
            if api_specs:
                # Determine component type from the specs we got
                resolved_type = component_type
                if not resolved_type:
                    if api_specs.get("gbw_hz"):
                        resolved_type = "opamp"
                    elif api_specs.get("dropout_mv") or api_specs.get("iout_max_ma"):
                        resolved_type = "ldo"
                generator = _GENERATORS.get(resolved_type)
                if generator:
                    subckt = generator(mpn, api_specs)
                    if use_cache:
                        cache_dir = resolve_cache_dir(context or {}, override_dir=opts.cache_dir)
                        try:
                            cache_model(cache_dir, mpn, subckt, api_specs,
                                        api_source, resolved_type)
                        except OSError as exc:
                            record(diagnostics, "spice_model_cache.cache_model", exc,
                                   "model not cached")
                    return subckt, f"{api_source}", api_specs
        except ImportError:
            pass  # spice_spec_fetcher not available
        except Exception as exc:  # API/datasheet extraction failed — fall through
            record(diagnostics, "spice_model_cache.get_model_for_part", exc,
                   f"API/datasheet model tier skipped for {mpn}")

    # --- Tier 2: Built-in lookup table (offline fallback) ---
    specs, resolved_type = lookup_part_specs(mpn, component_type)
    if specs:
        generator = _GENERATORS.get(resolved_type)
        if generator:
            subckt = generator(mpn, specs)
            if use_cache:
                cache_dir = resolve_cache_dir(context or {}, override_dir=opts.cache_dir)
                try:
                    cache_model(cache_dir, mpn, subckt, specs, "lookup", resolved_type)
                except OSError as exc:
                    record(diagnostics, "spice_model_cache.cache_model", exc, "model not cached")
            return subckt, f"lookup:{mpn}", specs

    # --- Fallback: ideal model ---
    return None, "ideal", None
