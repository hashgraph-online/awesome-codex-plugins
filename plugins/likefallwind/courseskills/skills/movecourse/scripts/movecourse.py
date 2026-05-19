#!/usr/bin/env python3
"""Publish generated course lesson videos into aistudy101 course-assets."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_DEST_ROOT = Path("/home/likefallwind/code/aistudy101-website/static/course-assets")
DEFAULT_SOURCES_YAML = Path("/home/likefallwind/code/aistudy101-website/course-sources.yaml")
DEFAULT_COURSE_ID_REGISTRY = Path(
    "/home/likefallwind/code/aistudy101-website/docs/course-id-registry.md"
)

COURSE_ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


@dataclass(frozen=True)
class Operation:
    lesson: str
    source: Path
    destination: Path


@dataclass(frozen=True)
class CourseIdEntry:
    title: str
    standard_title: str
    course_id: str
    status: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish lesson*/.mp4 files into aistudy101 course-assets."
    )
    parser.add_argument("--course", help="Course id, e.g. ai-enlightenment")
    parser.add_argument("--source", default=".", help="Source course directory; default: cwd")
    parser.add_argument("--dest-root", default=str(DEFAULT_DEST_ROOT), help="Website course-assets root")
    parser.add_argument(
        "--sources-yaml",
        default=str(DEFAULT_SOURCES_YAML),
        help="course-sources.yaml used to validate course ids",
    )
    parser.add_argument(
        "--course-id-registry",
        default=str(DEFAULT_COURSE_ID_REGISTRY),
        help="Markdown course ID registry used to resolve planned curriculum course ids",
    )
    parser.add_argument(
        "--course-title",
        help="Curriculum or standard Chinese course title; resolves to --course via the ID registry",
    )
    parser.add_argument(
        "--filename-template",
        default="{lesson}-intro.mp4",
        help="English output filename template. Supports {lesson}, e.g. lesson1.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show operations without writing")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing destination mp4")
    parser.add_argument(
        "--move",
        action="store_true",
        help="Delete source mp4 after verified copy. Use only when explicitly requested.",
    )
    parser.add_argument(
        "--allow-unknown-course",
        action="store_true",
        help="Proceed even when --course is absent from course-sources.yaml",
    )
    parser.add_argument("--list-courses", action="store_true", help="Print known course ids and exit")
    return parser.parse_args()


def load_course_ids(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Course registry not found: {path}")

    ids: list[str] = []
    id_line = re.compile(r"^\s*-\s+id:\s*['\"]?([^'\"\s#]+)")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = id_line.match(line)
        if match:
            ids.append(match.group(1))
    return ids


def validate_course_id(course_id: str) -> str:
    if not COURSE_ID_RE.fullmatch(course_id):
        raise ValueError(
            f"Invalid course id {course_id!r}; use lowercase kebab-case letters, "
            "digits, and single hyphens only"
        )
    if len(course_id) > 64:
        raise ValueError(f"Invalid course id {course_id!r}; maximum length is 64")
    return course_id


def load_course_id_registry(path: Path) -> list[CourseIdEntry]:
    if not path.exists():
        return []

    entries: list[CourseIdEntry] = []
    row_re = re.compile(
        r"^\|\s*(?P<columns>.+?)\s*\|\s*$",
    )
    for line in path.read_text(encoding="utf-8").splitlines():
        match = row_re.match(line)
        if not match:
            continue
        cells = [cell.strip() for cell in match.group("columns").split("|")]
        if len(cells) == 6:
            title, standard_title, course_id, status = cells[2], cells[3], cells[4], cells[5]
        elif len(cells) == 5:
            title, standard_title, course_id, status = cells[1], cells[2], cells[3], cells[4]
        else:
            continue
        if title in {"全景图名称", "---"} or "`" not in course_id:
            continue
        id_match = re.fullmatch(r"`([^`]+)`", course_id)
        if id_match is None:
            continue
        entries.append(
            CourseIdEntry(
                title=title,
                standard_title=standard_title,
                course_id=validate_course_id(id_match.group(1)),
                status=status,
            )
        )
    return entries


def normalize_title(title: str) -> str:
    return re.sub(r"\s+", "", title).lower()


def resolve_course_id_from_title(
    title: str, registry_entries: list[CourseIdEntry]
) -> CourseIdEntry | None:
    normalized = normalize_title(title)
    matches = [
        entry
        for entry in registry_entries
        if normalize_title(entry.title) == normalized
        or normalize_title(entry.standard_title) == normalized
    ]
    if not matches:
        return None
    if len(matches) > 1:
        ids = ", ".join(entry.course_id for entry in matches)
        raise ValueError(f"Course title {title!r} matches multiple course ids: {ids}")
    return matches[0]


def lesson_sort_key(path: Path) -> tuple[int, str]:
    match = re.fullmatch(r"lesson0*(\d+)", path.name, flags=re.IGNORECASE)
    if not match:
        return (sys.maxsize, path.name)
    return (int(match.group(1)), path.name)


def normalized_lesson_name(path: Path) -> str:
    match = re.fullmatch(r"lesson0*(\d+)", path.name, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"Unsupported lesson directory name: {path.name}")
    return f"lesson{int(match.group(1))}"


def collect_operations(
    source_root: Path,
    dest_root: Path,
    course: str,
    filename_template: str,
    overwrite: bool,
) -> list[Operation]:
    if not source_root.is_dir():
        raise NotADirectoryError(f"Source directory not found: {source_root}")

    lesson_dirs = sorted(
        [
            path
            for path in source_root.iterdir()
            if path.is_dir() and re.fullmatch(r"lesson0*\d+", path.name, flags=re.IGNORECASE)
        ],
        key=lesson_sort_key,
    )
    if not lesson_dirs:
        raise ValueError(f"No lessonN directories found under {source_root}")

    errors: list[str] = []
    operations: list[Operation] = []
    for lesson_dir in lesson_dirs:
        lesson = normalized_lesson_name(lesson_dir)
        mp4s = sorted(path for path in lesson_dir.glob("*.mp4") if path.is_file())
        if len(mp4s) != 1:
            errors.append(f"{lesson_dir}: expected exactly one .mp4, found {len(mp4s)}")
            continue
        if mp4s[0].stat().st_size == 0:
            errors.append(f"{mp4s[0]}: source mp4 is empty")
            continue

        filename = filename_template.format(lesson=lesson, lesson_number=lesson.removeprefix("lesson"))
        if not filename.lower().endswith(".mp4"):
            errors.append(f"{lesson}: filename template must produce an .mp4 name, got {filename!r}")
            continue
        if not re.fullmatch(r"[A-Za-z0-9._-]+", filename):
            errors.append(f"{lesson}: output filename must be English/ASCII-safe, got {filename!r}")
            continue

        destination = dest_root / course / lesson / "video" / filename
        if destination.exists() and not overwrite:
            errors.append(f"{destination}: already exists; pass --overwrite to replace")
            continue
        operations.append(Operation(lesson=lesson, source=mp4s[0], destination=destination))

    if errors:
        raise ValueError("Preflight failed:\n" + "\n".join(f"- {error}" for error in errors))
    return operations


def verified_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_name(destination.name + ".tmp")
    if tmp.exists():
        tmp.unlink()
    shutil.copy2(source, tmp)
    if tmp.stat().st_size == 0 or source.stat().st_size != tmp.stat().st_size:
        tmp.unlink(missing_ok=True)
        raise IOError(f"Copy verification failed for {source}")
    tmp.replace(destination)


def print_manifest(operations: list[Operation], action: str) -> None:
    for operation in operations:
        print(f"{action}: {operation.source} -> {operation.destination}")


def main() -> int:
    args = parse_args()
    source_root = Path(args.source).expanduser().resolve()
    dest_root = Path(args.dest_root).expanduser().resolve()
    sources_yaml = Path(args.sources_yaml).expanduser().resolve()

    try:
        course_ids = load_course_ids(sources_yaml)
        registry_entries = load_course_id_registry(Path(args.course_id_registry).expanduser().resolve())
        registry_ids = [entry.course_id for entry in registry_entries]
        if args.list_courses:
            known = set(course_ids)
            for course_id in course_ids:
                print(course_id)
            for entry in registry_entries:
                if entry.course_id not in known:
                    print(f"{entry.course_id}\t{entry.status}\t{entry.standard_title}")
            return 0

        course = args.course
        if args.course_title:
            entry = resolve_course_id_from_title(args.course_title, registry_entries)
            if entry is None:
                print(
                    f"movecourse: course title {args.course_title!r} is not listed in "
                    f"{Path(args.course_id_registry).expanduser().resolve()}",
                    file=sys.stderr,
                )
                return 2
            if course and course != entry.course_id:
                print(
                    f"movecourse: --course {course!r} conflicts with --course-title "
                    f"{args.course_title!r}, which maps to {entry.course_id!r}",
                    file=sys.stderr,
                )
                return 2
            course = entry.course_id
            print(
                f"Resolved course title {args.course_title!r} to {course!r} "
                f"({entry.status})."
            )

        if not course:
            print(
                "movecourse: --course or --course-title is required unless --list-courses is used",
                file=sys.stderr,
            )
            return 2
        course = validate_course_id(course)

        if course not in course_ids and course not in registry_ids and not args.allow_unknown_course:
            print(
                f"Course id {course!r} is not listed in {sources_yaml} or "
                f"{Path(args.course_id_registry).expanduser().resolve()}. "
                "Check the course ID registry before inventing a new id. "
                "Pass --allow-unknown-course only after confirmation.",
                file=sys.stderr,
            )
            if course_ids:
                print("Known course ids: " + ", ".join(course_ids), file=sys.stderr)
            return 2
        if course not in course_ids and course in registry_ids:
            print(
                f"Course id {course!r} is reserved in the ID registry but not yet "
                f"registered in {sources_yaml}. Static assets can be copied now, "
                "but the website course will not become clickable until course-sources.yaml is updated."
            )

        operations = collect_operations(
            source_root=source_root,
            dest_root=dest_root,
            course=course,
            filename_template=args.filename_template,
            overwrite=args.overwrite,
        )

        print_manifest(operations, "Would move" if args.dry_run and args.move else "Would copy" if args.dry_run else "Move" if args.move else "Copy")
        if args.dry_run:
            return 0

        for operation in operations:
            verified_copy(operation.source, operation.destination)
            if args.move:
                operation.source.unlink()

        print(f"Completed {len(operations)} video file(s).")
        return 0
    except Exception as exc:
        print(f"movecourse: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
