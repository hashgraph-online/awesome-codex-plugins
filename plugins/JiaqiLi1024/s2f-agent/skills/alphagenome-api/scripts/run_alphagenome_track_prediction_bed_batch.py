#!/usr/bin/env python3
"""Batch AlphaGenome interval track prediction for BED or single interval."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

import numpy as np

DEFAULT_PROXY_URL = "http://127.0.0.1:7890"
PROXY_ENV_KEYS = ("grpc_proxy", "http_proxy", "https_proxy")
SUPPORTED_WIDTHS = (16_384, 131_072, 524_288, 1_048_576)


def log(msg: str) -> None:
    print(msg, flush=True)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_env_file(env_path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not env_path.exists():
        return data
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip("'").strip('"')
    return data


def load_api_key(repo_root: Path) -> str:
    env_path = repo_root / ".env"
    if env_path.exists():
        env_map = parse_env_file(env_path)
        if "ALPHAGENOME_API_KEY" in env_map and not os.environ.get("ALPHAGENOME_API_KEY"):
            os.environ["ALPHAGENOME_API_KEY"] = env_map["ALPHAGENOME_API_KEY"]
    api_key = os.environ.get("ALPHAGENOME_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ALPHAGENOME_API_KEY not found in environment or .env")
    return api_key


def ensure_alphagenome_installed() -> None:
    try:
        import alphagenome  # noqa: F401
        return
    except ImportError:
        pass
    log("[INFO] Installing alphagenome...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "alphagenome"])


def has_proxy_env() -> bool:
    return any(os.environ.get(key, "").strip() for key in PROXY_ENV_KEYS)


def set_proxy_env(proxy_url: str) -> None:
    for key in PROXY_ENV_KEYS:
        os.environ[key] = proxy_url


def create_client_with_retry(dna_client, api_key: str, timeout: float, proxy_url: str | None):
    import grpc

    try:
        model = dna_client.create(api_key, timeout=timeout)
        log("[INFO] AlphaGenome client created")
        return model
    except grpc.FutureTimeoutError:
        if not proxy_url:
            raise
        if has_proxy_env():
            raise
        log(
            f"[WARN] dna_client.create timed out after {timeout}s; "
            f"retrying with proxy vars = {proxy_url}"
        )
        set_proxy_env(proxy_url)
        model = dna_client.create(api_key, timeout=timeout)
        log("[INFO] AlphaGenome client created (proxy retry)")
        return model


def parse_bed(bed_path: Path, limit: int | None) -> list[dict]:
    rows: list[dict] = []
    with bed_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            text = line.strip()
            if not text or text.startswith("#") or text.startswith("track ") or text.startswith("browser "):
                continue
            parts = text.split()
            if len(parts) < 3:
                continue
            chrom = parts[0]
            if not chrom.startswith("chr"):
                chrom = f"chr{chrom}"
            start = int(parts[1])
            end = int(parts[2])
            if start < 0 or end <= start:
                raise ValueError(f"Invalid BED interval: {text}")
            name = parts[3] if len(parts) >= 4 else f"{chrom}:{start}-{end}"
            rows.append(
                {
                    "chrom": chrom,
                    "start": start,
                    "end": end,
                    "name": name,
                }
            )
            if limit is not None and len(rows) >= limit:
                break
    if not rows:
        raise ValueError(f"No valid intervals found in BED: {bed_path}")
    return rows


def parse_interval_spec(interval_spec: str) -> dict:
    text = interval_spec.strip()
    if ":" not in text or "-" not in text:
        raise ValueError(f"Invalid --interval format: {interval_spec} (expected chr:start-end)")
    chrom, rest = text.split(":", 1)
    start_raw, end_raw = rest.split("-", 1)
    start = int(start_raw.replace(",", "").replace("_", ""))
    end = int(end_raw.replace(",", "").replace("_", ""))
    if not chrom.startswith("chr"):
        chrom = f"chr{chrom}"
    if start < 0 or end <= start:
        raise ValueError(f"Invalid interval (0-based half-open expected): {interval_spec}")
    return {
        "chrom": chrom,
        "start": start,
        "end": end,
        "name": f"{chrom}:{start}-{end}",
    }


def choose_inference_window(start: int, end: int, width_override: int | None) -> tuple[int, int, int]:
    target_width = end - start
    if width_override is not None:
        if width_override not in SUPPORTED_WIDTHS:
            raise ValueError(
                f"interval_width must be one of {list(SUPPORTED_WIDTHS)}, got {width_override}"
            )
        inf_width = width_override
    else:
        inf_width = -1
        for width in SUPPORTED_WIDTHS:
            if target_width <= width:
                inf_width = width
                break
        if inf_width < 0:
            raise ValueError(
                f"Interval width {target_width} exceeds AlphaGenome limit (max {SUPPORTED_WIDTHS[-1]})."
            )

    center = (start + end) // 2
    inf_start = max(0, center - (inf_width // 2))
    inf_end = inf_start + inf_width
    return inf_start, inf_end, inf_width


def run_batch(
    bed_rows: list[dict],
    *,
    species: str,
    assembly: str,
    bed_path: str | None,
    input_mode: str,
    output_dir: Path,
    output_prefix: str,
    output_head: str,
    ontology_terms: list[str],
    interval_width: int | None,
    api_key: str,
    timeout: float,
    delay: float,
    proxy_url: str | None,
) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from alphagenome.data import genome
    from alphagenome.models import dna_client
    from alphagenome.visualization import plot_components

    output_dir.mkdir(parents=True, exist_ok=True)

    output_type = getattr(dna_client.OutputType, output_head, None)
    if output_type is None:
        raise ValueError(f"Unsupported output head: {output_head}")

    output_attr = output_head.lower()
    organism = {
        "human": dna_client.Organism.HOMO_SAPIENS,
        "mouse": dna_client.Organism.MUS_MUSCULUS,
    }[species]

    model = create_client_with_retry(
        dna_client=dna_client,
        api_key=api_key,
        timeout=timeout,
        proxy_url=proxy_url,
    )

    summary_rows: list[dict] = []
    for idx, row in enumerate(bed_rows, start=1):
        chrom = row["chrom"]
        start = int(row["start"])
        end = int(row["end"])
        name = str(row["name"])
        requested_width = end - start

        inf_start = None
        inf_end = None
        inf_width = None
        status = "running"
        error = None
        track_shape = None
        num_tracks = None
        track_resolution = None
        plot_path = None
        npz_path = None

        prefix = f"{output_prefix}_{chrom}_{start}_{end}"
        result_json = output_dir / f"{prefix}_result.json"
        plot_file = output_dir / f"{prefix}_trackplot.png"
        npz_file = output_dir / f"{prefix}_track_prediction.npz"

        try:
            inf_start, inf_end, inf_width = choose_inference_window(start, end, interval_width)
            inference_interval = genome.Interval(chromosome=chrom, start=inf_start, end=inf_end)
            requested_interval = genome.Interval(chromosome=chrom, start=start, end=end)

            outputs = model.predict_interval(
                interval=inference_interval,
                organism=organism,
                requested_outputs=[output_type],
                ontology_terms=ontology_terms,
            )

            track_data = getattr(outputs, output_attr, None)
            if track_data is None:
                raise RuntimeError(f"predict_interval returned no data for {output_head}")

            requested_track_data = track_data.slice_by_interval(requested_interval)
            track_values = requested_track_data.values
            track_shape = list(track_values.shape)
            num_tracks = int(requested_track_data.num_tracks)
            track_resolution = int(requested_track_data.resolution)

            names = []
            strands = []
            if "name" in requested_track_data.metadata.columns:
                names = [str(x) for x in requested_track_data.metadata["name"].values.tolist()]
            if "strand" in requested_track_data.metadata.columns:
                strands = [str(x) for x in requested_track_data.metadata["strand"].values.tolist()]

            np.savez_compressed(
                npz_file,
                preds=track_values,
                preds_inference_window=track_data.values,
                track_names=np.array(names, dtype=object),
                track_strands=np.array(strands, dtype=object),
                resolution=np.array([track_resolution], dtype=np.int32),
                requested_start=np.array([start], dtype=np.int64),
                requested_end=np.array([end], dtype=np.int64),
                inference_start=np.array([inf_start], dtype=np.int64),
                inference_end=np.array([inf_end], dtype=np.int64),
            )

            fig = plot_components.plot(
                [
                    plot_components.OverlaidTracks(
                        tdata={output_head: requested_track_data},
                        colors={output_head: "royalblue"},
                    ),
                ],
                interval=requested_track_data.interval,
                title=f"AlphaGenome {output_head} {chrom}:{start}-{end}",
            )
            fig.savefig(plot_file, dpi=200, bbox_inches="tight")
            plt.close(fig)

            plot_path = str(plot_file.resolve())
            npz_path = str(npz_file.resolve())
            status = "success"
        except Exception as exc:  # pragma: no cover - runtime robustness
            status = "failed"
            error = f"{type(exc).__name__}: {exc}"
        finally:
            payload = {
                "skill_id": "alphagenome-api",
                "task": "track-prediction",
                "application_mode": f"predict_interval-{input_mode}",
                "run_time_utc": utc_now_iso(),
                "status": status,
                "error": error,
                "assembly": assembly,
                "species": species,
                "output_head": output_head,
                "ontology_terms": ontology_terms,
                "bed_name": name,
                "interval_name": name,
                "chrom": chrom,
                "requested_interval": [start, end],
                "requested_width": requested_width,
                "inference_interval": [inf_start, inf_end] if inf_start is not None else None,
                "inference_width": inf_width,
                "track_shape": track_shape,
                "num_tracks": num_tracks,
                "track_resolution": track_resolution,
                "plot_path": plot_path,
                "npz_path": npz_path,
                "summary_path": str(result_json.resolve()),
                "outputs": {
                    "plot": plot_path,
                    "npz": npz_path,
                    "result_json": str(result_json.resolve()),
                },
            }
            result_json.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            summary_rows.append(payload)
            log(
                f"[INFO] progress={idx}/{len(bed_rows)} "
                f"status={status} interval={chrom}:{start}-{end}"
            )
            if delay > 0:
                time.sleep(delay)

    success_count = sum(1 for r in summary_rows if r["status"] == "success")
    failed_count = len(summary_rows) - success_count
    summary = {
        "status": "completed" if failed_count == 0 else "completed_with_failures",
        "task": "track-prediction",
        "application_mode": f"predict_interval-{input_mode}",
        "generated_at_utc": utc_now_iso(),
        "total_intervals": len(summary_rows),
        "succeeded_count": success_count,
        "failed_count": failed_count,
        "species": species,
        "assembly": assembly,
        "bed_path": bed_path,
        "output_head": output_head,
        "ontology_terms": ontology_terms,
        "output_dir": str(output_dir.resolve()),
        "results": summary_rows,
    }
    summary_path = output_dir / f"{output_prefix}_bed_batch_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return summary_path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Batch AlphaGenome interval track prediction")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--bed", help="BED file with intervals (0-based half-open).")
    src.add_argument("--interval", help="Single interval (0-based half-open), format: chr:start-end")
    p.add_argument("--species", choices=("human", "mouse"), default="human", help="Species, default: human")
    p.add_argument("--assembly", default="hg38", help="Assembly label, default: hg38")
    p.add_argument("--output-dir", default="output/alphagenome_track", help="Output directory")
    p.add_argument("--output-prefix", default="alphagenome_track", help="Output prefix")
    p.add_argument("--output-head", default="RNA_SEQ", help="AlphaGenome output head (default: RNA_SEQ)")
    p.add_argument(
        "--ontology-term",
        action="append",
        default=None,
        help="Ontology term. Repeatable. Default: UBERON:0001157",
    )
    p.add_argument(
        "--interval-width",
        type=int,
        default=None,
        help="Force inference interval width (16384/131072/524288/1048576).",
    )
    p.add_argument("--limit", type=int, default=None, help="Optional max number of BED rows")
    p.add_argument("--delay", type=float, default=0.0, help="Delay seconds between intervals")
    p.add_argument("--request-timeout-sec", type=float, default=120.0, help="Client timeout in seconds")
    p.add_argument(
        "--proxy-url",
        default=os.environ.get("ALPHAGENOME_PROXY_URL", DEFAULT_PROXY_URL),
        help=(
            "Proxy URL for retry when dna_client.create times out "
            "(default: env ALPHAGENOME_PROXY_URL or http://127.0.0.1:7890). "
            "Set empty string to disable."
        ),
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    input_mode = "bed-batch"
    bed_path_for_summary: str | None = None
    if args.bed:
        bed_path = Path(args.bed).resolve()
        if not bed_path.exists():
            raise FileNotFoundError(f"BED file not found: {bed_path}")
        rows = parse_bed(bed_path, args.limit)
        bed_path_for_summary = str(bed_path)
    else:
        rows = [parse_interval_spec(args.interval)]
        input_mode = "single-interval"

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent.parent.parent

    ensure_alphagenome_installed()
    log(f"[INFO] alphagenome version: {metadata.version('alphagenome')}")
    api_key = load_api_key(repo_root)
    ontology_terms = args.ontology_term if args.ontology_term else ["UBERON:0001157"]
    proxy_url = args.proxy_url if args.proxy_url.strip() else None

    summary_path = run_batch(
        rows,
        species=args.species,
        assembly=args.assembly,
        bed_path=bed_path_for_summary,
        input_mode=input_mode,
        output_dir=output_dir,
        output_prefix=args.output_prefix,
        output_head=args.output_head,
        ontology_terms=ontology_terms,
        interval_width=args.interval_width,
        api_key=api_key,
        timeout=args.request_timeout_sec,
        delay=args.delay,
        proxy_url=proxy_url,
    )
    log(f"[INFO] Intervals: {len(rows)}")
    log(f"[INFO] Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
