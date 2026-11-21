"""Structural and content checks on a .docx, plus a package digest.

Every check reads the file. A check that cannot run says so instead of passing:
`verify` reports `skipped` with the reason, never a silent green.
"""

import posixpath
import re

from docxlib import (
    CT_APP,
    CT_COMMENTS,
    CT_CORE,
    CT_DOCUMENT,
    CT_FOOTER,
    CT_HEADER,
    CT_NUMBERING,
    CT_SETTINGS,
    CT_STYLES,
    DocxError,
    Package,
    local,
    qn,
    read_text,
)
from xml.etree import ElementTree as ET

EXPECTED_TYPES = {
    CT_DOCUMENT: "document",
    CT_STYLES: "styles",
    CT_SETTINGS: "settings",
    CT_CORE: "core properties",
    CT_APP: "app properties",
}

PLACEHOLDER_WORDS = ("TODO", "TBD", "FIXME", "XXX", "lorem ipsum", "LOREM IPSUM")


def _result(code, status, detail):
    return {"check": code, "status": status, "detail": detail}


MAX_DPI = 2400


def _image_pixels(data):
    """Intrinsic pixel width of PNG or JPEG bytes, or 0 when unreadable."""
    if not data:
        return 0
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        return int.from_bytes(data[16:20], "big")
    if data[:2] == b"\xff\xd8":
        index = 2
        while index < len(data) - 9:
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB):
                return int.from_bytes(data[index + 7:index + 9], "big")
            length = int.from_bytes(data[index + 2:index + 4], "big")
            index += 2 + max(length, 2)
    return 0


def _page_width_emu(pkg):
    """The usable page width in EMU, from the body-level section properties."""
    sect = pkg.body().find(qn("w:sectPr"))
    if sect is None:
        return 0
    size = sect.find(qn("w:pgSz"))
    margins = sect.find(qn("w:pgMar"))
    if size is None or margins is None:
        return 0
    width = int(size.get(qn("w:w"), "0") or 0)
    left = int(margins.get(qn("w:left"), "0") or 0)
    right = int(margins.get(qn("w:right"), "0") or 0)
    return int((width - left - right) * 635)


def verify(path, spec=None):
    checks = []
    try:
        pkg = Package.open(path)
    except DocxError as exc:
        return {"path": path, "checks": [_result("package", "fail", str(exc))], "status": "fail"}

    # 1. every part is well-formed XML
    broken = []
    for name in pkg.names():
        if not name.endswith((".xml", ".rels")):
            continue
        try:
            pkg.root(name)
        except DocxError as exc:
            broken.append("%s: %s" % (name, exc))
    checks.append(_result("xml-wellformed", "fail" if broken else "pass", "; ".join(broken) or "%d XML parts parsed" % sum(1 for n in pkg.names() if n.endswith((".xml", ".rels")))))

    # 2. the document part exists and is reachable from the package relationships
    doc_part = pkg.document_part()
    reachable = pkg.get(doc_part) is not None
    checks.append(_result("document-part", "pass" if reachable else "fail",
                          "%s %s" % (doc_part, "present" if reachable else "missing")))

    # 3. content types cover every override that exists
    defaults, overrides = pkg.content_types()
    missing_types = []
    for part in overrides:
        name = part.lstrip("/")
        if pkg.get(name) is None:
            missing_types.append("override points at a missing part: %s" % name)
    missing_defaults = []
    for name in pkg.names():
        if name.endswith((".xml", ".rels")):
            continue
        ext = name.rsplit(".", 1)[-1].lower()
        if ext not in defaults and ("/" + name) not in overrides:
            missing_defaults.append(name)
    checks.append(_result("content-types", "fail" if (missing_types or missing_defaults) else "pass",
                          "; ".join(missing_types + missing_defaults) or "%d overrides, %d defaults" % (len(overrides), len(defaults))))

    # 4. every relationship target resolves
    dangling = []
    for name in pkg.names():
        if not name.endswith(".rels"):
            continue
        owner = _owner_of(name)
        for rid, rel_type, target, mode in pkg.relationships(owner):
            if mode != "Internal":
                continue
            resolved = pkg.resolve(owner, target)
            if pkg.get(resolved) is None:
                dangling.append("%s -> %s (%s)" % (owner or "/", resolved, rid))
    checks.append(_result("relationship-targets", "fail" if dangling else "pass",
                          "; ".join(dangling) or "every internal target exists"))

    # 5. styles referenced by paragraphs exist
    style_ids = set()
    for name in pkg.names():
        if name.startswith("word/") and name.endswith("styles.xml"):
            for style in pkg.root(name).findall(qn("w:style")):
                style_ids.add(style.get(qn("w:styleId")))
    unresolved_styles = set()
    for paragraph in pkg.document().iter(qn("w:p")):
        ppr = paragraph.find(qn("w:pPr"))
        if ppr is None:
            continue
        node = ppr.find(qn("w:pStyle"))
        if node is not None and node.get(qn("w:val")) not in style_ids:
            unresolved_styles.add(node.get(qn("w:val")))
    checks.append(_result("styles-resolve", "fail" if unresolved_styles else "pass",
                          ", ".join(sorted(unresolved_styles)) or "%d style(s) defined" % len(style_ids)))

    # 6. images exist with real bytes, every blip is declared, and every extent
    #    is a plausible EMU size (a twip value there shrinks the picture 17x)
    image_rels = {}
    for rid, rel_type, target, mode in pkg.relationships(doc_part):
        if rel_type.endswith("/image") and mode == "Internal":
            image_rels[rid] = pkg.resolve(doc_part, target)
    problems = []
    media = {}
    for part in image_rels.values():
        data = pkg.get(part)
        if not data:
            problems.append("missing part %s" % part)
        else:
            media[part] = data
    max_w_emu = _page_width_emu(pkg) or 0
    for drawing in pkg.document().iter(qn("w:drawing")):
        blip = drawing.find(".//" + qn("a:blip"))
        rid = blip.get(qn("r:embed")) if blip is not None else None
        if rid and rid not in image_rels:
            problems.append("undeclared r:embed %s" % rid)
        extent = drawing.find(".//" + qn("wp:extent"))
        if extent is None:
            problems.append("drawing without wp:extent")
            continue
        cx = int(float(extent.get("cx", "0") or 0))
        if cx <= 0:
            problems.append("drawing with zero width")
            continue
        width_mm = cx / 36000.0
        if max_w_emu and cx > max_w_emu:
            problems.append("drawing %.1f mm wider than the page" % width_mm)
            continue
        px_w = _image_pixels(media.get(image_rels.get(rid))) if rid else 0
        if px_w and width_mm > 0:
            dpi = px_w * 25.4 / width_mm
            if dpi > MAX_DPI:
                problems.append(
                    "drawing %.2f mm wide holds a %d px image (%.0f dpi); "
                    "wp:extent is EMU, not twips" % (width_mm, px_w, dpi))
    checks.append(_result("images", "fail" if problems else "pass",
                          "; ".join(problems) or "%d image part(s) present, extents plausible"
                          % len(image_rels)))

    # 7. comments are anchored: each comment id has a range in the document
    anchored = _comment_anchor_check(pkg)
    checks.append(_result("comment-anchors", anchored[0], anchored[1]))

    # 8. no unanswered placeholder left in the body
    body_text = read_text(pkg.body())
    found = [word for word in PLACEHOLDER_WORDS if word in body_text]
    checks.append(_result("placeholders", "fail" if found else "pass",
                          ", ".join(found) or "no placeholder markers"))

    # 9. page geometry matches the spec when a spec was given
    if spec:
        checks.append(_geometry_check(pkg, spec))
    else:
        checks.append(_result("geometry", "skipped", "no spec supplied; geometry unverified"))

    # 10. a spec-declared word count, if the spec sets one
    if spec and spec.get("min_chars"):
        length = len(re.sub(r"\s+", "", body_text))
        checks.append(_result(
            "length",
            "pass" if length >= int(spec["min_chars"]) else "fail",
            "%d characters without whitespace, floor %s" % (length, spec["min_chars"]),
        ))

    status = "pass" if all(c["status"] in ("pass", "skipped") for c in checks) else "fail"
    return {
        "path": path,
        "sha256": _digest(path),
        "parts": len(pkg.names()),
        "checks": checks,
        "status": status,
    }


def _owner_of(rels_name):
    if rels_name == "_rels/.rels":
        return ""
    directory = posixpath.dirname(posixpath.dirname(rels_name))
    base = posixpath.basename(rels_name)[: -len(".rels")]
    return posixpath.join(directory, base) if directory else base


def _comment_anchor_check(pkg):
    document = pkg.document_part()
    starts = set()
    for node in pkg.document().iter(qn("w:commentRangeStart")):
        starts.add(node.get(qn("w:id")))
    ends = set()
    for node in pkg.document().iter(qn("w:commentRangeEnd")):
        ends.add(node.get(qn("w:id")))
    ids = set()
    for _rid, rel_type, target, mode in pkg.relationships(document):
        if not rel_type.endswith("/comments") or mode != "Internal":
            continue
        part = pkg.resolve(document, target)
        if pkg.get(part) is None:
            return ("fail", "comments relationship points at a missing part")
        for node in pkg.root(part).findall(qn("w:comment")):
            ids.add(node.get(qn("w:id")))
    unanchored = sorted(ids - starts)
    orphan_ranges = sorted((starts | ends) - ids)
    if unanchored:
        return ("fail", "comment(s) with no range: %s" % ", ".join(unanchored))
    if orphan_ranges:
        return ("fail", "range(s) with no comment: %s" % ", ".join(orphan_ranges))
    return ("pass", "%d comment(s), all anchored" % len(ids))


def _geometry_check(pkg, spec):
    from build_docx import PAGE_PRESETS
    from docxlib import mm_to_twip

    preset = spec.get("page") or "official-kr"
    if isinstance(preset, dict):
        expected_margin = dict(PAGE_PRESETS["official-kr"]["margin_mm"])
        expected_margin.update(preset.get("margin_mm") or {})
        expected_size = tuple(preset.get("size") or PAGE_PRESETS["official-kr"]["size"])
    else:
        table = PAGE_PRESETS.get(preset)
        if table is None:
            return _result("geometry", "fail", "unknown page preset %r" % preset)
        expected_margin = table["margin_mm"]
        expected_size = table["size"]
    if spec.get("margin_mm"):
        expected_margin = dict(expected_margin)
        expected_margin.update(spec["margin_mm"])
    sect = pkg.body().find(qn("w:sectPr"))
    if sect is None:
        return _result("geometry", "fail", "no section properties in the body")
    size = sect.find(qn("w:pgSz"))
    mar = sect.find(qn("w:pgMar"))
    problems = []
    if size is None:
        problems.append("no page size")
    else:
        width = int(size.get(qn("w:w")))
        height = int(size.get(qn("w:h")))
        if (width, height) != tuple(expected_size):
            problems.append("page size %dx%d twip, expected %dx%d" % (width, height, expected_size[0], expected_size[1]))
    if mar is None:
        problems.append("no page margins")
    else:
        for edge in ("top", "bottom", "left", "right"):
            if edge not in expected_margin:
                continue
            actual = int(mar.get(qn("w:" + edge)))
            want = mm_to_twip(expected_margin[edge])
            if abs(actual - want) > 2:
                problems.append("%s margin %s twip, expected %s (%s mm)" % (edge, actual, want, expected_margin[edge]))
    return _result("geometry", "fail" if problems else "pass",
                   "; ".join(problems) or "page %s, margins match the spec" % (preset,))


def _digest(path):
    import hashlib

    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()