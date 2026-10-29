"""The files omitted from both write legs' check-tree measurements."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from .output_handler import workflow_file_entries


def check_tree_exclusions(
    phase_dir: Path, repo_root: str, *, output_dir: Optional[str] = None,
) -> List[str]:
    """Exclude workflow artifacts while keeping code beside those artifacts.

    A plan's output folder can also be a source directory. Its name alone
    never makes its contents bookkeeping; use the same ownership rule as
    file tracking. The plan itself stays visible, as it was before.
    """
    phase_dir = Path(os.path.abspath(str(phase_dir)))
    entries = workflow_file_entries(
        None, root=repo_root,
        output_dirs=[output_dir or str(phase_dir.parent)],
    )
    for path in (phase_dir, Path(repo_root) / ".multi-llm"):
        try:
            relative = os.path.relpath(str(path), repo_root).replace(os.sep, "/")
        except ValueError:  # pragma: no cover - different Windows drives
            continue
        if relative != "." and relative != ".." and not relative.startswith("../"):
            entries.append(relative + "/")
    return sorted(set(entries))
