#!/usr/bin/env python3
"""Audit DICOM metadata for bounded de-identification review signals."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from _common import (
    DEFAULT_MAX_ELEMENTS,
    DEFAULT_MAX_FILES,
    DEFAULT_MAX_INPUT_BYTES,
    HARD_MAX_ELEMENTS,
    HARD_MAX_FILES,
    HARD_MAX_INPUT_BYTES,
    MAX_SEQUENCE_DEPTH,
    SCHEMA_VERSION,
    SENSITIVE_KEYWORDS,
    STRUCTURAL_UID_KEYWORDS,
    TEXT_VRS,
    UID_REMAP_KEYWORDS,
    ToolError,
    bounded_int,
    checked_input,
    collect_local_files,
    counter_dict,
    element_tag,
    fail_json,
    load_json,
    parse_size,
    safe_dcmread,
    starter_profile,
    validate_profile,
    write_or_emit_report,
)

TOOL = "deidentification_audit"
PIXEL_METADATA = {
    "BitsAllocated",
    "BitsStored",
    "Columns",
    "DoubleFloatPixelData",
    "FloatPixelData",
    "NumberOfFrames",
    "PhotometricInterpretation",
    "PixelData",
    "Rows",
    "SamplesPerPixel",
}
BULK_OR_CONTENT_KEYWORDS = {
    "AcquisitionContextSequence",
    "AudioSampleData",
    "ContentSequence",
    "EncapsulatedDocument",
    "GraphicAnnotationSequence",
    "IconImageSequence",
    "SpectroscopyData",
    "WaveformData",
}


def _has_value(element: Any) -> bool:
    """Return whether value."""
    value = element.value
    if value is None:
        return False
    if isinstance(value, (str, bytes)):
        return bool(value)
    try:
        return len(value) > 0
    except TypeError:
        return True


@dataclass
class _AuditState:
    """Mutable tallies accumulated while walking a dataset."""

    categories: Counter[str] = field(default_factory=Counter)
    residual_keywords: Counter[str] = field(default_factory=Counter)
    unclassified_text: Counter[str] = field(default_factory=Counter)
    unclassified_uids: Counter[str] = field(default_factory=Counter)
    image_metadata_present: bool = False


def _tally_element_flags(
    element: Any, keyword: str, has_value: bool, state: _AuditState
) -> None:
    """Tally pixel metadata, bulk content, private and overlay/curve elements."""
    categories = state.categories
    if keyword in PIXEL_METADATA:
        state.image_metadata_present = True
    if keyword in BULK_OR_CONTENT_KEYWORDS:
        categories["bulk_or_structured_content_elements"] += 1
    if element.tag.is_private:
        categories["private_elements"] += 1
        if has_value:
            categories["nonempty_private_elements"] += 1
    group = int(element.tag.group)
    if 0x5000 <= group <= 0x50FF or 0x6000 <= group <= 0x60FF:
        categories["curve_or_overlay_elements"] += 1


def _tally_profile_action(
    action: str | None, keyword: str, has_value: bool, state: _AuditState
) -> None:
    """Tally residual values left behind by remove/empty/pseudonym/keep actions."""
    if not has_value:
        return
    if action in {"remove", "empty"}:
        state.residual_keywords[keyword] += 1
        state.categories["profile_action_residuals"] += 1
    elif action == "pseudonym":
        state.categories["pseudonym_values_requiring_provenance_review"] += 1
    elif action == "keep":
        state.categories["explicit_profile_retention"] += 1


def _tally_uid(keyword: str, state: _AuditState) -> None:
    """Classify a UI element as structural, instance, or unclassified."""
    if keyword in STRUCTURAL_UID_KEYWORDS:
        state.categories["structural_uid_elements"] += 1
    elif keyword in UID_REMAP_KEYWORDS or keyword.endswith(
        ("InstanceUID", "FrameOfReferenceUID")
    ):
        state.categories["instance_uid_elements"] += 1
    else:
        state.unclassified_uids[keyword] += 1


def _tally_value(vr: str, keyword: str, state: _AuditState) -> None:
    """Tally date/time, UID, sensitive-keyword and free-text elements that carry values."""
    if vr in {"DA", "DT", "TM"}:
        state.categories["nonempty_date_or_time_elements"] += 1
    if vr == "UI":
        _tally_uid(keyword, state)
    if keyword in SENSITIVE_KEYWORDS:
        state.categories["known_sensitive_elements_present"] += 1
    elif vr in TEXT_VRS and keyword not in {"SpecificCharacterSet"}:
        state.unclassified_text[keyword] += 1


def _audit_summary(
    dataset: Any, state: _AuditState, elements: int, file_id: str
) -> dict[str, Any]:
    """Build the per-file audit record from the accumulated tallies."""
    categories = state.categories
    burned_in = str(dataset.get("BurnedInAnnotation", "")).strip().upper()
    recognizable = str(dataset.get("RecognizableVisualFeatures", "")).strip().upper()
    identity_removed = str(dataset.get("PatientIdentityRemoved", "")).strip().upper()
    pixel_review_required = state.image_metadata_present
    high_risk_findings = (
        categories["nonempty_private_elements"]
        + categories["profile_action_residuals"]
        + categories["curve_or_overlay_elements"]
        + categories["bulk_or_structured_content_elements"]
        + len(state.unclassified_text)
        + len(state.unclassified_uids)
    )
    if state.image_metadata_present and burned_in != "NO":
        high_risk_findings += 1
    return {
        "burned_in_annotation": burned_in or "ABSENT",
        "categories": counter_dict(categories),
        "elements_examined": elements,
        "file_id": file_id,
        "high_risk_findings": high_risk_findings,
        "patient_identity_removed_claim": identity_removed or "ABSENT",
        "pixel_review_required": pixel_review_required,
        "profile_action_residuals_by_keyword": counter_dict(state.residual_keywords),
        "recognizable_visual_features": recognizable or "ABSENT",
        "review_passed": high_risk_findings == 0 and not pixel_review_required,
        "unclassified_text_by_keyword": counter_dict(state.unclassified_text),
        "unclassified_uids_by_keyword": counter_dict(state.unclassified_uids),
    }


def _audit_element(
    element: Any,
    depth: int,
    actions: dict[str, str],
    state: _AuditState,
    stack: list[tuple[Any, int]],
) -> None:
    """Tally one element and queue sequence items for later traversal."""
    keyword = element.keyword or element_tag(element)
    vr = str(element.VR)
    has_value = _has_value(element)

    _tally_element_flags(element, keyword, has_value, state)
    action = actions.get(keyword, actions.get(element_tag(element)))
    _tally_profile_action(action, keyword, has_value, state)

    if vr == "SQ":
        for item in reversed(list(element.value)):
            stack.append((item, depth + 1))
    elif has_value:
        _tally_value(vr, keyword, state)


def audit_dataset(
    dataset: Any,
    *,
    profile: dict[str, Any],
    file_id: str,
    max_elements: int,
) -> dict[str, Any]:
    """Walk a dataset (including sequences) and summarise de-identification review signals."""
    actions = profile["actions"]
    state = _AuditState()
    stack: list[tuple[Any, int]] = [(dataset, 0)]
    elements = 0
    while stack:
        current, depth = stack.pop()
        if depth > MAX_SEQUENCE_DEPTH:
            raise ToolError("sequence nesting exceeds the hard depth limit")
        for element in current:
            elements += 1
            if elements > max_elements:
                raise ToolError("data-element limit exceeded")
            _audit_element(element, depth, actions, state, stack)

    return _audit_summary(dataset, state, elements, file_id)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    """Build report."""
    max_input_bytes = parse_size(
        args.max_input_bytes,
        name="max_input_bytes",
        maximum=HARD_MAX_INPUT_BYTES,
    )
    max_files = bounded_int(
        args.max_files,
        name="max_files",
        minimum=1,
        maximum=HARD_MAX_FILES,
    )
    max_elements = bounded_int(
        args.max_elements,
        name="max_elements",
        minimum=1,
        maximum=HARD_MAX_ELEMENTS,
    )
    source = checked_input(
        args.input,
        root=args.root,
        kind="any",
        max_bytes=max_input_bytes,
    )
    files = collect_local_files(
        source,
        max_files=max_files,
        max_bytes=max_input_bytes,
        recursive=args.recursive,
    )
    profile = starter_profile()
    profile_source = "built-in"
    if args.profile_json:
        profile_path = checked_input(
            args.profile_json,
            root=args.root,
            kind="file",
            max_bytes=1 * 1024 * 1024,
        )
        profile = validate_profile(load_json(profile_path))
        profile_source = "local-json"
    records: list[dict[str, Any]] = []
    parse_failures = 0
    for index, path in enumerate(files, start=1):
        try:
            dataset = safe_dcmread(
                path,
                stop_before_pixels=True,
                force=args.force_dicom_read,
            )
            records.append(
                audit_dataset(
                    dataset,
                    profile=profile,
                    file_id=f"file-{index:06d}",
                    max_elements=max_elements,
                )
            )
        except ToolError:
            parse_failures += 1
            records.append(
                {
                    "file_id": f"file-{index:06d}",
                    "high_risk_findings": 1,
                    "parse_failed": True,
                    "pixel_review_required": True,
                    "review_passed": False,
                }
            )
    category_totals: Counter[str] = Counter()
    for record in records:
        category_totals.update(record.get("categories", {}))
    review_failures = sum(not record["review_passed"] for record in records)
    return {
        "aggregate": {
            "categories": counter_dict(category_totals),
            "files_examined": len(records),
            "parse_failures": parse_failures,
            "pixel_review_files": sum(
                bool(record.get("pixel_review_required")) for record in records
            ),
            "review_failure_files": review_failures,
        },
        "file_names_emitted": False,
        "metadata_only": True,
        "network_accessed": False,
        "not_a_compliance_determination": True,
        "ok": bool(records),
        "profile": {
            "name": profile["name"],
            "source": profile_source,
            "version": profile["version"],
        },
        "records": records,
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "warnings": [
            "Attribute auditing cannot establish that an Information Object is de-identified.",
            "Patient Identity Removed=YES is not treated as proof.",
            "Pixels, recognizable visual features, graphics, overlays, structured content, private data, and external context require expert review.",
            "Profile and regulatory applicability are purpose, recipient, jurisdiction, and risk specific.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Audit bounded DICOM metadata for residual identifier categories; "
            "never claims de-identification or regulatory compliance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Local authorized data only. This metadata-only audit never decompresses pixels.
It is one input to a context-specific expert de-identification review, not a
replacement for DICOM PS3.15 profile selection or re-identification risk analysis.

Examples:
  python deidentification_audit.py candidate.dcm
  python deidentification_audit.py export-dir --recursive --output audit.json
  python deidentification_audit.py candidate.dcm --profile-json site-profile.json
""",
    )
    parser.add_argument("input", help="Local DICOM file or directory")
    parser.add_argument("--root", default=".", help="Existing local I/O root")
    parser.add_argument(
        "--recursive", action="store_true", help="Recursively inspect directories"
    )
    parser.add_argument("--profile-json", help="Local bounded action-profile JSON")
    parser.add_argument("--output", "-o", help="Private JSON report path")
    parser.add_argument(
        "--force-dicom-read",
        action="store_true",
        help="Parse missing File Format headers; does not validate them",
    )
    parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Exit 1 when any file requires review",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=DEFAULT_MAX_FILES,
        help=f"Maximum files (default: {DEFAULT_MAX_FILES})",
    )
    parser.add_argument(
        "--max-elements",
        type=int,
        default=DEFAULT_MAX_ELEMENTS,
        help=f"Maximum elements per file (default: {DEFAULT_MAX_ELEMENTS})",
    )
    parser.add_argument(
        "--max-input-bytes",
        default=str(DEFAULT_MAX_INPUT_BYTES),
        help="Maximum bytes per input file",
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite an existing report only"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    args = build_parser().parse_args(argv)
    try:
        report = build_report(args)
        write_or_emit_report(report, args, TOOL)
        findings = report["aggregate"]["review_failure_files"]
        if args.fail_on_findings and findings:
            return 1
        return 0 if report["ok"] else 1
    except Exception as exc:  # noqa: BLE001 - sanitize unexpected library errors
        return fail_json(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
