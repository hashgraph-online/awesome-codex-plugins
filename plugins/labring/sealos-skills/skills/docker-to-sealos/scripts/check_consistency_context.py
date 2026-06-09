#!/usr/bin/env python3
"""Context builder layer for consistency checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Tuple

from check_consistency_models import ScanContext, Violation
from check_consistency_parser import build_context


@dataclass(frozen=True)
class ContextBuilder:
    skill_path: Path
    references_dir: Path
    include_paths: Sequence[str]

    def build(self) -> Tuple[ScanContext, list[Violation]]:
        return build_context(
            skill_path=self.skill_path,
            references_dir=self.references_dir,
            include_paths=self.include_paths,
        )
