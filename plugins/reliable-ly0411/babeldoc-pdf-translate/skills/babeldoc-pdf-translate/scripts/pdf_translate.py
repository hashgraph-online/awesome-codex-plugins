#!/usr/bin/env python3
"""Portable BabelDOC CLI adapter. Python 3.10+; dry-run by default."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

VALUE_FLAGS = {
    "source_language": "--lang-in", "target_language": "--lang-out",
    "pages": "--pages", "qps": "--qps", "workers": "--pool-max-workers",
    "term_workers": "--term-pool-max-workers", "font": "--primary-font-family",
    "watermark": "--watermark-output-mode", "max_pages_per_part": "--max-pages-per-part",
}
BOOL_FLAGS = {
    "translated_first": "--dual-translate-first",
    "selected_pages_only": "--only-include-translated-page",
    "save_terms": "--save-auto-extracted-glossary",
    "translate_tables": "--translate-table-text",
    "ignore_cache": "--ignore-cache",
}
ALLOWED = set(VALUE_FLAGS) | set(BOOL_FLAGS) | {
    "input", "output", "outputs", "dual_layout", "auto_terms", "scan_mode",
    "glossaries", "prompt_file", "provider"
}

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def resolve(base, value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Paths must be nonempty strings")
    p = Path(value).expanduser()
    return (base / p).resolve() if not p.is_absolute() else p.resolve()

def glossary(path):
    rows, seen = [], {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not {"source", "target"}.issubset(reader.fieldnames or []):
            raise ValueError(f"Glossary needs source,target columns: {path}")
        for n, row in enumerate(reader, 2):
            source, target = ((row.get(k) or "").strip() for k in ("source", "target"))
            if not source or not target:
                raise ValueError(f"Empty glossary source/target at row {n}: {path}")
            lang = (row.get("tgt_lng") or "").strip()
            key = (source.casefold(), lang.casefold())
            if key in seen and seen[key] != target:
                raise ValueError(f"Conflicting glossary term: {source}")
            seen[key] = target
            rows.append({"source": source, "target": target, "tgt_lng": lang})
    return rows

def executable(value):
    p = shutil.which(value)
    if p:
        return p
    if Path(value).is_file():
        return str(Path(value).resolve())
    raise ValueError("BabelDOC executable not found; install runtime or pass --engine ABS_PATH")

def probe(engine):
    help_result = subprocess.run([engine, "--help"], capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=60)
    version_result = subprocess.run([engine, "--version"], capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=60)
    if help_result.returncode or version_result.returncode:
        raise ValueError("Engine --help/--version failed")
    flags = set(re.findall(r"--[a-z][a-z0-9-]+", help_result.stdout))
    return flags, (version_result.stdout + version_result.stderr).strip()

def inspect_pdf(path):
    import pymupdf
    p = Path(path).resolve()
    with pymupdf.open(p) as doc:
        if doc.needs_pass:
            raise ValueError("Encrypted PDF requires an independently authorized decrypted copy")
        pages = [{"page": i + 1, "width": page.rect.width, "height": page.rect.height,
                  "text_characters": len(page.get_text().strip()),
                  "image_objects": len(page.get_images())} for i, page in enumerate(doc)]
    return {"file": str(p), "bytes": p.stat().st_size, "modified_epoch": p.stat().st_mtime,
            "sha256": digest(p), "page_count": len(pages), "pages": pages,
            "scan_candidates": [x["page"] for x in pages if x["text_characters"] < 30],
            "note": "Low text is only a scan heuristic; no OCR or visual QA performed."}

def prepare(job_path):
    base = Path(job_path).resolve().parent
    job = read_json(job_path)
    if not isinstance(job, dict):
        raise ValueError("Job must be a JSON object")
    unknown = set(job) - ALLOWED
    if unknown:
        raise ValueError(f"Unknown options: {sorted(unknown)}")
    for key in ("input", "output", "target_language", "provider"):
        if key not in job:
            raise ValueError(f"Missing required option: {key}")
    source = resolve(base, job["input"])
    output = resolve(base, job["output"])
    if not source.is_file() or source.suffix.lower() != ".pdf":
        raise ValueError("Input must be an existing PDF")
    if output == source or output == source.parent:
        raise ValueError("Use a separate output directory")
    for key in set(BOOL_FLAGS) | {"auto_terms"}:
        if key in job and type(job[key]) is not bool:
            raise ValueError(f"{key} must be a boolean")
    for key in ("qps", "workers", "term_workers", "max_pages_per_part"):
        if key in job and (type(job[key]) is not int or job[key] < 1):
            raise ValueError(f"{key} must be a positive integer")
    choices = {"outputs": ("mono", "dual", "both"),
               "dual_layout": ("side-by-side", "alternating"),
               "font": ("serif", "sans-serif", "script"),
               "watermark": ("watermarked", "no_watermark", "both"),
               "scan_mode": ("off", "auto", "force")}
    for key, values in choices.items():
        if key in job and job[key] not in values:
            raise ValueError(f"{key} must be one of {values}")
    for key in ("source_language", "target_language"):
        if key in job and (not isinstance(job[key], str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", job[key])):
            raise ValueError(f"Invalid language code: {key}")
    if "pages" in job:
        # Deliberately use only explicit 1-based pages and closed ranges.
        if not isinstance(job["pages"], str) or not re.fullmatch(r"[1-9]\d*(?:-[1-9]\d*)?(?:,[1-9]\d*(?:-[1-9]\d*)?)*", job["pages"]):
            raise ValueError("pages must use 1-based pages/closed ranges, e.g. 1,3-5")
        for part in job["pages"].split(","):
            ends = [int(v) for v in part.split("-")]
            if len(ends) == 2 and ends[0] > ends[1]:
                raise ValueError("Reversed page range")
    if job.get("selected_pages_only") and "pages" not in job:
        raise ValueError("selected_pages_only requires pages")
    provider = job["provider"]
    if not isinstance(provider, dict) or set(provider) != {"base_url", "model", "api_key_env"}:
        raise ValueError("provider requires exactly base_url,model,api_key_env (no literal keys)")
    if any(not isinstance(v, str) or not v.strip() for v in provider.values()):
        raise ValueError("Provider fields must be nonempty strings")
    url = urlparse(provider["base_url"])
    if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError("Endpoint must be http(s), without embedded credentials/query/fragment")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", provider["api_key_env"]):
        raise ValueError("Invalid API key environment variable name")
    args = ["--files", str(source), "--output", str(output), "--openai",
            "--openai-base-url", provider["base_url"], "--openai-model", provider["model"]]
    for key, flag in VALUE_FLAGS.items():
        if key in job:
            args.extend([flag, str(job[key])])
    for key, flag in BOOL_FLAGS.items():
        if job.get(key):
            args.append(flag)
    if job.get("outputs", "both") == "mono":
        args.append("--no-dual")
    elif job.get("outputs") == "dual":
        args.append("--no-mono")
    if job.get("dual_layout") == "alternating":
        args.append("--use-alternating-pages-dual")
    if not job.get("auto_terms", True):
        args.append("--no-auto-extract-glossary")
    scan = job.get("scan_mode", "off")
    if scan != "off":
        args.append("--auto-enable-ocr-workaround" if scan == "auto" else "--ocr-workaround")
    paths, merged = [], {}
    if not isinstance(job.get("glossaries", []), list):
        raise ValueError("glossaries must be a list")
    for value in job.get("glossaries", []):
        p = resolve(base, value)
        if "," in str(p):
            raise ValueError("BabelDOC glossary list cannot represent a comma in a path")
        for row in glossary(p):
            # Conservative conflict detection also covers language-unspecified entries.
            key = row["source"].casefold()
            if key in merged and merged[key] != row["target"]:
                raise ValueError(f"Conflicting glossary translations across files: {row['source']}")
            merged[key] = row["target"]
        paths.append(str(p))
    if paths:
        args.extend(["--glossary-files", ",".join(paths)])
    if job.get("prompt_file"):
        prompt = resolve(base, job["prompt_file"]).read_text(encoding="utf-8-sig").strip()
        if not prompt:
            raise ValueError("Empty prompt file")
        if len(prompt) > 4000:
            raise ValueError("Keep prompt under 4000 characters; put terminology in glossary CSV")
        args.extend(["--custom-system-prompt", prompt])
    return job, source, output, args

def run_job(job_path, engine, execute=False):
    job, source, output, args = prepare(job_path)
    engine = executable(engine)
    available, version = probe(engine)
    value_flags = set(VALUE_FLAGS.values()) | {"--files", "--output", "--openai-base-url", "--openai-model", "--glossary-files", "--custom-system-prompt"}
    requested = {"--config"}
    i = 0
    while i < len(args):
        requested.add(args[i])
        i += 2 if args[i] in value_flags else 1
    if requested - available:
        raise ValueError(f"Installed engine lacks flags: {sorted(requested - available)}")
    inspection = inspect_pdf(source)
    if "pages" in job and max(int(n) for n in re.findall(r"\d+", job["pages"])) > inspection["page_count"]:
        raise ValueError("Page range exceeds PDF page count")
    plan = {"status": "planned", "engine": engine, "engine_version": version,
            "input_sha256": digest(source), "arguments": args,
            "credential_env": job["provider"]["api_key_env"], "visual_qa": "not performed"}
    if not execute:
        return plan
    if "YOUR-" in job["provider"]["model"] or ".example" in job["provider"]["base_url"]:
        raise ValueError("Replace example model/endpoint before execution")
    key = os.environ.get(job["provider"]["api_key_env"])
    if not key:
        raise ValueError("Required credential environment variable is unset")
    if output.exists():
        raise ValueError("Execution requires a new output directory; choose a new run name")
    output.mkdir(parents=True)
    manifest = output / "run-manifest.json"
    plan["status"] = "running"
    manifest.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    # Never put the credential in process arguments or distributable job files.
    # Temp directory permissions inherit the host's private user temp policy.
    try:
        with tempfile.TemporaryDirectory(prefix="pdf-translate-") as tmp:
            config = Path(tmp) / "credential.toml"
            config.write_text("[babeldoc]\nopenai-api-key = " + json.dumps(key) + "\n", encoding="utf-8")
            config.chmod(0o600)
            result = subprocess.run([engine, "--config", str(config), *args], capture_output=True,
                                    text=True, encoding="utf-8", errors="replace")
            log = (result.stdout + "\n" + result.stderr).replace(key, "[REDACTED]")
            (output / "engine.log").write_text(log, encoding="utf-8")
        plan["returncode"] = result.returncode
        plan["outputs"] = [str(p) for p in output.glob("*.pdf")]
        plan["source_unchanged"] = digest(source) == plan["input_sha256"]
        plan["status"] = "needs-review" if result.returncode == 0 and plan["outputs"] and plan["source_unchanged"] else "failed"
    except BaseException:
        plan["status"] = "interrupted-or-failed"
        raise
    finally:
        manifest.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return plan

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("inspect", help="Read PDF statistics without rendering or external requests")
    p.add_argument("pdf")
    p = sub.add_parser("glossary", help="Validate glossary CSV")
    p.add_argument("csv")
    p = sub.add_parser("doctor", help="Probe installed BabelDOC capabilities")
    p.add_argument("--engine", default="babeldoc")
    p = sub.add_parser("run", help="Plan a job; translation only with --execute")
    p.add_argument("job")
    p.add_argument("--engine", default="babeldoc")
    p.add_argument("--execute", action="store_true")
    a = parser.parse_args()
    try:
        if a.command == "inspect":
            result = inspect_pdf(a.pdf)
        elif a.command == "glossary":
            result = {"valid": True, "rows": len(glossary(a.csv))}
        elif a.command == "doctor":
            flags, version = probe(executable(a.engine))
            result = {"version": version, "flags": sorted(flags)}
        else:
            result = run_job(a.job, a.engine, a.execute)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get("status") == "failed" else 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
