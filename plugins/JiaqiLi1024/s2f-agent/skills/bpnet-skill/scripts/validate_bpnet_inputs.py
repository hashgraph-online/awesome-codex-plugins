#!/usr/bin/env python3
"""Validate BPNet 2.0.0 JSON inputs before training, prediction, or SHAP."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


@dataclass
class Report:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "valid": not self.errors,
            "errors": self.errors,
            "warnings": self.warnings,
            "notes": self.notes,
        }


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def load_json(path: Path, label: str, report: Report) -> Optional[Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        report.error(f"{label}: file not found: {path}")
    except PermissionError:
        report.error(f"{label}: cannot read file: {path}")
    except json.JSONDecodeError as exc:
        report.error(
            f"{label}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        )
    return None


def validate_contiguous_ids(
    value: Any, label: str, report: Report
) -> Optional[Dict[str, Any]]:
    if not isinstance(value, dict) or not value:
        report.error(f"{label}: expected a non-empty JSON object")
        return None

    keys = list(value.keys())
    if any(not isinstance(key, str) or not key.isdigit() for key in keys):
        report.error(f'{label}: top-level keys must be string integers such as "0"')
        return None

    numeric = sorted(int(key) for key in keys)
    expected = list(range(len(keys)))
    if numeric != expected:
        report.error(
            f"{label}: IDs must be contiguous from 0; found {numeric}, expected {expected}"
        )
        return None
    return value


def validate_string_list(
    value: Any,
    label: str,
    report: Report,
    *,
    allow_empty: bool = False,
) -> Optional[List[str]]:
    if not isinstance(value, list):
        report.error(f"{label}: expected a list")
        return None
    if not value and not allow_empty:
        report.error(f"{label}: list must not be empty")
        return None
    if any(not isinstance(item, str) or not item.strip() for item in value):
        report.error(f"{label}: every entry must be a non-empty string")
        return None
    return value


def check_referenced_paths(paths: Iterable[str], label: str, report: Report) -> None:
    for raw_path in paths:
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.is_file():
            report.error(f"{label}: referenced file not found: {raw_path}")


def validate_source_block(
    task: Dict[str, Any],
    block_name: str,
    label: str,
    report: Report,
    *,
    allow_empty: bool = False,
    check_paths: bool = False,
) -> Optional[List[str]]:
    block = task.get(block_name)
    if not isinstance(block, dict):
        report.error(f"{label}.{block_name}: expected an object")
        return None
    sources = validate_string_list(
        block.get("source"),
        f"{label}.{block_name}.source",
        report,
        allow_empty=allow_empty,
    )
    if sources is not None and check_paths:
        check_referenced_paths(sources, f"{label}.{block_name}.source", report)
    return sources


def validate_input_data(
    value: Any,
    report: Report,
    *,
    check_paths: bool,
    command: str,
    task_id: int,
) -> Tuple[int, int, int]:
    tasks = validate_contiguous_ids(value, "input_data", report)
    if tasks is None:
        return (0, 0, 0)

    total_signal_tracks = 0
    total_bias_tracks = 0
    for task_index in range(len(tasks)):
        label = f'input_data["{task_index}"]'
        task = tasks[str(task_index)]
        if not isinstance(task, dict):
            report.error(f"{label}: expected an object")
            continue

        signal_sources = validate_source_block(
            task, "signal", label, report, check_paths=check_paths
        )
        validate_source_block(task, "loci", label, report, check_paths=check_paths)
        if signal_sources is not None:
            total_signal_tracks += len(signal_sources)

        bias_sources = validate_source_block(
            task,
            "bias",
            label,
            report,
            allow_empty=True,
            check_paths=check_paths,
        )
        bias = task.get("bias")
        if isinstance(bias, dict):
            smoothing = bias.get("smoothing")
            if not isinstance(smoothing, list):
                report.error(f"{label}.bias.smoothing: expected a list")
            elif bias_sources is not None and len(smoothing) != len(bias_sources):
                report.error(
                    f"{label}.bias: source and smoothing lengths differ "
                    f"({len(bias_sources)} != {len(smoothing)})"
                )
            else:
                for index, item in enumerate(smoothing):
                    item_label = f"{label}.bias.smoothing[{index}]"
                    if item is None:
                        continue
                    if not isinstance(item, list) or len(item) != 2:
                        report.error(f"{item_label}: expected null or [sigma, window_width]")
                    elif not is_number(item[0]) or item[0] < 0:
                        report.error(f"{item_label}: sigma must be a non-negative number")
                    elif not isinstance(item[1], int) or isinstance(item[1], bool) or item[1] <= 0:
                        report.error(f"{item_label}: window_width must be a positive integer")
        if bias_sources is not None:
            total_bias_tracks += len(bias_sources)

        if "background_loci" in task:
            background_sources = validate_source_block(
                task,
                "background_loci",
                label,
                report,
                check_paths=check_paths,
            )
            background = task.get("background_loci")
            if isinstance(background, dict):
                ratios = background.get("ratio")
                if not isinstance(ratios, list):
                    report.error(f"{label}.background_loci.ratio: expected a list")
                elif background_sources is not None and len(ratios) != len(background_sources):
                    report.error(
                        f"{label}.background_loci: source and ratio lengths differ "
                        f"({len(background_sources)} != {len(ratios)})"
                    )
                elif any(not is_number(item) or item < 0 for item in ratios):
                    report.error(
                        f"{label}.background_loci.ratio: values must be non-negative numbers"
                    )

    if command == "predict" and not 1 <= total_signal_tracks <= 2:
        report.error(
            "predict: BPNet 2.0.0 requires one or two total signal tracks; "
            f"found {total_signal_tracks}"
        )
    if command == "shap" and not 0 <= task_id < len(tasks):
        report.error(f"shap: task ID {task_id} is outside 0..{len(tasks) - 1}")

    report.note(
        f"input_data: {len(tasks)} task(s), {total_signal_tracks} signal track(s), "
        f"{total_bias_tracks} control track(s)"
    )
    return (len(tasks), total_signal_tracks, total_bias_tracks)


def validate_numeric_list(
    value: Any, label: str, report: Report, *, length: Optional[int] = None
) -> Optional[List[Any]]:
    if not isinstance(value, list) or not value:
        report.error(f"{label}: expected a non-empty list")
        return None
    if length is not None and len(value) != length:
        report.error(f"{label}: expected {length} values, found {len(value)}")
    if any(not is_number(item) for item in value):
        report.error(f"{label}: every entry must be numeric")
        return None
    return value


def validate_model_params(
    value: Any,
    report: Report,
    *,
    num_tasks: int,
    total_bias_tracks: int,
    input_seq_len: Optional[int],
    output_len: Optional[int],
) -> None:
    if not isinstance(value, dict):
        report.error("bpnet_params: expected a JSON object")
        return

    validate_numeric_list(value.get("loss_weights"), "bpnet_params.loss_weights", report, length=2)
    counts_loss = value.get("counts_loss")
    if counts_loss not in {"MSE", "POISSON"}:
        report.error('bpnet_params.counts_loss: expected "MSE" or "POISSON"')

    for key in ("input_len", "output_profile_len"):
        if key in value and (
            not isinstance(value[key], int) or isinstance(value[key], bool) or value[key] <= 0
        ):
            report.error(f"bpnet_params.{key}: expected a positive integer")

    if input_seq_len is not None and value.get("input_len", 2114) != input_seq_len:
        report.error(
            "bpnet_params.input_len does not match --input-seq-len "
            f"({value.get('input_len', 2114)} != {input_seq_len})"
        )
    if output_len is not None and value.get("output_profile_len", 1000) != output_len:
        report.error(
            "bpnet_params.output_profile_len does not match --output-len "
            f"({value.get('output_profile_len', 1000)} != {output_len})"
        )

    motif = value.get("motif_module_params")
    if isinstance(motif, dict):
        filters = motif.get("filters")
        kernels = motif.get("kernel_sizes")
        if isinstance(filters, list) and isinstance(kernels, list) and len(filters) != len(kernels):
            report.error("bpnet_params.motif_module_params: filters and kernel_sizes lengths differ")

    counts_head = value.get("counts_head_params")
    if not isinstance(counts_head, dict):
        report.error("bpnet_params.counts_head_params: expected an object")
    else:
        units = counts_head.get("units")
        if not isinstance(units, list) or not units or any(
            not isinstance(item, int) or isinstance(item, bool) for item in units
        ):
            report.error("bpnet_params.counts_head_params.units: expected a non-empty integer list")
        elif num_tasks and units[-1] not in {-1, num_tasks}:
            report.error(
                "bpnet_params.counts_head_params.units[-1]: expected -1 or task count "
                f"{num_tasks}, found {units[-1]}"
            )
        for key in ("dropouts", "activations"):
            item = counts_head.get(key)
            if isinstance(units, list) and (not isinstance(item, list) or len(item) != len(units)):
                report.error(
                    f"bpnet_params.counts_head_params.{key}: length must match units"
                )

    if total_bias_tracks:
        profile_bias = value.get("profile_bias_module_params")
        kernels = profile_bias.get("kernel_sizes") if isinstance(profile_bias, dict) else None
        if not isinstance(kernels, list) or len(kernels) != num_tasks:
            report.error(
                "bpnet_params.profile_bias_module_params.kernel_sizes: "
                f"expected one value per task ({num_tasks})"
            )

    report.note("bpnet_params: architecture and loss fields checked")


def validate_path_pair(
    split: Dict[str, Any], first: str, second: str, label: str, report: Report, check_paths: bool
) -> None:
    has_first = first in split
    has_second = second in split
    if has_first != has_second:
        report.error(f"{label}: {first} and {second} must be supplied together")
        return
    if not has_first:
        return
    values = [split[first], split[second]]
    if any(not isinstance(item, str) or not item for item in values):
        report.error(f"{label}: {first} and {second} must be non-empty paths")
    elif check_paths:
        check_referenced_paths(values, label, report)


def validate_splits(
    value: Any,
    report: Report,
    *,
    chrom_names: Optional[Set[str]],
    check_paths: bool,
) -> None:
    splits = validate_contiguous_ids(value, "splits", report)
    if splits is None:
        return

    for split_index in range(len(splits)):
        label = f'splits["{split_index}"]'
        split = splits[str(split_index)]
        if not isinstance(split, dict):
            report.error(f"{label}: expected an object")
            continue

        if "val" in split:
            chromosome_sets: Dict[str, Set[str]] = {}
            for key in ("train", "val", "test"):
                if key not in split:
                    continue
                values = validate_string_list(split[key], f"{label}.{key}", report)
                if values is not None:
                    chromosome_sets[key] = set(values)
                    if len(values) != len(chromosome_sets[key]):
                        report.warn(f"{label}.{key}: duplicate chromosomes found")
                    if chrom_names is not None:
                        missing = sorted(chromosome_sets[key] - chrom_names)
                        if missing:
                            report.error(
                                f"{label}.{key}: chromosomes absent from chrom sizes: {missing}"
                            )
            for left, right in (("train", "val"), ("train", "test"), ("val", "test")):
                overlap = sorted(chromosome_sets.get(left, set()) & chromosome_sets.get(right, set()))
                if overlap:
                    report.error(f"{label}: {left}/{right} chromosome leakage: {overlap}")
        elif "loci_val_indices_file" not in split:
            report.error(
                f"{label}: expected chromosome-based 'val' or loci_val_indices_file"
            )

        validate_path_pair(
            split,
            "loci_train_indices_file",
            "loci_val_indices_file",
            label,
            report,
            check_paths,
        )
        validate_path_pair(
            split,
            "background_train_indices_file",
            "background_val_indices_file",
            label,
            report,
            check_paths,
        )

    report.note(f"splits: {len(splits)} split(s) checked")


def validate_chrom_sizes(path: Path, report: Report) -> Optional[Set[str]]:
    if not path.is_file():
        report.error(f"chrom_sizes: file not found: {path}")
        return None
    names: Set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 2:
                report.error(f"chrom_sizes:{line_number}: expected tab-separated chrom and size")
                continue
            chrom = fields[0]
            try:
                size = int(fields[1])
            except ValueError:
                report.error(f"chrom_sizes:{line_number}: size is not an integer")
                continue
            if not chrom or size <= 0:
                report.error(f"chrom_sizes:{line_number}: invalid chromosome name or size")
            if chrom in names:
                report.error(f"chrom_sizes:{line_number}: duplicate chromosome {chrom}")
            names.add(chrom)
    if not names:
        report.error("chrom_sizes: no chromosome rows found")
        return None
    report.note(f"chrom_sizes: {len(names)} chromosome(s) checked")
    return names


def run_self_test() -> int:
    valid_input = {
        "0": {
            "signal": {"source": ["plus.bw", "minus.bw"]},
            "loci": {"source": ["peaks.bed"]},
            "bias": {"source": [], "smoothing": []},
        }
    }
    valid_params = {
        "input_len": 2114,
        "output_profile_len": 1000,
        "counts_head_params": {
            "units": [1],
            "dropouts": [0.0],
            "activations": ["linear"],
        },
        "loss_weights": [1, 42],
        "counts_loss": "MSE",
    }
    valid_splits = {"0": {"train": ["chr1"], "val": ["chr2"], "test": ["chr3"]}}

    report = Report()
    num_tasks, _, bias_tracks = validate_input_data(
        valid_input, report, check_paths=False, command="predict", task_id=0
    )
    validate_model_params(
        valid_params,
        report,
        num_tasks=num_tasks,
        total_bias_tracks=bias_tracks,
        input_seq_len=2114,
        output_len=1000,
    )
    validate_splits(
        valid_splits,
        report,
        chrom_names={"chr1", "chr2", "chr3"},
        check_paths=False,
    )
    if report.errors:
        print("self-test failed: valid fixture was rejected", file=sys.stderr)
        for item in report.errors:
            print(f"  {item}", file=sys.stderr)
        return 1

    invalid = Report()
    validate_input_data(
        {"1": valid_input["0"]}, invalid, check_paths=False, command="train", task_id=0
    )
    validate_splits(
        {"0": {"train": ["chr1"], "val": ["chr1"]}},
        invalid,
        chrom_names={"chr1"},
        check_paths=False,
    )
    if len(invalid.errors) < 2:
        print("self-test failed: invalid fixtures were not rejected", file=sys.stderr)
        return 1
    print("self-test passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate BPNet 2.0.0 input_data, model params, and splits JSON files."
    )
    parser.add_argument("--input-data", type=Path)
    parser.add_argument("--model-params", type=Path)
    parser.add_argument("--splits", type=Path)
    parser.add_argument("--chrom-sizes", type=Path)
    parser.add_argument("--reference-genome", type=Path)
    parser.add_argument("--command", choices=("train", "predict", "shap"), default="train")
    parser.add_argument("--input-seq-len", type=int)
    parser.add_argument("--output-len", type=int)
    parser.add_argument("--output-window-size", type=int)
    parser.add_argument("--task-id", type=int, default=0)
    parser.add_argument(
        "--check-paths",
        action="store_true",
        help="Check signal, loci, control, background, and index paths from JSON files.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON report.")
    parser.add_argument("--self-test", action="store_true", help=argparse.SUPPRESS)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.self_test:
        return run_self_test()
    if args.input_data is None:
        print("error: --input-data is required", file=sys.stderr)
        return 2

    report = Report()
    chrom_names = validate_chrom_sizes(args.chrom_sizes, report) if args.chrom_sizes else None

    if args.reference_genome is not None:
        if not args.reference_genome.is_file():
            report.error(f"reference_genome: file not found: {args.reference_genome}")
        else:
            report.note("reference_genome: file exists")

    input_data = load_json(args.input_data, "input_data", report)
    num_tasks = 0
    total_bias_tracks = 0
    if input_data is not None:
        num_tasks, _, total_bias_tracks = validate_input_data(
            input_data,
            report,
            check_paths=args.check_paths,
            command=args.command,
            task_id=args.task_id,
        )

    if args.model_params is not None:
        params = load_json(args.model_params, "bpnet_params", report)
        if params is not None:
            validate_model_params(
                params,
                report,
                num_tasks=num_tasks,
                total_bias_tracks=total_bias_tracks,
                input_seq_len=args.input_seq_len,
                output_len=args.output_len,
            )
    elif args.command == "train":
        report.warn("train: --model-params was not supplied")

    if args.splits is not None:
        splits = load_json(args.splits, "splits", report)
        if splits is not None:
            validate_splits(
                splits,
                report,
                chrom_names=chrom_names,
                check_paths=args.check_paths,
            )
    elif args.command == "train":
        report.warn("train: --splits was not supplied")

    if args.output_window_size is not None:
        if args.output_window_size <= 0:
            report.error("--output-window-size must be positive")
        if args.output_len is None:
            report.warn("--output-window-size supplied without --output-len")
        elif args.output_window_size > args.output_len:
            report.error("--output-window-size must be <= --output-len")

    payload = report.as_dict()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for item in report.notes:
            print(f"ok: {item}")
        for item in report.warnings:
            print(f"warning: {item}", file=sys.stderr)
        for item in report.errors:
            print(f"error: {item}", file=sys.stderr)
        print(
            f"validation {'passed' if payload['valid'] else 'failed'}: "
            f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)"
        )
    return 0 if payload["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
