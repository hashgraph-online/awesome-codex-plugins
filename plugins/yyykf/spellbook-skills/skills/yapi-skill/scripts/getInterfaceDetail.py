#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from common import (
    YapiSkillError,
    build_interface_detail_vo,
    load_config,
    parse_interface_url,
    print_json,
    render_interface_detail_markdown,
    yapi_get_interface_detail_raw,
)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Get Yapi interface details (supports interfaceId/projectId or interface page URL)")
    parser.add_argument("--interfaceId", type=int, required=False, help="Yapi interface ID")
    parser.add_argument("--projectId", type=int, required=False, help="Yapi project ID (used to get token from config)")
    parser.add_argument("--url", type=str, default=None, help="Yapi interface page URL (can automatically parse projectId/interfaceId)")
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

        if args.url:
            project_id, interface_id = parse_interface_url(args.url)
        else:
            if args.projectId is None or args.interfaceId is None:
                parser.error("Please provide --url, or provide both --projectId and --interfaceId")
            project_id, interface_id = int(args.projectId), int(args.interfaceId)

        detail = yapi_get_interface_detail_raw(config, interface_id, project_id)
        vo = build_interface_detail_vo(detail)

        if args.format == "markdown":
            md = render_interface_detail_markdown(vo)
            sys.stdout.write(md)
            if not md.endswith("\n"):
                sys.stdout.write("\n")
        else:
            print_json(vo)
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
