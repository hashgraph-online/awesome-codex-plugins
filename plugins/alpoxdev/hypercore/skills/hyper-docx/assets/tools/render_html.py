"""Render a .docx to HTML for a visual check or a PDF pass.

The HTML keeps the page box, the paragraph indents, the table shading, and the
run marks, so a page-image check shows what Word would show. It is not a pixel
copy of Word's layout engine; it is a proof surface for the content and the
geometry the package stores.
"""

from docxlib import Package, local, paragraph_runs, paragraph_style, qn, read_text, twip_to_mm
from inspect_docx import inspect, styles_index

import base64


def _esc(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _run_html(run, kind):
    text = read_text(run)
    if not text:
        return ""
    rpr = run.find(qn("w:rPr"))
    style = []
    if rpr is not None:
        if rpr.find(qn("w:b")) is not None:
            style.append("font-weight:700")
        if rpr.find(qn("w:i")) is not None:
            style.append("font-style:italic")
        if rpr.find(qn("w:u")) is not None:
            style.append("text-decoration:underline")
        color = rpr.find(qn("w:color"))
        if color is not None and color.get(qn("w:val")):
            style.append("color:#%s" % color.get(qn("w:val")))
        size = rpr.find(qn("w:sz"))
        if size is not None and size.get(qn("w:val")):
            style.append("font-size:%.1fpt" % (int(size.get(qn("w:val"))) / 2.0))
    css = ' style="%s"' % ";".join(style) if style else ""
    body = _esc(text)
    if kind == "ins":
        body = '<ins class="ins">%s</ins>' % body
    elif kind == "del":
        body = '<del class="del">%s</del>' % body
    return "<span%s>%s</span>" % (css, body)


def _figure_html(drawing, pkg):
    """An inline picture as an <img> data URI at the extent the package stores.

    DrawingML expresses an extent in EMU (1 mm = 36000), not twips. Reading it as
    twips silently shrinks the picture by the 635/36 ratio, so a proof built on it
    shows a sliver instead of the figure.
    """
    extent = drawing.find(".//" + qn("wp:extent"))
    if extent is None:
        return ""
    cx = int(float(extent.get("cx", "0") or 0))
    cy = int(float(extent.get("cy", "0") or 0))
    width_mm = cx / 36000.0
    height_mm = cy / 36000.0
    body = ""
    blip = drawing.find(".//" + qn("a:blip"))
    rid = blip.get(qn("r:embed")) if blip is not None else None
    if rid and pkg is not None:
        part = pkg.document_part()
        for rel_id, rel_type, target, mode in pkg.relationships(part):
            if rel_id != rid or mode != "Internal":
                continue
            data = pkg.get(pkg.resolve(part, target))
            if not data:
                break
            kind = "png" if data[:8] == b"\x89PNG\r\n\x1a\n" else "jpeg"
            body = '<img alt="" src="data:image/%s;base64,%s">' % (
                kind, base64.b64encode(data).decode("ascii"))
            break
    if not body:
        body = "[그림]"
    return (
        '<span class="figure" style="display:inline-block;width:%.1fmm;height:%.1fmm;'
        'text-align:center;line-height:%.1fmm;color:#666">%s</span>'
        % (width_mm, height_mm, height_mm, body)
    )


def render(path, out_path, title=None):
    data = inspect(path)
    styles = data["styles"]
    geometry = data["geometry"]["pages"][0] if data["geometry"]["pages"] else {}
    width = geometry.get("width_mm") or 210
    height = geometry.get("height_mm") or 297
    margins = {
        "top": geometry.get("top_mm") or 15,
        "right": geometry.get("right_mm") or 20,
        "bottom": geometry.get("bottom_mm") or 15,
        "left": geometry.get("left_mm") or 20,
    }
    defaults = data["defaults"]
    font = defaults.get("eastAsia") or "휴먼명조"
    size_pt = defaults.get("size_pt") or 15
    line_240 = defaults.get("line_240ths") or 480

    pkg = Package.open(path)
    body = pkg.body()
    html_blocks = []
    for child in list(body):
        tag = local(child.tag)
        if tag == "p":
            html_blocks.append(_paragraph_html(child, styles, line_240, pkg))
        elif tag == "tbl":
            html_blocks.append(_table_html(child))
    footer_html = ""
    if data["footers"]:
        footer_html = " / ".join(t for t in data["footers"][0]["text"] if t.strip()) or ""
    header_html = ""
    if data["headers"]:
        header_html = " / ".join(t for t in data["headers"][0]["text"] if t.strip()) or ""

    page_css = (
        "@page { size: %(w)smm %(h)smm; margin: 0; }"
        "body { margin: 0; background: #fff; }"
        ".page { width: %(w)smm; min-height: %(h)smm; padding: %(t)smm %(r)smm %(b)smm %(l)smm;"
        " box-sizing: border-box; font-family: '%(font)s', 'Apple SD Gothic Neo', serif;"
        " font-size: %(size).1fpt; line-height: %(line).2f; color: #000; }"
        ".page p { margin: 0; text-align: justify; }"
        ".ins { color: #1f6feb; text-decoration: underline; }"
        ".del { color: #b3261e; text-decoration: line-through; }"
        "table { border-collapse: collapse; width: 100%%; margin: 4pt auto; }"
        "td, th { border: 0.6pt solid #000; padding: 2pt 4pt; text-align: center; font-size: 11pt; }"
        ".foot { position: relative; margin-top: 8pt; text-align: center; font-size: 9pt; color: #444; }"
        ".head { text-align: center; font-size: 9pt; color: #444; margin-bottom: 6pt; }"
        ".page + .page { page-break-before: always; }"
        ".figure img { width: 100%%; height: 100%%; }"
    ) % {
        "w": width, "h": height, "t": margins["top"], "r": margins["right"],
        "b": margins["bottom"], "l": margins["left"], "font": font,
        "size": size_pt, "line": line_240 / 240.0,
    }
    document = (
        "<!DOCTYPE html><html lang=\"ko\"><head><meta charset=\"utf-8\">"
        "<title>%s</title><style>%s</style></head><body><div class=\"page\">%s%s%s</div></body></html>"
        % (
            _esc(title or data["path"]),
            page_css,
            ('<div class="head">%s</div>' % _esc(header_html)) if header_html else "",
            "".join(html_blocks),
            ('<div class="foot">%s</div>' % _esc(footer_html)) if footer_html else "",
        )
    )
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(document)
    return {"out": out_path, "blocks": len(html_blocks), "font": font, "size_pt": size_pt}


ALIGN_CSS = {
    "center": "center", "centre": "center", "right": "right", "end": "right",
    "left": "left", "start": "left", "both": "justify", "distribute": "justify",
}


def _paragraph_html(paragraph, styles, default_line, pkg=None):
    style_id = paragraph_style(paragraph)
    style = styles.get(style_id) or {}
    css = []
    name = (style.get("name") or "").lower()
    if name.startswith("title") or style_id == "Title":
        css.append("font-size:22pt;font-weight:700;text-align:center;margin-bottom:12pt")
    elif name.startswith("heading 1") or style_id == "Heading1":
        css.append("font-size:17pt;font-weight:700;margin:14pt 0 6pt")
    elif name.startswith("heading 2") or style_id == "Heading2":
        css.append("font-size:16pt;font-weight:700;margin:10pt 0 4pt")
    elif name.startswith("heading 3") or style_id == "Heading3":
        css.append("font-size:15pt;font-weight:700;margin:8pt 0 3pt")
    ppr = paragraph.find(qn("w:pPr"))
    if ppr is not None:
        ind = ppr.find(qn("w:ind"))
        if ind is not None:
            left = ind.get(qn("w:left")) or ind.get(qn("w:start"))
            if left:
                css.append("margin-left:%.1fmm" % twip_to_mm(int(left)))
            hanging = ind.get(qn("w:hanging"))
            if hanging:
                css.append("text-indent:-%.1fmm" % twip_to_mm(int(hanging)))
            first = ind.get(qn("w:firstLine"))
            if first:
                css.append("text-indent:%.1fmm" % twip_to_mm(int(first)))
        jc = ppr.find(qn("w:jc"))
        if jc is not None:
            css.append("text-align:%s" % ALIGN_CSS.get(jc.get(qn("w:val")), "justify"))
        spacing = ppr.find(qn("w:spacing"))
        if spacing is not None:
            line = spacing.get(qn("w:line"))
            if line:
                css.append("line-height:%.2f" % (int(line) / 240.0))
            before = spacing.get(qn("w:before"))
            if before:
                css.append("margin-top:%.1fpt" % (int(before) / 20.0))
            after = spacing.get(qn("w:after"))
            if after:
                css.append("margin-bottom:%.1fpt" % (int(after) / 20.0))
    pieces = []
    for kind, run in paragraph_runs(paragraph):
        pieces.append(_run_html(run, kind))
    drawing = paragraph.find(".//" + qn("w:drawing"))
    if drawing is not None:
        pieces.append(_figure_html(drawing, pkg))
    if not pieces and not drawing:
        return ""
    return '<p style="%s">%s</p>' % (";".join(css), "".join(pieces))


def _table_html(table):
    rows = []
    for tr in table.findall(qn("w:tr")):
        cells = []
        for tc in tr.findall(qn("w:tc")):
            tcpr = tc.find(qn("w:tcPr"))
            style = []
            if tcpr is not None:
                shd = tcpr.find(qn("w:shd"))
                if shd is not None and shd.get(qn("w:fill")):
                    style.append("background:#%s" % shd.get(qn("w:fill")))
            content = "<br>".join(_esc(read_text(p)) for p in tc.findall(qn("w:p")))
            cells.append('<td style="%s">%s</td>' % (";".join(style), content))
        rows.append("<tr>%s</tr>" % "".join(cells))
    return "<table>%s</table>" % "".join(rows)