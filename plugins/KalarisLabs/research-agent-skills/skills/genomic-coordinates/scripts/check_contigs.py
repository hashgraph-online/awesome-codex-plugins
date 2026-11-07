#!/usr/bin/env python3
"""Identify the assembly behind a file, and check that two files can be joined.

The two ways a genomics pipeline produces confident nonsense are a chr-prefix
mismatch (the join returns nothing, or worse, returns only the contigs that
happen to agree) and an assembly mismatch (the join succeeds and every
coordinate means something else). Both are visible in the contig list.

    python3 check_contigs.py --identify ref.fa.fai
    python3 check_contigs.py variants.vcf annotation.gtf ref.fa.fai
    python3 check_contigs.py peaks.bed --genome hg38.chrom.sizes

Exit codes: 0 compatible, 1 incompatible or unidentifiable, 2 usage error.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import canonical_contig, emit, naming_style  # noqa: E402

# Primary-chromosome lengths, read from the UCSC bigZips chrom.sizes for each
# assembly (hg19, hg38, hs1) and cross-checked against the NCBI assembly report
# for GRCh37.p13. Verified 2026-07-26.
#
# GRCh37 and hg19 are the same assembly for every contig here except chrM: UCSC
# kept the older NC_001807 mitochondrion (16,571 bp) while GRCh37 adopted the
# rCRS (16,569 bp). That two-base difference is the only signal in the primary
# chromosomes that tells the two apart, and it is why an hg19 BAM and a GRCh37
# VCF can disagree about every mitochondrial variant.
BUILDS: dict[str, dict[str, int]] = {
    "GRCh37/hg19": {
        "1": 249250621, "2": 243199373, "3": 198022430, "4": 191154276,
        "5": 180915260, "6": 171115067, "7": 159138663, "8": 146364022,
        "9": 141213431, "10": 135534747, "11": 135006516, "12": 133851895,
        "13": 115169878, "14": 107349540, "15": 102531392, "16": 90354753,
        "17": 81195210, "18": 78077248, "19": 59128983, "20": 63025520,
        "21": 48129895, "22": 51304566, "X": 155270560, "Y": 59373566,
    },
    "GRCh38/hg38": {
        "1": 248956422, "2": 242193529, "3": 198295559, "4": 190214555,
        "5": 181538259, "6": 170805979, "7": 159345973, "8": 145138636,
        "9": 138394717, "10": 133797422, "11": 135086622, "12": 133275309,
        "13": 114364328, "14": 107043718, "15": 101991189, "16": 90338345,
        "17": 83257441, "18": 80373285, "19": 58617616, "20": 64444167,
        "21": 46709983, "22": 50818468, "X": 156040895, "Y": 57227415,
    },
    "T2T-CHM13v2.0/hs1": {
        "1": 248387328, "2": 242696752, "3": 201105948, "4": 193574945,
        "5": 182045439, "6": 172126628, "7": 160567428, "8": 146259331,
        "9": 150617247, "10": 134758134, "11": 135127769, "12": 133324548,
        "13": 113566686, "14": 101161492, "15": 99753195, "16": 96330374,
        "17": 84276897, "18": 80542538, "19": 61707364, "20": 66210255,
        "21": 45090682, "22": 51324926, "X": 154259566, "Y": 62460029,
    },
}

MITO = {16571: "hg19 (UCSC NC_001807 chrM)", 16569: "GRCh37/38 (rCRS MT)"}

COLUMNS = ["file", "kind", "contigs", "naming", "assembly", "detail"]


# --------------------------------------------------------------------------
# readers
# --------------------------------------------------------------------------


def read_sizes(path: Path) -> tuple[dict[str, int], str]:
    """.fai, .chrom.sizes, or .genome -- name in column 1, length in column 2."""
    sizes = {}
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t") if "\t" in line else line.split()
        if len(parts) >= 2 and parts[1].isdigit():
            sizes[parts[0]] = int(parts[1])
    return sizes, "sizes"


def read_fasta_names(path: Path) -> tuple[dict[str, int], str]:
    """Read fasta names."""
    sizes: dict[str, int] = {}
    name, count = None, 0
    with path.open() as handle:
        for line in handle:
            if line.startswith(">"):
                if name is not None:
                    sizes[name] = count
                name, count = line[1:].split()[0], 0
            elif name is not None:
                count += len(line.strip())
    if name is not None:
        sizes[name] = count
    return sizes, "fasta"


def read_vcf(path: Path) -> tuple[dict[str, int], str]:
    """Prefer the ##contig header; fall back to the CHROM column."""
    header: dict[str, int] = {}
    seen: dict[str, int] = {}
    with path.open() as handle:
        for line in handle:
            if line.startswith("##contig="):
                ident = re.search(r"ID=([^,>]+)", line)
                length = re.search(r"length=(\d+)", line)
                if ident:
                    header[ident.group(1)] = int(length.group(1)) if length else 0
            elif not line.startswith("#") and line.strip():
                fields = line.split("\t")
                if len(fields) >= 2 and fields[1].isdigit():
                    pos = int(fields[1])
                    seen[fields[0]] = max(seen.get(fields[0], 0), pos)
    if header:
        return header, "vcf header"
    return seen, "vcf records (max POS, not contig length)"


def read_sam_header(path: Path) -> tuple[dict[str, int], str]:
    """Read sam header."""
    sizes: dict[str, int] = {}
    with path.open() as handle:
        for line in handle:
            if not line.startswith("@"):
                break
            if line.startswith("@SQ"):
                ident = re.search(r"SN:(\S+)", line)
                length = re.search(r"LN:(\d+)", line)
                if ident and length:
                    sizes[ident.group(1)] = int(length.group(1))
    return sizes, "sam header"


def read_intervals(path: Path, start_col: int, end_col: int) -> tuple[dict[str, int], str]:
    """BED/GTF/GFF: names from column 1, plus the largest coordinate observed."""
    sizes: dict[str, int] = {}
    with path.open() as handle:
        for line in handle:
            if not line.strip() or line.startswith(("#", "track", "browser")):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) <= end_col:
                continue
            try:
                far = max(int(fields[start_col]), int(fields[end_col]))
            except ValueError:
                continue
            sizes[fields[0]] = max(sizes.get(fields[0], 0), far)
    return sizes, "intervals (max coordinate, not contig length)"


def load(path: Path) -> tuple[dict[str, int], str]:
    """Load."""
    suffixes = [s.lower() for s in path.suffixes]
    name = path.name.lower()
    if name.endswith((".fai", ".chrom.sizes", ".sizes", ".genome")):
        return read_sizes(path)
    if ".vcf" in suffixes:
        return read_vcf(path)
    if ".sam" in suffixes or name.endswith(".header") or name.endswith(".header.txt"):
        return read_sam_header(path)
    if ".gtf" in suffixes or ".gff" in suffixes or ".gff3" in suffixes:
        return read_intervals(path, 3, 4)
    if ".bed" in suffixes or ".narrowpeak" in suffixes or ".broadpeak" in suffixes:
        return read_intervals(path, 1, 2)
    if ".fa" in suffixes or ".fasta" in suffixes or ".fna" in suffixes:
        return read_fasta_names(path)
    raise SystemExit(
        f"error: cannot tell what kind of file {path.name} is. Supported: "
        ".fai, .chrom.sizes, .vcf, .sam (header), .bed, .gtf, .gff, .fasta"
    )


# --------------------------------------------------------------------------
# identification
# --------------------------------------------------------------------------


def identify(sizes: dict[str, int], exact: bool) -> tuple[str, str]:
    """Match observed contig lengths against the known assemblies.

    ``exact`` is False for interval files, where the numbers are the largest
    coordinate seen rather than the contig length -- there the useful question is
    only whether anything overflows a candidate assembly.
    """
    folded = {canonical_contig(n): length for n, length in sizes.items()}
    mito = folded.get("M")

    scores = []
    for build, lengths in BUILDS.items():
        shared = [c for c in lengths if c in folded]
        if not shared:
            continue
        if exact:
            agree = sum(1 for c in shared if folded[c] == lengths[c])
        else:
            agree = sum(1 for c in shared if 0 < folded[c] <= lengths[c])
        scores.append((agree / len(shared), agree, len(shared), build))
    if not scores:
        return "unknown", "no primary chromosomes to match against"
    scores.sort(reverse=True)
    fraction, agree, total, build = scores[0]

    if not exact:
        fits = [b for f, _, _, b in scores if math.isclose(f, 1.0, rel_tol=0.0, abs_tol=0.0)]
        if len(fits) == 1:
            return f"consistent with {fits[0]}", "no coordinate overflows this assembly"
        if not fits:
            over = [c for c in folded if c in BUILDS[build] and folded[c] > BUILDS[build][c]]
            return "CONFLICT", (
                f"coordinates run past the end of every known assembly (closest is "
                f"{build}, overflowing on {', '.join(sorted(over)[:4])}); wrong "
                "assembly, or 1-based data written into a 0-based file"
            )
        return "ambiguous", f"coordinates fit any of: {', '.join(fits)}"

    if fraction < 0.9:
        return "unknown", (
            f"closest is {build} at {agree}/{total} chromosomes -- not a match"
        )
    detail = f"{agree}/{total} primary chromosome lengths match"
    if build == "GRCh37/hg19" and mito is not None:
        detail += f"; chrM is {mito} bp, i.e. {MITO.get(mito, 'a non-standard mitochondrion')}"
        if mito == 16571:
            build = "hg19"
        elif mito == 16569:
            build = "GRCh37"
    elif mito is not None and mito not in MITO:
        detail += f"; chrM length {mito} is not a standard human mitochondrion"
    if agree != total:
        wrong = [c for c in BUILDS[scores[0][3]] if c in folded and folded[c] != BUILDS[scores[0][3]][c]]
        detail += f"; disagrees on {', '.join(sorted(wrong))}"
    return build, detail


# --------------------------------------------------------------------------
# comparison
# --------------------------------------------------------------------------


def _naming_problem(loaded: list[tuple[Path, dict[str, int], str, bool]]) -> list[str]:
    """A problem message when the files use different contig naming styles."""
    styles = {path.name: naming_style(list(sizes)) for path, sizes, _, _ in loaded}
    distinct = {s for s in styles.values() if s != "empty"}
    if len(distinct) <= 1:
        return []
    detail = ", ".join(f"{name}={style}" for name, style in styles.items())
    return [
        f"contig naming differs between files ({detail}). A join on the raw "
        "name returns zero rows for every contig; rename one side first"
    ]


def _exact_length_clash(
    name_a: str, fold_a: dict[str, int], name_b: str, fold_b: dict[str, int], shared: set[str]
) -> list[str]:
    """Problem message when two exact files disagree on shared contig lengths."""
    clash = sorted(c for c in shared if fold_a[c] and fold_b[c] and fold_a[c] != fold_b[c])
    if not clash:
        return []
    example = clash[0]
    return [
        f"{name_a} and {name_b} disagree on contig length "
        f"for {', '.join(clash[:5])}"
        f"{'...' if len(clash) > 5 else ''} "
        f"(e.g. {example}: {fold_a[example]} vs {fold_b[example]}) -- "
        "these are different assemblies and their coordinates are "
        "not comparable"
    ]


def _overflow_problems(
    path_a: Path,
    fold_a: dict[str, int],
    exact_a: bool,
    path_b: Path,
    fold_b: dict[str, int],
    exact_b: bool,
    shared: set[str],
) -> list[str]:
    """Problem messages for an inexact file overflowing a declared contig length.

    One side holds only the largest coordinate observed, so equality proves
    nothing. Overflowing a declared contig length still does.
    """
    pairs = []
    if exact_b and not exact_a:
        pairs.append((path_a.name, fold_a, path_b.name, fold_b))
    if exact_a and not exact_b:
        pairs.append((path_b.name, fold_b, path_a.name, fold_a))
    problems: list[str] = []
    for name_hi, hi, name_lo, lo in pairs:
        over = sorted(c for c in shared if lo[c] and hi[c] > lo[c])
        if over:
            example = over[0]
            problems.append(
                f"{name_hi} has coordinates past the end of {name_lo} on "
                f"{', '.join(over[:5])}{'...' if len(over) > 5 else ''} "
                f"(e.g. {example}: {hi[example]} > {lo[example]}) -- "
                "wrong assembly, or an off-by-one from a 1-based source"
            )
    return problems


def _absent_contigs_problem(
    name_a: str, fold_a: dict[str, int], name_b: str, fold_b: dict[str, int]
) -> list[str]:
    """Problem message when many contigs of file A are absent from file B."""
    only_a = sorted(set(fold_a) - set(fold_b))
    if not (only_a and len(only_a) <= len(fold_a) / 2):
        return []
    return [
        f"{len(only_a)} contigs in {name_a} are absent from "
        f"{name_b} ({', '.join(only_a[:5])}"
        f"{'...' if len(only_a) > 5 else ''}); records on them are "
        "dropped silently by most tools"
    ]


def _compare_pair(
    first: tuple[Path, dict[str, int], str, bool], second: tuple[Path, dict[str, int], str, bool]
) -> list[str]:
    """Every problem a join between one pair of loaded files would hit."""
    path_a, sizes_a, _, exact_a = first
    path_b, sizes_b, _, exact_b = second
    fold_a = {canonical_contig(n): v for n, v in sizes_a.items()}
    fold_b = {canonical_contig(n): v for n, v in sizes_b.items()}
    shared = set(fold_a) & set(fold_b)
    if not shared:
        return [
            f"{path_a.name} and {path_b.name} share no contigs at all, "
            "even ignoring the chr prefix"
        ]

    if exact_a and exact_b:
        problems = _exact_length_clash(path_a.name, fold_a, path_b.name, fold_b, shared)
        problems += _absent_contigs_problem(path_a.name, fold_a, path_b.name, fold_b)
        return problems
    return _overflow_problems(path_a, fold_a, exact_a, path_b, fold_b, exact_b, shared)


def compare(loaded: list[tuple[Path, dict[str, int], str, bool]]) -> list[str]:
    """Report every reason a join between these files would go wrong.

    Each entry carries ``exact``: True when its numbers are declared contig
    lengths, False when they are only the largest coordinate observed. Two exact
    files must agree exactly; an inexact one can only ever be caught overflowing.
    """
    problems = _naming_problem(loaded)
    for i in range(len(loaded)):
        for j in range(i + 1, len(loaded)):
            problems.extend(_compare_pair(loaded[i], loaded[j]))
    return problems


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description="Identify assemblies and check contig compatibility between files."
    )
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument(
        "--identify",
        action="store_true",
        help="only report the assembly of each file, skipping the cross-file checks",
    )
    parser.add_argument(
        "--genome",
        type=Path,
        help="a .chrom.sizes/.fai to check every other file against",
    )
    parser.add_argument("--format", choices=("tsv", "json"), default="tsv")
    parser.add_argument("-o", "--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)

    paths = list(args.files)
    if args.genome:
        paths.append(args.genome)
    for path in paths:
        if not path.exists():
            print(f"error: no such file: {path}", file=sys.stderr)
            return 2

    loaded = []
    rows = []
    for path in paths:
        sizes, kind = load(path)
        exact = kind in {"sizes", "fasta", "vcf header", "sam header"}
        loaded.append((path, sizes, kind, exact))
        assembly, detail = identify(sizes, exact)
        rows.append(
            {
                "file": path.name,
                "kind": kind,
                "contigs": len(sizes),
                "naming": naming_style(list(sizes)),
                "assembly": assembly,
                "detail": detail,
            }
        )

    emit(rows, COLUMNS, args.format, args.output)
    sys.stdout.flush()

    failed = any(r["assembly"] == "CONFLICT" for r in rows)
    if not args.identify and len(loaded) > 1:
        problems = compare(loaded)
        if problems:
            failed = True
            print("\nincompatibilities:", file=sys.stderr)
            for problem in problems:
                print(f"  - {problem}", file=sys.stderr)
        else:
            print("\nno contig incompatibilities found", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
