#!/usr/bin/env python3
"""Validate ChromBPNet training inputs and render the official CLI command."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
from typing import Any


EXPECTED_OUTPUT_CHILDREN = ("logs", "auxiliary", "models", "evaluation")
REQUIRED_TOOLS = ("chrombpnet", "samtools", "bedtools", "bedGraphToBigWig", "modisco")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a ChromBPNet or bias-model training bundle without loading "
            "TensorFlow, then emit the corresponding chrombpnet command."
        )
    )
    parser.add_argument("--mode", choices=("chrombpnet", "bias"), required=True)
    parser.add_argument("--assay", choices=("ATAC", "DNASE"), required=True)
    parser.add_argument("--genome", type=Path, required=True)
    parser.add_argument("--chrom-sizes", type=Path, required=True)
    parser.add_argument("--peaks", type=Path, required=True)
    parser.add_argument("--nonpeaks", type=Path, required=True)
    parser.add_argument("--fold", type=Path, required=True)
    reads = parser.add_mutually_exclusive_group(required=True)
    reads.add_argument("--bam", type=Path)
    reads.add_argument("--fragments", type=Path)
    reads.add_argument("--tagalign", type=Path)
    parser.add_argument("--bias-model", type=Path)
    parser.add_argument("--bias-threshold-factor", type=float)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--inputlen", type=int, default=2114)
    parser.add_argument("--outputlen", type=int, default=1000)
    parser.add_argument("--json-output", type=Path)
    return parser


def add_error(report: dict[str, Any], message: str) -> None:
    report["errors"].append(message)


def add_warning(report: dict[str, Any], message: str) -> None:
    report["warnings"].append(message)


def require_file(path: Path, label: str, report: dict[str, Any]) -> bool:
    if not path.is_file():
        add_error(report, f"{label} is not a file: {path}")
        return False
    if path.stat().st_size == 0:
        add_error(report, f"{label} is empty: {path}")
        return False
    return True


def read_chrom_sizes(path: Path, report: dict[str, Any]) -> dict[str, int]:
    sizes: dict[str, int] = {}
    if not require_file(path, "chromosome sizes", report):
        return sizes
    with path.open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            line = raw.rstrip("\n")
            if not line:
                continue
            fields = line.split("\t")
            if len(fields) != 2:
                add_error(report, f"chromosome sizes line {line_number} must have 2 tab-separated columns")
                continue
            chrom, size_text = fields
            if not chrom:
                add_error(report, f"chromosome sizes line {line_number} has an empty chromosome")
                continue
            if chrom in sizes:
                add_error(report, f"chromosome sizes contains duplicate chromosome {chrom!r}")
                continue
            try:
                size = int(size_text)
            except ValueError:
                add_error(report, f"chromosome sizes line {line_number} has non-integer length {size_text!r}")
                continue
            if size <= 0:
                add_error(report, f"chromosome sizes line {line_number} must have a positive length")
                continue
            sizes[chrom] = size
    if not sizes:
        add_error(report, "chromosome sizes contains no valid records")
    return sizes


def read_fasta_names(path: Path, report: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    if not require_file(path, "reference FASTA", report):
        return names
    with path.open(encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            if raw.startswith(">"):
                name = raw[1:].strip().split(maxsplit=1)[0]
                if name:
                    names.add(name)
    if not names:
        add_error(report, "reference FASTA contains no sequence headers")
    return names


def validate_narrowpeak(
    path: Path,
    label: str,
    chrom_sizes: dict[str, int],
    inputlen: int,
    report: dict[str, Any],
) -> dict[str, int]:
    summary = {"records": 0, "edge_filtered": 0}
    if not require_file(path, label, report):
        return summary
    with path.open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            summary["records"] += 1
            fields = line.split("\t")
            if len(fields) != 10:
                add_error(report, f"{label} line {line_number} must have exactly 10 tab-separated columns")
                continue
            chrom = fields[0]
            if chrom not in chrom_sizes:
                add_error(report, f"{label} line {line_number} chromosome {chrom!r} is absent from chromosome sizes")
                continue
            try:
                start, end, summit = int(fields[1]), int(fields[2]), int(fields[9])
            except ValueError:
                add_error(report, f"{label} line {line_number} has non-integer start, end, or summit")
                continue
            if start < 0 or end <= start:
                add_error(report, f"{label} line {line_number} must satisfy 0 <= start < end")
                continue
            if end > chrom_sizes[chrom]:
                add_error(report, f"{label} line {line_number} ends beyond {chrom} length")
                continue
            if summit < 0 or summit >= end - start:
                add_error(report, f"{label} line {line_number} summit must be a 0-based offset within the interval")
                continue
            center = start + summit
            half = inputlen // 2
            if center - half < 0 or center + half > chrom_sizes[chrom]:
                summary["edge_filtered"] += 1
    if summary["records"] == 0:
        add_error(report, f"{label} contains no data records")
    elif summary["edge_filtered"]:
        add_warning(
            report,
            f"{label}: {summary['edge_filtered']} of {summary['records']} records cannot provide a full "
            f"{inputlen}-bp input window and may be filtered",
        )
    return summary


def validate_fold(path: Path, chrom_sizes: dict[str, int], report: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not require_file(path, "fold JSON", report):
        return counts
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        add_error(report, f"fold JSON cannot be parsed: {exc}")
        return counts
    if not isinstance(data, dict):
        add_error(report, "fold JSON root must be an object")
        return counts
    sets: dict[str, set[str]] = {}
    for key in ("train", "valid", "test"):
        values = data.get(key)
        if not isinstance(values, list) or not values or not all(isinstance(value, str) and value for value in values):
            add_error(report, f"fold JSON key {key!r} must be a nonempty list of chromosome strings")
            continue
        if len(values) != len(set(values)):
            add_error(report, f"fold JSON key {key!r} contains duplicate chromosomes")
        sets[key] = set(values)
        counts[key] = len(values)
        missing = sorted(sets[key] - set(chrom_sizes))
        if missing:
            add_error(report, f"fold JSON key {key!r} contains chromosomes absent from chromosome sizes: {missing}")
    keys = list(sets)
    for index, left in enumerate(keys):
        for right in keys[index + 1 :]:
            overlap = sorted(sets[left] & sets[right])
            if overlap:
                add_error(report, f"fold JSON keys {left!r} and {right!r} overlap: {overlap}")
    return counts


def validate_output_dir(path: Path, report: dict[str, Any]) -> None:
    if path.exists() and not path.is_dir():
        add_error(report, f"output path exists and is not a directory: {path}")
        return
    collisions = [str(path / child) for child in EXPECTED_OUTPUT_CHILDREN if (path / child).exists()]
    if collisions:
        add_error(report, "ChromBPNet output children already exist: " + ", ".join(collisions))
    parent = path if path.exists() else path.parent
    if not parent.exists():
        add_warning(report, f"output parent does not exist yet and will need to be created: {parent}")
    elif not os.access(parent, os.W_OK):
        add_error(report, f"output parent is not writable: {parent}")


def render_command(args: argparse.Namespace) -> list[str]:
    command = ["chrombpnet"]
    if args.mode == "chrombpnet":
        command.append("pipeline")
    else:
        command.extend(("bias", "pipeline"))
    input_path = args.bam or args.fragments or args.tagalign
    input_flag = {
        "bam": "--input-bam-file",
        "fragments": "--input-fragment-file",
        "tagalign": "--input-tagalign-file",
    }["bam" if args.bam else "fragments" if args.fragments else "tagalign"]
    command.extend(
        (
            input_flag,
            str(input_path),
            "--data-type",
            args.assay,
            "--genome",
            str(args.genome),
            "--chrom-sizes",
            str(args.chrom_sizes),
            "--peaks",
            str(args.peaks),
            "--nonpeaks",
            str(args.nonpeaks),
            "--chr-fold-path",
            str(args.fold),
        )
    )
    if args.mode == "chrombpnet":
        command.extend(("--bias-model-path", str(args.bias_model)))
    else:
        command.extend(("--bias-threshold-factor", str(args.bias_threshold_factor)))
    command.extend(
        (
            "--inputlen",
            str(args.inputlen),
            "--outputlen",
            str(args.outputlen),
            "--output-dir",
            str(args.output_dir),
        )
    )
    return command


def main() -> int:
    args = build_parser().parse_args()
    report: dict[str, Any] = {
        "status": "pending",
        "mode": args.mode,
        "assay": args.assay,
        "errors": [],
        "warnings": [],
        "checks": {},
    }
    if args.inputlen <= 0 or args.inputlen % 2:
        add_error(report, "--inputlen must be a positive even integer")
    if args.outputlen <= 0 or args.outputlen % 2:
        add_error(report, "--outputlen must be a positive even integer")
    if args.outputlen > args.inputlen:
        add_error(report, "--outputlen cannot exceed --inputlen")

    read_path = args.bam or args.fragments or args.tagalign
    require_file(read_path, "read input", report)
    if args.bam and not (Path(str(args.bam) + ".bai").is_file() or args.bam.with_suffix(".bai").is_file()):
        add_warning(report, f"BAM index was not found next to {args.bam}")

    if args.mode == "chrombpnet":
        if args.bias_model is None:
            add_error(report, "--bias-model is required in chrombpnet mode")
        else:
            require_file(args.bias_model, "bias model", report)
        if args.bias_threshold_factor is not None:
            add_warning(report, "--bias-threshold-factor is ignored in chrombpnet mode")
    else:
        if args.bias_model is not None:
            add_warning(report, "--bias-model is ignored in bias mode")
        if args.bias_threshold_factor is None:
            args.bias_threshold_factor = 0.5 if args.assay == "ATAC" else 0.8
            add_warning(
                report,
                f"using the repository starting value --bias-threshold-factor {args.bias_threshold_factor}; review QC",
            )
        elif args.bias_threshold_factor <= 0:
            add_error(report, "--bias-threshold-factor must be positive")

    chrom_sizes = read_chrom_sizes(args.chrom_sizes, report)
    fasta_names = read_fasta_names(args.genome, report)
    if chrom_sizes and fasta_names:
        missing_fasta = sorted(set(chrom_sizes) - fasta_names)
        if missing_fasta:
            add_warning(report, f"chromosome sizes entries absent from FASTA headers: {missing_fasta[:20]}")
    report["checks"]["peaks"] = validate_narrowpeak(args.peaks, "peaks", chrom_sizes, args.inputlen, report)
    report["checks"]["nonpeaks"] = validate_narrowpeak(
        args.nonpeaks, "nonpeaks", chrom_sizes, args.inputlen, report
    )
    report["checks"]["fold_counts"] = validate_fold(args.fold, chrom_sizes, report)
    validate_output_dir(args.output_dir, report)
    report["checks"]["executables"] = {tool: shutil.which(tool) for tool in REQUIRED_TOOLS}
    missing_tools = [tool for tool, path in report["checks"]["executables"].items() if path is None]
    if missing_tools:
        add_warning(report, "executables not found on PATH: " + ", ".join(missing_tools))

    if not report["errors"]:
        command = render_command(args)
        report["command_argv"] = command
        report["command"] = shlex.join(command)
        report["status"] = "ok"
    else:
        report["status"] = "error"

    output = json.dumps(report, indent=2, sort_keys=True)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
