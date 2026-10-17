"""Language detection and scanner dispatch for source-index output."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from source_index.native_scanners import (
    scan_c_like,
    scan_csharp,
    scan_go,
    scan_java_kotlin,
    scan_rust,
    scan_swift,
)
from source_index.python_js_scanners import scan_js_ts, scan_python


C_LIKE_EXTENSIONS = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}
CSHARP_EXTENSIONS = {".cs"}
GO_EXTENSIONS = {".go"}
JVM_EXTENSIONS = {".java", ".kt", ".kts"}
JS_TS_EXTENSIONS = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts"}
PYTHON_EXTENSIONS = {".py", ".pyi"}
RUST_EXTENSIONS = {".rs"}
SWIFT_EXTENSIONS = {".swift"}
RESOLVE_EXTENSIONS = (
    ".py",
    ".pyi",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".mts",
    ".cts",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".kts",
    ".swift",
    ".cs",
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hh",
    ".hpp",
    ".hxx",
)
SCANNER_MODES = [
    "python-ast",
    "javascript-typescript-scanner",
    "go-scanner",
    "rust-scanner",
    "java-scanner",
    "kotlin-scanner",
    "swift-scanner",
    "c-scanner",
    "cpp-scanner",
    "csharp-scanner",
    "text-metrics",
]


def language_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in PYTHON_EXTENSIONS:
        return "python"
    if suffix in JS_TS_EXTENSIONS:
        return "typescript" if "ts" in suffix else "javascript"
    if suffix in GO_EXTENSIONS:
        return "go"
    if suffix in RUST_EXTENSIONS:
        return "rust"
    if suffix == ".java":
        return "java"
    if suffix in {".kt", ".kts"}:
        return "kotlin"
    if suffix in SWIFT_EXTENSIONS:
        return "swift"
    if suffix in CSHARP_EXTENSIONS:
        return "csharp"
    if suffix in C_LIKE_EXTENSIONS:
        return "cpp" if suffix in {".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx"} else "c"
    return "text"


def scan_file(language: str, text: str) -> tuple[str, list[dict[str, Any]], list[dict[str, str]]]:
    if language == "python":
        return scan_python(text)
    if language in {"javascript", "typescript"}:
        return scan_js_ts(text)
    if language == "go":
        return scan_go(text)
    if language == "rust":
        return scan_rust(text)
    if language in {"java", "kotlin"}:
        return scan_java_kotlin(language, text)
    if language == "swift":
        return scan_swift(text)
    if language in {"c", "cpp"}:
        return scan_c_like(language, text)
    if language == "csharp":
        return scan_csharp(text)
    return "text-metrics", [], []

