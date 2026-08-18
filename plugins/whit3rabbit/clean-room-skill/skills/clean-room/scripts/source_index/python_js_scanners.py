"""Python and JavaScript/TypeScript source scanners."""

from __future__ import annotations

import ast
import re
from typing import Any

from source_index.scanner_utils import JS_STRING_RE, truncate_scanned


def literal_all(node: ast.AST) -> list[str]:
    try:
        value = ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return []
    if isinstance(value, (list, tuple)):
        return [item for item in value if isinstance(item, str)]
    return []


def scan_python(text: str) -> tuple[str, list[dict[str, Any]], list[dict[str, str]]]:
    imports: list[dict[str, Any]] = []
    exports: list[dict[str, str]] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return "python-ast-error", imports, exports

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(
                    {
                        "specifier": alias.name,
                        "kind": "python-import",
                        "is_relative": False,
                        "names": [alias.asname or alias.name.split(".")[0]],
                    }
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            specifier = "." * node.level + module
            imports.append(
                {
                    "specifier": specifier,
                    "kind": "python-from-import",
                    "is_relative": node.level > 0,
                    "names": [alias.asname or alias.name for alias in node.names],
                }
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            exports.append({"name": node.name, "kind": "top-level-function"})
        elif isinstance(node, ast.ClassDef):
            exports.append({"name": node.name, "kind": "top-level-class"})
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets: list[ast.AST] = []
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
                value = node.value
            else:
                targets = [node.target]
                value = node.value
            for target in targets:
                if isinstance(target, ast.Name) and target.id == "__all__" and value is not None:
                    for name in literal_all(value):
                        exports.append({"name": name, "kind": "explicit-all"})
                elif isinstance(target, ast.Name):
                    exports.append({"name": target.id, "kind": "top-level-assignment"})

    return "python-ast", *truncate_scanned(imports, exports)


def strip_js_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"(?m)//.*$", " ", text)
    return text


def split_export_names(raw: str) -> list[str]:
    names: list[str] = []
    for part in raw.split(","):
        item = part.strip()
        if not item:
            continue
        match = re.search(r"\bas\s+([A-Za-z_$][\w$]*)$", item)
        if match:
            names.append(match.group(1))
        else:
            names.append(item.split()[0].strip())
    return [name for name in names if re.fullmatch(r"[A-Za-z_$][\w$]*", name)]


def scan_js_ts(text: str) -> tuple[str, list[dict[str, Any]], list[dict[str, str]]]:
    scanned = strip_js_comments(text)
    imports: list[dict[str, Any]] = []
    exports: list[dict[str, str]] = []

    for match in re.finditer(rf"(?m)^\s*import(?:\s+type)?(?:[\s\w$*{{}},]+?\s+from\s*)?{JS_STRING_RE}", scanned):
        imports.append({"specifier": match.group(1), "kind": "esm-import", "is_relative": match.group(1).startswith("."), "names": []})
    for match in re.finditer(rf"(?m)^\s*export(?:\s+type)?\s+[^;]*?\s+from\s+{JS_STRING_RE}", scanned):
        imports.append({"specifier": match.group(1), "kind": "esm-re-export", "is_relative": match.group(1).startswith("."), "names": []})
    for match in re.finditer(rf"\brequire\(\s*{JS_STRING_RE}\s*\)", scanned):
        imports.append({"specifier": match.group(1), "kind": "commonjs-require", "is_relative": match.group(1).startswith("."), "names": []})
    for match in re.finditer(rf"\bimport\(\s*{JS_STRING_RE}\s*\)", scanned):
        imports.append({"specifier": match.group(1), "kind": "dynamic-import", "is_relative": match.group(1).startswith("."), "names": []})

    for match in re.finditer(
        r"(?m)^\s*export\s+(?:async\s+)?(?:class|function|const|let|var|interface|type|enum)\s+([A-Za-z_$][\w$]*)",
        scanned,
    ):
        exports.append({"name": match.group(1), "kind": "esm-declaration"})
    for match in re.finditer(r"(?m)^\s*export\s+default\b", scanned):
        exports.append({"name": "default", "kind": "esm-default"})
    for match in re.finditer(r"(?m)^\s*export\s*{([^}]+)}", scanned):
        for name in split_export_names(match.group(1)):
            exports.append({"name": name, "kind": "esm-named"})
    for match in re.finditer(r"\bmodule\.exports\s*=", scanned):
        exports.append({"name": "module.exports", "kind": "commonjs-module"})
    for match in re.finditer(r"\bexports\.([A-Za-z_$][\w$]*)\s*=", scanned):
        exports.append({"name": match.group(1), "kind": "commonjs-named"})

    return "javascript-typescript-scanner", *truncate_scanned(imports, exports)

