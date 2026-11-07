"""
Shared analysis cache management for kicad-happy.

Manages the analysis/ directory convention: timestamped run folders,
manifest.json for freshness tracking, source file hashing, retention
pruning, and .gitignore generation.

Consumed by the kicad skill (writer): creates runs, updates manifest.
Other tools (diff_analysis, what_if) read runs via the manifest.

Zero external dependencies -- stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from kicad_core.diagnostics import record
from kicad_core.fileio import atomic_write_text
from finding_schema import strip_llm_overlays


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MANIFEST_FILENAME = 'manifest.json'

CANONICAL_OUTPUTS = {
    'schematic': 'schematic.json',
    'pcb': 'pcb.json',
    'gerber': 'gerber.json',
    'spice': 'spice.json',
    'emc': 'emc.json',
    'thermal': 'thermal.json',
    'lifecycle': 'lifecycle.json',
    'cross_analysis': 'cross_analysis.json',
}

# File extensions that each output's contents depend on. Used by create_run
# to decide per-file whether a carried-forward output is stale vs safe to
# copy. Outputs not listed are treated as derived (never blocked from copy).
_OUTPUT_SOURCE_EXT = {
    'schematic.json': ('.kicad_sch', '.sch'),
    'pcb.json': ('.kicad_pcb',),
    'gerber.json': ('.gbr', '.gtl', '.gbl', '.gts', '.gbs', '.gto', '.gbo',
                    '.gm1', '.drl', '.txt'),
}

# The only names the cache ever records in a run's 'outputs' map.
_CANONICAL_NAMES = frozenset(CANONICAL_OUTPUTS.values())

# Outputs built from other outputs of the run. One stays in a run only while every
# output it was built from (inputs.upstream_artifacts) is unchanged; one without that
# record counts as built from the run's schematic and pcb outputs.
_DERIVED_OUTPUTS = ('thermal.json', 'emc.json', 'cross_analysis.json', 'spice.json')
_UPSTREAM_OUTPUTS = ('schematic.json', 'pcb.json')

GITIGNORE_CONTENT = """\
# Analysis output -- regenerable from source files
*
!.gitignore
!manifest.json
"""

def _run_id_problem(analysis_dir: str, rid: Any) -> Optional[str]:
    """Why *rid* does not name one run folder directly inside *analysis_dir*, or None.

    Manifest run ids become paths that are written into and deleted; a manifest is
    user-editable (track_in_git commits it), so an absolute, dotted or nested id must
    never resolve outside the analysis directory.
    """
    if not isinstance(rid, str) or not rid or rid in ('.', '..'):
        return "is not a folder name"
    if os.path.basename(rid) != rid or os.path.isabs(rid) or '/' in rid or '\\' in rid:
        return "is not a folder name"
    try:
        root = os.path.realpath(analysis_dir)
        # A symlinked run dir resolving anywhere but directly under the root is not a run.
        if os.path.dirname(os.path.realpath(os.path.join(analysis_dir, rid))) == root:
            return None
        return "resolves outside the analysis directory"
    except (ValueError, OSError):
        return "is not a folder name"


def _is_run_id(analysis_dir: str, rid: Any) -> bool:
    """True when *rid* names one run folder directly inside *analysis_dir*."""
    return _run_id_problem(analysis_dir, rid) is None


def get_run(analysis_dir: str, run_id: Any,
            manifest: Optional[Dict[str, Any]] = None) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Return (folder_path, run_metadata) for *run_id*, or None when the manifest has no
    such run or the id is not a folder directly inside *analysis_dir*."""
    if manifest is None:
        manifest = load_manifest(analysis_dir)
    runs = manifest.get('runs', {})
    if not run_id or not isinstance(run_id, str) or run_id not in runs:
        return None
    if not _is_run_id(analysis_dir, run_id):
        return None
    return os.path.join(analysis_dir, run_id), runs[run_id]


def merged_overlay_path(path: str) -> str:
    """analysis/merged/<run>/<file>: the reviewed copy of analysis/<run>/<file> that the
    consumers read unless --only-deterministic is given."""
    run_dir, name = os.path.split(path)
    return os.path.join(os.path.dirname(run_dir), "merged", os.path.basename(run_dir), name)


def reviewed_overlay(path: str) -> Optional[str]:
    """merged_overlay_path(path) when that reviewed copy holds the same deterministic content as
    *path* (its llm_* fields stripped, it equals the raw file), else None. A copy that no longer
    matches, such as one merged before the raw file was rewritten, is reported and not used."""
    overlay = merged_overlay_path(path)
    if not os.path.lexists(overlay):
        return None
    try:
        if os.path.isfile(overlay):
            with open(overlay, encoding="utf-8") as f:
                merged = json.load(f)
            try:
                with open(path, encoding="utf-8") as f:
                    raw = json.load(f)
            except (ValueError, OSError):
                print(f"Note: cannot read {path}; ignoring the reviewed copy {overlay}",
                      file=sys.stderr)
                return None
            if strip_llm_overlays(merged) == raw:
                return overlay
    except (ValueError, OSError):
        pass
    print(f"Note: {overlay} does not match {path}; reading the raw file "
          f"(re-run merge_annotations.py to use the review)", file=sys.stderr)
    return None


def _empty_manifest() -> Dict[str, Any]:
    """Return a fresh empty manifest (avoids mutable default sharing)."""
    return {
        'version': 1,
        'project': '',
        'current': None,
        'runs': {},
    }


# ---------------------------------------------------------------------------
# Directory resolution
# ---------------------------------------------------------------------------

def resolve_analysis_dir(path: str) -> str:
    """Return a canonical analysis-dir path.

    Command-line ``--analysis-dir`` paths should be interpreted the same way
    across all analyzers:
    - absolute paths stay absolute
    - relative paths are resolved from the current working directory

    Do not anchor ``path`` to the input schematic/PCB file's directory. When
    callers already pass a project-relative path like ``hardware/foo/analysis``
    alongside a project-relative input file like ``hardware/foo/design.kicad_*``,
    joining them would incorrectly duplicate the prefix as
    ``hardware/foo/hardware/foo/analysis``.
    """
    return os.path.abspath(path)


# ---------------------------------------------------------------------------
# Manifest I/O
# ---------------------------------------------------------------------------

def load_manifest(analysis_dir: str) -> Dict[str, Any]:
    """Read manifest.json from analysis directory.

    Returns empty manifest structure if file is missing or corrupt.
    """
    manifest_path = os.path.join(analysis_dir, MANIFEST_FILENAME)
    if not os.path.isfile(manifest_path):
        return _empty_manifest()
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (ValueError, OSError):
        # Corrupt manifest -- back up and return empty
        backup = manifest_path + '.bak'
        try:
            backed_up = _copy_regular(manifest_path, backup, "load_manifest")
        except OSError:
            backed_up = False
        if backed_up:
            print(f'Warning: corrupt manifest at {manifest_path}, '
                  f'backed up to .bak', file=sys.stderr)
        else:
            print(f'Warning: corrupt manifest at {manifest_path}; '
                  f'no backup made ({backup} is not a regular file)', file=sys.stderr)
        return _empty_manifest()


def save_manifest(analysis_dir: str, manifest: Dict[str, Any]) -> None:
    """Write manifest.json atomically. An existing file keeps its mode, a new one gets the
    umask mode; a symlink at the path is replaced, never written through. An owner-only
    (0600) file is what earlier versions wrote, so it is rewritten with the umask mode."""
    os.makedirs(analysis_dir, exist_ok=True)
    manifest_path = os.path.join(analysis_dir, MANIFEST_FILENAME)
    try:
        st = os.lstat(manifest_path)
        owner_only = stat.S_ISREG(st.st_mode) and stat.S_IMODE(st.st_mode) == 0o600
    except OSError:
        owner_only = False
    atomic_write_text(manifest_path, json.dumps(manifest, indent=2) + '\n',
                      follow_symlinks=False, keep_mode=not owner_only)


# ---------------------------------------------------------------------------
# Source file hashing
# ---------------------------------------------------------------------------

def hash_source_file(filepath: str) -> Optional[str]:
    """SHA-256 hash of a file, returned as 'sha256:<hex>'.

    Returns None if the file doesn't exist.
    """
    if not os.path.isfile(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return f'sha256:{h.hexdigest()}'


# ---------------------------------------------------------------------------
# Run folder naming
# ---------------------------------------------------------------------------

def generate_run_folder_name(analysis_dir: Optional[str] = None) -> str:
    """Generate a run folder name in YYYY-MM-DD_HHMM format.

    This names the folder under analysis/ and keys the manifest. It is not
    the provenance ``run_id`` stamped into analyzer output, which
    ``run_id.generate_run_id`` produces.

    If analysis_dir is provided and a folder with that name already exists,
    appends a suffix: 2026-04-08_1919-2, 2026-04-08_1919-3, etc.
    """
    now = datetime.now().astimezone()
    base_id = now.strftime('%Y-%m-%d_%H%M')

    if analysis_dir is None or not os.path.isdir(analysis_dir):
        return base_id

    if not os.path.exists(os.path.join(analysis_dir, base_id)):
        return base_id

    # Deduplicate
    for suffix in range(2, 100):
        candidate = f'{base_id}-{suffix}'
        if not os.path.exists(os.path.join(analysis_dir, candidate)):
            return candidate

    return base_id  # fallback (should never happen)


# ---------------------------------------------------------------------------
# Run creation
# ---------------------------------------------------------------------------

def _is_symlink_or_irregular(path: str) -> bool:
    try:
        return not stat.S_ISREG(os.lstat(path).st_mode)
    except OSError:
        return True


def _copy_regular(src: str, dst: str, caller: str = "copy") -> bool:
    """Copy a regular file without reading or writing through a symlink.

    A symlink or other non-regular file at ``src`` or ``dst`` is refused
    (returns False after one diagnostic) and never read or written through.
    Otherwise the copy goes to a temp file beside ``dst`` and is renamed over it.
    """
    if _is_symlink_or_irregular(src):
        record(None, f"analysis_cache.{caller}",
               ValueError(f"{src} is a symlink"), "file not copied")
        return False
    if os.path.lexists(dst) and _is_symlink_or_irregular(dst):
        record(None, f"analysis_cache.{caller}",
               ValueError(f"{dst} is a symlink"), "file not copied")
        return False
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(dst) or ".", prefix=".copy-")
    os.close(fd)
    try:
        shutil.copy2(src, tmp)
        os.replace(tmp, dst)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return True


def ensure_gitignore(analysis_dir: str) -> None:
    """Write analysis/.gitignore unless anything is already at that path.

    A symlink there (even a dangling one) is skipped with a warning, never
    written through.
    """
    path = os.path.join(analysis_dir, '.gitignore')
    if os.path.lexists(path):
        if os.path.islink(path):
            record(None, "analysis_cache.ensure_gitignore",
                   ValueError(f"{path} is a symlink"), "file not written")
        return
    with open(path, 'w', encoding='utf-8', newline="\n") as f:
        f.write(GITIGNORE_CONTENT)


def _sha256_hex(path: str) -> Optional[str]:
    if _is_symlink_or_irregular(path):
        return None
    h = hash_source_file(path)
    return h[len('sha256:'):] if h else None


def _built_from(run_dir: str, filename: str) -> Dict[str, Optional[str]]:
    """Upstream output name -> sha256 hex the derived *filename* in *run_dir* was built from
    (None when not recorded: the run's own file of that name is assumed)."""
    path = os.path.join(run_dir, filename)
    data = None
    if not _is_symlink_or_irregular(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = None
    inputs = data.get('inputs') if isinstance(data, dict) else None
    upstream = inputs.get('upstream_artifacts') if isinstance(inputs, dict) else None
    if isinstance(upstream, dict) and upstream:
        built = {}
        for stage, art in upstream.items():
            name = CANONICAL_OUTPUTS.get(stage)
            if name in _UPSTREAM_OUTPUTS:
                sha = art.get('sha256') if isinstance(art, dict) else None
                built[name] = sha if isinstance(sha, str) else None
        return built
    return {name: None for name in _UPSTREAM_OUTPUTS
            if os.path.lexists(os.path.join(run_dir, name))}


def _derived_stale(run_dir: str, filename: str,
                   replaced: Dict[str, Optional[str]]) -> List[str]:
    """Names of the inputs that make derived *filename* in *run_dir* stale (empty = fresh).

    *replaced* maps each upstream output that changes in the next state of the run to the
    file that will hold it (None = it leaves the run); upstreams not listed stay as they are.
    """
    stale = []
    for name, recorded in sorted(_built_from(run_dir, filename).items()):
        if name not in replaced:
            continue
        new_path = replaced[name]
        expected = recorded or _sha256_hex(os.path.join(run_dir, name))
        if new_path is None or expected is None or _sha256_hex(new_path) != expected:
            stale.append(name)
    return stale


def _prune_output_hashes(hashes: Dict[str, str], run_dir: str) -> None:
    """Drop the schematic.json/pcb.json hashes an EMC or SPICE write recorded unless such an
    output is still in *run_dir* and the run holds that same file."""
    keep = any(os.path.lexists(os.path.join(run_dir, name)) for name in ('emc.json', 'spice.json'))
    for name in _UPSTREAM_OUTPUTS:
        if name in hashes and not (keep and hashes[name] == 'sha256:%s' % _sha256_hex(
                os.path.join(run_dir, name))):
            del hashes[name]


def _incoming_outputs(outputs_dir: str) -> Dict[str, str]:
    """Canonical output name -> path for each new output file in *outputs_dir*."""
    return {name: os.path.join(outputs_dir, name) for name in sorted(os.listdir(outputs_dir))
            if name in _CANONICAL_NAMES and os.path.isfile(os.path.join(outputs_dir, name))}


def outputs_landed(run_dir: str, outputs_dir: str) -> bool:
    """True when every canonical output in *outputs_dir* is a regular file in *run_dir*."""
    return all(not _is_symlink_or_irregular(os.path.join(run_dir, name))
               for name in _incoming_outputs(outputs_dir))


def _note_dropped(filename: str, upstream: str) -> None:
    print(f"Note: {filename} dropped from the run: built from an older {upstream}; "
          f"re-run its analyzer", file=sys.stderr)


def create_run(analysis_dir: str,
               outputs_dir: str,
               source_hashes: Dict[str, str],
               scripts: Dict[str, str],
               run_id: Optional[str] = None) -> str:
    """Create a new timestamped run folder with outputs.

    Copies all files from outputs_dir into the new run folder.
    Copies forward any outputs from the previous current run that
    are not present in outputs_dir (partial run support), except one
    whose sources changed or a derived output built from an upstream
    output this run replaces.
    Updates the manifest: adds the run entry, sets current pointer.

    Args:
        analysis_dir: Path to the analysis/ directory.
        outputs_dir: Temp directory containing the new output files.
        source_hashes: Dict of source file hashes for this run.
        scripts: Dict of analysis_type -> script command used.
        run_id: Override the auto-generated run ID (for testing).

    Returns:
        The run ID (folder name) of the created run.
    """
    manifest = load_manifest(analysis_dir)
    if run_id is None:
        run_id = generate_run_folder_name(analysis_dir)

    run_dir = os.path.join(analysis_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)

    # Copy forward outputs from previous current run. Per-file staleness
    # check: a carried-forward output is stale only if *its* source files
    # (by extension) appear in cur_hashes with a different hash than in
    # prev_hashes. Source files that only appear on one side (e.g.
    # re-running pcb leaves the schematic hash untouched) do not poison
    # unrelated outputs.
    prev_run_id = manifest.get('current')
    prev_outputs = {}
    dropped = set()
    problem = _run_id_problem(analysis_dir, prev_run_id) if prev_run_id else None
    if problem:
        record(None, "analysis_cache.create_run",
               ValueError(f"manifest current run id {prev_run_id!r} {problem}"),
               "run id ignored")
        prev_run_id = None
    if prev_run_id and prev_run_id in manifest.get('runs', {}):
        prev_run_dir = os.path.join(analysis_dir, prev_run_id)
        prev_run_info = manifest['runs'][prev_run_id]
        prev_outputs = {}
        for analysis_type, filename in (prev_run_info.get('outputs', {}) or {}).items():
            if filename in _CANONICAL_NAMES:
                prev_outputs[analysis_type] = filename
            else:
                record(None, "analysis_cache.create_run",
                       ValueError(f"manifest output {filename!r} is not a canonical output name"),
                       "manifest output ignored")
        prev_hashes = prev_run_info.get('source_hashes', {}) or {}
        cur_hashes = source_hashes or {}
        incoming = _incoming_outputs(outputs_dir)
        # Upstream outputs this run replaces or drops; filled before the derived outputs
        # (ordered last) are checked against it.
        replaced = {name: path for name, path in incoming.items() if name in _UPSTREAM_OUTPUTS}
        ordered = sorted(prev_outputs.items(), key=lambda item: item[1] in _DERIVED_OUTPUTS)
        for analysis_type, filename in ordered:
            exts = _OUTPUT_SOURCE_EXT.get(filename, ())
            stale = False
            if exts:
                for key, old_hash in prev_hashes.items():
                    if not any(key.lower().endswith(e) for e in exts):
                        continue
                    new_hash = cur_hashes.get(key)
                    if new_hash is not None and new_hash != old_hash:
                        stale = True
                        break
            if not stale and filename in _DERIVED_OUTPUTS and filename not in incoming:
                upstream = _derived_stale(prev_run_dir, filename, replaced)
                if upstream:
                    _note_dropped(filename, upstream[0])
                    stale = True
            prev_file = os.path.join(prev_run_dir, filename)
            new_file = os.path.join(run_dir, filename)
            if not stale and os.path.lexists(prev_file):
                if os.path.isfile(new_file) or _copy_regular(prev_file, new_file, "create_run"):
                    continue
            dropped.add(analysis_type)
            if filename in _UPSTREAM_OUTPUTS and filename not in incoming:
                replaced[filename] = None

    # Copy new outputs (overwrites any copied-forward files)
    new_outputs = {}
    for filename in os.listdir(outputs_dir):
        src = os.path.join(outputs_dir, filename)
        if os.path.isfile(src) and filename.endswith('.json'):
            if not _copy_regular(src, os.path.join(run_dir, filename), "create_run"):
                continue
            # Map filename back to analysis type
            for atype, canonical in CANONICAL_OUTPUTS.items():
                if filename == canonical:
                    new_outputs[atype] = filename
                    break

    # Merge output maps: previous outputs still in the run + new (new wins)
    merged_outputs = {atype: new_outputs.get(atype, filename)
                      for atype, filename in prev_outputs.items()
                      if atype in new_outputs or atype not in dropped}
    merged_outputs.update(new_outputs)

    # Every source behind the run's outputs keeps its hash; this run's hashes win.
    run_hashes = {}
    if prev_run_id and prev_run_id in manifest.get('runs', {}):
        run_hashes.update(manifest['runs'][prev_run_id].get('source_hashes', {}) or {})
        _prune_output_hashes(run_hashes, run_dir)
    run_hashes.update(source_hashes or {})

    # Update manifest
    manifest['current'] = run_id
    manifest.setdefault('runs', {})[run_id] = {
        'source_hashes': run_hashes,
        'outputs': merged_outputs,
        'scripts': scripts,
        'generated': datetime.now().astimezone().isoformat(timespec='seconds'),
        'pinned': False,
    }
    save_manifest(analysis_dir, manifest)

    return run_id


def overwrite_current(analysis_dir: str,
                      outputs_dir: str,
                      source_hashes: Optional[Dict[str, str]] = None) -> bool:
    """Overwrite the current run folder with new outputs.

    Used when sources changed but analysis results didn't differ
    meaningfully. Updates source hashes and timestamp in the manifest
    without creating a new folder.

    Args:
        analysis_dir: Path to the analysis/ directory.
        outputs_dir: Temp directory containing the new output files.
        source_hashes: Updated source hashes (None = keep existing).

    Returns:
        False when a file was refused (not copied), else True.
    """
    manifest = load_manifest(analysis_dir)
    current_id = manifest.get('current')
    if not current_id or current_id not in manifest.get('runs', {}):
        # No current run -- fall back to creating a new run
        rid = create_run(analysis_dir, outputs_dir,
                         source_hashes=source_hashes or {},
                         scripts={})
        return outputs_landed(os.path.join(analysis_dir, rid), outputs_dir)
    problem = _run_id_problem(analysis_dir, current_id)
    if problem:
        record(None, "analysis_cache.overwrite_current",
               ValueError(f"manifest current run id {current_id!r} {problem}"),
               "run id ignored")
        manifest['current'] = None
        manifest['runs'] = {rid: meta for rid, meta in manifest.get('runs', {}).items()
                            if _is_run_id(analysis_dir, rid)}
        save_manifest(analysis_dir, manifest)
        rid = create_run(analysis_dir, outputs_dir,
                         source_hashes=source_hashes or {},
                         scripts={})
        return outputs_landed(os.path.join(analysis_dir, rid), outputs_dir)

    current_dir = os.path.join(analysis_dir, current_id)
    os.makedirs(current_dir, exist_ok=True)

    # Derived outputs built from an upstream output this write replaces leave the run.
    incoming = _incoming_outputs(outputs_dir)
    replaced = {name: path for name, path in incoming.items() if name in _UPSTREAM_OUTPUTS}
    stale = {}
    if replaced:
        for filename in _DERIVED_OUTPUTS:
            if filename in incoming or not os.path.lexists(os.path.join(current_dir, filename)):
                continue
            upstream = _derived_stale(current_dir, filename, replaced)
            if upstream:
                stale[filename] = upstream

    # Overwrite files
    refused = set()
    copied = set()
    for filename in os.listdir(outputs_dir):
        src = os.path.join(outputs_dir, filename)
        if os.path.isfile(src) and filename.endswith('.json'):
            if _copy_regular(src, os.path.join(current_dir, filename), "overwrite_current"):
                copied.add(filename)
            else:
                refused.add(filename)

    # Update manifest entry
    run_entry = manifest['runs'][current_id]
    dropped = False
    for filename, upstreams in sorted(stale.items()):
        upstream = next((name for name in upstreams if name in copied), None)
        if upstream is None:
            continue
        try:
            os.unlink(os.path.join(current_dir, filename))
        except OSError as exc:
            record(None, "analysis_cache.overwrite_current", exc, "stale output kept")
            continue
        dropped = True
        _note_dropped(filename, upstream)
        outputs_map = run_entry.get('outputs')
        if isinstance(outputs_map, dict):
            for atype in [t for t, fn in outputs_map.items() if fn == filename]:
                del outputs_map[atype]
    if dropped and isinstance(run_entry.get('source_hashes'), dict):
        _prune_output_hashes(run_entry['source_hashes'], current_dir)
    if source_hashes is not None and not refused:
        # Merge, don't replace — running pcb after schematic should keep
        # the schematic's hash alongside the pcb's, so staleness detection
        # still works against every source file contributing to the run.
        existing = run_entry.get('source_hashes', {}) or {}
        existing.update(source_hashes)
        run_entry['source_hashes'] = existing
    run_entry['generated'] = datetime.now().astimezone().isoformat(timespec='seconds')

    # Update outputs map for any new output types written
    outputs = run_entry.setdefault('outputs', {})
    inv_canonical = {v: k for k, v in CANONICAL_OUTPUTS.items()}
    for filename in os.listdir(current_dir):
        if filename.endswith('.json') and filename in inv_canonical:
            atype = inv_canonical[filename]
            if atype not in outputs and not _is_symlink_or_irregular(
                    os.path.join(current_dir, filename)):
                outputs[atype] = filename
    for atype in [t for t, fn in outputs.items() if fn in refused]:
        del outputs[atype]

    save_manifest(analysis_dir, manifest)
    return not refused


# ---------------------------------------------------------------------------
# Retention pruning
# ---------------------------------------------------------------------------

def prune_runs(analysis_dir: str, retention: int = 5) -> List[str]:
    """Delete oldest unpinned runs exceeding the retention limit.

    Args:
        analysis_dir: Path to the analysis/ directory.
        retention: Max unpinned runs to keep. 0 = unlimited.

    Returns:
        List of pruned run IDs.
    """
    if retention <= 0:
        return []

    manifest = load_manifest(analysis_dir)
    current_id = manifest.get('current')
    runs = manifest.get('runs', {})

    # Separate pinned and unpinned, sorted by generated timestamp
    unpinned = [
        (rid, meta) for rid, meta in sorted(
            runs.items(), key=lambda x: x[1].get('generated', ''))
        if not meta.get('pinned', False) and rid != current_id
    ]
    for rid, _meta in list(unpinned):
        problem = _run_id_problem(analysis_dir, rid)
        if problem:
            record(None, "analysis_cache.prune_runs",
                   ValueError(f"manifest run id {rid!r} {problem}"),
                   "run id ignored")
            unpinned.remove((rid, _meta))

    # Always keep current in the unpinned count
    unpinned_count = len(unpinned) + (1 if current_id and current_id in runs
                                      and not runs[current_id].get('pinned')
                                      else 0)

    pruned = []
    while unpinned_count > retention and unpinned:
        rid, _meta = unpinned.pop(0)  # oldest first
        # Delete folder
        run_dir = os.path.join(analysis_dir, rid)
        if os.path.isdir(run_dir):
            shutil.rmtree(run_dir)
        # Remove from manifest
        del manifest['runs'][rid]
        pruned.append(rid)
        unpinned_count -= 1

    if pruned:
        save_manifest(analysis_dir, manifest)

    return pruned


# ---------------------------------------------------------------------------
# Pinning
# ---------------------------------------------------------------------------

def pin_run(analysis_dir: str, run_id: str) -> None:
    """Mark a run as pinned (survives retention pruning)."""
    manifest = load_manifest(analysis_dir)
    if run_id in manifest.get('runs', {}):
        manifest['runs'][run_id]['pinned'] = True
        save_manifest(analysis_dir, manifest)


# ---------------------------------------------------------------------------
# Current run accessor
# ---------------------------------------------------------------------------

def get_current_run(analysis_dir: str
                    ) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Return (folder_path, run_metadata) for the current run.

    Returns None if no current run exists.
    """
    manifest = load_manifest(analysis_dir)
    return get_run(analysis_dir, manifest.get('current'), manifest)


def list_runs(analysis_dir: str, limit: int = 0) -> list:
    """Return run entries sorted newest-first.

    Each entry is (run_id, run_metadata_dict). If limit > 0, return at most
    that many. Excludes runs whose folders no longer exist on disk.
    """
    manifest = load_manifest(analysis_dir)
    runs = manifest.get('runs', {})
    sorted_ids = sorted(runs.keys(), reverse=True)
    result = []
    for run_id in sorted_ids:
        if not _is_run_id(analysis_dir, run_id):
            continue
        run_dir = os.path.join(analysis_dir, run_id)
        if os.path.isdir(run_dir):
            result.append((run_id, runs[run_id]))
        if limit > 0 and len(result) >= limit:
            break
    return result


# ---------------------------------------------------------------------------
# New-run decision logic
# ---------------------------------------------------------------------------

# Severity ordering for threshold comparison; the 'all' threshold means any detected change, the
# same level as 'minor' (an unchanged output still overwrites the current run).
_SEVERITY_ORDER = {'none': 0, 'all': 1, 'minor': 1, 'major': 2, 'breaking': 3}


def should_create_new_run(analysis_dir: str,
                          new_outputs_dir: str,
                          diff_threshold: str = 'major') -> bool:
    """Decide whether new outputs warrant a new timestamped folder.

    Runs the pure diff engine (diff_engine) on each matching output type between the
    current run and the new outputs. If any diff severity meets or
    exceeds the threshold, returns True.

    Returns True if:
      - No current run exists (first run)
      - diff_engine finds changes at or above the threshold
    Returns False if all diffs are below the threshold.

    Args:
        analysis_dir: Path to the analysis/ directory.
        new_outputs_dir: Directory containing the new output JSONs.
        diff_threshold: Minimum severity to trigger a new folder.
            One of: 'all' (any detected change, same as 'minor'), 'minor', 'major', 'breaking'.
    """
    current = get_current_run(analysis_dir)
    if current is None:
        return True

    current_dir, current_meta = current
    threshold_level = _SEVERITY_ORDER.get(diff_threshold, 2)

    # Pure diff engine (no CLI import; v3 removed the analysis_cache <-> diff_analysis cycle).
    try:
        import diff_engine
    except ImportError:
        import sys
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        try:
            import diff_engine
        except ImportError:
            # Can't diff -- default to creating a new run
            return True

    # Compare each output type
    for filename in os.listdir(new_outputs_dir):
        if not filename.endswith('.json'):
            continue
        new_path = os.path.join(new_outputs_dir, filename)
        current_path = os.path.join(current_dir, filename)
        if not os.path.isfile(current_path):
            # New output type (e.g., pcb.json landing after a schematic-only
            # run). Extend the current run instead of spawning a duplicate
            # folder — only actual diffs vs existing outputs warrant a new run.
            continue

        try:
            with open(current_path, encoding="utf-8") as f:
                base_data = json.load(f)
            with open(new_path, encoding="utf-8") as f:
                head_data = json.load(f)
        except (ValueError, OSError):
            return True  # Can't compare -- treat as changed

        # Detect analyzer type and diff
        analyzer_type = base_data.get('analyzer_type', '')
        diff_func = {
            'schematic': getattr(diff_engine, 'diff_schematic', None),
            'pcb': getattr(diff_engine, 'diff_pcb', None),
            'emc': getattr(diff_engine, 'diff_emc', None),
            'spice': getattr(diff_engine, 'diff_spice', None),
        }.get(analyzer_type)

        if diff_func is None:
            continue  # Unknown type -- skip

        diff_result = diff_func(base_data, head_data, threshold=1.0)
        severity = diff_engine.classify_severity(analyzer_type, diff_result)
        if _SEVERITY_ORDER.get(severity, 0) >= threshold_level:
            return True

    return False
