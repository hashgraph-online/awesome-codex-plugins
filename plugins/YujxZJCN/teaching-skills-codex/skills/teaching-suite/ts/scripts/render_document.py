#!/usr/bin/env python3
"""Document renderer — Markdown teaching artifacts → DOCX / PDF.

Closes the adoption gap where the syllabus, exam paper, rubric, and project brief were
Markdown-only: a professor must hand these out and submit them upward, where DOCX/PDF is
expected. Uses Pandoc (DOCX) and Pandoc + a PDF engine (PDF), with honest graceful
degradation — like deck-studio, it never pretends to render. No toolchain installed →
it prints the exact install command and leaves the Markdown source untouched.

Usage:
  python3 scripts/render_document.py syllabus.md --to docx
  python3 scripts/render_document.py exam.md --to pdf -o exam.pdf
  python3 scripts/render_document.py syllabus.md --to docx --reference-doc dept_template.docx

Exit: 0 = rendered (or source-only fallback reported) · 1 = render attempted and failed · 2 = error
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PDF_ENGINES = ["tectonic", "xelatex", "weasyprint", "wkhtmltopdf"]


def have(tool):
    return shutil.which(tool) is not None


def detect():
    return {"pandoc": have("pandoc"),
            "pdf_engines": [e for e in PDF_ENGINES if have(e)]}


def render(src, to, out=None, reference_doc=None):
    src = Path(src)
    if not src.exists():
        raise FileNotFoundError(src)
    out = Path(out) if out else src.with_suffix("." + to)
    tools = detect()

    if not tools["pandoc"]:
        print("Pandoc not found — cannot render. Markdown source is unchanged.\n"
              "  Install: brew install pandoc   (macOS) | apt-get install pandoc (Debian)\n"
              f"  Would produce: {out}", file=sys.stderr)
        return 0  # honest fallback, not a hard failure

    cmd = ["pandoc", str(src), "-o", str(out)]
    if to == "docx":
        if reference_doc:
            cmd += ["--reference-doc", str(reference_doc)]  # apply institutional .docx template
    elif to == "pdf":
        engine = tools["pdf_engines"][0] if tools["pdf_engines"] else None
        if not engine:
            print("Pandoc is installed but no PDF engine found.\n"
                  f"  Install one of: {', '.join(PDF_ENGINES)}  (e.g. brew install tectonic)\n"
                  "  DOCX works now: rerun with --to docx", file=sys.stderr)
            return 0
        cmd += [f"--pdf-engine={engine}"]
    else:
        print(f"error: unknown target '{to}' (use docx or pdf)", file=sys.stderr)
        return 2

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"render failed:\n{res.stderr.strip()}", file=sys.stderr)
        return 1
    if not out.exists():
        print("render reported success but output is missing", file=sys.stderr)
        return 1
    print(f"rendered: {out}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source", nargs="?", help="markdown artifact")
    ap.add_argument("--to", choices=["docx", "pdf"])
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--reference-doc", default=None,
                    help="institutional .docx template to match (DOCX only)")
    ap.add_argument("--detect", action="store_true", help="report available toolchain and exit")
    args = ap.parse_args(argv)
    if args.detect:
        t = detect()
        print(f"pandoc: {'yes' if t['pandoc'] else 'no'} · "
              f"pdf engines: {', '.join(t['pdf_engines']) or 'none'}")
        return 0
    if not args.source or not args.to:
        ap.error("source and --to are required (or use --detect)")
        return 2
    try:
        return render(args.source, args.to, args.out, args.reference_doc)
    except Exception as ex:
        print(f"error: {type(ex).__name__}: {ex}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
