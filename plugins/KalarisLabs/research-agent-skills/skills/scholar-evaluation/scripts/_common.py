#!/usr/bin/env python3
"""Bounded, dependency-free helpers for local scholar-evaluation records."""

from __future__ import annotations
# research-agent-skills: utf-8 console output
import sys as _ras_sys
for _ras_stream in (_ras_sys.stdout, _ras_sys.stderr):
    if hasattr(_ras_stream, "reconfigure"):
        _ras_stream.reconfigure(encoding="utf-8", errors="replace")

import json
import math
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "2.0"
NOTICE = (
    "DESCRIPTIVE DEVELOPMENTAL ASSESSMENT ONLY — NOT A DECISION "
    "RECOMMENDATION — QUALIFIED HUMAN REVIEW REQUIRED"
)
PROHIBITED_USES = {
    "admissions",
    "awards",
    "discipline",
    "funding",
    "hiring",
    "promotion",
    "tenure",
    "other_high_impact_personnel_decision",
}
ALLOWED_PURPOSE = "developmental_review_of_scholarly_work"
ALLOWED_UNIT = "scholarly_work"
ALLOWED_CLASSIFICATIONS = {
    "synthetic",
    "public_scholarly_work",
    "deidentified_low_stakes",
}
RATING_STATUSES = {"rated", "missing", "not_applicable"}

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_TEXT_CHARS = 4_000
MAX_LIST_ITEMS = 1_000
MAX_OBJECT_FIELDS = 100
MAX_DEPTH = 20
MAX_TOTAL_NODES = 25_000
MAX_CRITERIA = 50
MAX_EVALUATIONS = 50
MAX_CSV_ROWS = 20_000

IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]{1,95}$")
PRIVATE_FIELD_KEYS = {
    "applicant_name",
    "application_text",
    "candidate_name",
    "cv_text",
    "date_of_birth",
    "dob",
    "document_text",
    "email",
    "full_name",
    "home_address",
    "person_name",
    "phone",
    "private_application",
    "raw_application",
    "resume_text",
    "social_security_number",
    "ssn",
}
PROXY_TERMS = (
    "journal impact factor",
    "impact factor",
    "h-index",
    "h index",
    "citation count",
    "altmetric",
    "conference ranking",
    "journal ranking",
    "institution prestige",
    "journal prestige",
    "venue prestige",
    "university ranking",
)


class ValidationError(ValueError):
    """A deterministic input failure that never includes a supplied value."""

    def __init__(self, code: str, path: str = "$") -> None:
        """Initialise the instance."""
        super().__init__(code)
        self.code = code
        self.path = path


@dataclass(frozen=True)
class Issue:
    """A minimized validation issue."""

    code: str
    path: str
    level: str = "error"

    def as_dict(self) -> dict[str, str]:
        """Handle as dict."""
        return {"code": self.code, "path": self.path, "level": self.level}


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Handle pairs no duplicates."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("JSON_DUPLICATE_KEY")
        result[key] = value
    return result


def _check_local_file(path: Path, suffix: str) -> None:
    """Check local file."""
    if path.suffix.lower() != suffix:
        raise ValidationError("INPUT_SUFFIX_NOT_ALLOWED")
    if not path.exists():
        raise ValidationError("INPUT_NOT_FOUND")
    if path.is_symlink():
        raise ValidationError("INPUT_SYMLINK_NOT_ALLOWED")
    if not path.is_file():
        raise ValidationError("INPUT_NOT_REGULAR_FILE")
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ValidationError("INPUT_TOO_LARGE")


def _scan_structure(value: Any, path: str = "$") -> None:
    """Handle scan structure."""
    nodes = 0
    stack: list[tuple[Any, str, int]] = [(value, path, 0)]
    while stack:
        current, current_path, depth = stack.pop()
        nodes += 1
        if nodes > MAX_TOTAL_NODES:
            raise ValidationError("STRUCTURE_TOO_LARGE", current_path)
        if depth > MAX_DEPTH:
            raise ValidationError("STRUCTURE_TOO_DEEP", current_path)
        if isinstance(current, dict):
            if len(current) > MAX_OBJECT_FIELDS:
                raise ValidationError("OBJECT_TOO_LARGE", current_path)
            for key, child in current.items():
                if not isinstance(key, str):
                    raise ValidationError("OBJECT_KEY_NOT_TEXT", current_path)
                normalized = key.strip().lower()
                if normalized in PRIVATE_FIELD_KEYS:
                    raise ValidationError("PRIVATE_FIELD_NOT_ALLOWED", f"{current_path}.{key}")
                stack.append((child, f"{current_path}.{key}", depth + 1))
        elif isinstance(current, list):
            if len(current) > MAX_LIST_ITEMS:
                raise ValidationError("LIST_TOO_LARGE", current_path)
            for index, child in enumerate(current):
                stack.append((child, f"{current_path}[{index}]", depth + 1))
        elif isinstance(current, str) and len(current) > MAX_TEXT_CHARS:
            raise ValidationError("TEXT_TOO_LONG", current_path)
        elif current is not None and not isinstance(
            current, (str, int, float, bool)
        ):
            raise ValidationError("VALUE_TYPE_NOT_ALLOWED", current_path)
        if isinstance(current, float) and not math.isfinite(current):
            raise ValidationError("NUMBER_NOT_FINITE", current_path)


def read_json(path: Path | str) -> Any:
    """Read bounded JSON with duplicate-key and private-field rejection."""

    local_path = Path(path)
    _check_local_file(local_path, ".json")
    try:
        data = json.loads(
            local_path.read_text(encoding="utf-8"),
            object_pairs_hook=_pairs_no_duplicates,
        )
    except UnicodeDecodeError as error:
        raise ValidationError("INPUT_NOT_UTF8") from error
    except json.JSONDecodeError as error:
        raise ValidationError("JSON_INVALID") from error
    _scan_structure(data)
    return data


def read_csv_text(path: Path | str) -> str:
    """Read a bounded UTF-8 CSV file after local-path checks."""

    local_path = Path(path)
    _check_local_file(local_path, ".csv")
    try:
        return local_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValidationError("INPUT_NOT_UTF8") from error


def write_json(
    value: dict[str, Any], output: Path | None, *, force: bool = False
) -> None:
    """Write deterministic JSON locally or print it to standard output."""

    rendered = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if len(rendered.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise ValidationError("OUTPUT_TOO_LARGE")
    if output is None:
        print(rendered, end="")
        return
    if output.suffix.lower() != ".json":
        raise ValidationError("OUTPUT_SUFFIX_NOT_ALLOWED")
    if output.is_symlink():
        raise ValidationError("OUTPUT_SYMLINK_NOT_ALLOWED")
    if output.exists() and not force:
        raise ValidationError("OUTPUT_EXISTS")
    if not output.parent.exists() or not output.parent.is_dir():
        raise ValidationError("OUTPUT_PARENT_NOT_FOUND")
    output.write_text(rendered, encoding="utf-8")


def failure_report(error: ValidationError) -> dict[str, Any]:
    """Handle failure report."""
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "error",
        "issues": [Issue(error.code, error.path).as_dict()],
    }


def is_number(value: Any) -> bool:
    """Return whether number."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_identifier(value: Any) -> bool:
    """Return whether identifier."""
    return isinstance(value, str) and bool(IDENTIFIER_RE.fullmatch(value))


def is_nonempty_text(value: Any, maximum: int = MAX_TEXT_CHARS) -> bool:
    """Return whether nonempty text."""
    return isinstance(value, str) and bool(value.strip()) and len(value) <= maximum


def is_reference(value: Any) -> bool:
    """Return whether reference."""
    if not is_nonempty_text(value, 500):
        return False
    lowered = value.strip().lower()
    return not (
        lowered.startswith(("http://", "https://", "file://"))
        or "\n" in value
        or "\r" in value
    )


def is_date(value: Any) -> bool:
    """Return whether date."""
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return len(value) == 10


def exact_keys(
    value: Any,
    expected: Iterable[str],
    path: str,
    issues: list[Issue],
) -> bool:
    """Handle exact keys."""
    if not isinstance(value, dict):
        issues.append(Issue("SCHEMA_OBJECT_REQUIRED", path))
        return False
    expected_set = set(expected)
    actual_set = set(value)
    for missing in sorted(expected_set - actual_set):
        issues.append(Issue("SCHEMA_REQUIRED_FIELD", f"{path}.{missing}"))
    for unknown in sorted(actual_set - expected_set):
        issues.append(Issue("SCHEMA_UNKNOWN_FIELD", f"{path}.{unknown}"))
    return not (expected_set - actual_set)


def validate_identifier(
    value: Any, path: str, issues: list[Issue], code: str = "IDENTIFIER_INVALID"
) -> None:
    """Validate identifier."""
    if not is_identifier(value):
        issues.append(Issue(code, path))


def validate_reference(
    value: Any, path: str, issues: list[Issue], *, allow_empty: bool = False
) -> None:
    """Validate reference."""
    if allow_empty and value == "":
        return
    if not is_reference(value):
        issues.append(Issue("LOCAL_REFERENCE_INVALID", path))


def validate_text(
    value: Any, path: str, issues: list[Issue], *, allow_empty: bool = False
) -> None:
    """Validate text."""
    if allow_empty and value == "":
        return
    if not is_nonempty_text(value):
        issues.append(Issue("TEXT_INVALID", path))


def validate_bool(value: Any, path: str, issues: list[Issue]) -> None:
    """Validate bool."""
    if not isinstance(value, bool):
        issues.append(Issue("BOOLEAN_REQUIRED", path))


def validate_text_list(
    value: Any,
    path: str,
    issues: list[Issue],
    *,
    minimum: int = 0,
    maximum: int = 100,
    references: bool = False,
) -> None:
    """Validate text list."""
    if not isinstance(value, list):
        issues.append(Issue("LIST_REQUIRED", path))
        return
    if not minimum <= len(value) <= maximum:
        issues.append(Issue("LIST_LENGTH_INVALID", path))
    for index, item in enumerate(value):
        if references:
            validate_reference(item, f"{path}[{index}]", issues)
        else:
            validate_text(item, f"{path}[{index}]", issues)


def _validate_scale(scale: Any, issues: list[Issue]) -> tuple[float, float, float]:
    """Validate scale."""
    path = "$.scale"
    expected = {"minimum", "maximum", "step", "anchors"}
    if not exact_keys(scale, expected, path, issues):
        return 0.0, 0.0, 1.0
    minimum = scale.get("minimum")
    maximum = scale.get("maximum")
    step = scale.get("step")
    if not is_number(minimum) or not is_number(maximum) or not is_number(step):
        issues.append(Issue("SCALE_NUMBER_REQUIRED", path))
        return 0.0, 0.0, 1.0
    minimum_f = float(minimum)
    maximum_f = float(maximum)
    step_f = float(step)
    if minimum_f < 0 or maximum_f <= minimum_f or maximum_f - minimum_f > 10:
        issues.append(Issue("SCALE_BOUNDS_INVALID", path))
    if step_f <= 0 or step_f > maximum_f - minimum_f:
        issues.append(Issue("SCALE_STEP_INVALID", f"{path}.step"))
    anchors = scale.get("anchors")
    if not isinstance(anchors, list) or not 2 <= len(anchors) <= 21:
        issues.append(Issue("SCALE_ANCHORS_INVALID", f"{path}.anchors"))
        return minimum_f, maximum_f, step_f
    anchor_scores: list[float] = []
    for index, anchor in enumerate(anchors):
        anchor_path = f"{path}.anchors[{index}]"
        if not exact_keys(anchor, {"score", "label", "description"}, anchor_path, issues):
            continue
        score = anchor.get("score")
        if not is_number(score):
            issues.append(Issue("ANCHOR_SCORE_INVALID", f"{anchor_path}.score"))
        else:
            anchor_scores.append(float(score))
        validate_text(anchor.get("label"), f"{anchor_path}.label", issues)
        validate_text(anchor.get("description"), f"{anchor_path}.description", issues)
    if anchor_scores:
        if len(anchor_scores) != len(set(anchor_scores)):
            issues.append(Issue("ANCHOR_SCORE_DUPLICATE", f"{path}.anchors"))
        if min(anchor_scores) != minimum_f or max(anchor_scores) != maximum_f:
            issues.append(Issue("ANCHOR_BOUNDS_MISSING", f"{path}.anchors"))
    return minimum_f, maximum_f, step_f


def _validate_proxy_absence(value: Any, path: str, issues: list[Issue]) -> None:
    """Validate proxy absence."""
    strings: list[str] = []
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, str):
            strings.append(current.lower())
        elif isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, dict):
            stack.extend(current.values())
    combined = "\n".join(strings)
    if any(term in combined for term in PROXY_TERMS):
        issues.append(Issue("PROXY_METRIC_CRITERION_PROHIBITED", path))


_RUBRIC_ID_PATH = "$.rubric_id"
_VALIDITY_STATUSES = {"not_established", "pilot_evidence", "documented"}
_RUBRIC_TOP_KEYS = {
    "schema_version",
    "rubric_id",
    "title",
    "intended_use",
    "construct",
    "provenance",
    "scale",
    "criteria",
    "rater_protocol",
    "governance",
}
_CRITERION_KEYS = {
    "criterion_id",
    "label",
    "construct_component",
    "weight",
    "required",
    "anchors",
    "evidence_requirements",
    "limitations",
}
_RATER_PROTOCOL_KEYS = {
    "minimum_raters",
    "training_required",
    "training_ref",
    "calibration_required",
    "calibration_ref",
    "agreement_method",
    "inter_rater_reliability_status",
    "inter_rater_reliability_ref",
    "drift_monitoring_required",
    "drift_review_ref",
}
_GOVERNANCE_BOOL_FIELDS = (
    "accountable_committee_required",
    "conflict_disclosure_required",
    "recusal_required",
    "appeal_process_required",
    "accessibility_accommodations_required",
    "data_protection_review_required",
    "subgroup_bias_review_required",
)
_GOVERNANCE_REF_FIELDS = (
    "committee_owner_role",
    "appeal_process_ref",
    "accessibility_process_ref",
    "data_protection_process_ref",
    "subgroup_review_ref",
    "review_cycle_ref",
)


def _validate_intended_use(rubric: dict[str, Any], issues: list[Issue]) -> None:
    """Validate the intended_use section and that every prohibited use is listed."""
    intended = rubric.get("intended_use")
    if not exact_keys(
        intended,
        {"purpose", "unit_of_assessment", "allowed_contexts", "prohibited_uses"},
        "$.intended_use",
        issues,
    ):
        return
    if intended.get("purpose") != ALLOWED_PURPOSE:
        issues.append(Issue("PURPOSE_NOT_ALLOWED", "$.intended_use.purpose"))
    if intended.get("unit_of_assessment") != ALLOWED_UNIT:
        issues.append(
            Issue("UNIT_OF_ASSESSMENT_NOT_ALLOWED", "$.intended_use.unit_of_assessment")
        )
    validate_text_list(
        intended.get("allowed_contexts"),
        "$.intended_use.allowed_contexts",
        issues,
        minimum=1,
        maximum=20,
    )
    prohibited = intended.get("prohibited_uses")
    validate_text_list(
        prohibited,
        "$.intended_use.prohibited_uses",
        issues,
        minimum=len(PROHIBITED_USES),
        maximum=30,
    )
    prohibited_set = (
        set(prohibited)
        if isinstance(prohibited, list)
        and all(isinstance(item, str) for item in prohibited)
        else set()
    )
    if isinstance(prohibited, list) and not PROHIBITED_USES.issubset(prohibited_set):
        issues.append(
            Issue("PROHIBITED_USES_INCOMPLETE", "$.intended_use.prohibited_uses")
        )


def _validate_construct(rubric: dict[str, Any], issues: list[Issue]) -> None:
    """Validate the construct section (label, definition, boundaries, limitations)."""
    construct = rubric.get("construct")
    if not exact_keys(
        construct,
        {"label", "definition", "boundaries", "limitations"},
        "$.construct",
        issues,
    ):
        return
    validate_text(construct.get("label"), "$.construct.label", issues)
    validate_text(construct.get("definition"), "$.construct.definition", issues)
    validate_text_list(
        construct.get("boundaries"),
        "$.construct.boundaries",
        issues,
        minimum=1,
        maximum=20,
    )
    validate_text_list(
        construct.get("limitations"),
        "$.construct.limitations",
        issues,
        minimum=1,
        maximum=20,
    )


def _validate_provenance(rubric: dict[str, Any], issues: list[Issue]) -> None:
    """Validate the provenance section, warning when content validity is not documented."""
    provenance = rubric.get("provenance")
    if not exact_keys(
        provenance,
        {
            "rubric_version",
            "owner_role",
            "source_ids",
            "content_validity_status",
            "content_validity_evidence_ref",
            "last_reviewed_date",
        },
        "$.provenance",
        issues,
    ):
        return
    validate_text(provenance.get("rubric_version"), "$.provenance.rubric_version", issues)
    validate_text(provenance.get("owner_role"), "$.provenance.owner_role", issues)
    validate_text_list(
        provenance.get("source_ids"),
        "$.provenance.source_ids",
        issues,
        minimum=1,
        maximum=50,
        references=True,
    )
    validity_status = provenance.get("content_validity_status")
    if validity_status not in _VALIDITY_STATUSES:
        issues.append(
            Issue(
                "CONTENT_VALIDITY_STATUS_INVALID",
                "$.provenance.content_validity_status",
            )
        )
    validate_reference(
        provenance.get("content_validity_evidence_ref"),
        "$.provenance.content_validity_evidence_ref",
        issues,
        allow_empty=validity_status == "not_established",
    )
    if validity_status != "documented":
        issues.append(
            Issue(
                "CONTENT_VALIDITY_NOT_DOCUMENTED",
                "$.provenance.content_validity_status",
                "warning",
            )
        )
    if not is_date(provenance.get("last_reviewed_date")):
        issues.append(Issue("DATE_INVALID", "$.provenance.last_reviewed_date"))


def _scale_anchor_score_set(scale_object: Any) -> set[float]:
    """Collect the numeric anchor scores declared on the rubric scale."""
    raw_scale_anchors = (
        scale_object.get("anchors") if isinstance(scale_object, dict) else []
    )
    if not isinstance(raw_scale_anchors, list):
        raw_scale_anchors = []
    return {
        float(anchor["score"])
        for anchor in raw_scale_anchors
        if isinstance(anchor, dict) and is_number(anchor.get("score"))
    }


def _validate_criterion_anchors(
    criterion: dict[str, Any], path: str, issues: list[Issue]
) -> set[float]:
    """Validate a criterion's anchors and return the numeric scores they declare."""
    anchors = criterion.get("anchors")
    scores: set[float] = set()
    if not isinstance(anchors, list) or not 2 <= len(anchors) <= 21:
        issues.append(Issue("CRITERION_ANCHORS_INVALID", f"{path}.anchors"))
        return scores
    for anchor_index, anchor in enumerate(anchors):
        anchor_path = f"{path}.anchors[{anchor_index}]"
        if not exact_keys(anchor, {"score", "description"}, anchor_path, issues):
            continue
        if not is_number(anchor.get("score")):
            issues.append(Issue("ANCHOR_SCORE_INVALID", f"{anchor_path}.score"))
        else:
            scores.add(float(anchor["score"]))
        validate_text(
            anchor.get("description"),
            f"{anchor_path}.description",
            issues,
        )
    return scores


def _validate_criterion(
    criterion: Any,
    path: str,
    issues: list[Issue],
    criterion_ids: set[str],
    scale_anchor_scores: set[float],
) -> float:
    """Validate one criterion and return the weight it contributes to the total."""
    if not exact_keys(criterion, _CRITERION_KEYS, path, issues):
        return 0.0
    criterion_id = criterion.get("criterion_id")
    validate_identifier(criterion_id, f"{path}.criterion_id", issues)
    if isinstance(criterion_id, str):
        if criterion_id in criterion_ids:
            issues.append(Issue("CRITERION_ID_DUPLICATE", f"{path}.criterion_id"))
        criterion_ids.add(criterion_id)
    validate_text(criterion.get("label"), f"{path}.label", issues)
    validate_text(
        criterion.get("construct_component"),
        f"{path}.construct_component",
        issues,
    )
    validate_bool(criterion.get("required"), f"{path}.required", issues)
    weight = criterion.get("weight")
    contributed = 0.0
    if not is_number(weight) or not 0 < float(weight) <= 1:
        issues.append(Issue("CRITERION_WEIGHT_INVALID", f"{path}.weight"))
    else:
        contributed = float(weight)
    validate_text_list(
        criterion.get("evidence_requirements"),
        f"{path}.evidence_requirements",
        issues,
        minimum=1,
        maximum=20,
    )
    validate_text_list(
        criterion.get("limitations"),
        f"{path}.limitations",
        issues,
        minimum=1,
        maximum=20,
    )
    if _validate_criterion_anchors(criterion, path, issues) != scale_anchor_scores:
        issues.append(Issue("CRITERION_ANCHORS_INCOMPLETE", f"{path}.anchors"))
    _validate_proxy_absence(criterion, path, issues)
    return contributed


def _validate_criteria(
    rubric: dict[str, Any], issues: list[Issue], scale_anchor_scores: set[float]
) -> None:
    """Validate every criterion and that the criterion weights sum to one."""
    criteria = rubric.get("criteria")
    criterion_ids: set[str] = set()
    total_weight = 0.0
    if not isinstance(criteria, list) or not 1 <= len(criteria) <= MAX_CRITERIA:
        issues.append(Issue("CRITERIA_INVALID", "$.criteria"))
    else:
        for index, criterion in enumerate(criteria):
            total_weight += _validate_criterion(
                criterion,
                f"$.criteria[{index}]",
                issues,
                criterion_ids,
                scale_anchor_scores,
            )
    if criteria and not math.isclose(total_weight, 1.0, abs_tol=1e-9):
        issues.append(Issue("CRITERION_WEIGHTS_MUST_SUM_TO_ONE", "$.criteria"))


def _validate_required_true_fields(
    section: dict[str, Any],
    fields: Iterable[str],
    base_path: str,
    code: str,
    issues: list[Issue],
) -> None:
    """Require each named field to be a boolean that is exactly True."""
    for field in fields:
        validate_bool(section.get(field), f"{base_path}.{field}", issues)
        if section.get(field) is not True:
            issues.append(Issue(code, f"{base_path}.{field}"))


def _validate_rater_protocol(rubric: dict[str, Any], issues: list[Issue]) -> None:
    """Validate the rater protocol, requiring training, calibration and drift monitoring."""
    protocol = rubric.get("rater_protocol")
    if not exact_keys(protocol, _RATER_PROTOCOL_KEYS, "$.rater_protocol", issues):
        return
    minimum_raters = protocol.get("minimum_raters")
    if (
        not isinstance(minimum_raters, int)
        or isinstance(minimum_raters, bool)
        or not 2 <= minimum_raters <= 50
    ):
        issues.append(
            Issue("MINIMUM_RATERS_INVALID", "$.rater_protocol.minimum_raters")
        )
    _validate_required_true_fields(
        protocol,
        ("training_required", "calibration_required", "drift_monitoring_required"),
        "$.rater_protocol",
        "RATER_CONTROL_MUST_BE_REQUIRED",
        issues,
    )
    for field in ("training_ref", "calibration_ref", "drift_review_ref"):
        validate_reference(protocol.get(field), f"$.rater_protocol.{field}", issues)
    if protocol.get("agreement_method") != (
        "exact_within_step_and_mean_absolute_difference"
    ):
        issues.append(
            Issue("AGREEMENT_METHOD_INVALID", "$.rater_protocol.agreement_method")
        )
    reliability_status = protocol.get("inter_rater_reliability_status")
    if reliability_status not in _VALIDITY_STATUSES:
        issues.append(
            Issue(
                "INTER_RATER_RELIABILITY_STATUS_INVALID",
                "$.rater_protocol.inter_rater_reliability_status",
            )
        )
    validate_reference(
        protocol.get("inter_rater_reliability_ref"),
        "$.rater_protocol.inter_rater_reliability_ref",
        issues,
        allow_empty=reliability_status == "not_established",
    )
    if reliability_status != "documented":
        issues.append(
            Issue(
                "INTER_RATER_RELIABILITY_NOT_DOCUMENTED",
                "$.rater_protocol.inter_rater_reliability_status",
                "warning",
            )
        )


def _validate_governance(rubric: dict[str, Any], issues: list[Issue]) -> None:
    """Validate the governance section, requiring every control flag to be true."""
    governance = rubric.get("governance")
    if not exact_keys(
        governance,
        set(_GOVERNANCE_BOOL_FIELDS) | set(_GOVERNANCE_REF_FIELDS),
        "$.governance",
        issues,
    ):
        return
    _validate_required_true_fields(
        governance,
        _GOVERNANCE_BOOL_FIELDS,
        "$.governance",
        "GOVERNANCE_CONTROL_MUST_BE_REQUIRED",
        issues,
    )
    for field in _GOVERNANCE_REF_FIELDS:
        validate_reference(governance.get(field), f"$.governance.{field}", issues)


def validate_rubric(rubric: Any) -> list[Issue]:
    """Validate the strict local rubric schema."""

    issues: list[Issue] = []
    if not exact_keys(rubric, _RUBRIC_TOP_KEYS, "$", issues):
        return issues
    if rubric.get("schema_version") != SCHEMA_VERSION:
        issues.append(Issue("SCHEMA_VERSION_UNSUPPORTED", "$.schema_version"))
    validate_identifier(rubric.get("rubric_id"), _RUBRIC_ID_PATH, issues)
    validate_text(rubric.get("title"), "$.title", issues)

    _validate_intended_use(rubric, issues)
    _validate_construct(rubric, issues)
    _validate_provenance(rubric, issues)

    scale_object = rubric.get("scale")
    minimum, maximum, step = _validate_scale(scale_object, issues)
    _validate_criteria(rubric, issues, _scale_anchor_score_set(scale_object))
    _validate_rater_protocol(rubric, issues)
    _validate_governance(rubric, issues)

    if maximum <= minimum or step <= 0:
        issues.append(Issue("SCALE_UNUSABLE", "$.scale"))
    return issues


def scale_values(rubric: dict[str, Any]) -> set[float]:
    """Handle scale values."""
    return {
        float(anchor["score"])
        for anchor in rubric["scale"]["anchors"]
        if is_number(anchor["score"])
    }


_EVALUATION_KEYS = {
    "schema_version",
    "evaluation_id",
    "rubric_id",
    "work_id",
    "data_classification",
    "purpose",
    "ratings",
}
_RATING_KEYS = {
    "criterion_id",
    "status",
    "score",
    "uncertainty",
    "evidence_ids",
    "rationale_ref",
}


def _validate_evaluation_header(
    evaluation: dict[str, Any], rubric: dict[str, Any], issues: list[Issue]
) -> None:
    """Validate the evaluation's schema version, identifiers, classification and purpose."""
    if evaluation.get("schema_version") != SCHEMA_VERSION:
        issues.append(Issue("SCHEMA_VERSION_UNSUPPORTED", "$.schema_version"))
    validate_identifier(evaluation.get("evaluation_id"), "$.evaluation_id", issues)
    validate_identifier(evaluation.get("rubric_id"), _RUBRIC_ID_PATH, issues)
    validate_identifier(evaluation.get("work_id"), "$.work_id", issues)
    if evaluation.get("rubric_id") != rubric.get("rubric_id"):
        issues.append(Issue("RUBRIC_ID_MISMATCH", _RUBRIC_ID_PATH))
    if evaluation.get("data_classification") not in ALLOWED_CLASSIFICATIONS:
        issues.append(Issue("DATA_CLASSIFICATION_NOT_ALLOWED", "$.data_classification"))
    if evaluation.get("purpose") != ALLOWED_PURPOSE:
        issues.append(Issue("PURPOSE_NOT_ALLOWED", "$.purpose"))


def _validate_rating_criterion(
    rating: dict[str, Any],
    path: str,
    criteria: dict[str, Any],
    seen: set[str],
    issues: list[Issue],
) -> None:
    """Validate a rating's criterion id: well-formed, not repeated, and defined by the rubric."""
    criterion_id = rating.get("criterion_id")
    validate_identifier(criterion_id, f"{path}.criterion_id", issues)
    if not isinstance(criterion_id, str):
        return
    if criterion_id in seen:
        issues.append(Issue("RATING_DUPLICATE", f"{path}.criterion_id"))
    seen.add(criterion_id)
    if criterion_id not in criteria:
        issues.append(Issue("CRITERION_UNKNOWN", f"{path}.criterion_id"))


def _validate_evidence_ids(
    rating: dict[str, Any], path: str, issues: list[Issue]
) -> list[Any]:
    """Validate a rating's evidence id list and return it (empty when invalid)."""
    evidence_ids = rating.get("evidence_ids")
    if not isinstance(evidence_ids, list) or len(evidence_ids) > 100:
        issues.append(Issue("EVIDENCE_IDS_INVALID", f"{path}.evidence_ids"))
        return []
    hashable_evidence_ids = [
        evidence_id for evidence_id in evidence_ids if isinstance(evidence_id, str)
    ]
    if len(hashable_evidence_ids) != len(set(hashable_evidence_ids)):
        issues.append(Issue("EVIDENCE_ID_DUPLICATE", f"{path}.evidence_ids"))
    for evidence_index, evidence_id in enumerate(evidence_ids):
        validate_identifier(
            evidence_id,
            f"{path}.evidence_ids[{evidence_index}]",
            issues,
            "EVIDENCE_ID_INVALID",
        )
    return evidence_ids


def _validate_rated_values(
    rating: dict[str, Any],
    path: str,
    evidence_ids: list[Any],
    accepted_scores: set[float],
    maximum_uncertainty: float,
    issues: list[Issue],
) -> None:
    """Validate the score, uncertainty and evidence of a rating whose status is 'rated'."""
    score = rating.get("score")
    uncertainty = rating.get("uncertainty")
    if not is_number(score) or float(score) not in accepted_scores:
        issues.append(Issue("SCORE_NOT_ON_SCALE", f"{path}.score"))
    if not is_number(uncertainty) or not 0 <= float(uncertainty) <= maximum_uncertainty:
        issues.append(Issue("UNCERTAINTY_INVALID", f"{path}.uncertainty"))
    if not evidence_ids:
        issues.append(Issue("RATED_EVIDENCE_REQUIRED", f"{path}.evidence_ids"))


def _validate_unrated_values(
    rating: dict[str, Any], path: str, evidence_ids: list[Any], issues: list[Issue]
) -> None:
    """Require a missing or not-applicable rating to carry no score, uncertainty or evidence."""
    if rating.get("score") is not None:
        issues.append(Issue("UNRATED_SCORE_MUST_BE_NULL", f"{path}.score"))
    if rating.get("uncertainty") is not None:
        issues.append(Issue("UNRATED_UNCERTAINTY_MUST_BE_NULL", f"{path}.uncertainty"))
    if evidence_ids:
        issues.append(Issue("UNRATED_EVIDENCE_MUST_BE_EMPTY", f"{path}.evidence_ids"))


def _validate_rating(
    rating: Any,
    path: str,
    criteria: dict[str, Any],
    seen: set[str],
    accepted_scores: set[float],
    maximum_uncertainty: float,
    issues: list[Issue],
) -> None:
    """Validate one rating entry against the rubric."""
    if not exact_keys(rating, _RATING_KEYS, path, issues):
        return
    _validate_rating_criterion(rating, path, criteria, seen, issues)
    status = rating.get("status")
    if status not in RATING_STATUSES:
        issues.append(Issue("RATING_STATUS_INVALID", f"{path}.status"))
    evidence_ids = _validate_evidence_ids(rating, path, issues)
    validate_reference(rating.get("rationale_ref"), f"{path}.rationale_ref", issues)
    if status == "rated":
        _validate_rated_values(
            rating, path, evidence_ids, accepted_scores, maximum_uncertainty, issues
        )
    elif status in {"missing", "not_applicable"}:
        _validate_unrated_values(rating, path, evidence_ids, issues)


def validate_evaluation(
    evaluation: Any, rubric: dict[str, Any]
) -> list[Issue]:
    """Validate one strict scholarly-work evaluation record."""

    issues: list[Issue] = []
    if not exact_keys(evaluation, _EVALUATION_KEYS, "$", issues):
        return issues
    _validate_evaluation_header(evaluation, rubric, issues)

    criteria = {criterion["criterion_id"]: criterion for criterion in rubric["criteria"]}
    accepted_scores = scale_values(rubric)
    maximum_uncertainty = float(rubric["scale"]["maximum"]) - float(
        rubric["scale"]["minimum"]
    )
    ratings = evaluation.get("ratings")
    seen: set[str] = set()
    if not isinstance(ratings, list) or not 1 <= len(ratings) <= MAX_CRITERIA:
        issues.append(Issue("RATINGS_INVALID", "$.ratings"))
        return issues
    for index, rating in enumerate(ratings):
        _validate_rating(
            rating,
            f"$.ratings[{index}]",
            criteria,
            seen,
            accepted_scores,
            maximum_uncertainty,
            issues,
        )
    for criterion_id in sorted(set(criteria) - seen):
        issues.append(Issue("CRITERION_RATING_REQUIRED", f"$.ratings.{criterion_id}"))
    return issues


def error_issues(issues: Iterable[Issue]) -> list[Issue]:
    """Handle error issues."""
    return [issue for issue in issues if issue.level == "error"]


def require_valid(issues: Iterable[Issue]) -> None:
    """Handle require valid."""
    errors = error_issues(issues)
    if errors:
        raise ValidationError(errors[0].code, errors[0].path)


def rounded(value: float | None) -> float | None:
    """Handle rounded."""
    if value is None:
        return None
    return round(value, 6)


def weights_by_criterion(rubric: dict[str, Any]) -> dict[str, float]:
    """Handle weights by criterion."""
    return {
        criterion["criterion_id"]: float(criterion["weight"])
        for criterion in rubric["criteria"]
    }


def score_evaluation(
    rubric: dict[str, Any],
    evaluation: dict[str, Any],
    *,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Calculate bounded descriptive rubric math without a recommendation."""

    selected_weights = weights or weights_by_criterion(rubric)
    scale_minimum = float(rubric["scale"]["minimum"])
    scale_maximum = float(rubric["scale"]["maximum"])
    rating_by_id = {
        rating["criterion_id"]: rating for rating in evaluation["ratings"]
    }
    criteria_output: list[dict[str, Any]] = []
    weighted_sum = 0.0
    lower_sum = 0.0
    upper_sum = 0.0
    rated_weight = 0.0
    missing_weight = 0.0
    not_applicable_weight = 0.0
    for criterion in rubric["criteria"]:
        criterion_id = criterion["criterion_id"]
        rating = rating_by_id[criterion_id]
        weight = float(selected_weights[criterion_id])
        status = rating["status"]
        item: dict[str, Any] = {
            "criterion_id": criterion_id,
            "status": status,
            "weight": rounded(weight),
            "score": None,
            "uncertainty": None,
            "weighted_contribution": None,
            "lower_contribution": None,
            "upper_contribution": None,
        }
        if status == "rated":
            score = float(rating["score"])
            uncertainty = float(rating["uncertainty"])
            lower = max(scale_minimum, score - uncertainty)
            upper = min(scale_maximum, score + uncertainty)
            contribution = weight * score
            weighted_sum += contribution
            lower_sum += weight * lower
            upper_sum += weight * upper
            rated_weight += weight
            item.update(
                {
                    "score": rounded(score),
                    "uncertainty": rounded(uncertainty),
                    "weighted_contribution": rounded(contribution),
                    "lower_contribution": rounded(weight * lower),
                    "upper_contribution": rounded(weight * upper),
                }
            )
        elif status == "missing":
            missing_weight += weight
        else:
            not_applicable_weight += weight
        criteria_output.append(item)
    applicable_weight = rated_weight + missing_weight
    normalized = weighted_sum / rated_weight if rated_weight else None
    lower_score = lower_sum / rated_weight if rated_weight else None
    upper_score = upper_sum / rated_weight if rated_weight else None
    coverage = rated_weight / applicable_weight if applicable_weight else None
    warnings: list[str] = []
    if missing_weight > 0:
        warnings.append("MISSING_RATINGS_EXCLUDED_FROM_NORMALIZED_SCORE")
    if not_applicable_weight > 0:
        warnings.append("NOT_APPLICABLE_RATINGS_EXCLUDED")
    if coverage is None or coverage < 1.0:
        warnings.append("INCOMPLETE_APPLICABLE_COVERAGE")
    if normalized is None:
        warnings.append("NO_NORMALIZED_SCORE_AVAILABLE")
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": "bounded_descriptive_rubric_score",
        "notice": NOTICE,
        "evaluation_id": evaluation["evaluation_id"],
        "work_id": evaluation["work_id"],
        "rubric_id": rubric["rubric_id"],
        "scale": {"minimum": scale_minimum, "maximum": scale_maximum},
        "formula": (
            "normalized_score = sum(score_i * weight_i for rated criteria) "
            "/ sum(weight_i for rated criteria); missing and not_applicable "
            "criteria are reported and excluded"
        ),
        "criteria": criteria_output,
        "aggregates": {
            "total_weight": rounded(sum(selected_weights.values())),
            "applicable_weight": rounded(applicable_weight),
            "rated_weight": rounded(rated_weight),
            "missing_weight": rounded(missing_weight),
            "not_applicable_weight": rounded(not_applicable_weight),
            "coverage_of_applicable_weight": rounded(coverage),
            "weighted_sum": rounded(weighted_sum),
            "normalized_score": rounded(normalized),
            "uncertainty_interval": {
                "lower": rounded(lower_score),
                "upper": rounded(upper_score),
                "method": (
                    "weighted aggregation of criterion-level bounded uncertainty "
                    "intervals; not a confidence interval"
                ),
            },
        },
        "warnings": warnings,
        "decision_recommendation_provided": False,
    }
