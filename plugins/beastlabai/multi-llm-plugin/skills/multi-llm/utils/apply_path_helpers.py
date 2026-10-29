"""Path helper utilities for apply orchestrators.

Provides shared path resolution and JSON file loading functions
extracted from the three apply orchestrators.
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional, Union

from .output_handler import sanitize_prefix


def load_json_file(path: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """Load a JSON file, returning None if not found or invalid."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"ERROR: Failed to load {path}: {e}", file=sys.stderr)
        return None
