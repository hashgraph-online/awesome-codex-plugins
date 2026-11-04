#!/usr/bin/env python3
"""Send the daily MorningAI digest as multipart HTML email via SMTP.

Reads data_{DATE}.json (same source as gen-message), filters by score, and
delivers to the configured recipient list. Writes a manifest of per-recipient
send status for inspection / retry logic.

Usage:
    python3 skills/gen-email/scripts/send_email.py --date 2026-04-20
    python3 skills/gen-email/scripts/send_email.py --dry-run
    EMAIL_DRY_RUN=true python3 skills/gen-email/scripts/send_email.py
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Allow `from lib import ...` from this script's location
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from lib import env  # noqa: E402
from lib import email_sender, email_template, recipients  # noqa: E402


# Per-content-type slot caps (mirrors gen-message MESSAGE_CATEGORY_BALANCE logic)
TYPE_CAPS = {
    "product": 4,
    "model": 3,
    "benchmark": 2,
    "financing": 2,
}


# ----------------------------- helpers -----------------------------


def _today_str() -> str:
    """Today in UTC+8 as YYYY-MM-DD (matches gen-message convention)."""
    return datetime.now(tz=timezone(timedelta(hours=8))).strftime("%Y-%m-%d")


def _bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("true", "1", "yes", "on")


def _float(val: Any, default: float) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _int(val: Any, default: int) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _has_credible_source(item: Dict[str, Any]) -> bool:
    return bool(item.get("source_url", "").strip())


def _select_items(
    items: List[Dict[str, Any]],
    min_score: float,
    max_items: int,
) -> List[Dict[str, Any]]:
    """Apply score filter, verification gate (score>=7), category balance, and cap."""
    qualifying = [
        i for i in items
        if i.get("importance", 0) >= min_score
        and _has_credible_source(i)
        and (i.get("importance", 0) < 7 or i.get("verified", False))
        and not i.get("is_kol_voice", False)  # KOL voices render in their own section
    ]

    by_type: Dict[str, List[Dict[str, Any]]] = {}
    for it in qualifying:
        by_type.setdefault(it.get("content_type", ""), []).append(it)
    for lst in by_type.values():
        lst.sort(key=lambda x: x.get("importance", 0), reverse=True)

    selected: List[Dict[str, Any]] = []
    selected_ids = set()
    for ctype, cap in TYPE_CAPS.items():
        for it in by_type.get(ctype, [])[:cap]:
            selected.append(it)
            selected_ids.add(id(it))

    # Fill remaining slots with next-highest by score from any type
    if len(selected) < max_items:
        remaining = sorted(
            (i for i in qualifying if id(i) not in selected_ids),
            key=lambda x: x.get("importance", 0),
            reverse=True,
        )
        for it in remaining:
            if len(selected) >= max_items:
                break
            selected.append(it)

    selected.sort(key=lambda x: x.get("importance", 0), reverse=True)
    return selected[:max_items]


def _select_kol_items(
    items: List[Dict[str, Any]],
    min_score: float,
    max_items: int,
) -> List[Dict[str, Any]]:
    """Filter KOL voice items.

    Mirrors gen-infographic's KOL handling: NO 7+ verification gate because
    KOL voices are scored 4-7 by design (independent commentary, not vendor
    announcements that need cross-source verification). Just requires a
    credible source URL and meets `min_score`. Sorted by importance desc.
    """
    qualifying = [
        i for i in items
        if i.get("is_kol_voice", False)
        and i.get("importance", 0) >= min_score
        and _has_credible_source(i)
    ]
    qualifying.sort(key=lambda x: x.get("importance", 0), reverse=True)
    return qualifying[:max_items]


def _load_data(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        sys.stderr.write(f"[gen-email] data file not found: {path}\n")
        sys.exit(2)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.stderr.write(f"[gen-email] failed to parse {path}: {e}\n")
        sys.exit(2)
    # Accept either a bare list or {"items": [...]} envelope
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return payload["items"]
    sys.stderr.write(f"[gen-email] unexpected schema in {path}\n")
    sys.exit(2)


def _validate_smtp_config(config: Dict[str, Any]) -> Optional[str]:
    for k in ("EMAIL_SMTP_HOST", "EMAIL_SMTP_USER", "EMAIL_SMTP_PASSWORD"):
        if not config.get(k):
            return f"missing required config: {k}"
    return None


# ----------------------------- main -----------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=None, help="YYYY-MM-DD (default: today UTC+8)")
    parser.add_argument("--data", default=None, help="data file path (default: data_{date}.json)")
    parser.add_argument("--lang", default=None, help="zh | en | ja (overrides EMAIL_LANG)")
    parser.add_argument("--dry-run", action="store_true", help="generate previews, do not send")
    args = parser.parse_args()

    config = env.get_config()

    if not _bool(config.get("EMAIL_ENABLED")):
        # Silent skip — matches MESSAGE_ENABLED / SOCIAL_ENABLED behavior in pipeline
        return 0

    date = args.date or _today_str()
    data_path = Path(args.data) if args.data else Path(f"data_{date}.json")
    items_raw = _load_data(data_path)

    min_score = _float(config.get("EMAIL_MIN_SCORE", 5), 5.0)
    max_items = _int(config.get("EMAIL_MAX_ITEMS", 10), 10)
    selected = _select_items(items_raw, min_score=min_score, max_items=max_items)

    # KOL section: independent commentary rendered separately. Defaults to enabled
    # so subscribers see the section exists even on quiet KOL days (empty-state
    # message). Set EMAIL_KOL_ENABLED=false to suppress the section entirely.
    kol_enabled = _bool(config.get("EMAIL_KOL_ENABLED", "true"))
    kol_min_score = _float(config.get("EMAIL_KOL_MIN_SCORE", 4), 4.0)
    kol_max_items = _int(config.get("EMAIL_KOL_MAX_ITEMS", 5), 5)
    kol_show_empty = _bool(config.get("EMAIL_KOL_SHOW_EMPTY", "true"))
    kol_selected = (
        _select_kol_items(items_raw, min_score=kol_min_score, max_items=kol_max_items)
        if kol_enabled else []
    )
    # Render the KOL section block whenever enabled AND (we have items OR
    # operator opted into empty-state). When kol_enabled=false the section
    # is fully suppressed.
    show_kol_section = kol_enabled and (bool(kol_selected) or kol_show_empty)

    default_lang = args.lang or config.get("EMAIL_LANG") or "en"
    subject_tpl = config.get("EMAIL_SUBJECT_TEMPLATE", "MorningAI {date} · {n} updates")
    unsubscribe = config.get("EMAIL_LIST_UNSUBSCRIBE", "")

    # Always write a local preview using the default language
    preview_subject = email_template.render_subject(subject_tpl, date, len(selected), default_lang)
    preview_html = email_template.render_html(
        selected, date, lang=default_lang, subject=preview_subject, unsubscribe=unsubscribe,
        kol_items=kol_selected, show_kol_section=show_kol_section,
    )
    preview_text = email_template.render_text(
        selected, date, lang=default_lang, unsubscribe=unsubscribe,
        kol_items=kol_selected, show_kol_section=show_kol_section,
    )
    Path(f"email_{date}.html").write_text(preview_html, encoding="utf-8")
    Path(f"email_{date}.txt").write_text(preview_text, encoding="utf-8")

    dry_run = args.dry_run or _bool(config.get("EMAIL_DRY_RUN"))
    if dry_run:
        sys.stdout.write(
            f"[gen-email] dry-run: wrote email_{date}.html and email_{date}.txt "
            f"({len(selected)} items, {len(kol_selected)} KOL items, "
            f"lang={default_lang}). No SMTP traffic.\n"
        )
        return 0

    # Validate SMTP config before loading recipients (fail fast on missing creds)
    err = _validate_smtp_config(config)
    if err:
        sys.stderr.write(f"[gen-email] {err}\n")
        return 3

    rcpts = recipients.load_recipients(config)
    if not rcpts:
        sys.stderr.write(
            "[gen-email] no active recipients (set EMAIL_RECIPIENTS or EMAIL_RECIPIENTS_FILE)\n"
        )
        return 4

    smtp_cfg = email_sender.SmtpConfig(
        host=config["EMAIL_SMTP_HOST"],
        port=_int(config.get("EMAIL_SMTP_PORT", 587), 587),
        user=config["EMAIL_SMTP_USER"],
        password=config["EMAIL_SMTP_PASSWORD"],
        tls=config.get("EMAIL_SMTP_TLS", "starttls"),
    )
    from_addr = config.get("EMAIL_FROM") or smtp_cfg.user
    reply_to = config.get("EMAIL_REPLY_TO", "")
    rate_delay = _float(config.get("EMAIL_RATE_LIMIT_DELAY", 1), 1.0)
    extra_headers = email_sender.build_unsubscribe_headers(unsubscribe)

    attachments: List[Path] = []
    if _bool(config.get("EMAIL_ATTACH_IMAGE", "true")):
        img = Path(f"message_{date}.png")
        if img.exists():
            attachments.append(img)

    results: List[Dict[str, Any]] = []
    succeeded = 0
    failed = 0

    for i, r in enumerate(rcpts):
        # Per-recipient overrides
        rcpt_lang = r.lang or default_lang
        rcpt_min_score = r.min_score if r.min_score is not None else min_score
        # Re-select per-recipient only if their min_score differs from global
        rcpt_items = (
            selected if rcpt_min_score == min_score
            else _select_items(items_raw, min_score=rcpt_min_score, max_items=max_items)
        )
        # KOL items use a separate threshold (kol_min_score) — not influenced by
        # the recipient's main-feed min_score override, so KOL voices remain
        # visible to subscribers who set a high score floor for the main feed.

        subject = email_template.render_subject(subject_tpl, date, len(rcpt_items), rcpt_lang)
        html_body = email_template.render_html(
            rcpt_items, date, lang=rcpt_lang, subject=subject, unsubscribe=unsubscribe,
            kol_items=kol_selected, show_kol_section=show_kol_section,
        )
        text_body = email_template.render_text(
            rcpt_items, date, lang=rcpt_lang, unsubscribe=unsubscribe,
            kol_items=kol_selected, show_kol_section=show_kol_section,
        )

        try:
            res = email_sender.send(
                smtp_config=smtp_cfg,
                from_addr=from_addr,
                to_addr=r.display(),
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                reply_to=reply_to,
                extra_headers=extra_headers,
                attachments=attachments,
            )
            results.append({
                "email": r.email,
                "status": "sent",
                "message_id": res.message_id,
            })
            succeeded += 1
        except email_sender.SendError as e:
            results.append({
                "email": r.email,
                "status": "failed",
                "error": e.reason,
            })
            failed += 1

        # Rate limit between sends (skip after the last one)
        if i < len(rcpts) - 1 and rate_delay > 0:
            time.sleep(rate_delay)

    manifest = {
        "date": date,
        "subject": preview_subject,
        "total": len(rcpts),
        "succeeded": succeeded,
        "failed": failed,
        "lang_default": default_lang,
        "items_count": len(selected),
        "kol_items_count": len(kol_selected),
        "kol_section_shown": show_kol_section,
        "results": results,
    }
    Path(f"email_{date}_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8",
    )

    sys.stdout.write(
        f"[gen-email] {succeeded}/{len(rcpts)} sent ({failed} failed). "
        f"Manifest: email_{date}_manifest.json\n"
    )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
