#!/usr/bin/env python3
"""Validate a durable Suede clip-to-guide Markdown package."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_FIELDS = {
    "campaign",
    "platform",
    "identity",
    "rights_status",
    "guide_status",
    "publication_status",
    "execution_mode",
    "certainty_status",
}

ALLOWED_VALUES = {
    "rights_status": {
        "original",
        "licensed",
        "permission-recorded",
        "native-repost-only",
        "fair-use-review",
        "blocked",
    },
    "guide_status": {"existing", "drafted", "needs-long-form", "blocked"},
    "publication_status": {"draft", "approved", "published", "blocked"},
    "execution_mode": {"standard", "max-effort", "worker-fleet"},
    "certainty_status": {
        "not-required",
        "pending",
        "proved",
        "unproved",
        "blocked",
    },
}

REQUIRED_HEADINGS = [
    "# Clip-to-Guide Package",
    "## Decision Snapshot",
    "## Source and Rights",
    "### Fair-use review",
    "## Guide Anchor",
    "## Clip Brief",
    "## Funnel Post",
    "### Exact post text",
    "## Publish Sequence",
    "## Measurement",
    "## Certainty Gate",
    "## Approval Gate",
    "## Verification",
]

UNRESOLVED_VALUES = {
    "",
    "pending",
    "not available",
    "not required",
    "blocked",
    "none",
    "n/a",
}


def parse_frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    if not text.startswith("---\n"):
        return {}, ["missing opening YAML frontmatter delimiter"]

    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, ["missing closing YAML frontmatter delimiter"]

    fields: dict[str, str] = {}
    for line_number, line in enumerate(text[4:end].splitlines(), start=2):
        if not line.strip():
            continue
        match = re.fullmatch(r"([a-z_]+):\s*[\"']?(.+?)[\"']?\s*", line)
        if not match:
            errors.append(f"frontmatter line {line_number} is not key: value")
            continue
        key, value = match.groups()
        fields[key] = value

    return fields, errors


def bullet_value(text: str, label: str) -> str | None:
    match = re.search(rf"(?mi)^-\s*{re.escape(label)}:\s*(.+)$", text)
    return match.group(1).strip() if match else None


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"cannot read {path}: {exc}"]

    fields, frontmatter_errors = parse_frontmatter(text)
    errors.extend(frontmatter_errors)

    missing_fields = sorted(REQUIRED_FIELDS - fields.keys())
    if missing_fields:
        errors.append(f"missing frontmatter fields: {', '.join(missing_fields)}")

    for field, allowed in ALLOWED_VALUES.items():
        value = fields.get(field)
        if value is not None and value not in allowed:
            errors.append(
                f"{field} must be one of {', '.join(sorted(allowed))}; got {value!r}"
            )

    for heading in REQUIRED_HEADINGS:
        if not re.search(rf"(?m)^{re.escape(heading)}\s*$", text):
            errors.append(f"missing heading: {heading}")

    if re.search(r"\b(?:TODO|TBD|PLACEHOLDER)\b", text, flags=re.IGNORECASE):
        errors.append("contains TODO, TBD, or PLACEHOLDER text")

    rights_status = fields.get("rights_status")
    publication_status = fields.get("publication_status")
    guide_status = fields.get("guide_status")
    execution_mode = fields.get("execution_mode")
    certainty_status = fields.get("certainty_status")

    if publication_status in {"approved", "published"}:
        if rights_status == "blocked" or guide_status == "blocked":
            errors.append(
                f"{publication_status} package cannot have blocked rights or guide status"
            )

    if rights_status == "fair-use-review" and publication_status in {
        "approved",
        "published",
    }:
        decision_match = re.search(
            r"(?mi)^-\s*Decision or legal-review state:\s*(.+)$", text
        )
        owner_match = re.search(
            r"(?mi)^-\s*Accountable decision owner:\s*(.+)$", text
        )
        unresolved = {"pending", "not available", "blocked", "not reviewed"}
        if not decision_match or decision_match.group(1).strip().lower() in unresolved:
            errors.append(
                "approved fair-use-review package needs a resolved accountable decision"
            )
        if not owner_match or owner_match.group(1).strip().lower() in unresolved:
            errors.append(
                "approved fair-use-review package needs an accountable decision owner"
            )

    certainty_required = execution_mode in {"max-effort", "worker-fleet"}
    if certainty_required and certainty_status == "not-required":
        errors.append(f"{execution_mode} package requires the dual certainty gate")

    if certainty_required and publication_status in {"approved", "published"}:
        if certainty_status != "proved":
            errors.append(
                f"{publication_status} {execution_mode} package needs "
                "certainty_status: proved"
            )

    if certainty_required and certainty_status == "proved":
        check_labels = [
            "Checked artifact version/hash",
            "Check 1 owner/process",
            "Check 1 evidence",
            "Check 1 verdict",
            "Check 2 owner/process",
            "Check 2 evidence",
            "Check 2 verdict",
            "Contradictions resolved",
            "Final certainty verdict",
        ]
        values = {label: bullet_value(text, label) for label in check_labels}

        for label, value in values.items():
            if value is None or value.rstrip(".").strip().lower() in UNRESOLVED_VALUES:
                errors.append(f"proved certainty gate needs resolved {label}")

        for label in ("Check 1 verdict", "Check 2 verdict", "Final certainty verdict"):
            value = values[label]
            if value is not None and value.rstrip(".").strip().upper() != "PROVED":
                errors.append(f"{label} must be PROVED when certainty_status is proved")

        check_1 = values["Check 1 owner/process"]
        check_2 = values["Check 2 owner/process"]
        if (
            check_1 is not None
            and check_2 is not None
            and check_1.rstrip(".").strip().casefold()
            == check_2.rstrip(".").strip().casefold()
        ):
            errors.append(
                "proved certainty gate needs two distinct check owners or processes"
            )

        evidence_1 = values["Check 1 evidence"]
        evidence_2 = values["Check 2 evidence"]
        if (
            evidence_1 is not None
            and evidence_2 is not None
            and evidence_1.rstrip(".").strip().casefold()
            == evidence_2.rstrip(".").strip().casefold()
        ):
            errors.append(
                "proved certainty gate needs two distinct evidence records"
            )

        if execution_mode == "worker-fleet":
            normalized_check_1 = (check_1 or "").casefold()
            normalized_check_2 = (check_2 or "").casefold()
            if "worker" not in normalized_check_1 or "self-check" not in normalized_check_1:
                errors.append(
                    "proved worker-fleet gate needs a worker self-check as Check 1"
                )
            if "controller" not in normalized_check_2:
                errors.append(
                    "proved worker-fleet gate needs controller review as Check 2"
                )

    if publication_status == "published":
        if not re.search(r"(?mi)^-\s*Live permalink:\s*https?://\S+", text):
            errors.append("published package needs a public Live permalink URL")
        if not re.search(r"(?mi)^-\s*Publication timestamp:\s*\S+", text):
            errors.append("published package needs a publication timestamp")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: validate_package.py path/to/clip-to-guide-package.md", file=sys.stderr)
        return 2

    path = Path(argv[1]).expanduser()
    errors = validate(path)
    if errors:
        print(f"FAIL {path}")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"PASS {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
