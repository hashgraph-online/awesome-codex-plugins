#!/usr/bin/env python3
"""Closed capability registry and lightweight format checks for EDA tools."""

from __future__ import annotations

import itertools
import zipfile
from pathlib import Path
from typing import Any

from _common import (
    MAX_COMPRESSION_RATIO,
    MAX_NPZ_MEMBERS,
    MAX_NPZ_UNCOMPRESSED_BYTES,
    CliError,
)


_REF_GENERAL = "references/general_scientific_formats.md"
_REF_BIO = "references/bioinformatics_genomics_formats.md"
_REF_CHEM = "references/chemistry_molecular_formats.md"
_REF_IMAGING = "references/microscopy_imaging_formats.md"
_REF_SPECTRO = "references/spectroscopy_analytical_formats.md"
_REF_PROTEOMICS = "references/proteomics_metabolomics_formats.md"
_DEP_STDLIB = "Python standard library"
_DEP_BIOPYTHON = "biopython==1.87"
_DEP_PILLOW = "pillow==12.3.0"
_DEP_TIFFFILE = "tifffile==2026.7.14"
_DEPTH_SEQUENCE = "bounded record sample with length, alphabet, and GC aggregates"
_DEPTH_PIXELS_NOT_DECODED = "container metadata only; pixels are not decoded"
_NOTE_VENDOR_READER = "vendor-aware reader required; no bundled parser"
_NOTE_TRAJECTORY = "topology-dependent trajectory tooling required"


AUTOMATED_FORMATS: dict[str, dict[str, Any]] = {
    ".csv": {
        "format": "CSV",
        "tier": "automated_core",
        "depth": "bounded schema, aggregate profile, missingness, and sensitivity audit",
        "dependency": _DEP_STDLIB,
        "reference": _REF_GENERAL,
    },
    ".tsv": {
        "format": "TSV",
        "tier": "automated_core",
        "depth": "bounded schema, aggregate profile, missingness, and sensitivity audit",
        "dependency": _DEP_STDLIB,
        "reference": _REF_GENERAL,
    },
    ".json": {
        "format": "JSON",
        "tier": "automated_core",
        "depth": "bounded strict parse and structural aggregate profile",
        "dependency": _DEP_STDLIB,
        "reference": _REF_GENERAL,
    },
    ".npy": {
        "format": "NumPy NPY",
        "tier": "automated_optional",
        "depth": "header, shape, dtype, and bounded numeric sample",
        "dependency": "numpy==2.5.1",
        "reference": _REF_GENERAL,
    },
    ".npz": {
        "format": "NumPy NPZ",
        "tier": "automated_optional",
        "depth": "ZIP bomb preflight plus per-array bounded inspection",
        "dependency": "numpy==2.5.1",
        "reference": _REF_GENERAL,
    },
    ".h5": {
        "format": "HDF5",
        "tier": "automated_optional",
        "depth": "bounded hierarchy and dataset metadata; no dataset values or external links",
        "dependency": "h5py==3.16.0",
        "reference": _REF_GENERAL,
    },
    ".hdf5": {
        "format": "HDF5",
        "tier": "automated_optional",
        "depth": "bounded hierarchy and dataset metadata; no dataset values or external links",
        "dependency": "h5py==3.16.0",
        "reference": _REF_GENERAL,
    },
    ".fasta": {
        "format": "FASTA",
        "tier": "automated_optional",
        "depth": _DEPTH_SEQUENCE,
        "dependency": _DEP_BIOPYTHON,
        "reference": _REF_BIO,
    },
    ".fa": {
        "format": "FASTA",
        "tier": "automated_optional",
        "depth": _DEPTH_SEQUENCE,
        "dependency": _DEP_BIOPYTHON,
        "reference": _REF_BIO,
    },
    ".fna": {
        "format": "FASTA",
        "tier": "automated_optional",
        "depth": _DEPTH_SEQUENCE,
        "dependency": _DEP_BIOPYTHON,
        "reference": _REF_BIO,
    },
    ".fastq": {
        "format": "FASTQ",
        "tier": "automated_optional",
        "depth": "bounded record sample with length, GC, and Phred+33 aggregates",
        "dependency": _DEP_BIOPYTHON,
        "reference": _REF_BIO,
    },
    ".fq": {
        "format": "FASTQ",
        "tier": "automated_optional",
        "depth": "bounded record sample with length, GC, and Phred+33 aggregates",
        "dependency": _DEP_BIOPYTHON,
        "reference": _REF_BIO,
    },
    ".png": {
        "format": "PNG",
        "tier": "automated_optional",
        "depth": _DEPTH_PIXELS_NOT_DECODED,
        "dependency": _DEP_PILLOW,
        "reference": _REF_IMAGING,
    },
    ".jpg": {
        "format": "JPEG",
        "tier": "automated_optional",
        "depth": _DEPTH_PIXELS_NOT_DECODED,
        "dependency": _DEP_PILLOW,
        "reference": _REF_IMAGING,
    },
    ".jpeg": {
        "format": "JPEG",
        "tier": "automated_optional",
        "depth": _DEPTH_PIXELS_NOT_DECODED,
        "dependency": _DEP_PILLOW,
        "reference": _REF_IMAGING,
    },
    ".tif": {
        "format": "TIFF",
        "tier": "automated_optional",
        "depth": "bounded TIFF series/page metadata only; pixels are not decoded",
        "dependency": _DEP_TIFFFILE,
        "reference": _REF_IMAGING,
    },
    ".tiff": {
        "format": "TIFF",
        "tier": "automated_optional",
        "depth": "bounded TIFF series/page metadata only; pixels are not decoded",
        "dependency": _DEP_TIFFFILE,
        "reference": _REF_IMAGING,
    },
    ".ome.tif": {
        "format": "OME-TIFF",
        "tier": "automated_optional",
        "depth": "bounded TIFF/OME structural metadata only; OME-XML and pixels are not emitted",
        "dependency": _DEP_TIFFFILE,
        "reference": _REF_IMAGING,
    },
    ".ome.tiff": {
        "format": "OME-TIFF",
        "tier": "automated_optional",
        "depth": "bounded TIFF/OME structural metadata only; OME-XML and pixels are not emitted",
        "dependency": _DEP_TIFFFILE,
        "reference": _REF_IMAGING,
    },
}


def _reference(
    format_name: str,
    reference: str,
    note: str,
) -> dict[str, str]:
    """Handle reference."""
    return {
        "format": format_name,
        "tier": "reference_only",
        "depth": note,
        "dependency": "manual or separately validated domain tooling",
        "reference": reference,
    }


REFERENCE_ONLY_FORMATS: dict[str, dict[str, str]] = {
    # General tabular/array containers
    ".parquet": _reference(
        "Apache Parquet",
        _REF_GENERAL,
        "documented pandas/Polars/Arrow workflow; no bundled parser",
    ),
    ".feather": _reference(
        "Apache Feather",
        _REF_GENERAL,
        "documented columnar workflow; no bundled parser",
    ),
    ".xlsx": _reference(
        "Excel OOXML",
        _REF_GENERAL,
        "manual workbook review required, including formulas and hidden content",
    ),
    ".xls": _reference(
        "Legacy Excel",
        _REF_GENERAL,
        "manual workbook review required; macros are never executed",
    ),
    ".zarr": _reference(
        "Zarr",
        _REF_GENERAL,
        "directory/store format is not accepted by bundled file inspectors",
    ),
    ".nc": _reference(
        "NetCDF",
        _REF_GENERAL,
        "documented xarray/netCDF workflow; no bundled parser",
    ),
    ".mat": _reference(
        "MATLAB MAT",
        _REF_GENERAL,
        "manual version-aware workflow; no bundled parser",
    ),
    ".fits": _reference(
        "FITS",
        _REF_GENERAL,
        "documented Astropy workflow; no bundled parser",
    ),
    # Bioinformatics/genomics
    ".sam": _reference(
        "SAM",
        _REF_BIO,
        "use a pinned SAM/BAM validator; no bundled parser",
    ),
    ".bam": _reference(
        "BAM",
        _REF_BIO,
        "use a pinned SAM/BAM validator; no bundled parser",
    ),
    ".cram": _reference(
        "CRAM",
        _REF_BIO,
        "reference-aware validation required; no bundled parser",
    ),
    ".vcf": _reference(
        "VCF",
        _REF_BIO,
        "use a pinned VCF validator; no bundled parser",
    ),
    ".bcf": _reference(
        "BCF",
        _REF_BIO,
        "use a pinned VCF/BCF validator; no bundled parser",
    ),
    ".bed": _reference(
        "BED",
        _REF_BIO,
        "assembly-aware interval validation required; no bundled parser",
    ),
    ".gff": _reference(
        "GFF",
        _REF_BIO,
        "version-aware annotation validation required; no bundled parser",
    ),
    ".gff3": _reference(
        "GFF3",
        _REF_BIO,
        "version-aware annotation validation required; no bundled parser",
    ),
    ".gtf": _reference(
        "GTF",
        _REF_BIO,
        "annotation-specific validation required; no bundled parser",
    ),
    ".h5ad": _reference(
        "AnnData H5AD",
        _REF_BIO,
        "generic HDF5 metadata is not AnnData semantic validation",
    ),
    ".loom": _reference(
        "Loom",
        _REF_BIO,
        "generic HDF5 metadata is not Loom semantic validation",
    ),
    ".mtx": _reference(
        "Matrix Market",
        _REF_BIO,
        "matrix and sidecar alignment require domain tooling",
    ),
    # Chemistry/molecular
    ".pdb": _reference(
        "Legacy PDB",
        _REF_CHEM,
        "wwPDB-aware structural validation required; no bundled parser",
    ),
    ".cif": _reference(
        "CIF or PDBx/mmCIF",
        _REF_CHEM,
        "extension is ambiguous; dictionary-aware validation required",
    ),
    ".mmcif": _reference(
        "PDBx/mmCIF",
        _REF_CHEM,
        "wwPDB dictionary-aware validation required; no bundled parser",
    ),
    ".mol": _reference(
        "MDL Molfile",
        _REF_CHEM,
        "chemistry-aware validation required; no bundled parser",
    ),
    ".sdf": _reference(
        "Structure Data File",
        _REF_CHEM,
        "chemistry-aware validation required; no bundled parser",
    ),
    ".smi": _reference(
        "SMILES table",
        _REF_CHEM,
        "line notation requires chemistry-aware parsing; no bundled parser",
    ),
    ".xyz": _reference(
        "XYZ coordinates",
        _REF_CHEM,
        "units and record boundaries require explicit confirmation",
    ),
    ".dcd": _reference(
        "DCD trajectory",
        _REF_CHEM,
        _NOTE_TRAJECTORY,
    ),
    ".xtc": _reference(
        "XTC trajectory",
        _REF_CHEM,
        _NOTE_TRAJECTORY,
    ),
    ".trr": _reference(
        "TRR trajectory",
        _REF_CHEM,
        _NOTE_TRAJECTORY,
    ),
    # Imaging beyond the bounded metadata inspectors
    ".nd2": _reference(
        "Nikon ND2",
        _REF_IMAGING,
        _NOTE_VENDOR_READER,
    ),
    ".czi": _reference(
        "Zeiss CZI",
        _REF_IMAGING,
        _NOTE_VENDOR_READER,
    ),
    ".lif": _reference(
        "Leica LIF",
        _REF_IMAGING,
        _NOTE_VENDOR_READER,
    ),
    ".dcm": _reference(
        "DICOM",
        _REF_IMAGING,
        "PHI-aware DICOM tooling and policy required",
    ),
    ".nii": _reference(
        "NIfTI",
        _REF_IMAGING,
        "orientation-aware neuroimaging tooling required",
    ),
    ".nii.gz": _reference(
        "Compressed NIfTI",
        _REF_IMAGING,
        "compressed content is not decompressed by bundled tools",
    ),
    ".mrc": _reference(
        "MRC",
        _REF_IMAGING,
        "electron-microscopy-aware tooling required",
    ),
    ".svs": _reference(
        "Aperio SVS",
        _REF_IMAGING,
        "whole-slide reader and privacy review required",
    ),
    ".ndpi": _reference(
        "Hamamatsu NDPI",
        _REF_IMAGING,
        "whole-slide reader and privacy review required",
    ),
    # Spectroscopy/proteomics/metabolomics
    ".mzml": _reference(
        "HUPO-PSI mzML",
        _REF_SPECTRO,
        "schema/CV-aware mass-spectrometry tooling required",
    ),
    ".mzxml": _reference(
        "mzXML",
        _REF_SPECTRO,
        "legacy MS tooling required; no bundled parser",
    ),
    ".jdx": _reference(
        "JCAMP-DX",
        _REF_SPECTRO,
        "technique/version-aware JCAMP parser required",
    ),
    ".dx": _reference(
        "JCAMP-DX",
        _REF_SPECTRO,
        "technique/version-aware JCAMP parser required",
    ),
    ".spc": _reference(
        "SPC",
        _REF_SPECTRO,
        "vendor/variant-aware reader required",
    ),
    ".mgf": _reference(
        "Mascot Generic Format",
        _REF_SPECTRO,
        "MS-specific parser required; no bundled parser",
    ),
    ".raw": _reference(
        "Ambiguous vendor RAW",
        _REF_SPECTRO,
        "extension alone cannot identify the vendor format",
    ),
    ".mzid": _reference(
        "mzIdentML",
        _REF_PROTEOMICS,
        "schema/CV-aware identification tooling required",
    ),
    ".mzidentml": _reference(
        "mzIdentML",
        _REF_PROTEOMICS,
        "schema/CV-aware identification tooling required",
    ),
    ".pepxml": _reference(
        "pepXML",
        _REF_PROTEOMICS,
        "search-engine-aware parser required",
    ),
    ".protxml": _reference(
        "protXML",
        _REF_PROTEOMICS,
        "protein-inference-aware parser required",
    ),
    ".mztab": _reference(
        "mzTab or mzTab-M",
        _REF_PROTEOMICS,
        "version-aware PSI validation required; generic TSV parsing is insufficient",
    ),
    ".featurexml": _reference(
        "OpenMS featureXML",
        _REF_PROTEOMICS,
        "OpenMS-aware parser required",
    ),
}


def suffix_key(path: Path) -> str:
    """Return a registered compound or simple suffix, failing closed otherwise."""

    name = path.name.casefold()
    keys = sorted(
        {*AUTOMATED_FORMATS, *REFERENCE_ONLY_FORMATS},
        key=len,
        reverse=True,
    )
    for key in keys:
        if name.endswith(key):
            return key
    raise CliError("unknown format; no content sniffing or generic fallback is allowed")


def capability_for_path(path: Path) -> dict[str, Any]:
    """Return a copy of the closed capability entry for a path."""

    key = suffix_key(path)
    entry = AUTOMATED_FORMATS.get(key) or REFERENCE_ONLY_FORMATS[key]
    return {"suffix": key, **entry}


def _first_nonempty_text_byte(path: Path, *, limit: int = 8192) -> bytes | None:
    """Handle first nonempty text byte."""
    with path.open("rb") as handle:
        chunk = handle.read(limit)
    for line in chunk.splitlines():
        stripped = line.lstrip()
        if stripped:
            return stripped[:1]
    return None


def validate_magic(path: Path, suffix: str) -> None:
    """Check unambiguous signatures without guessing an unsupported format."""

    try:
        with path.open("rb") as handle:
            prefix = handle.read(16)
    except OSError as exc:
        raise CliError("the input header could not be read") from exc

    if suffix == ".npy" and not prefix.startswith(b"\x93NUMPY"):
        raise CliError("the NPY signature does not match the declared suffix")
    if suffix == ".npz" and not prefix.startswith(b"PK"):
        raise CliError("the NPZ ZIP signature does not match the declared suffix")
    if suffix in {".h5", ".hdf5"}:
        signature = b"\x89HDF\r\n\x1a\n"
        found = False
        with path.open("rb") as handle:
            for offset in itertools.takewhile(
                lambda value: value < max(path.stat().st_size, 1),
                (0, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536),
            ):
                handle.seek(offset)
                if handle.read(8) == signature:
                    found = True
                    break
        if not found:
            raise CliError("the HDF5 signature does not match the declared suffix")
    if suffix in {".fasta", ".fa", ".fna"} and _first_nonempty_text_byte(path) != b">":
        raise CliError("the FASTA record marker does not match the declared suffix")
    if suffix in {".fastq", ".fq"} and _first_nonempty_text_byte(path) != b"@":
        raise CliError("the FASTQ record marker does not match the declared suffix")
    if suffix == ".png" and not prefix.startswith(b"\x89PNG\r\n\x1a\n"):
        raise CliError("the PNG signature does not match the declared suffix")
    if suffix in {".jpg", ".jpeg"} and not prefix.startswith(b"\xff\xd8\xff"):
        raise CliError("the JPEG signature does not match the declared suffix")
    tiff_signatures = (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+")
    if suffix in {".tif", ".tiff", ".ome.tif", ".ome.tiff"} and not prefix.startswith(
        tiff_signatures
    ):
        raise CliError("the TIFF signature does not match the declared suffix")


def preflight_npz(path: Path) -> dict[str, Any]:
    """Reject encrypted, traversing, oversized, or high-ratio NPZ members."""

    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise CliError("the NPZ container is not a valid bounded ZIP archive") from exc
    if not members or len(members) > MAX_NPZ_MEMBERS:
        raise CliError(
            f"the NPZ member count must be between 1 and {MAX_NPZ_MEMBERS}"
        )
    total_uncompressed = 0
    highest_ratio = 0.0
    member_names: set[str] = set()
    for member in members:
        member_path = Path(member.filename)
        normalized_name = member.filename.replace("\\", "/")
        normalized_parts = Path(normalized_name).parts
        if (
            member.is_dir()
            or member_path.is_absolute()
            or normalized_name.startswith("/")
            or ":" in normalized_name
            or ".." in normalized_parts
        ):
            raise CliError("the NPZ contains an invalid member path")
        if normalized_name in member_names:
            raise CliError("the NPZ contains duplicate member names")
        member_names.add(normalized_name)
        if member.flag_bits & 0x1:
            raise CliError("encrypted NPZ members are not accepted")
        if not member.filename.casefold().endswith(".npy"):
            raise CliError("every NPZ member must be an NPY array")
        total_uncompressed += member.file_size
        denominator = max(member.compress_size, 1)
        highest_ratio = max(highest_ratio, member.file_size / denominator)
    if total_uncompressed > MAX_NPZ_UNCOMPRESSED_BYTES:
        raise CliError(
            "the NPZ declared uncompressed size exceeds the safety limit"
        )
    if highest_ratio > MAX_COMPRESSION_RATIO:
        raise CliError("the NPZ compression ratio exceeds the safety limit")
    return {
        "member_count": len(members),
        "declared_uncompressed_bytes": total_uncompressed,
        "maximum_compression_ratio": round(highest_ratio, 3),
    }


def automated_capability_rows() -> list[dict[str, Any]]:
    """Return deterministic rows for the public capability matrix."""

    return [
        {"suffix": suffix, **AUTOMATED_FORMATS[suffix]}
        for suffix in sorted(AUTOMATED_FORMATS)
    ]
