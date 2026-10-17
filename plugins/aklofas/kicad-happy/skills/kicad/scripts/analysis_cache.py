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
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


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

GITIGNORE_CONTENT = """\
# Analysis output -- regenerable from source files
*
!.gitignore
!manifest.json
"""

def _empty_manifest() -> Dict[str, Any]:
    """Return a fresh empty manifest (avoids mutable default sharing)."""
    return {
        'version': 1,
        'project': '',
        'current': None,
        'runs': {},
    }


# ---------------------------------------------------------------------------
# Directory initialization
# ---------------------------------------------------------------------------

def ensure_analysis_dir(project_dir: str,
                        project_file: str = '',
                        config: Optional[Dict[str, Any]] = None) -> str:
    """Create analysis/ directory with manifest and .gitignore if needed.

    Args:
        project_dir: Root directory of the KiCad project.
        project_file: Name of the .kicad_pro file (for manifest).
        config: Merged project config dict. If None, uses defaults.

    Returns:
        Absolute path to the analysis directory.
    """
    if config is None:
        config = {}
    analysis_cfg = config.get('analysis', {})
    output_dir = analysis_cfg.get('output_dir', 'analysis')
    track_in_git = analysis_cfg.get('track_in_git', False)

    analysis_dir = os.path.join(os.path.abspath(project_dir), output_dir)
    os.makedirs(analysis_dir, exist_ok=True)

    # Create manifest if it doesn't exist
    manifest_path = os.path.join(analysis_dir, MANIFEST_FILENAME)
    if not os.path.isfile(manifest_path):
        manifest = _empty_manifest()
        manifest['project'] = project_file
        save_manifest(analysis_dir, manifest)

    # Create .gitignore if needed
    gitignore_path = os.path.join(analysis_dir, '.gitignore')
    if not track_in_git and not os.path.isfile(gitignore_path):
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(GITIGNORE_CONTENT)

    return analysis_dir


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
    except (json.JSONDecodeError, OSError):
        # Corrupt manifest -- back up and return empty
        backup = manifest_path + '.bak'
        try:
            shutil.copy2(manifest_path, backup)
        except OSError:
            pass
        print(f'Warning: corrupt manifest at {manifest_path}, '
              f'backed up to .bak', file=sys.stderr)
        return _empty_manifest()


def save_manifest(analysis_dir: str, manifest: Dict[str, Any]) -> None:
    """Write manifest.json atomically (write-to-temp then rename)."""
    os.makedirs(analysis_dir, exist_ok=True)
    manifest_path = os.path.join(analysis_dir, MANIFEST_FILENAME)
    with tempfile.NamedTemporaryFile(
        mode='w',
        encoding='utf-8',
        dir=analysis_dir,
        prefix=MANIFEST_FILENAME + '.',
        suffix='.tmp',
        delete=False,
    ) as f:
        json.dump(manifest, f, indent=2)
        f.write('\n')
        tmp_path = f.name
    os.replace(tmp_path, manifest_path)


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


def hash_source_files(project_dir: str,
                      source_files: List[str]) -> Dict[str, str]:
    """Hash multiple source files relative to project_dir.

    Args:
        project_dir: Root directory of the KiCad project.
        source_files: List of paths relative to project_dir.

    Returns:
        Dict of {relative_path: "sha256:<hex>"} for files that exist.
    """
    hashes = {}
    for relpath in source_files:
        abspath = os.path.join(project_dir, relpath)
        h = hash_source_file(abspath)
        if h is not None:
            hashes[relpath] = h
    return hashes


def sources_changed(old_hashes: Dict[str, str],
                    project_dir: str) -> bool:
    """Check if any source file has changed since the hashes were recorded.

    Args:
        old_hashes: Dict of {relative_path: "sha256:<hex>"} from manifest.
        project_dir: Root directory of the KiCad project.

    Returns:
        True if any file's current hash differs from old_hashes.
    """
    for relpath, old_hash in old_hashes.items():
        abspath = os.path.join(project_dir, relpath)
        current_hash = hash_source_file(abspath)
        if current_hash != old_hash:
            return True
    return False


# ---------------------------------------------------------------------------
# Run ID generation
# ---------------------------------------------------------------------------

def generate_run_id(analysis_dir: Optional[str] = None) -> str:
    """Generate a timestamped run ID in YYYY-MM-DD_HHMM format.

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

def create_run(analysis_dir: str,
               outputs_dir: str,
               source_hashes: Dict[str, str],
               scripts: Dict[str, str],
               run_id: Optional[str] = None) -> str:
    """Create a new timestamped run folder with outputs.

    Copies all files from outputs_dir into the new run folder.
    Copies forward any outputs from the previous current run that
    are not present in outputs_dir (partial run support).
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
        run_id = generate_run_id(analysis_dir)

    run_dir = os.path.join(analysis_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)

    # Copy forward outputs from previous current run. Per-file staleness
    # check: a carried-forward output is stale only if *its* source files
    # (by extension) appear in cur_hashes with a different hash than in
    # prev_hashes. Source files that only appear on one side (e.g.
    # re-running pcb leaves the schematic hash untouched) do not poison
    # unrelated outputs. (KH-281 follow-up: original guard was too blunt.)
    prev_run_id = manifest.get('current')
    prev_outputs = {}
    if prev_run_id and prev_run_id in manifest.get('runs', {}):
        prev_run_dir = os.path.join(analysis_dir, prev_run_id)
        prev_run_info = manifest['runs'][prev_run_id]
        prev_outputs = prev_run_info.get('outputs', {})
        prev_hashes = prev_run_info.get('source_hashes', {}) or {}
        cur_hashes = source_hashes or {}
        for analysis_type, filename in prev_outputs.items():
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
            if stale:
                continue
            prev_file = os.path.join(prev_run_dir, filename)
            new_file = os.path.join(run_dir, filename)
            if os.path.isfile(prev_file) and not os.path.isfile(new_file):
                shutil.copy2(prev_file, new_file)

    # Copy new outputs (overwrites any copied-forward files)
    new_outputs = {}
    for filename in os.listdir(outputs_dir):
        src = os.path.join(outputs_dir, filename)
        if os.path.isfile(src) and filename.endswith('.json'):
            shutil.copy2(src, os.path.join(run_dir, filename))
            # Map filename back to analysis type
            for atype, canonical in CANONICAL_OUTPUTS.items():
                if filename == canonical:
                    new_outputs[atype] = filename
                    break

    # Merge output maps: previous + new (new wins)
    merged_outputs = dict(prev_outputs)
    merged_outputs.update(new_outputs)

    # Update manifest
    manifest['current'] = run_id
    manifest.setdefault('runs', {})[run_id] = {
        'source_hashes': source_hashes,
        'outputs': merged_outputs,
        'scripts': scripts,
        'generated': datetime.now().astimezone().isoformat(timespec='seconds'),
        'pinned': False,
    }
    save_manifest(analysis_dir, manifest)

    return run_id


def overwrite_current(analysis_dir: str,
                      outputs_dir: str,
                      source_hashes: Optional[Dict[str, str]] = None) -> None:
    """Overwrite the current run folder with new outputs.

    Used when sources changed but analysis results didn't differ
    meaningfully. Updates source hashes and timestamp in the manifest
    without creating a new folder.

    Args:
        analysis_dir: Path to the analysis/ directory.
        outputs_dir: Temp directory containing the new output files.
        source_hashes: Updated source hashes (None = keep existing).
    """
    manifest = load_manifest(analysis_dir)
    current_id = manifest.get('current')
    if not current_id or current_id not in manifest.get('runs', {}):
        # No current run -- fall back to creating a new run
        create_run(analysis_dir, outputs_dir,
                   source_hashes=source_hashes or {},
                   scripts={})
        return

    current_dir = os.path.join(analysis_dir, current_id)
    os.makedirs(current_dir, exist_ok=True)

    # Overwrite files
    for filename in os.listdir(outputs_dir):
        src = os.path.join(outputs_dir, filename)
        if os.path.isfile(src) and filename.endswith('.json'):
            shutil.copy2(src, os.path.join(current_dir, filename))

    # Update manifest entry
    run_entry = manifest['runs'][current_id]
    if source_hashes is not None:
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
            if atype not in outputs:
                outputs[atype] = filename

    save_manifest(analysis_dir, manifest)


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


def unpin_run(analysis_dir: str, run_id: str) -> None:
    """Mark a run as unpinned."""
    manifest = load_manifest(analysis_dir)
    if run_id in manifest.get('runs', {}):
        manifest['runs'][run_id]['pinned'] = False
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
    current_id = manifest.get('current')
    if not current_id or current_id not in manifest.get('runs', {}):
        return None
    run_dir = os.path.join(analysis_dir, current_id)
    return run_dir, manifest['runs'][current_id]


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
        run_dir = os.path.join(analysis_dir, run_id)
        if os.path.isdir(run_dir):
            result.append((run_id, runs[run_id]))
        if limit > 0 and len(result) >= limit:
            break
    return result


# ---------------------------------------------------------------------------
# New-run decision logic
# ---------------------------------------------------------------------------

# Severity ordering for threshold comparison
_SEVERITY_ORDER = {'none': 0, 'minor': 1, 'major': 2, 'breaking': 3}


def should_create_new_run(analysis_dir: str,
                          new_outputs_dir: str,
                          diff_threshold: str = 'major') -> bool:
    """Decide whether new outputs warrant a new timestamped folder.

    Runs diff_analysis.py on each matching output type between the
    current run and the new outputs. If any diff severity meets or
    exceeds the threshold, returns True.

    Returns True if:
      - No current run exists (first run)
      - diff_analysis.py finds changes at or above the threshold
    Returns False if all diffs are below the threshold.

    Args:
        analysis_dir: Path to the analysis/ directory.
        new_outputs_dir: Directory containing the new output JSONs.
        diff_threshold: Minimum severity to trigger a new folder.
            One of: 'minor', 'major', 'breaking'.
    """
    current = get_current_run(analysis_dir)
    if current is None:
        return True

    current_dir, current_meta = current
    threshold_level = _SEVERITY_ORDER.get(diff_threshold, 2)

    # Try to import diff_analysis for programmatic comparison
    try:
        import diff_analysis
    except ImportError:
        # diff_analysis.py not on sys.path -- try adding our directory
        import sys
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        try:
            import diff_analysis
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
            with open(current_path) as f:
                base_data = json.load(f)
            with open(new_path) as f:
                head_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return True  # Can't compare -- treat as changed

        # Detect analyzer type and diff
        analyzer_type = base_data.get('analyzer_type', '')
        diff_func = {
            'schematic': getattr(diff_analysis, 'diff_schematic', None),
            'pcb': getattr(diff_analysis, 'diff_pcb', None),
            'emc': getattr(diff_analysis, 'diff_emc', None),
            'spice': getattr(diff_analysis, 'diff_spice', None),
        }.get(analyzer_type)

        if diff_func is None:
            continue  # Unknown type -- skip

        diff_result = diff_func(base_data, head_data, threshold=1.0)
        severity = diff_analysis.classify_severity(analyzer_type, diff_result)
        if _SEVERITY_ORDER.get(severity, 0) >= threshold_level:
            return True

    return False
