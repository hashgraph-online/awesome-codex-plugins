"""
S-expression parser for KiCad files.

Parses KiCad's Lisp-like S-expression format into nested Python lists.
Handles quoted strings, multi-line expressions, and large files efficiently.

Usage:
    from kicad_core.sexp import parse_file, find_all, find_first, get_property
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


class _Escaped(str):
    """A token whose text carried brace escapes: the value is the decoded text, ``raw``
    the text as written (KiCad keeps net names in that form)."""
    __slots__ = ("raw",)


def _decoded(text: str) -> str:
    out = _unescape_braces(text)
    if out == text:
        return text
    tok = _Escaped(out)
    tok.raw = text
    return tok


def raw_text(token) -> str:
    """The token's text as written in the file, brace escapes kept."""
    return token.raw if isinstance(token, _Escaped) else str(token)


def unescape_string(text: str) -> str:
    """KiCad's UnescapeString (string_utils.cpp): the text KiCad shows for an escaped name."""
    n = len(text)
    if n <= 2 or "{" not in text:
        return text
    out = []
    i = 0
    prev = ch = ""
    while i < n:
        prev, ch = ch, text[i]
        if ch != "{":
            out.append(ch)
            i += 1
            continue
        depth, j = 1, i + 1
        while j < n:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth <= 0:
                    break
            j += 1
        token = text[i + 1:j]
        if j >= n:
            out.append("{" + unescape_string(token))
        elif prev in ("$", "~", "^", "_") or token not in _KICAD_UNESCAPE:
            out.append("{" + unescape_string(token) + "}")
        else:
            out.append(_KICAD_UNESCAPE[token])
        ch = text[j] if j < n else ""
        i = j + 1
    return "".join(out)


_KICAD_UNESCAPE = {
    "dblquote": '"', "quote": "'", "lt": "<", "gt": ">", "backslash": "\\", "slash": "/",
    "bar": "|", "comma": ",", "colon": ":", "space": " ", "dollar": "$", "tab": "\t",
    "return": "\n", "brace": "{",
}


def net_name_escape(text: str) -> str:
    """KiCad's EscapeString(text, CTX_NETNAME): '/' becomes {slash}, line breaks are dropped."""
    return text.replace("/", "{slash}").replace("\n", "").replace("\r", "")


def parse(text: str) -> list:
    """Parse S-expression text into nested Python lists."""
    tokens = _tokenize(text)
    result = _parse_tokens(tokens, 0)[0]
    return result


def parse_file(path: str) -> list:
    """Parse a KiCad S-expression file."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return parse(f.read())


_C_ESCAPES = {"a": "\x07", "b": "\x08", "f": "\x0c", "n": "\n", "r": "\r",
              "t": "\t", "v": "\x0b", '"': '"', "\\": "\\"}
_C_ESCAPE_RE = re.compile(r"\\(x[0-9A-Fa-f]{1,2}|[0-7]{1,3}|.)", re.S)


def _unescape_c(raw: str) -> str:
    """Decode a quoted token's escapes as KiCad's lexer does (dsnlexer.cpp).

    \\x and octal escapes are raw bytes that the token then reads as UTF-8; an
    unknown escape keeps its backslash.
    """
    if "\\" not in raw:
        return raw
    out = bytearray()
    pos = 0
    for m in _C_ESCAPE_RE.finditer(raw):
        out += raw[pos:m.start()].encode("utf-8", "surrogatepass")
        pos = m.end()
        g = m.group(1)
        if g[0] == "x" and len(g) > 1:
            out.append(int(g[1:], 16))
        elif g[0] in "01234567":
            out.append(int(g, 8) & 0xFF)
        elif g in _C_ESCAPES:
            out += _C_ESCAPES[g].encode()
        else:
            out += ("\\" + g).encode("utf-8", "surrogatepass")
    out += raw[pos:].encode("utf-8", "surrogatepass")
    return out.decode("utf-8", "replace")


class _Quoted(str):
    """A quoted token whose text spells a keyword the readers test for."""
    __slots__ = ()


_KEYWORD_LOOKALIKES = frozenset({"private", "hide"})


def is_keyword(token, word: str) -> bool:
    """True only for an unquoted atom equal to *word* (a quoted "hide" is a string)."""
    return token == word and not isinstance(token, _Quoted)


# KiCad ends an atom only at whitespace (NUL included) or a parenthesis; a quote
# starts a string only as a token's first character.
_ATOM_END = frozenset(" \t\n\r\0()")
_SPACE = frozenset(" \t\n\r\0")

# Punctuation tokens are sentinels so a quoted "(" or ")" stays a plain string.
_LPAREN = object()
_RPAREN = object()


def _tokenize(text: str) -> list:
    """Tokenize S-expression text into a flat list of tokens."""
    tokens = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c in _SPACE:
            i += 1
        elif c == "#" and not text[text.rfind("\n", 0, i) + 1:i].strip(" \t\r\0"):
            # A comment only when first on its line; elsewhere # is an atom character
            while i < n and text[i] != "\n":
                i += 1
        elif c == "(":
            tokens.append(_LPAREN)
            i += 1
        elif c == ")":
            tokens.append(_RPAREN)
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
            tok = _decoded(_unescape_c(raw))
            tokens.append(_Quoted(tok) if tok in _KEYWORD_LOOKALIKES else tok)
            i = j + 1
        else:
            # Unquoted atom
            j = i
            while j < n and text[j] not in _ATOM_END:
                j += 1
            tokens.append(_decoded(text[i:j]))
            i = j
    return tokens


def _parse_tokens(tokens: list, pos: int) -> tuple[Any, int]:
    """Recursively parse tokens starting at pos. Returns (result, new_pos)."""
    # Bounds check for truncated/malformed files with unbalanced parens
    if pos >= len(tokens):
        raise ValueError("Unexpected end of input at position %d" % pos)
    if tokens[pos] is _LPAREN:
        lst = []
        pos += 1
        while pos < len(tokens) and tokens[pos] is not _RPAREN:
            item, pos = _parse_tokens(tokens, pos)
            lst.append(item)
        return lst, pos + 1  # skip ')'
    else:
        tok = tokens[pos]
        # A stray ")" at top level comes back as the string, as for any other atom.
        return (")" if tok is _RPAREN else tok), pos + 1


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


def get_value(node: list, keyword: str, raw: bool = False) -> str | None:
    """Get the value of a simple (keyword value) pair.

    Example: get_value(symbol, "lib_id") -> "Device:C"
    ``raw=True`` returns the text as written (brace escapes kept).
    """
    child = find_first(node, keyword)
    if child and len(child) > 1:
        return raw_text(child[1]) if raw else str(child[1])
    return None


def _iter_properties(node: list):
    """Yield ``(name, value)`` for each ``(property ["private"] name value ...)`` child,
    in file order; the raw tokens, so each reader keeps its own matching policy."""
    for child in node:
        if isinstance(child, list) and len(child) >= 3 and child[0] == "property":
            off = 1 if is_keyword(child[1], "private") else 0
            if len(child) >= 3 + off:
                yield child[1 + off], child[2 + off]


def get_property(node: list, prop_name: str) -> str | None:
    """Get the value of a named property (exact case match).

    Handles KiCad 9+ ``(property private "Name" "Value" ...)`` format
    where ``private`` shifts the name/value indices by one.

    Example: get_property(symbol, "Reference") -> "C7"
    """
    for name, value in _iter_properties(node):
        if name == prop_name:
            return str(value)
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
    for name, value in _iter_properties(node):
        result[name.lower()] = str(value)
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


def has_flag(node: list, flag: str) -> bool:
    """Check if a node contains a flag like 'hide' or 'yes'.

    Handles three KiCad forms:
    - Bare token:    (pin ... hide ...)        — legacy (KiCad 5/6/early 7)
    - Bare list:     (fp_text ... (hide))      — true (KiCad's absent-bool default)
    - Boolean yes:   (pin ... (hide yes) ...)  — true
    - Boolean no:    (pin ... (hide no) ...)   — false

    Absent flag returns False.
    """
    if any(is_keyword(child, flag) for child in node):
        return True
    for child in node:
        if isinstance(child, list) and child and child[0] == flag:
            return len(child) < 2 or str(child[1]).lower() in ("yes", "true")
    return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sexp_parser.py <file.kicad_sch|.kicad_pcb>")
        sys.exit(1)
    tree = parse_file(sys.argv[1])
    print(f"Parsed {sys.argv[1]}: root node = {tree[0] if isinstance(tree, list) else tree}")
    print(f"Top-level children: {len(tree) - 1}")
