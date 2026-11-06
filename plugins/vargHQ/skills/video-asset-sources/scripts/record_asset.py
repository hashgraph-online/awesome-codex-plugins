#!/usr/bin/env python3
"""Add one asset to assets/CREDITS.json, refusing licenses that fail the gate.

  python3 record_asset.py --file assets/whoosh.mp3 --source-url URL --license CC0 --license-url URL [--author NAME]

Keep only what the source returned. Do not guess a license. Exit 2 means do not use the file.
"""
import argparse, datetime, json, os, re, sys

REJECT = re.compile(r"\b(nc|nd|non-?commercial|no-?deriv\w*|sampling\+?|remarc|restricted|polyform)\b|\bsa\b|share-?alike", re.I)
NEEDS_CREDIT = re.compile(r"\bcc[- ]?by\b|incompetech|attribution", re.I)
FREE = re.compile(r"\bcc0\b|public domain|\bpd\b|pexels|pixabay|mixkit free|coverr|unsplash|\bofl\b|\bisc\b|\bmit\b|apache", re.I)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--file", required=True); p.add_argument("--source-url", required=True)
    p.add_argument("--license", required=True); p.add_argument("--license-url", default="")
    p.add_argument("--author", default=""); p.add_argument("--paid-plan", action="store_true", help="the person holds a paid plan that covers this")
    p.add_argument("--credits", default="assets/CREDITS.json")
    a = p.parse_args()
    lic = a.license.replace("_", " ").strip()
    if not lic or lic.lower() in ("unknown", "none", "n/a"):
        print("REJECTED: no license signal. Do not use %s" % a.file); sys.exit(2)
    if REJECT.search(lic) and not a.paid_plan:
        print("REJECTED: %s fails the license gate. Do not use %s" % (lic, a.file)); sys.exit(2)
    credit_needed = bool(NEEDS_CREDIT.search(lic))
    if credit_needed and not a.author:
        print("REJECTED: %s needs a credit line, so name the author with --author" % lic); sys.exit(2)
    if not (FREE.search(lic) or credit_needed or a.paid_plan):
        print("REJECTED: %s is not on the accept list. Read it, then pass --paid-plan only if a plan really covers it" % lic); sys.exit(2)
    rows = json.load(open(a.credits)) if os.path.exists(a.credits) else []
    row = {"file": a.file, "source_url": a.source_url, "license": lic, "license_url": a.license_url, "author": a.author,
           "credit_line": "%s by %s (%s)" % (os.path.basename(a.file), a.author, lic) if credit_needed else "",
           "fetched": datetime.date.today().isoformat()}
    rows = [r for r in rows if r["file"] != a.file] + [row]
    os.makedirs(os.path.dirname(a.credits) or ".", exist_ok=True)
    json.dump(rows, open(a.credits, "w"), indent=1)
    print(json.dumps({"ok": True, "credit_needed": credit_needed, "credit_line": row["credit_line"], "assets": len(rows)}))


if __name__ == "__main__":
    main()
