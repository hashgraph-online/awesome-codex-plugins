"""Build a .docx package from a declarative spec.

Standard library only. The package is written part by part, so a build never
depends on a template file, and the same spec always produces the same bytes.
"""

import json
import os

from docxlib import (
    A4_TWIP,
    CT_APP,
    CT_CORE,
    CT_DOCUMENT,
    CT_FONT_TABLE,
    CT_FOOTER,
    CT_HEADER,
    CT_NUMBERING,
    CT_SETTINGS,
    CT_STYLES,
    NS,
    Package,
    REL_APP,
    REL_CORE,
    REL_FONT_TABLE,
    REL_FOOTER,
    REL_IMAGE,
    REL_HEADER,
    REL_NUMBERING,
    REL_OFFICE_DOCUMENT,
    REL_SETTINGS,
    REL_STYLES,
    XML_DECL,
    mm_to_twip,
    pct_to_twip_line,
    pt_to_half_points,
    qn,
)

W = NS["w"]

# Page presets in twips and millimetre margins. official-kr follows the layout
# convention Korean public documents are written in (A4, 15 pt body, 200 % line
# spacing, 15 mm top and bottom, 20 mm left and right); it is this package's
# default, not a quotation of the regulation.
PAGE_PRESETS = {
    "a4": {"size": A4_TWIP, "margin_mm": {"top": 20, "bottom": 20, "left": 20, "right": 20}},
    "official-kr": {
        "size": A4_TWIP,
        "margin_mm": {"top": 15, "bottom": 15, "left": 20, "right": 20, "header": 10, "footer": 10},
    },
    "letter": {"size": (12240, 15840), "margin_mm": {"top": 25.4, "bottom": 25.4, "left": 25.4, "right": 25.4}},
}

DEFAULT_FONT = {"ascii": "휴먼명조", "eastAsia": "휴먼명조", "hAnsi": "휴먼명조"}
DEFAULT_SIZE_PT = 15.0
DEFAULT_LINE_PCT = 200

ROMAN = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"


def _el(tag, attrib=None, parent=None):
    node = _new(tag)
    for key, value in (attrib or {}).items():
        node.set(qn(key) if ":" in key else key, str(value))
    if parent is not None:
        parent.append(node)
    return node


def _new(tag):
    from xml.etree import ElementTree as ET

    return ET.Element(qn(tag))


def _sub(parent, tag, attrib=None):
    return _el(tag, attrib, parent)


def _text(parent, tag, value):
    node = _sub(parent, tag)
    node.text = value
    return node


class SpecError(Exception):
    """A spec the builder cannot honor; the message names the offending block."""


def _fonts(spec_font):
    font = dict(DEFAULT_FONT)
    if isinstance(spec_font, str) and spec_font.strip():
        font = {"ascii": spec_font, "eastAsia": spec_font, "hAnsi": spec_font}
    elif isinstance(spec_font, dict):
        font.update({k: v for k, v in spec_font.items() if v})
    return font


def _run_props(rpr_parent, *, font=None, size=None, bold=False, italic=False,
               underline=False, color=None, char_spacing=None):
    rpr = _sub(rpr_parent, "w:rPr")
    if font:
        _sub(rpr, "w:rFonts", {
            "w:ascii": font["ascii"],
            "w:hAnsi": font["hAnsi"],
            "w:eastAsia": font["eastAsia"],
            "w:hint": "eastAsia",
        })
    if bold:
        _sub(rpr, "w:b")
        _sub(rpr, "w:bCs")
    if italic:
        _sub(rpr, "w:i")
        _sub(rpr, "w:iCs")
    if color:
        _sub(rpr, "w:color", {"w:val": color.lstrip("#")})
    if size:
        half = pt_to_half_points(size)
        _sub(rpr, "w:sz", {"w:val": half})
        _sub(rpr, "w:szCs", {"w:val": half})
    if char_spacing:
        _sub(rpr, "w:spacing", {"w:val": int(round(float(char_spacing) * 20))})
    if underline:
        _sub(rpr, "w:u", {"w:val": "single"})
    return rpr


def make_run(text, *, font=None, size=None, bold=False, italic=False, underline=False,
             color=None, break_before=False, tab=False):
    run = _new("w:r")
    _run_props(run, font=font, size=size, bold=bold, italic=italic, underline=underline, color=color)
    if tab:
        _sub(run, "w:tab")
    if break_before:
        _sub(run, "w:br")
    if text:
        for index, line in enumerate(str(text).split("\n")):
            if index:
                _sub(run, "w:br")
            if line:
                node = _sub(run, "w:t")
                node.text = line
                node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return run


ALIGN = {
    "left": "left", "start": "start", "center": "center", "centre": "center",
    "right": "right", "end": "end", "justify": "both", "both": "both",
    "distribute": "distribute",
}


def make_paragraph(children, *, style=None, align=None, left_mm=None, right_mm=None,
                   first_mm=None, hanging_mm=None, line_pct=None, before_pt=None,
                   after_pt=None, keep_next=False, outline_level=None,
                   page_break_before=False, contextual_spacing=False):
    paragraph = _new("w:p")
    ppr = _sub(paragraph, "w:pPr")
    if style:
        _sub(ppr, "w:pStyle", {"w:val": style})
    if keep_next:
        _sub(ppr, "w:keepNext")
    if page_break_before:
        _sub(ppr, "w:pageBreakBefore")
    if contextual_spacing:
        _sub(ppr, "w:contextualSpacing")
    if outline_level is not None:
        _sub(ppr, "w:outlineLvl", {"w:val": outline_level})
    spacing = {}
    if before_pt is not None:
        spacing["w:before"] = int(round(float(before_pt) * 20))
    if after_pt is not None:
        spacing["w:after"] = int(round(float(after_pt) * 20))
    if line_pct is not None:
        spacing["w:line"] = pct_to_twip_line(line_pct)
        spacing["w:lineRule"] = "auto"
    if spacing:
        _sub(ppr, "w:spacing", spacing)
    ind = {}
    if left_mm is not None:
        ind["w:start"] = mm_to_twip(left_mm)
        ind["w:left"] = mm_to_twip(left_mm)
    if right_mm is not None:
        ind["w:end"] = mm_to_twip(right_mm)
        ind["w:right"] = mm_to_twip(right_mm)
    if first_mm is not None:
        ind["w:firstLine"] = mm_to_twip(first_mm)
    if hanging_mm is not None:
        ind["w:hanging"] = mm_to_twip(hanging_mm)
    if ind:
        _sub(ppr, "w:ind", ind)
    if align:
        _sub(ppr, "w:jc", {"w:val": ALIGN.get(align, align)})
    for child in children:
        paragraph.append(child)
    return paragraph


def _borders(parent, color="000000", size=4, edges=("top", "left", "bottom", "right")):
    borders = _sub(parent, "w:tblBorders")
    for edge in edges:
        _sub(borders, "w:" + edge, {
            "w:val": "single", "w:sz": size, "w:space": 0, "w:color": color,
        })


def make_table(rows, *, widths_mm=None, header=True, header_fill="E7E6E6",
               font_size=None, font=None, align="center", first_col_bold=False,
               text_width_mm=None):
    if not rows or not rows[0]:
        raise SpecError("table needs at least one row with one cell")
    columns = max(len(row) for row in rows)
    if widths_mm:
        grid_widths = [mm_to_twip(value) for value in widths_mm[:columns]]
        while len(grid_widths) < columns:
            grid_widths.append(grid_widths[-1] if grid_widths else mm_to_twip(40))
    else:
        span = text_width_mm or 170
        grid_widths = [mm_to_twip(span / float(columns))] * columns
    table = _new("w:tbl")
    tblpr = _sub(table, "w:tblPr")
    _sub(tblpr, "w:tblStyle", {"w:val": "TableGrid"})
    # A literal width in twips renders identically in Word, Pages, and previewers;
    # a percentage width does not.
    _sub(tblpr, "w:tblW", {"w:w": sum(grid_widths), "w:type": "dxa"})
    _sub(tblpr, "w:jc", {"w:val": "center"})
    _sub(tblpr, "w:tblInd", {"w:w": 0, "w:type": "dxa"})
    _borders(tblpr)
    _sub(tblpr, "w:tblLayout", {"w:type": "fixed"})
    grid = _sub(table, "w:tblGrid")
    for width in grid_widths:
        _sub(grid, "w:gridCol", {"w:w": width})
    for index, row in enumerate(rows):
        tr = _sub(table, "w:tr")
        if index == 0 and header:
            _sub(_sub(tr, "w:trPr"), "w:tblHeader")
        for col in range(columns):
            cell = _sub(tr, "w:tc")
            tcpr = _sub(cell, "w:tcPr")
            _sub(tcpr, "w:tcW", {"w:w": grid_widths[col], "w:type": "dxa"})
            if index == 0 and header and header_fill:
                _sub(tcpr, "w:shd", {"w:val": "clear", "w:color": "auto", "w:fill": header_fill})
            _sub(tcpr, "w:vAlign", {"w:val": "center"})
            value = row[col] if col < len(row) else ""
            bold = (index == 0 and header) or (first_col_bold and col == 0)
            cell_paragraph = make_paragraph(
                [make_run(value, font=font, size=font_size, bold=bold)],
                align=align,
                line_pct=140,
                before_pt=2,
                after_pt=2,
            )
            cell.append(cell_paragraph)
    return table


def make_figure(path, *, width_mm, caption=None, shape_id=1, rel_id=None, font=None,
                size=11):
    """An inline picture block returned as (paragraphs, needs).

    `needs` tells the caller which media part and relationship to install.
    """
    if not os.path.isfile(path):
        raise SpecError("figure file not found: %s" % path)
    with open(path, "rb") as handle:
        head = handle.read(8)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        ext = "png"
    elif head[:2] == b"\xff\xd8":
        ext = "jpg"
    else:
        raise SpecError("figure must be PNG or JPEG: %s" % path)
    width = mm_to_twip(width_mm)
    height = _image_height(path, width)
    emu_w = mm_to_emu(width_mm)
    emu_h = int(round(emu_w * float(height) / float(width))) if width else emu_w
    name = os.path.basename(path)
    drawing = (
        '<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
        '<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
        '<wp:docPr id="{sid}" name="Picture {sid}"/>'
        '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic><pic:nvPicPr><pic:cNvPr id="{sid}" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr>'
        '<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
        "</a:graphicData></a:graphic></wp:inline></w:drawing></w:r>"
    ).format(cx=emu_w, cy=emu_h, sid=shape_id, name=name, rid=rel_id)
    from xml.etree import ElementTree as ET

    register_prefixes()
    wrapper = ET.fromstring('<w:p xmlns:w="%s" xmlns:r="%s" xmlns:wp="%s" xmlns:a="%s" xmlns:pic="%s">'
                            "<w:pPr><w:jc w:val=\"center\"/></w:pPr>%s</w:p>"
                            % (NS["w"], NS["r"], NS["wp"], NS["a"], NS["pic"], drawing))
    blocks = [wrapper]
    if caption:
        blocks.append(make_paragraph([make_run(caption, font=font, size=size, color="595959")],
                                     align="center", before_pt=3, after_pt=6, line_pct=150))
    return blocks, {"media": (name, ext, path), "rel_id": rel_id}


def register_prefixes():
    from xml.etree import ElementTree as ET

    for prefix, uri in NS.items():
        ET.register_namespace(prefix, uri)


def mm_to_emu(mm):
    """DrawingML extent unit: 1 mm = 36000 EMU."""
    return int(round(float(mm) * 36000.0))


def _image_height(path, width_twip):
    """PNG/JPEG pixel dimensions read from the header, scaled to the given width."""
    with open(path, "rb") as handle:
        data = handle.read()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        px_w = int.from_bytes(data[16:20], "big")
        px_h = int.from_bytes(data[20:24], "big")
    else:
        px_w, px_h = _jpeg_size(data)
    if not px_w or not px_h:
        return width_twip
    return int(round(width_twip * float(px_h) / float(px_w)))


def _jpeg_size(data):
    index = 2
    while index < len(data) - 9:
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB):
            height = int.from_bytes(data[index + 5:index + 7], "big")
            width = int.from_bytes(data[index + 7:index + 9], "big")
            return width, height
        length = int.from_bytes(data[index + 2:index + 4], "big")
        index += 2 + max(length, 2)
    return 0, 0


def styles_xml(font, size_pt, line_pct):
    register_prefixes()
    from xml.etree import ElementTree as ET

    root = ET.fromstring(
        '<w:styles xmlns:w="%s"><w:docDefaults><w:rPrDefault><w:rPr>'
        '<w:rFonts w:ascii="%s" w:hAnsi="%s" w:eastAsia="%s" w:cs="%s" w:hint="eastAsia"/>'
        '<w:sz w:val="%d"/><w:szCs w:val="%d"/><w:lang w:val="en-US" w:eastAsia="ko-KR"/>'
        "</w:rPr></w:rPrDefault><w:pPrDefault><w:pPr>"
        '<w:spacing w:line="%d" w:lineRule="auto"/><w:jc w:val="both"/>'
        "</w:pPr></w:pPrDefault></w:docDefaults></w:styles>"
        % (W, font["ascii"], font["hAnsi"], font["eastAsia"], font["eastAsia"],
           pt_to_half_points(size_pt), pt_to_half_points(size_pt), pct_to_twip_line(line_pct))
    )

    def style(style_id, name, *, para=True, based="Normal", size=None, bold=False,
              align=None, before=0, after=0, outline=None, next_id=None):
        node = _sub(root, "w:style", {"w:type": "paragraph" if para else "character", "w:styleId": style_id})
        _sub(node, "w:name", {"w:val": name})
        if based:
            _sub(node, "w:basedOn", {"w:val": based})
        if next_id:
            _sub(node, "w:next", {"w:val": next_id})
        _sub(node, "w:qFormat")
        ppr = _sub(node, "w:pPr")
        if outline is not None:
            _sub(ppr, "w:keepNext")
            _sub(ppr, "w:keepLines")
            _sub(ppr, "w:spacing", {"w:before": int(before * 20), "w:after": int(after * 20),
                                    "w:line": pct_to_twip_line(line_pct), "w:lineRule": "auto"})
            _sub(ppr, "w:outlineLvl", {"w:val": outline})
        else:
            _sub(ppr, "w:spacing", {"w:before": int(before * 20), "w:after": int(after * 20)})
        if align:
            _sub(ppr, "w:jc", {"w:val": align})
        rpr = _sub(node, "w:rPr")
        if bold:
            _sub(rpr, "w:b")
            _sub(rpr, "w:bCs")
        if size:
            half = pt_to_half_points(size)
            _sub(rpr, "w:sz", {"w:val": half})
            _sub(rpr, "w:szCs", {"w:val": half})
        return node

    normal = style("Normal", "Normal", based=None, align="both")
    _sub(_sub(normal, "w:pPr"), "w:jc", {"w:val": "both"})
    style("Title", "Title", size=22, bold=True, align="center", before=0, after=12, outline=0, next_id="BodyText")
    style("Heading1", "heading 1", size=17, bold=True, align="left", before=14, after=6, outline=0, next_id="BodyText")
    style("Heading2", "heading 2", size=16, bold=True, align="left", before=10, after=4, outline=1, next_id="BodyText")
    style("Heading3", "heading 3", size=15, bold=True, align="left", before=8, after=3, outline=2, next_id="BodyText")
    style("BodyText", "Body Text", based="Normal")
    style("TableGrid", "Table Grid", based="Normal", align="center")
    style("Caption", "caption", based="Normal", size=10, align="center", before=2, after=6)
    style("Quote", "Quote", based="Normal")
    return XML_DECL + ET.tostring(root, encoding="unicode")


def numbering_xml(items):
    """Decimal multilevel numbering used by `list` blocks."""
    register_prefixes()
    from xml.etree import ElementTree as ET

    root = ET.fromstring('<w:numbering xmlns:w="%s"/>' % W)
    abstract = _sub(root, "w:abstractNum", {"w:abstractNumId": "0"})
    _sub(abstract, "w:multiLevelType", {"w:val": "multilevel"})
    for level in range(3):
        lvl = _sub(abstract, "w:lvl", {"w:ilvl": level})
        _sub(lvl, "w:start", {"w:val": 1})
        _sub(lvl, "w:numFmt", {"w:val": "decimal"})
        _sub(lvl, "w:lvlText", {"w:val": "%%%d." % (level + 1)})
        _sub(lvl, "w:lvlJc", {"w:val": "left"})
        _sub(lvl, "w:pPr", {"w:ind": ""})
        ppr = lvl.find(qn("w:pPr"))
        ppr.attrib.clear()
        _sub(ppr, "w:ind", {"w:left": mm_to_twip(10 + level * 5), "w:hanging": mm_to_twip(5)})
    num = _sub(root, "w:num", {"w:numId": "1"})
    _sub(num, "w:abstractNumId", {"w:val": "0"})
    return XML_DECL + ET.tostring(root, encoding="unicode")


def footer_xml(font, size_pt):
    register_prefixes()
    from xml.etree import ElementTree as ET

    root = ET.fromstring('<w:ftr xmlns:w="%s"/>' % W)
    paragraph = make_paragraph([], align="center", line_pct=100)
    paragraph.append(make_run("－ ", font=font, size=size_pt))
    _field(paragraph, " PAGE ")
    paragraph.append(make_run(" / ", font=font, size=size_pt))
    _field(paragraph, " NUMPAGES ")
    root.append(paragraph)
    return XML_DECL + ET.tostring(root, encoding="unicode")


def _field(paragraph, instruction):
    """Append one complete field: begin, instruction, separate, placeholder, end."""
    for fld_type in ("begin", "separate", "end"):
        run = _sub(paragraph, "w:r")
        _sub(run, "w:fldChar", {"w:fldCharType": fld_type})
        if fld_type == "begin":
            code_run = _sub(paragraph, "w:r")
            _sub(code_run, "w:instrText").text = instruction
        elif fld_type == "separate":
            result = _sub(paragraph, "w:r")
            _sub(result, "w:t").text = "1"


def document_xml(blocks, page):
    """Assemble word/document.xml from block elements."""
    register_prefixes()
    from xml.etree import ElementTree as ET

    root = ET.fromstring(
        '<w:document xmlns:w="%s" xmlns:r="%s" xmlns:wp="%s" xmlns:a="%s" xmlns:pic="%s"/>'
        % (W, NS["r"], NS["wp"], NS["a"], NS["pic"])
    )
    body = _sub(root, "w:body")
    for block in blocks:
        body.append(block)
    sect = _sub(body, "w:sectPr")
    width, height = page["size"]
    _sub(sect, "w:pgSz", {"w:w": width, "w:h": height, "w:orient": "portrait" if height >= width else "landscape"})
    margin = page["margin_mm"]
    _sub(sect, "w:pgMar", {
        "w:top": mm_to_twip(margin["top"]),
        "w:right": mm_to_twip(margin["right"]),
        "w:bottom": mm_to_twip(margin["bottom"]),
        "w:left": mm_to_twip(margin["left"]),
        "w:header": mm_to_twip(margin.get("header", 10)),
        "w:footer": mm_to_twip(margin.get("footer", 10)),
        "w:gutter": 0,
    })
    _sub(sect, "w:cols", {"w:space": 720})
    _sub(sect, "w:docGrid", {"w:linePitch": 360})
    return XML_DECL + ET.tostring(root, encoding="unicode")


def core_xml(spec):
    from xml.etree import ElementTree as ET

    ET.register_namespace("cp", NS["cp"])
    ET.register_namespace("dc", NS["dc"])
    ET.register_namespace("dcterms", NS["dcterms"])
    ET.register_namespace("xsi", NS["xsi"])
    root = ET.Element(qn("cp:coreProperties"))
    _text_el(root, "dc:title", spec.get("title") or "")
    _text_el(root, "dc:creator", spec.get("author") or "")
    _text_el(root, "cp:lastModifiedBy", spec.get("author") or "")
    _text_el(root, "dc:subject", spec.get("subject") or "")
    _text_el(root, "dc:language", "ko-KR")
    return XML_DECL + ET.tostring(root, encoding="unicode")


def _text_el(parent, tag, value):
    node = _sub(parent, tag)
    node.text = value
    return node


def block_elements(spec, font, size_pt, line_pct, figure_state):
    """Translate spec blocks into document body elements."""
    blocks = []
    for index, block in enumerate(spec.get("blocks") or []):
        kind = (block.get("type") or "paragraph").lower()
        if kind in ("paragraph", "p", "text"):
            blocks.append(make_paragraph(
                [make_run(block.get("text", ""), font=block.get("font") or font,
                          size=block.get("size") or size_pt,
                          bold=block.get("bold", False), italic=block.get("italic", False),
                          underline=block.get("underline", False), color=block.get("color"))],
                style=block.get("style"),
                align=block.get("align"),
                left_mm=block.get("left_mm"),
                first_mm=block.get("first_mm"),
                hanging_mm=block.get("hanging_mm"),
                line_pct=block.get("line_pct", line_pct),
                before_pt=block.get("before_pt"),
                after_pt=block.get("after_pt", 0 if block.get("tight") else None),
                keep_next=block.get("keep_next", False),
                page_break_before=block.get("page_break_before", False),
            ))
        elif kind in ("title",):
            blocks.append(make_paragraph(
                [make_run(block.get("text", ""), font=font, size=block.get("size") or 22, bold=True)],
                style="Title", align=block.get("align", "center"), after_pt=block.get("after_pt", 12),
                line_pct=line_pct,
            ))
        elif kind in ("heading", "h"):
            level = int(block.get("level") or 1)
            style = {1: "Heading1", 2: "Heading2", 3: "Heading3"}.get(level, "Heading3")
            size = {1: 17, 2: 16, 3: 15}.get(level, 15)
            blocks.append(make_paragraph(
                [make_run(block.get("text", ""), font=font, size=block.get("size") or size, bold=True)],
                style=style, line_pct=line_pct,
            ))
        elif kind in ("list", "bullets", "numbered"):
            numbered = kind == "numbered" or block.get("numbered", False)
            for item_index, item in enumerate(block.get("items") or []):
                text = item if isinstance(item, str) else item.get("text", "")
                depth = int(item.get("depth", 0)) if isinstance(item, dict) else 0
                if numbered:
                    marker = "%d." % (item_index + 1)
                    run_children = [make_run(marker + "\t", font=font, size=size_pt),
                                    make_run(text, font=font, size=size_pt)]
                else:
                    run_children = [make_run(("•" if depth == 0 else "◦") + " ", font=font, size=size_pt),
                                    make_run(text, font=font, size=size_pt)]
                blocks.append(make_paragraph(
                    run_children, line_pct=line_pct, left_mm=8 + depth * 5, hanging_mm=5,
                    after_pt=0,
                ))
        elif kind in ("item", "clause"):
            # Korean item hierarchy: 1.  가.  1)  가)  (1)  (가)  ①
            mark = block.get("mark") or "가."
            text = block.get("text", "")
            blocks.append(make_paragraph(
                [make_run(mark + " ", font=font, size=size_pt), make_run(text, font=font, size=size_pt)],
                line_pct=line_pct, left_mm=block.get("left_mm", 0), hanging_mm=block.get("hanging_mm"),
                after_pt=block.get("after_pt", 0),
            ))
        elif kind in ("item_line", "row"):
            # A single line with a dot leader, as in 붙임 lists: label ....... value
            text = block.get("text", "")
            value = block.get("value", "")
            children = [make_run(text, font=font, size=size_pt)]
            children.append(_positional_tab("right", "dot"))
            children.append(make_run(value, font=font, size=size_pt))
            blocks.append(make_paragraph(children, line_pct=line_pct, after_pt=0))
        elif kind == "table":
            blocks.append(make_table(
                block.get("rows") or [],
                text_width_mm=figure_state.get("text_width_mm"),
                widths_mm=block.get("widths_mm"),
                header=block.get("header", True),
                header_fill=block.get("header_fill", "E7E6E6"),
                font_size=block.get("font_size") or 11,
                font=font,
                align=block.get("align", "center"),
                first_col_bold=block.get("first_col_bold", False),
            ))
        elif kind in ("figure", "image"):
            figure_state["counter"] += 1
            rel_id = "rId%d" % (100 + figure_state["counter"])
            elements, needs = make_figure(
                block.get("path", ""),
                width_mm=block.get("width_mm", 120),
                caption=block.get("caption"),
                shape_id=figure_state["counter"],
                rel_id=rel_id,
                font=font,
                size=block.get("caption_size", 10),
            )
            blocks.extend(elements)
            needs["media"] = needs["media"] + (rel_id,)
            figure_state["figures"].append(needs["media"])
        elif kind == "page_break":
            blocks.append(make_paragraph([make_run("", font=font)], page_break_before=True))
        elif kind == "spacer":
            blocks.append(make_paragraph([], line_pct=block.get("line_pct", 100),
                                          after_pt=block.get("after_pt", 0)))
        else:
            raise SpecError("block %d has unknown type %r" % (index + 1, kind))
    return blocks


def _positional_tab(alignment, leader):
    from xml.etree import ElementTree as ET

    run = ET.fromstring(
        '<w:r xmlns:w="%s"><w:rPr><w:noProof/></w:rPr><w:ptab w:alignment="%s" w:relativeTo="margin" w:leader="%s"/></w:r>'
        % (W, alignment, leader)
    )
    return run


def build(spec, out_path):
    """Build a package from a spec dict and write it to out_path."""
    page = dict(PAGE_PRESETS[spec.get("page") or "official-kr"])
    if isinstance(spec.get("page"), dict):
        page = {"size": tuple(spec["page"].get("size") or A4_TWIP),
                "margin_mm": dict(PAGE_PRESETS["official-kr"]["margin_mm"])}
        page["margin_mm"].update(spec["page"].get("margin_mm") or {})
    elif spec.get("margin_mm"):
        page["margin_mm"] = dict(page["margin_mm"])
        page["margin_mm"].update(spec["margin_mm"])

    font = _fonts(spec.get("font"))
    size_pt = float(spec.get("size_pt") or DEFAULT_SIZE_PT)
    line_pct = float(spec.get("line_pct") or DEFAULT_LINE_PCT)

    text_width_mm = (
        page["size"][0] - mm_to_twip(page["margin_mm"]["left"]) - mm_to_twip(page["margin_mm"]["right"])
    ) * 25.4 / 1440.0
    figure_state = {"counter": 0, "figures": [], "text_width_mm": round(text_width_mm, 2)}
    blocks = block_elements(spec, font, size_pt, line_pct, figure_state)
    if spec.get("footer", True):
        blocks.append(make_paragraph([], line_pct=100))  # keep the footer off the last line

    pkg = Package()
    pkg.set(
        "[Content_Types].xml",
        (
            XML_DECL
            + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Default Extension="png" ContentType="image/png"/>'
            '<Default Extension="jpg" ContentType="image/jpeg"/>'
            '<Default Extension="jpeg" ContentType="image/jpeg"/>'
            '<Override PartName="/word/document.xml" ContentType="%s"/>'
            '<Override PartName="/word/styles.xml" ContentType="%s"/>'
            '<Override PartName="/word/settings.xml" ContentType="%s"/>'
            '<Override PartName="/word/fontTable.xml" ContentType="%s"/>'
            '<Override PartName="/docProps/core.xml" ContentType="%s"/>'
            '<Override PartName="/docProps/app.xml" ContentType="%s"/>'
            "</Types>"
            % (CT_DOCUMENT, CT_STYLES, CT_SETTINGS, CT_FONT_TABLE, CT_CORE, CT_APP)
        ).encode("utf-8"),
    )
    pkg.set(
        "_rels/.rels",
        (
            XML_DECL
            + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="%s" Target="word/document.xml"/>'
            '<Relationship Id="rId2" Type="%s" Target="docProps/core.xml"/>'
            '<Relationship Id="rId3" Type="%s" Target="docProps/app.xml"/>'
            "</Relationships>" % (REL_OFFICE_DOCUMENT, REL_CORE, REL_APP)
        ).encode("utf-8"),
    )
    pkg.set("word/document.xml", document_xml(blocks, page).encode("utf-8"))
    pkg.set("word/styles.xml", styles_xml(font, size_pt, line_pct).encode("utf-8"))
    pkg.set(
        "word/settings.xml",
        (
            XML_DECL
            + '<w:settings xmlns:w="%s"><w:zoom w:percent="100"/><w:defaultTabStop w:val="720"/>'
            '<w:characterSpacingControl w:val="compressPunctuation"/>'
            '<w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat>'
            "</w:settings>" % W
        ).encode("utf-8"),
    )
    pkg.set(
        "word/fontTable.xml",
        (
            XML_DECL
            + '<w:fonts xmlns:w="%s"><w:font w:name="%s"><w:charset w:val="81"/>'
            '<w:family w:val="auto"/><w:pitch w:val="variable"/></w:font></w:fonts>'
            % (W, font["eastAsia"])
        ).encode("utf-8"),
    )
    pkg.set("docProps/core.xml", core_xml(spec).encode("utf-8"))
    pkg.set(
        "docProps/app.xml",
        (
            XML_DECL
            + '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
            "<Application>hyper-docx</Application></Properties>"
        ).encode("utf-8"),
    )

    rel_entries = [
        ("rId1", REL_STYLES, "styles.xml"),
        ("rId2", REL_SETTINGS, "settings.xml"),
        ("rId3", REL_FONT_TABLE, "fontTable.xml"),
    ]
    if spec.get("footer", True):
        pkg.set("word/footer1.xml", footer_xml(font, 10).encode("utf-8"))
        pkg.ensure_override("word/footer1.xml", CT_FOOTER)
        rel_entries.append(("rId4", REL_FOOTER, "footer1.xml"))
        document = pkg.document()
        sect = pkg.body().find(qn("w:sectPr"))
        ref = _sub(sect, "w:footerReference", {"w:type": "default", "r:id": "rId4"})
        sect.remove(ref)
        sect.insert(0, ref)

    for counter, (name, ext, source, rel_id) in enumerate(figure_state["figures"], start=1):
        media_name = "word/media/%s" % name
        with open(source, "rb") as handle:
            pkg.set(media_name, handle.read())
        rel_entries.append((rel_id, REL_IMAGE, "media/%s" % name))

    pkg.set(
        "word/_rels/document.xml.rels",
        (
            XML_DECL
            + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + "".join(
                '<Relationship Id="%s" Type="%s" Target="%s"/>' % (rid, rel_type, target)
                for rid, rel_type, target in rel_entries
            )
            + "</Relationships>"
        ).encode("utf-8"),
    )
    pkg.save(out_path)
    return {"out": out_path, "blocks": len(blocks), "figures": len(figure_state["figures"])}


def load_spec(path):
    if path == "-":
        import sys

        return json.load(sys.stdin)
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)
