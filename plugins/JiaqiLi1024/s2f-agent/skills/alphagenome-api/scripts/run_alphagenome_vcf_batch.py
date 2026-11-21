#!/usr/bin/env python3
"""Batch AlphaGenome variant-effect prediction for VCF input.

Input: standard VCF (CHROM without 'chr', POS 1-based, REF, ALT)
Outputs per tissue: {tissue}_mean_diff, {tissue}_log2fc
Final output: output/alphagenome/case-study/<vcf_stem>_tissues.tsv
"""

from __future__ import annotations

DEFAULT_TISSUE_DICT = {
    'Neuronal_stem_cell': 'CL:0000047',
    'Skeletal_Muscle':    'UBERON:0011907',
    'Whole_Blood':        'UBERON:0013756',
    'Endothelial_cell':   'CL:0000115',
    'Lung':               'UBERON:0002048',
    'Liver':              'UBERON:0002107',
    'Visceral_Adipose':   'UBERON:0010414',
    'Skin':               'UBERON:0036149',
}

import argparse
import csv
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

DEFAULT_PROXY_URL = "http://127.0.0.1:7890"
PROXY_ENV_KEYS = ("grpc_proxy", "http_proxy", "https_proxy")
TRANSIENT_API_ERROR_TOKENS = (
    "StatusCode.UNAVAILABLE",
    "StatusCode.DEADLINE_EXCEEDED",
    "StatusCode.RESOURCE_EXHAUSTED",
    "FD shutdown",
    "failed to connect to all addresses",
    "grpc_status:14",
)


class TransientAlphaGenomeApiError(RuntimeError):
    """Raised when AlphaGenome API stayed unavailable after retries."""


def load_tissue_dict(tissues_arg: str | None) -> dict[str, str]:
    """Return tissue dict from --tissues argument or interactive confirmation.

    --tissues accepts:
      - path to a JSON file: {"name": "ontology_curie", ...}
      - inline JSON string: same format
      - omitted: prompt user to confirm or customise DEFAULT_TISSUE_DICT
    """
    if tissues_arg:
        # Try as file path first, then inline JSON
        p = Path(tissues_arg)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return json.loads(tissues_arg)

    # Interactive confirmation
    print("\n[TISSUE CONFIG] Default tissues:")
    for i, (name, curie) in enumerate(DEFAULT_TISSUE_DICT.items(), 1):
        print(f"  {i:2d}. {name:<25} {curie}")
    print()
    choice = input("Use default tissues? [Y/n/path-to-json]: ").strip()
    if choice.lower() in ("", "y", "yes"):
        return DEFAULT_TISSUE_DICT.copy()
    p = Path(choice)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    # Try inline JSON
    try:
        return json.loads(choice)
    except json.JSONDecodeError:
        print("[WARN] Could not parse input, using default tissues.")
        return DEFAULT_TISSUE_DICT.copy()


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


def _has_proxy_env() -> bool:
    return any(os.environ.get(key, "").strip() for key in PROXY_ENV_KEYS)


def _set_proxy_env(proxy_url: str) -> None:
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
        if _has_proxy_env():
            raise
        log(
            f"[WARN] dna_client.create timed out after {timeout}s; "
            f"retrying with proxy vars = {proxy_url}"
        )
        _set_proxy_env(proxy_url)
        model = dna_client.create(api_key, timeout=timeout)
        log("[INFO] AlphaGenome client created (proxy retry)")
        return model


def create_client_resilient(
    dna_client,
    api_key: str,
    timeout: float,
    proxy_url: str | None,
    max_retries: int,
    retry_base_delay: float,
    retry_max_delay: float,
):
    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 2):
        try:
            return create_client_with_retry(dna_client, api_key, timeout, proxy_url)
        except Exception as exc:
            last_exc = exc
            if not is_transient_api_error(exc) and type(exc).__name__ != "FutureTimeoutError":
                raise
            if attempt > max_retries:
                raise
            sleep_for = retry_sleep_seconds(attempt, retry_base_delay, retry_max_delay)
            log(
                f"[RETRY] AlphaGenome client create transient error "
                f"({attempt}/{max_retries}); sleeping {sleep_for:.1f}s: {brief_error(exc)}"
            )
            time.sleep(sleep_for)
    raise TransientAlphaGenomeApiError(f"exhausted client-create retries: {last_exc}")


def is_transient_api_error(exc: Exception) -> bool:
    text = f"{type(exc).__name__}: {exc}"
    return any(token in text for token in TRANSIENT_API_ERROR_TOKENS)


def brief_error(exc: Exception, limit: int = 240) -> str:
    text = " ".join(f"{type(exc).__name__}: {exc}".split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def retry_sleep_seconds(attempt: int, base: float, max_delay: float) -> float:
    delay = min(max_delay, base * (2 ** max(0, attempt - 1)))
    return delay + random.uniform(0.0, min(1.0, delay * 0.1))


SUPPORTED_WIDTHS = {16_384, 131_072, 524_288, 1_048_576}


def build_interval(position_1based: int, width: int = 16_384) -> tuple[int, int]:
    if width not in SUPPORTED_WIDTHS:
        raise ValueError(f"interval_width must be one of {sorted(SUPPORTED_WIDTHS)}, got {width}")
    start = max(0, position_1based - (width // 2))
    return start, start + width


def _vtype(ref: str, alt: str) -> str:
    if len(ref) == 1 and len(alt) == 1:
        return "SNP"
    elif len(alt) > len(ref):
        return "INS"
    elif len(alt) < len(ref):
        return "DEL"
    return "MNP"


def _parse_info(info_str: str) -> dict[str, str]:
    result: dict[str, str] = {}
    if info_str in (".", ""):
        return result
    for field in info_str.split(";"):
        if "=" in field:
            k, v = field.split("=", 1)
            result[k] = v
        elif field:
            result[field] = "true"
    return result


def _iter_vcf_records(vcf_path: Path):
    """Yield parsed record dicts for every non-header VCF line."""
    with open(vcf_path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 5:
                continue
            chrom_raw = parts[0].strip()
            chrom = chrom_raw if chrom_raw.startswith("chr") else f"chr{chrom_raw}"
            position = int(parts[1])
            vid = parts[2].strip() if len(parts) > 2 else "."
            ref = parts[3].strip().upper()
            # Take only the first ALT allele if multi-allelic
            alt = parts[4].strip().upper().split(",")[0]
            info = _parse_info(parts[7]) if len(parts) > 7 else {}
            yield {
                "vid": vid,
                "chrom": chrom,
                "position": position,
                "ref": ref,
                "alt": alt,
                "variant_type": _vtype(ref, alt),
                "info": info,
            }


def load_vcf(vcf_path: Path) -> tuple[list[dict], list[str]]:
    """Return (variants, sorted_info_keys) after two passes over the VCF."""
    all_info_keys: set[str] = set()
    records = list(_iter_vcf_records(vcf_path))
    for r in records:
        all_info_keys.update(r["info"].keys())
    return records, sorted(all_info_keys)


def run_batch(
    variants: list[dict],
    info_keys: list[str],
    tissue_dict: dict[str, str],
    assembly: str,
    interval_width: int,
    output_dir: Path,
    output_name: str,
    api_key: str,
    timeout: float,
    delay: float,
    resume: bool,
    proxy_url: str | None,
    max_retries: int,
    retry_base_delay: float,
    retry_max_delay: float,
) -> list[dict]:
    import numpy as np
    from alphagenome.data import genome
    from alphagenome.models import dna_client

    tissue_names = list(tissue_dict.keys())
    all_ontology_terms = list(tissue_dict.values())

    done_path = output_dir / output_name
    done_keys: set[str] = set()
    if resume and done_path.exists():
        with open(done_path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                status = (r.get("status") or "").strip().lower()
                if status == "success":
                    done_keys.add(f"{r['chrom']}:{r['position']}:{r['ref']}>{r['alt']}")
        log(f"[INFO] Resuming: {len(done_keys)} already successful")

    tissue_fields = []
    for t in tissue_names:
        tissue_fields += [f"{t}_mean_diff", f"{t}_log2fc"]
    fields = (["vid", "chrom", "position", "ref", "alt", "variant_type",
               "assembly", "interval_start", "interval_end"]
              + info_keys + tissue_fields
              + ["status", "error", "run_time_utc"])

    write_header = not (resume and done_path.exists())
    tsv_fh = open(done_path, "a" if resume else "w", newline="", encoding="utf-8")
    writer = csv.DictWriter(tsv_fh, fieldnames=fields, delimiter="\t", extrasaction="ignore")
    if write_header:
        writer.writeheader()

    summaries: list[dict] = []
    total = len(variants)
    succeeded = 0
    failed = 0

    try:
        model = create_client_resilient(
            dna_client,
            api_key,
            timeout,
            proxy_url,
            max_retries,
            retry_base_delay,
            retry_max_delay,
        )
        log(f"[INFO] Tissues: {tissue_names}")

        for i, v in enumerate(variants):
            key = f"{v['chrom']}:{v['position']}:{v['ref']}>{v['alt']}"
            if key in done_keys:
                continue

            row: dict = {
                "vid": v["vid"],
                "chrom": v["chrom"],
                "position": v["position"],
                "ref": v["ref"],
                "alt": v["alt"],
                "variant_type": v["variant_type"],
                "assembly": assembly,
                "interval_start": None,
                "interval_end": None,
                "status": "running",
                "error": None,
                "run_time_utc": utc_now_iso(),
            }
            for k in info_keys:
                row[k] = v["info"].get(k, ".")
            for t in tissue_names:
                row[f"{t}_mean_diff"] = None
                row[f"{t}_log2fc"] = None

            try:
                interval_start, interval_end = build_interval(v["position"], width=interval_width)
                row["interval_start"] = interval_start
                row["interval_end"] = interval_end

                interval = genome.Interval(
                    chromosome=v["chrom"],
                    start=interval_start,
                    end=interval_end,
                )
                variant = genome.Variant(
                    chromosome=v["chrom"],
                    position=v["position"],
                    reference_bases=v["ref"],
                    alternate_bases=v["alt"],
                )
                last_exc: Exception | None = None
                for attempt in range(1, max_retries + 2):
                    try:
                        outputs = model.predict_variant(
                            interval=interval,
                            variant=variant,
                            requested_outputs=[dna_client.OutputType.RNA_SEQ],
                            ontology_terms=all_ontology_terms,
                        )
                        break
                    except Exception as exc:
                        last_exc = exc
                        if not is_transient_api_error(exc) or attempt > max_retries:
                            raise
                        sleep_for = retry_sleep_seconds(attempt, retry_base_delay, retry_max_delay)
                        log(
                            f"[RETRY] {key}: transient AlphaGenome API error "
                            f"({attempt}/{max_retries}); sleeping {sleep_for:.1f}s: {brief_error(exc)}"
                        )
                        time.sleep(sleep_for)
                        model = create_client_resilient(
                            dna_client,
                            api_key,
                            timeout,
                            proxy_url,
                            max_retries,
                            retry_base_delay,
                            retry_max_delay,
                        )
                else:
                    raise TransientAlphaGenomeApiError(f"exhausted retries: {last_exc}")
                if outputs.reference.rna_seq is None or outputs.alternate.rna_seq is None:
                    raise RuntimeError("RNA_SEQ output missing")

                ref_td = outputs.reference.rna_seq
                alt_td = outputs.alternate.rna_seq
                track_curies = ref_td.metadata['ontology_curie'].values

                for t_name, t_curie in tissue_dict.items():
                    mask = track_curies == t_curie
                    if not mask.any():
                        continue
                    ref_vals = ref_td.values[:, mask].astype(float)
                    alt_vals = alt_td.values[:, mask].astype(float)
                    mean_diff = float(np.mean(alt_vals - ref_vals))
                    log2fc = float(np.mean(np.log2((alt_vals + 1.0) / (ref_vals + 1.0))))
                    row[f"{t_name}_mean_diff"] = round(mean_diff, 6)
                    row[f"{t_name}_log2fc"] = round(log2fc, 6)

                row["status"] = "success"
                succeeded += 1
                log(f"[OK] {key}")

            except Exception as exc:
                row["status"] = "failed"
                row["error"] = f"{type(exc).__name__}: {exc}"
                failed += 1
                log(f"[WARN] {key}: {exc}")

            row["run_time_utc"] = utc_now_iso()
            writer.writerow(row)
            tsv_fh.flush()
            summaries.append(row)

            if (i + 1) % 50 == 0:
                log(f"[INFO] Progress: {i+1}/{total} | success={succeeded} failed={failed}")

            if delay > 0:
                time.sleep(delay)

    finally:
        tsv_fh.close()

    return summaries


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Batch AlphaGenome SNP variant-effect prediction from VCF")
    p.add_argument("--input", default="case-study-playbooks/variant-effect/vcf/Test.geuvadis.vcf")
    p.add_argument("--assembly", default="hg19",
                   help="Genome assembly (default: hg19 for GEUVADIS)")
    p.add_argument("--output-dir", default="output/alphagenome/case-study")
    p.add_argument("--request-timeout-sec", type=float, default=120.0)
    p.add_argument("--delay", type=float, default=0.0)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--limit", type=int, default=0,
                   help="Process only first N variants (0 = all)")
    p.add_argument("--interval-width", type=int, default=16_384,
                   choices=sorted(SUPPORTED_WIDTHS),
                   help="Prediction interval width in bp (default: 16384)")
    p.add_argument("--tissues", default=None,
                   help="Tissue config: path to JSON file or inline JSON {name: ontology_curie}. "
                        "Omit to confirm interactively.")
    p.add_argument("--non-interactive", action="store_true",
                   help="Use default tissues without interactive prompt")
    p.add_argument(
        "--proxy-url",
        default=os.environ.get("ALPHAGENOME_PROXY_URL", DEFAULT_PROXY_URL),
        help=(
            "Proxy URL for one automatic retry when dna_client.create times out "
            "(default: env ALPHAGENOME_PROXY_URL or http://127.0.0.1:7890). "
            "Set to empty string to disable retry."
        ),
    )
    p.add_argument(
        "--max-retries",
        type=int,
        default=int(os.environ.get("ALPHAGENOME_MAX_RETRIES", "6")),
        help="Per-variant retries for transient AlphaGenome API/gRPC failures.",
    )
    p.add_argument(
        "--retry-base-delay-sec",
        type=float,
        default=float(os.environ.get("ALPHAGENOME_RETRY_BASE_DELAY_SEC", "8")),
        help="Initial delay before retrying transient AlphaGenome API failures.",
    )
    p.add_argument(
        "--retry-max-delay-sec",
        type=float,
        default=float(os.environ.get("ALPHAGENOME_RETRY_MAX_DELAY_SEC", "120")),
        help="Maximum delay between transient AlphaGenome API retries.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    # scripts/ -> alphagenome-api/ -> skills/ -> repo root
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    vcf_path = Path(args.input)
    output_name = vcf_path.stem + "_tissues.tsv"

    variants, info_keys = load_vcf(vcf_path)
    if args.limit > 0:
        variants = variants[:args.limit]
    log(f"[INFO] Loaded {len(variants)} variants from {vcf_path} ({len(info_keys)} INFO keys)")

    if args.tissues:
        tissue_dict = load_tissue_dict(args.tissues)
    elif args.non_interactive:
        tissue_dict = DEFAULT_TISSUE_DICT.copy()
    else:
        tissue_dict = load_tissue_dict(None)  # interactive prompt
    log(f"[INFO] Tissues ({len(tissue_dict)}): {list(tissue_dict.keys())}")

    ensure_alphagenome_installed()
    api_key = load_api_key(repo_root)
    log("[INFO] API key loaded")
    log(f"[INFO] alphagenome version: {metadata.version('alphagenome')}")

    proxy_url = args.proxy_url.strip() if args.proxy_url is not None else ""
    if not proxy_url:
        proxy_url = None

    summaries = run_batch(
        variants, info_keys, tissue_dict, args.assembly, args.interval_width,
        output_dir, output_name, api_key,
        args.request_timeout_sec, args.delay, args.resume, proxy_url,
        args.max_retries, args.retry_base_delay_sec, args.retry_max_delay_sec,
    )

    failed = [s for s in summaries if s["status"] != "success"]
    log(f"\n[INFO] Done: {len(summaries)-len(failed)}/{len(summaries)} succeeded, {len(failed)} failed")
    log(f"[INFO] Results: {output_dir}/{output_name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
