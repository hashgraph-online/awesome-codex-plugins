#!/usr/bin/env python3
"""Run a complete external SPICE deck with an explicitly selected simulator."""

import argparse
import contextlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import time

from spice_simulator import PspiceBackend, detect_simulator


SIMULATORS = ("pspice", "ngspice", "ltspice", "xyce")
DEFAULT_TIMEOUT_S = 600


def select_backend(simulator: str):
    if simulator == "pspice":
        backend = PspiceBackend()
        return backend if backend.find() else None
    return detect_simulator(simulator)


# Files each simulator writes beside the deck, named <stem><suffix>.
_SIMULATOR_OUTPUT_SUFFIXES = {
    "pspice": (".out", ".json", ".dat"),
    "ltspice": (".log", ".raw"),
    "xyce": (".mt0",),
}


def native_output_for(deck: Path, simulator: str) -> Path | None:
    if simulator == "pspice":
        return PspiceBackend.native_output_path(deck)
    return None


def _same_path(first: Path, second: Path) -> bool:
    return os.path.normcase(str(first.resolve())) == os.path.normcase(
        str(second.resolve())
    )


def _output_conflict(
    output: Path, deck: Path, native_output: Path | None
) -> str | None:
    """Explain why --output cannot be written, or return None if it can."""
    protected = [("the deck", deck)]
    if native_output is not None:
        protected.append(("the PSpice native output", native_output))
        protected.append((
            "the PSpice sidecar file",
            native_output.with_suffix(".json"),
        ))
        protected.append((
            "the PSpice waveform data file",
            native_output.with_suffix(".dat"),
        ))
    for label, path in protected:
        if _same_path(output, path):
            return f"--output would overwrite {label}: {output}"
    if output.is_dir():
        return f"--output is a directory: {output}"
    if not output.resolve().parent.is_dir():
        return f"--output directory does not exist: {output.parent}"
    return None


def _build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Run a complete external SPICE deck without generating "
            "measurements"
        )
    )
    parser.add_argument("deck", type=Path, help="Existing external .cir deck")
    parser.add_argument(
        "--simulator",
        required=True,
        choices=SIMULATORS,
        help=(
            "pspice checks its native .out log and kills the whole process "
            "tree on timeout; ngspice, ltspice and xyce report exit code "
            "only and kill only the direct process"
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_S,
        help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT_S})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write result JSON to this path",
    )
    return parser


def _result(simulator, success, deck, native_output, elapsed_s, note):
    return {
        "simulator": simulator,
        "success": success,
        "deck": str(deck),
        "native_output": (
            str(native_output) if native_output is not None else None
        ),
        "elapsed_s": round(elapsed_s, 3),
        "note": note,
    }


def _result_mode(target):
    """Keep an existing result file's mode; otherwise honor the umask."""
    try:
        return stat.S_IMODE(target.stat().st_mode)
    except FileNotFoundError:
        umask = os.umask(0)
        os.umask(umask)
        return 0o666 & ~umask


def _write_json(payload, output_path):
    """Write the result, returning False with a diagnostic on I/O failure."""
    try:
        if output_path:
            target = Path(output_path)
            descriptor, temp_name = tempfile.mkstemp(
                dir=target.resolve().parent,
                prefix=f".{target.name}.",
                suffix=".tmp",
            )
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                    json.dump(payload, stream, indent=2)
                    stream.write("\n")
                os.chmod(temp_name, _result_mode(target))
                os.replace(temp_name, target)
            except BaseException:
                # A copied read-only mode would block unlink on Windows.
                with contextlib.suppress(OSError):
                    os.chmod(temp_name, stat.S_IREAD | stat.S_IWRITE)
                Path(temp_name).unlink(missing_ok=True)
                raise
        else:
            json.dump(payload, sys.stdout, indent=2)
            sys.stdout.write("\n")
    except OSError as exc:
        print(
            f"Error: could not write {output_path or 'stdout'}: {exc}",
            file=sys.stderr,
        )
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    deck = args.deck.resolve()
    if not deck.is_file():
        parser.error(f"deck is not a file: {deck}")
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")

    if deck.suffix.lower() in _SIMULATOR_OUTPUT_SUFFIXES.get(
        args.simulator, ()
    ):
        parser.error(
            f"deck must not use the {deck.suffix} suffix, which "
            f"{args.simulator} uses for the files it writes next to the "
            f"deck: {deck}"
        )

    native_output = native_output_for(deck, args.simulator)
    if args.output is not None:
        conflict = _output_conflict(args.output, deck, native_output)
        if conflict:
            parser.error(conflict)

    backend = select_backend(args.simulator)
    if backend is None:
        if args.simulator == "pspice":
            diagnostic = (
                "PSpice executable not found; set PSPICE_PATH or add "
                "pspice to PATH"
            )
        else:
            diagnostic = f"{args.simulator} executable not found"
        payload = _result(
            args.simulator,
            False,
            deck,
            native_output,
            0.0,
            diagnostic,
        )
        if not _write_json(payload, args.output):
            return 1
        print(diagnostic, file=sys.stderr)
        return 1

    started = time.perf_counter()
    success, _stdout, diagnostic = backend.run(
        str(deck),
        timeout=args.timeout,
    )
    elapsed_s = time.perf_counter() - started
    if success and args.simulator == "pspice":
        note = "PSpice reported JOB CONCLUDED"
    elif success:
        note = f"{backend.name} exited successfully"
    else:
        note = (
            diagnostic
            or f"{backend.name} did not report successful completion"
        )

    payload = _result(
        args.simulator,
        success,
        deck,
        native_output,
        elapsed_s,
        note,
    )
    if not _write_json(payload, args.output):
        return 1
    if not success:
        print(note, file=sys.stderr)
    return 0 if success else 1


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # UTF-8 on a cp1252 pipe (Windows)
        if (getattr(_stream, "encoding", "") or "").lower().replace("-", "") != "utf8" \
                and hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    raise SystemExit(main())
