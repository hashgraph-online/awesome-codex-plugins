#!/usr/bin/env python3
"""Export captured, read-only Rewst GraphQL requests into a private directory.

The request manifest deliberately contains queries and non-secret variables only.
An appSession is supplied at runtime through a chosen environment variable or a
hidden prompt; it is never written to disk or included in diagnostics.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
import re
import stat
import sys
import time
import urllib.error
import urllib.request
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import urlsplit


MAX_RESPONSE_BYTES = 100 * 1024 * 1024
MAX_PAGES = 10_000
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_RETRIES = 2
NAME_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
VARIABLE_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
PATH_SEGMENT_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")

Transport = Callable[
    [str, dict[str, str], bytes, float], tuple[int, Mapping[str, str], bytes]
]


class ValidationError(ValueError):
    """The supplied manifest or CLI options are unsafe or unsupported."""


class ExtractionError(RuntimeError):
    """A request could not be completed without exposing response details."""


@dataclass(frozen=True)
class Pagination:
    limit_variable: str
    offset_variable: str
    page_size: int


@dataclass(frozen=True)
class RequestDefinition:
    name: str
    query: str
    operation_name: str | None
    variables: dict[str, Any]
    result_path: tuple[str, ...]
    pagination: Pagination | None
    org_references: Mapping[str, Any] | None


@dataclass(frozen=True)
class RequestManifest:
    requests: tuple[RequestDefinition, ...]


def validate_endpoint(value: str) -> str:
    """Accept a direct HTTPS endpoint with no embedded authority secrets."""
    try:
        parsed = urlsplit(value)
    except ValueError as error:
        raise ValidationError("endpoint is invalid") from error
    if parsed.scheme != "https" or not parsed.netloc or parsed.hostname is None:
        raise ValidationError("endpoint must be an absolute HTTPS URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValidationError("endpoint must not contain credentials")
    if parsed.query or parsed.fragment:
        raise ValidationError("endpoint must not contain query or fragment data")
    try:
        parsed.port
    except ValueError as error:
        raise ValidationError("endpoint has an invalid port") from error
    if any(character.isspace() for character in value):
        raise ValidationError("endpoint must not contain whitespace")
    return value


def _graphql_tokens(document: str) -> list[str]:
    """Tokenize enough GraphQL syntax to identify operation definitions safely."""
    tokens: list[str] = []
    index = 0
    length = len(document)
    while index < length:
        character = document[index]
        if character in " \t\n\r,":
            index += 1
            continue
        if character.isspace():
            raise ValidationError("GraphQL document contains unsupported whitespace")
        if character == "#":
            index += 1
            while index < length and document[index] not in "\r\n":
                index += 1
            continue
        if document.startswith('"""', index):
            end = index + 3
            while end < length:
                if document.startswith('"""', end) and document[end - 1] != "\\":
                    index = end + 3
                    break
                end += 1
            else:
                raise ValidationError(
                    "GraphQL document has an unterminated block string"
                )
            continue
        if character == '"':
            index += 1
            while index < length:
                if document[index] == "\\":
                    index += 2
                    continue
                if document[index] == '"':
                    index += 1
                    break
                index += 1
            else:
                raise ValidationError("GraphQL document has an unterminated string")
            continue
        if character.isalpha() or character == "_":
            end = index + 1
            while end < length and (document[end].isalnum() or document[end] == "_"):
                end += 1
            tokens.append(document[index:end])
            index = end
            continue
        tokens.append(character)
        index += 1
    return tokens


def _skip_selection(tokens: list[str], index: int) -> int:
    if index >= len(tokens) or tokens[index] != "{":
        raise ValidationError("GraphQL operation has no selection set")
    depth = 0
    while index < len(tokens):
        if tokens[index] == "{":
            depth += 1
        elif tokens[index] == "}":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    raise ValidationError("GraphQL document has an unterminated selection set")


def _selection_start(tokens: list[str], index: int) -> int:
    parentheses = brackets = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "(":
            parentheses += 1
        elif token == ")":
            parentheses -= 1
        elif token == "[":
            brackets += 1
        elif token == "]":
            brackets -= 1
        elif token == "{" and not parentheses and not brackets:
            return index
        index += 1
    raise ValidationError("GraphQL operation has no selection set")


def _declared_variables(tokens: list[str]) -> set[str]:
    if not tokens or tokens[0] != "query":
        return set()
    selection = _selection_start(tokens, 1)
    return {
        tokens[index + 1]
        for index in range(1, selection - 1)
        if tokens[index] == "$" and VARIABLE_PATTERN.fullmatch(tokens[index + 1])
    }


def validate_read_only_query(query: str) -> set[str]:
    tokens = _graphql_tokens(query)
    if not tokens:
        raise ValidationError("GraphQL document is empty")
    if tokens[0] not in {"{", "query"}:
        raise ValidationError("only read-only query operations are supported")
    variables = _declared_variables(tokens)
    index = (
        _skip_selection(tokens, 0)
        if tokens[0] == "{"
        else _skip_selection(tokens, _selection_start(tokens, 1))
    )
    while index < len(tokens):
        if tokens[index] != "fragment":
            raise ValidationError(
                "GraphQL document must contain exactly one read-only query operation"
            )
        index = _skip_selection(tokens, _selection_start(tokens, index + 1))
    if tokens[0] == "{" and variables:
        raise ValidationError("shorthand query cannot declare variables")
    return variables


def _require_mapping(value: Any, message: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(message)
    return value


def _validate_json_value(value: Any, message: str) -> None:
    try:
        json.dumps(value, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValidationError(message) from error


def validate_manifest(raw_manifest: Any) -> RequestManifest:
    """Validate the credential-free JSON request manifest before any I/O."""
    root = _require_mapping(raw_manifest, "manifest must be a JSON object")
    if root.get("version") != 1:
        raise ValidationError("manifest version must be 1")
    raw_requests = root.get("requests")
    if not isinstance(raw_requests, list) or not raw_requests:
        raise ValidationError("manifest requests must be a non-empty array")

    parsed: list[RequestDefinition] = []
    names: set[str] = set()
    for item in raw_requests:
        request = _require_mapping(item, "each request must be a JSON object")
        allowed = {
            "name",
            "query",
            "operation_name",
            "variables",
            "result_path",
            "pagination",
            "org_references",
        }
        unknown = set(request) - allowed
        if unknown:
            raise ValidationError("request has unsupported fields")
        name = request.get("name")
        if (
            not isinstance(name, str)
            or not NAME_PATTERN.fullmatch(name)
            or name in names
            or name == "summary"
        ):
            raise ValidationError("request names must be unique safe file names")
        names.add(name)
        query = request.get("query")
        if not isinstance(query, str):
            raise ValidationError("request query must be a string")
        declared_variables = validate_read_only_query(query)
        operation_name = request.get("operation_name")
        if operation_name is not None and (
            not isinstance(operation_name, str)
            or not VARIABLE_PATTERN.fullmatch(operation_name)
        ):
            raise ValidationError("request operation_name is invalid")
        variables = request.get("variables", {})
        if not isinstance(variables, dict):
            raise ValidationError("request variables must be an object")
        if set(variables) - declared_variables:
            raise ValidationError(
                "request variables must match declared query variables"
            )
        _validate_json_value(variables, "request variables must be valid JSON values")
        result_path = request.get("result_path")
        if not isinstance(result_path, str):
            raise ValidationError("request result_path must be a dot-separated string")
        path_parts = tuple(result_path.split("."))
        if (
            not path_parts
            or path_parts[0] != "data"
            or not all(PATH_SEGMENT_PATTERN.fullmatch(part) for part in path_parts)
        ):
            raise ValidationError(
                "request result_path must start with data and contain field names"
            )

        pagination = None
        if "pagination" in request:
            raw_pagination = _require_mapping(
                request["pagination"], "pagination must be an object"
            )
            if set(raw_pagination) != {
                "limit_variable",
                "offset_variable",
                "page_size",
            }:
                raise ValidationError(
                    "pagination must contain limit_variable, offset_variable, and page_size"
                )
            limit_variable = raw_pagination.get("limit_variable")
            offset_variable = raw_pagination.get("offset_variable")
            page_size = raw_pagination.get("page_size")
            if not isinstance(limit_variable, str) or not VARIABLE_PATTERN.fullmatch(
                limit_variable
            ):
                raise ValidationError("pagination limit_variable is invalid")
            if not isinstance(offset_variable, str) or not VARIABLE_PATTERN.fullmatch(
                offset_variable
            ):
                raise ValidationError("pagination offset_variable is invalid")
            if (
                limit_variable == offset_variable
                or not isinstance(page_size, int)
                or isinstance(page_size, bool)
                or not 1 <= page_size <= 1000
            ):
                raise ValidationError("pagination fields are invalid")
            if {limit_variable, offset_variable} - declared_variables:
                raise ValidationError(
                    "pagination variables must be declared by the query"
                )
            existing_offset = variables.get(offset_variable, 0)
            if (
                not isinstance(existing_offset, int)
                or isinstance(existing_offset, bool)
                or existing_offset < 0
            ):
                raise ValidationError(
                    "pagination offset variable must be a non-negative integer"
                )
            pagination = Pagination(limit_variable, offset_variable, page_size)

        org_references = request.get("org_references")
        if org_references is not None:
            if not isinstance(org_references, dict):
                raise ValidationError("org_references must be an object")
            _validate_json_value(
                org_references, "org_references must contain valid JSON values"
            )
        parsed.append(
            RequestDefinition(
                name,
                query,
                operation_name,
                dict(variables),
                path_parts,
                pagination,
                org_references,
            )
        )
    return RequestManifest(tuple(parsed))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, request: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        return None


def default_transport(
    endpoint: str, headers: dict[str, str], payload: bytes, timeout: float
) -> tuple[int, Mapping[str, str], bytes]:
    """POST once, keeping redirect responses visible to the caller."""
    request = urllib.request.Request(
        endpoint, data=payload, headers=headers, method="POST"
    )
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
            return response.status, dict(response.headers.items()), body
    except urllib.error.HTTPError as error:
        body = error.read(MAX_RESPONSE_BYTES + 1)
        return error.code, dict(error.headers.items()) if error.headers else {}, body
    except urllib.error.URLError as error:
        raise ExtractionError("network request failed") from error


def _response_json(
    endpoint: str,
    headers: dict[str, str],
    payload: bytes,
    timeout: float,
    transport: Transport,
    retries: int,
) -> Any:
    attempts = 0
    while True:
        attempts += 1
        try:
            status, _response_headers, body = transport(
                endpoint, headers, payload, timeout
            )
        except OSError as error:
            raise ExtractionError("network request failed") from error
        if len(body) > MAX_RESPONSE_BYTES:
            raise ExtractionError("response exceeded the size limit")
        if 300 <= status < 400:
            raise ExtractionError("redirect response rejected")
        if not 200 <= status < 300:
            if (status == 429 or 500 <= status < 600) and attempts <= retries:
                time.sleep(min(2 ** (attempts - 1), 4))
                continue
            raise ExtractionError(f"HTTP {status} after {attempts} attempts")
        try:
            response = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ExtractionError("response was not valid JSON") from error
        if not isinstance(response, dict):
            raise ExtractionError("response JSON must be an object")
        if response.get("errors"):
            raise ExtractionError("GraphQL error response")
        return response


def _result_at_path(response: Any, path: tuple[str, ...]) -> Any:
    current = response
    for part in path:
        if not isinstance(current, dict) or part not in current:
            raise ExtractionError("response did not contain the requested result_path")
        current = current[part]
    if current is None:
        raise ExtractionError("response result_path was null")
    return current


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def fetch_request(
    request: RequestDefinition,
    endpoint: str,
    token: str,
    transport: Transport | None = None,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    retries: int = DEFAULT_RETRIES,
) -> tuple[Any, int]:
    """Fetch one captured request, aggregating only an explicitly paginated list."""
    if transport is None:
        transport = default_transport
    headers = {
        "Cookie": f"appSession={token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload_body = {"query": request.query, "variables": request.variables}
    if request.operation_name:
        payload_body["operationName"] = request.operation_name
    if request.pagination is None:
        payload = _canonical_json(payload_body)
        return _result_at_path(
            _response_json(endpoint, headers, payload, timeout, transport, retries),
            request.result_path,
        ), 1

    records: list[Any] = []
    seen_pages: set[str] = set()
    seen_ids: set[tuple[type[Any], Any]] = set()
    variables = dict(request.variables)
    offset = variables.get(request.pagination.offset_variable, 0)
    for page_number in range(1, MAX_PAGES + 1):
        variables[request.pagination.limit_variable] = request.pagination.page_size
        variables[request.pagination.offset_variable] = offset
        page_payload = dict(payload_body)
        page_payload["variables"] = variables
        payload = _canonical_json(page_payload)
        page = _result_at_path(
            _response_json(endpoint, headers, payload, timeout, transport, retries),
            request.result_path,
        )
        if not isinstance(page, list):
            raise ExtractionError("paginated result_path did not resolve to a list")
        if not page:
            return records, page_number
        page_digest = hashlib.sha256(_canonical_json(page)).hexdigest()
        if page_digest in seen_pages:
            raise ExtractionError("pagination returned a repeated page")
        seen_pages.add(page_digest)
        for record in page:
            identifier = record.get("id") if isinstance(record, dict) else None
            if isinstance(identifier, (str, int)) and not isinstance(identifier, bool):
                key = (type(identifier), identifier)
                if key in seen_ids:
                    raise ExtractionError("pagination returned a duplicate id")
                seen_ids.add(key)
        records.extend(page)
        offset += len(page)
    raise ExtractionError("pagination exceeded the page limit")


def _reject_symlink_ancestors(path: Path) -> None:
    absolute = path.absolute()
    for ancestor in (absolute, *absolute.parents):
        try:
            mode = os.lstat(ancestor).st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise ValidationError("output path must not contain symlinks")


def create_private_output(path: Path) -> None:
    _reject_symlink_ancestors(path)
    if path.exists() or path.is_symlink():
        raise ValidationError("output directory must not already exist")
    parent = path.parent
    if not parent.is_dir():
        raise ValidationError("output parent directory does not exist")
    try:
        path.mkdir(mode=0o700)
        path.chmod(0o700)
    except OSError as error:
        raise ValidationError("could not create private output directory") from error


def write_private_json(output: Path, filename: str, value: Any) -> None:
    destination = output / filename
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(destination, flags, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(
                value,
                stream,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            stream.write("\n")
        destination.chmod(0o600)
    except OSError as error:
        raise ExtractionError("could not write private export file") from error


def _record_count(value: Any) -> int:
    return len(value) if isinstance(value, list) else 1


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--endpoint", required=True, help="direct Rewst GraphQL HTTPS endpoint"
    )
    parser.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help="credential-free request manifest JSON",
    )
    parser.add_argument(
        "--output", required=True, type=Path, help="new private output directory"
    )
    parser.add_argument(
        "--token-env", metavar="NAME", help="environment variable that holds appSession"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="per-request timeout in seconds (1-60)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help="retries for 429/5xx only (0-5)",
    )
    return parser.parse_args(argv)


def _token_from_runtime(args: argparse.Namespace, environ: Mapping[str, str]) -> str:
    if args.token_env:
        if not VARIABLE_PATTERN.fullmatch(args.token_env):
            raise ValidationError("token environment variable name is invalid")
        token = environ.get(args.token_env, "")
    else:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", getpass.GetPassWarning)
                token = getpass.getpass("Rewst appSession: ")
        except (getpass.GetPassWarning, EOFError, KeyboardInterrupt) as error:
            raise ValidationError(
                "hidden appSession prompt is unavailable; use --token-env"
            ) from error
    if not token:
        raise ValidationError("appSession was not provided")
    if any(character in token for character in "\r\n;"):
        raise ValidationError("appSession contains an unsafe cookie character")
    return token


def _summary_entry(
    request: RequestDefinition, status: str, count: int, pages: int, digest: str | None
) -> dict[str, Any]:
    entry = {
        "name": request.name,
        "status": status,
        "count": count,
        "pages": pages,
        "sha256": digest,
    }
    if request.org_references is not None:
        entry["org_references"] = request.org_references
    return entry


def main(
    argv: Sequence[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    print_fn: Callable[[str], None] = print,
) -> int:
    """Run the exporter. Return 0 only when every requested collection completed."""
    try:
        args = parse_args(argv)
        if not 1 <= args.timeout <= 60:
            raise ValidationError("timeout must be between 1 and 60 seconds")
        if not 0 <= args.retries <= 5:
            raise ValidationError("retries must be between 0 and 5")
        endpoint = validate_endpoint(args.endpoint)
        try:
            manifest_bytes = args.manifest.read_bytes()
            raw_manifest = json.loads(manifest_bytes.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValidationError("manifest could not be read as JSON") from error
        request_manifest = validate_manifest(raw_manifest)
        create_private_output(args.output)
        token = _token_from_runtime(args, os.environ if environ is None else environ)
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    except (ValidationError, ExtractionError) as error:
        print_fn(f"error: {error}")
        return 2

    summary: list[dict[str, Any]] = []
    failures = 0
    halted = False
    for request in request_manifest.requests:
        if halted:
            failure = {
                "status": "failed",
                "count": 0,
                "pages": 0,
                "sha256": None,
                "error": "not attempted after authentication or authorization failure",
            }
            write_private_json(args.output, f"{request.name}.json", failure)
            summary.append(_summary_entry(request, "failed", 0, 0, None))
            continue
        try:
            value, pages = fetch_request(
                request, endpoint, token, timeout=args.timeout, retries=args.retries
            )
            digest = hashlib.sha256(_canonical_json(value)).hexdigest()
            result = {
                "status": "complete",
                "count": _record_count(value),
                "pages": pages,
                "sha256": digest,
                "data": value,
            }
            write_private_json(args.output, f"{request.name}.json", result)
            summary.append(
                _summary_entry(request, "complete", result["count"], pages, digest)
            )
            print_fn(
                f"{request.name}: complete ({result['count']} records, sha256 {digest})"
            )
        except (ValidationError, ExtractionError) as error:
            failures += 1
            failure = {
                "status": "failed",
                "count": 0,
                "pages": 0,
                "sha256": None,
                "error": str(error),
            }
            try:
                write_private_json(args.output, f"{request.name}.json", failure)
            except ExtractionError:
                print_fn(f"{request.name}: failed (could not write status)")
            else:
                print_fn(f"{request.name}: failed")
            summary.append(_summary_entry(request, "failed", 0, 0, None))
            halted = str(error).startswith(("HTTP 401", "HTTP 403"))
    try:
        write_private_json(
            args.output,
            "summary.json",
            {
                "version": 1,
                "coverage": "requested_queries_only",
                "source_endpoint": endpoint,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "manifest_sha256": manifest_sha256,
                "collections": summary,
            },
        )
    except ExtractionError:
        print_fn("error: could not write export summary")
        return 2
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
