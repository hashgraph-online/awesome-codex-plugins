#!/usr/bin/env python3
"""Validate the structure of a Suede rights transfer package.

Checks that a package folder produced by create_transfer_package.py (or
hand-assembled to the same standard) is structurally complete:

- All 7 required report files are present.
- suede-intake.json is valid JSON and matches the documented top-level and
  nested shape from references/intake-schema.md.
- Every asset entry in suede-intake.json carries a sha256 hash.

This is a structural/completeness check only. It does not evaluate rights
facts, ownership claims, split confirmations, or risk-flag severity. A
package can be structurally valid while still carrying open, high-severity
risk flags (unconfirmed ownership, unconfirmed splits, unknown sample
status, etc.) -- that is expected and correct for a package documenting a
project with real open questions. See SKILL.md and
references/package-standard.md for what "valid" does and does not mean
here.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from validate_json_schema import assert_supported_schema, validate_instance


REQUIRED_FILES = [
    "RIGHTS_PASSPORT.md",
    "suede-intake.json",
    "provenance.md",
    "credits-and-splits.md",
    "license-notes.md",
    "optimization-brief.md",
    "missing-info-report.md",
]

# Top-level keys documented in references/intake-schema.md.
REQUIRED_TOP_LEVEL_KEYS = [
    "schema_version",
    "package_type",
    "generated_at",
    "project",
    "creator",
    "assets",
    "rights",
    "provenance",
    "optimization",
    "missing_information",
    "risk_flags",
]

CURRENT_SCHEMA_VERSION = "0.2.0"
LEGACY_SCHEMA_VERSIONS = {"0.1.0"}
V2_REQUIRED_TOP_LEVEL_KEYS = [
    "parties",
    "works",
    "recordings",
    "releases",
    "rights_claims",
    "licenses",
    "third_party_material",
    "consents",
    "privacy",
]
EVIDENCE_STATUSES = {"confirmed", "claimed", "unconfirmed", "disputed", "unknown"}
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "assets" / "suede-intake.schema.json"
V2_REQUIRED_ITEM_KEYS: dict[str, set[str]] = {
    "parties": {
        "id", "name", "roles", "identifiers", "organization", "status", "evidence_refs", "privacy_classification"
    },
    "works": {
        "id", "title", "identifiers", "writer_party_ids", "publisher_party_ids", "status", "evidence_refs"
    },
    "recordings": {
        "id", "title", "asset_ids", "identifiers", "performer_party_ids", "master_owner_party_ids", "status", "evidence_refs"
    },
    "releases": {
        "id", "title", "recording_ids", "identifiers", "label_party_id", "distributor_party_id",
        "release_date", "territories", "status", "evidence_refs"
    },
    "rights_claims": {
        "id", "subject_type", "subject_id", "right_type", "party_id", "share_percent", "territories",
        "start_date", "end_date", "status", "evidence_refs", "conflict_notes"
    },
    "licenses": {
        "id", "subject_ids", "licensor_party_ids", "licensee_party_ids", "use_types", "media", "territories",
        "start_date", "end_date", "exclusive", "sublicensing", "revocable", "status", "restrictions", "evidence_refs"
    },
    "third_party_material": {"id", "type", "source", "subject_ids", "license_id", "status", "evidence_refs"},
    "consents": {"id", "party_id", "scope", "media", "ai_use", "voice_likeness", "status", "evidence_refs"},
}

# Nested object/array keys, keyed by their parent top-level field.
REQUIRED_NESTED_KEYS: dict[str, list[str]] = {
    "project": ["title", "artist_name", "work_type", "description", "release_status", "public_urls"],
    "creator": ["name", "email", "wallet_address", "organization", "confirmation_status"],
    "rights": [
        "owner_claim",
        "ownership_status",
        "contributors_confirmed",
        "splits_confirmed",
        "contains_samples",
        "sample_clearance_status",
        "cover_or_interpolation",
        "license_restrictions",
    ],
    "provenance": ["source_root", "creation_notes", "chain_of_custody", "registry_status"],
    "optimization": ["requested_services", "recommended_services", "priority", "notes"],
}

# Required fields per-item for list-shaped sections.
REQUIRED_ASSET_KEYS = [
    "id",
    "relative_path",
    "category",
    "role",
    "mime_guess",
    "size_bytes",
    "sha256",
]
REQUIRED_MISSING_INFO_KEYS = ["field", "question", "blocks", "severity"]
REQUIRED_RISK_FLAG_KEYS = ["label", "severity", "detail", "recommended_action"]


class ValidationError(Exception):
    """Raised for a structural problem; message is shown to the user."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate that a Suede rights transfer package folder is "
            "structurally complete: all 7 required report files are present, "
            "suede-intake.json is valid JSON matching the documented schema, "
            "and every asset entry has a sha256 hash. This does not evaluate "
            "rights facts or risk-flag severity -- a structurally valid "
            "package can still carry open, high-severity risk flags."
        )
    )
    parser.add_argument(
        "package",
        help="Path to a transfer package folder (e.g. output of create_transfer_package.py).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the pass summary; print nothing on success.",
    )
    parser.add_argument(
        "--strict-current",
        action="store_true",
        help=(
            f"Require schema_version {CURRENT_SCHEMA_VERSION}. Without this flag, "
            "legacy 0.1.0 packages remain structurally inspectable."
        ),
    )
    return parser.parse_args()


def check_required_files(package: Path) -> list[str]:
    missing = [name for name in REQUIRED_FILES if not (package / name).is_file()]
    if missing:
        return [f"Missing required file: {name}" for name in missing]
    return []


def load_intake_json(package: Path) -> tuple[dict[str, Any] | None, list[str]]:
    intake_path = package / "suede-intake.json"
    if not intake_path.is_file():
        # Already reported by check_required_files; do not double-report.
        return None, []
    text = intake_path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, [f"suede-intake.json is not valid JSON: {exc}"]
    if not isinstance(data, dict):
        return None, ["suede-intake.json must contain a JSON object at the top level."]
    return data, []


def check_top_level_shape(data: dict[str, Any], strict_current: bool = False) -> list[str]:
    errors = []
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in data:
            errors.append(f"suede-intake.json missing top-level field: {key}")
    version = data.get("schema_version")
    if version == CURRENT_SCHEMA_VERSION:
        if data.get("package_type") != "suede-transfer-package":
            errors.append("suede-intake.json package_type must be 'suede-transfer-package'.")
        for key in V2_REQUIRED_TOP_LEVEL_KEYS:
            if key not in data:
                errors.append(f"suede-intake.json schema 0.2.0 missing top-level field: {key}")
        allowed = set(REQUIRED_TOP_LEVEL_KEYS) | set(V2_REQUIRED_TOP_LEVEL_KEYS) | {"metadata_source"}
        for key in sorted(set(data) - allowed):
            errors.append(f"suede-intake.json schema 0.2.0 has unsupported top-level field: {key}")
    elif version in LEGACY_SCHEMA_VERSIONS:
        if strict_current:
            errors.append(
                f"suede-intake.json uses legacy schema {version}; --strict-current requires {CURRENT_SCHEMA_VERSION}."
            )
    else:
        errors.append(
            f"suede-intake.json schema_version must be {CURRENT_SCHEMA_VERSION}"
            f" or a supported legacy version ({', '.join(sorted(LEGACY_SCHEMA_VERSIONS))})."
        )
    return errors


def check_nested_shape(data: dict[str, Any]) -> list[str]:
    errors = []
    for parent, keys in REQUIRED_NESTED_KEYS.items():
        section = data.get(parent)
        if not isinstance(section, dict):
            # Missing-top-level-field already reported; skip nested check
            # rather than raising a redundant/confusing error.
            if parent in data:
                errors.append(f"suede-intake.json field '{parent}' must be a JSON object.")
            continue
        for key in keys:
            if key not in section:
                errors.append(f"suede-intake.json '{parent}.{key}' is missing.")
    return errors


def check_list_shaped_sections(data: dict[str, Any]) -> list[str]:
    errors = []
    for field in ("assets", "missing_information", "risk_flags"):
        if field in data and not isinstance(data[field], list):
            errors.append(f"suede-intake.json field '{field}' must be a JSON array.")
    return errors


def check_assets(data: dict[str, Any]) -> list[str]:
    errors = []
    assets = data.get("assets")
    if not isinstance(assets, list):
        return errors  # already reported above
    for index, asset in enumerate(assets):
        label = f"assets[{index}]"
        if not isinstance(asset, dict):
            errors.append(f"suede-intake.json {label} must be a JSON object.")
            continue
        asset_id = asset.get("id")
        if isinstance(asset_id, str) and asset_id:
            label = f"assets[{index}] ({asset_id})"
        for key in REQUIRED_ASSET_KEYS:
            if key not in asset:
                errors.append(f"suede-intake.json {label} missing field: {key}")
        sha = asset.get("sha256")
        if "sha256" in asset:
            if not isinstance(sha, str) or not sha.strip():
                errors.append(f"suede-intake.json {label} has an empty or non-string sha256 field.")
            elif len(sha) != 64 or any(c not in "0123456789abcdefABCDEF" for c in sha):
                errors.append(
                    f"suede-intake.json {label} sha256 field does not look like a 64-char hex digest: {sha!r}"
                )
    return errors


def check_missing_information(data: dict[str, Any]) -> list[str]:
    errors = []
    items = data.get("missing_information")
    if not isinstance(items, list):
        return errors
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"suede-intake.json missing_information[{index}] must be a JSON object.")
            continue
        for key in REQUIRED_MISSING_INFO_KEYS:
            if key not in item:
                errors.append(f"suede-intake.json missing_information[{index}] missing field: {key}")
    return errors


def check_risk_flags(data: dict[str, Any]) -> list[str]:
    errors = []
    items = data.get("risk_flags")
    if not isinstance(items, list):
        return errors
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"suede-intake.json risk_flags[{index}] must be a JSON object.")
            continue
        for key in REQUIRED_RISK_FLAG_KEYS:
            if key not in item:
                errors.append(f"suede-intake.json risk_flags[{index}] missing field: {key}")
    return errors


def _object_list(data: dict[str, Any], field: str, errors: list[str]) -> list[dict[str, Any]]:
    value = data.get(field)
    if not isinstance(value, list):
        errors.append(f"suede-intake.json field '{field}' must be a JSON array.")
        return []
    objects: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"suede-intake.json {field}[{index}] must be a JSON object.")
        else:
            for key in sorted(V2_REQUIRED_ITEM_KEYS.get(field, set())):
                if key not in item:
                    errors.append(f"suede-intake.json {field}[{index}] missing field: {key}")
            objects.append(item)
    return objects


def _ids_for(records: list[dict[str, Any]], field: str, errors: list[str]) -> set[str]:
    ids: set[str] = set()
    for index, record in enumerate(records):
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id:
            errors.append(f"suede-intake.json {field}[{index}] requires a non-empty id.")
            continue
        if record_id in ids:
            errors.append(f"suede-intake.json {field} contains duplicate id: {record_id}")
        ids.add(record_id)
    return ids


def _check_evidence_state(record: dict[str, Any], label: str, errors: list[str]) -> None:
    status = record.get("status")
    evidence = record.get("evidence_refs")
    if status not in EVIDENCE_STATUSES:
        errors.append(
            f"suede-intake.json {label}.status must be one of: {', '.join(sorted(EVIDENCE_STATUSES))}."
        )
    if not isinstance(evidence, list):
        errors.append(f"suede-intake.json {label}.evidence_refs must be a JSON array.")
    elif status == "confirmed" and not any(isinstance(item, str) and item for item in evidence):
        errors.append(
            f"suede-intake.json {label} is confirmed but has no evidence_refs; downgrade the state or add evidence."
        )


def _check_identifiers(record: dict[str, Any], label: str, errors: list[str]) -> None:
    identifiers = record.get("identifiers")
    if not isinstance(identifiers, list):
        errors.append(f"suede-intake.json {label}.identifiers must be a JSON array.")
        return
    allowed = {"ISRC", "ISWC", "IPI_CAE", "ISNI", "UPC_EAN", "CATALOG_NUMBER", "PROPRIETARY"}
    for index, identifier in enumerate(identifiers):
        item_label = f"{label}.identifiers[{index}]"
        if not isinstance(identifier, dict):
            errors.append(f"suede-intake.json {item_label} must be a JSON object.")
            continue
        if identifier.get("scheme") not in allowed:
            errors.append(f"suede-intake.json {item_label}.scheme is unsupported.")
        if not isinstance(identifier.get("value"), str) or not identifier.get("value"):
            errors.append(f"suede-intake.json {item_label}.value must be a non-empty string.")
        _check_evidence_state(identifier, item_label, errors)


def _check_refs(
    record: dict[str, Any], field: str, allowed: set[str], label: str, errors: list[str], nullable: bool = False
) -> None:
    value = record.get(field)
    if nullable and value is None:
        return
    values = value if isinstance(value, list) else [value]
    for item in values:
        if not isinstance(item, str) or item not in allowed:
            errors.append(f"suede-intake.json {label}.{field} references unknown id: {item!r}")


def _check_array_fields(record: dict[str, Any], fields: tuple[str, ...], label: str, errors: list[str]) -> None:
    for field in fields:
        if not isinstance(record.get(field), list):
            errors.append(f"suede-intake.json {label}.{field} must be a JSON array.")


def check_v2_interoperability(data: dict[str, Any]) -> list[str]:
    """Check v0.2 evidence state and cross-object references without legal inference."""
    if data.get("schema_version") != CURRENT_SCHEMA_VERSION:
        return []

    errors: list[str] = []
    parties = _object_list(data, "parties", errors)
    works = _object_list(data, "works", errors)
    recordings = _object_list(data, "recordings", errors)
    releases = _object_list(data, "releases", errors)
    claims = _object_list(data, "rights_claims", errors)
    licenses = _object_list(data, "licenses", errors)
    third_party = _object_list(data, "third_party_material", errors)
    consents = _object_list(data, "consents", errors)

    party_ids = _ids_for(parties, "parties", errors)
    work_ids = _ids_for(works, "works", errors)
    recording_ids = _ids_for(recordings, "recordings", errors)
    release_ids = _ids_for(releases, "releases", errors)
    _ids_for(claims, "rights_claims", errors)
    license_ids = _ids_for(licenses, "licenses", errors)
    _ids_for(third_party, "third_party_material", errors)
    _ids_for(consents, "consents", errors)
    asset_ids = {
        item.get("id") for item in data.get("assets", []) if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    subject_ids = work_ids | recording_ids | release_ids

    for index, party in enumerate(parties):
        label = f"parties[{index}]"
        _check_evidence_state(party, label, errors)
        _check_identifiers(party, label, errors)
        _check_array_fields(party, ("roles",), label, errors)
        if party.get("privacy_classification") not in {
            "public", "shared-with-recipient", "private-draft", "restricted", "do-not-share"
        }:
            errors.append(f"suede-intake.json {label}.privacy_classification is unsupported.")

    for field, records in (("works", works), ("recordings", recordings), ("releases", releases)):
        for index, record in enumerate(records):
            label = f"{field}[{index}]"
            _check_evidence_state(record, label, errors)
            _check_identifiers(record, label, errors)

    for index, work in enumerate(works):
        label = f"works[{index}]"
        _check_array_fields(work, ("writer_party_ids", "publisher_party_ids", "evidence_refs"), label, errors)
        _check_refs(work, "writer_party_ids", party_ids, label, errors)
        _check_refs(work, "publisher_party_ids", party_ids, label, errors)
    for index, recording in enumerate(recordings):
        label = f"recordings[{index}]"
        _check_array_fields(
            recording,
            ("asset_ids", "performer_party_ids", "master_owner_party_ids", "evidence_refs"),
            label,
            errors,
        )
        _check_refs(recording, "asset_ids", asset_ids, label, errors)
        _check_refs(recording, "performer_party_ids", party_ids, label, errors)
        _check_refs(recording, "master_owner_party_ids", party_ids, label, errors)
    for index, release in enumerate(releases):
        label = f"releases[{index}]"
        _check_array_fields(release, ("recording_ids", "territories", "evidence_refs"), label, errors)
        _check_refs(release, "recording_ids", recording_ids, label, errors)
        _check_refs(release, "label_party_id", party_ids, label, errors, nullable=True)
        _check_refs(release, "distributor_party_id", party_ids, label, errors, nullable=True)

    share_totals: dict[tuple[str, str, tuple[str, ...], Any, Any], float] = {}
    allowed_right_types = {
        "composition", "publishing", "mechanical", "performance", "synchronization",
        "master", "neighboring", "distribution", "other"
    }
    for index, claim in enumerate(claims):
        label = f"rights_claims[{index}]"
        _check_evidence_state(claim, label, errors)
        _check_array_fields(claim, ("territories", "evidence_refs"), label, errors)
        if claim.get("subject_type") not in {"work", "recording", "release"}:
            errors.append(f"suede-intake.json {label}.subject_type is unsupported.")
        if claim.get("right_type") not in allowed_right_types:
            errors.append(f"suede-intake.json {label}.right_type is unsupported.")
        _check_refs(claim, "subject_id", subject_ids, label, errors)
        _check_refs(claim, "party_id", party_ids, label, errors)
        share = claim.get("share_percent")
        if share is not None:
            if not isinstance(share, (int, float)) or isinstance(share, bool) or not 0 <= share <= 100:
                errors.append(f"suede-intake.json {label}.share_percent must be null or between 0 and 100.")
            else:
                territories = claim.get("territories")
                territory_scope = tuple(
                    sorted(str(item) for item in territories)
                ) if isinstance(territories, list) else ()
                key = (
                    str(claim.get("subject_id")),
                    str(claim.get("right_type")),
                    territory_scope,
                    claim.get("start_date"),
                    claim.get("end_date"),
                )
                share_totals[key] = share_totals.get(key, 0.0) + float(share)
    for (subject_id, right_type, territories, start_date, end_date), total in share_totals.items():
        if total > 100.000001:
            scope = ",".join(territories) or "unspecified-territory"
            term = f"{start_date or 'open'}..{end_date or 'open'}"
            errors.append(
                f"suede-intake.json rights claims for {subject_id}/{right_type} "
                f"scope {scope} {term} total {total:g}%, above 100%."
            )

    for index, license_record in enumerate(licenses):
        label = f"licenses[{index}]"
        _check_evidence_state(license_record, label, errors)
        _check_array_fields(
            license_record,
            (
                "subject_ids", "licensor_party_ids", "licensee_party_ids", "use_types", "media",
                "territories", "restrictions", "evidence_refs"
            ),
            label,
            errors,
        )
        if license_record.get("sublicensing") not in {"allowed", "prohibited", "unknown"}:
            errors.append(f"suede-intake.json {label}.sublicensing is unsupported.")
        for field in ("exclusive", "revocable"):
            if license_record.get(field) is not None and not isinstance(license_record.get(field), bool):
                errors.append(f"suede-intake.json {label}.{field} must be boolean or null.")
        _check_refs(license_record, "subject_ids", subject_ids, label, errors)
        _check_refs(license_record, "licensor_party_ids", party_ids, label, errors)
        _check_refs(license_record, "licensee_party_ids", party_ids, label, errors)
    for index, item in enumerate(third_party):
        label = f"third_party_material[{index}]"
        _check_evidence_state(item, label, errors)
        _check_array_fields(item, ("subject_ids", "evidence_refs"), label, errors)
        if item.get("type") not in {"sample", "interpolation", "cover", "beat", "loop", "visual", "other"}:
            errors.append(f"suede-intake.json {label}.type is unsupported.")
        _check_refs(item, "subject_ids", subject_ids, label, errors)
        _check_refs(item, "license_id", license_ids, label, errors, nullable=True)
    for index, consent in enumerate(consents):
        label = f"consents[{index}]"
        _check_evidence_state(consent, label, errors)
        _check_array_fields(consent, ("media", "evidence_refs"), label, errors)
        for field in ("ai_use", "voice_likeness"):
            if consent.get(field) not in {"allowed", "prohibited", "limited", "unknown"}:
                errors.append(f"suede-intake.json {label}.{field} is unsupported.")
        _check_refs(consent, "party_id", party_ids, label, errors)

    provenance = data.get("provenance")
    if isinstance(provenance, dict):
        credentials = provenance.get("content_credentials")
        if not isinstance(credentials, list):
            errors.append("suede-intake.json provenance.content_credentials must be a JSON array.")
        else:
            for index, credential in enumerate(credentials):
                label = f"provenance.content_credentials[{index}]"
                if not isinstance(credential, dict):
                    errors.append(f"suede-intake.json {label} must be a JSON object.")
                    continue
                for key in (
                    "asset_id", "kind", "manifest_reference", "verification_status", "verified_at", "evidence_refs"
                ):
                    if key not in credential:
                        errors.append(f"suede-intake.json {label} missing field: {key}")
                if credential.get("kind") not in {"sha256", "c2pa", "other"}:
                    errors.append(f"suede-intake.json {label}.kind is unsupported.")
                if credential.get("verification_status") not in {"verified", "unverified", "failed", "not-checked"}:
                    errors.append(f"suede-intake.json {label}.verification_status is unsupported.")
                if not isinstance(credential.get("evidence_refs"), list):
                    errors.append(f"suede-intake.json {label}.evidence_refs must be a JSON array.")
                _check_refs(credential, "asset_id", asset_ids, label, errors)

    privacy = data.get("privacy")
    if not isinstance(privacy, dict):
        errors.append("suede-intake.json privacy must be a JSON object.")
    else:
        allowed_privacy = {"public", "shared-with-recipient", "private-draft", "restricted", "do-not-share"}
        if privacy.get("default_classification") not in allowed_privacy:
            errors.append("suede-intake.json privacy.default_classification is unsupported.")
        if not isinstance(privacy.get("field_rules"), list):
            errors.append("suede-intake.json privacy.field_rules must be a JSON array.")
        else:
            for index, rule in enumerate(privacy["field_rules"]):
                label = f"privacy.field_rules[{index}]"
                if not isinstance(rule, dict):
                    errors.append(f"suede-intake.json {label} must be a JSON object.")
                    continue
                for key in ("json_pointer", "classification", "redaction_action", "reason"):
                    if key not in rule:
                        errors.append(f"suede-intake.json {label} missing field: {key}")
                if not isinstance(rule.get("json_pointer"), str) or not rule.get("json_pointer", "").startswith("/"):
                    errors.append(f"suede-intake.json {label}.json_pointer must start with '/'.")
                if rule.get("classification") not in allowed_privacy:
                    errors.append(f"suede-intake.json {label}.classification is unsupported.")
                if rule.get("redaction_action") not in {"keep", "mask", "remove", "review"}:
                    errors.append(f"suede-intake.json {label}.redaction_action is unsupported.")
        if not isinstance(privacy.get("redaction_required_before_external_share"), bool):
            errors.append(
                "suede-intake.json privacy.redaction_required_before_external_share must be a boolean."
            )
    return errors


def check_published_json_schema(data: dict[str, Any]) -> list[str]:
    if data.get("schema_version") != CURRENT_SCHEMA_VERSION:
        return []
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Could not load published JSON Schema {SCHEMA_PATH}: {exc}"]
    if not isinstance(schema, dict):
        return [f"Published JSON Schema must be a JSON object: {SCHEMA_PATH}"]
    try:
        assert_supported_schema(schema)
        return [f"JSON Schema {error}" for error in validate_instance(data, schema)]
    except ValueError as exc:
        return [f"Published JSON Schema uses an unsupported or invalid contract: {exc}"]


def summarize_risk_posture(data: dict[str, Any]) -> str:
    """Describe risk-flag posture for the pass summary. Informational only --
    never affects the exit code. Structural validity and business-logic
    confirmation status are independent axes; see module docstring."""
    flags = data.get("risk_flags")
    if not isinstance(flags, list) or not flags:
        return "no risk flags recorded"
    high = sum(1 for f in flags if isinstance(f, dict) and f.get("severity") == "high")
    medium = sum(1 for f in flags if isinstance(f, dict) and f.get("severity") == "medium")
    low = sum(1 for f in flags if isinstance(f, dict) and f.get("severity") == "low")
    parts = []
    if high:
        parts.append(f"{high} high")
    if medium:
        parts.append(f"{medium} medium")
    if low:
        parts.append(f"{low} low")
    other = len(flags) - high - medium - low
    if other:
        parts.append(f"{other} other")
    return f"{len(flags)} risk flag(s) recorded ({', '.join(parts)}) -- structural validity is unaffected"


def main() -> int:
    args = parse_args()
    package = Path(args.package).expanduser().resolve()

    if not package.exists() or not package.is_dir():
        print(f"Package folder not found: {package}", file=sys.stderr)
        return 2

    errors: list[str] = []
    errors += check_required_files(package)

    data, load_errors = load_intake_json(package)
    errors += load_errors

    if data is not None:
        errors += check_top_level_shape(data, strict_current=args.strict_current)
        errors += check_nested_shape(data)
        errors += check_list_shaped_sections(data)
        errors += check_assets(data)
        errors += check_missing_information(data)
        errors += check_risk_flags(data)
        errors += check_published_json_schema(data)
        errors += check_v2_interoperability(data)

    if errors:
        print(f"FAIL: {package} is not a structurally valid transfer package.", file=sys.stderr)
        print("", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        print("", file=sys.stderr)
        print(
            "Structural validity means the required files exist and "
            "suede-intake.json matches the documented schema. It says "
            "nothing about whether rights facts are confirmed.",
            file=sys.stderr,
        )
        return 1

    if not args.quiet:
        asset_count = len(data.get("assets", [])) if data else 0
        missing_count = len(data.get("missing_information", [])) if data else 0
        print(f"PASS: {package}")
        version = data.get("schema_version", "unknown") if data else "unknown"
        posture = "current" if version == CURRENT_SCHEMA_VERSION else "legacy"
        print(f"- Schema {version} ({posture}).")
        print(f"- All {len(REQUIRED_FILES)} required report files present.")
        if version == CURRENT_SCHEMA_VERSION:
            print("- suede-intake.json passes the published Draft 2020-12 JSON Schema contract.")
        else:
            print("- suede-intake.json is valid JSON and matches the supported legacy shape.")
        print(f"- {asset_count} asset(s) inventoried, each with a sha256 hash.")
        print(f"- {missing_count} open missing-information item(s) recorded.")
        if data is not None:
            print(f"- Risk posture: {summarize_risk_posture(data)}.")
        print(
            "\nThis confirms structural completeness only. Confirm rights facts "
            "with the creator before registry, licensing, or royalty routing."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
