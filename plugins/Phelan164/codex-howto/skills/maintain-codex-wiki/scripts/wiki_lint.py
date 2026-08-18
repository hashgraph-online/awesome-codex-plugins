#!/usr/bin/env python3
"""Validate a review-first Codex knowledge wiki using only the standard library."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse


SOURCE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
OBJECT_ID_RE = re.compile(r"^[0-9a-f]+$", re.IGNORECASE)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
SOURCE_REF_RE = re.compile(r"`([a-z0-9]+(?:-[a-z0-9]+)*)`")
STATUS_RE = re.compile(r"^>\s*Status:\s*(\S+)\s*$", re.IGNORECASE)
VERIFIED_RE = re.compile(
    r"^>\s*Last verified:\s*(\d{4}-\d{2}-\d{2})\s*$", re.IGNORECASE
)
UPDATED_RE = re.compile(
    r"^>\s*Last updated:\s*(\d{4}-\d{2}-\d{2})\s*$", re.IGNORECASE
)
SOURCES_RE = re.compile(r"^>\s*Sources:\s*(.+?)\s*$", re.IGNORECASE)
ALLOWED_KINDS = {"official", "repository", "community", "experiment"}
ALLOWED_STATUSES = {"verified", "community", "experimental", "decision"}
PAGE_DIRS = ("topics", "decisions", "experiments")
SENSITIVE_PATH_NAMES = {
    ".netrc",
    ".npmrc",
    ".pypirc",
    "credentials.json",
    "credentials.yaml",
    "credentials.yml",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "id_rsa",
    "secrets.json",
    "secrets.yaml",
    "secrets.yml",
}
SENSITIVE_PATH_SUFFIXES = (".key", ".kdbx", ".p12", ".pem", ".pfx")


def run_git(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["GIT_NO_LAZY_FETCH"] = "1"
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    return subprocess.run(args, env=env, **kwargs)


def parse_date(value: str, label: str, errors: list[str]) -> None:
    try:
        date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label}: expected ISO date YYYY-MM-DD, got {value!r}")


def confined_regular_file(
    path: Path,
    root: Path,
    label: str,
    errors: list[str],
    *,
    missing_message: str | None = None,
) -> bool:
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError:
        errors.append(missing_message or f"{label}: file does not exist")
        return False
    if not resolved.is_relative_to(root.resolve()):
        errors.append(f"{label}: file escapes the project root")
        return False
    try:
        relative = path.relative_to(root)
    except ValueError:
        errors.append(f"{label}: file escapes the project root")
        return False
    candidate = root
    for part in relative.parts:
        candidate /= part
        if candidate.is_symlink():
            errors.append(f"{label}: path or parent is a symlink")
            return False
    if not resolved.is_file():
        errors.append(f"{label}: expected a regular file")
        return False
    return True


def sensitive_repository_path(relative: PurePosixPath) -> bool:
    names = {part.casefold() for part in relative.parts}
    filename = relative.name.casefold()
    return (
        any(name in names for name in {".aws", ".git", ".gnupg", ".ssh"})
        or filename == ".env"
        or filename.startswith(".env.")
        or filename in SENSITIVE_PATH_NAMES
        or filename.endswith(SENSITIVE_PATH_SUFFIXES)
    )


def git_tree_entry(root: Path, revision: str, relative: str) -> tuple[str, str] | None:
    completed = run_git(
        [
            "git",
            "-C",
            str(root),
            "ls-tree",
            "-z",
            "--full-tree",
            revision,
            "--",
            relative,
        ],
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout:
        return None
    metadata, separator, returned_path = completed.stdout.partition(b"\t")
    fields = metadata.split()
    if separator != b"\t" or len(fields) != 3:
        return None
    try:
        decoded_path = returned_path.removesuffix(b"\0").decode("utf-8")
        mode = fields[0].decode("ascii")
        object_type = fields[1].decode("ascii")
    except UnicodeDecodeError:
        return None
    if decoded_path != relative:
        return None
    return mode, object_type


def git_trusted_refs(root: Path) -> list[str]:
    configured = run_git(
        ["git", "-C", str(root), "config", "--get-all", "codex.wikiTrustedRef"],
        capture_output=True,
        text=True,
        check=False,
    )
    refs = [
        value.strip()
        for value in configured.stdout.splitlines()
        if value.strip().startswith(("refs/heads/", "refs/remotes/"))
    ]
    if refs:
        return refs

    default_remote = run_git(
        [
            "git",
            "-C",
            str(root),
            "symbolic-ref",
            "--quiet",
            "refs/remotes/origin/HEAD",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if default_remote.returncode == 0 and default_remote.stdout.strip():
        return [default_remote.stdout.strip()]
    return []


def git_revision_is_trusted(root: Path, revision: str, refs: list[str]) -> bool:
    return any(
        run_git(
            [
                "git",
                "-C",
                str(root),
                "merge-base",
                "--is-ancestor",
                revision,
                ref,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
        for ref in refs
    )


def git_revision_exists(root: Path, revision: str) -> bool:
    completed = run_git(
        [
            "git",
            "-C",
            str(root),
            "cat-file",
            "-e",
            f"{revision}^{{commit}}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def git_blob_exists(root: Path, revision: str, relative: str) -> bool:
    completed = run_git(
        [
            "git",
            "-C",
            str(root),
            "cat-file",
            "-e",
            f"{revision}:{relative}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def git_repository_is_shallow(root: Path) -> bool:
    completed = run_git(
        ["git", "-C", str(root), "rev-parse", "--is-shallow-repository"],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0 and completed.stdout.strip() == "true"


def git_repository_is_partial(root: Path) -> bool:
    completed = run_git(
        [
            "git",
            "-C",
            str(root),
            "config",
            "--get-regexp",
            r"^remote\..*\.promisor$",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0 and any(
        line.rsplit(maxsplit=1)[-1].casefold() == "true"
        for line in completed.stdout.splitlines()
        if line.split()
    )


def git_object_id_length(root: Path) -> int | None:
    completed = run_git(
        ["git", "-C", str(root), "rev-parse", "--show-object-format"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return {"sha1": 40, "sha256": 64}.get(completed.stdout.strip())


def load_sources(root: Path, errors: list[str]) -> dict[str, dict[str, object]]:
    path = root / "knowledge" / "sources.json"
    if not confined_regular_file(
        path,
        root,
        "knowledge/sources.json",
        errors,
        missing_message="missing knowledge/sources.json",
    ):
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid knowledge/sources.json: {exc}")
        return {}

    if payload.get("schema_version") != 1:
        errors.append("knowledge/sources.json: schema_version must be 1")
    items = payload.get("sources")
    if not isinstance(items, list):
        errors.append("knowledge/sources.json: sources must be a list")
        return {}

    sources: dict[str, dict[str, object]] = {}
    for position, item in enumerate(items, start=1):
        label = f"knowledge/sources.json source #{position}"
        if not isinstance(item, dict):
            errors.append(f"{label}: expected an object")
            continue
        source_id = item.get("id")
        if not isinstance(source_id, str) or not SOURCE_ID_RE.fullmatch(source_id):
            errors.append(f"{label}: invalid id {source_id!r}")
            continue
        if source_id in sources:
            errors.append(f"{label}: duplicate id {source_id!r}")
            continue
        sources[source_id] = item

        if not isinstance(item.get("title"), str) or not item["title"].strip():
            errors.append(f"{label}: title is required")
        if item.get("kind") not in ALLOWED_KINDS:
            errors.append(
                f"{label}: kind must be one of {', '.join(sorted(ALLOWED_KINDS))}"
            )
        verified = item.get("last_verified")
        if not isinstance(verified, str):
            errors.append(f"{label}: last_verified is required")
        else:
            parse_date(verified, f"{label} last_verified", errors)

        revision = item.get("revision")
        if revision is not None and (
            not isinstance(revision, str) or not revision.strip()
        ):
            errors.append(f"{label}: revision must be a non-empty string")

        supersedes = item.get("supersedes")
        if supersedes is not None and (
            not isinstance(supersedes, list)
            or any(
                not isinstance(value, str) or not SOURCE_ID_RE.fullmatch(value)
                for value in supersedes
            )
        ):
            errors.append(f"{label}: supersedes must be a list of source IDs")

        affected_pages = item.get("affected_pages")
        if affected_pages is not None and (
            not isinstance(affected_pages, list)
            or any(not isinstance(value, str) or not value for value in affected_pages)
        ):
            errors.append(
                f"{label}: affected_pages must be a list of project-relative paths"
            )

        has_url = "url" in item
        has_path = "path" in item
        if has_url == has_path:
            errors.append(f"{label}: define exactly one of url or path")
        elif has_url:
            url = item["url"]
            parsed = urlparse(url) if isinstance(url, str) else None
            if not parsed or parsed.scheme != "https" or not parsed.netloc:
                errors.append(f"{label}: url must be an absolute HTTPS URL")
        else:
            local = item["path"]
            if not isinstance(local, str) or not local:
                errors.append(f"{label}: path must be a non-empty string")
                continue
            local_path = PurePosixPath(local)
            if (
                local_path.is_absolute()
                or ".." in local_path.parts
                or local_path.as_posix() != local
            ):
                errors.append(
                    f"{label}: path must be a normalized project-relative path"
                )
                continue
            if sensitive_repository_path(local_path):
                errors.append(f"{label}: sensitive repository path is not allowed")
                continue
            object_id_length = git_object_id_length(root)
            if object_id_length is None:
                errors.append(
                    f"{label}: cannot determine repository Git object format"
                )
            elif (
                not isinstance(revision, str)
                or len(revision) != object_id_length
                or not OBJECT_ID_RE.fullmatch(revision)
            ):
                errors.append(
                    f"{label}: repository evidence requires a full "
                    f"{object_id_length}-character Git revision"
                )
            else:
                trusted_refs = git_trusted_refs(root)
                revision_exists = git_revision_exists(root, revision)
                revision_is_trusted = bool(
                    trusted_refs
                    and revision_exists
                    and git_revision_is_trusted(root, revision, trusted_refs)
                )
                incomplete_shallow_history = git_repository_is_shallow(root) and (
                    not revision_exists or not revision_is_trusted
                )
                incomplete_partial_clone = git_repository_is_partial(root) and (
                    not revision_exists or not revision_is_trusted
                )
                if not trusted_refs:
                    errors.append(
                        f"{label}: repository trusted refs are not configured"
                    )
                elif incomplete_shallow_history:
                    errors.append(
                        f"{label}: shallow repository history cannot verify "
                        f"revision against trusted refs: {revision}"
                    )
                elif incomplete_partial_clone:
                    errors.append(
                        f"{label}: partial clone is missing objects required to "
                        f"verify revision against trusted refs: {revision}"
                    )
                elif not revision_is_trusted:
                    errors.append(
                        f"{label}: repository revision is not reachable from "
                        f"trusted refs: {revision}"
                    )
            if (
                isinstance(revision, str)
                and len(revision) == object_id_length
                and OBJECT_ID_RE.fullmatch(revision)
                and not (
                    (
                        git_repository_is_shallow(root)
                        or git_repository_is_partial(root)
                    )
                    and not git_revision_exists(root, revision)
                )
            ):
                entry = git_tree_entry(root, revision, local)
                if entry is None:
                    errors.append(
                        f"{label}: repository evidence does not exist at revision: "
                        f"{revision}:{local}"
                    )
                elif entry[0] not in {"100644", "100755"} or entry[1] != "blob":
                    errors.append(
                        f"{label}: repository evidence must be a regular file at "
                        f"revision: {revision}:{local}"
                    )
                elif not git_blob_exists(root, revision, local):
                    if git_repository_is_partial(root):
                        errors.append(
                            f"{label}: partial clone is missing the repository "
                            f"evidence blob: {revision}:{local}"
                        )
                    else:
                        errors.append(
                            f"{label}: repository evidence blob is unavailable: "
                            f"{revision}:{local}"
                        )
    return sources


def wiki_pages(root: Path) -> list[Path]:
    knowledge = root / "knowledge"
    pages: list[Path] = []
    for name in PAGE_DIRS:
        directory = knowledge / name
        if directory.is_dir():
            pages.extend(directory.rglob("*.md"))
    return sorted(pages)


def page_metadata(
    path: Path, root: Path, known_sources: set[str], errors: list[str]
) -> set[str]:
    relative = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith("# "):
        errors.append(f"{relative}: first line must be an H1")

    status = None
    verified = None
    updated = None
    source_ids: set[str] = set()
    for line in lines[1:12]:
        if match := STATUS_RE.match(line):
            status = match.group(1).lower()
        elif match := VERIFIED_RE.match(line):
            verified = match.group(1)
        elif match := UPDATED_RE.match(line):
            updated = match.group(1)
        elif match := SOURCES_RE.match(line):
            source_ids = set(SOURCE_REF_RE.findall(match.group(1)))

    if status not in ALLOWED_STATUSES:
        errors.append(
            f"{relative}: Status must be one of "
            f"{', '.join(sorted(ALLOWED_STATUSES))}"
        )
    if status == "verified":
        if verified is None:
            errors.append(f"{relative}: missing Last verified metadata")
        else:
            parse_date(verified, f"{relative} Last verified", errors)
    elif status in ALLOWED_STATUSES:
        if verified is not None:
            errors.append(
                f"{relative}: Last verified is only valid for verified pages"
            )
        if updated is None:
            errors.append(f"{relative}: missing Last updated metadata")
        else:
            parse_date(updated, f"{relative} Last updated", errors)
    if not source_ids:
        errors.append(f"{relative}: Sources must contain at least one backticked ID")
    for source_id in sorted(source_ids - known_sources):
        errors.append(f"{relative}: unknown source ID {source_id!r}")
    return source_ids


def check_page_titles(pages: list[Path], root: Path, errors: list[str]) -> None:
    titles: dict[str, Path] = {}
    for page in pages:
        lines = page.read_text(encoding="utf-8").splitlines()
        if not lines:
            continue
        first_line = lines[0]
        title = first_line.removeprefix("# ").strip()
        normalized = re.sub(r"\s+", " ", title).casefold()
        previous = titles.get(normalized)
        if previous is not None:
            errors.append(
                f"{page.relative_to(root)}: duplicate page title {title!r}; "
                f"already used by {previous.relative_to(root)}"
            )
        else:
            titles[normalized] = page


def check_source_relationships(
    root: Path,
    sources: dict[str, dict[str, object]],
    page_sources: dict[str, set[str]],
    errors: list[str],
) -> None:
    graph: dict[str, list[str]] = {}
    for source_id, item in sources.items():
        supersedes = item.get("supersedes", [])
        if not isinstance(supersedes, list):
            continue
        graph[source_id] = [
            target for target in supersedes if isinstance(target, str)
        ]
        for target in supersedes:
            if not isinstance(target, str):
                continue
            if target == source_id:
                errors.append(f"source {source_id!r}: cannot supersede itself")
            elif target not in sources:
                errors.append(
                    f"source {source_id!r}: unknown superseded source {target!r}"
                )

        affected_pages = item.get("affected_pages", [])
        if not isinstance(affected_pages, list):
            continue
        for relative in affected_pages:
            if not isinstance(relative, str):
                continue
            target = (root / relative).resolve()
            if not target.is_relative_to((root / "knowledge").resolve()):
                errors.append(
                    f"source {source_id!r}: affected page escapes knowledge/: "
                    f"{relative}"
                )
            elif relative not in page_sources:
                errors.append(
                    f"source {source_id!r}: affected page is not a wiki page: "
                    f"{relative}"
                )
            elif source_id not in page_sources[relative]:
                errors.append(
                    f"source {source_id!r}: affected page does not cite this "
                    f"source: {relative}"
                )

    state: dict[str, int] = {}

    def visit(source_id: str, trail: list[str]) -> None:
        if state.get(source_id) == 2:
            return
        if state.get(source_id) == 1:
            start = trail.index(source_id)
            cycle = trail[start:] + [source_id]
            errors.append(f"source supersession cycle: {' -> '.join(cycle)}")
            return
        state[source_id] = 1
        for target in graph.get(source_id, []):
            if target in sources:
                visit(target, trail + [source_id])
        state[source_id] = 2

    for source_id in sources:
        visit(source_id, [])


def check_index(root: Path, pages: list[Path], errors: list[str]) -> None:
    index = root / "knowledge" / "index.md"
    if not confined_regular_file(
        index,
        root,
        "knowledge/index.md",
        errors,
        missing_message="missing knowledge/index.md",
    ):
        return
    text = index.read_text(encoding="utf-8")

    indexed: set[Path] = set()
    for target in LINK_RE.findall(text):
        local = target.partition("#")[0]
        if not local or local.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (index.parent / unquote(local)).resolve()
        if any(resolved.is_relative_to((root / "knowledge" / name).resolve()) for name in PAGE_DIRS):
            indexed.add(resolved)

    for page in pages:
        if page.resolve() not in indexed:
            errors.append(
                f"knowledge/index.md: missing page "
                f"{page.relative_to(root / 'knowledge').as_posix()}"
            )


def check_local_links(root: Path, errors: list[str]) -> None:
    knowledge = root / "knowledge"
    if not knowledge.is_dir():
        errors.append("missing knowledge/ directory")
        return
    for path in sorted(knowledge.rglob("*.md")):
        relative = path.relative_to(root).as_posix()
        if not confined_regular_file(path, root, relative, errors):
            continue
        text = path.read_text(encoding="utf-8")
        for target in LINK_RE.findall(text):
            local = target.partition("#")[0]
            if not local or local.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (path.parent / unquote(local)).resolve()
            if not resolved.is_relative_to(root.resolve()):
                errors.append(
                    f"{path.relative_to(root)}: link escapes project root: {target}"
                )
            elif not resolved.exists():
                errors.append(
                    f"{path.relative_to(root)}: broken local link: {target}"
                )


def validate(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    sources = load_sources(root, errors)
    discovered_pages = wiki_pages(root)
    pages = [
        page
        for page in discovered_pages
        if confined_regular_file(
            page, root, page.relative_to(root).as_posix(), errors
        )
    ]
    if not pages:
        errors.append("knowledge/: no topic, decision, or experiment pages found")

    referenced: set[str] = set()
    page_sources: dict[str, set[str]] = {}
    for page in pages:
        source_ids = page_metadata(page, root, set(sources), errors)
        referenced.update(source_ids)
        page_sources[page.relative_to(root).as_posix()] = source_ids
    for source_id in sorted(set(sources) - referenced):
        warnings.append(f"unreferenced source: {source_id}")

    check_page_titles(pages, root, errors)
    check_source_relationships(root, sources, page_sources, errors)
    check_index(root, pages, errors)
    check_local_links(root, errors)
    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="repository containing knowledge/ (default: current directory)",
    )
    args = parser.parse_args(argv)
    root = Path(args.project_root).resolve()
    errors, warnings = validate(root)

    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        print(
            f"Wiki lint failed: {len(errors)} error(s), {len(warnings)} warning(s).",
            file=sys.stderr,
        )
        return 1
    print(f"Wiki lint passed: {len(wiki_pages(root))} pages, {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
