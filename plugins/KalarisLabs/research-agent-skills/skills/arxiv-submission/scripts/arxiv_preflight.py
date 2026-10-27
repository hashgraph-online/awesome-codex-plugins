#!/usr/bin/env python3
"""Preflight a LaTeX project before uploading the source to arXiv.

Catches the problems that make arXiv's TeX processing fail or leak private
content: missing .bbl, case-mismatched or absolute include paths, EPS figures
with pdflatex, stray files (reviews, .docx, hidden files), private comments
left in the source, spaces/unicode in file names, and oversized uploads.

Usage:
    python arxiv_preflight.py path/to/paper/            # report
    python arxiv_preflight.py path/to/paper/ --json

Exit codes: 0 no errors, 1 errors found, 2 bad input. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

SIZE_WARN_MB = 10
INCLUDE_RE = re.compile(r"\\(includegraphics|input|include|subfile|includepdf)\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
BIB_RE = re.compile(r"\\(bibliography|addbibresource)\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
GRAPHICS_EXT = [".pdf", ".png", ".jpg", ".jpeg", ".eps", ".ps"]
SUSPECT_NAMES = re.compile(r"(response|rebuttal|review|cover[-_ ]?letter|reply|old|backup|copy|draft)", re.I)
ALLOWED_EXT = {".tex", ".bbl", ".bib", ".sty", ".cls", ".bst", ".clo", ".cfg", ".def", ".pdf", ".png", ".jpg", ".jpeg",
               ".eps", ".ps", ".txt", ".csv", ".dat", ".tikz", ".pgf", ".ind", ".gls", ".nls", ".bbx", ".cbx", ".lbx",
               ".mp", ".fd", ".sty.ltxml", ".xmpdata"}
BUILD_ARTIFACTS = {".aux", ".log", ".out", ".blg", ".toc", ".lof", ".lot", ".fls", ".fdb_latexmk", ".synctex",
                   ".gz", ".bcf", ".run.xml", ".xdv", ".dvi", ".nav", ".snm", ".vrb", ".idx", ".ilg"}


def strip_comments(tex: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", tex)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = args.folder.resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    findings: list[dict] = []

    def add(sev: str, msg: str, path: str = "") -> None:
        findings.append({"severity": sev, "file": path, "message": msg})

    files = [p for p in root.rglob("*") if p.is_file()]
    rels = {p.relative_to(root).as_posix(): p for p in files}
    lower = {r.lower(): r for r in rels}
    tex_files = [p for p in files if p.suffix == ".tex"]
    mains = [p for p in tex_files if re.search(r"\\documentclass", strip_comments(p.read_text(encoding="utf-8", errors="replace")))
             and "\\begin{document}" in p.read_text(encoding="utf-8", errors="replace")]
    if not mains:
        add("error", "no main .tex file (with \\documentclass and \\begin{document}) found")
    elif len(mains) > 1:
        add("warning", f"several top-level .tex files ({', '.join(p.name for p in mains)}); arXiv may compile the wrong one. "
                       "Remove extras or name the main file clearly")

    uses_pdflatex = True
    referenced: set[str] = set()
    for tex in tex_files:
        rel = tex.relative_to(root).as_posix()
        raw = tex.read_text(encoding="utf-8", errors="replace")
        code = strip_comments(raw)
        if tex in mains and re.search(r"\\usepackage(\[[^\]]*\])?\{fontspec\}", code):
            uses_pdflatex = False
            add("info", "fontspec detected: select XeLaTeX/LuaLaTeX processing on arXiv if supported, "
                        "or switch to pdflatex-compatible fonts", rel)
        for cmd, target in INCLUDE_RE.findall(code):
            for t in [x.strip() for x in target.split(",")]:
                if re.match(r"^([A-Za-z]:|/|~)", t):
                    add("error", f"absolute path in \\{cmd}{{{t}}}: use a path relative to the main file", rel)
                    continue
                candidates = [t] if Path(t).suffix else [t + e for e in (GRAPHICS_EXT if cmd == "includegraphics" else [".tex"])]
                hit = next((c for c in candidates if c in rels or f"{Path(rel).parent.as_posix()}/{c}".lstrip("./") in rels), None)
                if hit:
                    referenced.add(hit)
                    if hit.endswith((".eps", ".ps")) and uses_pdflatex:
                        add("warning", f"EPS figure {hit} with pdflatex: convert to PDF (epstopdf) or arXiv may fail", rel)
                    continue
                ci = next((lower[c.lower()] for c in candidates if c.lower() in lower), None)
                if ci:
                    add("error", f"case mismatch: \\{cmd}{{{t}}} but the file is '{ci}' (arXiv's filesystem is case-sensitive)", rel)
                    referenced.add(ci)
                else:
                    add("error", f"\\{cmd}{{{t}}} refers to a file that is not in the upload", rel)
        for _, bib in BIB_RE.findall(code):
            if tex in mains and not any(p.suffix == ".bbl" for p in files):
                add("error", f"bibliography '{bib}' but no .bbl file: compile locally and upload the .bbl "
                             "(it must match the main file name). arXiv does not reliably run BibTeX/biber for you", rel)
        if tex in mains and "\\pdfoutput=1" not in raw[:2000] and uses_pdflatex:
            add("info", "add \\pdfoutput=1 in the first lines of the main file so arXiv uses pdflatex", rel)
        private = [ln.strip() for ln in raw.splitlines()
                   if re.search(r"(?<!\\)%.*\b(TODO|FIXME|XXX|reviewer|rebuttal|confidential|do not share)\b", ln, re.I)]
        if private:
            add("warning", f"{len(private)} comment line(s) with TODO/reviewer/confidential notes. arXiv source is public; "
                           f"strip comments (arxiv_latex_cleaner). First: {private[0][:80]}", rel)

    total = 0
    for rel, p in sorted(rels.items()):
        total += p.stat().st_size
        name = p.name
        suffix = "".join(p.suffixes[-2:]) if name.endswith(".run.xml") else p.suffix.lower()
        if any(part.startswith(".") for part in Path(rel).parts):
            add("warning", "hidden file or folder: remove before upload", rel)
        elif suffix in BUILD_ARTIFACTS:
            add("warning", "build artifact: remove (arXiv regenerates it)", rel)
        elif suffix not in ALLOWED_EXT and name not in ("00README", "00README.XXX", "00README.json", "00README.yaml"):
            add("warning", f"unexpected file type '{suffix or name}' (e.g. .docx/.zip): remove unless required", rel)
        if SUSPECT_NAMES.search(name) and suffix != ".sty":
            add("warning", "looks like a private/working file (response, review, draft, backup): remove", rel)
        if " " in rel or not rel.isascii():
            add("error", "spaces or non-ASCII characters in the file name: rename", rel)
        if suffix in {".pdf", ".png", ".jpg", ".jpeg"} and rels and referenced and rel not in referenced \
                and not any(Path(r).with_suffix("").as_posix() == Path(rel).with_suffix("").as_posix() for r in referenced):
            add("info", "figure not referenced by any \\includegraphics: remove if unused", rel)
    mb = total / 1024 / 1024
    if mb > SIZE_WARN_MB:
        add("warning", f"upload is {mb:.1f} MB: compress figures (large PNG photos to JPEG, rasterize huge vector plots) "
                       "and check arXiv's current size limit")

    if args.json:
        print(json.dumps({"size_mb": round(mb, 2), "findings": findings}, indent=2))
    else:
        order = {"error": 0, "warning": 1, "info": 2}
        for f in sorted(findings, key=lambda x: order[x["severity"]]):
            print(f"{f['severity']:<7} {f['file'] or '-'}: {f['message']}")
        n = {s: sum(f["severity"] == s for f in findings) for s in order}
        print(f"\n{len(files)} files, {mb:.1f} MB: {n['error']} errors, {n['warning']} warnings, {n['info']} info")
    return 1 if any(f["severity"] == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
