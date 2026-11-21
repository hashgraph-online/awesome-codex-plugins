"""Compact machine-response helpers for Perform."""

import json

from .catalog import ActionCatalog
from .diagnostics import PerformRequestError


def compact_json(value):
    """Serialize one JSON value without optional whitespace."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def error_payload(code, message, alternatives=None):
    """Build one compact error response with optional alternatives."""
    payload = {"error": {"code": code, "message": message}}
    if alternatives:
        payload["available_variants"] = list(alternatives)
    return payload


def error_exit_code(code):
    """Map one error code to its documented shell class."""
    if code == "fatal_catalog":
        return 3
    if code == "runtime_error":
        return 4
    return 2


def diagnostic_strings(catalog):
    """Return unique warning and error diagnostics as human-ready strings."""
    if not isinstance(catalog, ActionCatalog):
        raise TypeError("catalog must be an ActionCatalog")
    visible = []
    seen = set()
    for diagnostic in catalog.diagnostics:
        if diagnostic.severity not in ("warning", "error"):
            continue
        location = diagnostic.source_file or "discovery"
        if diagnostic.json_path:
            location += diagnostic.json_path
        rendered = "{}: {} ({})".format(diagnostic.severity, diagnostic.message, location)
        if rendered not in seen:
            seen.add(rendered)
            visible.append(rendered)
    return visible


def merge_response_payload(result=None, error=None):
    """Merge an optional result and request error into one response."""
    payload = {} if result is None else dict(result)
    if error is not None:
        if not isinstance(error, PerformRequestError):
            raise TypeError("error must be a PerformRequestError")
        payload.update(error_payload(error.status, error.message, error.alternatives))
        if error.diagnostics:
            payload["diagnostics"] = list(error.diagnostics)
    return payload


def response_payload(catalog, result=None, error=None):
    """Build one minimal response from a catalog result or request error."""
    if not isinstance(catalog, ActionCatalog):
        raise TypeError("catalog must be an ActionCatalog")
    payload = merge_response_payload(result=result, error=error)
    diagnostics = list(payload.get("diagnostics", []))
    for diagnostic in diagnostic_strings(catalog):
        if diagnostic not in diagnostics:
            diagnostics.append(diagnostic)
    if diagnostics:
        payload["diagnostics"] = diagnostics
    return payload


__all__ = (
    "compact_json",
    "diagnostic_strings",
    "error_exit_code",
    "error_payload",
    "merge_response_payload",
    "response_payload",
)
