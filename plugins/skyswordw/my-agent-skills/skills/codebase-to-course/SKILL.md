---
name: codebase-to-course
description: Turn the current workspace or an explicit repository into a multi-file, offline-readable course that helps non-technical learners understand how the code works through short real excerpts, visual structure, and purposeful interaction.
---

# Codebase to Course

Use this skill when the user wants a codebase explained as a browser-openable course instead of a plain text walkthrough. The default deliverable is a multi-file course directory, not a single-file HTML page.

## Main Responsibility

- Convert the current workspace or a caller-provided repository path into a course that teaches what the system does, how its important parts connect, and where the learner should look next.
- Keep the result directly openable in a browser and readable offline.
- Keep runtime assets local and clean-room. Do not depend on CDN-hosted scripts, fonts, or styles.

## Public Commands

Use these public entry points:

```bash
bash .codex/skills/codebase-to-course/scripts/init-course.sh --source <repo-or-dir> --out <course-dir> [--title <title>] [--accent <vermillion|coral|teal|amber|forest>]
bash .codex/skills/codebase-to-course/scripts/build-course.sh --course-dir <course-dir>
```

In `init-course.sh`, `<repo-or-dir>` means a local checkout or local directory path.

Command resolution rules:

- If the user refers to the current workspace without naming a path, resolve `--source` to the current workspace root.
- If the user supplies a local repository checkout or local directory path, pass that explicit location as `--source`.
- Do not pass remote repository URLs, hosted repo references, or git transport strings to `--source`.
- If the user provides a remote repo reference, clone it locally first or ask the user for a local path before running `init-course.sh`.
- If the caller does not choose an output directory, derive one with this convention and pass it as `--out`:
  `<workspace>/.codex-artifacts/codebase-to-course/<slug>/`
- Use a stable lowercase slug derived from the chosen title when present, otherwise from the source directory name.
- `--accent` may be only `vermillion`, `coral`, `teal`, `amber`, or `forest`.

## Output Shape

Treat the course directory as the working artifact. It should contain:

- `modules/`
- `briefs/`
- `_base.html`
- `_footer.html`
- `styles.css`
- `main.js`

After a build, the same directory should also contain:

- `index.html`

`index.html` is the assembled entry page produced by `build-course.sh`. Report the final path after building, but do not promise that a browser window will open automatically.

## Module Authoring Contract

- Author lesson modules as `modules/*.html`.
- Each module file must contain exactly one root `<section id="...">` for the assembled course body.
- Keep each module id unique within the course.
- The navigation title comes from the root section's `data-title` when present; otherwise the builder falls back to the first heading in the module.
- Do not add extra `<link>` tags or extra `<script>` includes inside modules. The assembled course should rely on the shipped local runtime files `styles.css` and `main.js`.
- If a teaching moment needs more structure, add semantic HTML inside the root section and keep it compatible with the shipped local runtime instead of introducing more asset includes.

## Workflow

1. Resolve the source codebase, title, accent, and output directory.
2. Inspect the repository structure and identify the learner-facing story:
   - Treat the codebase as simple when one main execution path can carry most of the explanation.
   - Treat the codebase as complex when it has multiple subsystems, runtimes, or distinct user journeys that need separate framing.
3. Run `init-course.sh` with the resolved `--source` and `--out` values.
4. Plan the course structure:
   - Simple codebases: write modules sequentially so each module depends on the context established by the previous one.
   - Complex codebases: write module briefs in `briefs/` first, then write modules from those briefs. Module writing may be parallel only when the host can support parallel work cleanly.
5. Teach with evidence, not file dumps:
   - Use short real excerpts only when the exact code shape matters to the lesson.
   - Prefer a few lines, a compact function fragment, a type definition, or a tightly scoped config snippet.
   - Never dump whole files, long generated blocks, or large copied sections.
   - Do not claim that the skill provides automatic redaction. If source text is not safe to quote, paraphrase it or skip it.
6. Keep the course grounded in practical understanding:
   - Explain visible behavior before internal detail.
   - Tie diagrams, callouts, and code excerpts back to concrete user or operator outcomes.
   - Use file paths and component names as landmarks, not as the lesson itself.
7. Rebuild with `build-course.sh` whenever authored content changes materially.

## Interaction Palette

The runtime can support a broad set of teaching patterns, but this is not a blanket guarantee that every authored module should use every interaction or that every desired behavior already has a dedicated widget. Prefer shipped runtime widgets when they are available in the installed skill bundle. If a needed widget is not available, fall back to static or minimal local HTML/CSS/JS patterns that remain offline-readable and do not add extra asset includes.

Choose only the pieces that clarify the lesson:

- translation blocks
- quizzes
- drag/drop
- group chat
- data flow
- architecture diagrams
- layer toggles
- bug challenges
- scenario quizzes
- callouts
- pattern cards
- flow diagrams
- permission/config badges
- glossary tooltips
- visual file trees
- icon-label rows
- numbered step cards

Read `references/interactive-elements.md` when you need the current shipped widget contracts.

## Teaching Guardrails

- Write for non-technical learners first. Define unfamiliar terms before relying on them.
- Prefer explaining why a file matters over listing many files.
- Keep examples sanitized and public-safe.
- If the codebase includes sensitive names, secrets, or private identifiers, do not quote them. Replace them with a short explanation of their role.
- Favor original diagrams, phrasing, and structure. Do not mirror a source repo's README, docs site, or marketing language.

## References

- Read `references/content-philosophy.md` for the teaching stance and module-writing principles.
- Read `references/module-brief-template.md` before planning complex codebases.
- Read `references/gotchas.md` before building or revising a course.
