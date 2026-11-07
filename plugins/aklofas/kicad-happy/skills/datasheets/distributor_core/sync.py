"""One datasheet-sync driver over the provider adapters.

``sync_datasheets(provider, ...)`` takes a provider module (``provider_<p>.py``) that supplies
the identifier sets (``ID_KEYS``, ``KEY_PRIORITY``, ``SEARCH_KEY``), the console
``LABELS``, ``DEFAULT_DELAY``, ``RENAME_PRESENT``, ``FAILED_DETAIL_WITH_URL`` and the hooks
``preflight``, ``authenticate``, ``sync_one_part`` and ``report_tail``. The driver reads the
parts (analyzer BOM or MPN list) as one part per manifest key, decides which need a download,
fetches them serially or on a thread pool, records each outcome in ``manifest.json`` and prints
the summary. With ``as_json`` every return, an error included, is printed as JSON on stdout;
progress and errors go to stderr.

A ``not_found`` or ``failed`` whose search or download failed in transport
(``distributor_core.download`` records it) is stored as ``error`` so the next run retries it, and
any result but ``ok`` keeps an ``ok`` entry whose file is still on disk. A failure names
the distributors that gave it (``failed_providers``); only those skip it on the next run.

Imports ``distributor_core.inputs``/``manifest``/``download`` and the stdlib only; never a provider.
"""

import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from distributor_core.download import take_transport_failure
from distributor_core.inputs import (
    _SKIP_TYPES,
    _str,
    get_analyzer_output,
    extract_parts,
    load_mpn_list,
)
from distributor_core.manifest import (
    friendly_filename,
    MANIFEST_FILENAME,
    load_index,
    manifest_file_path,
    save_index,
)


def _outage_entry(result: dict, previous: dict, out_dir: Path) -> tuple[dict, dict]:
    """(entry to store, result to report) for one part. A ``not_found`` or ``failed`` caused by
    a network failure, a rate limit or refused access is not an answer: report it as ``error``
    (not a skipped previous failure, so the next run retries), with the distributor's own message
    after it. Any result but ``ok`` keeps a previous ``ok`` entry whose file is still on disk:
    one distributor not listing the part, or listing it without a datasheet, does not void the
    datasheet already found."""
    outage = take_transport_failure()
    if outage is not None and result.get("status") in ("not_found", "failed"):
        said = result.get("error")
        result = {**result, "status": "error",
                  "error": f"{outage}; distributor said: {said}" if said else outage}
    if result.get("status") == "ok":
        return result, result
    prev_file = manifest_file_path(out_dir, previous.get("file", ""))
    if previous.get("status") == "ok" and prev_file is not None and prev_file.is_file():
        return previous, result
    return result, result


# A distributor's answer without a datasheet; only the distributors that gave it skip the part
# on the next run.
_FAILED_STATUSES = ("failed", "not_found", "no_datasheet")


def _failed_providers(entry: dict) -> set[str] | None:
    """The distributors an entry's failure is recorded for, or None when the entry does not say
    (written before failures were recorded per distributor): every distributor retries it once."""
    names = entry.get("failed_providers")
    if not isinstance(names, list):
        return None
    return {n for n in names if isinstance(n, str)}


def _attributed(stored: dict, previous: dict, name: str) -> dict:
    """``stored`` with ``failed_providers`` when it is a failure: this distributor plus those
    that had already failed the part."""
    if stored.get("status") not in _FAILED_STATUSES:
        return stored
    prior = _failed_providers(previous) if previous.get("status") in _FAILED_STATUSES else None
    return {**stored, "failed_providers": sorted((prior or set()) | {name})}


def _part_key(part: dict, key_priority) -> str:
    """The manifest key: the MPN, else the first distributor number in ``key_priority``."""
    return part["mpn"] or next((part.get(k, "") for k in key_priority if part.get(k, "")), "")


def _coalesce(parts: list[dict], key_priority) -> list[dict]:
    """One part per manifest key, in BOM order, so a part on several BOM rows is fetched once.
    References are unioned in BOM order; every other field takes the first non-empty value. The
    MPN counts as read from the Value only when no row has it as a property (strict identity).
    A distributor number that differs between the rows is noted on stderr: only the first is used."""
    merged: dict[str, dict] = {}
    dropped: dict[tuple[str, str], list[str]] = {}
    for part in parts:
        key = _part_key(part, key_priority)
        first = merged.get(key)
        if first is None:
            merged[key] = {**part, "_key": key, "references": list(part["references"])}
            continue
        first["references"] += [r for r in part["references"] if r not in first["references"]]
        for name in key_priority:
            value = part.get(name, "")
            if value and first.get(name) and value != first[name]:
                seen = dropped.setdefault((key, name), [])
                if value not in seen:
                    seen.append(value)
        for name, value in part.items():
            if name not in ("references", "mpn", "mpn_source") and value and not first.get(name):
                first[name] = value
        if part["mpn"] and (not first["mpn"] or part.get("mpn_source") != "value"):
            first["mpn"] = part["mpn"]
            first["mpn_source"] = part.get("mpn_source", "")
    for (key, name), values in dropped.items():
        print(f"Note: {key} is on several BOM rows with different {name} numbers; using "
              f"{merged[key][name]}, not {', '.join(values)}", file=sys.stderr)
    return list(merged.values())


def _error(message: str, as_json: bool) -> dict:
    """An error return, reported on stderr and, with ``as_json``, as JSON on stdout."""
    print(f"Error: {message}", file=sys.stderr)
    result = {"error": message}
    if as_json:
        json.dump(result, sys.stdout, indent=2)
    return result


class _Run:
    """State shared by the fetch workers: the manifest, its path and the outcome tallies."""

    def __init__(self, *, provider_name, out_dir, index, index_path, source, total):
        self.provider_name = provider_name
        self.out_dir = out_dir
        self.index = index
        self.index_path = index_path
        self.source = source
        self.total = total
        self.lock = threading.Lock()
        self.counter = 0
        self.downloaded = []
        self.failed = []
        self.kept_errors = {}  # part key -> error, for a failure that kept the previous ok entry
        self.warnings = []  # parts whose verification says the datasheet is probably wrong


def _same_file(out_dir: Path, a: object, b: object) -> bool:
    """Whether two manifest ``file`` values name one file: the same physical file when both exist
    (a case-insensitive volume, ``./x.pdf``), else the same name after normalising case and
    separators."""
    if not isinstance(a, str) or not isinstance(b, str):
        return False
    if a == b:
        return True
    try:
        return os.path.samefile(out_dir / a, out_dir / b)
    except OSError:
        return os.path.normcase(os.path.normpath(a)) == os.path.normcase(os.path.normpath(b))


def _replaced_file(run, part_key: str, previous: dict, stored: dict) -> Path | None:
    """The PDF a replaced ``ok`` entry named, when nothing names it any more: not the new entry
    and not another entry."""
    old = manifest_file_path(run.out_dir, previous.get("file", ""))
    if old is None or not old.is_file():
        return None
    name = previous.get("file")
    if _same_file(run.out_dir, stored.get("file"), name) or any(
            k != part_key and _same_file(run.out_dir, e.get("file"), name)
            for k, e in run.index.get("parts", {}).items() if isinstance(e, dict)):
        return None
    return old


def _record(run, part, outcome) -> None:
    """Store one part's outcome in the manifest, count it, print its progress line and save the
    index. Callers hold ``run.lock`` when several workers run. It must run on the thread that
    fetched the part: the transport failure it reads is recorded per thread."""
    part_key = part["_key"]
    previous = run.index.get("parts", {}).get(part_key, {})
    stored, result = _outage_entry(outcome, previous, run.out_dir)
    if stored is result:
        stored = result = _attributed(result, previous, run.provider_name)
    run.index.setdefault("parts", {})[part_key] = stored
    if stored is not result:
        run.kept_errors[part_key] = result["error"]
        replaced = None
    else:
        replaced = (_replaced_file(run, part_key, previous, stored)
                    if previous.get("status") == "ok" else None)

    if result["status"] == "ok":
        run.downloaded.append(part_key)
        vconf = result.get("verification", "")
        vmark = ""
        if vconf == "wrong":
            vmark = " ⚠ WRONG DATASHEET?"
            run.warnings.append(part_key)
        elif vconf == "unverified":
            vmark = " (unverified)"
        print(f"  OK: {result['file']} ({result['size_bytes']:,} bytes){vmark}", file=sys.stderr)
    else:
        run.failed.append(part_key)
        print(f"  {result['status'].upper()}: {result.get('error', '')}", file=sys.stderr)

    run.index["schematic"] = run.source
    run.index["last_sync"] = datetime.now(timezone.utc).isoformat()
    save_index(run.index_path, run.index)
    # Removed only after the manifest no longer names it
    if replaced is not None:
        try:
            replaced.unlink()
        except OSError as exc:
            print(f"Warning: cannot remove {replaced}: {exc}", file=sys.stderr)


def sync_datasheets(
    provider,
    *,
    input_path: str | None = None,
    output_dir: str | None = None,
    force: bool = False,
    force_all: bool = False,
    delay: float | None = None,
    parallel: int = 1,
    dry_run: bool = False,
    as_json: bool = False,
    mpn_list: str | None = None,
    **provider_kwargs,
) -> dict:
    """Main sync function. Returns summary dict."""
    delay = provider.DEFAULT_DELAY if delay is None else delay
    if input_path is None and mpn_list is None:
        return _error("Must provide either input_path or mpn_list", as_json)
    if input_path is not None and mpn_list is not None:
        return _error("Cannot provide both input_path and mpn_list", as_json)

    pre = provider.preflight(**provider_kwargs)
    if "error" in pre:
        return _error(pre["error"], as_json)
    ctx = pre.get("ctx")

    # Determine output directory
    if output_dir:
        out_dir = Path(output_dir)
    elif input_path:
        out_dir = Path(input_path).resolve().parent / "datasheets"
    else:
        # MPN-list mode without explicit --output: use cwd/datasheets
        out_dir = Path.cwd() / "datasheets"
    # A datasheets/ link found in the project would send every write to its target;
    # only an explicit --output may point elsewhere.
    if not output_dir and out_dir.is_symlink():
        return _error(f"{out_dir} is a symlink; pass --output to write datasheets there", as_json)

    # Source parts: either analyzer BOM or plain MPN list. Read before the output directory is
    # created, so an input error leaves nothing behind.
    if mpn_list:
        mpn_list_path = Path(mpn_list).resolve()
        print(f"Loading MPNs from {mpn_list_path.name}...", file=sys.stderr)
        try:
            mpns = load_mpn_list(mpn_list_path, id_keys=provider.ID_KEYS)
        except (OSError, ValueError) as e:
            return _error(f"cannot read {mpn_list_path}: {e}", as_json)
        parts = _coalesce(mpns, provider.KEY_PRIORITY)
        print(f"Loaded {len(parts)} unique MPNs", file=sys.stderr)
        skipped_no_id = 0
    else:
        resolved_input = Path(input_path).resolve()
        print(f"Analyzing {resolved_input.name}...", file=sys.stderr)
        analyzer_output = get_analyzer_output(resolved_input)
        if analyzer_output is None:
            return _error("Failed to analyze schematic", as_json)

        # Extract parts with real MPNs
        # A provider searches with an MPN or its own part number; another distributor's number
        # is no query for it.
        parts = [p for p in extract_parts(analyzer_output, id_keys=provider.ID_KEYS,
                                          search_key=provider.SEARCH_KEY)
                 if p["mpn"] or p.get(provider.SEARCH_KEY)]
        eligible = sum(1 for e in analyzer_output.get("bom", [])
                       if not e.get("dnp") and _str(e.get("type")) not in _SKIP_TYPES)
        skipped_no_id = eligible - len(parts)
        parts = _coalesce(parts, provider.KEY_PRIORITY)

        print(provider.LABELS["found"].format(n=len(parts), k=skipped_no_id), file=sys.stderr)

    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / MANIFEST_FILENAME
    try:
        index = load_index(index_path)
    except ValueError as exc:
        return _error(str(exc), as_json)

    # Determine what needs processing
    to_download = []
    already_present = []
    skipped_failed = []

    for part in parts:
        part_key = part["_key"]
        existing = index.get("parts", {}).get(part_key, {})
        status = existing.get("status", "")

        if status == "ok":
            old_file = existing.get("file", "")
            old_path = manifest_file_path(out_dir, old_file)
            if old_path is None and old_file:
                print(f"Warning: manifest entry {part_key} names a file outside {out_dir}; ignored",
                      file=sys.stderr)
            # Verify file still exists
            if old_path is not None and old_path.exists():
                if not force_all:
                    # Rename to friendly filename if the old name was plain MPN
                    if provider.RENAME_PRESENT and not dry_run:
                        desc = existing.get("description", "") or part.get("description", "")
                        mfg = existing.get("manufacturer", "") or part.get("manufacturer", "")
                        new_file = friendly_filename(part_key, desc, mfg) + ".pdf"
                        if new_file != old_file and not (out_dir / new_file).exists():
                            old_path.rename(out_dir / new_file)
                            existing["file"] = new_file
                            print(f"  Renamed: {old_file} -> {new_file}", file=sys.stderr)
                    already_present.append(part_key)
                    existing["references"] = part["references"]
                    continue
            # File missing — re-download

        if status in _FAILED_STATUSES and not (force or force_all):
            failed_for = _failed_providers(existing)
            if failed_for is not None and provider.NAME in failed_for:
                skipped_failed.append(part_key)
                continue

        to_download.append(part)

    if dry_run:
        summary = {
            "would_download": [p["_key"] for p in to_download],
            "already_present": already_present,
            "skipped_previous_failures": skipped_failed,
            provider.LABELS["skipped_key"]: skipped_no_id,
        }
        if as_json:
            json.dump(summary, sys.stdout, indent=2)
        else:
            print(f"\nDry run — would download {len(to_download)} datasheets:")
            for p in to_download:
                print(f"  {p['_key']} ({p['manufacturer'] or 'unknown mfg'})")
            print(f"Already present: {len(already_present)}")
            print(f"Skipped (previous failures): {len(skipped_failed)}")
            print(provider.LABELS["dry_skipped"].format(k=skipped_no_id))
        return summary

    if not to_download:
        msg = f"All {len(already_present)} datasheets up to date."
        if skipped_failed:
            msg += f" {len(skipped_failed)} previous failures (use --force to retry)."
        print(msg, file=sys.stderr)
        # Still update the manifest (references may have changed)
        index["schematic"] = str(mpn_list or input_path)
        index["last_sync"] = datetime.now(timezone.utc).isoformat()
        save_index(index_path, index)
        summary = {"downloaded": 0, "already_present": len(already_present),
                   "failed": len(skipped_failed)}
        if as_json:
            json.dump(summary, sys.stdout, indent=2)
        return summary

    # Get OAuth token
    auth = provider.authenticate()
    if "error" in auth:
        return _error(auth["error"], as_json)
    if auth.get("ctx") is not None:
        ctx = auth["ctx"]

    # Process each part
    run = _Run(provider_name=provider.NAME, out_dir=out_dir, index=index, index_path=index_path,
               source=str(mpn_list or input_path), total=len(to_download))

    def _fetch(part):
        take_transport_failure()
        try:
            return provider.sync_one_part(part, out_dir, delay, ctx)
        except Exception as exc:
            return {"manufacturer": part.get("manufacturer", ""),
                    "description": part.get("description", ""),
                    "value": part.get("value", ""), "references": part["references"],
                    "status": "error",
                    "error": f"{provider.NAME} sync failed: {type(exc).__name__}: {exc}",
                    "last_attempt": datetime.now(timezone.utc).isoformat()}

    if parallel > 1:
        def _process_part(part):
            with run.lock:
                run.counter += 1
                n = run.counter
            print(f"[{n}/{run.total}] {part['_key']}", file=sys.stderr)
            outcome = _fetch(part)
            with run.lock:
                _record(run, part, outcome)

        with ThreadPoolExecutor(max_workers=parallel) as executor:
            for _ in executor.map(_process_part, to_download):
                pass
    else:
        for i, part in enumerate(to_download):
            print(f"[{i+1}/{run.total}] {part['_key']}", file=sys.stderr)
            _record(run, part, _fetch(part))

    downloaded, failed = run.downloaded, run.failed
    kept_errors, warnings = run.kept_errors, run.warnings

    # Summary
    summary = {
        "downloaded": len(downloaded),
        "already_present": len(already_present),
        "failed": len(failed),
        "verification_warnings": len(warnings),
        "skipped_previous_failures": len(skipped_failed),
        provider.LABELS["skipped_key"]: skipped_no_id,
        provider.LABELS["total_key"]: len(parts),
        "output_dir": str(out_dir),
        "index_path": str(index_path),
    }

    if as_json:
        json.dump(summary, sys.stdout, indent=2)
    else:
        print(f"\nDatasheet sync complete:", file=sys.stderr)
        print(f"  Downloaded: {len(downloaded)}", file=sys.stderr)
        if downloaded:
            for m in downloaded:
                print(f"    {m}", file=sys.stderr)
        if warnings:
            print(f"  Verification warnings: {len(warnings)}", file=sys.stderr)
            for m in warnings:
                entry = index["parts"].get(m, {})
                detail = entry.get("verification_details", "")
                print(f"    {m}: {detail}", file=sys.stderr)
        print(f"  Already present: {len(already_present)}", file=sys.stderr)
        print(f"  Failed: {len(failed)}", file=sys.stderr)
        if failed:
            for m in failed:
                entry = index["parts"].get(m, {})
                if m in kept_errors:
                    print(f"    {m} — {kept_errors[m]}", file=sys.stderr)
                    continue
                if provider.FAILED_DETAIL_WITH_URL:
                    url = entry.get("datasheet_url", "")
                    err = entry.get("error", "")
                    detail = f" — {url}" if url else f" — {err}"
                    print(f"    {m}{detail}", file=sys.stderr)
                else:
                    err = entry.get("error", "")
                    print(f"    {m} — {err}", file=sys.stderr)
        if skipped_failed:
            print(f"  Skipped (previous failures, use --force): "
                  f"{len(skipped_failed)}", file=sys.stderr)
        print(provider.LABELS["summary_skipped"].format(k=skipped_no_id), file=sys.stderr)
        print(f"  Output: {out_dir}/", file=sys.stderr)
        provider.report_tail(out_dir, downloaded, already_present, failed)

    return summary
