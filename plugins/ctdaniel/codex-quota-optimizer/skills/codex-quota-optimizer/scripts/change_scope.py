#!/usr/bin/env python3
"""Summarize Git change scope and suggest a minimal verification level."""
from __future__ import annotations
import subprocess


def run(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def main() -> None:
    names = run("diff", "--name-only").splitlines()
    staged = run("diff", "--cached", "--name-only").splitlines()
    files = sorted(set(filter(None, names + staged)))
    print(f"Changed files: {len(files)}")
    for f in files[:60]:
        print(f"- {f}")
    if len(files) > 60:
        print(f"- ... +{len(files)-60} more")

    if not files:
        print("Suggested verification: none yet; identify the change surface first.")
        return

    code = [f for f in files if f.endswith((".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".kt", ".rb", ".php"))]
    config = [f for f in files if f.endswith((".json", ".yaml", ".yml", ".toml", ".lock"))]
    tests = [f for f in files if "test" in f.lower() or "spec" in f.lower()]

    if len(files) <= 3 and len(code) <= 2:
        level = "Level 1–2: touched-file checks + closest focused test."
    elif len(files) <= 12:
        level = "Level 2–3: focused tests + package type/lint/test as relevant."
    else:
        level = "Level 3–4: package checks; consider full suite if change is cross-cutting."

    print(f"Code files: {len(code)} | Config/lock files: {len(config)} | Test/spec files: {len(tests)}")
    print(f"Suggested verification: {level}")


if __name__ == "__main__":
    main()
