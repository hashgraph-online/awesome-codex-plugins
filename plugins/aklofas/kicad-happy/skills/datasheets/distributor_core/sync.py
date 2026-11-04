"""One datasheet-sync driver over the provider adapters.

``sync_datasheets(provider, ...)`` is the DigiKey ``sync_datasheets`` body of
935b429 verbatim, with exactly these thirteen substitutions (and nothing else);
the provider module (``provider_<p>.py``) arrives as the first argument:

  1. ``delay`` defaults to ``provider.DEFAULT_DELAY`` (first statement).
  2. ``provider.preflight(**provider_kwargs)`` after the input validation and
     before the output-dir block (where element14 checked its API key); an
     ``error`` returns early, otherwise its ``ctx`` is kept.
  3. ``load_mpn_list`` / ``extract_parts`` take ``id_keys=provider.ID_KEYS``.
  4. The no-identifier count tests ``provider.SKIPPED_COUNTS_IDS`` (an empty
     tuple counts every part without a real MPN — the Mouser rule).
  5. The "Found ..." line is ``provider.LABELS["found"]``.
  6. The manifest key is the MPN, else the first non-empty
     ``provider.KEY_PRIORITY`` identifier.
  7. The already-present friendly rename runs only if ``provider.RENAME_PRESENT``.
  8. The dry-run summary key / line are ``LABELS["skipped_key"]`` /
     ``LABELS["dry_skipped"]``.
  9. ``provider.authenticate()`` after the "nothing to download" early return;
     an ``error`` returns early; only a non-None ``ctx`` replaces preflight's.
 10. ``provider.sync_one_part(part, out_dir, index, delay, ctx)`` in both the
     parallel and the serial branch (the dead DigiKey not_found ``pass`` block
     is kept verbatim).
 11. The summary keys ``LABELS["skipped_key"]`` / ``LABELS["total_key"]``.
 12. The failed-list line: with the datasheet URL if
     ``provider.FAILED_DETAIL_WITH_URL``, else ``<key> — <error>``.
 13. The closing skipped line is ``LABELS["summary_skipped"]``; the DigiKey
     tips became ``provider.report_tail(out_dir, downloaded, already_present, failed)``.

Later fixes: a ``not_found`` whose search failed in transport (``distributor_core.download``
records it) is stored as ``error`` so the next run retries it, and an ``ok`` entry whose file
is still on disk is kept.

Imports ``distributor_core.inputs``/``manifest``/``download`` and the stdlib only — never a provider.
"""

import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from distributor_core.download import take_transport_failure
from distributor_core.inputs import (
    _SKIP_TYPES,
    is_real_mpn,
    get_analyzer_output,
    extract_parts,
    load_mpn_list,
)
from distributor_core.manifest import (
    friendly_filename,
    MANIFEST_FILENAME,
    load_index,
    save_index,
)


def _outage_entry(result: dict, previous: dict, out_dir: Path) -> tuple[dict, dict]:
    """(entry to store, result to report) for one part. A ``not_found`` caused by a network
    failure, a rate limit or refused access is not an answer: report it as ``error`` (not a
    skipped previous failure, so the next run retries) and keep a previous ``ok`` entry whose
    file is still on disk."""
    outage = take_transport_failure()
    if outage is None or result.get("status") != "not_found":
        return result, result
    result = {**result, "status": "error", "error": outage}
    if previous.get("status") == "ok" and (out_dir / previous.get("file", "")).is_file():
        return previous, result
    return result, result


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
        return {"error": "Must provide either input_path or mpn_list"}
    if input_path is not None and mpn_list is not None:
        return {"error": "Cannot provide both input_path and mpn_list"}

    pre = provider.preflight(**provider_kwargs)
    if "error" in pre:
        return {"error": pre["error"]}
    ctx = pre.get("ctx")

    # Determine output directory
    if output_dir:
        out_dir = Path(output_dir)
    elif input_path:
        out_dir = Path(input_path).resolve().parent / "datasheets"
    else:
        # MPN-list mode without explicit --output: use cwd/datasheets
        out_dir = Path.cwd() / "datasheets"
    out_dir.mkdir(parents=True, exist_ok=True)

    index_path = out_dir / MANIFEST_FILENAME
    index = load_index(index_path)

    # Source parts: either analyzer BOM or plain MPN list
    if mpn_list:
        mpn_list_path = Path(mpn_list).resolve()
        print(f"Loading MPNs from {mpn_list_path.name}...", file=sys.stderr)
        parts = load_mpn_list(mpn_list_path, id_keys=provider.ID_KEYS)
        print(f"Loaded {len(parts)} unique MPNs", file=sys.stderr)
        skipped_no_id = 0
    else:
        resolved_input = Path(input_path).resolve()
        print(f"Analyzing {resolved_input.name}...", file=sys.stderr)
        analyzer_output = get_analyzer_output(resolved_input)
        if analyzer_output is None:
            return {"error": "Failed to analyze schematic"}

        # Extract parts with real MPNs
        parts = extract_parts(analyzer_output, id_keys=provider.ID_KEYS)
        all_bom = analyzer_output.get("bom", [])
        skipped_no_id = sum(
            1 for e in all_bom
            if not e.get("dnp") and e.get("type", "") not in _SKIP_TYPES
            and not is_real_mpn(e.get("mpn", ""))
            and not any(e.get(k, "").strip() for k in provider.SKIPPED_COUNTS_IDS)
        )

        print(provider.LABELS["found"].format(n=len(parts), k=skipped_no_id), file=sys.stderr)

    # Determine what needs processing
    to_download = []
    already_present = []
    skipped_failed = []

    for part in parts:
        # Use MPN as index key if available, otherwise distributor PN
        part_key = part["mpn"] or next((part.get(k, "") for k in provider.KEY_PRIORITY if part.get(k, "")), "")
        part["_key"] = part_key
        existing = index.get("parts", {}).get(part_key, {})
        status = existing.get("status", "")

        if status == "ok":
            old_file = existing.get("file", "")
            # Verify file still exists
            if (out_dir / old_file).exists():
                if not force_all:
                    # Rename to friendly filename if the old name was plain MPN
                    if provider.RENAME_PRESENT and not dry_run:
                        desc = existing.get("description", "") or part.get("description", "")
                        mfg = existing.get("manufacturer", "") or part.get("manufacturer", "")
                        new_file = friendly_filename(part_key, desc, mfg) + ".pdf"
                        if new_file != old_file and not (out_dir / new_file).exists():
                            (out_dir / old_file).rename(out_dir / new_file)
                            existing["file"] = new_file
                            print(f"  Renamed: {old_file} -> {new_file}", file=sys.stderr)
                    already_present.append(part_key)
                    existing["references"] = part["references"]
                    continue
            # File missing — re-download

        if status in ("failed", "not_found", "no_datasheet") and not (force or force_all):
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
        return {"downloaded": 0, "already_present": len(already_present),
                "failed": len(skipped_failed)}

    # Get OAuth token
    auth = provider.authenticate()
    if "error" in auth:
        return {"error": auth["error"]}
    if auth.get("ctx") is not None:
        ctx = auth["ctx"]

    # Process each part
    downloaded = []
    failed = []
    kept_errors = {}  # part key -> error, for an outage that kept the previous ok entry
    warnings = []  # verification warnings

    if parallel > 1:
        lock = threading.Lock()
        counter = [0]

        def _process_part(part):
            part_key = part["_key"]
            with lock:
                counter[0] += 1
                n = counter[0]
            print(f"[{n}/{len(to_download)}] {part_key}", file=sys.stderr)

            take_transport_failure()
            result = provider.sync_one_part(part, out_dir, index, delay, ctx)

            with lock:
                stored, result = _outage_entry(result, index.get("parts", {}).get(part_key, {}), out_dir)
                index.setdefault("parts", {})[part_key] = stored
                if stored is not result:
                    kept_errors[part_key] = result["error"]

                if result["status"] == "ok":
                    downloaded.append(part_key)
                    vconf = result.get("verification", "")
                    vmark = ""
                    if vconf == "wrong":
                        vmark = " ⚠ WRONG DATASHEET?"
                        warnings.append(part_key)
                    elif vconf == "unverified":
                        vmark = " (unverified)"
                    print(f"  OK: {result['file']} ({result['size_bytes']:,} bytes){vmark}",
                          file=sys.stderr)
                else:
                    failed.append(part_key)
                    print(f"  {result['status'].upper()}: {result.get('error', '')}",
                          file=sys.stderr)

                index["schematic"] = str(mpn_list or input_path)
                index["last_sync"] = datetime.now(timezone.utc).isoformat()
                save_index(index_path, index)

        with ThreadPoolExecutor(max_workers=parallel) as executor:
            executor.map(_process_part, to_download)
    else:
        for i, part in enumerate(to_download):
            part_key = part["_key"]
            print(f"[{i+1}/{len(to_download)}] {part_key}", file=sys.stderr)

            take_transport_failure()
            result = provider.sync_one_part(part, out_dir, index, delay, ctx)

            # Handle token expiry — refresh once and retry
            if result.get("status") == "not_found" and "No DigiKey results" in result.get("error", ""):
                pass

            stored, result = _outage_entry(result, index.get("parts", {}).get(part_key, {}), out_dir)
            index.setdefault("parts", {})[part_key] = stored
            if stored is not result:
                kept_errors[part_key] = result["error"]

            if result["status"] == "ok":
                downloaded.append(part_key)
                vconf = result.get("verification", "")
                vmark = ""
                if vconf == "wrong":
                    vmark = " ⚠ WRONG DATASHEET?"
                    warnings.append(part_key)
                elif vconf == "unverified":
                    vmark = " (unverified)"
                print(f"  OK: {result['file']} ({result['size_bytes']:,} bytes){vmark}",
                      file=sys.stderr)
            else:
                failed.append(part_key)
                print(f"  {result['status'].upper()}: {result.get('error', '')}",
                      file=sys.stderr)

            index["schematic"] = str(mpn_list or input_path)
            index["last_sync"] = datetime.now(timezone.utc).isoformat()
            save_index(index_path, index)

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
