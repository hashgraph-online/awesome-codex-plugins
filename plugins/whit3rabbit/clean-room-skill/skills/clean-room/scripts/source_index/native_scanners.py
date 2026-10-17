"""Language scanners for Go, Rust, JVM, Swift, C-family, and C#."""

from __future__ import annotations

import re
from typing import Any

from source_index.scanner_utils import IDENTIFIER_RE, truncate_scanned


CSHARP_KEYWORDS = {
    "abstract",
    "as",
    "base",
    "bool",
    "break",
    "byte",
    "case",
    "catch",
    "char",
    "checked",
    "class",
    "const",
    "continue",
    "decimal",
    "default",
    "delegate",
    "do",
    "double",
    "else",
    "enum",
    "event",
    "explicit",
    "extern",
    "false",
    "finally",
    "fixed",
    "float",
    "for",
    "foreach",
    "goto",
    "if",
    "implicit",
    "in",
    "int",
    "interface",
    "internal",
    "is",
    "lock",
    "long",
    "namespace",
    "new",
    "null",
    "object",
    "operator",
    "out",
    "override",
    "params",
    "private",
    "protected",
    "public",
    "readonly",
    "ref",
    "return",
    "sbyte",
    "sealed",
    "short",
    "sizeof",
    "stackalloc",
    "static",
    "string",
    "struct",
    "switch",
    "this",
    "throw",
    "true",
    "try",
    "typeof",
    "uint",
    "ulong",
    "unchecked",
    "unsafe",
    "ushort",
    "using",
    "virtual",
    "void",
    "volatile",
    "while",
}
CSHARP_TYPE_KEYWORDS = {
    "bool",
    "byte",
    "char",
    "decimal",
    "double",
    "float",
    "int",
    "long",
    "object",
    "sbyte",
    "short",
    "string",
    "uint",
    "ulong",
    "ushort",
    "void",
}
CSHARP_MODIFIERS = (
    "public",
    "internal",
    "private",
    "protected",
    "static",
    "async",
    "virtual",
    "override",
    "abstract",
    "sealed",
    "extern",
    "partial",
    "unsafe",
    "new",
)


def scan_go(text: str) -> tuple[str, list[dict[str, Any]], list[dict[str, str]]]:
    imports: list[dict[str, Any]] = []
    exports: list[dict[str, str]] = []

    for block in re.finditer(r"(?ms)^\s*import\s*\((.*?)\)", text):
        for match in re.finditer(r'"([^"]+)"', block.group(1)):
            imports.append({"specifier": match.group(1), "kind": "go-import", "is_relative": match.group(1).startswith("."), "names": []})
    for match in re.finditer(r'(?m)^\s*import\s+(?:[._A-Za-z]\w*\s+)?(?:"([^"]+)")', text):
        imports.append({"specifier": match.group(1), "kind": "go-import", "is_relative": match.group(1).startswith("."), "names": []})
    for match in re.finditer(rf"(?m)^\s*func\s+(?:\([^)]*\)\s*)?({IDENTIFIER_RE})\s*\(", text):
        exports.append({"name": match.group(1), "kind": "go-function"})
    for match in re.finditer(rf"(?m)^\s*type\s+({IDENTIFIER_RE})\b", text):
        exports.append({"name": match.group(1), "kind": "go-type"})
    for match in re.finditer(rf"(?m)^\s*(?:const|var)\s+(?:\(\s*)?({IDENTIFIER_RE})\b", text):
        exports.append({"name": match.group(1), "kind": "go-binding"})

    return "go-scanner", *truncate_scanned(imports, exports)


def scan_rust(text: str) -> tuple[str, list[dict[str, Any]], list[dict[str, str]]]:
    imports: list[dict[str, Any]] = []
    exports: list[dict[str, str]] = []

    for match in re.finditer(r"(?m)^\s*use\s+([^;]+);", text):
        specifier = re.sub(r"\s+", "", match.group(1))
        imports.append({"specifier": specifier, "kind": "rust-use", "is_relative": specifier.startswith(("self::", "super::", "crate::")), "names": []})
    for match in re.finditer(rf"(?m)^\s*(?:pub\s+)?mod\s+({IDENTIFIER_RE})\s*;", text):
        imports.append({"specifier": match.group(1), "kind": "rust-mod", "is_relative": True, "names": []})
    for match in re.finditer(
        rf"(?m)^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:fn|struct|enum|trait|type|const|static)\s+({IDENTIFIER_RE})\b",
        text,
    ):
        exports.append({"name": match.group(1), "kind": "rust-declaration"})

    return "rust-scanner", *truncate_scanned(imports, exports)


def scan_java_kotlin(language: str, text: str) -> tuple[str, list[dict[str, Any]], list[dict[str, str]]]:
    imports: list[dict[str, Any]] = []
    exports: list[dict[str, str]] = []
    scanner = "java-scanner" if language == "java" else "kotlin-scanner"

    for match in re.finditer(r"(?m)^\s*import\s+(?:static\s+)?([A-Za-z_][\w.]*\*?)\s*;?", text):
        imports.append({"specifier": match.group(1), "kind": f"{language}-import", "is_relative": False, "names": []})
    for match in re.finditer(
        rf"(?m)^\s*(?:public|internal|private|protected|sealed|abstract|final|open|data|value|\s)*"
        rf"(?:class|interface|enum|object|record)\s+({IDENTIFIER_RE})\b",
        text,
    ):
        exports.append({"name": match.group(1), "kind": f"{language}-type"})
    if language == "kotlin":
        for match in re.finditer(rf"(?m)^\s*(?:public|internal|private|protected|suspend|\s)*fun\s+({IDENTIFIER_RE})\s*\(", text):
            exports.append({"name": match.group(1), "kind": "kotlin-function"})

    return scanner, *truncate_scanned(imports, exports)


def scan_swift(text: str) -> tuple[str, list[dict[str, Any]], list[dict[str, str]]]:
    imports: list[dict[str, Any]] = []
    exports: list[dict[str, str]] = []

    for match in re.finditer(r"(?m)^\s*import\s+(?:@\w+\s+)?([A-Za-z_][\w.]*)", text):
        imports.append({"specifier": match.group(1), "kind": "swift-import", "is_relative": False, "names": []})
    for match in re.finditer(
        rf"(?m)^\s*(?:public|internal|private|fileprivate|open|final|\s)*"
        rf"(?:class|struct|enum|protocol|actor|func|let|var)\s+({IDENTIFIER_RE})\b",
        text,
    ):
        exports.append({"name": match.group(1), "kind": "swift-declaration"})

    return "swift-scanner", *truncate_scanned(imports, exports)


def scan_c_like(language: str, text: str) -> tuple[str, list[dict[str, Any]], list[dict[str, str]]]:
    imports: list[dict[str, Any]] = []
    exports: list[dict[str, str]] = []

    for match in re.finditer(r'(?m)^\s*#\s*include\s*([<"])([^>"]+)[>"]', text):
        imports.append({"specifier": match.group(2), "kind": f"{language}-include", "is_relative": match.group(1) == '"', "names": []})
    for match in re.finditer(
        rf"(?m)^\s*(?:extern\s+)?(?:[A-Za-z_][\w:<>,\s\*&~]+\s+)+({IDENTIFIER_RE})\s*\([^;]*\)\s*(?:;|{{)",
        text,
    ):
        name = match.group(1)
        if name not in {"if", "for", "while", "switch", "return"}:
            exports.append({"name": name, "kind": f"{language}-function"})
    for match in re.finditer(rf"(?m)^\s*(?:class|struct|enum)\s+({IDENTIFIER_RE})\b", text):
        exports.append({"name": match.group(1), "kind": f"{language}-type"})

    return f"{language}-scanner", *truncate_scanned(imports, exports)


def scan_csharp(text: str) -> tuple[str, list[dict[str, Any]], list[dict[str, str]]]:
    imports: list[dict[str, Any]] = []
    exports: list[dict[str, str]] = []
    modifier_pattern = "|".join(CSHARP_MODIFIERS)

    for match in re.finditer(r"(?m)^\s*using\s+(?:static\s+)?([A-Za-z_][\w.]*)\s*;", text):
        imports.append({"specifier": match.group(1), "kind": "csharp-using", "is_relative": False, "names": []})
    for match in re.finditer(
        rf"(?m)^\s*(?:public|internal|private|protected|abstract|sealed|static|partial|\s)*"
        rf"(?:class|interface|struct|enum|record)\s+({IDENTIFIER_RE})\b",
        text,
    ):
        exports.append({"name": match.group(1), "kind": "csharp-type"})
    for match in re.finditer(
        rf"(?m)^\s*(?:(?:{modifier_pattern})\s+)*"
        rf"(?P<return_types>(?:[A-Za-z_][\w<>,\[\]?]*(?:\s*\.\s*[A-Za-z_][\w<>,\[\]?]*)*\s+)+)"
        rf"(?P<name>{IDENTIFIER_RE})\s*\([^;{{}}]*\)\s*(?:where\s+[^\n{{;]+)?(?:=>|;|{{)",
        text,
    ):
        name = match.group("name")
        return_tokens = re.findall(r"[A-Za-z_]\w*", match.group("return_types"))
        invalid_return_tokens = [
            token for token in return_tokens if token in CSHARP_KEYWORDS and token not in CSHARP_TYPE_KEYWORDS
        ]
        if name not in CSHARP_KEYWORDS and not invalid_return_tokens:
            exports.append({"name": name, "kind": "csharp-method"})

    return "csharp-scanner", *truncate_scanned(imports, exports)
