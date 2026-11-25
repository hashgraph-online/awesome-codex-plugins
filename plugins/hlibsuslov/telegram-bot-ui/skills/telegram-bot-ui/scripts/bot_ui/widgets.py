"""Widget workbench backend: source -> assemble -> build_widget (lint, check, zlib-9) -> payload.

A widget lives in widgets/<id>/: widget.json, an entry HTML file and optional local files.
An optional design.json is a design profile (skill scripts/widget_design.py) applied at build.
`<!--@file style.css-->` in the entry inlines a local file as <style>/<script> in place, so the
split keeps the order of styles and scripts; `<!--@file logo.svg-->` inlines raw <svg> markup. Kit partials (`<!--@kit runtime.js-->`) come
from widgets/_kit/ in the project (vendored by `bot-ui init`), else from the skill.

Every build is bound to `sourceHash` = sha256 of the widget's source bytes, the kit and the
options (language, caption). Export refuses a build whose hash is not the current one.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from typing import Any

from . import builder, render
from .project import Snapshot, normalize_bytes
from .skill import kit_dir as skill_kit_dir
from .skill import load

FILE_MARK = re.compile(r"<!--\s*@file\s+([\w.-]+)\s*-->")


class WidgetError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code, self.message = code, message


def _project_kit(snap: Snapshot) -> dict[str, bytes]:
    return {rel[len("widgets/_kit/"):]: data for rel, data in snap.files.items() if rel.startswith("widgets/_kit/")}


def assemble(snap: Snapshot, wid: str, lang: str | None = None, state: str | None = None) -> str:
    w = snap.widgets.get(wid)
    if w is None:
        raise WidgetError("WIDGET_NOT_FOUND", f"widget {wid} does not exist")
    if builder.active(w):  # generated from widget.json; `state` only for preview builds
        dl = (snap.project or {}).get("defaultLocale", "en")
        try:
            return builder.generate(w["builder"], lang, builder.assets_of(snap, wid), default_locale=dl,
                                    langs=w.get("languages") or None, state=state)
        except ValueError as err:
            raise WidgetError("BUILDER_INVALID", str(err))
    base = f"widgets/{wid}/"
    entry = base + w.get("entry", "index.html")
    if entry not in snap.files:
        raise WidgetError("WIDGET_ENTRY_MISSING", f"{entry} does not exist")
    text = normalize_bytes(snap.files[entry]).decode("utf-8")

    def sub(m: re.Match) -> str:
        rel = base + m.group(1)
        if rel not in snap.files:
            raise WidgetError("WIDGET_FILE_MISSING", f"{rel} (from {m.group(0)}) does not exist")
        body = normalize_bytes(snap.files[rel]).decode("utf-8")
        if rel.endswith(".svg"):  # raw inline <svg> markup (profile 1: no <image>, no data: images)
            body = re.sub(r"^\s*<\?xml[^>]*>\s*", "", body)
            # Inline SVG in HTML needs no namespace; its URL would read as an external link.
            body = re.sub(r'\s+xmlns(:xlink)?="http://www\.w3\.org/[^"]*"', "", body)
            return body.rstrip("\n")
        tag = "style" if rel.endswith(".css") else "script" if rel.endswith(".js") else None
        if tag is None:
            raise WidgetError("WIDGET_FILE_TYPE", f"{rel}: only .css, .js and .svg files can be inlined")
        return f"<{tag}>\n{body}</{tag}>"

    return FILE_MARK.sub(sub, text)


def source_hash(snap: Snapshot, wid: str, options: dict) -> str:
    h = hashlib.sha256()
    for rel in sorted(r for r in snap.files if r.startswith(f"widgets/{wid}/") or r.startswith("widgets/_kit/")):
        h.update(rel.encode() + b"\0" + normalize_bytes(snap.files[rel]) + b"\0")
    h.update(json.dumps(options, sort_keys=True, ensure_ascii=False).encode())
    if builder.active(snap.widgets.get(wid)):  # widget.json (the config) is hashed above; add the generator
        h.update(builder.GENERATOR.encode())
    return "sha256:" + h.hexdigest()


def caption_for(snap: Snapshot, wid: str, lang: str, values: dict | None = None) -> str | None:
    w = snap.widgets[wid]
    p = snap.project or {}
    raw = render.localized(w.get("caption"), lang, p.get("defaultLocale", "en"))
    if raw is None:
        return None
    text, _ = render.fill(raw, values or {}, "regular.plain")
    return text


def build(snap: Snapshot, wid: str, *, lang: str | None = None, values: dict | None = None,
          strict: bool = True, state: str | None = None) -> dict[str, Any]:
    bw = load("build_widget")
    p = snap.project or {}
    lang = lang or p.get("defaultLocale", "en")
    caption = caption_for(snap, wid, lang, values)
    options = {"lang": lang, "caption": caption, "strict": strict}
    w = snap.widgets.get(wid)
    if not (builder.active(w) and builder.is_preview_state(w["builder"], state)):
        state = None  # production/export builds: the default state, not in the hash
    else:
        options["state"] = state
    shash = source_hash(snap, wid, options)
    try:
        src = assemble(snap, wid, lang, state)
    except WidgetError as err:
        return {"ok": False, "widget": wid, "lang": lang, "sourceHash": shash, "errors": [f"[{err.code}] {err.message}"],
                "warnings": [], "html": "", "rawBytes": 0, "compressedBytes": 0, "limits": _limits(bw)}
    try:
        design = design_of(snap, wid)
    except WidgetError as err:
        return {"ok": False, "widget": wid, "lang": lang, "sourceHash": shash, "errors": [f"[{err.code}] {err.message}"],
                "warnings": [], "html": "", "rawBytes": 0, "compressedBytes": 0, "limits": _limits(bw)}
    kit = _project_kit(snap)
    with tempfile.TemporaryDirectory(prefix="bot-ui-kit-") as tmp:
        kd = skill_kit_dir()
        if kit:
            for name, data in kit.items():
                with open(os.path.join(tmp, name), "wb") as fh:
                    fh.write(normalize_bytes(data))
            kd = tmp
        res = bw.build_text(src, caption=caption or None, strict=strict, kit_dir=kd, langs=(lang,), design=design)
        plain = bw.build_text(src, caption=caption or None, kit_dir=kd, langs=(lang,)) if res.design_css else None
    out = {"ok": res.ok, "widget": wid, "lang": lang, "sourceHash": shash, "caption": caption, "html": res.html,
           "previewState": state,
           "rawBytes": res.raw_bytes, "compressedBytes": res.compressed_bytes, "includes": res.includes,
           "errors": res.errors, "warnings": res.warnings, "limits": _limits(bw), "summary": res.summary() if res.ok else ""}
    if design is not None:
        wd = load("widget_design")
        out["design"] = {"css": res.design_css, "bytes": res.compressed_bytes - plain.compressed_bytes if plain else 0,
                         "contrast": wd.contrast_report(design)}
    return out


def design_of(snap: Snapshot, wid: str) -> dict | None:
    """The widget's design profile (widgets/<id>/design.json), or None when it has none."""
    raw = snap.files.get(f"widgets/{wid}/design.json")
    if raw is None:
        return None
    try:
        design = json.loads(normalize_bytes(raw).decode("utf-8"))
    except ValueError as err:
        raise WidgetError("DESIGN_INVALID", f"widgets/{wid}/design.json is not valid JSON: {err}") from err
    if not isinstance(design, dict):
        raise WidgetError("DESIGN_INVALID", f"widgets/{wid}/design.json must be an object")
    return design


def _limits(bw) -> dict:
    return {"rawBytes": bw.HTML_MAX_BYTES, "compressedBytes": bw.HTML_MAX_COMPRESSED, "dataBytes": bw.DATA_MAX_BYTES}


def payload(snap: Snapshot, wid: str, built: dict, *, chat_id: int | str = 111111111, state: str = "default",
            reply_markup: dict | None = None) -> dict:
    """sendWidget request for a successful build, with the demo state of widget.json."""
    bw = load("build_widget")
    w = snap.widgets[wid]
    st = (w.get("states") or {}).get(state) or {}
    send = w.get("send") or {}
    allow = send.get("allow_queries", False) or (isinstance(w.get("builder"), dict) and builder.needs_queries(w["builder"]))
    return bw.payload(built["html"], chat_id=chat_id, caption=built.get("caption"), chat_data=st.get("chatData"),
                      public_data=st.get("publicData"), shared=send.get("is_shared", False),
                      allow_queries=allow, reply_markup=reply_markup,
                      width=send.get("width"), height=send.get("height"))


def export(snap: Snapshot, wid: str, built: dict, expected_hash: str) -> dict:
    """Refuse a stale build: the hash must match the current sources and options."""
    options = {"lang": built["lang"], "caption": built.get("caption"), "strict": True}
    current = source_hash(snap, wid, options)
    if built.get("previewState") or expected_hash != current or built.get("sourceHash") != current:
        raise WidgetError("STALE_BUILD", "the build is not of the current sources; rebuild before export")
    if not built.get("ok"):
        raise WidgetError("BUILD_FAILED", "the build has errors; fix them before export")
    return {"html": built["html"], "payload": payload(snap, wid, built), "sourceHash": current}


def split_html(single: str) -> dict[str, str]:
    """Import a single-file widget as index.html + style.css + widget.js, reversibly: only one
    <style> and one <script> without attributes are split out; anything else stays inline.
    assemble() of the result reproduces `single` byte for byte (checked by the caller)."""
    styles = list(re.finditer(r"<style>\n(.*?)</style>", single, re.S))
    scripts = list(re.finditer(r"<script>\n(.*?)</script>", single, re.S))
    files: dict[str, str] = {}
    out = single
    if len(scripts) == 1:
        m = scripts[0]
        files["widget.js"] = m.group(1)
        out = out[:m.start()] + "<!--@file widget.js-->" + out[m.end():]
    if len(styles) == 1:
        m = re.search(r"<style>\n(.*?)</style>", out, re.S)
        files["style.css"] = m.group(1)
        out = out[:m.start()] + "<!--@file style.css-->" + out[m.end():]
    files["index.html"] = out
    return files


def mock_answers(snap: Snapshot, wid: str) -> dict:
    """Precomputed answers of the gallery handler named in widget.json mock.handler."""
    w = snap.widgets[wid]
    if isinstance(w.get("builder"), dict):  # also after eject: the requests are the generated ones
        return builder.mock_answers(w["builder"])
    handler = (w.get("mock") or {}).get("handler", "")
    if not handler.startswith("gallery:"):
        return {}
    pw = load("preview_widget")
    demo = {k: w[k] for k in ("states", "queries", "fresh", "now", "caption") if k in w}
    return pw.precomputed_answers(handler.split(":", 1)[1], demo)


def preview_runtime() -> dict:
    """The skill's mock runtime (JS) and default CSS for the sandboxed preview frame, plus the
    design-profile catalogue (slots, options, presets) the Design tab draws its controls from."""
    pw = load("preview_widget")
    return {"mock": pw.MOCK_JS, "css": pw.DEFAULT_CSS, "themes": pw.THEMES, "design": load("widget_design").catalog()}


# ------------------------------------------------------------------ new widgets

BLANK_INDEX = """<!-- New widget (private chat). Build with `bot-ui build`.
  chat_data: {"title": "...", "text": "...", "r": 0} -->
<!--@file style.css-->
<div class="k">
  <div class="hd"><span class="tt el" id="ti"></span></div>
  <div class="mt" id="tx"></div>
  <div class="st" id="st"></div>
</div>
<!--@kit runtime.js-->
<!--@kit i18n.js-->
<!--@file widget.js-->
"""
BLANK_CSS = "/*@kit tokens.css*/\n#tx { margin-top: 4px }\n"
BLANK_JS = """/*@lang en*/K.add({ en: { none: "Nothing yet. The bot fills this in." } });/*@end*/
/*@lang ru*/K.add({ ru: { none: "Пока пусто. Бот заполнит это сам." } });/*@end*/
/*@lang uk*/K.add({ uk: { none: "Поки порожньо. Бот заповнить це сам." } });/*@end*/
function draw() {
  var s = K.S.chatData, $ = K.$;
  $("ti").textContent = (s && s.title) || K.t("none");
  $("tx").textContent = (s && s.text) || "";
}
K.start(draw);
"""


def templates() -> list[dict]:
    """Starting points for a new widget: a blank one and every skill gallery widget with a demo."""
    bw = load("build_widget")
    out = [{"id": "blank", "title": "Blank widget", "summary": "Title and text from chat_data, on the widget kit."}]
    # Visual (form-built) widgets right after the blank one; the blank entry stays first.
    out += [{"id": f"builder:{t}", "title": builder.TYPE_SCHEMA[t]["title"], "summary": builder.TYPE_SCHEMA[t]["summary"],
             "icon": builder.TYPE_SCHEMA[t]["icon"], "source": "builder"} for t in builder.TYPES]
    for name in bw.gallery_sources():
        demo_path = os.path.join(bw.DEMO_DIR, name)
        demo_path = demo_path[:-5] + ".json"
        if not os.path.isfile(demo_path):
            continue
        demo = bw.load_demo(demo_path)
        out.append({"id": f"gallery:{name[:-5]}", "title": demo.get("title", name[:-5]), "summary": demo.get("summary", ""),
                    "source": "gallery"})
    # Built examples from the recipes that have no separate source (kept as one HTML file).
    for name in sorted(os.listdir(bw.OUT_DIR)):
        stem = name[:-5]
        if name.endswith(".html") and not os.path.isfile(os.path.join(bw.SRC_DIR, name)):
            out.append({"id": f"recipe:{stem}", "title": stem.replace("-", " ").capitalize(),
                        "summary": "Built example from the skill recipes (one HTML file, no demo states).", "source": "recipe"})
    return out


def creation_patch(snap: Snapshot, widget_id: str, template: str, title: str | None = None) -> dict:
    """bot-ui-patch/v1 that creates widgets/<widget_id>/ from a template (written by write_patch)."""
    from . import PATCH_FORMAT
    from .project import check_id
    if (err := check_id(widget_id)) or "." in widget_id:
        raise WidgetError("WIDGET_ID_INVALID", err or "a widget ID is one segment (no '.')")
    if widget_id in snap.widgets:
        raise WidgetError("WIDGET_EXISTS", f"widget {widget_id} already exists")
    p = snap.project or {}
    locales = p.get("locales") or ["en"]
    bw = load("build_widget")
    if template == "blank":
        files = {"index.html": BLANK_INDEX, "style.css": BLANK_CSS, "widget.js": BLANK_JS}
        title = title or "New widget"
        meta = {"send": {}, "states": {"default": {"chatData": {"title": title, "text": "Edit me in Data and states.", "r": 0}},
                                       "empty": {}}, "queries": [], "fresh": [],
                "dataFields": {"chatData": {
                    "title": {"label": "Title", "type": "text", "help": "Bold first line of the widget."},
                    "text": {"label": "Text", "type": "text", "help": "Second line, smaller."},
                    "r": {"label": "Data version", "type": "number", "advanced": True,
                          "help": "Goes up with every update so the widget ignores older data. The bot sets it."}}}}
        langs = [loc for loc in locales if loc in ("en", "ru", "uk")] or ["en"]
    elif template.startswith("builder:"):
        kind = template.split(":", 1)[1]
        if kind not in builder.TYPES:
            raise WidgetError("TEMPLATE_UNKNOWN", f"no builder type {kind!r}")
        langs = [loc for loc in locales if loc in builder.KIT_LANGS] or ["en"]
        meta, files = builder.creation_files(kind, langs)
        dl = p.get("defaultLocale", "en")
        title = title or builder.TYPE_SCHEMA[kind]["title"]
        caps = {loc: builder.caption_text(meta["builder"], loc, dl) or title for loc in locales}
        meta["caption"] = caps
    elif template.startswith("gallery:"):
        name = template.split(":", 1)[1]
        src = os.path.join(bw.SRC_DIR, name + ".html")
        demo_path = os.path.join(bw.DEMO_DIR, name + ".json")
        if not re.match(r"^[a-z0-9-]+$", name) or not os.path.isfile(src) or not os.path.isfile(demo_path):
            raise WidgetError("TEMPLATE_UNKNOWN", f"no gallery widget {name!r}")
        with open(src, encoding="utf-8") as fh:
            files = split_html(fh.read().replace("\r\n", "\n"))
        demo = bw.load_demo(demo_path)
        title = title or demo.get("title", name)
        meta = {k: demo[k] for k in ("send", "states", "queries", "fresh") if k in demo}
        meta["mock"] = {"handler": f"gallery:{name}"}
        have = set(bw.source_languages("\n".join(files.values())))
        langs = [loc for loc in locales if loc in have] or sorted(have)[:1] or ["en"]
    elif template.startswith("recipe:"):
        name = template.split(":", 1)[1]
        built = os.path.join(bw.OUT_DIR, name + ".html")
        if not re.match(r"^[a-z0-9-]+$", name) or not os.path.isfile(built) or os.path.isfile(os.path.join(bw.SRC_DIR, name + ".html")):
            raise WidgetError("TEMPLATE_UNKNOWN", f"no recipe widget {name!r}")
        with open(built, encoding="utf-8") as fh:
            files = {"index.html": fh.read().replace("\r\n", "\n")}
        title = title or name.replace("-", " ").capitalize()
        meta = {"send": {}, "states": {"default": {}}, "queries": [], "fresh": []}
        langs = [loc for loc in locales if loc == "en"] or locales[:1]
    else:
        raise WidgetError("TEMPLATE_UNKNOWN", f"unknown template {template!r}")
    widget = {"id": widget_id, "title": title, "entry": "index.html", "languages": langs,
              "caption": {loc: title for loc in locales}, **meta, "now": builder.PREVIEW_NOW}
    changes = [{"widgetId": widget_id, "file": "widget.json",
                "content": json.dumps(widget, ensure_ascii=False, indent=2) + "\n"}]
    changes += [{"widgetId": widget_id, "file": name, "content": text} for name, text in files.items()]
    return {"format": PATCH_FORMAT, "projectId": p.get("projectId"), "baseRevision": snap.revision, "changes": changes}


_PREVIEW_CACHE: dict[tuple, dict] = {}


def template_preview(snap: Snapshot, template: str, lang: str | None = None) -> dict:
    """Build a library template in memory (nothing is written) for the library page thumbnails."""
    from .project import parse_files
    lang = lang or (snap.project or {}).get("defaultLocale", "en")
    key = (template, lang, snap.revision if template == "blank" else "")
    if key in _PREVIEW_CACHE:
        return _PREVIEW_CACHE[key]
    patch = creation_patch(snap, "library-preview", template)
    files = dict(snap.files)
    for c in patch["changes"]:
        files[f"widgets/library-preview/{c['file']}"] = c["content"].encode("utf-8")
    tmp = parse_files(snap.root, files)
    meta = tmp.widgets["library-preview"]
    use = lang if lang in (meta.get("languages") or []) else (meta.get("languages") or ["en"])[0]
    built = build(tmp, "library-preview", lang=use)
    state = (meta.get("states") or {}).get("default") or {}
    out = {"template": template, "lang": use, "ok": built["ok"], "html": built["html"] if built["ok"] else "",
           "rawBytes": built["rawBytes"], "compressedBytes": built["compressedBytes"], "errors": built["errors"][:3],
           "chatData": state.get("chatData"), "publicData": state.get("publicData"),
           "languages": meta.get("languages"), "now": meta.get("now")}
    _PREVIEW_CACHE[key] = out
    return out
