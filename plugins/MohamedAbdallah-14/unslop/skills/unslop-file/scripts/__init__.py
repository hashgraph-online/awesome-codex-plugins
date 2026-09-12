"""Tools to humanize natural-language Markdown — strip AI-isms, engineer burstiness,
preserve every code block, URL, and heading exactly. Two modes: deterministic (regex)
and LLM (Anthropic SDK or `claude --print` fallback).

The single source of truth for the package version is this `__version__`.
`pyproject.toml` reads it via `dynamic = ["version"]` + `tool.setuptools.dynamic`.
"""

__all__ = [
    "cli",
    "humanize",
    "detect",
    "validate",
    "structural",
    "soul",
    "stylometry",
    "style_memory",
    "detector",
]
__version__ = "0.7.0"
