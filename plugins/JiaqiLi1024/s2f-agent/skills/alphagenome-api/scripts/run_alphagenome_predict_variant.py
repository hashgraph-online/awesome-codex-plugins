#!/usr/bin/env python3
"""Run one real AlphaGenome predict_variant call and save plot + summary."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path


def log(message: str) -> None:
    print(message, flush=True)


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
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key:
            data[key] = value
    return data


def find_repo_env_file() -> Path | None:
    for base in (Path.cwd(), Path(__file__).resolve().parent):
        for candidate in (base, *base.parents):
            env_path = candidate / ".env"
            if env_path.exists():
                return env_path
    return None


def load_api_key() -> tuple[str, str]:
    env_file = find_repo_env_file()
    source = "process_env"

    if env_file is not None:
        env_map = parse_env_file(env_file)
        if "ALPHAGENOME_API_KEY" in env_map and not os.environ.get("ALPHAGENOME_API_KEY"):
            os.environ["ALPHAGENOME_API_KEY"] = env_map["ALPHAGENOME_API_KEY"]
            source = str(env_file)

    api_key = os.environ.get("ALPHAGENOME_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ALPHAGENOME_API_KEY not found in environment or .env")

    if source == "process_env" and env_file is not None:
        source = "process_env_with_dotenv_available"
    return api_key, source


def ensure_alphagenome_installed() -> str:
    try:
        import alphagenome  # noqa: F401
        return "skip_import_ok"
    except ImportError:
        pass

    print("[INFO] alphagenome not found, installing with pip in current environment...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "alphagenome"])
    import alphagenome  # noqa: F401
    return "installed_via_pip"


def fetch_reference_base(assembly: str, chrom: str, position_1based: int) -> str:
    start = position_1based - 1
    end = position_1based
    if start < 0:
        raise ValueError(f"Invalid position for 1-based coordinates: {position_1based}")
    params = {
        "genome": assembly,
        "chrom": chrom,
        "start": start,
        "end": end,
    }
    url = "https://api.genome.ucsc.edu/getData/sequence?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to query UCSC reference base: {exc}") from exc

    dna = str(payload.get("dna", "")).upper()
    if len(dna) != 1 or dna not in {"A", "C", "G", "T", "N"}:
        raise RuntimeError(f"Unexpected UCSC response for reference base: {payload}")
    return dna


def build_interval(position_1based: int, width: int) -> tuple[int, int]:
    start = max(0, position_1based - (width // 2))
    end = start + width
    return start, end


def normalize_position_token(raw: str) -> int:
    cleaned = re.sub(r"[_,\s]", "", raw)
    if not cleaned.isdigit():
        raise ValueError(f"Invalid position token: {raw}")
    return int(cleaned)


def parse_coordinate_spec(spec: str) -> tuple[str, int]:
    text = spec.strip()
    match = re.fullmatch(r"(chr[\w]+):([0-9_,]+)", text, flags=re.IGNORECASE)
    if not match:
        raise ValueError(
            f"Invalid --coordinate format: {spec}. Expected like chr12:1000000 (1-based)."
        )
    chrom = match.group(1)
    position = normalize_position_token(match.group(2))
    return chrom, position


def parse_variant_spec(spec: str) -> tuple[str, int, str]:
    text = spec.strip().replace(" ", "")
    with_ref = re.fullmatch(
        r"(chr[\w]+):([0-9_,]+):?([ACGTNacgtn])>([ACGTNacgtn])", text
    )
    if with_ref:
        chrom = with_ref.group(1)
        position = normalize_position_token(with_ref.group(2))
        alt = with_ref.group(4).upper()
        return chrom, position, alt

    no_ref = re.fullmatch(r"(chr[\w]+):([0-9_,]+):([ACGTNacgtn])", text)
    if no_ref:
        chrom = no_ref.group(1)
        position = normalize_position_token(no_ref.group(2))
        alt = no_ref.group(3).upper()
        return chrom, position, alt

    raise ValueError(
        f"Invalid --variant-spec format: {spec}. Expected chr12:1000000:G or chr12:1000000:T>G."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AlphaGenome predict_variant once and save artifacts.")
    parser.add_argument("--chrom", default="chr12", help="Chromosome, default: chr12")
    parser.add_argument("--position", type=int, default=1_000_000, help="1-based position, default: 1000000")
    parser.add_argument("--alt", default="G", help="ALT base, default: G")
    parser.add_argument(
        "--coordinate",
        default=None,
        help="Canonical alias for chromosome + 1-based position, e.g. chr12:1000000",
    )
    parser.add_argument(
        "--variant-spec",
        default=None,
        help="Canonical alias for variant, e.g. chr12:1000000:G or chr12:1000000:T>G",
    )
    parser.add_argument("--assembly", default="hg38", help="Genome assembly for UCSC lookup, default: hg38")
    parser.add_argument(
        "--output-dir",
        default="output/alphagenome",
        help="Output folder for plot and summary, default: output/alphagenome",
    )
    parser.add_argument(
        "--request-timeout-sec",
        type=float,
        default=120.0,
        help="AlphaGenome request timeout in seconds, default: 120",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    chrom = args.chrom
    position = int(args.position)
    alt = args.alt.upper()
    normalization_steps: list[str] = []

    if args.coordinate:
        chrom, position = parse_coordinate_spec(args.coordinate)
        normalization_steps.append("coordinate-overrides-chrom-position")

    if args.variant_spec:
        chrom, position, alt = parse_variant_spec(args.variant_spec)
        normalization_steps.append("variant-spec-overrides-chrom-position-alt")

    if len(alt) != 1 or alt not in {"A", "C", "G", "T", "N"}:
        raise ValueError(f"ALT must be a single base in A/C/G/T/N. Got: {alt}")

    ref = "NA"
    interval_start = None
    interval_end = None
    summary_path = output_dir / f"alphagenome_variant-effect_{chrom}_{position}_NA_to_{alt}_result.json"
    plot_path = output_dir / f"alphagenome_variant-effect_{chrom}_{position}_NA_to_{alt}_rnaseq_overlay.png"
    install_action = "not_checked"
    dotenv_source = "unknown"
    requested_outputs = ["RNA_SEQ"]
    ontology_terms = ["UBERON:0001157"]
    summary = {
        "skill_id": "alphagenome-api",
        "task": "variant-effect",
        "run_time_utc": utc_now_iso(),
        "env_prefix": sys.prefix,
        "alphagenome_version": None,
        "assembly": args.assembly,
        "chrom": chrom,
        "position": position,
        "ref": ref,
        "alt": alt,
        "interval_start": interval_start,
        "interval_end": interval_end,
        "interval_width": 16_384,
        "coordinate_convention": {
            "single_site_position": "1-based",
            "interval": "0-based [start, end)",
        },
        "input_normalization": {
            "coordinate_raw": args.coordinate,
            "variant_spec_raw": args.variant_spec,
            "chrom_raw": args.chrom,
            "position_raw": args.position,
            "alt_raw": args.alt,
            "normalization_steps": normalization_steps,
        },
        "resolved_inputs": {
            "assembly": args.assembly,
            "chrom": chrom,
            "position": position,
            "alt": alt,
        },
        "requested_outputs": requested_outputs,
        "ontology_terms": ontology_terms,
        "install_action": install_action,
        "api_key_source": dotenv_source,
        "plot_path": str(plot_path),
        "summary_path": str(summary_path),
        "outputs": {
            "plot": str(plot_path),
            "npz": None,
            "result_json": str(summary_path),
        },
        "status": "running",
        "error": None,
    }

    try:
        ref = fetch_reference_base(args.assembly, chrom, position)
        summary["ref"] = ref
        summary_path = output_dir / f"alphagenome_variant-effect_{chrom}_{position}_{ref}_to_{alt}_result.json"
        plot_path = output_dir / f"alphagenome_variant-effect_{chrom}_{position}_{ref}_to_{alt}_rnaseq_overlay.png"
        summary["plot_path"] = str(plot_path)
        summary["summary_path"] = str(summary_path)
        if alt == ref:
            raise ValueError(
                f"ALT equals REF ({alt}) at {chrom}:{position}; this is not a mutation."
            )

        install_action = ensure_alphagenome_installed()
        summary["install_action"] = install_action
        summary["alphagenome_version"] = metadata.version("alphagenome")
        log(f"[INFO] alphagenome install check: {install_action}")

        api_key, dotenv_source = load_api_key()
        summary["api_key_source"] = dotenv_source
        log("[INFO] loaded ALPHAGENOME_API_KEY from environment/.env")

        interval_start, interval_end = build_interval(position, 16_384)
        summary["interval_start"] = interval_start
        summary["interval_end"] = interval_end
        summary["resolved_inputs"]["interval_start"] = interval_start
        summary["resolved_inputs"]["interval_end"] = interval_end

        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from alphagenome.data import genome
        from alphagenome.models import dna_client
        from alphagenome.visualization import plot_components

        model = dna_client.create(api_key, timeout=args.request_timeout_sec)
        log("[INFO] AlphaGenome client created successfully")

        interval = genome.Interval(chromosome=chrom, start=interval_start, end=interval_end)
        variant = genome.Variant(
            chromosome=chrom,
            position=position,
            reference_bases=ref,
            alternate_bases=alt,
        )
        outputs = model.predict_variant(
            interval=interval,
            variant=variant,
            requested_outputs=[dna_client.OutputType.RNA_SEQ],
            ontology_terms=ontology_terms,
        )
        if outputs.reference.rna_seq is None or outputs.alternate.rna_seq is None:
            raise RuntimeError("predict_variant succeeded but RNA_SEQ output is missing")
        log("[INFO] predict_variant completed successfully")

        fig = plot_components.plot(
            [
                plot_components.OverlaidTracks(
                    tdata={"REF": outputs.reference.rna_seq, "ALT": outputs.alternate.rna_seq},
                    colors={"REF": "dimgrey", "ALT": "red"},
                ),
            ],
            interval=outputs.reference.rna_seq.interval,
            annotations=[plot_components.VariantAnnotation([variant], alpha=0.8)],
            title=f"AlphaGenome RNA-seq overlay {chrom}:{position} {ref}>{alt}",
        )
        fig.savefig(plot_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        log(f"[INFO] saved plot: {plot_path}")

        summary["status"] = "success"
        summary["error"] = None
    except Exception as exc:
        summary["status"] = "failed"
        summary["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        summary["run_time_utc"] = utc_now_iso()
        summary["chrom"] = chrom
        summary["position"] = position
        summary["alt"] = alt
        summary["ref"] = ref
        summary["interval_start"] = interval_start
        summary["interval_end"] = interval_end
        summary["install_action"] = install_action
        summary["api_key_source"] = dotenv_source
        summary["resolved_inputs"] = {
            "assembly": args.assembly,
            "chrom": chrom,
            "position": position,
            "alt": alt,
            "interval_start": interval_start,
            "interval_end": interval_end,
        }
        summary["summary_path"] = str(summary_path)
        summary["plot_path"] = str(plot_path)
        summary["outputs"] = {
            "plot": str(plot_path),
            "npz": None,
            "result_json": str(summary_path),
        }
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        log(f"[INFO] saved summary: {summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
