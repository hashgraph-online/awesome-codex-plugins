#!/usr/bin/env python3
"""Build a Telegram HTML widget (Bot API 10.4) from a source file and the widget kit.

  py -3 scripts/build_widget.py examples/widgets/src/metrics-dashboard.html -o out.html
  py -3 scripts/build_widget.py SRC --payload payload.json --chat-id 111 --caption "..." \
        [--chat-data JSON] [--public-data JSON] [--shared] [--allow-queries] [--widget-id ID]
  py -3 scripts/build_widget.py SRC --demo examples/widgets/demo/NAME.json --payload p.json
  py -3 scripts/build_widget.py --all [--check]      # the gallery: src/ -> examples/widgets/

What it does, in order:
1. Inlines kit partials from examples/widgets/_kit/: `<!--@kit tokens.css-->` becomes a
   <style>/<script> element; `/*@kit chart.js*/` inside an existing <style>/<script> inserts
   the raw text (one element instead of two, fewer bytes).
2. Minifies safely: comments go, indentation and blank lines go, spaces around punctuation go;
   strings, template literals and regular expressions are kept byte for byte, and JavaScript
   keeps its line breaks except where a join cannot change the meaning (no ASI surprises).
3. Measures exactly like the server: UTF-8 bytes (<= 32768) and zlib level 9 (<= 4096).
4. Fails on anything the runtime lacks (network, external URLs, form controls, vh, ...) via
   tgkit.widgets.check_widget, plus scripts/widget_lint.py errors; --strict also fails on lint
   warnings (the gallery is built with --strict).
5. Writes the final HTML and, on request, a ready sendWidget / sendSharedWidget payload.

Offline: no token, no network. A passing build proves the static contract only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "examples", "python"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tgkit.widgets import (DATA_MAX_BYTES, HTML_MAX_BYTES, HTML_MAX_COMPRESSED, check_widget,  # noqa: E402
                           compressed_size)
import widget_lint  # noqa: E402

KIT_DIR = os.path.join(ROOT, "examples", "widgets", "_kit")
SRC_DIR = os.path.join(ROOT, "examples", "widgets", "src")
OUT_DIR = os.path.join(ROOT, "examples", "widgets")
DEMO_DIR = os.path.join(ROOT, "examples", "widgets", "demo")

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


# ---------------------------------------------------------------- includes

_ELEMENT_MARK = re.compile(r"<!--\s*@kit\s+([\w.-]+)\s*-->")
_RAW_MARK = re.compile(r"/\*\s*@kit\s+([\w.-]+)\s*\*/")


def _kit_file(name: str, kit_dir: str) -> str:
    path = os.path.join(kit_dir, name)
    if os.path.dirname(os.path.normpath(name)) or not os.path.isfile(path):
        raise BuildError(f"unknown kit partial {name!r} (looked in {os.path.relpath(kit_dir, ROOT)})")
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def inline_kit(src: str, kit_dir: str = KIT_DIR) -> tuple[str, list[str]]:
    used: list[str] = []

    def element(m: re.Match) -> str:
        name = m.group(1)
        used.append(name)
        if name.endswith(".css"):
            return f"<style>{_KIT_CSS[0]}{_kit_file(name, kit_dir)}{_KIT_CSS[1]}</style>"
        return f"<script>\n{_kit_file(name, kit_dir)}\n</script>"

    def raw(m: re.Match) -> str:
        used.append(m.group(1))
        text = _kit_file(m.group(1), kit_dir)
        return f"{_KIT_CSS[0]}{text}{_KIT_CSS[1]}" if m.group(1).endswith(".css") else text

    return _RAW_MARK.sub(raw, _ELEMENT_MARK.sub(element, src)), used


_KIT_CSS = ("/*@kitcss{*/", "/*}@kitcss*/")
_LANG_BLOCK = re.compile(r"/\*@lang ([\w-]+)\*/(.*?)/\*@end\*/", re.S)


def select_languages(html: str, langs: tuple[str, ...]) -> str:
    """Keep only the string blocks of the languages this build is for. The bot sends the
    build that matches the user's language_code: one language costs a third of three."""
    found = {m[0] for m in _LANG_BLOCK.findall(html)}
    if found and not found & set(langs):
        raise BuildError(f"no strings for {', '.join(langs)} (the source has {', '.join(sorted(found))})")
    return _LANG_BLOCK.sub(lambda m: m.group(2) if m.group(1) in langs else "", html)


def _split_rules(css: str) -> list[str]:
    rules, depth, start = [], 0, 0
    for i, c in enumerate(css):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                rules.append(css[start:i + 1])
                start = i + 1
    return rules


def _used(selector: str, rest: str) -> bool:
    return all(re.search(rf"(?<![\w-]){re.escape(c)}(?![\w-])", rest)
               for c in re.findall(r"\.([A-Za-z_][\w-]*)", selector))


def prune_kit_css(html: str) -> str:
    """Drop kit rules whose classes appear nowhere else in the document (markup, the widget's
    own CSS, script strings). Only kit rules are pruned; the widget's own rules are kept."""
    pat = re.compile(re.escape(_KIT_CSS[0]) + r"(.*?)" + re.escape(_KIT_CSS[1]), re.S)
    rest = pat.sub("", html)

    def prune(css: str) -> str:
        out = []
        for rule in _split_rules(minify_css(css)):
            head, body = rule.split("{", 1)
            if head.startswith("@"):
                inner = prune(body[:-1])
                if inner:
                    out.append(head + "{" + inner + "}")
            elif any(_used(sel, rest) for sel in head.split(",")):
                out.append(rule)
        return "".join(out)

    html = pat.sub(lambda m: prune(m.group(1)), html)
    # Then drop kit custom properties (--k-*) that nothing reads any more.
    for name in sorted(set(re.findall(r"(--k-[\w-]+):", html))):
        if not re.search(re.escape(f"var({name}") + r"[,)]", html):
            html = re.sub(re.escape(name) + r":[^;}]*;?", "", html, count=1)
    return html


# ---------------------------------------------------------------- minify

_JS_TIGHT = set("{}()[];,:=<>!&|?*%^~")
_REGEX_AFTER = set("(,=:[!&|?{};+-*%<>~^")
_REGEX_KEYWORDS = {"return", "typeof", "case", "in", "of", "void", "delete", "instanceof", "new", "throw", "else"}
_JOIN_AFTER = tuple("{([,;:=&|?")
_JOIN_BEFORE = tuple("})].,?:&|")


def _scan_string(s: str, i: int) -> int:
    """Index just past the string/template literal starting at s[i]."""
    q, i = s[i], i + 1
    while i < len(s):
        if s[i] == "\\":
            i += 2
            continue
        if s[i] == q:
            return i + 1
        i += 1
    raise BuildError("unterminated string literal in script")


def _scan_regex(s: str, i: int) -> int:
    i += 1
    in_class = False
    while i < len(s):
        c = s[i]
        if c == "\\":
            i += 2
            continue
        if c == "[":
            in_class = True
        elif c == "]":
            in_class = False
        elif c == "/" and not in_class:
            i += 1
            while i < len(s) and (s[i].isalnum()):
                i += 1
            return i
        elif c == "\n":
            raise BuildError("unterminated regular expression in script")
        i += 1
    raise BuildError("unterminated regular expression in script")


def minify_js(s: str) -> str:
    out: list[str] = []
    lits: list[str] = []          # strings, templates and regexes, restored verbatim at the end

    def keep(text: str) -> None:
        out.append(f"\x00{len(lits)}\x00")
        lits.append(text)

    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in "\"'`":
            j = _scan_string(s, i)
            keep(s[i:j])
            i = j
        elif s.startswith("//", i):
            j = s.find("\n", i)
            i = n if j < 0 else j
        elif s.startswith("/*", i):
            j = s.find("*/", i + 2)
            if j < 0:
                raise BuildError("unterminated comment in script")
            i = j + 2
            out.append(" ")
        elif c == "/":
            prev = "".join(out).rstrip().replace("\x00", "")
            word = re.search(r"([A-Za-z_$][\w$]*)$", prev)
            if not prev or prev[-1] in _REGEX_AFTER or (word and word.group(1) in _REGEX_KEYWORDS):
                j = _scan_regex(s, i)
                keep(s[i:j])
                i = j
            else:
                out.append(c)
                i += 1
        elif c in " \t\r\n":
            j = i
            while j < n and s[j] in " \t\r\n":
                j += 1
            out.append("\n" if "\n" in s[i:j] else " ")
            i = j
        else:
            out.append(c)
            i += 1
    code = _tighten_js("".join(out))
    return re.sub(r"\x00(\d+)\x00", lambda m: lits[int(m.group(1))], code)


def _tighten_js(code: str) -> str:
    """Drop spaces next to punctuation and safe line breaks (literals are placeholders here)."""
    code = re.sub(r"[ ]*\n[ \n]*", "\n", code)
    code = re.sub(r" +", " ", code)
    code = re.sub(r" ?([{}()\[\];,:=<>!&|?*%^~]) ?", r"\1", code)
    lines = [ln.strip() for ln in code.split("\n")]
    joined: list[str] = []
    for ln in lines:
        if not ln:
            continue
        if joined and (joined[-1].endswith(_JOIN_AFTER) or ln.startswith(_JOIN_BEFORE)):
            joined[-1] += ln
        else:
            joined.append(ln)
    return "\n".join(joined)


def minify_css(s: str) -> str:
    parts = re.split(r"(\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')", s)
    res = []
    for k, p in enumerate(parts):
        if k % 2:
            res.append(p)
            continue
        p = re.sub(r"/\*.*?\*/", "", p, flags=re.S)
        p = re.sub(r"\s+", " ", p)
        p = re.sub(r" ?([{};,>]) ?", r"\1", p)
        p = re.sub(r": ", ":", p)
        p = p.replace(";}", "}").replace(" !important", "!important")
        res.append(p)
    return "".join(res).strip()


def minify_html(html: str) -> str:
    pieces = re.split(r"(<style[^>]*>.*?</style>|<script[^>]*>.*?</script>)", html, flags=re.S | re.I)
    out = []
    for k, p in enumerate(pieces):
        if k % 2:
            m = re.match(r"(<(style|script)[^>]*>)(.*?)(</\2>)", p, re.S | re.I)
            body = minify_css(m.group(3)) if m.group(2).lower() == "style" else minify_js(m.group(3))
            out.append(m.group(1) + body + m.group(4))
            continue
        p = re.sub(r"<!--.*?-->", "", p, flags=re.S)
        p = re.sub(r">\s*\n\s*<", "><", p)
        p = re.sub(r"\s*\n\s*", " ", p)
        p = re.sub(r"[ \t]{2,}", " ", p)
        out.append(p)
    return "".join(out).strip()


# ---------------------------------------------------------------- build

class BuildError(Exception):
    pass


@dataclass
class BuildResult:
    html: str
    raw_bytes: int
    compressed_bytes: int
    includes: list[str]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        pct = 100 * self.compressed_bytes / HTML_MAX_COMPRESSED
        return (f"{self.raw_bytes} bytes raw (limit {HTML_MAX_BYTES}), {self.compressed_bytes} bytes zlib-9 "
                f"(limit {HTML_MAX_COMPRESSED}, {pct:.0f}%, budget {widget_lint.BUDGET}); "
                f"kit: {', '.join(self.includes) or 'none'}")


def build_text(src: str, *, caption: str | None = "x", strict: bool = False, minify: bool = True,
               kit_dir: str = KIT_DIR, chat_data: str | None = None, public_data: str | None = None,
               langs: tuple[str, ...] = ("en",)) -> BuildResult:
    try:
        html, used = inline_kit(src, kit_dir)
        html = select_languages(html, langs)
        if minify:
            html = minify_html(prune_kit_css(html))
        else:
            html = html.replace(_KIT_CSS[0], "").replace(_KIT_CSS[1], "")
    except BuildError as err:
        return BuildResult(src, 0, 0, [], errors=[str(err)])
    rep = check_widget(html, caption=caption, chat_data=chat_data, public_data=public_data)
    res = BuildResult(html, rep.raw_bytes, rep.compressed_bytes, used)
    res.errors += rep.errors
    # Everything the runtime lacks is a build failure, not a hint.
    res.errors += [f"[runtime] {w}" for w in rep.warnings if "caption" not in w and "10%" not in w]
    lint = widget_lint.lint(html, caption=caption, compressed=rep.compressed_bytes)
    res.errors += lint.errors
    (res.errors if strict else res.warnings).extend(lint.warnings)
    return res


def build_file(path: str, **kw) -> BuildResult:  # noqa: D401
    with open(path, encoding="utf-8") as fh:
        return build_text(fh.read(), **kw)


def load_demo(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def state_text(value) -> str | None:
    if value is None:
        return None
    text = value if isinstance(value, str) else json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    if len(text.encode("utf-8")) > DATA_MAX_BYTES:
        raise BuildError(f"state is {len(text.encode('utf-8'))} UTF-8 bytes > {DATA_MAX_BYTES}")
    return text


def payload(html: str, *, chat_id, caption: str | None, chat_data=None, public_data=None, shared: bool = False,
            allow_queries: bool = False, widget_id: str | None = None, reply_markup: dict | None = None,
            width: int | None = None, height: int | None = None) -> dict:
    """A ready request. With widget_id: sendSharedWidget (code, size, public state and the
    request flag belong to the shared widget; only chat_data and the caption are per message)."""
    if widget_id:
        params = {"chat_id": chat_id, "widget_id": widget_id}
        method = "sendSharedWidget"
    else:
        params = {"chat_id": chat_id, "html": html}
        method = "sendWidget"
        if public_data is not None:
            params["public_data"] = state_text(public_data)
        if allow_queries:
            params["allow_queries"] = True
        if shared:
            params["is_shared"] = True
        if width:
            params["width"] = width
        if height:
            params["height"] = height
    if chat_data is not None:
        params["chat_data"] = state_text(chat_data)
    if caption:
        params["caption"] = caption
    if reply_markup:
        params["reply_markup"] = reply_markup
    return {"method": method, "params": params}


def demo_payload(html: str, demo: dict, *, chat_id=111111111, state: str = "default") -> dict:
    st = demo["states"][state]
    send = demo.get("send", {})
    return payload(html, chat_id=chat_id, caption=demo["caption"], chat_data=st.get("chatData"),
                   public_data=st.get("publicData"), shared=send.get("is_shared", False),
                   allow_queries=send.get("allow_queries", False), reply_markup=demo.get("fallback"),
                   width=send.get("width"), height=send.get("height"))


def gallery_sources() -> list[str]:
    return sorted(f for f in os.listdir(SRC_DIR) if f.endswith(".html"))


def source_languages(src: str) -> list[str]:
    """Languages a source has strings for (its own blocks and the kit's)."""
    text, _ = inline_kit(src)
    return sorted({m[0] for m in _LANG_BLOCK.findall(text)}) or ["en"]


def build_gallery(check: bool = False) -> int:
    """Build every gallery source with --strict. The English build is written next to the
    sources' parent (examples/widgets/NAME.html); every other language must pass too."""
    bad = 0
    for name in gallery_sources():
        demo_path = os.path.join(DEMO_DIR, name[:-5] + ".json")
        caption = load_demo(demo_path)["caption"] if os.path.exists(demo_path) else None
        with open(os.path.join(SRC_DIR, name), encoding="utf-8") as fh:
            src = fh.read()
        sizes, failed = [], []
        res = None
        for lang in source_languages(src):
            r = build_text(src, caption=caption, strict=True, langs=(lang,))
            sizes.append(f"{lang} {r.compressed_bytes}")
            failed += [f"{lang}: {e}" for e in r.errors]
            if lang == "en":
                res = r
        out = os.path.join(OUT_DIR, name)
        status = "OK"
        if failed or res is None:
            status, bad = "FAIL", bad + 1
            failed = failed or ["no English strings"]
        elif check:
            current = open(out, encoding="utf-8").read() if os.path.exists(out) else None
            if current != res.html + "\n":
                status, bad = "DRIFT", bad + 1
        else:
            with open(out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(res.html + "\n")
        print(f"{status:5} {name:26} zlib-9: {', '.join(sizes)}")
        for e in failed:
            print(f"      FAIL: {e}")
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("src", nargs="?")
    ap.add_argument("-o", "--out")
    ap.add_argument("--all", action="store_true", help="build every examples/widgets/src/*.html")
    ap.add_argument("--check", action="store_true", help="with --all: fail if a built file drifted")
    ap.add_argument("--strict", action="store_true", help="lint warnings fail the build")
    ap.add_argument("--no-minify", action="store_true")
    ap.add_argument("--lang", default="en", help="string blocks to keep, comma-separated (default en)")
    ap.add_argument("--caption")
    ap.add_argument("--demo", help="demo JSON: caption, states, send flags, fallback keyboard")
    ap.add_argument("--state", default="default")
    ap.add_argument("--payload", help="write a sendWidget/sendSharedWidget request here")
    ap.add_argument("--chat-id", default="111111111")
    ap.add_argument("--chat-data")
    ap.add_argument("--public-data")
    ap.add_argument("--shared", action="store_true")
    ap.add_argument("--allow-queries", action="store_true")
    ap.add_argument("--widget-id")
    a = ap.parse_args(argv)
    if a.all:
        return build_gallery(check=a.check)
    if not a.src:
        ap.error("give a source file or --all")
    demo = load_demo(a.demo) if a.demo else None
    caption = a.caption or (demo or {}).get("caption")
    res = build_file(a.src, caption=caption, strict=a.strict, minify=not a.no_minify,
                     langs=tuple(a.lang.split(",")))
    for w in res.warnings:
        print(f"WARN: {w}")
    for e in res.errors:
        print(f"FAIL: {e}")
    print(("INVALID: " if res.errors else "OK: ") + res.summary())
    if res.errors:
        return 1
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(res.html + "\n")
    if a.payload:
        chat_id = int(a.chat_id) if a.chat_id.lstrip("-").isdigit() else a.chat_id
        try:
            if demo:
                req = demo_payload(res.html, demo, chat_id=chat_id, state=a.state)
            else:
                req = payload(res.html, chat_id=chat_id, caption=caption, chat_data=a.chat_data,
                              public_data=a.public_data, shared=a.shared, allow_queries=a.allow_queries,
                              widget_id=a.widget_id)
        except BuildError as err:
            print(f"FAIL: {err}")
            return 1
        with open(a.payload, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(req, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print(f"payload: {req['method']} -> {a.payload}")
    if not a.out and not a.payload:
        print(res.html)
    return 0


if __name__ == "__main__":
    sys.exit(main())
