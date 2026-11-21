#!/usr/bin/env python3
"""hyper-docx entry point: one subcommand per job.

    python3 hyper_docx.py doctor
    python3 hyper_docx.py inspect <file.docx> [--outline|--text|--json]
    python3 hyper_docx.py verify  <file.docx> [--spec spec.json] [--json]
    python3 hyper_docx.py build   --spec spec.json --out out.docx
    python3 hyper_docx.py render  <file.docx> --out page.html [--pdf page.pdf]
    python3 hyper_docx.py accept  <file.docx> --out clean.docx
    python3 hyper_docx.py reject  <file.docx> --out original.docx
    python3 hyper_docx.py comment <file.docx> --out marked.docx --anchor "문장" --text "의견" [--author 이름]
    python3 hyper_docx.py replace <file.docx> --out revised.docx --find "옛 문장" --with "새 문장" [--author 이름]
    python3 hyper_docx.py compare <a.docx> <b.docx> [--json]
    python3 hyper_docx.py revisions <file.docx> [--json]
    python3 hyper_docx.py text <file.docx>

Python 3.8+ standard library only. `doctor` reports what this machine can do so
the skill never claims a capability it cannot exercise.
"""

import argparse
import datetime
import json
import os
import platform
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import build_docx  # noqa: E402
import inspect_docx  # noqa: E402
import render_html  # noqa: E402
import review_changes  # noqa: E402
import verify_docx  # noqa: E402
from docxlib import DocxError, Package  # noqa: E402


def now_iso():
    return datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()


def find_soffice():
    for candidate in (
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/bin/soffice",
        "/usr/local/bin/soffice",
        "/opt/homebrew/bin/soffice",
    ):
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return shutil.which("soffice") or shutil.which("libreoffice")


def find_headless_browser():
    """Locate a Chromium-family binary this machine can print with."""
    import glob

    found = []
    for root in (
        os.path.expanduser("~/Library/Caches/ms-playwright"),
        os.path.expanduser("~/.cache/ms-playwright"),
    ):
        if not os.path.isdir(root):
            continue
        for pattern in (
            "chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell",
            "chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
            "chromium-*/chrome-linux/chrome",
        ):
            found.extend(sorted(glob.glob(os.path.join(root, pattern))))
    for generic in (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
    ):
        if os.path.isfile(generic):
            found.append(generic)
    return found[0] if found else None


def doctor():
    info = {
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
            "stdlib_only": True,
        },
        "tools": {
            "soffice": find_soffice(),
            "headless_browser": find_headless_browser(),
            "textutil": shutil.which("textutil"),
            "unzip": shutil.which("unzip"),
            "qlmanage": shutil.which("qlmanage"),
            "sips": shutil.which("sips"),
        },
        "capabilities": {},
    }
    tools = info["tools"]
    info["capabilities"]["build"] = "yes"
    info["capabilities"]["inspect"] = "yes"
    info["capabilities"]["verify"] = "yes"
    info["capabilities"]["tracked_changes"] = "yes"
    info["capabilities"]["comments"] = "yes"
    info["capabilities"]["html_render"] = "yes"
    info["capabilities"]["pdf_render"] = "yes" if tools["headless_browser"] else "missing-browser"
    info["capabilities"]["docx_to_pdf"] = "yes" if tools["soffice"] else "missing-soffice"
    info["capabilities"]["png_preview"] = "yes" if tools["qlmanage"] or tools["soffice"] else "missing"
    info["capabilities"]["docx_to_text"] = "yes" if tools["textutil"] else "stdlib"
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0


def cmd_inspect(args):
    data = inspect_docx.inspect(args.file)
    if args.outline:
        print(inspect_docx.outline(args.file))
        return 0
    if args.text:
        print(inspect_docx.text_of(args.file))
        return 0
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_verify(args):
    spec = build_docx.load_spec(args.spec) if args.spec else None
    report = verify_docx.verify(args.file, spec)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("file: %s" % report["path"])
        print("sha256: %s" % report.get("sha256", "-"))
        for check in report["checks"]:
            print("  %-22s %-8s %s" % (check["check"], check["status"], check["detail"]))
        print("result: %s" % report["status"])
    return 0 if report["status"] == "pass" else 1


def cmd_build(args):
    spec = build_docx.load_spec(args.spec)
    result = build_docx.build(spec, args.out)
    print(json.dumps(result, ensure_ascii=False))
    return 0


def cmd_render(args):
    result = render_html.render(args.file, args.out, title=args.title)
    print(json.dumps(result, ensure_ascii=False))
    if args.pdf:
        browser = find_headless_browser()
        if not browser:
            print("pdf: skipped (no headless browser found; run doctor)", file=sys.stderr)
            return 0
        command = [
            browser,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            "--print-to-pdf=%s" % os.path.abspath(args.pdf),
            "file://%s" % os.path.abspath(args.out),
        ]
        completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if completed.returncode != 0:
            print("pdf: failed (exit %s)" % completed.returncode, file=sys.stderr)
            return 1
        print(json.dumps({"pdf": os.path.abspath(args.pdf), "bytes": os.path.getsize(args.pdf)}, ensure_ascii=False))
    return 0


def cmd_accept(args):
    pkg = Package.open(args.file)
    accepted, rejected = review_changes.accept_all(pkg)
    pkg.save(args.out)
    print(json.dumps({"out": args.out, "insertions_kept": accepted, "deletions_dropped": rejected}, ensure_ascii=False))
    return 0


def cmd_reject(args):
    pkg = Package.open(args.file)
    accepted, rejected = review_changes.reject_all(pkg)
    pkg.save(args.out)
    print(json.dumps({"out": args.out, "deletions_restored": accepted, "insertions_dropped": rejected}, ensure_ascii=False))
    return 0


def cmd_comment(args):
    pkg = Package.open(args.file)
    comment_id = review_changes.add_comment(
        pkg, args.anchor, args.text, args.author, args.initials or args.author[:2], now_iso()
    )
    if comment_id is None:
        print("anchor not found: %r" % args.anchor, file=sys.stderr)
        return 1
    pkg.save(args.out)
    print(json.dumps({"out": args.out, "comment_id": comment_id, "anchor": args.anchor}, ensure_ascii=False))
    return 0


def cmd_replace(args):
    pkg = Package.open(args.file)
    ok = review_changes.replace_text_as_revision(pkg, args.find, args.replace, args.author, now_iso())
    if not ok:
        print("text not found: %r" % args.find, file=sys.stderr)
        return 1
    pkg.save(args.out)
    print(json.dumps({"out": args.out, "find": args.find, "replace": args.replace, "as_revision": True}, ensure_ascii=False))
    return 0


def cmd_compare(args):
    report = review_changes.compare(args.left, args.right)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    print("left:  %s (%d paragraphs)" % (report["left"]["path"], report["left"]["paragraphs"]))
    print("right: %s (%d paragraphs)" % (report["right"]["path"], report["right"]["paragraphs"]))
    if not report["hunks"]:
        print("no textual differences")
    for hunk in report["hunks"]:
        print("[%s]" % hunk["op"])
        for line in hunk["left"]:
            print("  - %s" % line)
        for line in hunk["right"]:
            print("  + %s" % line)
    return 0


def cmd_revisions(args):
    data = review_changes.summary(args.file)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_text(args):
    print(inspect_docx.text_of(args.file))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="hyper_docx.py", description="Word (.docx) build, inspect, verify, and review")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="report what this machine can run")

    p = sub.add_parser("inspect", help="read the package and print its structure")
    p.add_argument("file")
    p.add_argument("--outline", action="store_true", help="print a heading outline instead of JSON")
    p.add_argument("--text", action="store_true", help="print plain text instead of JSON")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("verify", help="run the structural and content checks")
    p.add_argument("file")
    p.add_argument("--spec", help="the spec the file was built from, for the geometry check")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("build", help="build a package from a JSON spec")
    p.add_argument("--spec", required=True, help="spec path, or - for stdin")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("render", help="render to HTML and optionally print to PDF")
    p.add_argument("file")
    p.add_argument("--out", required=True)
    p.add_argument("--pdf")
    p.add_argument("--title")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("accept", help="accept every tracked change")
    p.add_argument("file")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_accept)

    p = sub.add_parser("reject", help="reject every tracked change")
    p.add_argument("file")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_reject)

    p = sub.add_parser("comment", help="attach a comment to the paragraph holding an anchor string")
    p.add_argument("file")
    p.add_argument("--out", required=True)
    p.add_argument("--anchor", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--author", default="검토자")
    p.add_argument("--initials")
    p.set_defaults(func=cmd_comment)

    p = sub.add_parser("replace", help="replace one exact string and record it as a tracked change")
    p.add_argument("file")
    p.add_argument("--out", required=True)
    p.add_argument("--find", required=True)
    p.add_argument("--with", dest="replace", required=True)
    p.add_argument("--author", default="검토자")
    p.set_defaults(func=cmd_replace)

    p = sub.add_parser("compare", help="diff the text of two files")
    p.add_argument("left")
    p.add_argument("right")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("revisions", help="count tracked changes by kind and author")
    p.add_argument("file")
    p.set_defaults(func=cmd_revisions)

    p = sub.add_parser("text", help="print the plain text")
    p.add_argument("file")
    p.set_defaults(func=cmd_text)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "doctor":
        return doctor()
    try:
        return args.func(args)
    except DocxError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    except build_docx.SpecError as exc:
        print("spec error: %s" % exc, file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())