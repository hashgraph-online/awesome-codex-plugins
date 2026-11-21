"""Stable Markdown catalogues for effective Perform actions."""

import contextlib
import os
import pathlib
import stat
import unicodedata
import uuid

from . import catalog as catalog_module
from .diagnostics import PerformRequestError

CATALOGUE_MARKER = "<!-- toolkit-perform-action-catalogue:v1 -->"
DEFAULT_CATALOGUE_PARTS = (".codex", "toolkit_perform_actions", "action_catalogue.md")
_PORTABLE_SOURCE_ROOTS = {
    "bundled": "<bundled-actions>",
    "repository": "<repository-actions>",
    "system": "<system-actions>",
    "user": "$CODEX_HOME/toolkit_perform_actions",
}


def _ascii_key(value):
    """Return the deterministic sort key for validated ASCII identifiers."""
    return value.encode("ascii")


def _escape_markdown_text(value):
    """Escape configured display text inside a Markdown table cell."""
    return value.replace("&", "&amp;").replace("\\", "&#92;").replace("|", "&#124;").replace("<", "&lt;").replace(">", "&gt;").replace("`", "&#96;")


def _escape_path_controls(value):
    """Escape path characters that are ambiguous, invisible, or not UTF-8 encodable."""
    escaped = []
    named = {"\t": "\\t", "\n": "\\n", "\r": "\\r"}
    for character in value:
        codepoint = ord(character)
        category = unicodedata.category(character)
        if character == "\\":
            escaped.append("\\\\")
        elif character in named:
            escaped.append(named[character])
        elif category in ("Cc", "Cf", "Cs", "Zl", "Zp") or (category == "Zs" and character != " "):
            escaped.append("\\u{:04x}".format(codepoint) if codepoint <= 0xFFFF else "\\U{:08x}".format(codepoint))
        else:
            escaped.append(character)
    return "".join(escaped)


def _format_inline_code(value):
    """Format one path with a CommonMark-safe code-span delimiter."""
    value = _escape_path_controls(value)
    longest_run = 0
    current_run = 0
    for character in value:
        if character == "`":
            current_run += 1
            longest_run = max(longest_run, current_run)
        else:
            current_run = 0
    delimiter = "`" * (longest_run + 1)
    if value.startswith((" ", "`")) or value.endswith((" ", "`")):
        value = " {} ".format(value)
    return "{}{}{}".format(delimiter, value, delimiter)


def _format_prompt_vars(prompt_vars):
    """Format one prompt-variable mapping for a table cell."""
    if not prompt_vars:
        return "None"
    return "<br>".join("`{}`: {}".format(name, _escape_markdown_text(prompt_vars[name])) for name in sorted(prompt_vars, key=_ascii_key))


def _format_variant_values(summaries, value_getter, value_formatter):
    """Format shared or language-specific values for one base action."""
    values = [value_getter(summary) for summary in summaries]
    if all(value == values[0] for value in values[1:]):
        return value_formatter(values[0])
    return "<br>".join("`{}`: {}".format(summary.language, value_formatter(value)) for summary, value in zip(summaries, values))


def _render_markdown_table(headers, rows, alignments):
    """Render one source-aligned Markdown table."""
    widths = [len(header) for header in headers]
    for row in rows:
        widths = [max(width, len(value)) for width, value in zip(widths, row)]

    def padded_row(row):
        cells = [value.center(width) if alignment == "center" else value.ljust(width) for value, width, alignment in zip(row, widths, alignments)]
        return "| {} |".format(" | ".join(cells))

    separators = [":{}:".format("-" * width) if alignment == "center" else "-" * (width + 2) for width, alignment in zip(widths, alignments)]
    return [padded_row(headers), "|{}|".format("|".join(separators))] + [padded_row(row) for row in rows]


def _action_rows(summaries):
    """Render the existing action rows for one provenance section."""
    grouped = {}
    for summary in summaries:
        grouped.setdefault(summary.name, []).append(summary)
    rows = []
    for name in sorted(grouped, key=_ascii_key):
        action_summaries = sorted(grouped[name], key=lambda summary: _ascii_key(summary.language))
        languages = ", ".join("`{}`".format(summary.language) for summary in action_summaries)
        descriptions = _format_variant_values(action_summaries, lambda summary: summary.gloss, _escape_markdown_text)
        inputs = _format_variant_values(action_summaries, lambda summary: summary.prompt_vars, _format_prompt_vars)
        rows.append(("`{}`".format(name), languages, descriptions, inputs))
    return rows


def _definition_path(source):
    """Return the displayed filesystem path for one definition source."""
    return str(pathlib.Path(source.directory) / source.filename)


def _repository_relative_path(path, repository_root):
    """Return a stable dot-relative path when a file is inside the repository."""
    if repository_root is None:
        return None
    path = os.path.abspath(path)  # noqa: PTH100 - Compare lexical displayed paths without resolving symlinks.
    repository_root = os.path.abspath(repository_root)  # noqa: PTH100 - Compare lexical displayed paths without resolving symlinks.
    try:
        contained = os.path.commonpath((repository_root, path)) == repository_root
    except ValueError:
        contained = False
    if not contained:
        return None
    return "./{}".format(os.path.relpath(path, repository_root))


def _portable_source_path(source, repository_root):
    """Return one stable semantic path for a defining JSON file."""
    definition_path = _definition_path(source)
    repository_relative = _repository_relative_path(definition_path, repository_root)
    if repository_relative is not None:
        return repository_relative
    root = _PORTABLE_SOURCE_ROOTS.get(source.kind, "<source-{}>".format(source.source_order + 1))
    return str(pathlib.PurePath(root) / source.filename)


def _portable_source_paths(sources, repository_root):
    """Return unique portable paths with source-ordinal collision fallbacks."""
    keys_by_semantic_root = {}
    for key, source in sources.items():
        if _repository_relative_path(_definition_path(source), repository_root) is None and source.kind in _PORTABLE_SOURCE_ROOTS:
            keys_by_semantic_root.setdefault(_PORTABLE_SOURCE_ROOTS[source.kind], []).append(key)
    ordinal_keys = set()
    for keys in keys_by_semantic_root.values():
        if len({sources[key].directory for key in keys}) > 1:
            ordinal_keys.update(keys)
    paths = {
        key: str(pathlib.PurePath("<source-{}>".format(source.source_order + 1)) / source.filename) if key in ordinal_keys else _portable_source_path(source, repository_root)
        for key, source in sources.items()
    }
    keys_by_path = {}
    for key, path in paths.items():
        keys_by_path.setdefault(path, []).append(key)
    for colliding_keys in keys_by_path.values():
        if len(colliding_keys) > 1:
            for key in colliding_keys:
                source = sources[key]
                paths[key] = str(pathlib.PurePath("<source-{}>".format(source.source_order + 1)) / source.filename)
    return paths


def _shortest_unique_suffixes(paths):
    """Return the shortest path-component suffix unique to every path."""
    path_parts = {path: pathlib.PurePath(path).parts for path in paths}
    lengths = dict.fromkeys(path_parts, 1)
    while True:
        suffixes = {path: path if lengths[path] >= len(parts) else str(pathlib.PurePath(*parts[-lengths[path] :])) for path, parts in path_parts.items()}
        paths_by_suffix = {}
        for path, suffix in suffixes.items():
            paths_by_suffix.setdefault(suffix, []).append(path)
        collisions = [colliding_paths for colliding_paths in paths_by_suffix.values() if len(colliding_paths) > 1]
        if not collisions:
            return suffixes
        for colliding_paths in collisions:
            for path in colliding_paths:
                if lengths[path] < len(path_parts[path]):
                    lengths[path] += 1


def _append_action_section(lines, heading, summaries, definition_path=None):
    """Append one heading, optional provenance, and existing action table."""
    lines.extend(("## {}".format(heading), ""))
    if definition_path is not None:
        lines.extend(("**JSON source:** {}".format(_format_inline_code(definition_path)), ""))
    lines.extend(_render_markdown_table(("Action", "Languages", "Description", "Required inputs"), _action_rows(summaries), ("left", "center", "left", "left")))
    lines.append("")


def render_action_catalogue(entries, repository_root=None):
    """Render catalogue entries as stable source-grouped Markdown."""
    entries = tuple(entries)
    if any(not isinstance(entry, catalog_module.ActionCatalogueEntry) for entry in entries):
        raise TypeError("entries must contain only ActionCatalogueEntry values")
    if repository_root is not None and not isinstance(repository_root, str):
        raise TypeError("repository_root must be a string or None")
    built_in = []
    by_source = {}
    sources = {}
    for entry in entries:
        source = entry.definition_source
        if source is None:
            built_in.append(entry)
            continue
        source_key = (source.source_order, source.directory, source.filename)
        by_source.setdefault(source_key, []).append(entry)
        sources[source_key] = source

    lines = [
        CATALOGUE_MARKER,
        "# Perform Action Catalogue",
        "",
        "This file lists the effective Perform actions available in the current Perform context.",
        "",
        "Regenerate it with `$toolkit:perform update-action-catalogue` or `codex-perform catalogue`. Use a bare action name when its language is clear, or an exact `ACTION[LANGUAGE]` selector. The `agnostic` language is language-independent.",
        "",
    ]
    if built_in:
        _append_action_section(lines, "Built-in", built_in)
    source_paths = _portable_source_paths(sources, repository_root)
    suffixes = _shortest_unique_suffixes(source_paths.values())
    ordered_sources = sorted(by_source, key=lambda key: (key[0], key[2].encode("utf-8", errors="surrogateescape")))
    for source_key in ordered_sources:
        path = source_paths[source_key]
        _append_action_section(lines, _format_inline_code(suffixes[path]), by_source[source_key], definition_path=path)
    return "\n".join(lines), len({entry.name for entry in entries}), len(entries)


def _repository_root(catalog):
    """Return the discovered repository root, if any."""
    discovery = getattr(catalog, "discovery", None)
    return None if discovery is None else discovery.repository_root


def resolve_action_catalogue_path(catalog, output=None):
    """Resolve one default or explicit catalogue target and path policy."""
    repository_root = _repository_root(catalog)
    if output is None:
        if repository_root is None:
            raise PerformRequestError("repository_not_found", "The default action catalogue path requires a discovered repository root.")
        return pathlib.Path(repository_root).joinpath(*DEFAULT_CATALOGUE_PARTS), True
    if not isinstance(output, str) or not output or "\x00" in output:
        raise PerformRequestError("invalid_output", "The action catalogue output must be a nonempty path without NUL characters.")
    expanded = pathlib.Path(output).expanduser()
    if expanded.is_absolute():
        return pathlib.Path(os.path.abspath(str(expanded))), False  # noqa: PTH100 - Preserve the final path component for symlink rejection.
    if repository_root is None:
        raise PerformRequestError("repository_not_found", "A relative action catalogue path requires a discovered repository root.")
    return pathlib.Path(os.path.abspath(str(pathlib.Path(repository_root) / expanded))), False  # noqa: PTH100 - Preserve the final path component for symlink rejection.


def _prepare_parent(path, create_parent):
    """Create the default parent or validate one custom parent."""
    parent = path.parent
    if create_parent:
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise PerformRequestError("runtime_error", "Could not create the default action catalogue directory {}: {}.".format(parent, exc)) from exc
    if not parent.is_dir():
        raise PerformRequestError("output_parent_missing", "The action catalogue parent directory does not exist: {}.".format(parent))


def _existing_bytes(path):
    """Read an existing safe target or return None when it is absent."""
    if path.is_symlink():
        raise PerformRequestError("unsafe_output", "Refusing to replace a symbolic-link action catalogue target: {}.".format(path))
    if not path.exists():
        return None
    if not path.is_file():
        raise PerformRequestError("unsafe_output", "The action catalogue target is not a regular file: {}.".format(path))
    try:
        return path.read_bytes()
    except OSError as exc:
        raise PerformRequestError("runtime_error", "Could not read the existing action catalogue {}: {}.".format(path, exc)) from exc


def _has_catalogue_marker(content):
    """Return whether nonempty bytes carry the exact generated marker."""
    return bool(content) and content.splitlines()[0] == CATALOGUE_MARKER.encode("ascii")


def _atomic_write(path, content, previous_mode=None):
    """Atomically replace one catalogue with complete UTF-8 bytes."""
    descriptor = None
    temporary_path = None
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        while True:
            temporary_path = path.parent / ".action_catalogue.{}.tmp".format(uuid.uuid4().hex)
            try:
                descriptor = os.open(str(temporary_path), flags, 0o666)
                break
            except FileExistsError:
                continue
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if previous_mode is not None:
            temporary_path.chmod(previous_mode)
        temporary_path.replace(path)
        temporary_path = None
    except OSError as exc:
        raise PerformRequestError("runtime_error", "Could not write the action catalogue {}: {}.".format(path, exc)) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_path is not None:
            with contextlib.suppress(OSError):
                temporary_path.unlink()


def write_action_catalogue(catalog, output=None):
    """Render and safely update one stable action catalogue."""
    if not isinstance(catalog, catalog_module.ActionCatalog):
        raise TypeError("catalog must be an ActionCatalog")
    entries = catalog.catalogue_entries()
    rendered, action_count, variant_count = render_action_catalogue(entries, repository_root=_repository_root(catalog))
    path, create_parent = resolve_action_catalogue_path(catalog, output=output)
    _prepare_parent(path, create_parent)
    content = rendered.encode("utf-8")
    existing = _existing_bytes(path)
    if existing == content:
        changed = False
    else:
        if existing and not _has_catalogue_marker(existing):
            raise PerformRequestError("unsafe_output", "Refusing to replace a nonempty file without the Perform action catalogue marker: {}.".format(path))
        previous_mode = None if existing is None else stat.S_IMODE(path.stat().st_mode)
        _atomic_write(path, content, previous_mode=previous_mode)
        changed = True
    return {
        "path": str(path),
        "changed": changed,
        "action_count": action_count,
        "variant_count": variant_count,
    }


__all__ = (
    "CATALOGUE_MARKER",
    "DEFAULT_CATALOGUE_PARTS",
    "render_action_catalogue",
    "resolve_action_catalogue_path",
    "write_action_catalogue",
)
