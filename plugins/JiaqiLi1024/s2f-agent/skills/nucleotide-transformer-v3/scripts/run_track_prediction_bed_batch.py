#!/usr/bin/env python3
"""Run NTv3 track prediction for all intervals in a BED file."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Batch NTv3 post-trained track prediction for BED intervals. "
            "Continues on per-interval failures and writes a summary JSON."
        )
    )
    parser.add_argument("--bed", required=True, help="Input BED file path (chrom start end).")
    parser.add_argument(
        "--model",
        default="InstaDeepAI/NTv3_100M_post",
        help="Hugging Face model id. Default: InstaDeepAI/NTv3_100M_post",
    )
    parser.add_argument("--species", default="human", help="Species condition token.")
    parser.add_argument("--assembly", default="hg38", help="Genome assembly.")
    parser.add_argument(
        "--hf-token",
        default=None,
        help="Optional Hugging Face token override; forwarded to single-interval runner.",
    )
    parser.add_argument(
        "--output-dir",
        default="output/ntv3_results",
        help="Directory for per-interval outputs and batch summary.",
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda", "mps"],
        default="auto",
        help="Inference device forwarded to single-interval runner. Default: auto.",
    )
    parser.add_argument(
        "--dtype",
        choices=["auto", "float32", "float16", "bfloat16"],
        default="auto",
        help="Inference dtype forwarded to single-interval runner. Default: auto.",
    )
    parser.add_argument(
        "--save-npz",
        action="store_true",
        help="Forward --save-npz to single-interval runs.",
    )
    return parser.parse_args()


def run_with_live_log(cmd: list[str], log_path: Path, append: bool) -> int:
    mode = "a" if append else "w"
    with log_path.open(mode, encoding="utf-8") as log_f:
        log_f.write(f"$ {shlex.join(cmd)}\n")
        log_f.flush()

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        if proc.stdout is not None:
            for line in proc.stdout:
                print(line, end="")
                log_f.write(line)
        ret = proc.wait()
        log_f.write(f"[exit_code] {ret}\n")
        log_f.flush()
    return ret


def build_single_interval_cmd(
    single_runner: Path,
    model: str,
    species: str,
    assembly: str,
    interval: str,
    output_dir: Path,
    hf_token: str | None,
    device: str,
    dtype: str,
    disable_xet: bool,
    save_npz: bool,
) -> list[str]:
    cmd = [
        sys.executable,
        str(single_runner),
        "--model",
        model,
        "--species",
        species,
        "--assembly",
        assembly,
        "--interval",
        interval,
        "--output-dir",
        str(output_dir),
        "--device",
        device,
        "--dtype",
        dtype,
    ]
    if hf_token:
        cmd.extend(["--hf-token", hf_token])
    if disable_xet:
        cmd.append("--disable-xet")
    if save_npz:
        cmd.append("--save-npz")
    return cmd


def main() -> int:
    args = parse_args()
    bed_path = Path(args.bed).expanduser()
    if not bed_path.is_absolute():
        bed_path = (Path.cwd() / bed_path).resolve()
    else:
        bed_path = bed_path.resolve()
    if not bed_path.exists():
        raise SystemExit(f"BED file not found: {bed_path}")

    output_dir = Path(args.output_dir).expanduser()
    if not output_dir.is_absolute():
        output_dir = (Path.cwd() / output_dir).resolve()
    else:
        output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    single_runner = Path(__file__).with_name("run_track_prediction.py")
    if not single_runner.exists():
        raise SystemExit(f"Single-interval runner not found: {single_runner}")

    total_rows = 0
    valid_intervals: list[tuple[str, int, int]] = []
    failures: list[dict[str, object]] = []

    for line_no, raw in enumerate(bed_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        total_rows += 1
        parts = stripped.split()
        if len(parts) < 3:
            failures.append(
                {
                    "line_no": line_no,
                    "raw_line": raw,
                    "reason": "invalid-bed-row",
                    "detail": "Expected at least 3 columns: chrom start end.",
                }
            )
            continue

        chrom = parts[0]
        try:
            start = int(parts[1])
            end = int(parts[2])
        except ValueError:
            failures.append(
                {
                    "line_no": line_no,
                    "raw_line": raw,
                    "reason": "invalid-coordinate",
                    "detail": "Start/end must be integers.",
                }
            )
            continue

        if end <= start:
            failures.append(
                {
                    "line_no": line_no,
                    "raw_line": raw,
                    "reason": "invalid-interval",
                    "detail": "End must be greater than start.",
                }
            )
            continue

        valid_intervals.append((chrom, start, end))

    successes: list[dict[str, object]] = []
    total_to_run = len(valid_intervals)
    for idx, (chrom, start, end) in enumerate(valid_intervals, start=1):
        interval = f"{chrom}:{start}-{end}"
        interval_log = output_dir / f"ntv3_{chrom}_{start}_{end}.log"
        prefix = f"ntv3_{args.species}_{args.assembly}_{chrom}_{start}_{end}"
        plot_path = output_dir / f"{prefix}_trackplot.png"
        result_path = output_dir / f"{prefix}_result.json"

        print(f"[RUN {idx}/{total_to_run}] {interval}", flush=True)
        cmd = build_single_interval_cmd(
            single_runner=single_runner,
            model=args.model,
            species=args.species,
            assembly=args.assembly,
            interval=interval,
            output_dir=output_dir,
            hf_token=args.hf_token,
            device=args.device,
            dtype=args.dtype,
            disable_xet=False,
            save_npz=args.save_npz,
        )
        first_code = run_with_live_log(cmd, interval_log, append=False)
        final_code = first_code
        retry_used = False

        if first_code != 0:
            retry_used = True
            print(f"[RETRY] {interval} with --disable-xet", flush=True)
            retry_cmd = build_single_interval_cmd(
                single_runner=single_runner,
                model=args.model,
                species=args.species,
                assembly=args.assembly,
                interval=interval,
                output_dir=output_dir,
                hf_token=args.hf_token,
                device=args.device,
                dtype=args.dtype,
                disable_xet=True,
                save_npz=args.save_npz,
            )
            final_code = run_with_live_log(retry_cmd, interval_log, append=True)

        outputs_ok = plot_path.exists() and result_path.exists() and interval_log.exists()
        if final_code == 0 and outputs_ok:
            successes.append(
                {
                    "interval": interval,
                    "chrom": chrom,
                    "start": start,
                    "end": end,
                    "retry_used": retry_used,
                    "outputs": {
                        "plot": str(plot_path),
                        "result_json": str(result_path),
                        "log": str(interval_log),
                    },
                }
            )
            print(f"[OK] {interval}", flush=True)
            continue

        detail = "single-run-failed"
        if final_code == 0 and not outputs_ok:
            detail = "missing-expected-output-files"
        failures.append(
            {
                "interval": interval,
                "chrom": chrom,
                "start": start,
                "end": end,
                "retry_used": retry_used,
                "first_exit_code": first_code,
                "final_exit_code": final_code,
                "reason": detail,
                "outputs_present": {
                    "plot": plot_path.exists(),
                    "result_json": result_path.exists(),
                    "log": interval_log.exists(),
                },
                "log_path": str(interval_log),
            }
        )
        print(f"[FAIL] {interval}", flush=True)

    summary = {
        "skill_id": "nucleotide-transformer-v3",
        "task": "track-prediction-batch",
        "coordinate_convention": "[start, end) zero-based",
        "model_name": args.model,
        "species": args.species,
        "assembly": args.assembly,
        "bed_path": str(bed_path),
        "output_dir": str(output_dir),
        "total_rows_considered": total_rows,
        "total_intervals": len(successes) + len(failures),
        "succeeded_count": len(successes),
        "failed_count": len(failures),
        "succeeded": successes,
        "failed": failures,
        "exit_code_policy": "always-zero-even-with-partial-failures",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    summary_path = output_dir / "ntv3_bed_batch_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"[SUMMARY] succeeded={len(successes)} failed={len(failures)}", flush=True)
    print(f"[SUMMARY] summary_json={summary_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
