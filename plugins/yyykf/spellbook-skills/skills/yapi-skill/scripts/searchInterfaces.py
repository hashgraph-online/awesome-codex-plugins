#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from common import (
    YapiSkillError,
    load_config,
    print_json,
    render_search_results_markdown,
    search_interfaces,
)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Search Yapi interfaces by project name/keyword/path (used to locate interfaceId)")
    parser.add_argument("--projectName", type=str, default=None, help="Project name (fuzzy match, optional)")
    parser.add_argument("--keyword", type=str, default=None, help="Keyword (fuzzy match in interface title, optional)")
    parser.add_argument("--path", type=str, default=None, help="Interface path (fuzzy match, optional)")
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format: json or markdown",
    )
    parser.add_argument("--config", type=str, default=None, help="Config file path (overrides default path)")
    args = parser.parse_args(argv)

    try:
        config_path = Path(args.config).expanduser() if args.config else None
        config, _ = load_config(config_path)
        items = search_interfaces(config, args.projectName, args.keyword, args.path)

        if args.format == "markdown":
            md = render_search_results_markdown(items)
            sys.stdout.write(md)
            if not md.endswith("\n"):
                sys.stdout.write("\n")
        else:
            print_json(items)
        return 0
    except YapiSkillError as e:
        print(str(e), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Cancelled", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unknown error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
