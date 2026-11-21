"""Server handlers for the widget gallery (examples/widgets/*.html, Bot API 10.4).

Each h_<name>.py module defines SPEC: the widget's demo state and its decide() function.
core.GalleryBot sends any gallery widget and answers its queries with the shared invariants
(authorization, stale revisions, answer exactly once, coalesced shared edits).
Standard library only; offline with tgkit's FakeTransport.
"""
from .core import Action, BadRequest, Ctx, GalleryBot, SPECS, Spec, load_demo, parse, query, register

register()

__all__ = ["Action", "BadRequest", "Ctx", "GalleryBot", "SPECS", "Spec", "load_demo", "parse", "query", "register"]
