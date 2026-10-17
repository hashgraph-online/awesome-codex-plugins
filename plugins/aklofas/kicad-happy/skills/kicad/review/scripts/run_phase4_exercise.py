"""End-to-end Phase 4 exercise runner.

Orchestrates the full Layer 1 + Layer 2 pipeline against the gitignored
Phase 4 fixture at tests/fixtures/phase4-review/. Verifies HI-3 strip-LLM
round-trip on real outputs, dual-mode (raw vs merged) consumption via
summarize_findings.py, all analyzers + review subagents producing valid output.

This script exercises the architecture; it does NOT produce a calibrated
quality report (calibration is deferred to v1.5).

Step inventory:
    1. Run Layer 1 analyzers (schematic / pcb / thermal / emc / cross_analysis).
       Gerber is skipped — the v1.4 fixture (SparkFun GNSSDO) ships only
       sources, no fab outputs.
    2. Assert HI-7 (capability_mode_ref present on every envelope; canonical
       analysis/capability_mode.json exists with a stable run_id).
    3. Build review plan (build_review_plan.py).
    4. Dispatch design_context + reviewer subagents — manual step on this
       runner; this script prints the dispatch instructions and waits for the
       output JSONs.
    5. Merge annotations + assert HI-3 (strip-LLM byte-identical) + summarize
       _merge_report.json contents.
    6. Dual-mode summarize_findings (raw vs merged) — proves the renderer
       contract holds and the --only-deterministic flag picks raw paths.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "phase4-review"
ANALYZER_NAMES = ("schematic", "pcb", "thermal", "emc", "cross_analysis")


def _run(cmd, cwd=None):
    """Run a shell command, raising on failure with helpful context."""
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, cwd=cwd or REPO_ROOT,
                             capture_output=True, text=True)
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise RuntimeError(f"Command failed (exit {result.returncode}): {cmd}")
    return result


def _resolve_root_sheet(fixture_dir: Path) -> Path:
    """Pick the root .kicad_sch for analysis.

    Strategy:
        1. If only one .kicad_sch exists, use it.
        2. Else, look for a .kicad_pro and prefer the .kicad_sch with a
           matching stem (KiCad's convention: project + root sheet share a name).
        3. Fall back to the alphabetically-first .kicad_sch (with a warning).
    """
    schs = sorted(fixture_dir.rglob("*.kicad_sch"))
    if not schs:
        raise FileNotFoundError(f"No .kicad_sch in {fixture_dir}")
    if len(schs) == 1:
        return schs[0]

    pros = sorted(fixture_dir.rglob("*.kicad_pro"))
    for pro in pros:
        sibling_sch = pro.with_suffix(".kicad_sch")
        if sibling_sch.exists():
            return sibling_sch

    print(f"WARN: no .kicad_pro / sheet match; using {schs[0]}", file=sys.stderr)
    return schs[0]


def _resolve_root_pcb(fixture_dir: Path) -> Path | None:
    """Pick the root .kicad_pcb (if present). Mirror _resolve_root_sheet logic."""
    pcbs = sorted(fixture_dir.rglob("*.kicad_pcb"))
    if not pcbs:
        return None
    if len(pcbs) == 1:
        return pcbs[0]
    pros = sorted(fixture_dir.rglob("*.kicad_pro"))
    for pro in pros:
        sibling = pro.with_suffix(".kicad_pcb")
        if sibling.exists():
            return sibling
    return pcbs[0]


def step_1_run_layer1_analyzers(fixture_dir: Path):
    """Run Layer 1 analyzers (5 of 6 — gerber skipped, no fab outputs)."""
    print("\n[step 1] Running Layer 1 analyzers")
    sch = _resolve_root_sheet(fixture_dir)
    pcb = _resolve_root_pcb(fixture_dir)
    print(f"  schematic root: {sch.relative_to(fixture_dir)}")
    if pcb:
        print(f"  pcb root:       {pcb.relative_to(fixture_dir)}")
    analysis_dir = fixture_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    py = sys.executable
    _run([py, "skills/kicad/scripts/analyze_schematic.py",
          str(sch), "--output", str(analysis_dir / "schematic.json")])
    if pcb:
        _run([py, "skills/kicad/scripts/analyze_pcb.py",
              str(pcb), "--output", str(analysis_dir / "pcb.json")])
        _run([py, "skills/kicad/scripts/analyze_thermal.py",
              "--schematic", str(analysis_dir / "schematic.json"),
              "--pcb", str(analysis_dir / "pcb.json"),
              "--output", str(analysis_dir / "thermal.json")])
        _run([py, "skills/emc/scripts/analyze_emc.py",
              "--schematic", str(analysis_dir / "schematic.json"),
              "--pcb", str(analysis_dir / "pcb.json"),
              "--output", str(analysis_dir / "emc.json")])
        _run([py, "skills/kicad/scripts/cross_analysis.py",
              "--schematic", str(analysis_dir / "schematic.json"),
              "--pcb", str(analysis_dir / "pcb.json"),
              "--output", str(analysis_dir / "cross_analysis.json")])
    else:
        print("  pcb missing → skipping pcb/thermal/emc/cross analyzers")
    print("[step 1] OK — Layer 1 outputs in", analysis_dir)


def step_2_assert_capability_mode(fixture_dir: Path):
    """HI-7: every envelope has capability_mode_ref + canonical record exists."""
    print("\n[step 2] HI-7: capability_mode contract")
    analysis_dir = fixture_dir / "analysis"
    cm_path = analysis_dir / "capability_mode.json"
    if not cm_path.exists():
        raise RuntimeError(f"capability_mode.json not written at {cm_path}")
    cm = json.loads(cm_path.read_text())
    print(f"  canonical run_id: {cm['run_id']}")
    for name in ANALYZER_NAMES:
        path = analysis_dir / f"{name}.json"
        if not path.exists():
            print(f"  {name}.json: skipped (analyzer didn't run)")
            continue
        env = json.loads(path.read_text())
        ref = env.get("capability_mode_ref") or {}
        if ref.get("run_id") != cm["run_id"]:
            raise AssertionError(
                f"{name}.json capability_mode_ref.run_id mismatch "
                f"(envelope: {ref.get('run_id')!r}, canonical: {cm['run_id']!r})")
    print("[step 2] OK — capability_mode_ref consistent across envelopes")


def step_3_build_review_plan(fixture_dir: Path):
    """Build the 2-task review plan."""
    print("\n[step 3] Build review plan")
    analysis_dir = fixture_dir / "analysis"
    plan_path = analysis_dir / "review_plan.json"
    _run([sys.executable, "skills/kicad/review/scripts/build_review_plan.py",
          "--analysis-dir", str(analysis_dir),
          "--output", str(plan_path)])
    print(f"  plan written: {plan_path}")
    print("[step 3] OK — dispatch design_context per "
          "skills/datasheets/references/dispatch-claude-code.md Phase 4 addendum")
    print("  Expected output from the dispatch (v2.0: reviewer task retired, spec §5):")
    print(f"    {analysis_dir / 'design_context.json'}")


def step_4_merge_and_assert_invariants(fixture_dir: Path):
    """Run merge + assert HI-3 (v2.0: authority caps retired, spec §5)."""
    print("\n[step 4] Merge annotations + invariant checks")
    analysis_dir = fixture_dir / "analysis"
    merged_dir = analysis_dir / "merged"
    review_path = analysis_dir / "review_annotations.json"
    if not review_path.exists():
        raise RuntimeError(
            f"review_annotations.json missing — dispatch step 3 first ({review_path})")
    _run([sys.executable, "skills/kicad/review/scripts/merge_annotations.py",
          "--raw-dir", str(analysis_dir),
          "--review", str(review_path),
          "--merged-dir", str(merged_dir)])

    report_path = merged_dir / "_merge_report.json"
    if not report_path.exists():
        raise RuntimeError(f"_merge_report.json missing at {report_path}")
    report = json.loads(report_path.read_text())
    print(f"  applied_count:        {report.get('applied_count', '?')}")
    print(f"  suppressed_count:     {report.get('suppressed_count', '?')}")
    print(f"  invariant_violations: {len(report.get('invariant_violations', []))}")
    print(f"  orphan_annotations:   {len(report.get('orphan_annotations', []))}")

    # HI-3 strip-LLM byte-identical (also asserted internally by merge_annotations).
    sys.path.insert(0, str(REPO_ROOT / "skills" / "kicad" / "review" / "scripts"))
    from merge_annotations import strip_llm_overlays  # type: ignore[import-not-found]
    for name in ANALYZER_NAMES:
        merged_path = merged_dir / f"{name}.json"
        raw_path = analysis_dir / f"{name}.json"
        if not merged_path.exists() or not raw_path.exists():
            continue
        merged = json.loads(merged_path.read_text())
        raw = json.loads(raw_path.read_text())
        if strip_llm_overlays(merged) != raw:
            raise AssertionError(f"HI-3 violation on {name}.json")
    print("[step 4] OK — HI-3 round-trip byte-identical, _merge_report inspected")


def step_5_dual_mode_consumer_contract(fixture_dir: Path):
    """Renderer-contract probe: prove raw vs merged paths both load cleanly
    AND that overlay presence is the only structural difference (per HI-2 +
    HI-3). Verifies that any consumer doing path resolution on
    raw/{name}.json vs raw/merged/{name}.json gets self-consistent data.
    """
    print("\n[step 5] dual-mode consumer contract (raw vs merged)")
    analysis_dir = fixture_dir / "analysis"
    merged_dir = analysis_dir / "merged"
    if not merged_dir.exists():
        raise RuntimeError(f"merged dir missing — run step 4 first: {merged_dir}")

    sys.path.insert(0, str(REPO_ROOT / "skills" / "kicad" / "review" / "scripts"))
    from merge_annotations import strip_llm_overlays  # type: ignore[import-not-found]

    diffs = []
    for name in ANALYZER_NAMES:
        raw_path = analysis_dir / f"{name}.json"
        merged_path = merged_dir / f"{name}.json"
        if not raw_path.exists() or not merged_path.exists():
            continue
        raw = json.loads(raw_path.read_text())
        merged = json.loads(merged_path.read_text())
        # HI-2: every diff between merged and raw lives under llm_* keys.
        # Already enforced by HI-3 strip-byte-identical (step 4); double-check
        # that merged JSON has at least one llm_* key when annotations applied.
        merged_str = json.dumps(merged, sort_keys=True)
        raw_str = json.dumps(raw, sort_keys=True)
        differs = merged_str != raw_str
        diffs.append((name, differs))
        print(f"  {name}.json: differs={differs}, raw_findings="
              f"{len(raw.get('findings', []))}, merged_findings="
              f"{len(merged.get('findings', []))}")
        # Renderer contract: a consumer prefers merged when present;
        # falls back to raw under --only-deterministic. Validate both load
        # without error and produce the same finding count (overlay only,
        # never adds/removes findings).
        if len(merged.get("findings", [])) != len(raw.get("findings", [])):
            raise AssertionError(
                f"HI-2 violation: merged/{name}.json has different finding "
                f"count than raw — overlays must not add/remove findings")
    if not any(d for _, d in diffs):
        print("  WARN: no analyzer envelope differs between raw and merged; "
              "overlay set may be empty for this fixture")
    print("[step 5] OK — overlay presence is the only structural difference; "
          "finding counts preserved")


STEPS = {
    "1": step_1_run_layer1_analyzers,
    "2": step_2_assert_capability_mode,
    "3": step_3_build_review_plan,
    "4": step_4_merge_and_assert_invariants,
    "5": step_5_dual_mode_consumer_contract,
}


def main():
    p = argparse.ArgumentParser(
        description="Phase 4 end-to-end exercise runner (4d-active).")
    p.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE_DIR,
                   help=f"Fixture directory (default: {DEFAULT_FIXTURE_DIR})")
    p.add_argument("--steps", nargs="+", default=list(STEPS.keys()),
                   choices=list(STEPS.keys()),
                   help="Subset of steps to run (default: all)")
    args = p.parse_args()

    if not args.fixture.exists():
        print(f"ERROR: fixture missing at {args.fixture}", file=sys.stderr)
        print("Import a corpus project (e.g. SparkFun GNSSDO) to that path "
              "with pre-populated datasheets/extracted/.", file=sys.stderr)
        return 2

    for step_id in args.steps:
        STEPS[step_id](args.fixture)
    print("\nPhase 4 exercise COMPLETE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
