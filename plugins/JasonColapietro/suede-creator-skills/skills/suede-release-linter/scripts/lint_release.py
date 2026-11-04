#!/usr/bin/env python3
"""Lint a music/media project folder for release and Suede intake readiness."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUDIO_EXTS = {".wav", ".wave", ".aiff", ".aif", ".flac", ".mp3", ".m4a", ".aac", ".ogg", ".opus"}
LOSSLESS_AUDIO_EXTS = {".wav", ".wave", ".aiff", ".aif", ".flac"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tif", ".tiff"}
LYRIC_EXTS = {".lrc", ".srt", ".vtt"}
TEXT_EXTS = {".txt", ".md"}
DOC_EXTS = {
    ".pdf",
    ".doc",
    ".docx",
    ".rtf",
    ".txt",
    ".md",
    ".csv",
    ".tsv",
    ".json",
    ".xls",
    ".xlsx",
}

SKIP_NAMES = {".ds_store", "thumbs.db"}
DENY_DIR_NAMES = {
    ".aws",
    ".azure",
    ".cache",
    ".config",
    ".docker",
    ".gnupg",
    ".gcloud",
    ".git",
    ".hg",
    ".kube",
    ".mypy_cache",
    ".next",
    ".nuxt",
    ".pytest_cache",
    ".ruff_cache",
    ".ssh",
    ".svn",
    ".turbo",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "env",
    "node_modules",
    "venv",
}
DENY_FILENAMES = {
    ".env",
    ".env.development",
    ".env.local",
    ".env.production",
    ".env.test",
    ".envrc",
    ".netrc",
    ".npmrc",
    ".pypirc",
    "credentials",
    "credentials.json",
    "id_ed25519",
    "id_rsa",
    "kubeconfig",
    "secrets.json",
    "wallet.json",
}
DENY_SUFFIXES = {".env", ".key", ".pem", ".p12", ".pfx"}
SECRET_NAME_TOKENS = {
    "access_token",
    "api_key",
    "apikey",
    "auth_token",
    "client_secret",
    "credential",
    "credentials",
    "password",
    "private_key",
    "private-key",
    "privatekey",
    "refresh_token",
    "secret",
    "seed_phrase",
    "seed-phrase",
    "service_account",
}
GENERATED_FILENAMES = {"release-lint-report.md", "release-lint-report.json"}
METADATA_CANDIDATES = {
    "metadata.json",
    "release.json",
    "suede-intake.json",
    "metadata.yaml",
    "metadata.yml",
    "release.yaml",
    "release.yml",
}
STEM_KEYWORDS = {
    "stem",
    "stems",
    "vocals",
    "vocal",
    "vox",
    "drums",
    "drum",
    "bass",
    "guitar",
    "keys",
    "piano",
    "instrumental",
    "inst",
}


class Finding(dict):
    def __init__(self, severity: str, category: str, code: str, message: str, fix: str) -> None:
        super().__init__(
            severity=severity,
            category=category,
            code=code,
            message=message,
            fix=fix,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lint a music release folder.")
    parser.add_argument("source", help="Source folder containing release assets.")
    parser.add_argument(
        "--metadata",
        default="",
        help="Optional metadata file: JSON, YAML/YML with PyYAML, or key=value text.",
    )
    parser.add_argument(
        "--output",
        default="release-lint-output",
        help="Output folder for release-lint-report.md/json. Must be outside the source folder.",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and folders. Secret-like files are still skipped.",
    )
    parser.add_argument(
        "--include-other",
        action="store_true",
        help="Include unrecognized file types in the inventory.",
    )
    parser.add_argument(
        "--include-absolute-paths",
        action="store_true",
        help="Write absolute local paths into reports. Off by default for public-safe sharing.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing generated report files in the output folder.",
    )
    return parser.parse_args()


def load_yaml_if_available(text: str) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover - dependency-dependent
        raise ValueError("YAML metadata requires PyYAML") from exc
    data = yaml.safe_load(text)
    return data if isinstance(data, dict) else {}


def load_key_value(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def load_metadata(path: Path | None) -> tuple[dict[str, Any], str]:
    if path is None:
        return {}, ""
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError(f"Metadata JSON must be an object: {path}")
        return data, str(path)
    if suffix in {".yaml", ".yml"}:
        return load_yaml_if_available(text), str(path)
    return load_key_value(text), str(path)


def discover_metadata(source: Path, explicit: str) -> Path | None:
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"Metadata file not found: {path}")
        if is_denied_path(path, source):
            raise SystemExit("Refusing to use a secret-like metadata path. Use a public-safe metadata JSON, YAML, or key=value text file.")
        return path
    for name in METADATA_CANDIDATES:
        candidate = source / name
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def normalize_key(data: dict[str, Any], aliases: list[str], default: Any = None) -> Any:
    for key in aliases:
        if key in data and data[key] not in (None, ""):
            return data[key]
    return default


def nested(data: dict[str, Any], key: str, default: Any = None) -> Any:
    value = data.get(key, default)
    return value if value not in (None, "") else default


def classify_file(path: Path, source: Path) -> tuple[str, str]:
    ext = path.suffix.lower()
    name = path.name.lower()
    try:
        context_parts = path.relative_to(source).parts
    except ValueError:
        context_parts = (path.name,)
    context = "/".join(part.lower() for part in context_parts)

    if ext in AUDIO_EXTS:
        if any(keyword in context for keyword in STEM_KEYWORDS) and "master" not in context and "final" not in context:
            return "stem", "stem"
        if "master" in context or "final" in context:
            return "audio", "master"
        if "mix" in context:
            return "audio", "mix"
        return "audio", "audio"
    if ext in VIDEO_EXTS:
        return "video", "video"
    if ext in LYRIC_EXTS or (ext in TEXT_EXTS and "lyric" in name):
        return "lyrics", "lyrics"
    if ext in IMAGE_EXTS:
        if "cover" in context or "artwork" in context:
            return "artwork", "cover-art"
        return "artwork", "image"
    if ext in DOC_EXTS:
        if "split" in context:
            return "document", "split-sheet"
        if "license" in context or "licence" in context:
            return "document", "license"
        if "contract" in context:
            return "document", "contract"
        return "document", "document"
    return "other", "unknown"


def is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def is_hidden_path(path: Path, source: Path) -> bool:
    try:
        relative = path.relative_to(source)
    except ValueError:
        relative = path
    return any(part.startswith(".") for part in relative.parts)


def is_denied_path(path: Path, source: Path) -> bool:
    try:
        relative = path.relative_to(source)
        within_source = True
    except ValueError:
        relative = path
        within_source = False
    lowered_parts = [part.lower() for part in relative.parts]
    # Only apply the directory-name denylist to ancestors inside the source
    # folder. For an explicit out-of-source --metadata path, the absolute path
    # may pass through benign dirs (.cache, .config, .next, ...) that would
    # otherwise trigger a false "secret-like path" rejection.
    if within_source and any(part in DENY_DIR_NAMES for part in lowered_parts[:-1]):
        return True
    filename = lowered_parts[-1]
    if filename in DENY_FILENAMES or filename.startswith(".env"):
        return True
    if path.suffix.lower() in DENY_SUFFIXES:
        return True
    normalized = filename.replace(".", "_")
    return any(token in normalized for token in SECRET_NAME_TOKENS)


def display_path(path: Path, source: Path, include_absolute: bool) -> str:
    if include_absolute:
        return str(path)
    try:
        return path.relative_to(source).as_posix()
    except ValueError:
        return path.name


def validate_output(source: Path, output: Path, force: bool) -> None:
    if output == source:
        raise SystemExit("Output folder must be separate from the source folder.")
    if is_under(output, source):
        raise SystemExit("Output folder must be outside the source folder.")
    existing = [output / filename for filename in GENERATED_FILENAMES if (output / filename).exists()]
    if existing and not force:
        names = ", ".join(path.name for path in existing)
        raise SystemExit(f"Refusing to overwrite existing report files ({names}); pass --force to replace them.")


def inventory_files(source: Path, output: Path, include_hidden: bool, include_other: bool) -> list[dict[str, Any]]:
    assets = []
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        if path.name.lower() in SKIP_NAMES:
            continue
        if is_under(path, output):
            continue
        if is_denied_path(path, source):
            continue
        if not include_hidden and is_hidden_path(path, source):
            continue
        category, role = classify_file(path, source)
        if category == "other" and not include_other:
            continue
        assets.append(
            {
                "relative_path": path.relative_to(source).as_posix(),
                "category": category,
                "role": role,
                "suffix": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
                "mime_guess": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            }
        )
    return assets


def optional_image_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        from PIL import Image  # type: ignore
    except Exception:
        return None
    try:
        with Image.open(path) as image:
            return image.size
    except Exception:
        return None


def maybe_number(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def boolish(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "y", "1", "confirmed"}:
            return True
        if lowered in {"false", "no", "n", "0", "unknown", "unconfirmed"}:
            return False
    return None


def contributor_sums(contributors: Any) -> tuple[float | None, float | None, bool]:
    if not isinstance(contributors, list) or not contributors:
        return None, None, False
    master_total = 0.0
    publishing_total = 0.0
    master_seen = False
    publishing_seen = False
    all_confirmed = True
    for contributor in contributors:
        if not isinstance(contributor, dict):
            all_confirmed = False
            continue
        master = maybe_number(
            normalize_key(contributor, ["master_percent", "master_pct", "master", "master_split"])
        )
        publishing = maybe_number(
            normalize_key(
                contributor,
                ["publishing_percent", "publishing_pct", "publishing", "publishing_split"],
            )
        )
        if master is not None:
            master_seen = True
            master_total += master
        if publishing is not None:
            publishing_seen = True
            publishing_total += publishing
        confirmed = boolish(normalize_key(contributor, ["confirmed", "confirmation", "approved"]))
        if confirmed is not True:
            all_confirmed = False
    return (
        master_total if master_seen else None,
        publishing_total if publishing_seen else None,
        all_confirmed,
    )


def scoped_value(metadata: dict[str, Any], scope_name: str, keys: str | list[str], default: Any = None) -> Any:
    aliases = [keys] if isinstance(keys, str) else keys
    scoped = metadata.get(scope_name)
    if isinstance(scoped, dict):
        for key in aliases:
            if key in scoped and scoped[key] not in (None, ""):
                return scoped[key]
    for key in aliases:
        if key in metadata and metadata[key] not in (None, ""):
            return metadata[key]
    return default


def rights_value(metadata: dict[str, Any], keys: str | list[str], default: Any = None) -> Any:
    return scoped_value(metadata, "rights", keys, default)


def project_value(metadata: dict[str, Any], keys: str | list[str], default: Any = None) -> Any:
    return scoped_value(metadata, "project", keys, default)


def creator_value(metadata: dict[str, Any], keys: str | list[str], default: Any = None) -> Any:
    return scoped_value(metadata, "creator", keys, default)


def suede_value(metadata: dict[str, Any], keys: str | list[str], default: Any = None) -> Any:
    return scoped_value(metadata, "suede", keys, default)


def confirmed_status(value: Any) -> bool:
    bool_value = boolish(value)
    if bool_value is True:
        return True
    return str(value).strip().lower() in {"confirmed", "claimed", "cleared", "yes", "true"}


def negative_status(value: Any) -> bool:
    return str(value).strip().lower() in {
        "no",
        "none",
        "false",
        "not-needed",
        "not_needed",
        "not-applicable",
        "not_applicable",
        "n/a",
    }


def positive_status(value: Any) -> bool:
    return boolish(value) is True or str(value).strip().lower() in {"1", "y", "yes", "true", "contains-samples", "contains_samples", "sampled"}


def unknown_status(value: Any) -> bool:
    return str(value).strip().lower() in {"unknown", "", "unconfirmed", "needs-confirmation"}


def add(findings: list[Finding], severity: str, category: str, code: str, message: str, fix: str) -> None:
    findings.append(Finding(severity, category, code, message, fix))


def lint(metadata: dict[str, Any], assets: list[dict[str, Any]], source: Path) -> list[Finding]:
    findings: list[Finding] = []
    counts = Counter(asset["category"] for asset in assets)

    title = project_value(metadata, ["title", "track_title", "song_title", "project_title"])
    artist = project_value(
        metadata,
        ["artist", "artist_name", "creator_name"],
        creator_value(metadata, ["name", "artist", "artist_name", "creator_name"]),
    )
    if not title:
        add(findings, "error", "metadata", "missing-title", "Title is missing.", "Add the official public title.")
    if not artist:
        add(findings, "error", "metadata", "missing-artist", "Artist or creator name is missing.", "Add the official artist or creator name.")

    for key, label in [
        ("release_date", "Release date"),
        ("genre", "Genre"),
        ("language", "Language"),
        ("description", "Description"),
    ]:
        if not nested(metadata, key):
            add(findings, "warning", "metadata", f"missing-{key.replace('_', '-')}", f"{label} is missing.", f"Add {label.lower()} metadata.")

    if "explicit" not in metadata and "explicit_content" not in metadata:
        add(findings, "warning", "metadata", "missing-explicit-status", "Explicit-content status is missing.", "Add explicit true/false status.")

    if counts["audio"] + counts["video"] == 0:
        add(findings, "error", "media", "missing-primary-media", "No primary audio or video file was found.", "Add or identify the final master or primary media file.")

    audio_assets = [asset for asset in assets if asset["category"] == "audio"]
    if audio_assets and not any(asset["suffix"] in LOSSLESS_AUDIO_EXTS for asset in audio_assets):
        add(findings, "warning", "media", "missing-lossless-master", "Audio exists but no WAV, AIFF, or FLAC master was found.", "Add a lossless master for high-quality delivery and optimization.")

    possible_masters = [
        asset
        for asset in audio_assets
        if asset["role"] == "master" or "master" in asset["relative_path"].lower() or "final" in asset["relative_path"].lower()
    ]
    if len(possible_masters) > 1:
        add(findings, "info", "media", "multiple-possible-masters", "Multiple possible masters were found.", "Mark one file as the final master.")

    if counts["artwork"] == 0:
        add(findings, "warning", "artwork", "missing-artwork", "No artwork image was found.", "Add release artwork before public distribution or catalog publication.")
    else:
        for asset in assets:
            if asset["category"] != "artwork":
                continue
            dimensions = optional_image_dimensions(source / asset["relative_path"])
            if dimensions is None:
                continue
            width, height = dimensions
            if width != height or width < 1400 or height < 1400:
                add(
                    findings,
                    "warning",
                    "artwork",
                    "weak-artwork-dimensions",
                    f"Artwork `{asset['relative_path']}` is {width}x{height}.",
                    "Use square high-resolution artwork when possible.",
                )

    if counts["lyrics"] == 0:
        add(findings, "info", "lyrics", "missing-lyrics", "No lyric or timed-text file was found.", "Add lyrics or timed lyrics if the release uses vocals.")

    intended_services = suede_value(metadata, "intended_services", [])
    intended_text = " ".join(intended_services) if isinstance(intended_services, list) else str(intended_services)
    needs_stems = any(token in intended_text.lower() for token in ["remix", "sync", "licens", "commerce", "optimization", "stems"])
    if counts["stem"] == 0:
        severity = "warning" if needs_stems else "info"
        add(findings, severity, "stems", "missing-stems", "No stems were found.", "Add stems or plan stem separation for remix, sync, licensing, or Suede optimization.")

    contributors = rights_value(metadata, ["contributors", "credits", "collaborators"])
    if not contributors:
        add(findings, "error", "credits", "missing-contributors", "Contributor or credit details are missing.", "Add contributors, roles, and confirmation status.")
    master_total, publishing_total, all_confirmed = contributor_sums(contributors)
    if master_total is not None and round(master_total, 4) != 100:
        add(findings, "error", "splits", "invalid-master-split-total", f"Master splits add to {master_total:g}, not 100.", "Correct master split percentages.")
    if publishing_total is not None and round(publishing_total, 4) != 100:
        add(findings, "error", "splits", "invalid-publishing-split-total", f"Publishing splits add to {publishing_total:g}, not 100.", "Correct publishing split percentages.")
    if contributors and not all_confirmed:
        add(findings, "warning", "credits", "contributors-unconfirmed", "One or more contributors lack confirmation.", "Collect contributor confirmations before royalty routing or licensing.")

    owner_claim = rights_value(
        metadata,
        ["owner_claim", "owner", "rights_owner", "master_owner", "publishing_owner"],
    )
    ownership_status = rights_value(
        metadata,
        ["ownership_status", "owner_status", "ownership_confirmed", "owner_confirmed"],
        "unknown",
    )
    if not owner_claim or not confirmed_status(ownership_status):
        add(findings, "error", "rights", "ownership-unconfirmed", "Ownership claim is missing or unconfirmed.", "Confirm master and publishing ownership.")

    contains_samples_value = rights_value(
        metadata,
        ["contains_samples", "samples", "sample_status", "third_party_material"],
        "unknown",
    )
    cover_or_interpolation_value = rights_value(
        metadata,
        ["cover_or_interpolation", "cover", "interpolation_status"],
        "unknown",
    )
    sample_clearance = str(
        rights_value(metadata, ["sample_clearance_status", "sample_clearance", "clearance_status"], "unknown")
    ).lower()
    if unknown_status(contains_samples_value) and unknown_status(cover_or_interpolation_value):
        add(findings, "error", "rights", "sample-status-unknown", "Sample, cover, interpolation, loop, or beat lease status is unknown.", "Confirm third-party material and clearance status.")
    third_party_indicated = positive_status(contains_samples_value) or positive_status(cover_or_interpolation_value)
    if third_party_indicated and sample_clearance not in {"cleared", "not-needed", "not_needed", "not_applicable", "not-applicable"}:
        add(findings, "error", "rights", "sample-clearance-missing", "Samples, covers, interpolations, or third-party material are indicated but clearance is not confirmed.", "Provide clearance details or remove uncleared material before licensing.")

    release_history = rights_value(
        metadata,
        "release_history",
        project_value(metadata, ["release_status", "release_history"], metadata.get("release_status", "unknown")),
    )
    if unknown_status(release_history):
        add(findings, "warning", "rights", "release-history-unknown", "Prior release, registration, minting, or licensing history is unknown.", "Confirm whether the work has already been distributed, registered, minted, licensed, or sold.")

    # Distributors and DSPs now ask for AI involvement at delivery, and purely
    # AI-generated material is not copyrightable in the US, so an unstated or
    # undocumented AI role is a licensing question, not a cosmetic gap.
    ai_involvement = rights_value(
        metadata,
        ["ai_involvement", "ai_disclosure", "ai_generated", "ai_use"],
        project_value(metadata, ["ai_involvement", "ai_disclosure"], "unknown"),
    )
    if isinstance(ai_involvement, (list, tuple)):
        ai_involvement = ", ".join(str(item) for item in ai_involvement) or "unknown"
    if unknown_status(ai_involvement):
        add(findings, "info", "rights", "ai-involvement-unstated", "AI involvement is not stated.", "State whether generative AI was used for vocals, instrumentation, composition, lyrics, artwork, or post-production (use \"none\" if not); distributors increasingly require this at delivery.")
    elif not negative_status(ai_involvement):
        human_authorship = rights_value(
            metadata,
            ["human_authorship", "human_authorship_notes", "human_contribution"],
            "",
        )
        if not human_authorship:
            add(findings, "warning", "rights", "ai-human-authorship-undocumented", "AI involvement is declared but human authorship is not documented.", "Record which elements a person wrote, performed, or arranged, with evidence such as session files or lyric drafts, before registration or licensing.")

    wallet = suede_value(
        metadata,
        ["wallet_address", "wallet", "payment_destination", "payment_address", "royalty_destination"],
        creator_value(
            metadata,
            ["wallet_address", "wallet", "payment_destination", "payment_address", "royalty_destination"],
            metadata.get("wallet_address", ""),
        ),
    )
    if not wallet:
        add(findings, "warning", "suede", "missing-wallet-or-payment-destination", "No creator wallet or payment destination was provided.", "Add a public wallet or payment-routing note if Suede royalty routing or agent commerce is intended.")

    provenance_notes = suede_value(
        metadata,
        ["provenance_notes", "creation_notes", "chain_of_custody", "source_notes"],
        scoped_value(
            metadata,
            "provenance",
            ["provenance_notes", "creation_notes", "chain_of_custody", "source_notes"],
            metadata.get("provenance_notes", ""),
        ),
    )
    if not provenance_notes:
        add(findings, "warning", "suede", "missing-provenance-notes", "No provenance or creation-history notes were provided.", "Add creation history, source notes, or chain-of-custody details.")

    add(findings, "info", "suede", "rights-passport-candidate", "Project can be prepared with a Suede Rights Passport after blockers are resolved.", "Use suede-rights-passport once error findings are fixed or clearly documented.")
    return findings


def score(findings: list[Finding]) -> int:
    value = 100
    for finding in findings:
        if finding["severity"] == "error":
            value -= 15
        elif finding["severity"] == "warning":
            value -= 5
        else:
            value -= 1
    return max(value, 0)


def status_for(score_value: int, severity_counts: Counter) -> str:
    if severity_counts["error"]:
        return "blocked"
    if score_value >= 90:
        return "strong"
    if score_value >= 75:
        return "usable-with-cleanup"
    if score_value >= 50:
        return "needs-work"
    return "blocked"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def markdown_table_findings(findings: list[Finding]) -> str:
    rows = ["| Severity | Category | Code | Message | Fix |", "| --- | --- | --- | --- | --- |"]
    for finding in findings:
        rows.append(
            f"| {finding['severity']} | {finding['category']} | `{finding['code']}` | "
            f"{finding['message']} | {finding['fix']} |"
        )
    return "\n".join(rows)


def markdown_asset_counts(counts: Counter) -> str:
    rows = ["| Category | Count |", "| --- | ---: |"]
    for category in ["audio", "video", "artwork", "lyrics", "stem", "document", "other"]:
        rows.append(f"| {category} | {counts[category]} |")
    return "\n".join(rows)


def write_markdown_report(path: Path, report: dict[str, Any]) -> None:
    counts = report["summary"]["asset_counts"]
    severity_counts = report["severity_counts"]
    title = report["summary"]["title"]
    artist = report["summary"]["artist"]
    readiness = "Blocked until error findings are resolved."
    if report["status"] == "strong":
        readiness = "Strong candidate for Suede Rights Passport preparation."
    elif report["status"] == "usable-with-cleanup":
        readiness = "Usable with cleanup before final release or Suede intake."

    content = f"""# Release Lint Report

Private draft: review and redact before publishing, committing, or sharing
outside the intended Suede intake workflow.

## Summary

- Project: {title}
- Artist: {artist}
- Source: {report['source_root']}
- Metadata source: {report['metadata_source'] or 'none detected'}
- Score: {report['score']}
- Status: {report['status']}

## Severity Counts

| Severity | Count |
| --- | ---: |
| Error | {severity_counts['error']} |
| Warning | {severity_counts['warning']} |
| Info | {severity_counts['info']} |

## Findings

{markdown_table_findings(report['findings'])}

## Asset Inventory

{markdown_asset_counts(Counter(counts))}

## Suede Readiness

{readiness}

## Recommended Next Action

{report['recommended_next_action']}
"""
    path.write_text(content, encoding="utf-8")


def recommend_next_action(status: str, severity_counts: Counter) -> str:
    if severity_counts["error"]:
        return "Fix error findings before preparing a Suede Rights Passport, registering rights, licensing, or routing royalties."
    if status == "strong":
        return "Prepare a Suede Rights Passport transfer package."
    return "Clean warning findings, then prepare a Suede Rights Passport transfer package."


def main() -> int:
    args = parse_args()
    source = Path(args.source).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    if not source.exists() or not source.is_dir():
        raise SystemExit(f"Source folder not found: {source}")
    validate_output(source, output, args.force)
    output.mkdir(parents=True, exist_ok=True)

    metadata_path = discover_metadata(source, args.metadata)
    try:
        metadata, _metadata_source = load_metadata(metadata_path)
    except Exception as exc:
        raise SystemExit(f"Could not load metadata: {exc}") from exc
    metadata_source = display_path(metadata_path, source, args.include_absolute_paths) if metadata_path else ""
    assets = inventory_files(source, output, args.include_hidden, args.include_other)
    findings = lint(metadata, assets, source)
    severity_counts = Counter(finding["severity"] for finding in findings)
    score_value = score(findings)
    status = status_for(score_value, severity_counts)
    asset_counts = Counter(asset["category"] for asset in assets)

    title = project_value(metadata, ["title", "track_title", "song_title", "project_title"], "unknown")
    artist = project_value(
        metadata,
        ["artist", "artist_name", "creator_name"],
        creator_value(metadata, ["name", "artist", "artist_name", "creator_name"], "unknown"),
    )

    report = {
        "schema_version": "0.1.0",
        "package_type": "music-release-lint-report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_root": str(source) if args.include_absolute_paths else source.name,
        "metadata_source": metadata_source,
        "score": score_value,
        "status": status,
        "severity_counts": {
            "error": severity_counts["error"],
            "warning": severity_counts["warning"],
            "info": severity_counts["info"],
        },
        "summary": {
            "title": title,
            "artist": artist,
            "asset_counts": {
                "audio": asset_counts["audio"],
                "video": asset_counts["video"],
                "artwork": asset_counts["artwork"],
                "lyrics": asset_counts["lyrics"],
                "stem": asset_counts["stem"],
                "document": asset_counts["document"],
                "other": asset_counts["other"],
            },
        },
        "assets": assets,
        "findings": findings,
        "recommended_next_action": recommend_next_action(status, severity_counts),
    }

    write_json(output / "release-lint-report.json", report)
    write_markdown_report(output / "release-lint-report.md", report)

    print(f"Created release lint report: {output}")
    print(f"Score: {score_value}")
    print(
        "Findings: "
        f"{severity_counts['error']} error, "
        f"{severity_counts['warning']} warning, "
        f"{severity_counts['info']} info"
    )
    return 1 if severity_counts["error"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
