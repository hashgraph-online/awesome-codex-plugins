#!/usr/bin/env python3
"""Stream a local VCF/BCF and emit variant/genotype summary counts as JSON.

Normal iteration scans in file order without an index. --region is a 1-based
inclusive samtools region string and requires TBI/CSI. Sample identifiers are
omitted unless --include-sample-names is supplied.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Iterator, Optional

import pysam
from _common import (
    nonnegative_int,
    optional_local_file,
    positive_int,
    region_coordinate_system,
    reject_output_overwriting_input,
    require_local_file,
    run_report_cli,
)


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="local VCF/VCF.gz/BCF file")
    parser.add_argument(
        "--index",
        type=Path,
        help="explicit local TBI/CSI index",
    )
    parser.add_argument(
        "--region",
        help="1-based inclusive samtools region, for example chr1:1-1000000",
    )
    parser.add_argument(
        "--sample",
        action="append",
        default=[],
        help="sample to decode; repeat for multiple samples (default: all)",
    )
    parser.add_argument(
        "--include-sample-names",
        action="store_true",
        help="include decoded sample identifiers in the JSON report",
    )
    parser.add_argument(
        "--threads",
        type=positive_int,
        default=1,
        help="HTSlib decompression threads",
    )
    parser.add_argument(
        "--max-records",
        type=nonnegative_int,
        default=0,
        help="stop after this many records; 0 scans the complete selection",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write JSON to a new file instead of stdout; refuses overwrite",
    )
    return parser


def variant_records(
    variants: pysam.VariantFile,
    region: Optional[str],
) -> Iterator[pysam.VariantRecord]:
    """Handle variant records."""
    if region is None:
        return iter(variants)
    return variants.fetch(region=region)


def is_symbolic_or_breakend(allele: str) -> bool:
    """Return whether symbolic or breakend."""
    return (
        allele == "*"
        or allele.startswith("<")
        or "[" in allele
        or "]" in allele
    )


def classify_record(record: pysam.VariantRecord) -> str:
    """Handle classify record."""
    alts = record.alts or ()
    if not alts:
        return "no_alt"
    if any(is_symbolic_or_breakend(alt) for alt in alts):
        return "symbolic_or_breakend"
    if len(record.ref) == 1 and all(len(alt) == 1 for alt in alts):
        return "snv"
    if all(len(alt) == len(record.ref) for alt in alts):
        return "mnv"
    if any(len(alt) != len(record.ref) for alt in alts):
        return "indel_or_mixed"
    return "other"


def filter_status(record: pysam.VariantRecord) -> str:
    """Filter status."""
    labels = tuple(record.filter.keys())
    if "PASS" in labels:
        return "pass"
    if not labels:
        return "unfiltered"
    return "failed"


def update_substitution_counts(
    record: pysam.VariantRecord,
    counts: Counter[str],
) -> None:
    """Update substitution counts."""
    alts = record.alts or ()
    if len(alts) != 1:
        return
    ref = record.ref.upper()
    alt = alts[0].upper()
    if ref not in "ACGT" or alt not in "ACGT" or len(ref) != 1 or len(alt) != 1:
        return

    pair = frozenset((ref, alt))
    if pair in (frozenset(("A", "G")), frozenset(("C", "T"))):
        counts["transitions"] += 1
    else:
        counts["transversions"] += 1


def update_genotype_counts(
    record: pysam.VariantRecord,
    counts: Counter[str],
    ploidy_counts: Counter[int],
) -> None:
    """Update genotype counts."""
    for call in record.samples.values():
        genotype = call.get("GT")
        counts["genotypes_seen"] += 1

        if genotype is None or all(allele is None for allele in genotype):
            counts["missing_genotypes"] += 1
            continue

        ploidy_counts[len(genotype)] += 1
        if any(allele is None for allele in genotype):
            counts["partially_missing_genotypes"] += 1
            continue

        called = tuple(int(allele) for allele in genotype)
        counts["called_genotypes"] += 1
        counts["called_alleles"] += len(called)
        counts["alternate_alleles"] += sum(
            allele > 0 for allele in called
        )
        if call.phased:
            counts["phased_called_genotypes"] += 1

        unique = set(called)
        if unique == {0}:
            counts["reference_only_genotypes"] += 1
        elif len(called) == 1:
            counts["haploid_alternate_genotypes"] += 1
        elif len(unique) == 1:
            counts["same_alternate_allele_genotypes"] += 1
        else:
            counts["mixed_allele_genotypes"] += 1


def summarize_variants(args: argparse.Namespace) -> dict[str, Any]:
    """Summarize variants."""
    path = require_local_file(args.input, "input")
    index = optional_local_file(args.index, "index")

    kwargs: dict[str, Any] = {"threads": args.threads}
    if index is not None:
        kwargs["index_filename"] = str(index)

    record_counts: Counter[str] = Counter()
    filter_label_counts: Counter[str] = Counter()
    substitution_counts: Counter[str] = Counter()
    genotype_counts: Counter[str] = Counter()
    ploidy_counts: Counter[int] = Counter()
    quality_sum = 0.0
    quality_count = 0
    record_limit_reached = False

    with pysam.VariantFile(str(path), **kwargs) as variants:
        available_samples = list(variants.header.samples)
        if args.sample:
            missing = sorted(set(args.sample) - set(available_samples))
            if missing:
                raise ValueError(
                    "samples not present in header: " + ", ".join(missing)
                )
            variants.subset_samples(args.sample)

        decoded_samples = list(variants.header.samples)

        for record in variant_records(variants, args.region):
            if args.max_records and record_counts["total"] >= args.max_records:
                record_limit_reached = True
                break

            record_counts["total"] += 1
            record_counts[classify_record(record)] += 1
            record_counts[filter_status(record)] += 1

            alts = record.alts or ()
            if len(alts) == 1:
                record_counts["biallelic"] += 1
            elif len(alts) > 1:
                record_counts["multiallelic"] += 1

            if record.qual is None:
                record_counts["missing_quality"] += 1
            else:
                quality_sum += float(record.qual)
                quality_count += 1

            labels = tuple(record.filter.keys())
            if not labels:
                filter_label_counts["."] += 1
            else:
                filter_label_counts.update(labels)

            update_substitution_counts(record, substitution_counts)
            update_genotype_counts(
                record,
                genotype_counts,
                ploidy_counts,
            )

        try:
            has_index = variants.index is not None
        except (AttributeError, OSError, ValueError):
            has_index = False

        report: dict[str, Any] = {
            "schema_version": "1.0",
            "pysam_version": pysam.__version__,
            "samtools_version": getattr(
                pysam, "__samtools_version__", None
            ),
            "file_name": path.name,
            "format": (
                "BCF"
                if bool(getattr(variants, "is_bcf", False))
                else "VCF"
            ),
            "has_index": has_index,
            "selection": {
                "region": args.region,
                "region_coordinate_system": region_coordinate_system(args.region),
                "max_records": args.max_records,
                "record_limit_reached": record_limit_reached,
                "available_sample_count": len(available_samples),
                "decoded_sample_count": len(decoded_samples),
            },
            "record_counts": dict(sorted(record_counts.items())),
            "filter_label_counts": dict(
                sorted(filter_label_counts.items())
            ),
            "substitution_counts": dict(
                sorted(substitution_counts.items())
            ),
            "quality": {
                "records_with_quality": quality_count,
                "mean_quality": (
                    quality_sum / quality_count
                    if quality_count
                    else None
                ),
            },
            "genotypes": dict(sorted(genotype_counts.items())),
            "observed_genotype_ploidy_counts": {
                str(ploidy): count
                for ploidy, count in sorted(ploidy_counts.items())
            },
            "semantics": (
                "PASS, unfiltered '.', and failed FILTER states are distinct. "
                "Record classes are mutually exclusive; indel_or_mixed can "
                "include multiallelic records with mixed allele lengths."
            ),
        }
        if args.include_sample_names:
            report["selection"]["decoded_samples"] = decoded_samples
        return report


def main(argv: Optional[list[str]] = None) -> int:
    """Run the command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)
    reject_output_overwriting_input(parser, args)
    return run_report_cli("variant_summary", args, summarize_variants, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
