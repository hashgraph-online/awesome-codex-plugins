# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""学习记录归档：两步走，先出方案再执行。只用标准库。

1. 出方案（不动任何文件）：
   python archive.py scan --inbox ~/Downloads --workspace <工作区> [--days 3] [--out plan.json]
   方案默认写到系统临时目录的 kaoyan-archive/ 下，不往工作区里写。
   找收件夹里最近 N 天的 .md / .txt，和工作区里已有的文件逐字节比对，相同的标 duplicate，
   其余标 classify，等模型读开头几行后填 subject、stage、dest，并把 action 改成 move 或 pending。

2. 执行：
   python archive.py apply plan.json [--log 99_整理记录/学习记录归档日志.md] [--dry-run]
   只移动 action 为 move 的项；移动前确认源文件还在收件夹里、不是符号链接、内容没变，
   目标在工作区里且没有同名文件。日志路径也必须在工作区里，否则一个文件都不动。
   duplicate、pending、classify 都留在原处，不删除。最后在日志末尾追加一节。

收件夹里的符号链接不进方案：移动它等于移动链接指向的别处的文件。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "node_modules", "_build", "__pycache__", ".work"}
DEFAULT_EXT = (".md", ".txt")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def walk(root: Path, exts: tuple[str, ...]):
    for p in root.rglob("*"):
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts[:-1]):
            continue
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def scan(inbox: Path, workspace: Path, days: float, exts: tuple[str, ...], now: float | None = None) -> dict:
    now = now or time.time()
    recent = sorted((p for p in inbox.iterdir() if p.is_file() and not p.is_symlink() and p.suffix.lower() in exts
                     and now - p.stat().st_mtime <= days * 86400), key=lambda p: p.stat().st_mtime)
    sizes = {p.stat().st_size for p in recent}
    index: dict[str, str] = {}
    inbox_r = inbox.resolve()
    for q in walk(workspace, exts):
        if q.resolve().parent == inbox_r or q.stat().st_size not in sizes:
            continue
        index.setdefault(sha256(q), q.relative_to(workspace).as_posix())
    items = []
    for p in recent:
        digest = sha256(p)
        dup = index.get(digest)
        items.append({"src": str(inbox_r / p.name), "name": p.name, "size": p.stat().st_size,
                      "mtime": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"),
                      "sha256": digest, "action": "duplicate" if dup else "classify", "dup_of": dup,
                      "subject": None, "stage": None, "dest": None, "note": ""})
    return {"created": datetime.now().isoformat(timespec="seconds"), "inbox": str(inbox.resolve()),
            "workspace": str(workspace.resolve()), "items": items}


def inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def apply(plan: dict, log_rel: str | None, dry_run: bool = False) -> dict:
    ws = Path(plan["workspace"])
    inbox_r = Path(plan["inbox"]).resolve()
    log = None
    if log_rel:
        log = Path(log_rel) if Path(log_rel).is_absolute() else ws / log_rel
        if not inside(log, ws) or log.is_symlink():
            raise ValueError(f"日志路径不在工作区里：{log_rel}。没有移动任何文件。")
    moved, skipped, left = [], [], []
    for it in plan["items"]:
        src = Path(it["src"])
        if it.get("action") != "move":
            left.append(it)
            continue
        if not it.get("dest"):
            skipped.append((it, "没有填 dest"))
            continue
        dest_dir = Path(it["dest"]) if Path(it["dest"]).is_absolute() else ws / it["dest"]
        target = dest_dir / src.name
        if not inside(dest_dir, ws):
            skipped.append((it, "目标不在工作区里"))
        elif src.is_symlink():
            skipped.append((it, "源文件是符号链接，不移动"))
        elif not src.exists():
            skipped.append((it, "源文件已不在"))
        elif src.parent.resolve() != inbox_r:
            skipped.append((it, "源文件不在收件夹里"))
        elif sha256(src) != it["sha256"]:
            skipped.append((it, "源文件出方案后被改过，重新出方案"))
        elif target.exists():
            skipped.append((it, "目标已有同名文件"))
        else:
            if not dry_run:
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(target))
            moved.append((it, target.relative_to(ws).as_posix()))
    if log and not dry_run and (moved or skipped or left):
        log.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"\n## {datetime.now():%Y-%m-%d %H:%M}\n",
                 f"移动 {len(moved)}，跳过 {len(skipped)}，留在原处 {len(left)}。\n"]
        lines += [f"- 移动：`{it['name']}` → `{dst}`（{it.get('subject') or '?'}，{it.get('stage') or '?'}）" for it, dst in moved]
        lines += [f"- 跳过：`{it['name']}`，{why}" for it, why in skipped]
        lines += [f"- 留在原处：`{it['name']}`，{it['action']}"
                  + (f"，与 `{it['dup_of']}` 相同" if it.get("dup_of") else "")
                  + (f"，{it['note']}" if it.get("note") else "") for it in left]
        with log.open("a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    return {"moved": moved, "skipped": skipped, "left": left}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="学习记录归档")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--inbox", type=Path, required=True)
    s.add_argument("--workspace", type=Path, required=True)
    s.add_argument("--days", type=float, default=3)
    s.add_argument("--ext", nargs="+", default=list(DEFAULT_EXT))
    s.add_argument("--out", type=Path)
    a_ = sub.add_parser("apply")
    a_.add_argument("plan", type=Path)
    a_.add_argument("--log")
    a_.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if a.cmd == "scan":
        exts = tuple(e.lower() if e.startswith(".") else f".{e.lower()}" for e in a.ext)
        plan = scan(a.inbox.expanduser(), a.workspace.expanduser(), a.days, exts)
        out = a.out or Path(tempfile.gettempdir()) / "kaoyan-archive" / f"plan_{datetime.now():%Y%m%d_%H%M%S}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        for it in plan["items"]:
            print(f"{it['action']:<10} {it['name']}" + (f"  = {it['dup_of']}" if it["dup_of"] else ""))
        print(f"共 {len(plan['items'])} 份；方案：{out}")
        print(f"PLAN={out}")
        return 0

    plan = json.loads(a.plan.read_text(encoding="utf-8"))
    try:
        res = apply(plan, a.log, a.dry_run)
    except ValueError as e:
        print(e)
        return 2
    tag = "（演练，未移动）" if a.dry_run else ""
    for it, dst in res["moved"]:
        print(f"移动{tag}  {it['name']} → {dst}")
    for it, why in res["skipped"]:
        print(f"跳过  {it['name']}：{why}")
    for it in res["left"]:
        print(f"留在原处  {it['name']}（{it['action']}）")
    return 1 if res["skipped"] else 0


if __name__ == "__main__":
    sys.exit(main())
