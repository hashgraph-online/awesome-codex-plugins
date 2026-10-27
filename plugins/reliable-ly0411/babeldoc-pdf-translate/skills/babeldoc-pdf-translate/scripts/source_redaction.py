"""Delete only owned prose glyphs without touching overlapping script boxes.

PDF text redaction uses glyph rectangles, not visible ink. A descender/script
rectangle can cross the next line even when their ink is separate. Carve a
representable interior rectangle for each editable glyph; keep the original
protected-glyph and final-paint checks unchanged.
"""
import math
import pymupdf as fitz
from math_operators import glyph_key


def owned_keys(units):
    return {tuple(key) for unit in units for key in unit.get('source_glyph_keys', [])}


def native_glyphs(page, area):
    records=[]
    for block in page.get_text('rawdict')['blocks']:
        if block['type']!=0:continue
        for line in block['lines']:
            for span in line['spans']:
                for char in span['chars']:
                    if not char['c'].strip():continue
                    box=fitz.Rect(char['bbox'])
                    if not box.intersects(area):continue
                    if box.is_empty or not all(math.isfinite(x) for x in box):
                        raise ValueError('SOURCE_GLYPH_FRAME_UNSUPPORTED')
                    records.append((glyph_key(span,char),box))
    if len(records)>20000:raise ValueError('SOURCE_REDACTION_GLYPH_LIMIT')
    return records


def subtract(box, obstacle):
    overlap=box&obstacle
    if overlap.is_empty:return [box]
    parts=[fitz.Rect(box.x0,box.y0,overlap.x0,box.y1),
           fitz.Rect(overlap.x1,box.y0,box.x1,box.y1),
           fitz.Rect(overlap.x0,box.y0,overlap.x1,overlap.y0),
           fitz.Rect(overlap.x0,overlap.y1,overlap.x1,box.y1)]
    return [part for part in parts if not part.is_empty]


def boxes(page, area, units):
    from render_lineage import next32
    area=fitz.Rect(area);owned=owned_keys(units)
    if not owned:return []
    records=native_glyphs(page,area);counts={}
    for key,box in records:counts[key]=counts.get(key,0)+1
    if owned-set(counts):raise ValueError('SOURCE_EDITABLE_GLYPH_MEMBERS_MISSING')
    if any(counts[key]!=1 for key in owned):raise ValueError('SOURCE_GLYPH_OWNERSHIP_AMBIGUOUS')
    protected=[box for key,box in records if key not in owned]
    result=[]
    for key,box in records:
        if key not in owned:continue
        parts=[box&area]
        for other in protected:
            parts=[part for item in parts for part in subtract(item,other)]
            if not parts:break
        if not parts:raise ValueError('SOURCE_EDITABLE_GLYPH_HAS_NO_SAFE_REDACTION')
        chosen=max(parts,key=lambda x:x.get_area())
        chosen=fitz.Rect(next32(chosen.x0,True),next32(chosen.y0,True),
                         next32(chosen.x1,False),next32(chosen.y1,False))
        if chosen.is_empty or any(chosen.intersects(other) for other in protected):
            raise ValueError('SOURCE_REDACTION_FRAME_NOT_REPRESENTABLE')
        if result:
            last=fitz.Rect(result[-1]);merged=last|chosen
            if (abs(last.y0-chosen.y0)<.0001 and abs(last.y1-chosen.y1)<.0001
                    and 0<=chosen.x0-last.x1<4
                    and not any(merged.intersects(other) for other in protected)):
                result[-1]=list(merged);continue
        result.append(list(chosen))
    return result


def apply(page, area, units):
    """Observe the actual annotation frame before any text is removed."""
    from render_lineage import next32
    owned=owned_keys(units)
    protected=[box for key,box in native_glyphs(page,fitz.Rect(area)) if key not in owned]
    planned=boxes(page,area,units);published=[]
    frame_values=[*page.rect,*page.mediabox,*fitz.Rect(area)]
    step=max(abs(next32(v,True)-v) for v in frame_values)
    for box in planned:
        trial=fitz.Rect(box)
        for attempt in range(8):
            annot=page.add_redact_annot(trial,fill=False,cross_out=False)
            actual=fitz.Rect(annot.rect)
            if not actual.is_empty and not any(actual.intersects(other) for other in protected):
                published.append(list(actual));break
            page.delete_annot(annot)
            inset=step*(2**attempt)
            trial=fitz.Rect(trial.x0+inset,trial.y0+inset,trial.x1-inset,trial.y1-inset)
            if trial.is_empty:raise ValueError('SOURCE_REDACTION_FRAME_NOT_REPRESENTABLE')
        else:raise ValueError('SOURCE_REDACTION_FRAME_NOT_REPRESENTABLE')
    if published:page.apply_redactions(images=0,graphics=0,text=0)
    return published
