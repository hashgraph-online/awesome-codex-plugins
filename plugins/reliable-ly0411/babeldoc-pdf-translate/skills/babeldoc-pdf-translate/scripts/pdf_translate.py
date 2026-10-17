#!/usr/bin/env python3
"""Portable BabelDOC CLI adapter. Python 3.10+; dry-run by default."""
import argparse
import csv
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from contextlib import nullcontext
from urllib.parse import urlparse

# Also support importlib-based callers and the installed standalone skill.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from chat_bridge import ChatBridge, BridgeError, NativeClient, run_bounded, validate_provider

VALUE_FLAGS = {
    "source_language": "--lang-in", "target_language": "--lang-out",
    "pages": "--pages", "qps": "--qps", "workers": "--pool-max-workers",
    "term_workers": "--term-pool-max-workers", "font": "--primary-font-family",
    "watermark": "--watermark-output-mode", "max_pages_per_part": "--max-pages-per-part",
    "min_text_length": "--min-text-length",
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
    "glossaries", "prompt_file", "provider", "timeout_seconds"
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

def engine_environment():
    """Normalize bracketed IPv6 bypass hosts only in the child environment.

    urllib/httpx prefer lowercase no_proxy. Preserve that precedence and all
    proxy endpoints; never copy a less restrictive uppercase value over it.
    """
    env = os.environ.copy()
    changes = []
    for name in ("no_proxy", "NO_PROXY"):
        if name not in env:
            continue
        hosts = []
        for item in env[name].split(","):
            host = item.strip()
            if host.startswith("[") and host.endswith("]"):
                try:
                    host = str(ipaddress.IPv6Address(host[1:-1]))
                except ValueError:
                    pass
            hosts.append(host)
        value = ",".join(hosts)
        if value != env[name]:
            env[name] = value
            changes.append(name)
    return env, changes

def probe(engine):
    env, _ = engine_environment()
    help_result = subprocess.run([engine, "--help"], capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=60, env=env)
    version_result = subprocess.run([engine, "--version"], capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=60, env=env)
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
    for key in ("qps", "workers", "term_workers", "max_pages_per_part", "min_text_length"):
        if key in job and (type(job[key]) is not int or job[key] < 1):
            raise ValueError(f"{key} must be a positive integer")
    if "timeout_seconds" in job and (type(job["timeout_seconds"]) is not int or not 5 <= job["timeout_seconds"] <= 86400):
        raise ValueError("timeout_seconds must be an integer from 5 to 86400")
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
    if isinstance(provider, dict) and "type" in provider:
        provider = job["provider"] = validate_provider(provider, base)
        for key in ("workers", "term_workers", "qps"):
            if job.get(key, 1) != 1:
                raise ValueError(f"Native chat jobs require {key}=1; requests are serialized")
            job[key] = 1
        # Native bridges own their cache and error accounting. A BabelDOC cache hit
        # would bypass authentication checks and confuse evidence of a live call.
        job["ignore_cache"] = True
        base_url, model = "http://127.0.0.1:0/v1", "native-" + provider["type"]
    else:
        if not isinstance(provider, dict) or set(provider) != {"base_url", "model", "api_key_env"}:
            raise ValueError("provider requires exactly base_url,model,api_key_env (no literal keys), or a native type")
        if any(not isinstance(v, str) or not v.strip() for v in provider.values()):
            raise ValueError("Provider fields must be nonempty strings")
        url = urlparse(provider["base_url"])
        if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError("Endpoint must be http(s), without embedded credentials/query/fragment")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", provider["api_key_env"]):
            raise ValueError("Invalid API key environment variable name")
        base_url, model = provider["base_url"], provider["model"]
    args = ["--files", str(source), "--output", str(output), "--openai",
            "--openai-base-url", base_url, "--openai-model", model]
    for key, flag in VALUE_FLAGS.items():
        if key in job:
            args.extend([flag, str(job[key])])
    if job.get("translate_tables") and "min_text_length" not in job:
        # BabelDOC's default of 5 silently excludes ordinary cells like Unit/Gain.
        # Four includes those cells without retypesetting short SI units (Hz/s/V).
        args.extend(["--min-text-length", "4"])
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

def selected_pages(job, page_count):
    if not job.get("pages"):
        return list(range(1, page_count + 1))
    selected = set()
    for part in job["pages"].split(","):
        ends = [int(v) for v in part.split("-")]
        selected.update(range(ends[0], ends[-1] + 1))
    return sorted(selected)

def validate_outputs(job, source, output, inspection):
    """Validate actual requested artifacts, independently of the engine exit code."""
    import pymupdf
    modes = ("mono", "dual") if job.get("outputs", "both") == "both" else (job["outputs"],)
    watermarks = ("watermarked", "no_watermark") if job.get("watermark") == "both" else (job.get("watermark", "watermarked"),)
    pages = selected_pages(job, inspection["page_count"])
    if not job.get("selected_pages_only"):
        pages = list(range(1, inspection["page_count"] + 1))
    expected, checks, errors = [], [], []
    for watermark in watermarks:
        suffix = ".no_watermark" if watermark == "no_watermark" else ""
        for mode in modes:
            path = output / f"{source.stem}{suffix}.{job['target_language']}.{mode}.pdf"
            expected.append(path)
            check = {"file": str(path), "kind": mode, "watermark": watermark, "valid": False}
            try:
                if path.is_symlink() or not path.is_file():
                    raise ValueError("Missing expected regular PDF")
                with pymupdf.open(path) as doc:
                    if not doc.is_pdf or doc.needs_pass or doc.page_count == 0:
                        raise ValueError("Not an accessible, nonempty PDF")
                    if doc.is_repaired:
                        raise ValueError("Damaged PDF required parser repair")
                    alternating = mode == "dual" and job.get("dual_layout") == "alternating"
                    count = len(pages) * (2 if alternating else 1)
                    check.update(page_count=len(doc), expected_page_count=count)
                    if len(doc) != count:
                        raise ValueError(f"Expected {count} pages, got {len(doc)}")
                    for i, page in enumerate(doc):
                        original = inspection["pages"][pages[i // 2 if alternating else i] - 1]
                        width = original["width"] * (2 if mode == "dual" and not alternating else 1)
                        if abs(page.rect.width - width) > 2 or abs(page.rect.height - original["height"]) > 2:
                            raise ValueError(f"Unexpected page dimensions at output page {i + 1}")
                        # Force content parsing, rather than only reading the file header.
                        page.get_text()
                check["valid"] = True
            except Exception as exc:
                check["error"] = str(exc)
                errors.append(f"{path.name}: {exc}")
            checks.append(check)
    unexpected = sorted(p.name for p in output.glob("*.pdf") if p not in expected)
    if unexpected:
        errors.append(f"Unexpected PDF artifacts: {unexpected}")
    return {"valid": not errors, "files": checks, "errors": errors,
            "note": "Checks structure, requested variants, page counts and dimensions; visual/content QA is still required."}

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
            "provider": job["provider"], "credential_env": job["provider"].get("api_key_env"), "visual_qa": "not performed",
            "normalized_proxy_variables": engine_environment()[1]}
    if not execute:
        return plan
    native = "type" in job["provider"]
    if not native and ("YOUR-" in job["provider"]["model"] or ".example" in job["provider"]["base_url"]):
        raise ValueError("Replace example model/endpoint before execution")
    key = None if native else os.environ.get(job["provider"]["api_key_env"])
    if not native and not key:
        raise ValueError("Required credential environment variable is unset")
    if output.exists():
        raise ValueError("Execution requires a new output directory; choose a new run name")
    output.mkdir(parents=True, mode=0o700)
    manifest = output / "run-manifest.json"
    plan["status"] = "running"
    manifest.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    # Never put the credential in process arguments or distributable job files.
    # Temp directory permissions inherit the host's private user temp policy.
    bridge = ChatBridge(job["provider"]) if native else None
    try:
        with bridge if bridge else nullcontext():
            if bridge:
                key = bridge.key
                args[args.index("--openai-base-url") + 1] = bridge.url
            with tempfile.TemporaryDirectory(prefix="pdf-translate-") as tmp:
                config = Path(tmp) / "credential.toml"
                config.write_text("[babeldoc]\nopenai-api-key = " + json.dumps(key) + "\n", encoding="utf-8")
                config.chmod(0o600)
                env = engine_environment()[0]
                if bridge:
                    for name in ("no_proxy", "NO_PROXY"):
                        env[name] = ",".join(filter(None, [env.get(name, ""), "127.0.0.1", "localhost"]))
                    result = run_bounded([engine, "--config", str(config), *args], "", job.get("timeout_seconds", 7200),
                                         env=env, cancel=bridge.failed, limit=32 * 1024 * 1024)
                else:
                    result = subprocess.run([engine, "--config", str(config), *args], capture_output=True,
                                            text=True, encoding="utf-8", errors="replace", env=env,
                                            timeout=job.get("timeout_seconds", 7200))
                log = (result.stdout + "\n" + result.stderr).replace(key, "[REDACTED]")
                (output / "engine.log").write_text(log, encoding="utf-8")
        plan["returncode"] = result.returncode
        plan["outputs"] = [str(p) for p in output.glob("*.pdf")]
        plan["output_validation"] = validate_outputs(job, source, output, inspection)
        plan["source_unchanged"] = digest(source) == plan["input_sha256"]
        bridge_ok = not bridge or (not bridge.failed.is_set() and bridge.stats["completed_requests"] > 0)
        plan["status"] = "needs-review" if result.returncode == 0 and plan["output_validation"]["valid"] and plan["source_unchanged"] and bridge_ok else "failed"
    except (BridgeError, subprocess.TimeoutExpired) as exc:
        plan["status"] = "failed"
        plan["error"] = bridge.stats["errors"][0] if bridge and bridge.stats["errors"] else (exc.code if isinstance(exc, BridgeError) else "TIMEOUT")
    except BaseException:
        plan["status"] = "interrupted-or-failed"
        raise
    finally:
        if bridge:
            plan["bridge"] = dict(bridge.stats)
            plan["bridge"]["native_item_types"] = getattr(bridge.client, "event_types", [])
        plan["source_unchanged"] = digest(source) == plan["input_sha256"]
        manifest.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return plan

def main():
    # SIGTERM should follow the same cleanup path as Ctrl-C, including owned
    # native model and engine process groups. SIGKILL cannot run cleanup.
    def terminate(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, terminate)
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("inspect", help="Read PDF statistics without rendering or external requests")
    p.add_argument("pdf")
    p = sub.add_parser("glossary", help="Validate glossary CSV")
    p.add_argument("csv")
    p = sub.add_parser("doctor", help="Probe installed BabelDOC capabilities")
    p.add_argument("--engine", default="babeldoc")
    p = sub.add_parser("chat-doctor", help="Check native chat login without translating or reading PDF content")
    p.add_argument("job")
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
            result = {"version": version, "flags": sorted(flags),
                      "normalized_proxy_variables": engine_environment()[1],
                      "scope": "CLI capability probe; no translation/provider or output-quality test"}
        elif a.command == "chat-doctor":
            provider = read_json(a.job).get("provider", {})
            provider = validate_provider(provider, Path(a.job).resolve().parent)
            import threading
            result = NativeClient(provider, threading.Event()).doctor()
        else:
            result = run_job(a.job, a.engine, a.execute)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get("status") == "failed" else 0
    except KeyboardInterrupt:
        print("Translation interrupted; successful private checkpoints are retained.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
