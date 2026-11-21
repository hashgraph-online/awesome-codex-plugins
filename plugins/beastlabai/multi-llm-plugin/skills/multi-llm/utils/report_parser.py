"""Parse report.md to extract user skip decisions and descriptions."""

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .judge_vocab import JUDGE_DECIDE, upgrade_legacy
from . import report_markdown as rm
from .scope_report import strip_selection_scope_fields
from .state_manager import (
    stamp_stable_ids,
    load_groups_payload,
    get_format_version,
    generate_suggestion_id,
)
from .selection_migration import _migrate_v1_html_selections

# Regex for extracting display hashes from bracket notation in report headers.
# Matches 8-16 char lowercase hex strings inside square brackets.
_HASH_RE = re.compile(r'\[([0-9a-f]{8,16})\]')

#: A code-review issue header, anchored at column 0.
_ISSUE_HEADER_RE = rm.ISSUE_HEADER_RE

#: An item's override boxes in precedence order: invalid > valid >
#: judge_decide (an explicit valid/invalid is a firmer signal than "you
#: decide"), so "invalid" wins when both are ticked (safety-first).
_ITEM_OVERRIDES = (
    (rm.MARK_INVALID, "invalid"),
    (rm.MARK_VALID, "valid"),
    (rm.LET_AGENT_DECIDE, JUDGE_DECIDE),
)

#: A consolidated group's: invalid > needs-human-decision > valid >
#: judge_decide.
_CONSOLIDATED_OVERRIDES = (
    (rm.MARK_INVALID, "invalid"),
    (rm.NEEDS_HUMAN, "needs-human-decision"),
    (rm.MARK_VALID, "valid"),
    (rm.LET_AGENT_DECIDE, JUDGE_DECIDE),
)


def _warn_unhashed(refused: List[str], header: str, report_path: str) -> None:
    """Say which unhashed headers a mixed report's parse ignored
    (``report_markdown.hashed_headers``)."""
    if refused:
        names = ", ".join(sorted(set(refused)))
        print(
            f"WARNING: {report_path} has unhashed {header} headers ({names}) "
            f"among hashed ones; the report writer never mixes the two, so "
            f"their checkboxes and text are ignored.",
            file=sys.stderr,
        )


def _strip_scope_fields(data, source: str):
    """*data* without scope/policy-like keys (``scope_report.strip_selection_scope_fields``)."""
    return strip_selection_scope_fields(data, source)


def _issue_headers(content: str) -> List[re.Match]:
    """The `### N.` lines that really open an issue block.

    An issue's *description* is model output rendered verbatim, so it can hold
    its own `### 2. …` line — and, under it, its own `- [x] Skip`. Read as a
    header that forges a tick on an issue the user never touched (measured: a
    description containing `### 2.` plus a ticked Skip box skipped two groups
    off one report). `code_review_orchestrator._format_issue` only ever writes a
    header at column 0 after the blank line that follows the previous issue's
    `---` rule, so that is the only shape accepted here; anything indented, or
    sitting mid-paragraph, is description text.
    """
    headers = []
    for match in _ISSUE_HEADER_RE.finditer(content):
        before = content[:match.start()]
        if not before:
            headers.append(match)  # first thing in the file
            continue
        # `^` under MULTILINE means `before` ends with the newline that put this
        # header at column 0; drop it to read the line above.
        previous = before[:-1].rsplit("\n", 1)[-1]
        # Blank (the renderer's own spacing) or the `---` rule that closes the
        # previous issue.
        if previous.strip() in ("", "---"):
            headers.append(match)
    return headers


def _load_stamped_groups_for_legacy(report_path: str) -> Optional[List[Dict]]:
    """Load grouped.json from the same directory as report_path and stamp stable IDs.

    Used as a legacy fallback when report.md lacks bracket-notation hashes.
    Returns stamped groups list, or None if grouped.json is unavailable.
    """

    report_dir = Path(report_path).parent
    grouped_path = report_dir / "grouped.json"
    if not grouped_path.exists():
        return None

    try:
        raw = json.loads(grouped_path.read_text(encoding='utf-8'))
        groups = load_groups_payload(raw)
        stamp_stable_ids(groups)
        return groups
    except (json.JSONDecodeError, ValueError, OSError) as e:
        print(
            f"WARNING: Failed to load grouped.json for legacy fallback: {e}",
            file=sys.stderr,
        )
        return None


def _build_positional_maps(
    groups: List[Dict],
) -> Tuple[Dict[int, str], Dict[str, str]]:
    """Build positional-to-hash maps from stamped groups.

    Returns:
        Tuple of:
        - group_index_to_hash: {1-based index -> group_hash}
        - suggestion_id_to_hash: {"G{N}S{M}" -> suggestion_hash}
    """
    group_idx_to_hash: Dict[int, str] = {}
    sugg_id_to_hash: Dict[str, str] = {}

    for g_idx, group in enumerate(groups):
        g_num = g_idx + 1
        ghash = group.get("group_hash", "")
        if ghash:
            group_idx_to_hash[g_num] = ghash

        suggestions = group.get("suggestions", group.get("issues", []))
        for s_idx, sugg in enumerate(suggestions):
            s_num = s_idx + 1
            shash = sugg.get("suggestion_hash", "")
            if shash:
                sugg_id_to_hash[f"G{g_num}S{s_num}"] = shash

    return group_idx_to_hash, sugg_id_to_hash


def parse_skipped_suggestions(report_path: str) -> Set[str]:
    """
    Parse report.md and return IDs of suggestions marked to skip.

    Looks for pattern:
        ### S001: Title
        - [x/etc] Skip

    Returns:
        Set of suggestion IDs marked with [x/etc] Skip (e.g., {"S001", "S003"})
    """
    if not Path(report_path).exists():
        return set()

    content = Path(report_path).read_text(encoding='utf-8')
    skipped = set()

    # The box on the line immediately under the header; any non-blank mark
    # inside the brackets counts as ticked (case insensitive).
    for match in rm.FLAT_SUGGESTION_HEADER_RE.finditer(content):
        line = rm.line_after(content, match.end())
        if line is not None and rm.is_checked(line, rm.SKIP):
            skipped.add(match.group(1))

    return skipped


def parse_skipped_issues(report_path: str) -> Set[int]:
    """
    Parse code review report.md and return indices of issues marked to skip.

    Code review reports use numeric indices like:
        ### 1. Title
        - [x/etc] Skip

    Only a header `_issue_headers` accepts opens an issue, so a `### N.` line
    inside a rendered description cannot carry a tick of its own.

    Returns:
        Set of issue indices marked with [x/etc] Skip (e.g., {1, 3})
    """
    if not Path(report_path).exists():
        return set()

    content = Path(report_path).read_text(encoding='utf-8')
    skipped = set()

    # The box on the line immediately under the header. Any non-blank content
    # inside the brackets counts as ticked.
    for match in _issue_headers(content):
        line = rm.line_after(content, match.end())
        if line is not None and rm.is_checked(line, rm.SKIP):
            skipped.add(int(match.group(1)))

    return skipped


def parse_skipped_groups(report_path: str) -> Set[str]:
    """
    Parse report.md and return group hashes of groups marked to skip.

    Supports two header formats:
        v2: ## G1 [a1b2c3d4]: Theme  (hash extracted from brackets)
        v1: ## G1: Theme              (legacy -- mapped via grouped.json)

    An unhashed header in a report that also has hashed ones is ignored
    (``report_markdown.hashed_headers``).

    Returns:
        Set of group hash strings marked with [x/etc] Skip this group
    """
    if not Path(report_path).exists():
        return set()

    content = Path(report_path).read_text(encoding='utf-8')
    skipped_hashes: Set[str] = set()
    skipped_indices: Set[int] = set()
    refused: List[str] = []
    found_bracket_notation = False

    # The box is the first non-blank line under the header.
    for section in rm.plan_sections(content):
        if section.kind != rm.GROUP:
            continue
        line = section.first_line()
        if line is None or not rm.is_checked(line, rm.SKIP_GROUP):
            continue
        match = section.match
        hash_val = match.group(2)
        if not section.trusted:
            refused.append(f"G{match.group(1)}")
        elif hash_val:
            found_bracket_notation = True
            skipped_hashes.add(hash_val)
        else:
            skipped_indices.add(int(match.group(1)))
    _warn_unhashed(refused, "`## G{N}:`", report_path)

    # Map any positional indices to hashes via grouped.json
    if skipped_indices:
        groups = _load_stamped_groups_for_legacy(report_path)
        if groups is not None:
            group_idx_to_hash, _ = _build_positional_maps(groups)
            for idx in skipped_indices:
                ghash = group_idx_to_hash.get(idx)
                if ghash:
                    skipped_hashes.add(ghash)
                else:
                    print(
                        f"WARNING: Skipped group index G{idx} could not be "
                        f"mapped to a hash (out of range). Ignoring.",
                        file=sys.stderr,
                    )
        else:
            if not found_bracket_notation:
                print(
                    "WARNING: Report uses legacy G{N} format but grouped.json "
                    "not found for hash migration. Skipped groups may not apply.",
                    file=sys.stderr,
                )

    return skipped_hashes


def parse_skipped_group_suggestions(report_path: str) -> Set[str]:
    """
    Parse report.md and return hashes of individual suggestions marked to skip.

    Supports two header formats:
        v2: ### G1S2 [e5f6a7b8]: Title  (hash extracted from brackets)
        v1: ### G1S2: Title              (legacy -- mapped via grouped.json)

    Returns:
        Set of suggestion hash strings marked with [x/etc] Skip
    """
    if not Path(report_path).exists():
        return set()

    content = Path(report_path).read_text(encoding='utf-8')
    skipped_hashes: Set[str] = set()
    skipped_positional: Set[str] = set()
    refused: List[str] = []
    found_bracket_notation = False

    # The Skip box (not "Skip this group") on the line immediately under the
    # header.
    for section in rm.plan_sections(content):
        if section.kind != rm.SUGGESTION:
            continue
        line = section.line_under()
        if line is None or not rm.is_checked(line, rm.SKIP):
            continue
        match = section.match
        hash_val = match.group(2)
        if not section.trusted:
            refused.append(match.group(1).upper())
        elif hash_val:
            found_bracket_notation = True
            skipped_hashes.add(hash_val)
        else:
            skipped_positional.add(match.group(1).upper())
    _warn_unhashed(refused, "`### G{N}S{M}:`", report_path)

    # Map any positional IDs to hashes via grouped.json
    if skipped_positional:
        groups = _load_stamped_groups_for_legacy(report_path)
        if groups is not None:
            _, sugg_id_to_hash = _build_positional_maps(groups)
            for sid in skipped_positional:
                shash = sugg_id_to_hash.get(sid)
                if shash:
                    skipped_hashes.add(shash)
                else:
                    print(
                        f"WARNING: Skipped suggestion {sid} could not be "
                        f"mapped to a hash. Ignoring.",
                        file=sys.stderr,
                    )
        else:
            if not found_bracket_notation:
                print(
                    "WARNING: Report uses legacy G{N}S{M} format but "
                    "grouped.json not found for hash migration. "
                    "Skipped suggestions may not apply.",
                    file=sys.stderr,
                )

    return skipped_hashes


def _drop_validation_reason(text: str) -> str:
    """*text* less every ``> **Validation Reason:**`` blockquote: the line
    that opens it and the ``>`` lines that continue it.

    review-code's report writes an issue's validation reason between its
    metadata line and its description, every line of it quoted
    (``code_review_orchestrator._format_issue``), so the reason, however many
    paragraphs it has, is never read as part of the description.
    """
    result_lines = []
    in_validation_blockquote = False
    for line in text.split('\n'):
        stripped = line.strip()
        if stripped.startswith('> **Validation Reason:**'):
            in_validation_blockquote = True
            continue
        if in_validation_blockquote:
            if stripped.startswith('>'):
                continue
            in_validation_blockquote = False
        result_lines.append(line)
    return '\n'.join(result_lines)


def normalize_description(desc: str) -> str:
    """Normalize description for comparison (strip whitespace, remove validation blockquotes).

    - Strip leading/trailing whitespace
    - Collapse multiple spaces to single space
    - Normalize CRLF to LF
    - Remove validation reason blockquotes that start with `> **Validation Reason:**`
      (including continuation lines starting with `>`)
    - Preserve other blockquotes and markdown formatting
    """
    if not desc:
        return ""

    # Normalize CRLF to LF
    text = _drop_validation_reason(desc.replace('\r\n', '\n'))

    # Collapse multiple spaces to single space (but preserve newlines)
    text = re.sub(r' +', ' ', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def parse_suggestion_descriptions(report_path: str) -> Dict[str, str]:
    """Extract descriptions from report.md keyed by suggestion hash.

    Supports two header formats:
        v2: ### G1S1 [e5f6a7b8]: Title  (hash extracted from brackets)
        v1: ### G1S1: Title              (legacy -- mapped via grouped.json)

    Extracts the description text that appears AFTER the metadata line
    (``**Validation:**...`` or ``**Importance:**...``) and BEFORE the
    ``---`` separator.

    Returns:
        Dict mapping suggestion hash to description text.
        Empty dict if file not found.
    """
    if not Path(report_path).exists():
        return {}

    content = Path(report_path).read_text(encoding='utf-8')
    descriptions_by_hash: Dict[str, str] = {}
    descriptions_by_positional: Dict[str, str] = {}
    refused: List[str] = []
    found_bracket_notation = False

    # Each suggestion header and everything under it up to the next `---` or
    # `###` line. Header format: ### G1S1 [hash]: Title  OR  ### G1S1: Title
    escaped = rm.has_escaped_text(content)
    matches, trust_unhashed = rm.hashed_headers(content, rm.SUGGESTION_HEADER_RE)
    for match in matches:
        positional_id = match.group(1)
        hash_val = match.group(2)
        block = _description_block(content, match)
        if block is None:
            continue
        description = _description_text(block, escaped)

        if description:
            if hash_val:
                found_bracket_notation = True
                descriptions_by_hash[hash_val] = description
            elif trust_unhashed:
                descriptions_by_positional[positional_id.upper()] = description
            else:
                refused.append(positional_id.upper())
    _warn_unhashed(refused, "`### G{N}S{M}:`", report_path)

    # Map positional IDs to hashes via grouped.json fallback
    if descriptions_by_positional:
        groups = _load_stamped_groups_for_legacy(report_path)
        if groups is not None:
            _, sugg_id_to_hash = _build_positional_maps(groups)
            for sid, desc in descriptions_by_positional.items():
                shash = sugg_id_to_hash.get(sid)
                if shash:
                    # Don't overwrite a hash-based entry
                    if shash not in descriptions_by_hash:
                        descriptions_by_hash[shash] = desc
                else:
                    print(
                        f"WARNING: Description for {sid} could not be "
                        f"mapped to a hash. Ignoring.",
                        file=sys.stderr,
                    )
        else:
            if not found_bracket_notation:
                # Fallback: return positional IDs as-is so callers can still
                # use them (preserves backward compatibility when grouped.json
                # is unavailable)
                return descriptions_by_positional

    return descriptions_by_hash


def parse_issue_descriptions(report_path: str) -> Dict[int, str]:
    """Extract descriptions from code review report.md by issue index (1, 2, 3...).

    Looks for headers like `### 1. Title` or `### 2. Title`.
    Extracts the description text that appears AFTER the metadata line
    (`**Validation:**...` or `**Importance:**...`) and BEFORE the `---` separator,
    less the validation reason the writer quotes between the two
    (:func:`_drop_validation_reason`).

    Returns:
        Dict mapping issue index to description text (e.g., {1: "Description..."})
        Empty dict if file not found.
    """
    if not Path(report_path).exists():
        return {}

    content = Path(report_path).read_text(encoding='utf-8')
    descriptions = {}

    # Each issue header `_issue_headers` accepts and everything under it up to
    # the next `---` or `###` line. Header format: ### 1. Title
    escaped = rm.has_escaped_text(content)
    for match in _issue_headers(content):
        block = _description_block(content, match)
        if block is None:
            continue
        description = _drop_validation_reason(_description_text(block, escaped)).strip()
        if description:
            descriptions[int(match.group(1))] = description

    return descriptions


#: The metadata line a description follows: ``**Validation:**`` or
#: ``**Importance:**``.
_METADATA_RE = re.compile(r'\*\*(?:Validation|Importance):\*\*[^\n]*\n')
#: The Skip box line, for a block with no metadata line.
_SKIP_LINE_RE = re.compile(r'^[ \t]*-[ \t]*\[[^\]\n]*\][ \t]*[Ss]kip[^\n]*\n', re.MULTILINE)


def _description_block(content: str, match: "re.Match[str]") -> Optional[str]:
    """The text under a header up to the next ``---`` or ``###`` line, or
    ``None`` for a header that ends the file."""
    if not content.startswith("\n", match.end()):
        return None
    start = match.end() + 1
    stop = _BLOCK_END_RE.search(content, start)
    return content[start:stop.start() if stop else len(content)]


def _description_text(block: str, escaped: bool) -> str:
    """The description in a header's block: what follows the metadata line
    (else the Skip box line), stripped, with the report's escaping undone
    when it has any (*escaped*: ``report_markdown.has_escaped_text``)."""
    metadata_match = _METADATA_RE.search(block)
    if metadata_match:
        description = block[metadata_match.end():]
    else:
        checkbox_match = _SKIP_LINE_RE.search(block)
        description = block[checkbox_match.end():] if checkbox_match else block
    description = description.strip()
    return rm.restore_model_text(description) if escaped else description


def find_edited_descriptions(
    report_path: str, grouped: List[Dict]
) -> Dict[str, Tuple[str, str]]:
    """Compare report.md descriptions with grouped.json, return edited items.

    Args:
        report_path: Path to report.md file
        grouped: List of group dicts from grouped.json with structure:
                 [{theme: str, suggestions: [{title, desc, ...}]}, ...]

    Returns:
        Dict mapping suggestion hash to (original_desc, edited_desc) for items
        where normalized descriptions differ. Keys are suggestion_hash values
        (hex strings). If suggestion_hash is not available on a suggestion,
        falls back to the positional G{N}S{M} ID.
    """
    report_descriptions = parse_suggestion_descriptions(report_path)

    if not report_descriptions:
        return {}
    escaped = escaped_report(report_path)

    # Ensure groups are stamped so suggestion_hash is available
    stamp_stable_ids(grouped)  # idempotent

    edited: Dict[str, Tuple[str, str]] = {}

    for group_idx, group in enumerate(grouped, start=1):
        suggestions = group.get('suggestions', [])
        for sugg_idx, suggestion in enumerate(suggestions, start=1):
            # Use suggestion_hash as the key; fall back to positional ID
            sugg_hash = suggestion.get('suggestion_hash', '')
            positional_id = f"G{group_idx}S{sugg_idx}"
            original_desc = suggestion.get('desc', '')

            # Check both hash-based and positional keys in report descriptions.
            # A v2 header carries the suggestion's *display* hash (its first 8+
            # characters, ``state_manager._assign_display_hashes``), which the
            # full ``suggestion_hash`` lookup alone never matched: an edit made
            # in report.md was silently dropped.
            display_hash = suggestion.get('display_hash', '')
            report_desc = None
            key_used = None
            if sugg_hash and sugg_hash in report_descriptions:
                report_desc = report_descriptions[sugg_hash]
                key_used = sugg_hash
            elif (display_hash and display_hash in report_descriptions
                  and (not sugg_hash or sugg_hash.startswith(display_hash))):
                report_desc = report_descriptions[display_hash]
                key_used = sugg_hash or display_hash
            elif positional_id in report_descriptions:
                report_desc = report_descriptions[positional_id]
                key_used = sugg_hash if sugg_hash else positional_id

            if report_desc is not None and key_used:
                if description_edited(original_desc, report_desc, escaped=escaped):
                    edited[key_used] = (original_desc, report_desc)

    return edited


def description_edited(
    original_desc: str, report_desc: str, *, escaped: bool = False,
) -> bool:
    """Whether *report_desc*, a description read back from ``report.md``, is
    the user's edit of *original_desc*, the review's own text.

    The one rule every lane's edit reader applies (``find_edited_descriptions``
    here, ``apply_code_fixes_orchestrator.find_edited_issue_descriptions``):
    the two differ once normalised (:func:`normalize_description`). In a report
    written with the escape (*escaped*, :func:`escaped_report`) a model's
    ``---`` or ``###`` line is escaped, so the parser reads every description
    whole and that is the whole rule: an edit anywhere in it, a cut included,
    is the user's. In an older report such a line cut the block, so a report
    description that is the original cut there (:func:`_is_block_cut`) is no
    edit, and the apply prompt keeps the whole description.
    """
    if normalize_description(original_desc) == normalize_description(report_desc):
        return False
    return escaped or not _is_block_cut(original_desc, report_desc)


def escaped_report(report_path: str) -> bool:
    """Whether the report at *report_path* was written with the escape
    (``report_markdown.has_escaped_text`` on its first line); ``False`` for
    one that cannot be read."""
    try:
        with open(report_path, encoding='utf-8') as handle:
            first = handle.readline()
    except (OSError, UnicodeDecodeError):
        return False
    return rm.has_escaped_text(first)


#: Where ``parse_suggestion_descriptions`` ends a block: a line that starts a
#: rule or a ``###`` header.
_BLOCK_END_RE = re.compile(r'\n---|\n###')


def _is_block_cut(original_desc: str, report_desc: str) -> bool:
    """True when *report_desc* is *original_desc* cut where the parser stops
    in a report written before ``report_markdown.neutralize_model_text``.

    There a description holding its own ``---`` rule or ``###`` line was
    rendered whole but read back only up to that line, so an untouched report
    would otherwise read as an edit that drops the rest of the description.
    A current report escapes both lines and is never cut.
    """
    raw = (original_desc or '').replace('\r\n', '\n')
    match = _BLOCK_END_RE.search(raw)
    return bool(match) and normalize_description(
        raw[:match.start()]
    ) == normalize_description(report_desc)


def load_html_selections(
    phase_dir: Path,
    groups: Optional[list] = None,
    plan_path: Optional[str] = None,
) -> Optional[Dict]:
    """Load user_selections.json if present in phase directory.

    Detects format_version and migrates v1 to v2 if needed.

    Args:
        phase_dir: Path to phase directory (e.g., plans/my-feature/review-plan/)
        groups: Optional list of groups/issues from grouped.json for v1 migration
            and index validation. If provided, warns about out-of-range references.
        plan_path: Optional absolute path to the plan file being processed.
            If provided and the JSON contains a different plan_path, raises ValueError.

    Returns:
        Parsed JSON dict if file exists and is valid, None otherwise.
        Expected v2 structure:
        {
            "format_version": 2,
            "plan_path": str,
            "phase": str,
            "exported_at": str (ISO timestamp),
            "skipped_groups": List[str],  # group hashes
            "skipped_suggestions": List[str],  # suggestion hashes
            "edited_descriptions": Dict[str, str]  # suggestion_hash -> new text
        }

    Raises:
        ValueError: If plan_path is provided and does not match the JSON's plan_path.
    """
    selections_path = phase_dir / "user_selections.json"

    try:
        content = selections_path.read_text(encoding='utf-8')
        # A report exported before the judge rename says `claude_decide`.
        data = upgrade_legacy(json.loads(content))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None
    # An export carries ids and choices only: scope tags and policy come from
    # the review's records and the command line (plan scope-policy §6).
    data = _strip_scope_fields(data, "user_selections.json")

    # Validate plan_path matches if provided
    if plan_path is not None:
        json_plan_path = data.get("plan_path")
        if json_plan_path is None:
            print(
                "WARNING: user_selections.json does not contain a plan_path "
                "field. Cannot verify selections match the current plan. "
                "This may be an export from an older version.",
                file=sys.stderr,
            )
        elif os.path.normpath(json_plan_path) != os.path.normpath(plan_path):
            raise ValueError(
                f"Plan path mismatch in user_selections.json!\n"
                f"  Selections were exported for: {json_plan_path}\n"
                f"  Current plan being processed:  {plan_path}\n"
                f"This likely means user_selections.json was copied from a "
                f"different plan's directory. Remove or replace the file "
                f"and retry."
            )

    # Detect format version and migrate v1 -> v2 if needed
    version = get_format_version(data)
    if version < 2 and groups is not None:
        data = _migrate_v1_html_selections(data, groups)

    # Validate references against groups if provided (post-migration, so
    # validation works on the v2 hash-based keys)
    if groups is not None:
        num_groups = len(groups)
        for idx in data.get("skipped_groups", []):
            if isinstance(idx, int) and idx > num_groups:
                print(
                    f"WARNING: user_selections.json references group/issue {idx} "
                    f"but only {num_groups} groups exist. This may indicate a "
                    f"numbering mismatch.",
                    file=sys.stderr,
                )
        for sid in data.get("skipped_suggestions", []):
            if isinstance(sid, str):
                m = re.match(r"G(\d+)", sid)
                if m and int(m.group(1)) > num_groups:
                    print(
                        f"WARNING: user_selections.json references {sid} "
                        f"but only {num_groups} groups exist.",
                        file=sys.stderr,
                    )
        for key in data.get("validation_overrides", {}):
            key_str = str(key)
            m = re.match(r"G(\d+)", key_str)
            if m and int(m.group(1)) > num_groups:
                print(
                    f"WARNING: validation override for {key_str} references "
                    f"group beyond {num_groups} groups.",
                    file=sys.stderr,
                )

    return data


def merge_selections(
    html_selections: Optional[Dict],
    md_skipped_groups: Set[str],
    md_skipped_suggestions: Set[str],
    md_edited: Dict[str, Tuple[str, str]],
) -> Tuple[Set[str], Set[str], Dict[str, str]]:
    """Merge HTML and markdown selections additively.

    Skips are unioned: markdown skips form the base and HTML skips are
    added on top, so an empty HTML ``skipped_groups`` list never erases
    markdown skip decisions.  Edited descriptions use overlay semantics
    (HTML wins per-key, markdown preserved otherwise).

    All keys are hash-based strings (group hashes for skipped_groups,
    suggestion hashes for skipped_suggestions and edited_descriptions).

    Args:
        html_selections: Parsed user_selections.json or None
        md_skipped_groups: Group hashes marked skip in report.md
        md_skipped_suggestions: Suggestion hashes marked skip in report.md
        md_edited: Dict of {hash: (original, edited)} from markdown

    Returns:
        Tuple of:
        - merged_skipped_groups: Set[str]
        - merged_skipped_suggestions: Set[str]
        - merged_edited_descriptions: Dict[str, str] (hash -> new description)
    """
    # Convert md_edited from (original, edited) tuples to just edited text
    md_edited_descriptions = {k: v[1] for k, v in md_edited.items()}

    # If no HTML selections, return markdown values
    if html_selections is None:
        return (
            md_skipped_groups,
            md_skipped_suggestions,
            md_edited_descriptions,
        )

    # Markdown skips are the base; HTML/C-level skips are unioned on top
    merged_skipped_groups = set(md_skipped_groups) | set(
        html_selections.get('skipped_groups', [])
    )
    merged_skipped_suggestions = set(md_skipped_suggestions) | set(
        html_selections.get('skipped_suggestions', [])
    )

    # For edited descriptions: start with markdown, then overlay HTML edits
    merged_edited_descriptions = dict(md_edited_descriptions)
    html_edited = html_selections.get('edited_descriptions', {})
    merged_edited_descriptions.update(html_edited)

    return (
        merged_skipped_groups,
        merged_skipped_suggestions,
        merged_edited_descriptions,
    )


def parse_validation_overrides_groups(report_path: str) -> Dict[str, str]:
    """
    Parse report.md and return validation overrides for groups, keyed by group hash.

    Supports two header formats:
        v2: ## G1 [a1b2c3d4]: Theme  (hash extracted from brackets)
        v1: ## G1: Theme              (legacy -- mapped via grouped.json)

    If both "Mark valid" and "Mark invalid" are checked, "invalid" wins (safety-first).
    "Let the agent decide" maps to "judge_decide" (precedence: invalid > valid >
    judge_decide).

    Returns:
        Dict mapping group hash to override value ("valid", "invalid", or
        "judge_decide")
    """
    if not Path(report_path).exists():
        return {}

    content = Path(report_path).read_text(encoding='utf-8')
    overrides_by_hash: Dict[str, str] = {}
    overrides_by_index: Dict[int, str] = {}
    refused: List[str] = []
    found_bracket_notation = False

    # A group's own region (``report_markdown.plan_sections``): from its header
    # to its first suggestion, so a suggestion's box is never the group's. A
    # ticked box (any non-blank mark) on a line of its own counts.
    for section in rm.plan_sections(content):
        if section.kind != rm.GROUP:
            continue
        override_val = rm.first_checked(section.body, _ITEM_OVERRIDES)
        if not override_val:
            continue
        match = section.match
        hash_val = match.group(2)
        if not section.trusted:
            refused.append(f"G{match.group(1)}")
        elif hash_val:
            found_bracket_notation = True
            overrides_by_hash[hash_val] = override_val
        else:
            overrides_by_index[int(match.group(1))] = override_val
    _warn_unhashed(refused, "`## G{N}:`", report_path)

    # Map positional indices to hashes via grouped.json
    if overrides_by_index:
        groups = _load_stamped_groups_for_legacy(report_path)
        if groups is not None:
            group_idx_to_hash, _ = _build_positional_maps(groups)
            for idx, val in overrides_by_index.items():
                ghash = group_idx_to_hash.get(idx)
                if ghash:
                    if ghash not in overrides_by_hash:
                        overrides_by_hash[ghash] = val
                else:
                    print(
                        f"WARNING: Validation override for G{idx} could not be "
                        f"mapped to a hash. Ignoring.",
                        file=sys.stderr,
                    )
        else:
            if not found_bracket_notation:
                print(
                    "WARNING: Report uses legacy G{N} format but grouped.json "
                    "not found for hash migration. Validation overrides may "
                    "not apply.",
                    file=sys.stderr,
                )

    return overrides_by_hash


def parse_suggestion_validation_overrides(report_path: str) -> Dict[str, str]:
    """
    Parse report.md and return validation overrides for individual suggestions,
    keyed by suggestion hash.

    Supports two header formats:
        v2: ### G1S2 [e5f6a7b8]: Title  (hash extracted from brackets)
        v1: ### G1S2: Title              (legacy -- mapped via grouped.json)

    If both "Mark valid" and "Mark invalid" are checked, "invalid" wins (safety-first).
    "Let the agent decide" maps to "judge_decide" (precedence: invalid > valid >
    judge_decide).

    Returns:
        Dict mapping suggestion hash to override value ("valid", "invalid", or
        "judge_decide")
    """
    if not Path(report_path).exists():
        return {}

    content = Path(report_path).read_text(encoding='utf-8')
    overrides_by_hash: Dict[str, str] = {}
    overrides_by_positional: Dict[str, str] = {}
    refused: List[str] = []
    found_bracket_notation = False

    # A suggestion's region (``report_markdown.plan_sections``): to the next
    # group or suggestion header, refused ones included, or its group's
    # closing `---`, so neither a forged header's box nor the next group's
    # own box reads as this suggestion's.
    for section in rm.plan_sections(content):
        if section.kind != rm.SUGGESTION:
            continue
        override_val = rm.first_checked(section.body, _ITEM_OVERRIDES)
        if not override_val:
            continue
        match = section.match
        positional_id = match.group(1).upper()
        hash_val = match.group(2)
        if not section.trusted:
            refused.append(positional_id)
        elif hash_val:
            found_bracket_notation = True
            overrides_by_hash[hash_val] = override_val
        else:
            overrides_by_positional[positional_id] = override_val
    _warn_unhashed(refused, "`### G{N}S{M}:`", report_path)

    # Map positional IDs to hashes via grouped.json
    if overrides_by_positional:
        groups = _load_stamped_groups_for_legacy(report_path)
        if groups is not None:
            _, sugg_id_to_hash = _build_positional_maps(groups)
            for sid, val in overrides_by_positional.items():
                shash = sugg_id_to_hash.get(sid)
                if shash:
                    if shash not in overrides_by_hash:
                        overrides_by_hash[shash] = val
                else:
                    print(
                        f"WARNING: Validation override for {sid} could not be "
                        f"mapped to a hash. Ignoring.",
                        file=sys.stderr,
                    )
        else:
            if not found_bracket_notation:
                print(
                    "WARNING: Report uses legacy G{N}S{M} format but "
                    "grouped.json not found for hash migration. "
                    "Suggestion validation overrides may not apply.",
                    file=sys.stderr,
                )

    return overrides_by_hash


def parse_validation_overrides_issues(report_path: str) -> Dict[int, str]:
    """
    Parse code review report.md and return validation overrides for issues.

    Looks for pattern:
        ### 1. Title
        - [ ] Skip
        - [x] Mark valid
        - [ ] Mark invalid

    If both "Mark valid" and "Mark invalid" are checked, "invalid" wins (safety-first).
    "Let the agent decide" maps to "judge_decide" (precedence: invalid > valid >
    judge_decide).

    Returns:
        Dict mapping issue index (1-based) to override value ("valid",
        "invalid", or "judge_decide")
    """
    if not Path(report_path).exists():
        return {}

    content = Path(report_path).read_text(encoding='utf-8')
    overrides = {}

    # Split into issue sections by the headers `_issue_headers` accepts — a
    # `### N.` line inside a description is description text, not a new block.
    for match, block in rm.sections(content, _issue_headers(content)):
        override_val = rm.first_checked(block, _ITEM_OVERRIDES)
        if override_val:
            overrides[int(match.group(1))] = override_val

    return overrides


def parse_consolidated_skipped_groups(report_path: str) -> Set[str]:
    """
    Parse consolidated report.md and return consolidated_ids of groups marked to skip.

    Looks for pattern:
        ## CG1 [abc123def456]:
        - [x/etc] Skip this group

    Returns:
        Set of consolidated_id values (12-char hex) marked with [x/etc] Skip this group
    """
    if not Path(report_path).exists():
        return set()

    content = Path(report_path).read_text(encoding='utf-8')
    skipped = set()

    # The box is the first non-blank line under the header; any non-blank
    # mark inside the brackets counts as ticked.
    for match in rm.CONSOLIDATED_HEADER_RE.finditer(content):
        line = rm.first_line_after(content, match.end())
        if line is not None and rm.is_checked(line, rm.SKIP_GROUP):
            skipped.add(match.group(1))

    return skipped


def parse_consolidated_validation_overrides(report_path: str) -> Dict[str, str]:
    """
    Parse consolidated report.md and return validation overrides for consolidated groups.

    Looks for pattern:
        ## CG1 [abc123def456]:
        - [ ] Skip this group
        - [x] Mark valid
        - [ ] Mark invalid
        - [ ] Needs human attention

    4-state priority: invalid > needs-human-decision > valid > judge_decide.

    Returns:
        Dict mapping consolidated_id (12-char hex) to override value
        ("valid", "invalid", "needs-human-decision", or "judge_decide")
    """
    if not Path(report_path).exists():
        return {}

    content = Path(report_path).read_text(encoding='utf-8')
    overrides = {}

    # Each consolidated group's block runs to the next `## CG` header.
    matches = list(rm.CONSOLIDATED_HEADER_RE.finditer(content))
    for match, block in rm.sections(content, matches):
        override_val = rm.first_checked(block, _CONSOLIDATED_OVERRIDES)
        if override_val:
            overrides[match.group(1)] = override_val

    return overrides


def load_consolidated_html_selections(
    phase_dir: Path,
    groups: Optional[List] = None,
    plan_path: Optional[str] = None,
) -> Optional[Dict]:
    """Load consolidated_user_selections.json if present in phase directory.

    Detects format_version and migrates v1 to v2 if needed.

    Args:
        phase_dir: Path to phase directory (e.g., plans/my-feature/review-plan/)
        groups: Optional list of groups for v1 migration.
        plan_path: Optional absolute path to the plan file being processed.
            If provided and the JSON contains a different plan_path, raises ValueError.

    Returns:
        Parsed JSON dict if file exists and is valid, None otherwise.
        Expected structure:
        {
            "plan_path": str,
            "phase": str,
            "exported_at": str (ISO timestamp),
            "skipped_groups": List[str],  # consolidated_ids (12-char hex)
            "validation_overrides": Dict[str, str]  # consolidated_id -> override value
        }

    Raises:
        ValueError: If plan_path is provided and does not match the JSON's plan_path.
    """
    selections_path = phase_dir / "consolidated_user_selections.json"

    try:
        content = selections_path.read_text(encoding='utf-8')
        # A report exported before the judge rename says `claude_decide`.
        data = upgrade_legacy(json.loads(content))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None
    data = _strip_scope_fields(data, "consolidated_user_selections.json")

    # Validate plan_path matches if provided
    if plan_path is not None:
        json_plan_path = data.get("plan_path")
        if json_plan_path is None:
            print(
                "WARNING: consolidated_user_selections.json does not contain a "
                "plan_path field. Cannot verify selections match the current plan. "
                "This may be an export from an older version.",
                file=sys.stderr,
            )
        elif os.path.normpath(json_plan_path) != os.path.normpath(plan_path):
            raise ValueError(
                f"Plan path mismatch in consolidated_user_selections.json!\n"
                f"  Selections were exported for: {json_plan_path}\n"
                f"  Current plan being processed:  {plan_path}\n"
                f"This likely means consolidated_user_selections.json was copied "
                f"from a different plan's directory. Remove or replace the file "
                f"and retry."
            )

    # Detect G-level format accidentally saved as consolidated_user_selections.json
    # G-level files have: skipped_suggestions (list of "G1S2" strings),
    # edited_descriptions (dict), and skipped_groups contains ints
    # C-level files have: skipped_groups as list of 12-char hex consolidated_ids
    has_g_level_markers = (
        "skipped_suggestions" in data
        or "edited_descriptions" in data
    )
    skipped_groups = data.get("skipped_groups", [])
    has_int_skipped = any(isinstance(g, int) for g in skipped_groups)

    if has_g_level_markers or has_int_skipped:
        print(
            "WARNING: consolidated_user_selections.json contains G-level format data. "
            "This file will be ignored for C-level decisions. If you exported from "
            "report.html, save as user_selections.json instead.",
            file=sys.stderr,
        )
        return None

    # Detect format version and migrate if needed
    version = get_format_version(data)
    if version < 2 and groups is not None:
        data = _migrate_v1_html_selections(data, groups)

    return data


def merge_consolidated_selections(
    html_selections: Optional[Dict],
    md_skipped: Set[str],
    md_overrides: Dict[str, str],
) -> Tuple[Set[str], Dict[str, str]]:
    """Merge HTML and markdown consolidated decisions with HTML taking precedence.

    Precedence rules:
    1. If item has decision in HTML selections -> use HTML decision
    2. If item not in HTML but in markdown -> use markdown decision
    3. If in neither -> not skipped, no override

    Args:
        html_selections: Parsed consolidated_user_selections.json or None
        md_skipped: Consolidated_ids marked skip in consolidated report.md
        md_overrides: Dict of {consolidated_id: override_value} from markdown

    Returns:
        Tuple of:
        - merged_skipped_groups: Set[str] (consolidated_ids)
        - merged_overrides: Dict[str, str] (consolidated_id -> override value)
    """
    # If no HTML selections, return markdown values
    if html_selections is None:
        return (
            md_skipped,
            md_overrides,
        )

    # HTML selections completely replace markdown equivalents
    merged_skipped = set(html_selections.get('skipped_groups', []))
    merged_overrides = dict(html_selections.get('validation_overrides', {}))

    return (
        merged_skipped,
        merged_overrides,
    )


# ---------------------------------------------------------------------------
# The binding between report.md's issue numbers and the issues.json they index
# ---------------------------------------------------------------------------

#: The footer `generate_review_report` stamps and `parse_issue_numbering_digest`
#: reads back. An HTML comment: it renders as nothing, and no parser above sees
#: it as a block, a checkbox or a description.
_ISSUE_DIGEST_RE = rm.ISSUE_DIGEST_RE


def issue_numbering_digest(issues: List[Dict]) -> str:
    """A short hash of the issue ORDER a report.md's ``### N.`` numbers index.

    report.md numbers issues positionally and ``build_issue_to_group_map`` reads
    those numbers back as positions in issues.json, so a checkbox means what the
    reader meant only while that list is the same list in the same order. The
    ordinary run writes both files from one pass and they agree; a hand-kept
    report.md against a re-aggregated issues.json resolves every number to
    whatever now sits at that position, silently.

    Hashed over the ordered suggestion hashes — the same identity the map itself
    joins on — rather than over issues.json's bytes, which are written by a
    different step and carry fields (timestamps, model attribution) that move
    without the numbering moving.
    """

    joined = "\n".join(
        str(issue.get("suggestion_hash") or generate_suggestion_id(issue))
        for issue in issues
    )
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def issue_numbering_footer(issues: List[Dict]) -> str:
    """The one line a rendered report.md carries so its numbers can be checked."""
    return f"<!-- multi-llm:issues-digest {issue_numbering_digest(issues)} -->"


def parse_issue_numbering_digest(report_path: str) -> Optional[str]:
    """The digest a report.md was stamped with, or ``None``.

    ``None`` for every report written before the stamp existed, which is why the
    check it feeds warns on a *mismatch* only and never on an absence.
    """
    try:
        with open(report_path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        return None
    return rm.issue_digest(text)
