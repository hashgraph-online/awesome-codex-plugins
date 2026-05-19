#!/usr/bin/env python3
"""Wrapper for the canonical Thoth init module."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from thoth.init.audit import audit_repository_state
from thoth.init.apply import build_init_preview
from thoth.init.render import (
    DEFAULT_PHASES,
    REQUIRED_AGENT_OS_FILES,
    generate_agent_os_docs,
    generate_codex_hook_projection,
    generate_dashboard,
    generate_host_projections,
    generate_milestones,
    generate_pre_commit_config,
    generate_scripts,
    generate_tests,
    generate_thoth_runtime,
    parse_config,
)
from thoth.init.service import initialize_project


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a Thoth project")
    parser.add_argument("--config", default="{}", help="JSON config payload")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    project_dir = Path.cwd()
    config = parse_config(args.config)
    if args.preview:
        audit = audit_repository_state(project_dir)
        print(json.dumps(build_init_preview(project_dir, audit), ensure_ascii=False, indent=2))
        return 0
    result = initialize_project(config, project_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


__all__ = [
    "DEFAULT_PHASES",
    "REQUIRED_AGENT_OS_FILES",
    "audit_repository_state",
    "build_init_preview",
    "generate_agent_os_docs",
    "generate_codex_hook_projection",
    "generate_dashboard",
    "generate_host_projections",
    "generate_milestones",
    "generate_pre_commit_config",
    "generate_scripts",
    "generate_tests",
    "generate_thoth_runtime",
    "initialize_project",
    "parse_config",
]


if __name__ == "__main__":
    raise SystemExit(main())
