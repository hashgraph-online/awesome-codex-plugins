#!/usr/bin/env python3
"""Local AlphaGenome Research helper.

This script supports three practical paths:
- check: verify Python imports and JAX devices without loading weights.
- template: write a runnable Python starter script for local AlphaGenome use.
- interval / variant: run a small local prediction when weights are available.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import sys
import textwrap
from typing import Any, Optional

import numpy as np


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return str(value)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True, default=json_default) + "\n",
        encoding="utf-8",
    )


def package_version(name: str) -> Optional[str]:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def collect_runtime_info() -> dict[str, Any]:
    info: dict[str, Any] = {
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "python_prefix": sys.prefix,
        "platform": platform.platform(),
        "packages": {
            "alphagenome": package_version("alphagenome"),
            "alphagenome_research": package_version("alphagenome_research"),
            "jax": package_version("jax"),
            "jaxlib": package_version("jaxlib"),
            "jax-cuda12-plugin": package_version("jax-cuda12-plugin"),
            "jax-cuda12-pjrt": package_version("jax-cuda12-pjrt"),
            "jax-cuda13-plugin": package_version("jax-cuda13-plugin"),
            "jax-cuda13-pjrt": package_version("jax-cuda13-pjrt"),
            "dm-haiku": package_version("dm-haiku"),
            "orbax": package_version("orbax"),
            "kagglehub": package_version("kagglehub"),
            "huggingface_hub": package_version("huggingface_hub"),
        },
        "imports": {},
        "jax_devices": [],
        "warnings": [],
    }

    cgroup_memory_max = Path("/sys/fs/cgroup/memory.max")
    if cgroup_memory_max.exists():
        raw_limit = cgroup_memory_max.read_text(encoding="utf-8").strip()
        info["cgroup_memory_max"] = raw_limit
        if raw_limit.isdigit() and int(raw_limit) < 8 * 1024**3:
            info["warnings"].append(
                "cgroup memory limit is below 8 GiB. Real checkpoint loading may be killed "
                "before model creation completes."
            )

    for module_name in (
        "alphagenome",
        "alphagenome_research",
        "alphagenome_research.model.dna_model",
        "jax",
    ):
        try:
            importlib.import_module(module_name)
            info["imports"][module_name] = "ok"
        except Exception as exc:
            info["imports"][module_name] = f"{type(exc).__name__}: {exc}"

    try:
        import jax

        info["jax_default_backend"] = jax.default_backend()
        info["jax_devices"] = [
            {
                "id": getattr(device, "id", None),
                "platform": getattr(device, "platform", None),
                "device_kind": getattr(device, "device_kind", None),
                "description": str(device),
            }
            for device in jax.local_devices()
        ]
        if not any(d.get("platform") in {"gpu", "tpu"} for d in info["jax_devices"]):
            info["warnings"].append(
                "No GPU/TPU JAX device detected. Local AlphaGenome full-model inference "
                "will fail by default unless a CPU device is explicitly passed for debugging."
            )
    except Exception as exc:
        info["warnings"].append(f"Unable to inspect JAX devices: {type(exc).__name__}: {exc}")

    if sys.version_info < (3, 11):
        info["warnings"].append("alphagenome_research requires Python >=3.11.")
    if info["packages"]["alphagenome_research"] is None:
        info["warnings"].append(
            "alphagenome_research is not installed. Run: python -m pip install -e /path/to/alphagenome_research"
        )

    return info


def normalize_chrom(chrom: str) -> str:
    chrom = chrom.strip()
    return chrom if chrom.startswith("chr") else f"chr{chrom}"


def parse_interval(interval: str) -> tuple[str, int, int]:
    text = interval.strip()
    if ":" not in text or "-" not in text:
        raise ValueError(f"Invalid interval '{interval}'. Expected chr:start-end.")
    chrom, rest = text.split(":", 1)
    start_raw, end_raw = rest.split("-", 1)
    start = int(start_raw.replace(",", "").replace("_", ""))
    end = int(end_raw.replace(",", "").replace("_", ""))
    if start < 0 or end <= start:
        raise ValueError(f"Invalid 0-based half-open interval: {interval}")
    return normalize_chrom(chrom), start, end


def build_centered_interval(position_1based: int, width: int) -> tuple[int, int]:
    if position_1based <= 0:
        raise ValueError("Variant position must be 1-based and positive.")
    if width <= 0:
        raise ValueError("Interval width must be positive.")
    start = max(0, position_1based - 1 - (width // 2))
    return start, start + width


def output_type_from_name(dna_model_module: Any, name: str) -> Any:
    try:
        return getattr(dna_model_module.OutputType, name)
    except AttributeError as exc:
        valid = [member.name for member in dna_model_module.OutputType]
        raise ValueError(f"Unknown output head '{name}'. Valid values include: {valid}") from exc


def organism_from_name(dna_model_module: Any, name: str) -> Any:
    normalized = name.lower().replace("-", "_")
    if normalized in {"human", "homo_sapiens", "homo"}:
        return dna_model_module.Organism.HOMO_SAPIENS
    if normalized in {"mouse", "mus_musculus", "mus"}:
        return dna_model_module.Organism.MUS_MUSCULUS
    raise ValueError("Species must be human or mouse.")


def build_organism_settings(
    args: argparse.Namespace, dna_model_module: Any
) -> Optional[dict[Any, Any]]:
    values = {
        "fasta_path": args.fasta_path,
        "gtf_feather_path": args.gtf_feather_path,
        "pas_feather_path": args.pas_feather_path,
        "splice_site_starts_feather_path": args.splice_site_starts_feather_path,
        "splice_site_ends_feather_path": args.splice_site_ends_feather_path,
    }
    if not any(values.values()) and not args.minimal_organism_settings and args.mode != "sequence":
        return None

    organism = organism_from_name(dna_model_module, args.species)
    settings = {
        dna_model_module.Organism.HOMO_SAPIENS: dna_model_module.OrganismSettings(),
        dna_model_module.Organism.MUS_MUSCULUS: dna_model_module.OrganismSettings(),
    }
    settings[organism] = dna_model_module.OrganismSettings(**values)
    return settings


def load_model(args: argparse.Namespace, dna_model_module: Any) -> Any:
    organism_settings = build_organism_settings(args, dna_model_module)
    if args.model_source == "kaggle":
        return dna_model_module.create_from_kaggle(
            args.model_version,
            organism_settings=organism_settings,
        )
    if args.model_source == "huggingface":
        return dna_model_module.create_from_huggingface(
            args.model_version,
            organism_settings=organism_settings,
        )
    if args.model_source == "checkpoint":
        if not args.checkpoint_path:
            raise ValueError("--checkpoint-path is required with --model-source checkpoint")
        return dna_model_module.create(
            args.checkpoint_path,
            organism_settings=organism_settings,
        )
    raise ValueError(f"Unsupported model source: {args.model_source}")


def save_track_npz(path: Path, **arrays: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = {}
    for key, value in arrays.items():
        if value is None:
            continue
        normalized[key] = value
    np.savez_compressed(path, **normalized)


def track_values(track: Any) -> np.ndarray:
    return np.asarray(track.values)


def run_sequence(args: argparse.Namespace) -> dict[str, Any]:
    from alphagenome_research.model import dna_model

    output_type = output_type_from_name(dna_model, args.output_head)
    organism = organism_from_name(dna_model, args.species)
    ontology_terms = args.ontology_term
    model = load_model(args, dna_model)

    outputs = model.predict_sequence(
        args.sequence,
        organism=organism,
        requested_outputs=[output_type],
        ontology_terms=ontology_terms,
    )
    track = getattr(outputs, args.output_head.lower(), None)
    if track is None:
        raise RuntimeError(f"predict_sequence returned no {args.output_head} output.")

    values = track_values(track)
    prefix = f"alphagenome_research_sequence_{len(args.sequence)}bp_{args.output_head}"
    npz_path = args.output_dir / f"{prefix}_prediction.npz"
    save_track_npz(
        npz_path,
        values=values,
        resolution=np.asarray([track.resolution], dtype=np.int32),
        sequence_length=np.asarray([len(args.sequence)], dtype=np.int64),
    )
    return {
        "task": "sequence",
        "species": args.species,
        "sequence_length": len(args.sequence),
        "output_head": args.output_head,
        "ontology_terms": ontology_terms,
        "track_shape": list(values.shape),
        "track_dtype": str(values.dtype),
        "track_resolution": int(track.resolution),
        "track_mean": float(values.mean()),
        "track_min": float(values.min()),
        "track_max": float(values.max()),
        "npz_path": str(npz_path.resolve()),
    }


def run_interval(args: argparse.Namespace) -> dict[str, Any]:
    from alphagenome.data import genome
    from alphagenome_research.model import dna_model

    chrom, start, end = parse_interval(args.interval)
    output_type = output_type_from_name(dna_model, args.output_head)
    organism = organism_from_name(dna_model, args.species)
    ontology_terms = args.ontology_term
    model = load_model(args, dna_model)

    interval = genome.Interval(chromosome=chrom, start=start, end=end)
    outputs = model.predict_interval(
        interval=interval,
        organism=organism,
        requested_outputs=[output_type],
        ontology_terms=ontology_terms,
    )
    track = getattr(outputs, args.output_head.lower(), None)
    if track is None:
        raise RuntimeError(f"predict_interval returned no {args.output_head} output.")

    prefix = f"alphagenome_research_interval_{chrom}_{start}_{end}_{args.output_head}"
    npz_path = args.output_dir / f"{prefix}_prediction.npz"
    save_track_npz(
        npz_path,
        values=track.values,
        resolution=np.asarray([track.resolution], dtype=np.int32),
        start=np.asarray([start], dtype=np.int64),
        end=np.asarray([end], dtype=np.int64),
    )
    return {
        "task": "interval",
        "chrom": chrom,
        "interval": [start, end],
        "output_head": args.output_head,
        "ontology_terms": ontology_terms,
        "track_shape": list(track.values.shape),
        "track_resolution": int(track.resolution),
        "npz_path": str(npz_path.resolve()),
    }


def run_variant(args: argparse.Namespace) -> dict[str, Any]:
    from alphagenome.data import genome
    from alphagenome_research.model import dna_model

    chrom = normalize_chrom(args.chrom)
    start, end = build_centered_interval(args.position, args.interval_width)
    output_type = output_type_from_name(dna_model, args.output_head)
    organism = organism_from_name(dna_model, args.species)
    ontology_terms = args.ontology_term
    model = load_model(args, dna_model)

    interval = genome.Interval(chromosome=chrom, start=start, end=end)
    variant = genome.Variant(
        chromosome=chrom,
        position=args.position,
        reference_bases=args.ref.upper(),
        alternate_bases=args.alt.upper(),
    )
    outputs = model.predict_variant(
        interval=interval,
        variant=variant,
        organism=organism,
        requested_outputs=[output_type],
        ontology_terms=ontology_terms,
    )
    output_attr = args.output_head.lower()
    ref_track = getattr(outputs.reference, output_attr, None)
    alt_track = getattr(outputs.alternate, output_attr, None)
    if ref_track is None or alt_track is None:
        raise RuntimeError(f"predict_variant returned no {args.output_head} output.")

    prefix = (
        f"alphagenome_research_variant_{chrom}_{args.position}_"
        f"{args.ref.upper()}_to_{args.alt.upper()}_{args.output_head}"
    )
    npz_path = args.output_dir / f"{prefix}_prediction.npz"
    save_track_npz(
        npz_path,
        reference=ref_track.values,
        alternate=alt_track.values,
        delta=alt_track.values - ref_track.values,
        resolution=np.asarray([ref_track.resolution], dtype=np.int32),
        interval_start=np.asarray([start], dtype=np.int64),
        interval_end=np.asarray([end], dtype=np.int64),
        position=np.asarray([args.position], dtype=np.int64),
    )
    return {
        "task": "variant",
        "chrom": chrom,
        "position": args.position,
        "ref": args.ref.upper(),
        "alt": args.alt.upper(),
        "interval": [start, end],
        "coordinate_convention": {
            "variant_position": "1-based",
            "interval": "0-based half-open",
        },
        "output_head": args.output_head,
        "ontology_terms": ontology_terms,
        "reference_shape": list(ref_track.values.shape),
        "alternate_shape": list(alt_track.values.shape),
        "track_resolution": int(ref_track.resolution),
        "npz_path": str(npz_path.resolve()),
    }


def render_template(args: argparse.Namespace) -> str:
    head = args.output_head
    ontology_terms = args.ontology_term or ["UBERON:0001157"]
    species_enum = (
        "MUS_MUSCULUS"
        if args.species.lower().replace("-", "_") in {"mouse", "mus_musculus", "mus"}
        else "HOMO_SAPIENS"
    )
    model_loader = {
        "kaggle": f"dna_model.create_from_kaggle({args.model_version!r})",
        "huggingface": f"dna_model.create_from_huggingface({args.model_version!r})",
        "checkpoint": f"dna_model.create({str(args.checkpoint_path or '/path/to/checkpoint')!r})",
    }[args.model_source]
    prelude = ""

    if args.task == "sequence":
        prelude = """
        organism_settings = {
            dna_model.Organism.HOMO_SAPIENS: dna_model.OrganismSettings(),
            dna_model.Organism.MUS_MUSCULUS: dna_model.OrganismSettings(),
        }
        """
        model_loader = {
            "kaggle": (
                f"dna_model.create_from_kaggle({args.model_version!r}, "
                "organism_settings=organism_settings)"
            ),
            "huggingface": (
                f"dna_model.create_from_huggingface({args.model_version!r}, "
                "organism_settings=organism_settings)"
            ),
            "checkpoint": (
                f"dna_model.create({str(args.checkpoint_path or '/path/to/checkpoint')!r}, "
                "organism_settings=organism_settings)"
            ),
        }[args.model_source]
        sequence_expr = '"ACGT" * 512' if args.sequence == "ACGT" * 512 else repr(args.sequence)

    if args.task == "sequence":
        body = f"""
        outputs = model.predict_sequence(
            {sequence_expr},
            organism=dna_model.Organism.{species_enum},
            requested_outputs=[dna_model.OutputType.{head}],
            ontology_terms={ontology_terms!r},
        )
        track = outputs.{head.lower()}
        print(track.values.shape, track.values.dtype, track.resolution)
        """
    elif args.task == "interval":
        chrom, start, end = parse_interval(args.interval)
        body = f"""
        interval = genome.Interval(chromosome={chrom!r}, start={start}, end={end})
        outputs = model.predict_interval(
            interval=interval,
            requested_outputs=[dna_model.OutputType.{head}],
            ontology_terms={ontology_terms!r},
        )
        track = outputs.{head.lower()}
        print(track.values.shape, track.resolution)
        """
    else:
        chrom = normalize_chrom(args.chrom)
        start, end = build_centered_interval(args.position, args.interval_width)
        body = f"""
        interval = genome.Interval(chromosome={chrom!r}, start={start}, end={end})
        variant = genome.Variant(
            chromosome={chrom!r},
            position={args.position},
            reference_bases={args.ref.upper()!r},
            alternate_bases={args.alt.upper()!r},
        )
        outputs = model.predict_variant(
            interval=interval,
            variant=variant,
            requested_outputs=[dna_model.OutputType.{head}],
            ontology_terms={ontology_terms!r},
        )
        print(outputs.reference.{head.lower()}.values.shape)
        print(outputs.alternate.{head.lower()}.values.shape)
        """

    return textwrap.dedent(
        f"""\
        #!/usr/bin/env python3
        from alphagenome.data import genome
        from alphagenome_research.model import dna_model

        {textwrap.indent(textwrap.dedent(prelude).strip(), "        ").strip()}
        model = {model_loader}
        {textwrap.indent(textwrap.dedent(body).strip(), "        ").strip()}
        """
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local AlphaGenome Research checks or small workflows.")
    parser.add_argument(
        "--mode",
        choices=("check", "template", "sequence", "interval", "variant"),
        default="check",
        help="Execution mode. 'sequence', 'interval', and 'variant' load model weights.",
    )
    parser.add_argument(
        "--task",
        choices=("sequence", "interval", "variant"),
        default="variant",
        help="Template task when --mode template is used.",
    )
    parser.add_argument(
        "--model-source",
        choices=("kaggle", "huggingface", "checkpoint"),
        default="huggingface",
        help="Where to load model weights from.",
    )
    parser.add_argument("--model-version", default="all_folds", help="Model version for Kaggle/Hugging Face.")
    parser.add_argument("--checkpoint-path", default=None, help="Local checkpoint path for --model-source checkpoint.")
    parser.add_argument("--species", default="human", help="human or mouse.")
    parser.add_argument("--output-dir", type=Path, default=Path("output/alphagenome_research"))
    parser.add_argument("--output-head", default="RNA_SEQ", help="OutputType name, e.g. RNA_SEQ, DNASE, ATAC.")
    parser.add_argument(
        "--sequence",
        default="ACGT" * 512,
        help="DNA sequence for --mode sequence. Default is a 2048 bp synthetic sequence.",
    )
    parser.add_argument(
        "--ontology-term",
        action="append",
        default=None,
        help="Ontology CURIE. Repeatable. Omit for no ontology filtering in generated code.",
    )
    parser.add_argument("--interval", default="chr22:35677410-35693800", help="0-based half-open interval.")
    parser.add_argument("--chrom", default="chr22")
    parser.add_argument("--position", type=int, default=36_201_698, help="1-based variant position.")
    parser.add_argument("--ref", default="A", help="Reference bases.")
    parser.add_argument("--alt", default="C", help="Alternate bases.")
    parser.add_argument("--interval-width", type=int, default=16_384, help="Centered variant prediction width.")
    parser.add_argument("--fasta-path", default=None)
    parser.add_argument("--gtf-feather-path", default=None)
    parser.add_argument("--pas-feather-path", default=None)
    parser.add_argument("--splice-site-starts-feather-path", default=None)
    parser.add_argument("--splice-site-ends-feather-path", default=None)
    parser.add_argument(
        "--minimal-organism-settings",
        action="store_true",
        help=(
            "Build human and mouse metadata-only OrganismSettings. This avoids remote "
            "FASTA/annotation loading for predict_sequence and preserves the two-organism "
            "embedding shape used by all_folds checkpoints."
        ),
    )
    parser.add_argument(
        "--xla-preallocate",
        action="store_true",
        help="Leave JAX GPU memory preallocation enabled. By default this helper disables it.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.xla_preallocate:
        os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    runtime = collect_runtime_info()

    if args.mode == "check":
        result = {
            "skill_id": "alphagenome-research",
            "mode": args.mode,
            "status": "ok" if not runtime["warnings"] else "ok_with_warnings",
            "run_time_utc": utc_now_iso(),
            "runtime": runtime,
        }
        out = args.output_dir / "alphagenome_research_check_result.json"
        write_json(out, result)
        print(json.dumps(result, indent=2, ensure_ascii=True))
        print(f"[INFO] wrote {out.resolve()}")
        return 0

    if args.mode == "template":
        template = render_template(args)
        out = args.output_dir / f"alphagenome_research_{args.task}_template.py"
        out.write_text(template, encoding="utf-8")
        print(template)
        print(f"[INFO] wrote {out.resolve()}")
        return 0

    result_path = args.output_dir / f"alphagenome_research_{args.mode}_result.json"
    result: dict[str, Any] = {
        "skill_id": "alphagenome-research",
        "mode": args.mode,
        "status": "running",
        "run_time_utc": utc_now_iso(),
        "runtime": runtime,
        "model_source": args.model_source,
        "model_version": args.model_version,
        "checkpoint_path": args.checkpoint_path,
        "species": args.species,
        "output_dir": str(args.output_dir.resolve()),
        "error": None,
    }
    try:
        if args.mode == "sequence":
            result.update(run_sequence(args))
        elif args.mode == "interval":
            result.update(run_interval(args))
        elif args.mode == "variant":
            result.update(run_variant(args))
        result["status"] = "success"
    except Exception as exc:
        result["status"] = "failed"
        result["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        result["run_time_utc"] = utc_now_iso()
        write_json(result_path, result)
        print(f"[INFO] wrote {result_path.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
