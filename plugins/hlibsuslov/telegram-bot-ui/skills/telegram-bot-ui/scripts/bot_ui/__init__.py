"""bot-ui: one versioned source of a Telegram bot interface, shared by the skill, the CLI,
the local Studio and the SDK adapters.

Standard library only. The file format version (SCHEMA_VERSION) is independent of the
tool version, the Bot API version and any SDK version.
"""
from __future__ import annotations

SCHEMA_VERSION = 1
TOOL_VERSION = "0.1.0"
PATCH_FORMAT = "bot-ui-patch/v1"
SNAPSHOT_FORMAT = "bot-ui-snapshot/v1"
