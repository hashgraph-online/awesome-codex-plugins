"""Output mechanics shared by the kicad-owned CLIs.

write_primary_run: the analysis-cache write path for the primary analyzers (schematic, pcb, EMC
and SPICE CLIs); write_derived_output: the current-run overwrite path for the derived analyzers (gerber,
thermal and cross-analysis CLIs). Each CLI keeps its own --output / --analysis-dir precedence
and calls these only on the --analysis-dir branch. Lives beside analysis_cache (which depends on
diff_engine), so it is not part of the stdlib-only kicad_core package.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from analysis_cache import (GITIGNORE_CONTENT, MANIFEST_FILENAME, CANONICAL_OUTPUTS, _empty_manifest,
                            create_run, get_current_run, hash_source_file, overwrite_current, prune_runs,
                            resolve_analysis_dir, save_manifest, should_create_new_run)


def write_primary_run(analysis_dir_arg: str, output_text: str, *, analyzer: str, source_path: str,
                      script_name: str, track_in_git: bool = False, extra_source_paths: tuple[str, ...] = (),
                      script_entry: str | None = None, diff_threshold: str = 'major', retention: int = 0,
                      record_project: bool = True) -> None:
    """Write one analyzer's canonical JSON into the analysis cache (new run or current overwrite).

    extra_source_paths hash into source_hashes after source_path; unreadable sources are skipped.
    script_entry overrides the manifest scripts[analyzer] string. record_project=False leaves a new
    manifest's project empty (the EMC and SPICE CLIs consume analyzer JSON, not a KiCad project).
    retention > 0 prunes the oldest unpinned runs after a new run is created; 0 keeps every run.
    """
    project_dir = str(Path(source_path).parent)
    analysis_dir = resolve_analysis_dir(analysis_dir_arg)

    # Find .kicad_pro for manifest
    pro_file = ""
    if record_project:
        try:
            for f in os.listdir(project_dir):
                if f.endswith(".kicad_pro"):
                    pro_file = f
                    break
        except OSError:
            pass

    # Ensure the target directory exists with manifest
    os.makedirs(analysis_dir, exist_ok=True)
    manifest_path = os.path.join(analysis_dir, MANIFEST_FILENAME)
    if not os.path.isfile(manifest_path):
        manifest = _empty_manifest()
        manifest['project'] = pro_file
        save_manifest(analysis_dir, manifest)
    # Respect track_in_git config — skip .gitignore if user wants git tracking
    gitignore_path = os.path.join(analysis_dir, '.gitignore')
    if not track_in_git and not os.path.isfile(gitignore_path):
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(GITIGNORE_CONTENT)

    source_hashes = {}
    for path in (source_path, *extra_source_paths):
        h = hash_source_file(os.path.abspath(path))
        if h:
            source_hashes[os.path.basename(path)] = h

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_file = os.path.join(tmp_dir, CANONICAL_OUTPUTS.get(analyzer, f"{analyzer}.json"))
        Path(out_file).write_text(output_text, encoding='utf-8')

        if should_create_new_run(analysis_dir, tmp_dir, diff_threshold):
            if script_entry is None:
                script_entry = f"{script_name} {os.path.basename(source_path)}"
            run_id = create_run(
                analysis_dir=analysis_dir,
                outputs_dir=tmp_dir,
                source_hashes=source_hashes,
                scripts={analyzer: script_entry},
            )
            if retention > 0:
                prune_runs(analysis_dir, retention)
            print(f"Analysis cached: {os.path.join(analysis_dir, run_id, os.path.basename(out_file))}", file=sys.stderr)
        else:
            overwrite_current(analysis_dir, tmp_dir, source_hashes=source_hashes)
            print(f"Analysis cache updated (current run)", file=sys.stderr)


def write_derived_output(analysis_dir_arg: str, output_text: str, *, analyzer: str) -> str:
    """Overwrite one derived analyzer's canonical JSON in the CURRENT run; return the path written.

    Derived analyzers (gerber, thermal, cross_analysis) carry no source hashes. When nothing is
    tracked yet, analysis_cache.overwrite_current creates a run (it calls create_run) and the
    run-folder path is returned; the trailing analysis-dir-root return is a defensive fallback only.
    """
    analysis_dir = resolve_analysis_dir(analysis_dir_arg)
    filename = CANONICAL_OUTPUTS.get(analyzer, f"{analyzer}.json")
    with tempfile.TemporaryDirectory() as tmp_dir:
        Path(os.path.join(tmp_dir, filename)).write_text(output_text, encoding='utf-8')
        overwrite_current(analysis_dir, tmp_dir, source_hashes=None)
    current = get_current_run(analysis_dir)
    if current:
        return os.path.join(current[0], filename)
    return os.path.join(analysis_dir, filename)
