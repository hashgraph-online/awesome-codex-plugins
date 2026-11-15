"""tgkit - small, SDK-independent helpers for the Bot API 10.3/10.4 recipes.

Standard library only. Offline by default (FakeTransport); live calls need an
explicit TELEGRAM_LIVE=1 and a test bot token (see transport.py).

Verified against the official Bot API docs on 2026-11-12 (Bot API 10.4).
This is example/harness code to copy and adapt, not a published package.
"""
__version__ = "0.1.0"
BOT_API_VERSION = "10.4"
