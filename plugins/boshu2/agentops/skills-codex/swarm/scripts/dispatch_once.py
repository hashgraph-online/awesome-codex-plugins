#!/usr/bin/env python3
"""One-shot dispatch for explicit packets with disjoint write scopes."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from pathlib import PurePosixPath
from typing import Any


def _packet_id(packet: Mapping[str, Any]) -> str:
    value = packet.get("packet_id", packet.get("id"))
    if not isinstance(value, str) or not value.strip():
        raise ValueError("each packet needs a nonempty packet_id")
    return value


def _includes(packet: Mapping[str, Any]) -> tuple[str, ...]:
    scope = packet.get("write_scope")
    if not isinstance(scope, Mapping):
        raise ValueError(f"{_packet_id(packet)}: write_scope must be an object")
    # `exclude` is not honored by the lexical disjointness proof below. Admitting
    # it silently would let a packet look narrower than it dispatches, so reject
    # its presence rather than ignore it.
    if scope.get("exclude"):
        raise ValueError(
            f"{_packet_id(packet)}: write_scope.exclude is not honored by the "
            "disjointness proof — remove it or narrow include instead"
        )
    raw = scope.get("include")
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{_packet_id(packet)}: write_scope.include must be nonempty")
    normalized: list[str] = []
    for value in raw:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{_packet_id(packet)}: include paths must be nonempty strings")
        path = PurePosixPath(value.replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"{_packet_id(packet)}: include path must be workspace-relative: {value}")
        normalized.append(path.as_posix().rstrip("/"))
    return tuple(normalized)


def _overlap(left: str, right: str) -> bool:
    """Conservatively decide whether two include patterns may intersect.

    Literal sibling paths are provably disjoint.  For globs, the literal path
    prefix before the first wildcard must itself be disjoint; otherwise the
    adapter rejects the batch instead of guessing about a shared write surface.
    """

    def literal_prefix(pattern: str) -> str:
        parts: list[str] = []
        for part in PurePosixPath(pattern).parts:
            if any(character in part for character in "*?["):
                break
            parts.append(part)
        return PurePosixPath(*parts).as_posix() if parts else "."

    # Case-fold the comparison so scopes differing only by case ("src/Auth" vs
    # "src/auth") are treated as a possible collision. On a case-insensitive
    # filesystem they ARE the same path; on a case-sensitive one this only
    # over-rejects, matching this module's reject-when-uncertain stance. Paths
    # must already be workspace-relative and canonical (symlink-resolved): the
    # check is lexical and cannot detect a symlink alias to a shared target.
    left_prefix = literal_prefix(left).casefold()
    right_prefix = literal_prefix(right).casefold()
    if left_prefix == "." or right_prefix == ".":
        return True
    return (
        left_prefix == right_prefix
        or left_prefix.startswith(right_prefix + "/")
        or right_prefix.startswith(left_prefix + "/")
    )


def dispatch_once(
    packets: Iterable[Mapping[str, Any]],
    executor: Callable[[Mapping[str, Any]], Any],
) -> list[dict[str, Any]]:
    """Validate the complete batch, then call ``executor`` once per packet.

    Results preserve input order. Executor exceptions are factual per-packet
    errors; they are returned and never retried.
    """

    batch = list(packets)
    identities: list[str] = []
    scopes: list[tuple[str, ...]] = []
    for packet in batch:
        if not isinstance(packet, Mapping):
            raise ValueError("each packet must be an object")
        identity = _packet_id(packet)
        if identity in identities:
            raise ValueError(f"duplicate packet_id: {identity}")
        identities.append(identity)
        scopes.append(_includes(packet))

    for left_index, left_scope in enumerate(scopes):
        for right_index in range(left_index + 1, len(scopes)):
            for left in left_scope:
                for right in scopes[right_index]:
                    if _overlap(left, right):
                        raise ValueError(
                            f"write scopes overlap: {identities[left_index]}:{left} and "
                            f"{identities[right_index]}:{right}"
                        )

    results: list[dict[str, Any]] = []
    for identity, packet in zip(identities, batch, strict=True):
        try:
            results.append({"packet_id": identity, "result": executor(packet)})
        except Exception as exc:  # The adapter reports executor evidence verbatim.
            results.append(
                {
                    "packet_id": identity,
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                }
            )
    return results
