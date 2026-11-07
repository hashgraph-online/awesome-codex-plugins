#!/usr/bin/env python3
"""Inspect a local HTS/sequence file and emit a bounded JSON summary.

The default report reads headers and index metadata only. It does not emit
alignment query names, FASTX record names, VCF sample names, or full headers.
CRAM requires an explicit local --reference to avoid hidden reference lookup.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Optional

import pysam
from _common import (
    alignment_format,
    nonnegative_int,
    optional_local_file,
    positive_int,
    reject_output_overwriting_input,
    require_local_file,
    run_report_cli,
)


CRAM_SUFFIX = ".cram"
KINDS = ("alignment", "variant", "fasta", "fastx", "tabix")


def detect_kind(path: Path) -> str:
    """Detect kind."""
    name = path.name.lower()

    if name.endswith((".bam", ".sam", CRAM_SUFFIX)):
        return "alignment"
    if name.endswith((".vcf", ".vcf.gz", ".vcf.bgz", ".bcf")):
        return "variant"
    if name.endswith(
        (
            ".fa",
            ".fasta",
            ".fna",
            ".fas",
            ".fa.gz",
            ".fasta.gz",
            ".fna.gz",
            ".fas.gz",
        )
    ):
        return "fasta"
    if name.endswith(
        (
            ".fq",
            ".fastq",
            ".fq.gz",
            ".fastq.gz",
            ".fq.bgz",
            ".fastq.bgz",
        )
    ):
        return "fastx"
    if name.endswith(
        (
            ".bed.gz",
            ".bed.bgz",
            ".gff.gz",
            ".gff3.gz",
            ".gtf.gz",
            ".tsv.gz",
            ".tab.gz",
        )
    ):
        return "tabix"

    raise ValueError(
        "could not infer file kind from suffix; pass --kind "
        + ", ".join(KINDS)
    )


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="local genomic data file")
    parser.add_argument(
        "--kind",
        choices=("auto",) + KINDS,
        default="auto",
        help="file interface to use",
    )
    parser.add_argument(
        "--reference",
        type=Path,
        help="local indexed reference FASTA; required for CRAM",
    )
    parser.add_argument(
        "--index",
        type=Path,
        help="explicit local BAI/CSI/CRAI/TBI/FAI index",
    )
    parser.add_argument(
        "--threads",
        type=positive_int,
        default=1,
        help="HTSlib decompression threads",
    )
    parser.add_argument(
        "--max-items",
        type=nonnegative_int,
        default=100,
        help="maximum contigs and metadata keys to include; 0 includes all",
    )
    parser.add_argument(
        "--include-identifiers",
        action="store_true",
        help="include VCF sample names and alignment read-group IDs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write JSON to a new file instead of stdout; refuses overwrite",
    )
    return parser


def limited(values: list[Any], maximum: int) -> tuple[list[Any], bool]:
    """Handle limited."""
    if maximum == 0 or len(values) <= maximum:
        return values, False
    return values[:maximum], True


def contig_records(
    names: tuple[str, ...] | list[str],
    lengths: tuple[int, ...] | list[int],
    maximum: int,
) -> tuple[list[dict[str, Any]], bool]:
    """Handle contig records."""
    records = [
        {"name": name, "length": int(length)}
        for name, length in zip(names, lengths)
    ]
    return limited(records, maximum)


def alignment_mode(path: Path) -> str:
    """Handle alignment mode."""
    name = path.name.lower()
    if name.endswith(".sam"):
        return "r"
    if name.endswith(CRAM_SUFFIX):
        return "rc"
    return "rb"


def inspect_alignment(
    path: Path,
    *,
    reference: Optional[Path],
    index: Optional[Path],
    threads: int,
    max_items: int,
    include_identifiers: bool,
) -> dict[str, Any]:
    """Handle inspect alignment."""
    if path.name.lower().endswith(CRAM_SUFFIX) and reference is None:
        raise ValueError("CRAM inspection requires --reference")

    kwargs: dict[str, Any] = {"threads": threads}
    if reference is not None:
        kwargs["reference_filename"] = str(reference)
    if index is not None:
        kwargs["index_filename"] = str(index)

    with pysam.AlignmentFile(
        str(path),
        alignment_mode(path),
        **kwargs,
    ) as alignments:
        contigs, contigs_truncated = contig_records(
            list(alignments.references),
            list(alignments.lengths),
            max_items,
        )
        header = alignments.header.to_dict()
        read_groups = header.get("RG", [])
        programs = header.get("PG", [])

        try:
            has_index = bool(alignments.has_index())
        except (AttributeError, OSError, ValueError):
            has_index = False

        report: dict[str, Any] = {
            "format": alignment_format(alignments),
            "is_remote": bool(alignments.is_remote),
            "has_index": has_index,
            "sort_order": header.get("HD", {}).get("SO"),
            "reference_count": len(alignments.references),
            "contigs": contigs,
            "contigs_truncated": contigs_truncated,
            "read_group_count": len(read_groups),
            "program_record_count": len(programs),
            "comment_count": len(header.get("CO", [])),
        }

        if include_identifiers:
            read_group_ids = [
                group.get("ID")
                for group in read_groups
                if group.get("ID") is not None
            ]
            report["read_group_ids"], report["read_group_ids_truncated"] = (
                limited(read_group_ids, max_items)
            )

        if has_index:
            try:
                statistics = alignments.get_index_statistics()
                report["index_statistics"] = {
                    "mapped": sum(item.mapped for item in statistics),
                    "unmapped_with_coordinates": sum(
                        item.unmapped for item in statistics
                    ),
                    "no_coordinate": int(alignments.nocoordinate),
                }
            except (AttributeError, OSError, ValueError):
                report["index_statistics"] = None

        return report


def variant_index_loaded(variants: pysam.VariantFile) -> bool:
    """Handle variant index loaded."""
    try:
        return variants.index is not None
    except (AttributeError, OSError, ValueError):
        return False


def inspect_variant(
    path: Path,
    *,
    index: Optional[Path],
    threads: int,
    max_items: int,
    include_identifiers: bool,
) -> dict[str, Any]:
    """Handle inspect variant."""
    kwargs: dict[str, Any] = {"threads": threads}
    if index is not None:
        kwargs["index_filename"] = str(index)

    with pysam.VariantFile(str(path), **kwargs) as variants:
        header = variants.header
        contig_values = [
            {"name": name, "length": metadata.length}
            for name, metadata in header.contigs.items()
        ]
        contigs, contigs_truncated = limited(contig_values, max_items)
        info_keys, info_truncated = limited(list(header.info), max_items)
        format_keys, formats_truncated = limited(
            list(header.formats), max_items
        )
        filter_keys, filters_truncated = limited(
            list(header.filters), max_items
        )

        report: dict[str, Any] = {
            "format": (
                "BCF"
                if bool(getattr(variants, "is_bcf", False))
                else "VCF"
            ),
            "is_remote": bool(variants.is_remote),
            "has_index": variant_index_loaded(variants),
            "contig_count": len(header.contigs),
            "contigs": contigs,
            "contigs_truncated": contigs_truncated,
            "sample_count": len(header.samples),
            "info_keys": info_keys,
            "info_keys_truncated": info_truncated,
            "format_keys": format_keys,
            "format_keys_truncated": formats_truncated,
            "filter_keys": filter_keys,
            "filter_keys_truncated": filters_truncated,
        }
        if include_identifiers:
            sample_names, samples_truncated = limited(
                list(header.samples), max_items
            )
            report["sample_names"] = sample_names
            report["sample_names_truncated"] = samples_truncated
        return report


def inspect_fasta(
    path: Path,
    *,
    index: Optional[Path],
    max_items: int,
) -> dict[str, Any]:
    """Handle inspect fasta."""
    kwargs: dict[str, Any] = {}
    if index is not None:
        kwargs["filepath_index"] = str(index)

    with pysam.FastaFile(str(path), **kwargs) as fasta:
        contigs, contigs_truncated = contig_records(
            list(fasta.references),
            list(fasta.lengths),
            max_items,
        )
        return {
            "format": "FASTA",
            "random_access": True,
            "reference_count": fasta.nreferences,
            "total_bases": sum(fasta.lengths),
            "contigs": contigs,
            "contigs_truncated": contigs_truncated,
        }


def inspect_fastx(path: Path) -> dict[str, Any]:
    """Handle inspect fastx."""
    with pysam.FastxFile(str(path), persist=False):
        return {
            "format": "FASTA/FASTQ",
            "random_access": False,
            "content_scanned": False,
            "note": (
                "FastxFile has no header index; use a streaming QC workflow "
                "to summarize records."
            ),
        }


def inspect_tabix(
    path: Path,
    *,
    index: Optional[Path],
    threads: int,
    max_items: int,
) -> dict[str, Any]:
    """Handle inspect tabix."""
    kwargs: dict[str, Any] = {"threads": threads}
    if index is not None:
        kwargs["index"] = str(index)

    with pysam.TabixFile(str(path), **kwargs) as table:
        contigs, contigs_truncated = limited(
            list(table.contigs), max_items
        )
        header_line_count = sum(1 for _ in table.header)
        return {
            "format": "TABIX",
            "has_index": True,
            "contig_count": len(table.contigs),
            "contigs": contigs,
            "contigs_truncated": contigs_truncated,
            "header_line_count": header_line_count,
        }


def inspect_file(args: argparse.Namespace) -> dict[str, Any]:
    """Handle inspect file."""
    path = require_local_file(args.input, "input")
    reference = optional_local_file(args.reference, "reference")
    index = optional_local_file(args.index, "index")
    kind = detect_kind(path) if args.kind == "auto" else args.kind

    if kind == "alignment":
        details = inspect_alignment(
            path,
            reference=reference,
            index=index,
            threads=args.threads,
            max_items=args.max_items,
            include_identifiers=args.include_identifiers,
        )
    elif kind == "variant":
        details = inspect_variant(
            path,
            index=index,
            threads=args.threads,
            max_items=args.max_items,
            include_identifiers=args.include_identifiers,
        )
    elif kind == "fasta":
        details = inspect_fasta(
            path,
            index=index,
            max_items=args.max_items,
        )
    elif kind == "fastx":
        details = inspect_fastx(path)
    else:
        details = inspect_tabix(
            path,
            index=index,
            threads=args.threads,
            max_items=args.max_items,
        )

    return {
        "schema_version": "1.0",
        "pysam_version": pysam.__version__,
        "samtools_version": getattr(
            pysam, "__samtools_version__", None
        ),
        "file_name": path.name,
        "size_bytes": path.stat().st_size,
        "kind": kind,
        "identifiers_included": args.include_identifiers,
        "details": details,
    }


def main(argv: Optional[list[str]] = None) -> int:
    """Run the command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)
    reject_output_overwriting_input(parser, args)
    return run_report_cli("inspect_hts", args, inspect_file, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
