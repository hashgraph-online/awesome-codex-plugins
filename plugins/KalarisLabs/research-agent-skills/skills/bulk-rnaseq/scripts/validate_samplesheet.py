#!/usr/bin/env python3
"""Validate a bulk RNA-seq samplesheet (and optional design metadata).

Catches the cheap-to-miss, expensive-to-debug problems before you spend compute:
missing/duplicate FASTQs, inconsistent paired/single-end rows, invalid
strandedness, and (with --metadata) too few replicates or batch fully confounded
with condition.

Checks an nf-core/rnaseq-style samplesheet:

    sample,fastq_1,fastq_2,strandedness

Exit code 0 if no errors (warnings allowed), 1 if any error is found.

Examples
--------
python validate_samplesheet.py --samplesheet samplesheet.csv
python validate_samplesheet.py --samplesheet samplesheet.csv \
    --metadata metadata.csv --condition-col condition
python validate_samplesheet.py --samplesheet sheet.csv --no-check-files  # skip local file existence

Requires: pandas.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

VALID_STRANDEDNESS = {"auto", "forward", "reverse", "unstranded"}
REMOTE_PREFIXES = ("http://", "https://", "ftp://", "s3://", "gs://", "az://")


class Report:
    """Collects errors (fatal) and warnings (advisory)."""

    def __init__(self) -> None:
        """Initialise the instance."""
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        """Handle error."""
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        """Handle warn."""
        self.warnings.append(msg)

    def summarize(self) -> int:
        """Summarize."""
        for w in self.warnings:
            print(f"  WARN  {w}")
        for e in self.errors:
            print(f"  ERROR {e}")
        print()
        if self.errors:
            print(f"FAILED: {len(self.errors)} error(s), {len(self.warnings)} warning(s)")
            return 1
        print(f"PASSED: 0 errors, {len(self.warnings)} warning(s)")
        return 0


def _is_remote(path: str) -> bool:
    """Return whether remote."""
    return str(path).startswith(REMOTE_PREFIXES)


def _check_fastq_file(label: str, fp: str, ln: int, sample: str, rep: Report) -> None:
    """Check one FASTQ path for existence and extension, recording errors or warnings."""
    if not fp:
        return
    if _is_remote(fp):
        rep.warn(f"row {ln} ({sample}): {label} is remote; existence not checked")
    elif not Path(fp).is_file():
        rep.error(f"row {ln} ({sample}): {label} not found: {fp}")
    elif not fp.endswith((".fastq.gz", ".fq.gz", ".fastq", ".fq")):
        rep.warn(f"row {ln} ({sample}): {label} has an unusual extension: {fp}")


def _check_sheet_row(row: pd.Series, ln: int, has_r2: bool, has_strand: bool,
                     check_files: bool, rep: Report) -> None:
    """Validate a single samplesheet row (required fields, strandedness, file paths)."""
    sample, r1 = row["sample"], row["fastq_1"]
    r2 = row["fastq_2"] if has_r2 else ""

    if not sample:
        rep.error(f"row {ln}: empty 'sample'")
    if not r1:
        rep.error(f"row {ln}: empty 'fastq_1'")
    if r1 and r2 and r1 == r2:
        rep.error(f"row {ln} ({sample}): fastq_1 and fastq_2 are the same file")

    if has_strand:
        s = row["strandedness"].lower()
        if s and s not in VALID_STRANDEDNESS:
            rep.error(f"row {ln} ({sample}): strandedness '{s}' not in {sorted(VALID_STRANDEDNESS)}")

    if check_files:
        for label, fp in (("fastq_1", r1), ("fastq_2", r2)):
            _check_fastq_file(label, fp, ln, sample, rep)


def _check_pairing_consistency(df: pd.DataFrame, rep: Report) -> None:
    """Flag samples that mix paired/single-end rows and samples spread over multiple rows."""
    for sample, grp in df.groupby("sample"):
        layouts = {"paired" if r2 else "single" for r2 in grp["fastq_2"]}
        if len(layouts) > 1:
            rep.error(f"sample '{sample}' mixes paired-end and single-end rows")
    dup_samples = df["sample"][df["sample"].duplicated()].unique()
    if len(dup_samples):
        rep.warn(f"samples appear on multiple rows (will be lane-merged): {list(dup_samples)}")


def validate_samplesheet(path: Path, check_files: bool, rep: Report) -> pd.DataFrame | None:
    """Validate the samplesheet CSV, recording problems on ``rep`` and returning the frame."""
    if not path.is_file():
        rep.error(f"samplesheet not found: {path}")
        return None

    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    for col in df.columns:
        df[col] = df[col].str.strip()

    if "sample" not in df.columns or "fastq_1" not in df.columns:
        rep.error("samplesheet must have at least 'sample' and 'fastq_1' columns")
        return None
    has_r2 = "fastq_2" in df.columns
    has_strand = "strandedness" in df.columns
    if not has_strand:
        rep.warn("no 'strandedness' column; nf-core/rnaseq recommends one (use 'auto')")

    seen_r1: dict[str, int] = {}
    for i, row in df.iterrows():
        ln = i + 2  # +1 for header, +1 for 1-based
        _check_sheet_row(row, ln, has_r2, has_strand, check_files, rep)
        r1 = row["fastq_1"]
        if r1:
            seen_r1[r1] = seen_r1.get(r1, 0) + 1

    for r1, n in seen_r1.items():
        if n > 1:
            rep.error(f"fastq_1 appears {n} times (each library file must be unique): {r1}")

    # Per-sample paired/single-end consistency (same sample over lanes is allowed in nf-core).
    if has_r2:
        _check_pairing_consistency(df, rep)

    print(f"samplesheet: {df['sample'].nunique()} unique sample(s) across {len(df)} row(s)")
    return df


def validate_metadata(meta_path: Path, sheet: pd.DataFrame | None,
                      condition_col: str, min_rep: int, rep: Report) -> None:
    """Validate metadata."""
    if not meta_path.is_file():
        rep.error(f"metadata not found: {meta_path}")
        return

    meta = pd.read_csv(meta_path, dtype=str, keep_default_na=False, index_col=0)
    meta.index = meta.index.astype(str).str.strip()

    if condition_col not in meta.columns:
        rep.error(f"metadata has no '{condition_col}' column (columns: {list(meta.columns)})")
        return

    # Cross-check sample IDs against the samplesheet.
    if sheet is not None:
        sheet_samples = set(sheet["sample"].unique())
        meta_samples = set(meta.index)
        missing = sheet_samples - meta_samples
        extra = meta_samples - sheet_samples
        if missing:
            rep.error(f"samples in samplesheet but missing from metadata: {sorted(missing)}")
        if extra:
            rep.warn(f"samples in metadata but not in samplesheet: {sorted(extra)}")

    # Replication per condition group.
    groups = meta[condition_col].replace("", pd.NA).dropna()
    if groups.empty:
        rep.error(f"'{condition_col}' is empty for all samples")
        return
    sizes = groups.value_counts()
    print(f"design: '{condition_col}' groups -> {sizes.to_dict()}")
    for level, n in sizes.items():
        if n < 2:
            rep.error(f"group '{level}' has {n} replicate(s); need >=2 to estimate variance")
        elif n < min_rep:
            rep.warn(f"group '{level}' has {n} replicate(s); >={min_rep} recommended for reliable DE")

    # Light confounding check: batch fully nested within condition.
    if "batch" in meta.columns and meta["batch"].replace("", pd.NA).notna().any():
        ct = pd.crosstab(meta[condition_col], meta["batch"])
        each_batch_single_condition = (ct > 0).sum(axis=0).eq(1).all()
        if ct.shape[0] > 1 and ct.shape[1] > 1 and each_batch_single_condition:
            rep.warn(
                "'batch' looks fully confounded with "
                f"'{condition_col}' (each batch holds a single condition); "
                "the batch effect cannot be separated from the biology. See design-and-qc.md."
            )


def main() -> None:
    """Run the command-line interface."""
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--samplesheet", type=Path, required=True, help="CSV samplesheet to validate.")
    p.add_argument("--metadata", type=Path, help="Optional design metadata CSV (index=sample).")
    p.add_argument("--condition-col", default="condition", help="Condition column in metadata (default: condition).")
    p.add_argument("--min-replicates", type=int, default=3, dest="min_rep",
                   help="Replicates per group to recommend (default: 3).")
    p.add_argument("--no-check-files", action="store_true", help="Skip local FASTQ existence checks.")
    args = p.parse_args()

    rep = Report()
    print(f"Validating {args.samplesheet} ...")
    sheet = validate_samplesheet(args.samplesheet, not args.no_check_files, rep)
    if args.metadata:
        print(f"Validating {args.metadata} ...")
        validate_metadata(args.metadata, sheet, args.condition_col, args.min_rep, rep)

    print()
    sys.exit(rep.summarize())


if __name__ == "__main__":
    main()
