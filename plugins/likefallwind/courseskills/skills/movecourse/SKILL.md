---
name: movecourse
description: Use when publishing AI-generated course lesson mp4 files into the aistudy101 website course-assets tree, especially from lesson*/ directories into static/course-assets/<course-id>/lesson*/video.
---

# Movecourse

## Overview

Move or publish generated lesson videos from a course-generation workspace into the aistudy101 website assets tree. Resolve and validate the requested course id against the website course ID registry first, then `course-sources.yaml`, map `lessonN/*.mp4` to the matching website lesson folder, and use English filenames.

Default behavior is a safe publish copy. Delete the generated originals only when the user explicitly asks for a true move.

When this workflow adjusts or registers course metadata, default the course status to `已发布` after the course is ready, unless the user gives a different status or special instruction.

## When to Use

Use this skill when:
- The user says to move, publish, upload, install, or sync AI-generated course videos to aistudy101.
- The current directory looks like `.../course-outline/.../<course>/lesson1`, `lesson2`, etc.
- Each lesson directory contains one generated `.mp4` that should land under `/home/likefallwind/code/aistudy101-website/static/course-assets/<course-id>/lessonN/video/`.

Do not use this skill for slide rendering, narration generation, or video assembly. Use `codex2course` or `pdf2video` first.

## Required Inputs

| Input | Default / source |
|---|---|
| Source course directory | Current working directory, unless user gives a path |
| Course id | Ask the user if not provided; examples: `ai-enlightenment`, `python-intro` |
| Destination root | `/home/likefallwind/code/aistudy101-website/static/course-assets` |
| Course registry | `/home/likefallwind/code/aistudy101-website/course-sources.yaml` |
| Course ID registry | `/home/likefallwind/code/aistudy101-website/docs/course-id-registry.md` |
| Website repo root | `/home/likefallwind/code/aistudy101-website` |
| Optional local asset config | `/home/likefallwind/code/aistudy101-website/course-assets.local.yaml` |

If the course id is not listed in `course-sources.yaml`, distinguish these cases:

- If the user only gave a Chinese title or curriculum placement, first look it up in `docs/course-id-registry.md`. Reuse that ID when present, even if the course is still marked `预留`.
- If the title is absent from the ID registry, inspect the source directory name, `README.md`, git remote, and `ai-study-101-curriculum-system-v0.3.md`. Choose a conservative lowercase kebab-case id only when it is obvious, then update `docs/course-id-registry.md`; otherwise ask.
- If the user expects this to become a real website course, register it in `course-sources.yaml` before copying videos. Prefer the source repo remote URL when available, and include fallback metadata matching the curriculum placement.
- If the source videos live only on this machine, add or update `course-assets.local.yaml` so `npm run sync` can republish them from the local source directory.
- Use `--allow-unknown-course` only when the user explicitly wants raw static assets without registering the course.

## Workflow

1. Inspect the source directory for direct child folders named `lessonN`.
2. In each lesson folder, require exactly one direct `.mp4`; report missing or duplicate videos before copying anything.
3. Resolve the course id from `docs/course-id-registry.md` when the user gave a Chinese title, then validate it against the ID registry or `course-sources.yaml`.
4. Create missing destination folders: `<dest-root>/<course-id>/lessonN/video/`.
5. Write English filenames. Default to the existing website convention: `lessonN-intro.mp4`.
6. Dry-run first, then execute the copy or true move.
7. Verify every destination file exists and has a non-zero size. Print a source-to-destination manifest.
8. From the website repo, run `npm run sync` so `src/data/course-content.json`, `src/data/courses.json`, and `src/data/curriculum-map.json` reference the published videos.
9. If course metadata was changed, set the course status to `已发布` by default. Follow the user's explicit status instead if they provide one, such as `待审核` or `AI初稿`.
10. Run `npm run build` when the change should be ready for review or deployment.

## New Course Registration

When the user says a source course "corresponds to" a curriculum item, treat the task as both course registration and video publishing.

1. Check whether the curriculum item already exists as a clickable course in `src/data/curriculum-map.json`.
2. If it is still a non-clickable placeholder, add a `course-sources.yaml` entry with:
   - `id`: the stable ID from `docs/course-id-registry.md`; add a registry row first if the curriculum item is new.
   - `type: gitee`
   - `repo`: the source repo URL from `git -C <source> remote -v` when present.
   - `fallback`: title, stage, education phase, track, status, hours, and theme lines. Use `status: 已发布` by default after the course has been adjusted, unless the user explicitly specifies another status.
3. If the source repo cannot be cloned due to Gitee credentials, keep the registry entry and rely on `course-assets.local.yaml` for the local source fallback.
4. After `npm run sync`, confirm the course appears in:
   - `src/data/courses.json`
   - `src/data/course-content.json`
   - `src/data/curriculum-map.json`

For local-only videos, add:

```yaml
courses:
  python-advanced:
    source_dir: /home/likefallwind/code/course-outline/stage3/01-python-advanced
    video_globs:
      - "lesson*/*.mp4"
    video_publish_name: "{lesson_id}-intro{suffix}"
```

`course-assets.local.yaml` is git-ignored; mention it in the final status, but do not expect it to show up in `git diff`.

## Helper Script

Prefer the bundled script because it preflights all lessons before writing:

```bash
python ~/.agents/skills/movecourse/scripts/movecourse.py --course ai-enlightenment --dry-run
python ~/.agents/skills/movecourse/scripts/movecourse.py --course-title "Python 编程进阶" --dry-run
python ~/.agents/skills/movecourse/scripts/movecourse.py --course ai-enlightenment
```

Useful options:

| Option | Use |
|---|---|
| `--source PATH` | Source course directory; defaults to `pwd` |
| `--course ID` | Required course id under `course-assets` |
| `--course-title TITLE` | Resolve a Chinese curriculum title through `docs/course-id-registry.md` |
| `--dry-run` | Print planned operations without writing |
| `--overwrite` | Replace existing destination mp4 files |
| `--move` | Delete source mp4 after verified copy; use only when user explicitly asked |
| `--allow-unknown-course` | Continue when course id is absent from both `course-sources.yaml` and the ID registry |
| `--filename-template '{lesson}-intro.mp4'` | English output pattern |

After copying, verify the website data:

```bash
npm run sync
rg -n "python-advanced|Python 编程进阶" src/data/courses.json src/data/course-content.json src/data/curriculum-map.json
npm run build
```

If `npm run sync` reports a Gitee clone/auth failure but then says it used `course-assets.local.yaml`, that is acceptable for local publishing. The final sync summary should have `error: 0`.

## Manual Fallback

If the script is unavailable, validate course id and mp4 counts first, then:

```bash
COURSE_ID="ai-enlightenment"
SRC="$PWD"
DST="/home/likefallwind/code/aistudy101-website/static/course-assets/$COURSE_ID"

for lesson_dir in "$SRC"/lesson*; do
  lesson="$(basename "$lesson_dir")"
  video_dir="$DST/$lesson/video"
  mkdir -p "$video_dir"
  cp -p "$lesson_dir"/*.mp4 "$video_dir/$lesson-intro.mp4"
done
```

## Common Mistakes

- **Using the Chinese source filename in the website tree.** Rename to English; default `lessonN-intro.mp4` is acceptable and matches existing courses.
- **Skipping the course ID registry.** `ai-enlightenment` is a course id; the Chinese title `AI 启蒙体验` should be resolved through `docs/course-id-registry.md`, not guessed from a folder name.
- **Publishing videos without registering a new course.** Static files can exist while the course map remains non-clickable. Add `course-sources.yaml` and run `npm run sync`.
- **Forgetting the local asset config.** Direct copies work once, but future syncs need `course-assets.local.yaml` to know where local videos come from.
- **Treating Gitee clone failures as fatal when a local source exists.** If sync falls back to `course-assets.local.yaml` and ends with `error: 0`, report the warning but continue verification.
- **Copying after the first valid lesson without preflight.** Validate every lesson first to avoid a half-published course.
- **Overwriting existing videos silently.** Use dry-run and require `--overwrite` when destination files already exist.
- **Deleting generated originals by default.** Treat "move to server position" as a publish copy unless the user explicitly asks to remove the source files.
