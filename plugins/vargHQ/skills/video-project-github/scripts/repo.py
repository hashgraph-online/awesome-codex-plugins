#!/usr/bin/env python3
"""repo.py: keep a video or code project in a private GitHub repo, for people who never used git.

Text goes in git. Media (video, audio, images, 3D) stays out of git: each file is listed by hash in
media.lock.jsonl and its bytes go to GitHub Releases of the same private repo, so one GitHub login
covers everything and a new laptop gets the whole project back, byte for byte.

  doctor                    what is missing on this machine and how to get it
  new <dir> [--kind video|code]   start a project from the template
  adopt [--apply]           bring an existing folder in; without --apply it only prints the plan
  connect [--name N] [--owner O]  create the private GitHub repo and upload
  save "what changed"       check, commit, back up
  approve <step> "note"     save, then mark this version as approved, e.g. approve story "ok by Sam"
  ship <file> [--note N]    publish a finished render as a private release with a link
  status                    where the project stands
  proof                     fresh copy from GitHub, restore, compare every hash: is the backup real?
  versions [-n 20]          the list of saved versions
  back <version> [paths]    make files what they were at a version; adds a new version, loses nothing
  try <name>                a side copy (own folder and branch) for a risky idea or a second agent
  keep <name> | drop <name> merge the side copy back, or throw it away
  restore                   after a fresh clone: set up this copy and download all media
  media note <file> ...     record how a generated file was made (prompt, model, seed, cost, job)
  media push|pull|verify|ls|forget  upload, download, check, list, drop a file from the list
  check [--staged] [--history]  stop secrets, big files and a public repo
  invite <github-user>      give someone access to the private repo

Python 3.9+ standard library only. Needs git and the GitHub CLI (gh).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

LOCK = "media.lock.jsonl"
# https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files
WARN_BYTES = 50 * 1024 * 1024  # GitHub warns at 50 MiB
BLOCK_BYTES = 100 * 1024 * 1024  # and blocks at 100 MiB
ASSET_MAX_BYTES = 2 * 1024 * 1024 * 1024  # a release asset must be under 2 GiB
ASSETS_PER_RELEASE = 1000  # a release holds at most 1000 assets
STORE_PREFIX = "media-store-"
UPLOAD_BATCH = 16

MEDIA_EXT = {
    ".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi", ".mxf", ".mts", ".mpg", ".mpeg",
    ".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".aif", ".aiff",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".tif", ".tiff", ".exr", ".heic", ".avif", ".bmp", ".psd", ".dng",
    ".blend", ".blend1", ".glb", ".fbx", ".usdz", ".usdc", ".obj", ".hdr", ".prproj", ".aep", ".drp",
    ".zip", ".rar", ".7z", ".tar", ".gz",
}
# Rebuilt on demand, never backed up.
JUNK_DIRS = {
    ".git", "node_modules", ".hyperframes", "renders", "tmp", ".cache", "__pycache__", ".venv", "venv",
    "dist", "build", "out", ".next", ".remotion", ".turbo", ".trash",
}
SECRET_FILE = re.compile(r"(^|/)(\.env(\.[\w.-]+)?|.*\.pem|.*\.p12|.*\.key|id_rsa|id_ed25519|credentials(\.\w+)?|\.npmrc|\.netrc)$")
SECRET_OK_FILE = re.compile(r"(^|/)\.env\.(example|sample|template)$")
SECRET_PATTERNS = [
    ("Anthropic key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("OpenAI or OpenRouter key", re.compile(r"\bsk-(proj-|svcacct-|or-)?[A-Za-z0-9_-]{32,}")),
    ("ElevenLabs key", re.compile(r"\bsk_[a-f0-9]{40,}")),
    ("Stripe key", re.compile(r"\b[rs]k_live_[A-Za-z0-9]{16,}")),
    ("GitHub token", re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})")),
    ("Google key", re.compile(r"\bAIza[A-Za-z0-9_-]{30,}")),
    ("AWS key", re.compile(r"\b(AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("varg key", re.compile(r"\bvarg_[A-Za-z0-9_]{16,}")),
    ("fal key", re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}:[0-9a-f]{16,}|\bfal-[0-9a-f]{16,}")),
    ("Replicate key", re.compile(r"\br8_[A-Za-z0-9]{30,}")),
    ("Hugging Face token", re.compile(r"\bhf_[A-Za-z0-9]{30,}")),
    ("Groq key", re.compile(r"\bgsk_[A-Za-z0-9]{40,}")),
    ("xAI key", re.compile(r"\bxai-[A-Za-z0-9]{40,}")),
    ("signed token", re.compile(r"\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{5,}")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("bearer token", re.compile(r"(?i)\bbearer\s+(?!\$|\{|<|your|xxx|token\b)[A-Za-z0-9._~+/-]{16,}")),
    # NAME_KEY=value, api_key: "value", password = value. Needs a name that says secret and a value that looks random.
    ("key in a setting", re.compile(
        r"""(?ix)(?:^|[^a-z0-9])(?:[a-z0-9]+[_-])*(?:api[_-]?key|(?<=[_-])key|secret|token|password|passwd|pwd|auth[_-]?key|access[_-]?key|credential)(?:[_-][a-z0-9]+)*["']?\s*[:=]\s*["']?
        (?!\$|\{|<|process\.|os\.|env\b|your|xxx|example|test|placeholder|none|null|true|false)
        (?P<value>[A-Za-z0-9_\-+/=.:]{16,})""")),
]
ALLOW_MARK = "repo:allow"  # put on a line to tell the scanner it is not a secret


class Stop(Exception):
    """Something the person or the agent must fix. The message says what to do."""


def run(cmd, cwd=None, check=True, capture=True, input_text=None):
    try:
        p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=capture, input=input_text)
    except FileNotFoundError:
        raise Stop(f"{cmd[0]} is not installed. Run: python3 tools/repo.py doctor")
    if check and p.returncode != 0:
        raise Stop(f"`{' '.join(map(str, cmd))}` failed:\n{(p.stderr or p.stdout or '').strip()}")
    return p


def git(*args, cwd=None, check=True):
    return run(["git", *args], cwd=cwd, check=check)


def out(*args, cwd=None):
    p = git(*args, cwd=cwd, check=False)
    return p.stdout.strip() if p.returncode == 0 else ""


def gh(*args, cwd=None, check=True):
    return run(["gh", *args], cwd=cwd, check=check)


def root() -> Path:
    r = out("rev-parse", "--show-toplevel")
    if not r:
        raise Stop("This folder is not a saved project yet. Run `new` or `adopt --apply` first.")
    return Path(r)


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit in ("B", "KB") else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def asset_name(entry: dict) -> str:
    return entry["sha256"][:32] + Path(entry["path"]).suffix.lower()


# ---------- the media list ----------

def load_lock(r: Path) -> dict:
    p = r / LOCK
    if not p.exists():
        return {}
    return parse_lock(p.read_text(encoding="utf-8"))


def parse_lock(text: str) -> dict:
    entries = {}
    for line in text.splitlines():
        if line.strip():
            e = json.loads(line)
            entries[e["path"]] = e
    return entries


def write_lock(r: Path, entries: dict) -> None:
    # One line per file, sorted, so a change reads as one changed line and merges cleanly.
    lines = [json.dumps(entries[k], sort_keys=True, ensure_ascii=False) for k in sorted(entries)]
    (r / LOCK).write_text("".join(line + "\n" for line in lines), encoding="utf-8")


def walk_files(r: Path):
    for dirpath, dirnames, filenames in os.walk(r):
        dirnames[:] = [d for d in dirnames if d not in JUNK_DIRS]
        for name in filenames:
            yield Path(dirpath) / name


def is_media(path: Path) -> bool:
    if path.suffix.lower() in MEDIA_EXT:
        return True
    try:
        return path.stat().st_size >= WARN_BYTES
    except OSError:
        return False


def load_cache(r: Path) -> dict:
    """path -> [bytes, mtime_ns, sha256], kept inside .git so the list itself never changes between machines."""
    try:
        return json.loads(Path(out("rev-parse", "--git-path", "repo-media-cache.json", cwd=r)).resolve().read_text())
    except (OSError, ValueError):
        return {}


def cached_sha(r: Path, rel: str, cache: dict) -> str:
    path = r / rel
    st = path.stat()
    hit = cache.get(rel)
    if hit and hit[0] == st.st_size and hit[1] == st.st_mtime_ns:
        return hit[2]
    digest = sha256(path)
    cache[rel] = [st.st_size, st.st_mtime_ns, digest]
    return digest


def save_cache(r: Path, cache: dict) -> None:
    git_path = out("rev-parse", "--git-path", "repo-media-cache.json", cwd=r)
    target = Path(git_path) if Path(git_path).is_absolute() else r / git_path
    target.write_text(json.dumps(cache))


def sync_media(r: Path) -> None:
    """Bring the list in line with the disk. A file moved to a new path keeps its notes. A file that is
    listed but not here stays listed: it may just not be downloaded yet (`media forget` removes it)."""
    entries = load_lock(r)
    cache = load_cache(r)
    seen = {}
    for path in walk_files(r):
        rel = path.relative_to(r).as_posix()
        if is_media(path) and not SECRET_FILE.search(rel):
            seen[rel] = cached_sha(r, rel, cache)
    by_hash = {}
    for e in entries.values():
        by_hash.setdefault(e["sha256"], e)
    for rel, digest in seen.items():
        old = entries.get(rel)
        if old and old["sha256"] == digest:
            continue
        notes = {k: v for k, v in by_hash.get(digest, {}).items() if k not in ("path", "sha256", "bytes")}
        entries[rel] = {**notes, "path": rel, "sha256": digest, "bytes": (r / rel).stat().st_size}
    for rel, e in list(entries.items()):
        if rel not in seen and e["sha256"] in seen.values():
            del entries[rel]  # moved, its bytes live at the new path
    write_lock(r, entries)
    save_cache(r, cache)


# ---------- checks ----------

def looks_binary(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return b"\0" in f.read(8192)
    except OSError:
        return True


def secret_on_line(line: str) -> str:
    for label, pattern in SECRET_PATTERNS:
        m = pattern.search(line)
        if not m:
            continue
        value = m.groupdict().get("value")
        # A readable name like my_long_descriptive_setting is not a key. Random values mix letters and digits.
        if value and not (re.search(r"\d", value) and re.search(r"[A-Za-z]", value)):
            continue
        return label
    return ""


def scan_text(path: Path, rel: str) -> list:
    found = []
    if looks_binary(path) or path.stat().st_size > 2 * 1024 * 1024:
        return found
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return found
    for number, line in enumerate(text.splitlines(), 1):
        if ALLOW_MARK in line:
            continue
        label = secret_on_line(line)
        if label:
            found.append(f"{rel}:{number} looks like a {label}. Move the value to .env (never saved) and read it from there.")
    return found


def pending_files(r: Path, staged: bool) -> list:
    if staged:
        names = out("diff", "--cached", "--name-only", "--diff-filter=ACMR", cwd=r)
    else:
        names = out("ls-files", "-m", "-o", "--exclude-standard", cwd=r) + "\n" + out("diff", "--cached", "--name-only", "--diff-filter=ACMR", cwd=r)
    return sorted({n for n in names.splitlines() if n and (r / n).is_file()})


def check_files(r: Path, staged: bool) -> list:
    problems = []
    for rel in pending_files(r, staged):
        path = r / rel
        if SECRET_FILE.search(rel) and not SECRET_OK_FILE.search(rel):
            problems.append(f"{rel} holds secrets and must never be saved to git. Add it to .gitignore.")
            continue
        size = path.stat().st_size
        if path.suffix.lower() in MEDIA_EXT or size >= WARN_BYTES:
            problems.append(f"{rel} ({human(size)}) is media and would bloat git forever. Add its type to .gitignore; `save` then lists it in {LOCK}.")
            continue
        problems += scan_text(path, rel)
    return problems


def check_history(r: Path) -> list:
    problems = []
    log = git("log", "--all", "-p", "--no-color", "--unified=0", cwd=r, check=False).stdout or ""
    commit = ""
    seen = set()
    for line in log.splitlines():
        if line.startswith("commit "):
            commit = line.split()[1][:10]
        elif line.startswith("+") and not line.startswith("+++") and ALLOW_MARK not in line:
            label = secret_on_line(line)
            if label and (label, commit) not in seen:
                seen.add((label, commit))
                problems.append(f"Version {commit} contains a {label}. It is burned: replace the key at its provider. See references/troubleshooting.md.")
    objects = git("rev-list", "--objects", "--all", cwd=r, check=False).stdout or ""
    if objects:
        sizes = run(["git", "cat-file", "--batch-check=%(objectsize) %(rest)"], cwd=r, input_text=objects, check=False).stdout or ""
        for line in sizes.splitlines():
            size, _, name = line.partition(" ")
            if size.isdigit() and int(size) >= WARN_BYTES and name:
                problems.append(f"History holds {name} ({human(int(size))}). GitHub blocks files over 100 MB and warns over 50 MB.")
    return problems


def visibility(r: Path) -> dict | None:
    if not out("remote", "get-url", "origin", cwd=r):
        return None
    p = gh("repo", "view", "--json", "visibility,url,nameWithOwner", cwd=r, check=False)
    if p.returncode != 0:
        return {"visibility": "UNKNOWN", "error": (p.stderr or "").strip()}
    return json.loads(p.stdout)


def require_private(r: Path) -> None:
    v = visibility(r)
    if v and v.get("visibility") == "PUBLIC":
        raise Stop(f"{v.get('nameWithOwner')} is PUBLIC. Nothing was uploaded. Make it private first: gh repo edit --visibility private --accept-visibility-change-consequences")


def set_identity(r: Path) -> None:
    """A commit needs a name and email. GitHub's noreply address keeps the real email out of history."""
    if out("config", "user.name", cwd=r) and out("config", "user.email", cwd=r):
        return
    name, email = "", ""
    p = gh("api", "user", "--jq", "[.login, .id, (.name // .login)] | @tsv", check=False)
    if p.returncode == 0 and p.stdout.strip():
        login, uid, display = p.stdout.strip().split("\t")
        name, email = display, f"{uid}+{login}@users.noreply.github.com"
    git("config", "user.name", name or "Project owner", cwd=r)
    git("config", "user.email", email or "owner@users.noreply.github.com", cwd=r)


def install_hook(r: Path) -> None:
    hooks = r / "tools" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    hook = hooks / "pre-commit"
    hook.write_text('#!/bin/sh\n# Stops secrets and media from entering git, even when someone runs git by hand.\n'
                    'PY=$(command -v python3 || command -v python)\nexec "$PY" tools/repo.py check --staged\n')
    hook.chmod(0o755)
    push = hooks / "pre-push"
    push.write_text('#!/bin/sh\n# Refuses a push that would overwrite versions on GitHub.\n'
                    'PY=$(command -v python3 || command -v python)\nexec "$PY" tools/repo.py check --pre-push\n')
    push.chmod(0o755)
    git("config", "core.hooksPath", "tools/hooks", cwd=r)


# ---------- GitHub Releases as the media store ----------

def store_releases(r: Path) -> list:
    p = gh("release", "list", "--limit", "1000", "--json", "tagName", cwd=r, check=False)
    if p.returncode != 0:
        return []
    return sorted(x["tagName"] for x in json.loads(p.stdout) if x["tagName"].startswith(STORE_PREFIX))


def store_assets(r: Path) -> dict:
    """asset name -> release tag, across every store release."""
    assets = {}
    for tag in store_releases(r):
        p = gh("release", "view", tag, "--json", "assets", "--jq", ".assets[].name", cwd=r)
        for name in p.stdout.split():
            assets[name] = tag
    return assets


def media_push(r: Path) -> tuple[int, int]:
    if not out("remote", "get-url", "origin", cwd=r):
        return 0, 0
    entries = load_lock(r)
    assets = store_assets(r)
    todo = {}
    for e in entries.values():
        name = asset_name(e)
        path = r / e["path"]
        if name in assets or name in todo or not path.exists():
            continue
        if e["bytes"] >= ASSET_MAX_BYTES:
            raise Stop(f"{e['path']} is {human(e['bytes'])}; one stored file must be under 2 GB. Make a smaller master, or upload it elsewhere and record `media note {e['path']} --url <link>`.")
        todo[name] = path
    if not todo:
        return 0, 0
    tags = store_releases(r)
    counts = {t: sum(1 for v in assets.values() if v == t) for t in tags}
    total = 0
    with tempfile.TemporaryDirectory(prefix="repo-media-") as tmp:
        names = list(todo)
        while names:
            tag = next((t for t in tags if counts[t] < ASSETS_PER_RELEASE), None)
            if not tag:
                tag = f"{STORE_PREFIX}{len(tags) + 1:03d}"
                gh("release", "create", tag, "--title", f"Media store {len(tags) + 1} (do not delete)", "--latest=false",
                   "--notes", f"Project media, one file per hash. Listed in {LOCK}; `python3 tools/repo.py restore` downloads it.", cwd=r)
                tags.append(tag)
                counts[tag] = 0
            room = min(UPLOAD_BATCH, ASSETS_PER_RELEASE - counts[tag])
            batch, names = names[:room], names[room:]
            files = []
            for name in batch:
                link = Path(tmp) / name
                try:
                    os.link(todo[name], link)
                except OSError:
                    shutil.copy2(todo[name], link)
                files.append(str(link))
                total += todo[name].stat().st_size
            gh("release", "upload", tag, *files, "--clobber", cwd=r)
            counts[tag] += len(batch)
            for f in files:
                os.unlink(f)
    return len(todo), total


def media_pull(r: Path, only=None) -> tuple[int, list]:
    entries = load_lock(r)
    cache = load_cache(r)
    missing = []
    for e in entries.values():
        if only is not None and e["path"] not in only:
            continue
        if not (r / e["path"]).exists() or cached_sha(r, e["path"], cache) != e["sha256"]:
            missing.append(e)
    save_cache(r, cache)
    if not missing:
        return 0, []
    assets = store_assets(r) if out("remote", "get-url", "origin", cwd=r) else {}
    failed = []
    got = 0
    with tempfile.TemporaryDirectory(prefix="repo-media-") as tmp:
        # One call per release: gh downloads the files of one call in parallel.
        by_tag = {}
        for e in missing:
            name = asset_name(e)
            if name in assets:
                by_tag.setdefault(assets[name], set()).add(name)
        for tag, names in by_tag.items():
            names = sorted(names)
            for i in range(0, len(names), UPLOAD_BATCH):
                patterns = [x for name in names[i:i + UPLOAD_BATCH] for x in ("--pattern", name)]
                gh("release", "download", tag, *patterns, "--dir", tmp, "--clobber", cwd=r, check=False)
        for e in missing:
            name = asset_name(e)
            part = Path(tmp) / name
            dest = r / e["path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not part.exists() and e.get("url"):
                try:
                    urllib.request.urlretrieve(e["url"], part)
                except Exception:  # noqa: BLE001 - a dead link is reported below, like any other missing file
                    pass
            if part.exists() and sha256(part) == e["sha256"]:
                shutil.copy2(part, dest)
                got += 1
            else:
                failed.append(e["path"])
    return got, failed


# ---------- commands ----------

def cmd_doctor(args):
    ok = True
    win = sys.platform == "win32"
    mac = sys.platform == "darwin"

    def line(good, what, fix=""):
        nonlocal ok
        print(f"{'ok ' if good else 'NO '} {what}" + ("" if good else f"\n    fix: {fix}"))
        ok = ok and good

    line(bool(shutil.which("git")), "git", "winget install Git.Git" if win else "xcode-select --install" if mac else "sudo apt install git")
    has_gh = bool(shutil.which("gh"))
    line(has_gh, "GitHub CLI (gh)", "winget install GitHub.cli" if win else "brew install gh" if mac else "see https://github.com/cli/cli#installation")
    if has_gh:
        signed = gh("auth", "status", check=False)
        line(signed.returncode == 0, "signed in to GitHub",
             "the person runs: gh auth login --web --git-protocol https   (one code, one click in the browser; no token, no password in chat)")
    print(f"ok  python {sys.version.split()[0]}")
    for tool, why in (("ffmpeg", "cutting and checking video"), ("node", "HyperFrames and Remotion")):
        print(f"{'ok ' if shutil.which(tool) else '-- '} {tool} ({why}; optional here)")
    return 0 if ok else 1


def template_dir(kind: str) -> Path:
    here = Path(__file__).resolve()
    for base in (here.parent.parent / "templates", here.parent / "templates"):
        if (base / kind).is_dir():
            return base / kind
    raise Stop(f"Template {kind} not found next to {here}.")


def copy_self(r: Path) -> None:
    dest = r / "tools" / "repo.py"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if Path(__file__).resolve() != dest.resolve():
        shutil.copy2(Path(__file__).resolve(), dest)


def fill(text: str, name: str) -> str:
    return text.replace("{{name}}", name).replace("{{date}}", time.strftime("%Y-%m-%d"))


def cmd_new(args):
    r = Path(args.dir).resolve()
    if r.exists() and any(r.iterdir()):
        raise Stop(f"{r} is not empty. Use `adopt` for an existing folder.")
    for source in (template_dir("common"), template_dir(args.kind)):
        for path in source.rglob("*"):
            if path.is_dir() or path.name == ".DS_Store":
                continue
            dest = r / path.relative_to(source)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(fill(path.read_text(encoding="utf-8"), r.name), encoding="utf-8")
    copy_self(r)
    git("init", "-q", "-b", "main", cwd=r)
    set_identity(r)
    install_hook(r)
    (r / LOCK).touch()
    git("add", "-A", cwd=r)
    git("commit", "-q", "-m", "Project started", cwd=r)
    print(f"Project ready in {r}. It is saved on this computer.\nNext: `python3 tools/repo.py connect` to create the private GitHub repo.")
    return 0


def cmd_adopt(args):
    r = Path(args.dir).resolve()
    source = template_dir("common")
    media, text, secrets, junk_bytes = [], [], [], 0
    for dirpath, dirnames, filenames in os.walk(r):
        for d in list(dirnames):
            if d in JUNK_DIRS:
                dirnames.remove(d)
                if d != ".git":
                    junk_bytes += sum(f.stat().st_size for f in (Path(dirpath) / d).rglob("*") if f.is_file() and not f.is_symlink())
        for name in filenames:
            path = Path(dirpath) / name
            rel = path.relative_to(r).as_posix()
            if name in (".DS_Store", "Thumbs.db"):
                continue
            if SECRET_FILE.search(rel) and not SECRET_OK_FILE.search(rel):
                secrets.append(f"{rel}: secrets file, stays on this computer only.")
            elif is_media(path):
                media.append((rel, path.stat().st_size))
            else:
                text.append(rel)
                secrets += [s for s in scan_text(path, rel)]
    print(f"Folder: {r}\nGoes in git (text): {len(text)} files\nMedia, listed by hash and stored in Releases: {len(media)} files, {human(sum(s for _, s in media))}")
    for rel, size in sorted(media, key=lambda x: -x[1])[:8]:
        print(f"  {human(size):>9}  {rel}")
    print(f"Skipped (rebuilt on demand): {human(junk_bytes)}")
    inline = [s for s in secrets if "looks like" in s]
    for s in secrets:
        print(f"SECRET  {s}")
    too_big = [rel for rel, size in media if size >= ASSET_MAX_BYTES]
    for rel in too_big:
        print(f"TOO BIG {rel}: over the 2 GB per-file limit. Make a smaller master or keep it elsewhere and record a link.")
    if not args.apply:
        print("\nNothing changed. Run again with --apply." + (" Fix the SECRET lines inside files first." if inline else ""))
        return 0
    if inline:
        raise Stop("Move these keys to .env first, then run again:\n" + "\n".join(inline))
    for path in source.rglob("*"):
        if path.is_dir() or path.name == ".DS_Store":
            continue
        rel = path.relative_to(source)
        dest = r / rel
        content = fill(path.read_text(encoding="utf-8"), r.name)
        if rel.name == ".gitignore" and dest.exists():
            have = dest.read_text(encoding="utf-8")
            add = [ln for ln in content.splitlines() if ln and ln not in have.splitlines()]
            dest.write_text(have.rstrip("\n") + "\n\n" + "\n".join(add) + "\n", encoding="utf-8")
        elif not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
    env = r / ".env"
    example = r / ".env.example"
    if env.exists() and not example.exists():
        names = re.findall(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=", env.read_text(encoding="utf-8", errors="ignore"), re.M)
        example.write_text("".join(f"{n}=\n" for n in names), encoding="utf-8")
    copy_self(r)
    if not (r / ".git").exists():
        git("init", "-q", "-b", "main", cwd=r)
    set_identity(r)
    install_hook(r)
    (r / LOCK).touch()
    sync_media(r)
    problems = check_files(r, staged=False)
    if problems:
        raise Stop("\n".join(problems))
    git("add", "-A", cwd=r)
    git("commit", "-q", "-m", "Project brought into git", cwd=r)
    print(f"Saved on this computer. Next: `python3 tools/repo.py connect`.")
    history = check_history(r)
    for p in history:
        print(f"WARNING {p}")
    return 0


def cmd_connect(args):
    r = root()
    if out("remote", "get-url", "origin", cwd=r):
        require_private(r)
        v = visibility(r) or {}
        print(f"Already connected: {v.get('url')} ({v.get('visibility')}).")
        return 0
    gh("auth", "setup-git", check=False)  # lets git use the gh login, no password prompts
    name = args.name or r.name
    full = f"{args.owner}/{name}" if args.owner else name
    gh("repo", "create", full, "--private", "--source", str(r), "--remote", "origin", "--push",
       "--description", "Private project. Text in git, media in Releases, listed in media.lock.jsonl.", cwd=r)
    v = visibility(r)
    if not v or v.get("visibility") != "PRIVATE":
        raise Stop(f"The repo should be private but GitHub says {v}. Stop and show this to the person.")
    count, size = media_push(r)
    print(f"Private repo ready: {v['url']}\nOnly you can see it. Uploaded {count} media files ({human(size)}).")
    return 0


def do_save(r: Path, message: str) -> None:
    require_private(r)
    set_identity(r)
    sync_media(r)
    problems = check_files(r, staged=False)
    if problems:
        raise Stop("Not saved. Fix these first:\n" + "\n".join(problems))
    git("add", "-A", cwd=r)
    if git("diff", "--cached", "--quiet", cwd=r, check=False).returncode != 0:
        git("commit", "-q", "-m", message, cwd=r)
        print(f"Saved: version {version_number(r)}, \"{message}\".")
    else:
        print("Nothing new to save.")
    if not out("remote", "get-url", "origin", cwd=r):
        print("Saved on this computer only. Run `connect` to back it up to GitHub.")
        return
    push_all(r)


def push_all(r: Path) -> None:
    branch = out("branch", "--show-current", cwd=r)
    empty = not out("ls-remote", "--heads", "origin", cwd=r)
    if empty:
        git("push", "-q", "-u", "origin", branch, cwd=r, check=False)
    try:
        count, size = media_push(r)
    except Stop as e:
        print(f"NOT BACKED UP YET (media): {e}\nThe version is safe on this computer. Run `media push` when fixed.")
        return
    p = git("push", "-q", "-u", "--follow-tags", "origin", branch, cwd=r, check=False)
    if p.returncode != 0:
        git("pull", "-q", "--rebase", "--autostash", "origin", branch, cwd=r, check=False)
        p = git("push", "-q", "-u", "--follow-tags", "origin", branch, cwd=r, check=False)
    if p.returncode != 0:
        print(f"NOT BACKED UP YET: {(p.stderr or '').strip()}\nThe version is safe on this computer. Try `save` again later.")
        return
    media = f" Uploaded {count} media files ({human(size)})." if count else ""
    print(f"Backed up to GitHub.{media}")


def version_number(r: Path) -> str:
    return out("rev-list", "--count", "--first-parent", "HEAD", cwd=r)


def cmd_save(args):
    do_save(root(), args.message)
    return 0


def cmd_approve(args):
    r = root()
    do_save(r, f"Approved {args.step}: {args.note}")
    existing = out("tag", "--list", f"approved/{args.step}/*", cwd=r).splitlines()
    tag = f"approved/{args.step}/{len(existing) + 1}"
    git("tag", "-a", tag, "-m", args.note, cwd=r)
    if out("remote", "get-url", "origin", cwd=r):
        git("push", "-q", "origin", tag, cwd=r, check=False)
    print(f"Marked as approved: {tag}. You can always come back to it.")
    return 0


def cmd_ship(args):
    r = root()
    f = Path(args.file)
    if not f.exists():
        raise Stop(f"{f} not found.")
    do_save(r, f"Shipped {f.name}")
    tag = args.tag or f"ship/{f.stem}"
    if not out("remote", "get-url", "origin", cwd=r):
        raise Stop("Connect to GitHub first: `connect`.")
    p = gh("release", "create", tag, str(f), "--title", f.stem, "--notes", args.note or f"Render of version {version_number(r)}.", cwd=r)
    print(f"Shipped. Only people with access to the private repo can open it: {p.stdout.strip()}")
    return 0


def cmd_status(args):
    r = root()
    v = visibility(r)
    entries = load_lock(r)
    size = sum(e["bytes"] for e in entries.values())
    here = sum(1 for e in entries.values() if (r / e["path"]).exists())
    changes = len(out("status", "--porcelain", cwd=r).splitlines())
    print(f"Project: {r.name}")
    print(f"GitHub: {v.get('url')} ({v.get('visibility')})" if v else "GitHub: not connected")
    print(f"Version: {version_number(r)} on {out('branch', '--show-current', cwd=r)}, unsaved changes: {changes}")
    print(f"Media: {len(entries)} files, {human(size)}, {here} on this computer" + ("" if here == len(entries) else " (`restore` downloads the rest)"))
    spent = sum(e.get("cost_usd") or 0 for e in entries.values())
    if spent:
        print(f"Recorded spend on generated files: ${spent:.2f}")
    if v and v.get("visibility") != "UNKNOWN":
        ahead = out("rev-list", "--count", "@{u}..HEAD", cwd=r)
        if ahead and ahead != "0":
            print(f"Not backed up yet: {ahead} versions. Run `save`.")
        assets = store_assets(r)
        unsent = [e["path"] for e in entries.values() if asset_name(e) not in assets and not e.get("url")]
        print(f"Media backed up: {len(entries) - len(unsent)} of {len(entries)}")
    return 0


def cmd_versions(args):
    r = root()
    log = git("log", "--first-parent", f"-n{args.n}", "--date=format:%Y-%m-%d %H:%M", "--format=%H%x09%ad%x09%s%x09%D", cwd=r).stdout
    total = int(version_number(r) or 0)
    for i, line in enumerate(log.splitlines()):
        _sha, date, subject, refs = (line.split("\t") + [""] * 4)[:4]
        tags = " ".join(x.strip().replace("tag: ", "") for x in refs.split(",") if "tag:" in x)
        print(f"{total - i:>4}  {date}  {subject}" + (f"  [{tags}]" if tags else ""))
    return 0


def resolve_version(r: Path, ref: str) -> str:
    if ref.isdigit() and len(ref) < 7:
        shas = out("rev-list", "--reverse", "--first-parent", "HEAD", cwd=r).splitlines()
        n = int(ref)
        if not 1 <= n <= len(shas):
            raise Stop(f"There is no version {ref}. See `versions`.")
        return shas[n - 1]
    sha = out("rev-parse", "--verify", f"{ref}^{{commit}}", cwd=r)
    if not sha:
        raise Stop(f"There is no version {ref}. See `versions`.")
    return sha


def cmd_back(args):
    r = root()
    target = resolve_version(r, args.version)
    if out("status", "--porcelain", cwd=r):
        do_save(r, "Saved before going back")
    current = load_lock(r)
    old_text = out("show", f"{target}:{LOCK}", cwd=r)
    old = parse_lock(old_text) if old_text else {}
    paths = args.paths or ["."]
    tracked = out("ls-tree", "-r", "--name-only", target, cwd=r).splitlines()
    git_paths = [p for p in paths if p == "." or p in tracked or any(t.startswith(p.rstrip("/") + "/") for t in tracked)]
    if git_paths:
        git("restore", f"--source={target}", "--staged", "--worktree", "--", *git_paths, cwd=r)
    if args.paths:
        scope = [p.rstrip("/") for p in args.paths]
        inside = lambda rel: any(rel == s or rel.startswith(s + "/") for s in scope)  # noqa: E731
        merged = {k: v for k, v in current.items() if not inside(k)}
        merged.update({k: v for k, v in old.items() if inside(k)})
    else:
        merged = old
    # Media the older version did not have leaves this folder only if GitHub holds a copy.
    assets = store_assets(r) if out("remote", "get-url", "origin", cwd=r) else {}
    for rel, e in current.items():
        if rel in merged:
            continue
        path = r / rel
        if path.exists():
            if asset_name(e) in assets or e.get("url"):
                path.unlink()
            else:
                trash = r / ".trash" / rel
                trash.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), trash)
                print(f"Kept a copy in .trash/: {rel} (not backed up yet)")
    write_lock(r, merged)
    got, failed = media_pull(r, set(merged))
    for rel in failed:
        print(f"MISSING {rel}: could not be downloaded.")
    git("add", "-A", cwd=r)
    label = args.version + (" for " + ", ".join(args.paths) if args.paths else "")
    if git("diff", "--cached", "--quiet", cwd=r, check=False).returncode != 0:
        git("commit", "-q", "-m", f"Went back to version {label}", cwd=r)
    print(f"Files are now as they were at version {label}. This is version {version_number(r)}; nothing was lost. Downloaded {got} media files.")
    if out("remote", "get-url", "origin", cwd=r):
        push_all(r)
    return 0


def side_copy(r: Path, name: str) -> Path:
    return r.parent / f"{r.name}--{name}"


def main_root(r: Path) -> Path:
    common = Path(out("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=r))
    return common.parent


def link_media(src: Path, dst: Path) -> None:
    for rel in load_lock(dst):
        a, b = src / rel, dst / rel
        if a.exists() and not b.exists():
            b.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(a, b)
            except OSError:
                shutil.copy2(a, b)


def cmd_try(args):
    r = root()
    do_save(r, f"Saved before trying {args.name}")
    copy = side_copy(r, args.name)
    git("worktree", "add", "-q", str(copy), "-b", f"try/{args.name}", cwd=r)
    link_media(r, copy)
    print(f"Side copy ready in {copy}. Work there; the main project stays as it is.\nKeep it with `keep {args.name}`, or throw it away with `drop {args.name}`.")
    return 0


def cmd_keep(args):
    r = main_root(root())
    copy = side_copy(r, args.name)
    if copy.exists():
        do_save(copy, f"Finished trying {args.name}")
    p = git("merge", "--no-ff", "-m", f"Kept {args.name}", f"try/{args.name}", cwd=r, check=False)
    if p.returncode != 0:
        raise Stop(f"Both versions changed the same lines. Files with conflicts:\n{out('diff', '--name-only', '--diff-filter=U', cwd=r)}\nOpen each one, keep the right lines, then run `save`. To cancel: git merge --abort")
    if copy.exists():
        link_media(copy, r)
        git("worktree", "remove", "--force", str(copy), cwd=r)
    git("branch", "-q", "-D", f"try/{args.name}", cwd=r, check=False)
    print(f"Kept {args.name}. This is version {version_number(r)}.")
    if out("remote", "get-url", "origin", cwd=r):
        git("push", "-q", "origin", "--delete", f"try/{args.name}", cwd=r, check=False)
        push_all(r)
    return 0


def cmd_drop(args):
    r = main_root(root())
    copy = side_copy(r, args.name)
    if copy.exists():
        if out("status", "--porcelain", cwd=copy) and not args.force:
            raise Stop(f"{copy} has unsaved changes. Run again with --force only if the person agreed to lose them.")
        git("worktree", "remove", "--force", str(copy), cwd=r)
    git("branch", "-q", "-D", f"try/{args.name}", cwd=r, check=False)
    print(f"Dropped {args.name}. The main project was not touched.")
    return 0


def cmd_restore(args):
    r = root()
    gh("auth", "setup-git", check=False)
    set_identity(r)
    install_hook(r)
    got, failed = media_pull(r)
    entries = load_lock(r)
    print(f"Project restored. {len(entries)} media files listed, {got} downloaded, {len(failed)} missing.")
    for rel in failed:
        print(f"MISSING {rel}")
    if (r / ".env.example").exists() and not (r / ".env").exists():
        print("Keys are not in GitHub on purpose. Copy .env.example to .env and fill it from your password manager.")
    return 1 if failed else 0


def cmd_proof(args):
    r = root()
    v = visibility(r)
    if not v or v.get("visibility") == "UNKNOWN":
        raise Stop("Not connected to GitHub, so there is nothing to prove yet. Run `connect`.")
    unsaved = out("status", "--porcelain", cwd=r)
    with tempfile.TemporaryDirectory(prefix="repo-proof-") as tmp:
        copy = Path(tmp) / "copy"
        gh("repo", "clone", v["nameWithOwner"], str(copy), cwd=tmp)
        run([sys.executable, str(copy / "tools" / "repo.py"), "restore"], cwd=copy, check=False)
        entries = load_lock(copy)
        bad = [e["path"] for e in entries.values() if not (copy / e["path"]).exists() or sha256(copy / e["path"]) != e["sha256"]]
        same = out("rev-parse", "HEAD", cwd=copy) == out("rev-parse", "HEAD", cwd=r)
        files = len(out("ls-files", cwd=copy).splitlines())
    for rel in bad:
        print(f"MISSING OR DIFFERENT {rel}")
    if bad:
        print(f"Proof FAILED: {len(bad)} of {len(entries)} media files did not come back. Run `media push`, then `proof` again.")
        return 1
    size = sum(e["bytes"] for e in entries.values())
    print(f"Proof passed: a fresh copy from GitHub has all {files} text files and all {len(entries)} media files ({human(size)}), byte for byte.")
    if not same:
        print("This computer has versions GitHub does not have yet. Run `save`.")
    if unsaved:
        print("You also have unsaved changes, and the proof does not cover them. Run `save`.")
    return 0


def cmd_media(args):
    r = root()
    if args.action == "push":
        require_private(r)
        sync_media(r)
        count, size = media_push(r)
        print(f"Uploaded {count} media files ({human(size)}). Run `save` to record the list.")
        return 0
    if args.action == "pull":
        got, failed = media_pull(r)
        print(f"Downloaded {got} files, {len(failed)} missing.")
        for rel in failed:
            print(f"MISSING {rel}")
        return 1 if failed else 0
    if args.action == "ls":
        for e in load_lock(r).values():
            bits = [e.get(k) for k in ("model", "seed", "cost_usd", "prompt_file") if e.get(k) is not None]
            print(f"{human(e['bytes']):>9}  {e['path']}" + (f"  ({', '.join(map(str, bits))})" if bits else ""))
        return 0
    if args.action == "verify":
        entries = load_lock(r)
        bad = 0
        for e in entries.values():
            path = r / e["path"]
            if not path.exists():
                print(f"NOT HERE  {e['path']}")
                bad += 1
            elif sha256(path) != e["sha256"]:
                print(f"CHANGED   {e['path']} (different from the list; `save` records it)")
                bad += 1
        assets = store_assets(r) if out("remote", "get-url", "origin", cwd=r) else None
        if assets is not None:
            for e in entries.values():
                if asset_name(e) not in assets and not e.get("url"):
                    print(f"NOT BACKED UP  {e['path']}")
                    bad += 1
        print(f"{len(entries)} files checked, {bad} problems.")
        return 1 if bad else 0
    if args.action == "forget":
        if not args.file:
            raise Stop("Usage: media forget <listed path>")
        entries = load_lock(r)
        rel = Path(args.file).as_posix()
        if entries.pop(rel, None) is None:
            raise Stop(f"{rel} is not on the list.")
        write_lock(r, entries)
        print(f"{rel} is off the list. Earlier versions still have it.")
        return 0
    if args.action == "note":
        if not args.file:
            raise Stop("Usage: media note <file> --prompt-file f --model m --seed s --cost 0.42 --job id --url u --status approved|rejected --note text")
        sync_media(r)
        rel = Path(args.file).resolve().relative_to(r.resolve()).as_posix()
        entries = load_lock(r)
        if rel not in entries:
            raise Stop(f"{rel} is not media, or is in a folder that is not backed up (renders/, tmp/).")
        for key, value in (("prompt_file", args.prompt_file), ("prompt", args.prompt), ("model", args.model), ("seed", args.seed),
                           ("cost_usd", args.cost), ("job", args.job), ("url", args.url), ("note", args.note), ("status", args.status)):
            if value is not None:
                entries[rel][key] = value
        write_lock(r, entries)
        print(f"Recorded how {rel} was made.")
        return 0
    return 2


def check_pre_push(r: Path) -> int:
    """Git feeds one line per ref: local-ref local-sha remote-ref remote-sha."""
    for line in sys.stdin:
        parts = line.split()
        if len(parts) != 4:
            continue
        _local_ref, local, remote_ref, remote = parts
        if set(local) == {"0"} and not remote_ref.startswith("refs/heads/try/"):
            print(f"STOP. This would delete {remote_ref} on GitHub. Nothing was pushed.", file=sys.stderr)
            return 2
        if set(remote) != {"0"} and set(local) != {"0"}:
            known = git("cat-file", "-e", remote, cwd=r, check=False).returncode == 0
            if not known or git("merge-base", "--is-ancestor", remote, local, cwd=r, check=False).returncode != 0:
                print(f"STOP. This would overwrite versions of {remote_ref} on GitHub. Nothing was pushed. Run `save`: it merges them instead.", file=sys.stderr)
                return 2
    return 0


def cmd_check(args):
    r = root()
    if args.pre_push:
        return check_pre_push(r)
    problems = check_files(r, staged=args.staged)
    if args.history:
        problems += check_history(r)
    if not args.staged:
        v = visibility(r)
        if v and v.get("visibility") == "PUBLIC":
            problems.append(f"{v.get('nameWithOwner')} is PUBLIC. Make it private: gh repo edit --visibility private --accept-visibility-change-consequences")
    if problems:
        print("STOP. Not safe to save:\n" + "\n".join(f"- {p}" for p in problems), file=sys.stderr)
        return 2
    if not args.staged:
        print("All clear: no secrets, no media in git" + (", repo is private." if out("remote", "get-url", "origin", cwd=r) else "."))
    return 0


def cmd_invite(args):
    r = root()
    v = visibility(r)
    if not v:
        raise Stop("Connect to GitHub first.")
    gh("api", "-X", "PUT", f"repos/{v['nameWithOwner']}/collaborators/{args.user}", "-f", f"permission={args.role}", cwd=r)
    print(f"Invited {args.user} to {v['nameWithOwner']} ({args.role}). They get an email and must accept it.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor").set_defaults(fn=cmd_doctor)
    p = sub.add_parser("new")
    p.add_argument("dir")
    p.add_argument("--kind", choices=["video", "code"], default="video")
    p.set_defaults(fn=cmd_new)
    p = sub.add_parser("adopt")
    p.add_argument("dir", nargs="?", default=".")
    p.add_argument("--apply", action="store_true")
    p.set_defaults(fn=cmd_adopt)
    p = sub.add_parser("connect")
    p.add_argument("--name")
    p.add_argument("--owner")
    p.set_defaults(fn=cmd_connect)
    p = sub.add_parser("save")
    p.add_argument("message")
    p.set_defaults(fn=cmd_save)
    p = sub.add_parser("approve")
    p.add_argument("step")
    p.add_argument("note")
    p.set_defaults(fn=cmd_approve)
    p = sub.add_parser("ship")
    p.add_argument("file")
    p.add_argument("--note")
    p.add_argument("--tag")
    p.set_defaults(fn=cmd_ship)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("proof").set_defaults(fn=cmd_proof)
    p = sub.add_parser("versions")
    p.add_argument("-n", type=int, default=20)
    p.set_defaults(fn=cmd_versions)
    p = sub.add_parser("back")
    p.add_argument("version")
    p.add_argument("paths", nargs="*")
    p.set_defaults(fn=cmd_back)
    p = sub.add_parser("try")
    p.add_argument("name")
    p.set_defaults(fn=cmd_try)
    p = sub.add_parser("keep")
    p.add_argument("name")
    p.set_defaults(fn=cmd_keep)
    p = sub.add_parser("drop")
    p.add_argument("name")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_drop)
    sub.add_parser("restore").set_defaults(fn=cmd_restore)
    p = sub.add_parser("media")
    p.add_argument("action", choices=["push", "pull", "verify", "ls", "note", "forget"])
    p.add_argument("file", nargs="?")
    p.add_argument("--prompt-file", dest="prompt_file")
    p.add_argument("--prompt")
    p.add_argument("--model")
    p.add_argument("--seed")
    p.add_argument("--cost", type=float)
    p.add_argument("--job")
    p.add_argument("--url")
    p.add_argument("--note")
    p.add_argument("--status", choices=["approved", "rejected"])
    p.set_defaults(fn=cmd_media)
    p = sub.add_parser("check")
    p.add_argument("--staged", action="store_true")
    p.add_argument("--history", action="store_true")
    p.add_argument("--pre-push", dest="pre_push", action="store_true")
    p.set_defaults(fn=cmd_check)
    p = sub.add_parser("invite")
    p.add_argument("user")
    p.add_argument("--role", default="push", choices=["pull", "triage", "push", "maintain", "admin"])
    p.set_defaults(fn=cmd_invite)
    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except Stop as e:
        print(f"STOP. {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
