"""
S-expression parser for KiCad files.

Parses KiCad's Lisp-like S-expression format into nested Python lists.
Handles quoted strings, multi-line expressions, and large files efficiently.

Usage:
    from sexp_parser import parse_file, find_all, find_first, get_property
"""

import re
import sys
from typing import Any

# KiCad brace-escape sequences (common/string_utils.cpp)
_BRACE_ESCAPES = {
    "{dblquote}": '"', "{quote}": "'", "{lt}": "<", "{gt}": ">",
    "{backslash}": "\\", "{slash}": "/", "{bar}": "|", "{colon}": ":",
    "{space}": " ", "{amp}": "&", "{tab}": "\t", "{newline}": "\n",
    "{return}": "\r", "{brace}": "{",
}
_BRACE_RE = re.compile(r"\{[a-z]+\}")


def _unescape_braces(s: str) -> str:
    """Replace KiCad {brace_escape} sequences with their characters."""
    if "{" not in s:
        return s
    return _BRACE_RE.sub(lambda m: _BRACE_ESCAPES.get(m.group(0), m.group(0)), s)


def parse(text: str) -> list:
    """Parse S-expression text into nested Python lists."""
    tokens = _tokenize(text)
    result = _parse_tokens(tokens, 0)[0]
    return result


def parse_file(path: str) -> list:
    """Parse a KiCad S-expression file."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return parse(f.read())


def _tokenize(text: str) -> list[str]:
    """Tokenize S-expression text into a flat list of tokens."""
    tokens = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c in " \t\n\r":
            i += 1
        elif c == "#":
            # Line comment — skip to end of line
            while i < n and text[i] != "\n":
                i += 1
        elif c == "(":
            tokens.append("(")
            i += 1
        elif c == ")":
            tokens.append(")")
            i += 1
        elif c == '"':
            # Quoted string
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                elif text[j] == '"':
                    break
                else:
                    j += 1
            raw = text[i + 1 : j]
            # Unescape: \\→placeholder first, then known sequences, then restore
            raw = raw.replace("\\\\", "\x00").replace('\\"', '"').replace("\\n", "\n").replace("\\r", "\r").replace("\x00", "\\")
            tokens.append(_unescape_braces(raw))
            i = j + 1
        else:
            # Unquoted atom
            j = i
            while j < n and text[j] not in " \t\n\r()\"":
                j += 1
            tokens.append(_unescape_braces(text[i:j]))
            i = j
    return tokens


def _parse_tokens(tokens: list[str], pos: int) -> tuple[Any, int]:
    """Recursively parse tokens starting at pos. Returns (result, new_pos)."""
    # KH-101: Bounds check for truncated/malformed files with unbalanced parens
    if pos >= len(tokens):
        raise ValueError("Unexpected end of input at position %d" % pos)
    if tokens[pos] == "(":
        lst = []
        pos += 1
        while pos < len(tokens) and tokens[pos] != ")":
            item, pos = _parse_tokens(tokens, pos)
            lst.append(item)
        return lst, pos + 1  # skip ')'
    else:
        return tokens[pos], pos + 1


def find_all(node: list, keyword: str) -> list[list]:
    """Find all direct children of node that start with keyword.

    Example: find_all(root, "symbol") returns all (symbol ...) blocks.
    """
    if not isinstance(node, list):
        return []
    return [child for child in node if isinstance(child, list) and len(child) > 0 and child[0] == keyword]


def find_first(node: list, keyword: str) -> list | None:
    """Find first direct child of node that starts with keyword."""
    if not isinstance(node, list):
        return None
    for child in node:
        if isinstance(child, list) and len(child) > 0 and child[0] == keyword:
            return child
    return None


def find_deep(node: list, keyword: str) -> list[list]:
    """Recursively find all nodes starting with keyword at any depth."""
    results = []
    if not isinstance(node, list):
        return results
    _find_deep_acc(node, keyword, results)
    return results


def _find_deep_acc(node: list, keyword: str, acc: list) -> None:
    """Accumulator helper for find_deep — avoids intermediate list allocations."""
    if len(node) > 0 and node[0] == keyword:
        acc.append(node)
    for child in node:
        if isinstance(child, list):
            _find_deep_acc(child, keyword, acc)


def get_value(node: list, keyword: str) -> str | None:
    """Get the value of a simple (keyword value) pair.

    Example: get_value(symbol, "lib_id") -> "Device:C"
    """
    child = find_first(node, keyword)
    if child and len(child) > 1:
        return str(child[1])
    return None


def get_property(node: list, prop_name: str) -> str | None:
    """Get the value of a named property (exact case match).

    Handles KiCad 9+ ``(property private "Name" "Value" ...)`` format
    where ``private`` shifts the name/value indices by one.

    Example: get_property(symbol, "Reference") -> "C7"
    """
    for child in node:
        if isinstance(child, list) and len(child) >= 3 and child[0] == "property":
            off = 1 if child[1] == "private" else 0
            if len(child) >= 3 + off and child[1 + off] == prop_name:
                return str(child[2 + off])
    return None


def get_properties(node: list) -> dict[str, str]:
    """Return all properties of a node as a case-normalised dict.

    Handles KiCad 9+ ``(property private ...)`` format.

    Keys are lowercased so callers can do case-insensitive lookups without
    enumerating every possible capitalisation variant.

    Example:
        props = get_properties(sym)
        digikey = props.get("digikey") or props.get("digi-key part number") or ""
    """
    result: dict[str, str] = {}
    for child in node:
        if isinstance(child, list) and len(child) >= 3 and child[0] == "property":
            off = 1 if child[1] == "private" else 0
            if len(child) >= 3 + off:
                result[child[1 + off].lower()] = str(child[2 + off])
    return result


def get_at(node: list) -> tuple[float, float, float] | None:
    """Get (x, y, angle) from an (at x y [angle]) node."""
    at = find_first(node, "at")
    if at and len(at) >= 3:
        x = float(at[1])
        y = float(at[2])
        angle = float(at[3]) if len(at) > 3 else 0.0
        return (x, y, angle)
    return None


def get_xy(node: list) -> tuple[float, float] | None:
    """Get (x, y) from an (xy x y) node."""
    if isinstance(node, list) and len(node) >= 3 and node[0] == "xy":
        return (float(node[1]), float(node[2]))
    return None


def has_flag(node: list, flag: str) -> bool:
    """Check if a node contains a flag like 'hide' or 'yes'.

    Handles three KiCad forms:
    - Bare token:    (pin ... hide ...)        — legacy (KiCad 5/6/early 7)
    - Boolean yes:   (pin ... (hide yes) ...)  — post-20241004
    - Boolean no:    (pin ... (hide no) ...)   — post-20241004 (returns False)

    Absent flag returns False.
    """
    if flag in node:
        return True
    for child in node:
        if isinstance(child, list) and len(child) >= 2 and child[0] == flag:
            return str(child[1]).lower() in ("yes", "true")
    return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sexp_parser.py <file.kicad_sch|.kicad_pcb>")
        sys.exit(1)
    tree = parse_file(sys.argv[1])
    print(f"Parsed {sys.argv[1]}: root node = {tree[0] if isinstance(tree, list) else tree}")
    print(f"Top-level children: {len(tree) - 1}")
