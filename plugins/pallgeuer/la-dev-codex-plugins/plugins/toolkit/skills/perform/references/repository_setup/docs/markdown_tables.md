# Markdown table formatting

`la-dev-codex-plugins` includes a dependency-free library, command, and published pre-commit hooks for canonical Markdown pipe tables. GitHub Flavored Markdown is the rendering baseline, while the source layout follows PyCharm's readable fully bordered and aligned presentation. The formatter is deliberately table-specific; it does not format headings, links, anchors, or general Markdown structure.

The implementation follows the [GFM table extension](https://github.github.com/gfm/#tables-extension-), the relevant CommonMark block rules, [PyCharm's Markdown table support](https://www.jetbrains.com/help/pycharm/markdown.html#tables), and the portability guidance in markdownlint MD055, MD056, and MD058.

## Canonical style

Canonical tables have leading and trailing pipes, one boundary space in header and body cells, no padding spaces in the delimiter row, and one shared source width per column:

```markdown
| Heading | Other |
|:--------|------:|
| Value   |  Text |
```

Every delimiter cell retains at least three dashes. A short aligned column is enlarged enough for its three dashes and alignment colons, and header/body cells are padded to the same slot width. Left and unaligned columns pad after content, right-aligned columns pad before it, and centered columns split padding with an odd extra space after the content.

Width is deterministic Python `len` over Unicode code points, not terminal display width. Combining marks, variation selectors, zero-width joiners, emoji components, East Asian wide characters, controls, and tabs each count as one code point. Existing content is never Unicode-normalized, and only ASCII spaces are inserted. Consequently, canonical source is stable and idempotent but may not appear visually aligned in every editor or font.

Only ASCII spaces and tabs at cell edges are structural padding. Nonbreaking spaces and every other Unicode character at an edge remain content. Meaningful internal whitespace and escaped content are preserved.

## Recognized input and safe repairs

Multi-column input may omit or inconsistently use outer pipes when unescaped internal pipes make cell ownership unambiguous. One-column tables require both borders. The formatter can safely:

- add and regularize outer borders;
- expand one- or two-dash delimiter cells and add missing trailing delimiter cells;
- add missing trailing empty body cells;
- normalize indentation, alignment, padding, and delimiter widths; and
- insert one safe container-correct blank line around top-level and blockquote tables.

An odd run of backslashes escapes a pipe; an even run leaves it structural. In accordance with GFM, unescaped pipes remain structural inside code spans, links, emphasis, and raw inline HTML. A pipe intended as cell content must be explicitly escaped, including inside backticks.

The parser protects fenced and indented code, all seven CommonMark HTML block classes, and leading YAML or TOML front matter, including unclosed regions. Fence and HTML opening and closing respect explicit blockquote and list-container ownership, including indentation relative to a list continuation; an unclosed block ends when its owning container ends. It supports top-level tables with zero through three spaces of indentation, consistently explicit blockquotes, and list tables beginning at the exact continuation column of an established list item. It does not guess through lazy list continuation, tab-derived nesting, inconsistent container ownership, or a table header on the same physical line as a list marker or ATX heading.

Blank lines are added only where the recognized boundary is safe. Existing blank lines are never removed. List-contained tables and tables following a contiguous possible lazy-list block receive no preceding boundary change. A one-column table followed by a plausible pipe-less row receives no following boundary change. These conservative omissions avoid changing list ownership or evicting a row into a paragraph.

An excess delimiter or body cell is unsafe because repairing it could discard or reassign content. The complete affected table remains byte-for-byte equivalent at the text level, a `malformed` issue is reported, and independently safe tables elsewhere in the document can still be formatted. Invalid delimiter-like prose that does not consist entirely of delimiter cells is ordinary Markdown rather than a malformed candidate.

This package repairs conservative border variations, preserves non-ASCII edge whitespace, enforces three delimiter dashes and equal source slots, rejects ambiguous container indentation, protects HTML/front matter, supports explicit quote/list containers, isolates failures per table, and uses bounded Git discovery plus atomic file replacement.

## Library API

Import the public API from `la_dev_codex_plugins.markdown_tables`:

```python
from la_dev_codex_plugins import markdown_tables

result = markdown_tables.format_markdown_tables(source, path="docs/example.md")
if result.changed:
    print(result.text)
for issue in result.issues:
    print(issue.path, issue.line_number, issue.message)
```

The partial APIs are:

- `parse_markdown_tables(text)`: return all safely parsed tables and raise `MarkdownTableError` when any malformed candidate exists;
- `format_markdown_tables(text, path=None)`: return safe partial formatting plus every unresolved issue;
- `markdown_table_issues(text, path=None)`: expose proposed changes as `format` issues together with unresolved `malformed` issues;
- `format_markdown_tables_file(path, check=False)`: inspect one file and write all safe changes unless checking;
- `select_markdown_paths(paths=(), root=None, include_untracked=False, exclude=(), config_path=None, use_config=True, apply_excludes=True)`: reproduce command-line path selection and return ordered absolute paths; and
- `normalize_markdown_tables(text)` and `normalize_markdown_tables_file(path, check=False)`: strict conveniences that refuse partial output or writes when malformed input remains.

Public result types are `MarkdownTable`, `MarkdownTableRow`, `MarkdownTableChange`, `MarkdownTableIssue`, `MarkdownTableFormatResult`, and `MarkdownTableError`. Line numbers are one-based physical lines; table ranges are inclusive. Rows retain their exact physical source text without the line ending and expose immutable structurally trimmed cells. Tables retain the exact raw substring, shared container prefix, table indentation, rows, and one alignment value (`none`, `left`, `right`, or `center`) per header cell. A `MarkdownTableChange` has `kind`, `message`, `line_number`, `path`, and `boundary_position`; the last field is `before` or `after` for a boundary change and `None` otherwise.

`MarkdownTableFormatResult.text` is the partial normalized text, `changed` records whether it differs from the input, and `has_errors` is exactly whether unresolved issues remain. Direct construction accepts `changed=False` and requires a Boolean. Equality and hashing include this observable state. Text-API paths are converted to `str` without filesystem resolution and propagated to changes and issues.

File APIs open one regular UTF-8 file with no-follow semantics and refuse a final-component symlink in both modes. They preserve a leading UTF-8 BOM, every existing `LF`, `CRLF`, or bare `CR` line ending, final-newline state, content outside explicit replacements, and existing mode bits. Fixes are computed in memory, the original mode is applied after writing the same-directory temporary regular file, and the destination identity is checked again immediately before the completed temporary is installed through atomic `os.replace`. A missing, replaced, symlinked, or otherwise changed destination fails without overwriting the new path. Portable POSIX APIs cannot make the final identity-check-and-rename pair conditional as one operation, so callers must still use a single writer per path. Ownership, timestamps, and extended attributes are not promised.

## Command

Install the base package and run:

```text
la-dev-markdown-tables [--check] [--include-untracked]
                       [--exclude REGEX | --no-exclude]
                       [--config PATH | --no-config]
                       [PATH ...]
la-dev-markdown-tables --version
la-dev-markdown-tables --help
```

### Controlling file selection

The invocation form determines the initial candidates:

| Invocation                                     | Initial candidates                                                                                                                  |
|------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| No `PATH`                                      | Present Git-tracked `.md` and `.markdown` files from the nearest worktree, case-insensitively and in repository-relative path order |
| No `PATH`, with `--include-untracked`          | The preceding files plus untracked, nonignored Markdown files                                                                       |
| Explicit file                                  | Exactly that file, even when untracked, ignored, outside the worktree, or not Markdown-suffixed                                     |
| Explicit directory                             | Present tracked Markdown descendants of that directory, which must be inside the active worktree                                    |
| Explicit directory, with `--include-untracked` | The preceding descendants plus untracked, nonignored Markdown descendants                                                           |
| Pre-commit hook                                | The filenames selected and passed by pre-commit; the command does not perform no-path discovery                                     |

Explicit inputs are expanded in first-occurrence command-line order, each directory expansion is repository-relative-path sorted, and overlapping inputs are processed once. Unless excluded, missing explicit files remain candidates and produce an operational diagnostic during processing. A real directory outside the active worktree is an error, while an ignored file remains available when named explicitly. `--include-untracked` never includes ignored files and has no effect on explicit file arguments.

Git discovery uses bounded, NUL-delimited `git ls-files` output. Explicit files remain usable when Git confirms that the current directory is outside every worktree, but Git launch failures, timeouts, unsafe output, and repository errors stop selection before any file is written. Without `--include-untracked`, Git ignore rules are irrelevant because only tracked files are selected. With the option, standard repository, information-exclude, and global Git ignore rules filter the additional untracked files. Deleted tracked paths are omitted. Final-component symlinks are not followed and fail regular-file or directory validation.

After candidate selection, exclusions apply to every invocation form, including explicit filenames passed by pre-commit. Repeat `--exclude REGEX` to add Python regular expressions. Patterns use `re.search` against repository-relative POSIX paths such as `docs/generated/a.md`; an explicit file outside the active worktree is matched by absolute POSIX path. Excluded paths are silently omitted, and a completely excluded invocation succeeds. Use `--no-exclude` for a one-off invocation that must bypass every configured exclusion.

By default the command loads `.la-dev-markdown-tables.json` from the active Git root when that file exists. The UTF-8 file is strict and versioned:

```json
{
  "version": 1,
  "exclude": [
    "^docs/generated/",
    "^vendor/"
  ]
}
```

Both fields are required and no other fields are accepted. Invalid JSON, schema values, versions, or regular expressions fail before any file is written. Configured exclusions and command-line exclusions are additive. `--config PATH` replaces automatic lookup, `--no-config` disables it, and `--no-exclude` bypasses configuration loading as well as filtering. Contradictory switches are rejected.

Python callers can use `select_markdown_paths()` for the same selection behavior. `paths` accepts one path-like value or an iterable, and `exclude` accepts one regular expression or an iterable. `root` selects the enclosing active worktree, `config_path` replaces automatic lookup, `use_config=False` corresponds to `--no-config`, and `apply_excludes=False` corresponds to `--no-exclude`.

Default mode writes safe changes and prints `Formatted Markdown tables: PATH` for each changed file. Check mode writes nothing and reports proposed changes. Malformed and operational diagnostics use `la-dev-markdown-tables: PATH:LINE: MESSAGE` on stderr; operational errors without a source line omit `:LINE`. Human-readable paths preserve printable Unicode but use backslash escapes for controls, format characters, surrogates, line separators, and literal backslashes so every record remains on one physical line.

Exit statuses are:

- `0`: clean check, or completed fix with no unresolved error;
- `1`: check mode found safe formatting changes and no malformed or operational error; and
- `2`: malformed input or an operational failure, taking precedence over status `1`.

Fix mode can therefore write independently safe changes and still return `2` for a malformed table left untouched in the same file.

## Pre-commit and CI

The repository publishes mutation and verification hooks. Downstream users must replace `vX.Y.Z` with an actual release tag containing the hooks:

```yaml
repos:
  - repo: https://github.com/pallgeuer/la-dev-codex-plugins
    rev: vX.Y.Z
    hooks:
      - id: markdown-tables-fix
```

Use the non-mutating alternative in CI or a manual verification stage:

```yaml
repos:
  - repo: https://github.com/pallgeuer/la-dev-codex-plugins
    rev: vX.Y.Z
    hooks:
      - id: markdown-tables-check
```

The hooks receive selected filenames and install only the dependency-free base package. Pre-commit first chooses candidates according to the hook stage or `pre-commit run` arguments, then applies its `files`, `exclude`, `types`, and `exclude_types` filters. The published hooks use `types: [markdown]`. The resulting filenames enter the command as explicit files, so command no-path and directory discovery do not run; repository configuration and tool-native exclusions still filter them.

There are two common exclusion levels. Pre-commit's path-level `exclude` affects only that hook invocation:

```yaml
      - id: markdown-tables-fix
        exclude: ^docs/vendor/
```

For matching standalone, CI, fix-hook, and check-hook behavior, prefer `.la-dev-markdown-tables.json`. Alternatively, pass tool-native patterns through hook arguments:

```yaml
      - id: markdown-tables-check
        args: [--exclude, ^docs/vendor/]
```

Version 1 has no per-table or in-document opt-out directives.

For local manual verification, run `la-dev-markdown-tables --check`. In CI, use the same command or the check hook so the job cannot mutate its checkout.
