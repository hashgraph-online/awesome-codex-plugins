#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from common import YapiSkillError, default_config_path, normalize_base_url, save_config


def _parse_project_token(value: str) -> Tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("Format must be projectId=token, e.g., 4135=xxxx")
    k, v = value.split("=", 1)
    k = k.strip()
    v = v.strip()
    if not k or not v:
        raise argparse.ArgumentTypeError("projectId or token cannot be empty")
    try:
        int(k)
    except ValueError as e:
        raise argparse.ArgumentTypeError("projectId must be a number") from e
    return k, v


def _parse_bool_arg(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off"):
        return False
    raise YapiSkillError(f"Invalid verify_tls parameter: {value} (supports true/false)")


def _ask(text: str, default: Optional[str] = None) -> str:
    prompt = f"{text}"
    if default is not None:
        prompt += f" (default: {default})"
    prompt += ": "
    val = input(prompt).strip()
    if not val and default is not None:
        return default
    return val


def _ask_bool(text: str, default: bool) -> bool:
    d = "y" if default else "n"
    while True:
        val = _ask(f"{text} [y/n]", d).lower()
        if val in ("y", "yes"):
            return True
        if val in ("n", "no"):
            return False
        print("Please enter y or n", file=sys.stderr)


def _ask_int(text: str, default: int) -> int:
    while True:
        val = _ask(text, str(default))
        try:
            return int(val)
        except ValueError:
            print("Please enter a number", file=sys.stderr)


def build_config_from_args_or_interactive(args: argparse.Namespace) -> Dict[str, Any]:
    base_url = args.base_url
    verify_tls = _parse_bool_arg(args.verify_tls)
    timeout_seconds = args.timeout_seconds
    page_size = args.page_size
    max_pages = args.max_pages

    project_tokens: Dict[str, str] = {}
    for item in args.project_token or []:
        project_tokens[item[0]] = item[1]

    interactive_needed = not base_url or not project_tokens

    if interactive_needed and not sys.stdin.isatty():
        missing: List[str] = []
        if not base_url:
            missing.append("--base-url")
        if not project_tokens:
            missing.append("--project-token")
        raise YapiSkillError(
            "Missing required parameters and currently in non-interactive environment (stdin not TTY), cannot enter interactive initialization.\n"
            f"Please provide parameters: {' '.join(missing)}\n"
            "Example: python3 skills/yapi-skill/scripts/init_config.py "
            "--base-url http://yapi.example.com --project-token 1650=xxxx --force"
        )

    if interactive_needed:
        print("Starting to initialize yapi-skill configuration (JSON file can be manually edited).")
        print("")
        if not base_url:
            base_url = _ask("Please enter Yapi base_url (e.g., https://yapi.example.com)", None).strip()
        if verify_tls is None:
            verify_tls = _ask_bool("Verify certificate? (choose n for self-signed)", True)
        if timeout_seconds is None:
            timeout_seconds = _ask_int("HTTP timeout (seconds)", 60)
        if page_size is None:
            page_size = _ask_int("searchInterfaces page_size", 2000)
        if max_pages is None:
            max_pages = _ask_int("searchInterfaces max_pages", 10)

        if not project_tokens:
            print("")
            print("Please enter project token (at least one).")
            while True:
                pid = _ask("Project ID (press Enter to finish)", None).strip()
                if not pid:
                    break
                try:
                    int(pid)
                except ValueError:
                    print("Project ID must be a number", file=sys.stderr)
                    continue
                token = getpass.getpass("Project token (input hidden): ").strip()
                if not token:
                    print("Token cannot be empty", file=sys.stderr)
                    continue
                project_tokens[pid] = token

    if not base_url:
        raise YapiSkillError("base_url cannot be empty")
    if not project_tokens:
        raise YapiSkillError("project_tokens cannot be empty (configure at least one project token)")

    return {
        "base_url": normalize_base_url(base_url),
        "project_tokens": project_tokens,
        "http": {
            "timeout_seconds": int(timeout_seconds if timeout_seconds is not None else 60),
            "verify_tls": bool(verify_tls if verify_tls is not None else True),
        },
        "search": {
            "page_size": int(page_size if page_size is not None else 2000),
            "max_pages": int(max_pages if max_pages is not None else 10),
        },
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Initialize yapi-skill configuration file (user directory)")
    parser.add_argument("--out", type=str, default=None, help="Output configuration file path (uses system recommended path by default)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing configuration file")

    parser.add_argument("--base-url", dest="base_url", type=str, default=None, help="Yapi base_url")
    parser.add_argument(
        "--project-token",
        dest="project_token",
        action="append",
        type=_parse_project_token,
        help="Project token, format: projectId=token, can be passed multiple times",
    )
    parser.add_argument(
        "--verify-tls",
        dest="verify_tls",
        nargs="?",
        const="true",
        default=None,
        choices=["true", "false"],
        help="Verify certificate (optional true/false; defaults to true if omitted)",
    )
    parser.add_argument(
        "--no-verify-tls",
        dest="verify_tls",
        action="store_const",
        const="false",
        help="Do not verify certificate (equivalent to --verify-tls false)",
    )
    parser.add_argument("--timeout-seconds", dest="timeout_seconds", type=int, default=None, help="HTTP timeout in seconds")
    parser.add_argument("--page-size", dest="page_size", type=int, default=None, help="Items per page for searchInterfaces")
    parser.add_argument("--max-pages", dest="max_pages", type=int, default=None, help="Maximum pages for searchInterfaces")

    args = parser.parse_args(argv)

    out_path = Path(args.out).expanduser() if args.out else default_config_path()
    if out_path.exists() and not args.force:
        print(f"Configuration file already exists: {out_path}\nUse --force to overwrite", file=sys.stderr)
        return 2

    try:
        config = build_config_from_args_or_interactive(args)
        saved = save_config(config, out_path)
    except YapiSkillError as e:
        print(str(e), file=sys.stderr)
        return 2

    print("Configuration initialization complete:")
    print(str(saved))
    print("")
    print("Next steps:")
    print("1) Search interfaces: python3 skills/yapi-skill/scripts/searchInterfaces.py --keyword login --format markdown")
    print("2) Get details: python3 skills/yapi-skill/scripts/getInterfaceDetail.py --projectId <project_id> --interfaceId <interface_id> --format markdown")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
