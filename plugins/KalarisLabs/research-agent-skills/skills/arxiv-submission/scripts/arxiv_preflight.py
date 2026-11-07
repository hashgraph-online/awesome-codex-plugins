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
JPEG_EXT = ".jpeg"
GRAPHICS_EXT = [".pdf", ".png", ".jpg", JPEG_EXT, ".eps", ".ps"]
SUSPECT_NAMES = re.compile(r"(response|rebuttal|review|cover[-_ ]?letter|reply|old|backup|copy|draft)", re.I)
ALLOWED_EXT = {".tex", ".bbl", ".bib", ".sty", ".cls", ".bst", ".clo", ".cfg", ".def", ".pdf", ".png", ".jpg", JPEG_EXT,
               ".eps", ".ps", ".txt", ".csv", ".dat", ".tikz", ".pgf", ".ind", ".gls", ".nls", ".bbx", ".cbx", ".lbx",
               ".mp", ".fd", ".sty.ltxml", ".xmpdata"}
BUILD_ARTIFACTS = {".aux", ".log", ".out", ".blg", ".toc", ".lof", ".lot", ".fls", ".fdb_latexmk", ".synctex",
                   ".gz", ".bcf", ".run.xml", ".xdv", ".dvi", ".nav", ".snm", ".vrb", ".idx", ".ilg"}


def strip_comments(tex: str) -> str:
    """Handle strip comments."""
    return re.sub(r"(?<!\\)%.*", "", tex)


README_NAMES = ("00README", "00README.XXX", "00README.json", "00README.yaml")
FIGURE_EXTS = {".pdf", ".png", ".jpg", JPEG_EXT}
SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}


def _include_candidates(cmd: str, target: str) -> list[str]:
    """Return the file names an include command may refer to."""
    if Path(target).suffix:
        return [target]
    return [target + e for e in (GRAPHICS_EXT if cmd == "includegraphics" else [".tex"])]


class _Preflight:
    """Collect preflight findings for one LaTeX project folder."""

    def __init__(self, root: Path) -> None:
        """Index the project files and locate the main .tex file(s)."""
        self.root = root
        self.findings: list[dict] = []
        self.files = [p for p in root.rglob("*") if p.is_file()]
        self.rels = {p.relative_to(root).as_posix(): p for p in self.files}
        self.lower = {r.lower(): r for r in self.rels}
        self.tex_files = [p for p in self.files if p.suffix == ".tex"]
        self.mains = [p for p in self.tex_files if self._is_main(p)]
        self.uses_pdflatex = True
        self.referenced: set[str] = set()

    @staticmethod
    def _is_main(path: Path) -> bool:
        """Return True when the file has both a documentclass and a document body."""
        raw = path.read_text(encoding="utf-8", errors="replace")
        return bool(re.search(r"\\documentclass", strip_comments(raw))) and "\\begin{document}" in raw

    def add(self, sev: str, msg: str, path: str = "") -> None:
        """Record one finding."""
        self.findings.append({"severity": sev, "file": path, "message": msg})

    def check_mains(self) -> None:
        """Report a missing or ambiguous main .tex file."""
        if not self.mains:
            self.add("error", "no main .tex file (with \\documentclass and \\begin{document}) found")
        elif len(self.mains) > 1:
            self.add("warning", f"several top-level .tex files ({', '.join(p.name for p in self.mains)}); arXiv may compile the wrong one. "
                                "Remove extras or name the main file clearly")

    def _find_hit(self, candidates: list[str], rel: str) -> str | None:
        """Return the first candidate present in the upload, relative to the project or the including file."""
        parent = Path(rel).parent.as_posix()
        return next((c for c in candidates if c in self.rels or f"{parent}/{c}".lstrip("./") in self.rels), None)

    def _check_include(self, cmd: str, t: str, rel: str) -> None:
        """Resolve one include target and report absolute, case-mismatched or missing files."""
        if re.match(r"^([A-Za-z]:|/|~)", t):
            self.add("error", f"absolute path in \\{cmd}{{{t}}}: use a path relative to the main file", rel)
            return
        candidates = _include_candidates(cmd, t)
        hit = self._find_hit(candidates, rel)
        if hit:
            self.referenced.add(hit)
            if hit.endswith((".eps", ".ps")) and self.uses_pdflatex:
                self.add("warning", f"EPS figure {hit} with pdflatex: convert to PDF (epstopdf) or arXiv may fail", rel)
            return
        ci = next((self.lower[c.lower()] for c in candidates if c.lower() in self.lower), None)
        if ci:
            self.add("error", f"case mismatch: \\{cmd}{{{t}}} but the file is '{ci}' (arXiv's filesystem is case-sensitive)", rel)
            self.referenced.add(ci)
        else:
            self.add("error", f"\\{cmd}{{{t}}} refers to a file that is not in the upload", rel)

    def _check_private_comments(self, raw: str, rel: str) -> None:
        """Warn about comment lines that leak TODO/reviewer/confidential notes."""
        private = [ln.strip() for ln in raw.splitlines()
                   if re.search(r"(?<!\\)%.*\b(TODO|FIXME|XXX|reviewer|rebuttal|confidential|do not share)\b", ln, re.I)]
        if private:
            self.add("warning", f"{len(private)} comment line(s) with TODO/reviewer/confidential notes. arXiv source is public; "
                                f"strip comments (arxiv_latex_cleaner). First: {private[0][:80]}", rel)

    def check_tex_file(self, tex: Path) -> None:
        """Run every per-source check on one .tex file."""
        rel = tex.relative_to(self.root).as_posix()
        raw = tex.read_text(encoding="utf-8", errors="replace")
        code = strip_comments(raw)
        is_main = tex in self.mains
        if is_main and re.search(r"\\usepackage(\[[^\]]*\])?\{fontspec\}", code):
            self.uses_pdflatex = False
            self.add("info", "fontspec detected: select XeLaTeX/LuaLaTeX processing on arXiv if supported, "
                             "or switch to pdflatex-compatible fonts", rel)
        for cmd, target in INCLUDE_RE.findall(code):
            for t in [x.strip() for x in target.split(",")]:
                self._check_include(cmd, t, rel)
        for _, bib in BIB_RE.findall(code):
            if is_main and not any(p.suffix == ".bbl" for p in self.files):
                self.add("error", f"bibliography '{bib}' but no .bbl file: compile locally and upload the .bbl "
                                  "(it must match the main file name). arXiv does not reliably run BibTeX/biber for you", rel)
        if is_main and "\\pdfoutput=1" not in raw[:2000] and self.uses_pdflatex:
            self.add("info", "add \\pdfoutput=1 in the first lines of the main file so arXiv uses pdflatex", rel)
        self._check_private_comments(raw, rel)

    def _check_file_type(self, rel: str, name: str, suffix: str) -> None:
        """Flag hidden files, build artifacts and unexpected file types."""
        if any(part.startswith(".") for part in Path(rel).parts):
            self.add("warning", "hidden file or folder: remove before upload", rel)
        elif suffix in BUILD_ARTIFACTS:
            self.add("warning", "build artifact: remove (arXiv regenerates it)", rel)
        elif suffix not in ALLOWED_EXT and name not in README_NAMES:
            self.add("warning", f"unexpected file type '{suffix or name}' (e.g. .docx/.zip): remove unless required", rel)

    def _figure_unreferenced(self, rel: str) -> bool:
        """Return True when a figure file is not matched by any referenced include."""
        if not (self.rels and self.referenced) or rel in self.referenced:
            return False
        stem = Path(rel).with_suffix("").as_posix()
        return not any(Path(r).with_suffix("").as_posix() == stem for r in self.referenced)

    def check_file(self, rel: str, p: Path) -> None:
        """Run every per-file name, type and reference check."""
        name = p.name
        suffix = "".join(p.suffixes[-2:]) if name.endswith(".run.xml") else p.suffix.lower()
        self._check_file_type(rel, name, suffix)
        if SUSPECT_NAMES.search(name) and suffix != ".sty":
            self.add("warning", "looks like a private/working file (response, review, draft, backup): remove", rel)
        if " " in rel or not rel.isascii():
            self.add("error", "spaces or non-ASCII characters in the file name: rename", rel)
        if suffix in FIGURE_EXTS and self._figure_unreferenced(rel):
            self.add("info", "figure not referenced by any \\includegraphics: remove if unused", rel)

    def run(self) -> float:
        """Run all checks and return the total upload size in MB."""
        self.check_mains()
        for tex in self.tex_files:
            self.check_tex_file(tex)
        total = 0
        for rel, p in sorted(self.rels.items()):
            total += p.stat().st_size
            self.check_file(rel, p)
        mb = total / 1024 / 1024
        if mb > SIZE_WARN_MB:
            self.add("warning", f"upload is {mb:.1f} MB: compress figures (large PNG photos to JPEG, rasterize huge vector plots) "
                                "and check arXiv's current size limit")
        return mb


def main() -> int:
    """Run the command-line interface."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = args.folder.resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    pre = _Preflight(root)
    mb = pre.run()
    findings = pre.findings

    if args.json:
        print(json.dumps({"size_mb": round(mb, 2), "findings": findings}, indent=2))
    else:
        for f in sorted(findings, key=lambda x: SEVERITY_ORDER[x["severity"]]):
            print(f"{f['severity']:<7} {f['file'] or '-'}: {f['message']}")
        n = {s: sum(f["severity"] == s for f in findings) for s in SEVERITY_ORDER}
        print(f"\n{len(pre.files)} files, {mb:.1f} MB: {n['error']} errors, {n['warning']} warnings, {n['info']} info")
    return 1 if any(f["severity"] == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
