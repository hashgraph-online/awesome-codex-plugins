#!/usr/bin/env python3
"""
SPICE simulation orchestrator for kicad-happy.

Reads analyzer JSON output (from analyze_schematic.py), identifies simulatable
subcircuits, generates ngspice testbenches, runs simulations, and produces a
structured report.

Usage:
    python3 simulate_subcircuits.py analysis.json
    python3 simulate_subcircuits.py --schematic analysis.json --output sim_report.json
    python3 simulate_subcircuits.py --analysis-dir analysis/
    python3 simulate_subcircuits.py analysis.json --workdir /tmp/spice_runs
    python3 simulate_subcircuits.py analysis.json --timeout 10
    python3 simulate_subcircuits.py analysis.json --types rc_filters,voltage_dividers

When --analysis-dir is given, the schematic is auto-resolved from the current
run (analysis/<run>/schematic.json), the output is written to spice.json in
the same run and registered in the manifest, and simulation artifacts (.cir,
.log) are written to analysis/<run>/spice_work/ instead of /tmp/.

Requires: ngspice (install: apt install ngspice / brew install ngspice)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

# Allow imports from same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spice_templates import TEMPLATE_REGISTRY, TOPLEVEL_REGISTRY, list_supported_types, SpiceTestbench
from spice_results import (
    EVALUATOR_REGISTRY,
    build_report,
    parse_output_file,
)

# Map detector key → singular subcircuit_type for output
# Most are just rstrip("s"), but some need special handling
_SINGULAR = {
    "decoupling_analysis": "decoupling",
    "power_regulators": "regulator_feedback",
    "rf_matching": "rf_matching",
    "bridge_circuits": "bridge_circuit",
    "inrush_analysis": "inrush",
    "bms_systems": "bms_balance",
    "rf_chains": "rf_chain",
    "snubber_circuits": "snubber_circuit",
}


def _singular_type(det_type):
    """Convert a detector key to its singular subcircuit_type name."""
    if det_type in _SINGULAR:
        return _SINGULAR[det_type]
    return det_type.rstrip("s")


def find_ngspice():
    """Locate the ngspice binary. Returns path or None.

    Legacy wrapper — prefer detect_simulator() for multi-simulator support.
    """
    from spice_simulator import NgspiceBackend
    backend = NgspiceBackend()
    return backend.find()


def run_ngspice(cir_file, timeout=5):
    """Run ngspice in batch mode on a .cir file.

    Legacy wrapper — prefer simulator_backend.run() for multi-simulator.
    """
    from spice_simulator import NgspiceBackend
    backend = NgspiceBackend()
    return backend.run(cir_file, timeout=timeout)


def simulate_subcircuits(analysis_json, workdir=None, timeout=5, types=None,
                         parasitics=None, simulator_backend=None,
                         monte_carlo_n=0, mc_distribution="gaussian",
                         mc_seed=42):
    """Run SPICE simulations for all simulatable subcircuits in the analysis.

    Args:
        analysis_json: Parsed JSON dict from analyze_schematic.py
        workdir: Directory for .cir and output files (default: temp dir)
        timeout: Seconds per simulation (default: 5)
        types: List of detector types to simulate, or None for all supported
        parasitics: PCB parasitic data from extract_parasitics.py
        simulator_backend: SimulatorBackend instance (auto-detected if None)
        monte_carlo_n: Number of Monte Carlo tolerance trials per subcircuit (0=disabled)
        mc_distribution: "gaussian" (3sigma=tolerance) or "uniform"
        mc_seed: Random seed for reproducible Monte Carlo runs

    Returns:
        Report dict with simulation results
    """
    # Detect pre-v1.3 format
    if 'signal_analysis' in analysis_json and 'findings' not in analysis_json:
        import sys as _sys
        print('Warning: this JSON uses the pre-v1.3 signal_analysis wrapper '
              'format. Re-run analyze_schematic.py to produce the current '
              'findings[] format.', file=_sys.stderr)
        return build_report([])

    # Build detector-keyed lookup from flat findings[]
    # Map detector names to legacy keys used by TEMPLATE_REGISTRY
    _DET_KEY_OVERRIDES = {
        "detect_decoupling": "decoupling_analysis",
        "detect_integrated_ldos": "power_regulators",
    }
    signal = {}
    for f in analysis_json.get("findings", []):
        det = f.get("detector", "")
        if not det:
            continue
        key = _DET_KEY_OVERRIDES.get(det)
        if not key:
            key = det[len("detect_"):] if det.startswith("detect_") else det
        signal.setdefault(key, []).append(f)
    if not signal:
        return build_report([])

    # Synthesize snubber_circuits from transistor_circuits with snubber_data
    tc = signal.get("transistor_circuits", [])
    if isinstance(tc, list):
        snubber_circuits = [t for t in tc if isinstance(t, dict) and t.get("snubber_data")]
        if snubber_circuits:
            signal["snubber_circuits"] = snubber_circuits

    # Filter to requested types
    sim_types = types if types else list_supported_types()

    # Set up working directory
    cleanup_workdir = False
    if workdir is None:
        workdir = tempfile.mkdtemp(prefix="spice_sim_")
        cleanup_workdir = True
    else:
        os.makedirs(workdir, exist_ok=True)

    results = []
    total_time = 0

    # Monte Carlo setup (lazy import only when needed)
    mc_rng = None
    if monte_carlo_n > 0:
        import random as _random
        mc_rng = _random.Random(mc_seed)

    def _run_single_sim(det_run, det_type, generator, evaluator,
                        cir_file, out_file, log_file):
        """Run one simulation: generate -> run -> parse -> evaluate.

        Returns (result_dict, elapsed) or (None, 0) on failure/skip.
        """
        nonlocal total_time
        out_file_spice = out_file.replace("\\", "/")

        try:
            cir_content = generator(det_run, out_file_spice,
                                    context=analysis_json,
                                    parasitics=parasitics)
        except (KeyError, TypeError, ValueError) as e:
            return {"_generator_fail": True,
                    "note": f"testbench generation failed: {type(e).__name__}: {e}"}, 0

        if cir_content is None:
            return None, 0

        if isinstance(cir_content, SpiceTestbench):
            cir_content = cir_content.render(simulator_backend, out_file_spice)

        with open(cir_file, "w") as f:
            f.write(cir_content)

        t0 = time.monotonic()
        if simulator_backend:
            success, stdout, stderr = simulator_backend.run(cir_file, timeout=timeout)
        else:
            success, stdout, stderr = run_ngspice(cir_file, timeout=timeout)
        elapsed = time.monotonic() - t0
        total_time += elapsed

        with open(log_file, "w") as f:
            f.write(f"=== stdout ===\n{stdout}\n=== stderr ===\n{stderr}\n")

        if not success:
            return None, elapsed

        if simulator_backend and hasattr(simulator_backend, 'parse_results'):
            sim_data = simulator_backend.parse_results(out_file, stdout, stderr)
        else:
            sim_data = parse_output_file(out_file)

        if evaluator:
            det_run["_context"] = analysis_json
            result = evaluator(det_run, sim_data)
            det_run.pop("_context", None)
        else:
            result = {
                "subcircuit_type": _singular_type(det_type),
                "components": _get_components(det_run),
                "status": "pass",
                "simulated": sim_data,
            }

        return result, elapsed

    def _run_detection_batch(det_type, detections, generator, evaluator):
        """Simulate a batch of detections — shared by signal_analysis and top-level loops."""
        for i, det in enumerate(detections):
            label = _make_label(det_type, det, i)
            cir_file = os.path.join(workdir, f"{label}.cir")
            out_file = os.path.join(workdir, f"{label}.out")
            log_file = os.path.join(workdir, f"{label}.log")

            # Nominal simulation
            result, elapsed = _run_single_sim(
                det, det_type, generator, evaluator,
                cir_file, out_file, log_file)

            if result is None:
                if elapsed > 0:
                    results.append({
                        "subcircuit_type": _singular_type(det_type),
                        "components": _get_components(det),
                        "status": "skip",
                        "note": "Simulation failed",
                        "cir_file": cir_file,
                        "log_file": log_file,
                        "elapsed_s": round(elapsed, 3),
                    })
                continue

            # Generator-time failure — still emit a skip record
            if isinstance(result, dict) and result.get("_generator_fail"):
                results.append({
                    "subcircuit_type": _singular_type(det_type),
                    "components": _get_components(det),
                    "status": "skip",
                    "note": result.get("note", "testbench generation failed"),
                    "elapsed_s": 0,
                })
                continue

            result["cir_file"] = cir_file
            result["log_file"] = log_file
            result["elapsed_s"] = round(elapsed, 3)

            # Monte Carlo tolerance analysis
            if monte_carlo_n > 0 and result.get("status") != "skip":
                from spice_tolerance import (
                    find_toleranceable_components, sample_detection,
                    aggregate_mc_results,
                )
                components = find_toleranceable_components(det)
                if components:
                    mc_results_list = []
                    sampled_values_list = []
                    mc_cir = os.path.join(workdir, f"{label}_mc.cir")
                    mc_out = os.path.join(workdir, f"{label}_mc.out")
                    mc_log = os.path.join(workdir, f"{label}_mc.log")

                    for _trial in range(monte_carlo_n):
                        sampled_det = sample_detection(
                            det, components, mc_rng, mc_distribution,
                            det_type=det_type)
                        mc_result, _mc_elapsed = _run_single_sim(
                            sampled_det, det_type, generator, evaluator,
                            mc_cir, mc_out, mc_log)
                        if mc_result is not None:
                            mc_results_list.append(mc_result)
                            # Store sampled values for sensitivity analysis
                            sv = {}
                            for idx, (kp, _ct, _nom, _tol) in enumerate(components):
                                try:
                                    from spice_tolerance import _get_nested
                                    sv[idx] = _get_nested(sampled_det, kp)
                                except (KeyError, TypeError, IndexError):
                                    pass
                            sampled_values_list.append(sv)

                    # Store original det for component ref lookup
                    result["_det"] = det
                    result["tolerance_analysis"] = aggregate_mc_results(
                        result, mc_results_list, components,
                        sampled_values_list,
                        _singular_type(det_type),
                        monte_carlo_n, mc_distribution, mc_seed,
                        det_type=det_type,
                    )
                    result.pop("_det", None)

                    # Clean up MC temp files
                    for f in (mc_cir, mc_out, mc_log):
                        if os.path.exists(f):
                            os.remove(f)

            results.append(result)

    # Process signal_analysis detections
    for det_type in sim_types:
        if det_type not in signal or det_type not in TEMPLATE_REGISTRY:
            continue
        detections = signal[det_type]
        if not isinstance(detections, list):
            continue
        _run_detection_batch(det_type, detections,
                            TEMPLATE_REGISTRY[det_type],
                            EVALUATOR_REGISTRY.get(det_type))

    # Process top-level types (not under signal_analysis)
    for tl_type, (list_key, generator) in TOPLEVEL_REGISTRY.items():
        if types and tl_type not in types:
            continue
        tl_data = analysis_json.get(tl_type, {})
        if not tl_data:
            continue
        detections = tl_data.get(list_key, [])
        if not isinstance(detections, list):
            continue
        _run_detection_batch(tl_type, detections,
                            generator, EVALUATOR_REGISTRY.get(tl_type))

    report = build_report(results)
    report["workdir"] = workdir
    report["total_elapsed_s"] = round(total_time, 3)
    report["simulator"] = find_ngspice() or None
    report["ngspice"] = report["simulator"]  # backward compat alias

    return report


def _make_label(det_type, det, index):
    """Generate a filesystem-safe label for a subcircuit simulation."""
    parts = []
    # Singular form of detector type
    parts.append(_singular_type(det_type).replace("_", "-"))
    # Component references
    comps = _get_components(det)
    if comps:
        parts.append("_".join(comps))
    else:
        parts.append(f"idx{index}")
    label = "_".join(parts)
    # Sanitize for filesystem
    return "".join(c if c.isalnum() or c in "_-" else "_" for c in label)


def _get_components(det):
    """Extract component reference list from any detector dict."""
    refs = []
    # Try common field patterns from different detector types
    for key in ("resistor", "r_top", "inductor", "shunt"):
        if key in det and isinstance(det[key], dict) and "ref" in det[key]:
            refs.append(det[key]["ref"])
    for key in ("capacitor", "r_bottom"):
        if key in det and isinstance(det[key], dict) and "ref" in det[key]:
            refs.append(det[key]["ref"])
    if "reference" in det:
        refs.append(det["reference"])
    # Feedback/input resistors for opamps
    for key in ("feedback_resistor", "input_resistor"):
        if key in det and isinstance(det[key], dict) and "ref" in det[key]:
            refs.append(det[key]["ref"])
    # Decoupling capacitor list
    if "capacitors" in det and isinstance(det["capacitors"], list):
        for c in det["capacitors"][:5]:  # Limit to 5 for label length
            if isinstance(c, dict) and "ref" in c:
                refs.append(c["ref"])
    # BMS: IC ref + balance resistor refs
    if "bms_reference" in det:
        refs.append(det["bms_reference"])
        br_list = det.get("balance_resistors", [])
        if not isinstance(br_list, list):
            br_list = []  # Old format was int count, not list
        for br in br_list[:3]:
            if isinstance(br, dict) and "reference" in br:
                refs.append(br["reference"])
    # Snubber components
    sd = det.get("snubber_data")
    if isinstance(sd, dict):
        if sd.get("resistor_ref"):
            refs.append(sd["resistor_ref"])
        if sd.get("capacitor_ref"):
            refs.append(sd["capacitor_ref"])
    # RF chain components
    for cat in ("transceivers", "amplifiers", "filters", "switches", "mixers"):
        for c in det.get(cat, [])[:2]:
            if isinstance(c, dict) and "reference" in c:
                refs.append(c["reference"])
    # Power regulators: IC ref + feedback divider resistors
    if "ref" in det and "feedback_divider" in det:
        refs.append(det["ref"])
        fd = det["feedback_divider"]
        if isinstance(fd, dict):
            for k in ("r_top", "r_bottom"):
                v = fd.get(k)
                if isinstance(v, dict) and "ref" in v:
                    refs.append(v["ref"])
    # RF matching components
    if "antenna" in det and "components" in det:
        for c in det.get("components", [])[:5]:
            if isinstance(c, dict) and "ref" in c:
                refs.append(c["ref"])
    return refs


def main():
    parser = argparse.ArgumentParser(
        description="Run SPICE simulations for detected subcircuits"
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to analyzer JSON output (from analyze_schematic.py --output)",
    )
    parser.add_argument(
        "--schematic", "-s",
        help="Path to schematic analyzer JSON (alias for positional input)",
    )
    parser.add_argument(
        "--analysis-dir",
        help="Analysis cache directory. When set, auto-resolves schematic "
             "from current run and writes spice.json into the run folder.",
    )
    parser.add_argument(
        "--output", "-o",
        help="Path to write simulation report JSON (default: stdout)",
    )
    parser.add_argument(
        "--workdir", "-w",
        help="Directory for simulation files (default: <run>/spice_work/ "
             "when --analysis-dir is set, else a temp dir)",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=5,
        help="Timeout per simulation in seconds (default: 5)",
    )
    parser.add_argument(
        "--types",
        help="Comma-separated list of detector types to simulate "
             f"(default: all supported: {', '.join(list_supported_types())})",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Omit file paths from output (for clean reports)",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="Human-readable text output instead of JSON",
    )
    parser.add_argument(
        "--parasitics",
        help="Path to parasitics JSON (from extract_parasitics.py) for "
             "PCB-aware simulation. When provided, testbenches include trace "
             "resistance and via inductance.",
    )
    parser.add_argument(
        "--simulator",
        choices=["auto", "ngspice", "ltspice", "xyce"],
        default="auto",
        help="SPICE simulator to use (default: auto-detect)",
    )
    parser.add_argument(
        "--monte-carlo",
        type=int,
        default=0,
        metavar="N",
        help="Run N Monte Carlo tolerance simulations per subcircuit "
             "(e.g., --monte-carlo 100)",
    )
    parser.add_argument(
        "--mc-distribution",
        choices=["gaussian", "uniform"],
        default="gaussian",
        help="Distribution for tolerance sampling (default: gaussian, "
             "3-sigma = tolerance band)",
    )
    parser.add_argument(
        "--mc-seed",
        type=int,
        default=42,
        help="Random seed for reproducible Monte Carlo runs (default: 42)",
    )

    args = parser.parse_args()

    # Resolve input: --schematic, positional, or --analysis-dir auto-resolve
    input_path = args.schematic or args.input
    workdir = args.workdir
    if args.analysis_dir:
        # analysis_cache lives in skills/kicad/scripts/
        sys.path.insert(0, os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', '..', 'kicad', 'scripts'))
        from analysis_cache import load_manifest, MANIFEST_FILENAME
        analysis_dir = os.path.abspath(args.analysis_dir)
        manifest = load_manifest(analysis_dir)
        current = manifest.get('current') if manifest else None
        if not current:
            print(f"Error: no 'current' run in {analysis_dir}/{MANIFEST_FILENAME}. "
                  f"Run analyze_schematic.py --analysis-dir first.",
                  file=sys.stderr)
            sys.exit(1)
        run_dir = os.path.join(analysis_dir, current)
        if not input_path:
            input_path = os.path.join(run_dir, 'schematic.json')
        if not workdir:
            workdir = os.path.join(run_dir, 'spice_work')

    if not input_path:
        parser.error("one of --schematic / positional input / --analysis-dir is required")

    # Detect simulator
    from spice_simulator import detect_simulator
    simulator_backend = detect_simulator(args.simulator)
    if not simulator_backend:
        print("Error: no SPICE simulator found. Install one of:", file=sys.stderr)
        print("  ngspice: apt install ngspice / brew install ngspice", file=sys.stderr)
        print("  LTspice: download from analog.com/ltspice", file=sys.stderr)
        print("  Xyce:    download from xyce.sandia.gov", file=sys.stderr)
        print("  Or set NGSPICE_PATH env var to the ngspice binary path.", file=sys.stderr)
        sys.exit(1)

    # Read analysis JSON
    try:
        with open(input_path, "r") as f:
            analysis = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error reading {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse types filter
    types = None
    if args.types:
        types = [t.strip() for t in args.types.split(",")]
        supported = set(list_supported_types())
        unknown = set(types) - supported
        if unknown:
            print(f"Warning: unknown types ignored: {', '.join(unknown)}",
                  file=sys.stderr)
            types = [t for t in types if t in supported]

    # Load parasitics if provided
    parasitics_data = None
    if args.parasitics:
        try:
            with open(args.parasitics, "r") as f:
                parasitics_data = json.load(f)
            n_nets = len(parasitics_data.get("nets", {}))
            print(f"Loaded parasitics for {n_nets} nets from {args.parasitics}",
                  file=sys.stderr)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: could not load parasitics: {e}", file=sys.stderr)

    # Run simulations
    report = simulate_subcircuits(
        analysis,
        workdir=workdir,
        timeout=args.timeout,
        types=types,
        parasitics=parasitics_data,
        simulator_backend=simulator_backend,
        monte_carlo_n=args.monte_carlo,
        mc_distribution=args.mc_distribution,
        mc_seed=args.mc_seed,
    )

    # Clean up file paths if compact mode
    if args.compact:
        for r in report.get("simulation_results", []):
            r.pop("cir_file", None)
            r.pop("log_file", None)
        report.pop("workdir", None)

    # Analysis cache integration — write spice.json into the current run folder
    # and update the manifest so downstream tools pick it up.
    if args.analysis_dir:
        import tempfile
        from analysis_cache import (hash_source_file, should_create_new_run,
                                    create_run, overwrite_current,
                                    CANONICAL_OUTPUTS, MANIFEST_FILENAME,
                                    save_manifest, _empty_manifest,
                                    GITIGNORE_CONTENT)
        os.makedirs(analysis_dir, exist_ok=True)
        manifest_path = os.path.join(analysis_dir, MANIFEST_FILENAME)
        if not os.path.isfile(manifest_path):
            save_manifest(analysis_dir, _empty_manifest())
        gitignore_path = os.path.join(analysis_dir, '.gitignore')
        if not os.path.isfile(gitignore_path):
            with open(gitignore_path, 'w') as f:
                f.write(GITIGNORE_CONTENT)

        source_hashes = {}
        h = hash_source_file(os.path.abspath(input_path))
        if h:
            source_hashes[os.path.basename(input_path)] = h

        with tempfile.TemporaryDirectory() as tmpdir:
            canonical = CANONICAL_OUTPUTS.get('spice', 'spice.json')
            tmp_out = os.path.join(tmpdir, canonical)
            with open(tmp_out, 'w') as f:
                json.dump(report, f, indent=2)

            if should_create_new_run(analysis_dir, tmpdir):
                run_id = create_run(analysis_dir, tmpdir,
                                    source_hashes=source_hashes,
                                    scripts={'spice': 'simulate_subcircuits.py'})
                print(f'SPICE simulation cached: new run {run_id}',
                      file=sys.stderr)
            else:
                overwrite_current(analysis_dir, tmpdir,
                                  source_hashes=source_hashes)
                print('SPICE simulation cached: updated current run',
                      file=sys.stderr)

    # Output
    output_json = json.dumps(report, indent=2)
    if args.text:
        # KH-345: --text parity with the other analyzers. Early-exit
        # reports (no simulatable data) omit total_elapsed_s — tolerate it.
        s = report.get("summary", {})
        _elapsed = report.get("total_elapsed_s")
        _suffix = (f" ({_elapsed:.1f}s)"
                   if isinstance(_elapsed, (int, float)) else "")
        print(f"SPICE simulation: {s.get('total', 0)} subcircuits — "
              f"{s.get('pass', 0)} pass, {s.get('warn', 0)} warn, "
              f"{s.get('fail', 0)} fail, {s.get('skip', 0)} skip{_suffix}")
        sys.path.insert(0, os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', '..', 'kicad', 'scripts'))
        from output_filters import format_text
        print(format_text(report.get("findings", []), "designer"))
        if args.output:
            with open(args.output, "w") as f:
                f.write(output_json)
    elif args.output:
        with open(args.output, "w") as f:
            f.write(output_json)
        # Print summary to stderr
        s = report["summary"]
        print(
            f"Simulation complete: {s['total']} subcircuits — "
            f"{s['pass']} pass, {s['warn']} warn, {s['fail']} fail, "
            f"{s['skip']} skip ({report['total_elapsed_s']:.1f}s)",
            file=sys.stderr,
        )
    elif not args.analysis_dir:
        print(output_json)


if __name__ == "__main__":
    main()
