"""Source-derived text repair islands with immutable original PDF mathematics.

The program derives every rectangle from source/target text geometry. Models
translate only named prose slots; they cannot supply geometry or replace math.
"""
from collections import Counter
from pathlib import Path
import hashlib
import html
import math
import re
import unicodedata
import pymupdf as fitz
import math_operators
import source_fragments
import source_redaction


MATH_FONT=re.compile(r'^(?:[A-Z]{6}\+)?(?:CM|MSAM|MSBM|STIX|Math|Symbol)',re.I)
LATIN=re.compile(r'[A-Za-z]')
CONTACT=re.compile(r'@[A-Za-z0-9.]+\.[A-Za-z]{2,}|https?://')
OPAQUE_MATH=re.compile(r'[∫∑√±=<>^_{}α-ωΑ-Ω∂∥≤≥∈∞\U0001d400-\U0001d7ff]|\(cid:')


class SourceRepairCommitError(ValueError):
    """The new in-memory candidate must be discarded after a write failure."""


def text_blocks(page):
    blocks=[b for b in page.get_text('rawdict')['blocks'] if b['type']==0]
    for block in blocks:
        for line in block['lines']:
            for span in line['spans']:span['text']=''.join(c['c'] for c in span['chars'])
        source_fragments.annotate_block(block,MATH_FONT,OPAQUE_MATH,CONTACT)
    return blocks


def source_spans(line):
    """Keep native literal ownership while exposing the surrounding prose."""
    if '_source_fragments' in line:
        yield from line['_source_fragments']
    else:
        yield from source_fragments.fragments(line,MATH_FONT,OPAQUE_MATH,CONTACT)


def block_text(block):
    return '\n'.join(''.join(s['text'] for s in l['spans']) for l in block['lines'])


def prose_signature(text):
    import chat_bridge as bridge
    plain=unicodedata.normalize('NFKC',bridge.MARKER.sub('',text)).casefold()
    return re.sub(r'[^a-z]','',plain)


def locate_source_prose(page,text):
    """Match unique complete prose evidence, with math kept opaque; no model box."""
    needle=prose_signature(text)
    if len(needle)<8:return None,'SOURCE_PROSE_EVIDENCE_TOO_SHORT'
    slots=units(page,page.rect,'mixed_prose');stream='';ranges=[]
    for unit in slots:
        part=prose_signature(unit['source'])
        if not part:continue
        ranges.append((len(stream),len(stream)+len(part),unit));stream+=part
    at=stream.find(needle)
    if at<0:return None,'SOURCE_PROSE_NOT_FOUND'
    if stream.find(needle,at+1)>=0:return None,'SOURCE_PROSE_AMBIGUOUS'
    end=at+len(needle)
    if at not in {r[0] for r in ranges} or end not in {r[1] for r in ranges}:
        return None,'SOURCE_PROSE_PARTIAL_UNIT'
    matched=[unit for start,stop,unit in ranges if start<end and stop>at]
    boxes=[fitz.Rect(box) for unit in matched for box in unit['boxes']]
    if not boxes:return None,'SOURCE_PROSE_NO_GEOMETRY'
    area=fitz.Rect(boxes[0])
    for box in boxes[1:]:area|=box
    return {'bbox':list(area),'source_prose_sha256':hashlib.sha256(needle.encode()).hexdigest(),
        'source_units':len(matched)},None


def restored_semantic_pair(slots,translations,signature):
    """Describe actual slot text and identical opaque source objects after verification."""
    if signature is None or not validate_paragraphs(slots,translations):raise ValueError('SOURCE_SEMANTIC_PAIR_UNVERIFIED')
    if not slots:return None
    source=[];target=[];bindings=[]
    def immutable(text):
        if not text.strip():return
        bindings.append(hashlib.sha256(text.encode()).hexdigest());token='{v'+str(len(bindings))+'}'
        source.append(token);target.append(token)
    if slots:immutable(slots[0].get('left_literal',''))
    for unit,replacement in zip(slots,translations):
        source.append(unit['source']);target.append(replacement);immutable(unit.get('right_literal',''))
    import json
    return {'pair':{'source':' '.join(source),'target':' '.join(target)},
        'source_prose_signature':prose_signature(' '.join(unit['source'] for unit in slots)),
        'opaque_source_bindings_sha256':bindings,
        'protected_source_signature_sha256':hashlib.sha256(json.dumps(signature,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),
        'scope':'Actual source-prose placements with unchanged source objects represented by local opaque IDs; not decoded mathematics.'}


def overlap(a,b):
    r=fitz.Rect(a)&fitz.Rect(b)
    return not r.is_empty and r.width>.2 and r.height>.2


def ink_blocks(page):
    """Separate visible ink from font ascent/descent margins for closure."""
    import numpy as np
    if page.rect.width*page.rect.height*4>20_000_000:raise ValueError('SOURCE_GEOMETRY_PIXEL_LIMIT')
    pix=page.get_pixmap(dpi=144,alpha=False)
    pixels=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,pix.n)
    result=text_blocks(page)
    for block in result:
        box=fitz.Rect(block['bbox'])&page.rect;r=box*2
        x0,y0=max(0,int(r.x0)),max(0,int(r.y0));x1,y1=min(pix.width,int(r.x1)+1),min(pix.height,int(r.y1)+1)
        ink=np.any(pixels[y0:y1,x0:x1]<250,axis=2)
        yy,xx=np.where(ink)
        block['ink_bbox']=([page.rect.x0+(x0+int(xx.min()))/2,page.rect.y0+(y0+int(yy.min()))/2,
            page.rect.x0+(x0+int(xx.max())+1)/2,page.rect.y0+(y0+int(yy.max())+1)/2] if len(xx) else None)
    return result


def derive_island(source,target,region,geometry=None):
    """Close over intersecting text blocks, bounded to one column or table band."""
    if source.rotation or target.rotation:return None,'SOURCE_ROTATED_PAGE'
    seed=fitz.Rect(region['bbox']);area=fitz.Rect(seed)
    source_blocks,target_blocks=geometry or (ink_blocks(source),ink_blocks(target))
    maximum_height=min(280,source.rect.height*.36)
    if area.height>maximum_height or area.width>source.rect.width*.92:
        return None,'SOURCE_ISLAND_TOO_LARGE'
    for _ in range(12):
        expanded=fitz.Rect(seed)
        for block in source_blocks+target_blocks:
            rect=fitz.Rect(block['bbox'])
            if block.get('ink_bbox') and overlap(area,block['ink_bbox']):expanded|=rect
        # Use real ink to decide whether a neighbor belongs to this island;
        # retain full selected font metrics plus HTML leading for its canvas.
        expanded+=(-1.7,-1.7,1.7,1.7)
        if expanded==area:break
        if expanded.height>maximum_height or expanded.width>source.rect.width*.92:
            return None,'SOURCE_ISLAND_TOO_LARGE'
        area=expanded
    else:return None,'SOURCE_ISLAND_NOT_CLOSED'
    if not source.rect.contains(area):return None,'SOURCE_ISLAND_OUTSIDE_PAGE'
    # Never replace raster figure pixels or vector drawings unless source and
    # target have the same drawing geometry in this derived island.
    if any(overlap(area,x['bbox']) for x in source.get_image_info()+target.get_image_info()):
        return None,'SOURCE_ISLAND_TOUCHES_IMAGE'
    drawing=lambda page:sorted(repr({k:d.get(k) for k in ('items','type','color','fill','width','dashes','closePath')})
                              for d in page.get_drawings() if overlap(area,d['rect']+(-.2,-.2,.2,.2)))
    if drawing(source)!=drawing(target):return None,'SOURCE_ISLAND_GRAPHICS_DIFFER'
    source_indices=[n for n,b in enumerate(source_blocks) if b.get('ink_bbox') and overlap(area,b['ink_bbox'])]
    selected=[source_blocks[n] for n in source_indices]
    target_redactions=[b['ink_bbox'] for b in target_blocks if b.get('ink_bbox') and overlap(area,b['ink_bbox'])]
    prose='\n'.join(block_text(b) for b in selected)
    decimals=re.findall(r'\d+\.\d+',source.get_text(clip=fitz.Rect(area.x0,area.y1,area.x1,min(source.rect.height,area.y1+90))))
    horizontal=[d for d in source.get_drawings() if d['rect'].width>area.width*.6 and d['rect'].height<2 and abs(d['rect'].y0-area.y1)<40]
    kind='table_header' if len(decimals)>=8 and horizontal else 'mixed_prose'
    if CONTACT.search(prose) and area.y0>source.rect.height*.65:kind='contact_metadata'
    return {'bbox':list(area),'kind':kind,'source_text_sha256':hashlib.sha256(prose.encode()).hexdigest(),
        'source_block_indices':source_indices,'target_redactions':target_redactions},None


def units(source,area,kind,block_indices=None,*,preserve_metadata=False,preserve_connectors=False):
    """Group prose on either side of immutable math, joining soft hyphens."""
    result=[];pending=None;last_line=None;literal='';previous=None
    operator_keys=math_operators.protected_glyph_keys(source)
    for block_number,b in enumerate(text_blocks(source)):
        pending=None
        if block_indices is not None and block_number not in block_indices:continue
        if b.get('_source_literal_scope_unclosed') and overlap(area,b['bbox']):
            raise ValueError('SOURCE_LITERAL_GROUP_UNCLOSED')
        # The operator explicitly preserves names, institutions, contacts and
        # URLs. Keep their complete source block and layout, including small
        # connecting words, rather than fragmenting it into translated pieces.
        if preserve_metadata and kind=='contact_metadata' and CONTACT.search(block_text(b)):continue
        for line in b['lines']:
            if tuple(line['dir'])!=(1.,0.) and overlap(area,line['bbox']):
                raise ValueError('SOURCE_ROTATED_TEXT')
            for span in source_spans(line):
                rect=fitz.Rect(span['bbox']);text=span['text']
                if not overlap(area,rect):continue
                if not text.strip():
                    if pending is not None:pending['source']+=text
                    elif literal:literal+=text
                    continue
                attached_name=(previous is not None and MATH_FONT.match(previous['font'])
                    and literal and not literal[-1].isspace() and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',text)
                    and 0<=rect.x0-previous['bbox'][2]<.8
                    and abs(rect.y0-previous['bbox'][1])<span['size']*.7)
                operator=bool(span.get('chars')) and all(math_operators.glyph_key(span,c) in operator_keys
                    for c in span['chars'] if c['c'].strip()) and bool(text.strip())
                editable=(LATIN.search(text) and not span.get('_source_literal') and not operator and not MATH_FONT.match(span['font']) and 'Mon' not in span['font']
                          and not CONTACT.search(text) and not OPAQUE_MATH.search(text)
                          and not re.fullmatch(r'\s*[IVXLCDM]+\.\s*',text))
                # Include numeric labels and punctuation in the same prose run;
                # their counts are checked, while separate math remains opaque.
                if pending is not None and not span.get('_source_literal') and not MATH_FONT.match(span['font']) and re.fullmatch(r'[\d\s.,:;!?()\[\]/-]+',text):
                    editable=True
                if re.fullmatch(r'\s*\(\d+[a-z]?\)\s*',text):editable=False
                if kind=='table_header' and not span.get('_source_literal') and all(len(word)<=3 for word in re.findall(r'[A-Za-z]+',text)):
                    editable=bool(re.search(r'[A-Za-z]{4,}',text))
                    if pending is not None and re.fullmatch(r'\s*\[[A-Za-z/0-9]+\]\s*',text):editable=True
                if attached_name:editable=False
                if editable:
                    if (pending is not None and last_line is not line
                            and bool(span['flags']&16)!=pending['bold']):pending=None
                    if pending is None:
                        pending={'source':'','boxes':[],'font_size':span['size'],'bold':bool(span['flags']&16),
                                  'left_literal':literal.strip(),'right_literal':'','paragraph':block_number,
                                  'fidelity_scope':'source_gap_v2','source_glyph_keys':[]}
                        literal=''
                        result.append(pending)
                    if pending['source'].endswith('-') and text and text[0].islower():
                        pending['source']=pending['source'][:-1]+text
                    else:
                        if pending['source'] and last_line is not line and not pending['source'][-1].isspace():pending['source']+=' '
                        pending['source']+=text
                    if pending['boxes'] and last_line is line:
                        pending['boxes'][-1]=list(fitz.Rect(pending['boxes'][-1])|rect)
                    else:pending['boxes'].append(list(rect))
                    pending['font_size']=min(pending['font_size'],span['size']);last_line=line
                    pending['source_glyph_keys'].extend(math_operators.glyph_key(span,c)
                        for c in span['chars'] if c['c'].strip())
                elif text.strip():
                    if result:result[-1]['right_literal']+=text
                    literal+=text;pending=None
                previous=span
    for unit in result:unit['source']=unit['source'].strip()
    if preserve_connectors:
        retained=[]
        for n,unit in enumerate(result):
            capacity=sum(fitz.Rect(b).width for b in unit['boxes'])/(unit['font_size']*.85)
            neighbors=result[max(0,n-1):n]+result[n+1:n+2]
            tiny=(unit['source'].lower() in {'in','of','at','to','by','on','as','if','or','and'} and capacity<1
                and len(neighbors)==2 and all(x['paragraph']==unit['paragraph'] for x in neighbors)
                and unit.get('left_literal','').strip() and unit.get('right_literal','').strip())
            if tiny:
                # Keep ORIGINAL PDF characters and position rather than
                # erasing a relation or moving its equation reference.
                result[n-1]['right_literal']+=unit['source']+unit['right_literal']
                result[n+1]['left_literal']=unit['left_literal']+unit['source']+result[n+1]['left_literal']
            else:retained.append(unit)
        result=retained
    return result


def protected_signature(page,area,editable_boxes,*,editable_glyph_keys=None):
    """Visible glyph/font/origin signature outside editable prose.

    Redaction may remove an adjacent space and split/re-anchor its text span.
    That is not a change to the original visible mathematical glyph. Compare
    each nonspace glyph's own origin, never the containing span's whitespace.
    """
    # A font's descent box can cross an island even when the glyph's ink is
    # entirely in the preceding line. Such an outside glyph is not copied by
    # show_pdf_page(clip=area). Scope partial boxes by their actual visible ink;
    # keep the exact font/character/origin check for every affected glyph.
    # Full-page protected_pixels still detects changes outside this island.
    import numpy as np
    limit=fitz.Rect(area)&page.rect;pixels=None;pix=None;scale=4
    def affected(box):
        nonlocal pixels,pix
        rect=fitz.Rect(box);inside=rect&limit
        if inside.is_empty:return False
        if limit.contains(rect):return True
        if pixels is None:
            if limit.width*limit.height*scale*scale>20_000_000:
                raise ValueError('SOURCE_SIGNATURE_PIXEL_LIMIT')
            pix=page.get_pixmap(dpi=72*scale,clip=limit,alpha=False)
            pixels=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,pix.n)
        x0=max(0,math.ceil(inside.x0*scale-.5)-pix.x)
        y0=max(0,math.ceil(inside.y0*scale-.5)-pix.y)
        x1=min(pix.width,math.ceil(inside.x1*scale-.5)-pix.x)
        y1=min(pix.height,math.ceil(inside.y1*scale-.5)-pix.y)
        return bool(np.any(pixels[y0:y1,x0:x1]<255))
    result=[]
    for b in text_blocks(page):
        for l in b['lines']:
            for s in source_spans(l):
                if not overlap(area,s['bbox']) or not s['text'].strip():continue
                if editable_glyph_keys is None and any(fitz.Rect(box).contains(fitz.Rect(s['bbox'])) for box in editable_boxes):continue
                for char in s['chars']:
                    if editable_glyph_keys is not None and math_operators.glyph_key(s,char) in editable_glyph_keys:continue
                    if char['c'].strip() and affected(char['bbox']):
                        result.append((s['font'],char['c'],round(s['size'],3),
                            tuple(round(x,3) for x in char['origin'])))
    return sorted(result)


def numeric(text):
    import numeric_literals
    return numeric_literals.tokens(text)


def validate_translation(unit,replacement,*,reorder_numbers=False):
    if not isinstance(replacement,str) or not replacement.strip() or len(replacement)>4000:return False
    import date_literals
    before,a=date_literals.extract(unit['source'],numeric_iso=False)
    after,b=date_literals.extract(replacement,numeric_iso=False)
    if (Counter(before)!=Counter(after) if reorder_numbers else before!=after):return False
    if (Counter(numeric(a))!=Counter(numeric(b)) if reorder_numbers else numeric(a)!=numeric(b)):return False
    mathematical=r'[=<>^_{}∫∑√±∂∈≥≤\u0370-\u03ff\u1f00-\u1fff\U0001d400-\U0001d7ff]'
    if Counter(re.findall(mathematical,unit['source']))!=Counter(re.findall(mathematical,replacement)):return False
    if re.search(r'\[已省略\]|\(cid:|\{v\d',replacement):return False
    if ('…' in replacement and '…' not in unit['source']) or ('...' in replacement and '...' not in unit['source']):return False
    for literal in re.findall(r'\[[A-Za-z/0-9]+\]',unit['source']):
        if unit['source'].count(literal)!=replacement.count(literal):return False
    for literal in re.findall(r'\b(?=[A-Za-z0-9-]*[A-Za-z])(?=[A-Za-z0-9-]*\d)[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\b',unit['source']):
        if unit['source'].count(literal)!=replacement.count(literal):return False
    return True


def validate_paragraphs(units,translations):
    return not paragraph_errors(units,translations)


def paragraph_errors(units,translations):
    """Bounded evidence for a corrective request; never relax a failed check."""
    if len(units)!=len(translations):return [{'kind':'slot_count'}]
    errors=[]
    strict=any(u.get('fidelity_scope')=='source_gap_v2' for u in units)
    if strict:
        literal_names=set(re.findall(r'(?<![A-Za-z0-9_])[A-Za-z][A-Za-z0-9_]*(?![A-Za-z0-9_])',
            ' '.join(u.get('left_literal','')+' '+u.get('right_literal','') for u in units)))
        originals=' '.join(u['source'] for u in units)
        candidates=' '.join(t for t in translations if isinstance(t,str))
        for literal in sorted(literal_names):
            pattern=r'(?<![A-Za-z0-9_])'+re.escape(literal)+r'(?![A-Za-z0-9_])'
            before=len(re.findall(pattern,originals));after=len(re.findall(pattern,candidates))
            if after>before:
                errors.append({'kind':'copied_immutable_context_in_prose','literal':literal,
                               'maximum_prose_count':before,'actual_prose_count':after})
        for n,(unit,text) in enumerate(zip(units,translations)):
            if not validate_translation(unit,text):
                errors.append({'kind':'source_gap_fidelity','slot':n,
                    'paragraph':unit.get('paragraph',0),'source_digits':numeric(unit['source']),
                    'candidate_digits':numeric(text) if isinstance(text,str) else None,
                    'nonempty_required':True})
        return errors[:32]
    groups={}
    for unit,text in zip(units,translations):
        if not isinstance(text,str) or len(text)>4000:return [{'kind':'invalid_slot_text'}]
        source,target=groups.setdefault(unit.get('paragraph',0),([],[]))
        source.append(unit['source']);target.append(text)
    return ([] if all(validate_translation({'source':' '.join(a)},' '.join(b),reorder_numbers=True)
                      for a,b in groups.values()) else [{'kind':'paragraph_fidelity'}])


def fit_prose(page,unit,replacement,*,commit=False,validated=False,max_scale=1,y_shift=0):
    """Flow translated prose through only the original prose gaps, >=85% size."""
    if not validated and not validate_translation(unit,replacement):return None
    if not replacement.strip():return {'scale':1,'font_pt':unit['font_size'],'placements':[]}
    for scale in (1,.95,.9,.85):
        if scale>max_scale:continue
        size=unit['font_size']*scale
        if size<5.5:continue
        remaining=replacement.strip();placements=[]
        for original in unit['boxes']:
            box=fitz.Rect(original)
            # Use interline leading, without entering adjacent horizontal math.
            box.y0+=y_shift-1.2;box.y1+=y_shift+1.2
            css='body {margin:0;padding:0;font-family:sans-serif;font-weight:%s;font-size:%.4fpt;line-height:1.15;}'%('bold' if unit.get('bold') else 'normal',size)
            def fits(text):
                with fitz.open() as trial:
                    p=trial.new_page(width=page.rect.width,height=page.rect.height)
                    return p.insert_htmlbox(box,html.escape(text),css=css,scale_low=1)[0]>=0
            low,high=0,len(remaining)
            while low<high:
                middle=(low+high+1)//2
                if fits(remaining[:middle]):low=middle
                else:high=middle-1
            # Never introduce a split inside an ASCII name/technical word.
            while 0<low<len(remaining) and remaining[low-1].isascii() and remaining[low-1].isalnum() and remaining[low].isascii() and remaining[low].isalnum():low-=1
            if low:
                placements.append({'bbox':list(box),'text':remaining[:low],'css':css})
                remaining=remaining[low:].lstrip()
            if not remaining:break
        if not remaining:
            import prose_ink
            # Validate real fallback-font ink after the complete candidate has
            # been laid out. Binary-search layout success alone can clip CJK
            # tops at line-height:1 even when spare height is nonnegative.
            with fitz.open() as trial:
                p=trial.new_page(width=page.rect.width,height=page.rect.height)
                for item in placements:p.insert_htmlbox(item['bbox'],html.escape(item['text']),css=item['css'],scale_low=1)
                ink=prose_ink.check(p)
            if not ink['passed']:continue
            if commit:
                boundary=prose_ink.glyph_count(page)
                for item in placements:
                    if page.insert_htmlbox(item['bbox'],html.escape(item['text']),css=item['css'],scale_low=1)[0]<0:
                        raise ValueError('SOURCE_PROSE_FIT_CHANGED')
                ink=prose_ink.check(page,first_glyph=boundary)
                if not ink['passed']:raise ValueError('SOURCE_PROSE_NATIVE_INK_UNSAFE')
            return {'scale':scale,'font_pt':size,'placements':placements,'native_ink':ink}
    return None


def restore_region(source_doc,source_index,target_doc,target_index,island,translations):
    """Build on a scratch source page; copy original math and numeric geometry."""
    area=fitz.Rect(island['bbox']);source=source_doc[source_index]
    import pdf_objects,render_lineage,prose_ink
    original_native=pdf_objects.inventory(source)
    original_native_sha256=pdf_objects.digest(original_native)
    slots=units(source,area,island['kind'],island.get('source_block_indices'),
        preserve_metadata=island.get('preserve_contact_metadata',False),
        preserve_connectors=island.get('preserve_tiny_connectors',False))
    if len(slots)!=len(translations):raise ValueError('SOURCE_REPAIR_SLOT_COUNT')
    if not validate_paragraphs(slots,translations):raise ValueError('SOURCE_REPAIR_PARAGRAPH_FIDELITY')
    target=target_doc[target_index]
    boxes=[box for u in slots for box in u['boxes']]
    owned=source_redaction.owned_keys(slots)
    for maximum,shift in [(scale,offset) for scale in (1,.95,.9,.85) for offset in (0,.6,1.2)]:
        with fitz.open() as scratch:
            scratch.insert_pdf(source_doc,from_page=source_index,to_page=source_index)
            p=scratch[0];signature=protected_signature(p,area,boxes,editable_glyph_keys=owned);fits=[]
            for unit,replacement in zip(slots,translations):
                fitted=fit_prose(p,unit,replacement,validated=True,max_scale=maximum,y_shift=shift)
                if fitted is None:raise ValueError('SOURCE_PROSE_DOES_NOT_FIT')
                fits.append(fitted)
            redactions=source_redaction.apply(p,area,slots)
            if protected_signature(p,area,[])!=signature:raise ValueError('SOURCE_PROTECTED_GLYPH_CHANGED')
            protected_reference=p.get_pixmap(dpi=144,alpha=False)
            fits=[fit_prose(p,unit,replacement,commit=True,validated=True,max_scale=maximum,y_shift=shift)
                for unit,replacement in zip(slots,translations)]
            if not protected_pixels(source,p,area,boxes,protected_reference=protected_reference):continue
            # Remove complete old glyphs, including hidden text, only after all
            # source math/literal checks and program-only font variants pass.
            prose_ids=[g['id'] for fit in fits for g in fit.get('native_ink',{}).get('native_glyphs',[])]
            def overlay(destination):
                for box in island.get('target_redactions',[list(area)]):destination.add_redact_annot(box,fill=False,cross_out=False)
                destination.apply_redactions(images=0,graphics=0,text=0)
                boundary=prose_ink.glyph_count(destination)
                cover=render_lineage.opaque_cover(destination,area)
                destination.show_pdf_page(area,scratch,0,clip=area)
                copied=render_lineage.observe_copy(p,destination,area,first_glyph=boundary,prose_ids=prose_ids)
                if not copied['passed']:raise ValueError('SOURCE_COPY_NATIVE_LINEAGE_UNSAFE')
                copied=render_lineage.bind_original(copied,original_native)
                return cover,copied
            # Validate the actual copy and its outer clip before modifying the
            # caller's candidate. The caller still owns a new unsaved PDF;
            # source and previous artifact paths are never overwritten here.
            with fitz.open() as preview:
                preview.insert_pdf(target_doc,from_page=target_index,to_page=target_index)
                overlay(preview[0])
            try:cover,copied=overlay(target)
            except Exception as error:
                raise SourceRepairCommitError('SOURCE_COPY_COMMIT_FAILED_DISCARD_CANDIDATE') from error
            frame={'source_page':source_index+1,'target_page':target_index+1,
                'original_source_native_sha256':original_native_sha256,
                'producer':'source_repair.restore_region','producer_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'planned_island_bbox':list(area),'opaque_cover':cover,'copy':copied,
                'source_redaction_version':1,'source_redaction_boxes':redactions,
                'editable_source_glyph_keys_sha256':hashlib.sha256(repr(sorted(owned)).encode()).hexdigest(),
                'source_prose_units':[{'source_text_sha256':hashlib.sha256(unit['source'].encode()).hexdigest(),
                    'replacement_text_sha256':hashlib.sha256(replacement.encode()).hexdigest(),
                    'original_source_candidate_glyph_ids':[g['id'] for g in original_native['glyphs']
                        if any((fitz.Rect(g['ink_bbox'])&fitz.Rect(box)).get_area()>0 for box in unit['boxes'])]}
                    for unit,replacement in zip(slots,translations)]}
            return {'bbox':list(area),'kind':island['kind'],'slots':len(slots),
                'source_protected_spans_verified':len(signature),'source_protected_glyphs_verified':len(signature),
                'retained_tiny_connectors':island.get('retained_tiny_connectors',[]),
                'protected_signature_unit':'visible_glyphs','fits':fits,'maximum_prose_scale':maximum,
                'prose_y_shift':shift,'semantic_pair':restored_semantic_pair(slots,translations,signature),'render_lineage':frame}
    raise ValueError('SOURCE_PROTECTED_PIXELS_CHANGED')


def protected_pixels(source,repaired,area,editable_boxes,dpi=144,protected_reference=None):
    """New prose may not paint over original math, literals or vector strokes."""
    import numpy as np
    left=source.get_pixmap(dpi=dpi,alpha=False);right=repaired.get_pixmap(dpi=dpi,alpha=False)
    a=np.frombuffer(left.samples,dtype=np.uint8).reshape(left.height,left.width,left.n)
    b=np.frombuffer(right.samples,dtype=np.uint8).reshape(right.height,right.width,right.n)
    reference=protected_reference or left
    protected=np.frombuffer(reference.samples,dtype=np.uint8).reshape(left.height,left.width,left.n)
    diff=np.any(a!=b,axis=2)
    def pixels(rect):
        r=fitz.Rect(rect)*(dpi/72)
        return max(0,int(r.y0)),min(left.height,int(r.y1)+1),max(0,int(r.x0)),min(left.width,int(r.x1)+1)
    for box in editable_boxes:
        y0,y1,x0,x1=pixels(fitz.Rect(box)+(-.5,-1.7,.5,1.7));diff[y0:y1,x0:x1]=False
    if diff.any():return False
    # The allowed prose gaps can touch math bboxes. Check these again without a
    # prose mask; an unchanged text signature alone cannot detect new ink.
    for block in text_blocks(source):
        for line in block['lines']:
            for span in source_spans(line):
                if not span['text'].strip() or not overlap(area,span['bbox']):continue
                if any(fitz.Rect(box).contains(fitz.Rect(span['bbox'])) for box in editable_boxes):continue
                # Font metric boxes include blank ascender/descender space.
                # Protect each actual glyph's ink bounds plus a pixel halo,
                # including holes, using a reference with editable prose removed.
                # This prevents both collision and false failures on blank font
                # margins, without changing any math glyph or its coordinates.
                glyphs=span.get('chars') or [{'bbox':span['bbox'],'c':span['text']}]
                for glyph in glyphs:
                    if not glyph['c'].strip():continue
                    y0,y1,x0,x1=pixels(fitz.Rect(glyph['bbox'])+(-.75,-.75,.75,.75))
                    ink=np.any(protected[y0:y1,x0:x1]<250,axis=2)
                    yy,xx=np.where(ink)
                    if not len(xx):continue
                    a0,a1=max(0,y0+int(yy.min())-1),min(left.height,y0+int(yy.max())+2)
                    b0,b1=max(0,x0+int(xx.min())-1),min(left.width,x0+int(xx.max())+2)
                    if np.any(protected[a0:a1,b0:b1]!=b[a0:a1,b0:b1]):return False
    return True


def prepare(source,target,known,issues,limit,*,preserve_metadata=False,preserve_connectors=False):
    """Prioritize serious issues and derive bounded, nonoverlapping islands."""
    by_id={r['id']:r for r in known};plans=[];decisions=[]
    if source.rotation or target.rotation:
        return [],[{'region_id':i['region_id'],'reason':'SOURCE_ROTATED_PAGE'} for i in issues]
    serious=any(x['severity']!='minor' for x in issues)
    order={'critical':0,'major':1,'minor':2}
    geometry=(ink_blocks(source),ink_blocks(target))
    for issue in sorted(issues,key=lambda x:order[x['severity']]):
        decision={'region_id':issue['region_id'],'category':issue['category'],'severity':issue['severity']}
        decisions.append(decision)
        if serious and issue['severity']=='minor':decision['reason']='SERIOUS_ISSUES_FIRST';continue
        region=by_id.get(issue['region_id'])
        if region is None:decision['reason']='UNMAPPED_ISSUE';continue
        island,error=derive_island(source,target,region,geometry)
        if error:decision['reason']=error;continue
        existing=next((x for x in plans if overlap(x['bbox'],island['bbox'])),None)
        if existing:
            decision['reason']='COVERED_BY_SOURCE_ISLAND';continue
        if len(plans)>=limit:decision['reason']='REPAIR_REGION_LIMIT';continue
        island['preserve_contact_metadata']=preserve_metadata and island['kind']=='contact_metadata'
        island['preserve_tiny_connectors']=preserve_connectors
        try:slots=units(source,fitz.Rect(island['bbox']),island['kind'],island.get('source_block_indices'),
            preserve_metadata=island['preserve_contact_metadata'],preserve_connectors=preserve_connectors)
        except ValueError as error:decision['reason']=str(error);continue
        if preserve_connectors:
            all_slots=units(source,fitz.Rect(island['bbox']),island['kind'],island.get('source_block_indices'),
                preserve_metadata=island['preserve_contact_metadata'])
            island['retained_tiny_connectors']=[{'source':u['source'],'boxes':u['boxes'],
                'reason':'ZERO_CJK_CAPACITY_BETWEEN_IMMUTABLE_OBJECTS'} for u in all_slots
                if not any(u['paragraph']==v['paragraph'] and u['boxes']==v['boxes'] for v in slots)]
        if not slots and not island['preserve_contact_metadata']:decision['reason']='NO_TRANSLATABLE_PROSE';continue
        if sum(len(x['source']) for x in slots)>16000 or len(slots)>96:
            decision['reason']='SOURCE_PLAN_TOO_LARGE';continue
        try:
            with fitz.open() as preview:
                preview.insert_pdf(source.parent,from_page=source.number,to_page=source.number)
                p=preview[0];owned=source_redaction.owned_keys(slots)
                signature=protected_signature(p,island['bbox'],[],editable_glyph_keys=owned)
                redactions=source_redaction.apply(p,island['bbox'],slots)
                if protected_signature(p,island['bbox'],[])!=signature:
                    raise ValueError('SOURCE_REDACTION_PROTECTED_GLYPH_CHANGED')
                island['source_redaction_preflight']={'actual_rectangles':len(redactions),
                    'protected_glyphs':len(signature),'verified':True}
        except ValueError as error:decision['reason']=str(error);continue
        plans.append({**island,'units':slots,'issue':issue})
        decision['reason']='SOURCE_ISLAND_PREPARED';decision['bbox']=island['bbox']
    return plans,decisions
