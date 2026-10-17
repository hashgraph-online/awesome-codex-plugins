"""Command-line interface for unslop.

Reads a markdown / text file (or stdin), strips AI-isms while preserving code,
URLs, paths, and headings, and writes the result (or a diff, or a JSON report).

Examples:
  humanize path/to/README.md                  # LLM mode, in-place, balanced
  humanize --deterministic --mode full README.md
  humanize --stdin --deterministic < in.md > out.md
  humanize --diff notes.md                    # show unified diff, don't write
  humanize --dry-run --json *.md              # batch, no writes, JSON report
  humanize --report replacements.json --deterministic notes.md

Exit codes:
  0  success (or no changes needed in --dry-run)
  1  usage error, file not found, sensitive path refused
  2  validation failure (structure changed, or LLM retry ceiling hit)
  3  partial failure in batch mode (some files succeeded, some failed)
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path

USAGE_EPILOG = """\
Modes:
  --deterministic   Fast regex pass, no API call, no subprocess.
  (default)         LLM mode: Anthropic SDK when ANTHROPIC_API_KEY is set,
                    falls back to `claude --print` CLI on PATH.

Intensity (--mode):
  subtle    Trim stock vocab only. Keep structure roughly intact.
  balanced  Default. Strip sycophancy, hedging, transitions, stock vocab,
            authority tropes, signposting, em-dash pileups.
  full      Strong rewrite. Everything balanced does, plus filler phrases
            and negative-parallelism knockouts.
  anti-detector
            Full rewrite plus detector-oriented structural nudges.

Input:
  <file>...         One or more paths. Glob expansion is done by your shell.
  --stdin           Read from stdin, write humanized text to stdout.
                    Forces --no-backup, --deterministic friendly.
  -                 Alias for --stdin when used as the single filepath.

Output:
  --output PATH     Write to PATH instead of overwriting input. Single-file only.
  --diff            Print unified diff to stdout. Implies --dry-run.
  --dry-run         Don't write anything; just validate + report.
  --no-backup       Skip the <stem>.original.md backup.
  --json            Emit machine-readable JSON per file.
  --report PATH     Write full replacement audit trail to PATH as JSON.
  --report-stylometric-gaps
                    Print measured gaps against stylometric baseline bands.
  --quiet / -q      Suppress progress lines on stdout.
"""


def _get_version() -> str:
    try:
        from . import __version__
        return __version__
    except Exception:
        return "0.0.0"


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="unslop",
        description=(
            "Humanize markdown / text files. Strips AI-isms (sycophancy, stock "
            "vocab, hedging, em-dash pileups, authority tropes, signposting) "
            "while preserving fenced code, inline code, URLs, paths, and "
            "headings byte-for-byte."
        ),
        epilog=USAGE_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"unslop {_get_version()}"
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="One or more input files. Use '-' or --stdin to read from stdin.",
    )
    parser.add_argument(
        "--deterministic",
        action="store_true",
        help="Use the deterministic regex pass only (no API, no subprocess).",
    )
    parser.add_argument(
        "--mode",
        "-m",
        choices=("subtle", "balanced", "full", "anti-detector"),
        default="balanced",
        help="Intensity level. Default: balanced.",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read from stdin, write to stdout. Implies --no-backup.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Write humanized output to this path instead of overwriting input.",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Print unified diff and exit without writing. Implies --dry-run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and report; do not write to disk.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip the <stem>.original.md backup. Use with care.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report per file instead of human-readable text.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help=(
            "Write the full replacement audit trail to this JSON file. "
            "Works only with --deterministic; LLM mode cannot produce a "
            "byte-level audit trail."
        ),
    )
    parser.add_argument(
        "--report-stylometric-gaps",
        action="store_true",
        help=(
            "Print stylometric target gaps against "
            "benchmarks/results/stylometric_baseline.json when present."
        ),
    )
    parser.add_argument(
        "--structural",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Phase 1 structural pass: split overlong sentences at safe "
            "boundaries and collapse parallel bullet-soup. Default: on for "
            "balanced/full, off for subtle. Use --no-structural to disable."
        ),
    )
    parser.add_argument(
        "--soul",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Phase 5 soul pass: contraction lift (do not → don't, it is → it's "
            "where safe). Default: on for balanced/full, off for subtle. Use "
            "--no-soul for highly formal content that shouldn't contract."
        ),
    )
    parser.add_argument(
        "--strip-reasoning",
        action="store_true",
        help=(
            "Strip agent reasoning traces (<thinking>, <think>, <analysis>, "
            "<reasoning>, <scratchpad>, <plan> tags and markdown '## Reasoning' "
            "sections) before humanization. Destructive; default off. Stripped "
            "content is written to <stem>.reasoning.md for audit. Research: "
            "'reason privately, humanize publicly' (Category 06)."
        ),
    )
    parser.add_argument(
        "--no-audit",
        action="store_true",
        help=(
            "Skip the LLM audit pass that normally runs at --mode full and "
            "--mode anti-detector. Faster, but leaves more residual AI tells."
        ),
    )
    parser.add_argument(
        "--voice-sample",
        type=Path,
        default=None,
        help=(
            "Path to a text sample whose stylometric profile the rewrite should "
            "match. LLM mode only; ignored in --deterministic. The sample's "
            "sentence-length μ/σ, contraction rate, punctuation rates, and "
            "pronoun ratios are measured and injected into the rewrite prompt "
            "as explicit numeric targets."
        ),
    )
    parser.add_argument(
        "--voice-memory",
        action="store_true",
        help=(
            "Use the persisted style memory (see --save-voice-profile) as the "
            "voice sample. Silently ignored if no memory is on file. Explicit "
            "--voice-sample always wins if both are provided."
        ),
    )
    parser.add_argument(
        "--save-voice-profile",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Measure the stylometric profile of the sample at PATH and persist "
            "it to the style-memory file ($UNSLOP_STYLE_MEMORY or "
            "$XDG_CONFIG_HOME/unslop/style-memory.json). One-shot command; "
            "exits after saving."
        ),
    )
    parser.add_argument(
        "--clear-voice-profile",
        action="store_true",
        help="Delete the persisted style memory. One-shot; exits after.",
    )
    parser.add_argument(
        "--detector-feedback",
        action="store_true",
        help=(
            "Run the output through an AI-text detector and re-humanize with "
            "escalating intensity until the score falls below target. Opt-in; "
            "first run downloads ~500MB of HF weights (or run `python3 -m "
            "unslop.scripts.fetch_detectors` ahead of time)."
        ),
    )
    parser.add_argument(
        "--detector-loop-aggressive",
        action="store_true",
        help=(
            "Use the 6-step detector-feedback ladder instead of the default "
            "4-step ladder."
        ),
    )
    parser.add_argument(
        "--detector-target",
        type=float,
        default=0.5,
        help="Stop escalating once the detector score drops below this. Default 0.5.",
    )
    parser.add_argument(
        "--detector-max-iterations",
        type=_positive_int,
        default=None,
        help="Cap how many escalation steps to try. Default 4 (default ladder) or 6 (aggressive).",
    )
    parser.add_argument(
        "--detector-model",
        choices=("tmr", "desklib"),
        default="tmr",
        help="Which detector to use. TMR (~500MB) is the default.",
    )
    parser.add_argument(
        "--detector-surprisal",
        action="store_true",
        help=(
            "Opt-in: attach a real surprisal-variance reading (distilgpt2, ~330MB) "
            "to each detector-feedback iteration. Without this flag, detector "
            "feedback runs without loading a language model. Uses --surprisal-model "
            "for the model id."
        ),
    )
    parser.add_argument(
        "--surprisal-variance",
        action="store_true",
        help=(
            "One-shot: read text from stdin (or --file if provided), run it "
            "through a small local LM (distilgpt2, ~330MB), and print a real "
            "DivEye-style surprisal-variance reading as JSON. Exits after. "
            "First call downloads weights; subsequent calls are ~1s. Research: "
            "Cat 15 DivEye (arXiv 2509.18880)."
        ),
    )
    parser.add_argument(
        "--surprisal-model",
        default="distilgpt2",
        metavar="MODEL_ID",
        help=(
            "HuggingFace model id for --surprisal-variance. Default distilgpt2. "
            "Any causal-LM that transformers can load works; bigger models "
            "give more reliable readings but take longer."
        ),
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress progress lines on stdout.",
    )
    return parser


def _process_stdin(args: argparse.Namespace) -> int:
    from .humanize import humanize_deterministic_with_report, humanize_llm
    from .validate import validate

    text = sys.stdin.read()
    feedback = None
    voice_sample = None
    voice_profile = None
    if args.voice_sample is not None:
        voice_sample = args.voice_sample.read_text(encoding="utf-8")
    else:
        voice_profile = _resolve_voice_profile(args)

    # --strip-reasoning runs on stdin input before any humanizer (deterministic,
    # LLM, or detector-feedback) sees it. Keeps the three paths consistent: the
    # LLM doesn't need to re-strip, and the deterministic inner pass becomes a
    # no-op on the reasoning step. stdin never writes a .reasoning.md sidecar
    # (no target path to write beside), so the content is discarded.
    if args.strip_reasoning:
        from .reasoning import strip_reasoning_traces

        text, _ = strip_reasoning_traces(text)

    if args.detector_feedback:
        from .detector import DetectorUnavailable, feedback_loop, feedback_loop_aggressive

        surprisal_fn = None
        if args.detector_surprisal:
            surprisal_fn = _build_surprisal_fn(args.surprisal_model)

        try:
            loop = feedback_loop_aggressive if args.detector_loop_aggressive else feedback_loop
            outcome = loop(
                text,
                target_probability=args.detector_target,
                max_iterations=_detector_feedback_max_iterations(args),
                detector=args.detector_model,
                surprisal_fn=surprisal_fn,
            )
        except DetectorUnavailable as exc:
            sys.stderr.write(f"detector feedback disabled: {exc}\n")
            return 1
        humanized = outcome.final_text
        feedback = outcome
        report = None
    elif args.deterministic or not _llm_available():
        # strip_reasoning already applied above on stdin entry; pass False here
        # so the deterministic report doesn't misleadingly show 0 blocks.
        humanized, report = humanize_deterministic_with_report(
            text,
            intensity=args.mode,
            structural=args.structural,
            soul=args.soul,
        )
    else:
        llm_kwargs: dict = {"intensity": args.mode}
        if voice_sample is not None:
            llm_kwargs["voice_sample"] = voice_sample
        if voice_profile is not None:
            llm_kwargs["voice_profile"] = voice_profile
        if args.no_audit:
            llm_kwargs["audit"] = False
        try:
            humanized = humanize_llm(text, **llm_kwargs)
        except RuntimeError as exc:
            if args.json:
                payload = {
                    "path": "<stdin>",
                    "ok": False,
                    "error_code": "sensitive_content_refused"
                    if str(exc).startswith("Refusing to send secret-like content")
                    else "llm_unavailable",
                    "error": str(exc),
                    "hint": "Use --deterministic for a local-only pass",
                }
                sys.stderr.write(json.dumps(payload, indent=2) + "\n")
            else:
                sys.stderr.write(str(exc) + "\n")
            return 1
        report = None

    result = validate(text, humanized)
    if args.diff:
        if result.ok:
            _emit_diff(sys.stdout, "stdin", text, humanized)
        else:
            from .validate import format_report

            sys.stderr.write(format_report(result) + "\n")
    else:
        sys.stdout.write(humanized)

    if args.json:
        payload = {
            "path": "<stdin>",
            "ok": result.ok,
            "validation": result.to_dict(),
        }
        if report is not None:
            payload["report"] = report.to_dict()
        if feedback is not None:
            payload["detector_feedback"] = feedback.to_dict()
        sys.stderr.write(json.dumps(payload, indent=2) + "\n")
    elif feedback is not None and not args.quiet:
        sys.stderr.write(
            f"detector: {feedback.original_probability:.1%} → "
            f"{feedback.final_probability:.1%} "
            f"({feedback.reason_stopped})\n"
        )
    if args.report_stylometric_gaps and not args.quiet:
        _emit_stylometric_gaps(sys.stderr, humanized)

    return 0 if result.ok else 2


def _llm_available() -> bool:
    import os
    import shutil
    return bool(os.environ.get("ANTHROPIC_API_KEY")) or shutil.which("claude") is not None


def _emit_diff(out, label: str, before: str, after: str) -> None:
    diff = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"{label} (original)",
        tofile=f"{label} (humanized)",
    )
    out.writelines(diff)


def _emit_stylometric_gaps(out, text: str) -> None:
    from .lexical_targets import measure_gaps

    gaps = measure_gaps(text)
    if not gaps:
        out.write("stylometric gaps: none (or no baseline file)\n")
        return
    out.write("stylometric gaps:\n")
    for gap in gaps:
        out.write(
            f"  {gap.field}: {gap.current:.3f} outside "
            f"{gap.target_low:.3f}-{gap.target_high:.3f} (delta {gap.delta:+.3f})\n"
        )


_SURPRISAL_WARNING_EMITTED = False


def _build_surprisal_fn(model: str):
    """Build a surprisal callable that returns full SurprisalReading objects.

    Returns None (not a callable) when deps are missing so the caller
    can distinguish 'user opted in but deps absent' from 'user did not
    opt in'. Emits exactly one stderr diagnostic per CLI invocation.
    """
    global _SURPRISAL_WARNING_EMITTED  # noqa: PLW0603
    try:
        from .surprisal import SurprisalUnavailable, compute_surprisal_variance
    except ImportError:
        if not _SURPRISAL_WARNING_EMITTED:
            _SURPRISAL_WARNING_EMITTED = True
            sys.stderr.write(
                "unslop: --detector-surprisal requested but dependencies unavailable. "
                "Install with: pip install unslop[surprisal]\n"
            )
        return None

    def _fn(text: str):
        nonlocal model
        try:
            return compute_surprisal_variance(text, model=model)
        except SurprisalUnavailable:
            global _SURPRISAL_WARNING_EMITTED  # noqa: PLW0603
            if not _SURPRISAL_WARNING_EMITTED:
                _SURPRISAL_WARNING_EMITTED = True
                sys.stderr.write(
                    "unslop: surprisal model unavailable. "
                    "Install with: pip install unslop[surprisal]\n"
                )
            return None
        except (RuntimeError, OSError):
            return None

    return _fn


def _detector_feedback_max_iterations(args: argparse.Namespace) -> int:
    """Map CLI defaults to full ladder length when user didn't override."""
    if args.detector_max_iterations is not None:
        return args.detector_max_iterations
    return 6 if args.detector_loop_aggressive else 4


def _process_file_detector_feedback(
    path: Path,
    args: argparse.Namespace,
    write: bool,
    report_accumulator: list[dict],
) -> int:
    """File-mode detector feedback loop. Separate path because the backup +
    validate + write sequence differs from humanize_file_ex — we validate
    the FINAL humanized text against the original, not an intermediate."""
    from .detector import DetectorUnavailable, feedback_loop, feedback_loop_aggressive
    from .validate import format_report, validate

    original = path.read_text(encoding="utf-8")

    surprisal_fn = None
    if args.detector_surprisal:
        surprisal_fn = _build_surprisal_fn(args.surprisal_model)

    try:
        loop = feedback_loop_aggressive if args.detector_loop_aggressive else feedback_loop
        outcome = loop(
            original,
            target_probability=args.detector_target,
            max_iterations=_detector_feedback_max_iterations(args),
            detector=args.detector_model,
            surprisal_fn=surprisal_fn,
        )
    except DetectorUnavailable as exc:
        sys.stderr.write(f"[{path.name}] detector feedback disabled: {exc}\n")
        return 1

    humanized = outcome.final_text
    result = validate(original, humanized)

    if args.diff:
        _emit_diff(sys.stdout, str(path), original, humanized)
    elif args.output is not None and result.ok:
        args.output.write_text(humanized, encoding="utf-8")
        if not args.quiet:
            sys.stdout.write(f"[{path.name}] wrote humanized text to {args.output}\n")
    elif write and result.ok:
        backup = path.with_name(path.stem + ".original.md")
        if not args.no_backup and not backup.exists():
            backup.write_text(original, encoding="utf-8")
        path.write_text(humanized, encoding="utf-8")

    if args.json:
        payload = {
            "path": str(path),
            "ok": result.ok,
            "validation": result.to_dict(),
            "detector_feedback": outcome.to_dict(),
        }
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    elif not args.quiet:
        sys.stdout.write(format_report(result) + "\n")
        sys.stdout.write(
            f"  detector: {outcome.original_probability:.1%} → "
            f"{outcome.final_probability:.1%} "
            f"({outcome.reason_stopped})\n"
        )

    if args.report is not None:
        report_accumulator.append(
            {"path": str(path), "detector_feedback": outcome.to_dict()}
        )
    if args.report_stylometric_gaps and not args.quiet:
        _emit_stylometric_gaps(sys.stdout, humanized)

    return 0 if result.ok else 2


def _process_file(
    path: Path,
    args: argparse.Namespace,
    report_accumulator: list[dict],
) -> int:
    from .detect import detect_file_type, should_compress
    from .humanize import humanize_file_ex
    from .validate import format_report

    if not path.exists():
        sys.stderr.write(f"Error: file not found: {path}\n")
        return 1
    if not path.is_file():
        sys.stderr.write(f"Error: not a file: {path}\n")
        return 1

    path = path.resolve()
    file_type = detect_file_type(path)

    if not args.quiet:
        sys.stdout.write(f"[{path.name}] detected: {file_type}\n")

    if not should_compress(path):
        sys.stdout.write(f"[{path.name}] skipped (not natural-language prose)\n")
        return 0

    write = not (args.dry_run or args.diff)
    if args.output is not None:
        write = False  # handle --output explicitly below

    if args.detector_feedback:
        return _process_file_detector_feedback(path, args, write, report_accumulator)

    voice_sample_text: str | None = None
    voice_profile = None
    if args.voice_sample is not None:
        voice_sample_text = args.voice_sample.read_text(encoding="utf-8")
    else:
        voice_profile = _resolve_voice_profile(args)

    outcome = humanize_file_ex(
        path,
        deterministic=args.deterministic,
        intensity=args.mode,
        backup=not args.no_backup,
        write=write,
        structural=args.structural,
        soul=args.soul,
        voice_sample=voice_sample_text,
        voice_profile=voice_profile,
        strip_reasoning=args.strip_reasoning,
        audit=False if args.no_audit else None,
    )

    if args.diff:
        if outcome.ok:
            _emit_diff(sys.stdout, str(path), outcome.original, outcome.humanized)
        else:
            if outcome.validation is not None and hasattr(outcome.validation, "to_dict"):
                sys.stderr.write(format_report(outcome.validation) + "\n")
            if outcome.error:
                sys.stderr.write(f"[{path.name}] {outcome.error}\n")
    elif args.output is not None and outcome.ok:
        args.output.write_text(outcome.humanized, encoding="utf-8")
        if not args.quiet:
            sys.stdout.write(f"[{path.name}] wrote humanized text to {args.output}\n")

    file_payload = {
        "path": str(path),
        "ok": outcome.ok,
        "attempts": outcome.attempts,
        "error": outcome.error,
    }
    if outcome.error and outcome.error.startswith("Refusing to send secret-like content"):
        file_payload["error_code"] = "sensitive_content_refused"
    if outcome.validation is not None and hasattr(outcome.validation, "to_dict"):
        file_payload["validation"] = outcome.validation.to_dict()
    if outcome.report is not None:
        file_payload["report"] = outcome.report.to_dict()

    if args.json:
        sys.stdout.write(json.dumps(file_payload, indent=2) + "\n")
    elif not args.quiet:
        if outcome.validation is not None and hasattr(outcome.validation, "to_dict"):
            sys.stdout.write(format_report(outcome.validation) + "\n")
        if outcome.report is not None:
            counts = outcome.report.counts_by_rule
            if counts:
                sys.stdout.write(
                    f"  replacements: {sum(counts.values())} "
                    f"({', '.join(f'{k}={v}' for k, v in sorted(counts.items()))})\n"
                )
        if outcome.error:
            sys.stderr.write(f"[{path.name}] {outcome.error}\n")
        if args.report_stylometric_gaps and outcome.ok:
            _emit_stylometric_gaps(sys.stdout, outcome.humanized)

    if args.report is not None and outcome.report is not None:
        report_accumulator.append({"path": str(path), "report": outcome.report.to_dict()})

    if not outcome.ok:
        if outcome.error and outcome.error.startswith("Refusing to send secret-like content"):
            return 1
        return 2
    return 0


def _handle_voice_memory_commands(args: argparse.Namespace) -> int | None:
    """Run --save-voice-profile / --clear-voice-profile if set. Returns an exit
    code when a memory command ran, or None when no command applied."""
    if args.save_voice_profile is not None:
        from .style_memory import StyleMemoryError, save_profile

        sample_path = args.save_voice_profile
        if not sample_path.is_file():
            sys.stderr.write(f"Error: voice sample not found: {sample_path}\n")
            return 1
        text = sample_path.read_text(encoding="utf-8")
        try:
            target = save_profile(text, source=str(sample_path))
        except StyleMemoryError as exc:
            sys.stderr.write(f"Error: {exc}\n")
            return 1
        if not args.quiet:
            sys.stdout.write(f"Saved style memory to {target}\n")
        return 0

    if args.clear_voice_profile:
        from .style_memory import StyleMemoryError, clear_profile

        try:
            removed = clear_profile()
        except StyleMemoryError as exc:
            sys.stderr.write(f"Error: {exc}\n")
            return 1
        if not args.quiet:
            msg = "Cleared style memory." if removed else "No style memory on file."
            sys.stdout.write(msg + "\n")
        return 0

    return None


def _handle_surprisal_command(args: argparse.Namespace) -> int:
    """Run the DivEye surprisal-variance reading and print JSON. One-shot.

    Source priority: --stdin > first positional file > stdin by default.
    No humanization; just the reading. Exits after."""
    from .surprisal import SurprisalUnavailable, compute_surprisal_variance

    if args.stdin or not args.files or args.files == ["-"]:
        text = sys.stdin.read()
        source = "<stdin>"
    else:
        source_path = Path(args.files[0])
        try:
            text = source_path.read_text(encoding="utf-8")
        except OSError as exc:
            sys.stderr.write(f"error: cannot read {source_path}: {exc}\n")
            return 1
        source = str(source_path)

    try:
        reading = compute_surprisal_variance(text, model=args.surprisal_model)
    except SurprisalUnavailable as exc:
        sys.stderr.write(f"surprisal reading unavailable: {exc}\n")
        return 1

    payload = {"path": source, **reading.to_dict()}
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    return 0


def _resolve_voice_profile(args: argparse.Namespace):
    """Return a StyleProfile when --voice-memory is requested and memory
    exists. Explicit --voice-sample is handled via text in the prompt
    builder; this path only applies when we only have the persisted
    numeric profile."""
    if args.voice_sample is not None:
        return None
    if not args.voice_memory:
        return None
    from .style_memory import StyleMemoryError, load_profile

    try:
        return load_profile()
    except StyleMemoryError as exc:
        sys.stderr.write(f"warn: style memory unreadable: {exc}\n")
        return None


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # One-shot memory management runs before any humanize work.
    memory_rc = _handle_voice_memory_commands(args)
    if memory_rc is not None:
        return memory_rc

    # One-shot: surprisal variance reading. Reads stdin (or the first file),
    # scores, prints JSON, exits. No humanization.
    if args.surprisal_variance:
        return _handle_surprisal_command(args)

    # --diff implies --dry-run. --stdin forces no-backup.
    if args.diff and args.json:
        parser.error("--diff and --json cannot be combined; use one output format")
    if args.diff:
        args.dry_run = True
    if args.stdin:
        args.no_backup = True

    # --- stdin mode ---
    if args.stdin or args.files == ["-"]:
        return _process_stdin(args)

    if not args.files:
        parser.error("no input files (pass a path, or --stdin)")

    if args.output is not None and len(args.files) != 1:
        parser.error("--output requires exactly one input file")

    if args.report is not None and not args.deterministic:
        parser.error("--report requires --deterministic")

    paths = [Path(p) for p in args.files]
    report_accumulator: list[dict] = []

    exit_codes = [_process_file(p, args, report_accumulator) for p in paths]

    if args.report is not None:
        args.report.write_text(
            json.dumps(report_accumulator, indent=2) + "\n", encoding="utf-8"
        )
        if not args.quiet:
            sys.stdout.write(f"wrote audit trail to {args.report}\n")

    if all(code == 0 for code in exit_codes):
        return 0
    if all(code != 0 for code in exit_codes):
        # All files failed — surface the worst code.
        return max(exit_codes)
    # Mixed — partial success
    return 3


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
