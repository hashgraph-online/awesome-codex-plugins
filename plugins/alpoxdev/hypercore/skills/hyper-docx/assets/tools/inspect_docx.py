"""Read a .docx and report what it actually stores.

Every value comes from the package bytes: paragraph text, styles, direct
formatting, tables, headers and footers, comments, tracked changes, images, and
the section geometry. Nothing is inferred from the file name or guessed from
the surrounding prose.
"""

import hashlib
import os
import posixpath
import re

from docxlib import (
    DocxError,
    NS,
    Package,
    local,
    paragraph_runs,
    paragraph_style,
    qn,
    read_text,
    revision_summary,
    twip_to_mm,
)

HEADING_RE = re.compile(r"^(Heading|heading|제목)\s*([1-9])$")
BULLET_CHARS = "•◦▪‣·-*"


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _mm(twip_value, fallback=None):
    if twip_value is None:
        return fallback
    try:
        return twip_to_mm(int(twip_value))
    except (TypeError, ValueError):
        return fallback


def section_geometry(pkg):
    body = pkg.body()
    sect = body.find(qn("w:sectPr"))
    if sect is None:
        return {"pages": []}
    pages = []
    size = sect.find(qn("w:pgSz"))
    mar = sect.find(qn("w:pgMar"))
    entry = {}
    if size is not None:
        entry["width_mm"] = _mm(size.get(qn("w:w")))
        entry["height_mm"] = _mm(size.get(qn("w:h")))
        entry["orient"] = size.get(qn("w:orient")) or "portrait"
    if mar is not None:
        for edge in ("top", "bottom", "left", "right", "header", "footer"):
            entry[edge + "_mm"] = _mm(mar.get(qn("w:" + edge)))
    pages.append(entry)
    return {"pages": pages}


def styles_index(pkg):
    for name in pkg.names():
        if posixpath.basename(name) != "styles.xml":
            continue
        if not name.startswith("word/"):
            continue
        root = pkg.root(name)
        table = {}
        for style in root.findall(qn("w:style")):
            style_id = style.get(qn("w:styleId"))
            if not style_id:
                continue
            entry = {"type": style.get(qn("w:type")) or "paragraph"}
            name_node = style.find(qn("w:name"))
            entry["name"] = name_node.get(qn("w:val")) if name_node is not None else style_id
            rpr = style.find(qn("w:rPr"))
            if rpr is not None:
                fonts = rpr.find(qn("w:rFonts"))
                if fonts is not None:
                    entry["eastAsia"] = fonts.get(qn("w:eastAsia"))
                size = rpr.find(qn("w:sz"))
                if size is not None:
                    try:
                        entry["size_pt"] = int(size.get(qn("w:val"))) / 2.0
                    except (TypeError, ValueError):
                        pass
                entry["bold"] = rpr.find(qn("w:b")) is not None
            ppr = style.find(qn("w:pPr"))
            if ppr is not None:
                spacing = ppr.find(qn("w:spacing"))
                if spacing is not None and spacing.get(qn("w:line")):
                    try:
                        entry["line_240ths"] = int(spacing.get(qn("w:line")))
                    except ValueError:
                        pass
            table[style_id] = entry
        return table
    return {}


def defaults(pkg):
    for name in pkg.names():
        if name.startswith("word/") and posixpath.basename(name) == "styles.xml":
            root = pkg.root(name)
            out = {}
            rpr = root.find("%s/%s/%s" % (qn("w:docDefaults"), qn("w:rPrDefault"), qn("w:rPr")))
            if rpr is not None:
                fonts = rpr.find(qn("w:rFonts"))
                if fonts is not None:
                    out["eastAsia"] = fonts.get(qn("w:eastAsia"))
                    out["ascii"] = fonts.get(qn("w:ascii"))
                size = rpr.find(qn("w:sz"))
                if size is not None:
                    out["size_pt"] = int(size.get(qn("w:val"))) / 2.0
            ppr = root.find("%s/%s/%s" % (qn("w:docDefaults"), qn("w:pPrDefault"), qn("w:pPr")))
            if ppr is not None:
                spacing = ppr.find(qn("w:spacing"))
                if spacing is not None and spacing.get(qn("w:line")):
                    out["line_240ths"] = int(spacing.get(qn("w:line")))
            return out
    return {}


def paragraph_record(paragraph, styles):
    text = read_text(paragraph)
    style_id = paragraph_style(paragraph)
    entry = {"text": text}
    if style_id:
        entry["style"] = style_id
        style = styles.get(style_id) or {}
        name = style.get("name") or ""
        match = HEADING_RE.match(name) or HEADING_RE.match(style_id)
        if match:
            entry["heading"] = int(match.group(2))
    ppr = paragraph.find(qn("w:pPr"))
    if ppr is not None:
        spacing = ppr.find(qn("w:spacing"))
        if spacing is not None and spacing.get(qn("w:line")):
            try:
                entry["line_240ths"] = int(spacing.get(qn("w:line")))
            except ValueError:
                pass
        ind = ppr.find(qn("w:ind"))
        if ind is not None:
            left = ind.get(qn("w:left")) or ind.get(qn("w:start"))
            if left is not None:
                entry["left_mm"] = _mm(left)
            hanging = ind.get(qn("w:hanging"))
            if hanging is not None:
                entry["hanging_mm"] = _mm(hanging)
        jc = ppr.find(qn("w:jc"))
        if jc is not None:
            entry["align"] = jc.get(qn("w:val"))
        numbering = ppr.find(qn("w:numPr"))
        if numbering is not None:
            entry["bullet"] = True
    if text[:1] in BULLET_CHARS and len(text) > 1:
        entry["bullet"] = True
    runs = []
    for kind, run in paragraph_runs(paragraph):
        rpr = run.find(qn("w:rPr"))
        flags = []
        if rpr is not None:
            if rpr.find(qn("w:b")) is not None:
                flags.append("bold")
            if rpr.find(qn("w:i")) is not None:
                flags.append("italic")
            if rpr.find(qn("w:u")) is not None:
                flags.append("underline")
            fonts = rpr.find(qn("w:rFonts"))
            if fonts is not None and fonts.get(qn("w:eastAsia")):
                flags.append("font:" + fonts.get(qn("w:eastAsia")))
            size = rpr.find(qn("w:sz"))
            if size is not None:
                flags.append("size:%spt" % (int(size.get(qn("w:val"))) / 2.0))
        if kind != "plain":
            flags.append(kind)
        if flags:
            runs.append({"text": read_text(run), "marks": flags})
    if runs:
        entry["runs"] = runs
    if paragraph.find(".//" + qn("w:drawing")) is not None:
        entry["image"] = True
    return entry


def table_record(table):
    rows = []
    for tr in table.findall(qn("w:tr")):
        cells = []
        for tc in tr.findall(qn("w:tc")):
            cell_text = "\n".join(read_text(p) for p in tc.findall(qn("w:p")))
            tcpr = tc.find(qn("w:tcPr"))
            cell = {"text": cell_text}
            if tcpr is not None:
                shd = tcpr.find(qn("w:shd"))
                if shd is not None and shd.get(qn("w:fill")):
                    cell["fill"] = shd.get(qn("w:fill"))
                width = tcpr.find(qn("w:tcW"))
                if width is not None and width.get(qn("w:w")):
                    cell["width_mm"] = _mm(width.get(qn("w:w")))
            cells.append(cell)
        rows.append(cells)
    return rows


def header_footer(pkg, part):
    root = pkg.root(part)
    return [read_text(p) for p in root.findall(qn("w:p"))]


def comments(pkg):
    document = pkg.document_part()
    result = []
    for _rid, rel_type, target, mode in pkg.relationships(document):
        if not rel_type.endswith("/comments") or mode != "Internal":
            continue
        part = pkg.resolve(document, target)
        if pkg.get(part) is None:
            continue
        root = pkg.root(part)
        for node in root.findall(qn("w:comment")):
            result.append({
                "id": node.get(qn("w:id")),
                "author": node.get(qn("w:author")),
                "date": node.get(qn("w:date")),
                "text": " ".join(read_text(p).strip() for p in node.findall(qn("w:p"))).strip(),
            })
    anchors = sum(
        1 for node in pkg.document().iter() if local(node.tag) == "commentRangeStart"
    )
    return {"items": result, "anchors": anchors}


def images(pkg):
    document = pkg.document_part()
    found = []
    for _rid, rel_type, target, mode in pkg.relationships(document):
        if not rel_type.endswith("/image") or mode != "Internal":
            continue
        part = pkg.resolve(document, target)
        data = pkg.get(part)
        if data is None:
            found.append({"part": part, "present": False})
            continue
        found.append({"part": part, "present": True, "bytes": len(data)})
    return found


def inspect(path):
    pkg = Package.open(path)
    document = pkg.document()
    body = pkg.body()
    style_table = styles_index(pkg)
    blocks = []
    for child in list(body):
        tag = local(child.tag)
        if tag == "p":
            record = paragraph_record(child, style_table)
            if record["text"].strip() or record.get("image"):
                blocks.append(record)
        elif tag == "tbl":
            blocks.append({"type": "table", "rows": table_record(child)})
    sect = body.find(qn("w:sectPr"))
    headers, footers = [], []
    if sect is not None:
        for ref in sect.findall(qn("w:footerReference")):
            rid = ref.get(qn("r:id"))
            for rel_id, rel_type, target, mode in pkg.relationships(pkg.document_part()):
                if rel_id == rid and mode == "Internal":
                    part = pkg.resolve(pkg.document_part(), target)
                    if pkg.get(part) is not None:
                        footers.append({"part": part, "text": header_footer(pkg, part)})
        for ref in sect.findall(qn("w:headerReference")):
            rid = ref.get(qn("r:id"))
            for rel_id, rel_type, target, mode in pkg.relationships(pkg.document_part()):
                if rel_id == rid and mode == "Internal":
                    part = pkg.resolve(pkg.document_part(), target)
                    if pkg.get(part) is not None:
                        headers.append({"part": part, "text": header_footer(pkg, part)})
    comment_data = comments(pkg)
    revisions = revision_summary(document)
    parts = pkg.names()
    return {
        "path": os.path.abspath(path),
        "bytes": os.path.getsize(path),
        "sha256": digest(path),
        "parts": len(parts),
        "document_part": pkg.document_part(),
        "defaults": defaults(pkg),
        "geometry": section_geometry(pkg),
        "blocks": blocks,
        "counts": {
            "paragraphs": sum(1 for b in blocks if "text" in b),
            "tables": sum(1 for b in blocks if b.get("type") == "table"),
            "headings": sum(1 for b in blocks if b.get("heading")),
            "images": len(images(pkg)),
            "comments": len(comment_data["items"]),
            "revisions": sum(item["count"] for item in revisions),
        },
        "comments": comment_data,
        "revisions": revisions,
        "revision_xml": {
            "trackChanges_setting": _track_setting(pkg),
        },
        "images": images(pkg),
        "headers": headers,
        "footers": footers,
        "styles": style_table,
        "macros": any(name.endswith("vbaProject.bin") for name in parts),
    }


def _track_setting(pkg):
    for name in pkg.names():
        if posixpath.basename(name) == "settings.xml" and name.startswith("word/"):
            root = pkg.root(name)
            node = root.find(qn("w:trackChanges"))
            return node is not None
    return False


def outline(path):
    data = inspect(path)
    lines = []
    for block in data["blocks"]:
        if block.get("type") == "table":
            lines.append("  [table %dx%d]" % (len(block["rows"]), len(block["rows"][0]) if block["rows"] else 0))
            continue
        text = block.get("text", "").strip()
        if not text:
            continue
        prefix = "#" * block.get("heading", 0) + " " if block.get("heading") else ""
        marks = " [%s]" % ",".join(sorted({m for run in block.get("runs", []) for m in run["marks"]})) if block.get("runs") else ""
        lines.append("%s%s%s" % (prefix, text, marks))
    return "\n".join(lines)


def text_of(path):
    data = inspect(path)
    out = []
    for block in data["blocks"]:
        if block.get("type") == "table":
            for row in block["rows"]:
                out.append("\t".join(cell["text"] for cell in row))
        elif block.get("text", "").strip():
            out.append(block["text"])
    return "\n".join(out)