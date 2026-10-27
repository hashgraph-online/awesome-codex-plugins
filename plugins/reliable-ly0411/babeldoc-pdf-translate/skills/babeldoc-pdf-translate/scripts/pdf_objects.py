"""Read actual painted glyphs, retaining clipped/hidden objects in a ledger.

Uses the already installed MuPDF renderer. Glyph identities are canonical
rendered masks from the actual font handle; PDF Unicode, subset GIDs and inferred
superscript flags are never identities. No OCR, model, PDF mutation or font
installation occurs. Unsupported outlines or uncertain visibility stay explicit.
"""
from collections import Counter
import hashlib
import json
import math
import re
import unicodedata

import pymupdf as fitz

VERSION = '0.3.0-draft.3'
m = fitz.mupdf


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def rect(value):
    return [float(value.x0), float(value.y0), float(value.x1), float(value.y1)]


def font_key(name):
    name=re.sub(r'^[A-Z]{6}\+','',name)
    return re.sub(r'(?:regular|regu)$','',re.sub('[^a-z0-9]','',name.lower()))


def quad_contains(quad,box):
    for point in (box.tl,box.tr,box.br,box.bl):
        crosses=[(b[0]-a[0])*(point.y-a[1])-(b[1]-a[1])*(point.x-a[0])
            for a,b in zip(quad,quad[1:]+quad[:1])]
        if not (all(v>=0 for v in crosses) or all(v<=0 for v in crosses)):return False
    return True


class GlyphDevice(fitz.JM_new_texttrace_device):
    def __init__(self, page):
        super().__init__([])
        self.page_rect = fitz.Rect(page.rect)
        self.spans = []
        self.fonts = {}  # Keep actual font handles alive; pointer cache cannot be reused.
        self.outlines = {}
        self.clip_stack = []
        self.group_stack = []
        self.actual_text_stack=[]
        self.opaque_covers = []
        for name in ('clip_path','clip_stroke_path','clip_text','clip_stroke_text',
                     'clip_image_mask','pop_clip','begin_group','end_group','begin_metatext','end_metatext'):
            getattr(self,'use_virtual_'+name)()

    def clip_path(self, ctx, path, even_odd, ctm, scissor):
        # Callback pointers are borrowed from the interpreter. FzPath(raw)
        # owns and drops that pointer; use the non-owning low-level query.
        self.clip_stack.append(not bool(m.ll_fz_path_is_rect(path, ctm)))

    def clip_stroke_path(self, *args):self.clip_stack.append(True)
    def clip_text(self, *args):self.clip_stack.append(True)
    def clip_stroke_text(self, *args):self.clip_stack.append(True)
    def clip_image_mask(self, *args):self.clip_stack.append(True)
    def pop_clip(self, *args):
        if not self.clip_stack:raise ValueError('NATIVE_CLIP_STACK_UNDERFLOW')
        self.clip_stack.pop()

    def begin_group(self, ctx, area, colorspace, isolated, knockout, blendmode, alpha):
        self.group_stack.append(bool(knockout or blendmode or alpha!=1))
    def end_group(self, *args):
        if not self.group_stack:raise ValueError('NATIVE_GROUP_STACK_UNDERFLOW')
        self.group_stack.pop()

    def begin_metatext(self,ctx,kind,text):
        # Only the writer's single-Unicode-character marked content is eligible
        # for a glyph binding. Do not duplicate arbitrary ActualText paragraphs
        # into every glyph or turn a label into visual/semantic proof.
        self.actual_text_stack.append(text if kind==m.FZ_METATEXT_ACTUALTEXT and isinstance(text,str) and len(text)==1 else None)

    def end_metatext(self,*args):
        if not self.actual_text_stack:raise ValueError('NATIVE_MARKED_TEXT_STACK_UNDERFLOW')
        self.actual_text_stack.pop()

    def fill_path(self, ctx, path, even_odd, ctm, colorspace, color, alpha, color_params):
        # A rectangle is a proof of occlusion only within its actual clip and
        # outside unsupported transparency groups. No bounding-box inference
        # from an arbitrary path or a clipped rectangle is accepted.
        # internal() is a borrowed view too. Retain its owning matrix until
        # both native calls return; a temporary owner can die before the call.
        identity=m.FzMatrix()
        if alpha==1 and not any(self.clip_stack) and not any(self.group_stack) and m.ll_fz_path_is_rect(path,identity.internal()):
            # The native rectangle may have a tiny rotation/shear in its CTM.
            # Keep its actual quadrilateral; its bounding box alone cannot
            # prove occlusion near a rotated corner. A null stroke is essential
            # here: default stroke bounds add ink that the fill does not paint.
            box=fitz.Rect(rect(m.ll_fz_bound_path(path,None,identity.internal())))
            matrix=fitz.Matrix(ctm.a,ctm.b,ctm.c,ctm.d,ctm.e,ctm.f)
            quad=[list(point*matrix) for point in (box.tl,box.tr,box.br,box.bl)]
            clip=fitz.Rect(rect(m.fz_device_current_scissor(self)))
            if not box.is_empty:self.opaque_covers.append((self.seqno,quad,clip))
        self.seqno+=1

    def outline(self, font, gid):
        identity = int(font.m_internal.this)
        self.fonts[identity] = font
        key = identity, gid
        if key not in self.outlines:
            if gid < 0:
                self.outlines[key] = None
            else:
                try:
                    masks=[]
                    for size in (128,256):
                        pix=m.fz_render_glyph_pixmap(font,gid,m.FzMatrix(size,0,0,size,0,0),m.FzIrect(-1024,-1024,1024,1024),8)
                        if not pix.m_internal:raise ValueError('NATIVE_GLYPH_MASK_UNAVAILABLE')
                        pm=fitz.Pixmap(pix)
                        if pm.x<=-1024 or pm.y<=-1024 or pm.x+pm.width>=1024 or pm.y+pm.height>=1024:
                            raise ValueError('CANONICAL_GLYPH_MASK_INCOMPLETE')
                        masks.append({'size':size,'bbox':[pm.x,pm.y,pm.width,pm.height,pm.n],
                            'sha256':hashlib.sha256(pm.samples).hexdigest()})
                    self.outlines[key]=digest(masks) if any(row['bbox'][2] and row['bbox'][3] for row in masks) else None
                except Exception:
                    self.outlines[key] = None
        return self.outlines[key]

    def capture(self, text, kind, ctm, colorspace, color, alpha):
        # Retain font handles only during callbacks. FreeType outline/bounds
        # work is deferred until the interpreter has released its font locks.
        clip = self.page_rect & fitz.Rect(rect(m.fz_device_current_scissor(self)))
        raw_span = text.head
        while raw_span:
            span = m.FzTextSpan(raw_span)
            font = span.font()
            self.fonts[int(font.m_internal.this)] = font
            trm = span.trm()
            self.spans.append({'font': font, 'kind': kind, 'seqno': self.seqno,
                'marked_actual_text':self.actual_text_stack[-1] if self.actual_text_stack else None,
                'clip': list(clip), 'matrix': [trm.a,trm.b,trm.c,trm.d],
                'clip_uncertain':any(self.clip_stack),'group_uncertain':any(self.group_stack),
                'ctm': [ctm.a,ctm.b,ctm.c,ctm.d,ctm.e,ctm.f],
                'items': [(span.items(i).ucs,span.items(i).gid,span.items(i).x,span.items(i).y)
                    for i in range(span.m_internal.len)]})
            raw_span = raw_span.next
        self.seqno += 1

    def fill_text(self, ctx, text, ctm, colorspace, color, alpha, color_params):
        self.capture(text, 0, ctm, colorspace, color, alpha)

    def stroke_text(self, ctx, text, stroke, ctm, colorspace, color, alpha, color_params):
        self.capture(text, 1, ctm, colorspace, color, alpha)

    def ignore_text(self, *args):
        self.capture(args[-2], 3, args[-1], None, None, 1)


def sampled_clip_ink(font,gid,matrix,clip):
    evidence=[]
    extent=max(abs(matrix.a),abs(matrix.b),abs(matrix.c),abs(matrix.d))
    if extent<=0 or 240/extent<4:raise ValueError('NATIVE_CLIP_MASK_RESOLUTION_LIMIT')
    scales=sorted({min(16,180/extent),min(32,240/extent)})
    for scale in scales:
        # MuPDF's glyph mask renderer ignores trm translation (including its
        # fractional part). Render the linear transform, then explicitly place
        # the local mask at the actual PDF origin. Comparing local ink with a
        # page-space clip was an rc14 coordinate-space error.
        linear=m.FzMatrix(matrix.a,matrix.b,matrix.c,matrix.d,0,0)
        transformed=m.fz_concat(linear,m.FzMatrix(scale,0,0,scale,0,0))
        bounds=fitz.Rect(rect(m.fz_bound_glyph(font,gid,transformed)))
        if bounds.width*bounds.height>4*1024*1024:raise ValueError('NATIVE_CLIP_MASK_LIMIT')
        pix=m.fz_render_glyph_pixmap(font,gid,transformed,m.FzIrect(-1048576,-1048576,1048576,1048576),8)
        if not pix.m_internal:raise ValueError('NATIVE_CLIP_MASK_UNAVAILABLE')
        pm=fitz.Pixmap(pix);samples=pm.samples
        if pm.n!=1 or pm.width*pm.height>4*1024*1024:raise ValueError('NATIVE_CLIP_MASK_UNSUPPORTED')
        xs=[];ys=[]
        for y in range(pm.height):
            indexes=[x for x in range(pm.width) if samples[y*pm.stride+x]]
            if indexes:xs.extend((indexes[0],indexes[-1]));ys.append(y)
        local=fitz.Rect((pm.x+min(xs))/scale,(pm.y+min(ys))/scale,
            (pm.x+max(xs)+1)/scale,(pm.y+max(ys)+1)/scale) if xs else fitz.Rect()
        bounds=local+(matrix.e,matrix.f,matrix.e,matrix.f)
        # One raster pixel on each edge bounds subpixel placement uncertainty.
        envelope=bounds+(-1/scale,-1/scale,1/scale,1/scale)
        evidence.append({'pixels_per_point':scale,'local_nonzero_ink_bbox':list(local),
            'actual_origin':[matrix.e,matrix.f],'nonzero_ink_bbox':list(bounds),
            'placement_envelope_bbox':list(envelope),'placement_uncertainty_pt':1/scale,
            'sampled_ink_fully_inside_clip':not xs or clip.contains(envelope),
            'mask_sha256':hashlib.sha256(samples).hexdigest()})
    return {'method':'Two finite native local glyph masks placed at the actual PDF origin, with a one-pixel envelope; not vector clipping equivalence.',
        'all_sampled_ink_inside_clip':all(r['sampled_ink_fully_inside_clip'] for r in evidence),'samples':evidence}


def inventory(page):
    """Every native text paint is counted, including nonvisible/alias paints.

    Scissor proves only complete exclusion. Partial clipping is never silently
    accepted. Only an opaque, later, axis-aligned filled rectangle can prove
    occlusion. Nonrectangular clipping/occlusion requires later verification.
    """
    if page.rotation:
        raise ValueError('OBJECT_INVENTORY_REQUIRES_UNROTATED_PAGE')
    device = GlyphDevice(page)
    device.ptm = m.FzMatrix(1, 0, 0, -1, 0, page.rect.height)
    m.fz_run_page(page.this, device, m.FzMatrix(), m.FzCookie())
    m.fz_close_device(device)
    traces = page.get_texttrace()
    if len(traces) != len(device.spans):
        raise ValueError('NATIVE_OBJECT_TRACE_COVERAGE_CHANGED')
    glyphs=[]
    for rendered, native in zip(traces,device.spans):
        if (native['seqno']!=rendered['seqno'] or native['kind']!=rendered['type']
            or [(c[0],c[1]) for c in native['items']] != [(c[0],c[1]) for c in rendered['chars']]):
            raise ValueError('NATIVE_OBJECT_TRACE_IDENTITY_CHANGED')
        font=native['font'];clip=fitz.Rect(native['clip'])
        primary=None
        for item,char in zip(native['items'],rendered['chars']):
            codepoint,gid,origin,box=char
            matrix=m.fz_concat(m.FzMatrix(*native['matrix'],item[2],item[3]),m.FzMatrix(*native['ctm']))
            try:ink=fitz.Rect(rect(m.fz_bound_glyph(font,gid,matrix))) if gid>=0 else fitz.Rect(box)
            except Exception:ink=fitz.Rect(box)
            row={'id':'g%06d'%len(glyphs),'unicode':chr(codepoint) if 0<=codepoint<=0x10ffff else '\ufffd',
                'shape':device.outline(font,gid),'font':rendered['font'],'size':rendered['size'],'gid':gid,
                'origin':list(origin),'bbox':list(box),'ink_bbox':list(ink),'clip_bbox':list(clip),
                'paint_type':rendered['type'],'opacity':rendered['opacity'],'color':list(rendered['color']),
                'direction':list(rendered['dir']),
                'seqno':rendered['seqno'],'visibility':'visible_candidate'}
            marked=native['marked_actual_text'] if len(native['items'])==1 and gid>=0 else None
            row.update(marked_actual_text=marked,marked_text_glyph_mask_sha256=None,marked_text_matches_native_mask=False)
            if marked and marked!=row['unicode'] and not marked.isspace() and row['shape'] is not None:
                try:
                    encoded=m.fz_encode_character(font,ord(marked))
                    shape=device.outline(font,encoded) if encoded>0 else None
                    row.update(marked_text_glyph_mask_sha256=shape,
                        marked_text_matches_native_mask=shape is not None and shape==row['shape'])
                except Exception:pass
            row.update(clip_uncertain=native['clip_uncertain'],group_uncertain=native['group_uncertain'])
            if rendered['type']==3 or rendered['opacity']==0:row['visibility']='hidden_paint'
            elif ink.is_empty or not (ink&clip).get_area():row['visibility']='clipped_out_or_empty'
            elif not clip.contains(ink):row['visibility']='partially_clipped'
            if row['visibility']=='partially_clipped' and gid>=0:
                try:row['clip_ink_evidence']=sampled_clip_ink(font,gid,matrix,clip)
                except Exception:row['clip_ink_evidence']={'all_sampled_ink_inside_clip':False,'error':'NATIVE_CLIP_MASK_UNSUPPORTED'}
            if gid<0 and primary is not None:
                row.update(continuation_of=primary['id'],logical_only=True,
                    visibility=primary['visibility'],ink_bbox=primary['ink_bbox'])
                if primary.get('clip_ink_evidence'):row['clip_ink_evidence']=primary['clip_ink_evidence']
            elif gid>=0:primary=row
            glyphs.append(row)
    covers = device.opaque_covers
    seen = {}
    for row in glyphs:
        if row['visibility'] == 'visible_candidate':
            ink = fitz.Rect(row['ink_bbox'])
            covering = [seq for seq, quad,clip in covers if seq > row['seqno'] and clip.contains(ink)
                and quad_contains(quad,ink)]
            if covering:
                row.update(visibility='occluded_by_opaque_rectangle', occluder_seqno=min(covering))
        if row['visibility'] != 'visible_candidate':
            continue
        # Two opaque identical paints at the same position are one visible
        # glyph, with both original objects explicitly accounted as aliases.
        key = (row['shape'], tuple(row['origin']), row['size'], tuple(row['clip_bbox']),
            row['paint_type'], tuple(row['color']))
        if row['shape'] and row['opacity'] == 1 and key in seen:
            row.update(visibility='opaque_paint_alias', alias_of=seen[key])
        elif row['shape'] and row['opacity'] == 1:
            seen[key] = row['id']
    images = []
    for number, item in enumerate(page.get_image_info(hashes=True, xrefs=True)):
        images.append({'id': 'image_%04d' % number, 'bbox': list(item['bbox']),
            'pixel_digest_md5': item['digest'].hex(), 'width': item['width'], 'height': item['height'],
            'transform': list(item['transform']), 'xref': item['xref'],
            'role': 'unclassified_image_content'})
    vector_paths=[]
    def path_value(value):
        if isinstance(value,(fitz.Point,fitz.Rect,fitz.Quad)):return path_value(list(value))
        if isinstance(value,(tuple,list)):return [path_value(v) for v in value]
        return value
    for drawing in page.get_drawings(extended=True):
        if drawing.get('type') not in {'f','s','fs'}:continue
        # Source curves, outline text, chart marks and structural rules need a
        # verified role. Identity or a bounding box cannot establish their
        # meaning. In particular outline text is not an empty semantic page.
        value={key:path_value(drawing.get(key)) for key in ('items','type','rect','fill','fill_opacity',
            'color','stroke_opacity','width','lineCap','lineJoin','dashes','even_odd','closePath')}
        vector_paths.append({'id':'vector_%06d'%len(vector_paths),'seqno':drawing.get('seqno'),
            'geometry_sha256':digest(value),'bbox':path_value(drawing.get('rect')),
            'native_opaque_rectangle':any(seq==drawing.get('seqno') for seq,quad,clip in device.opaque_covers),
            'role':'unclassified_vector_content','drawing':value})
    resources=[]
    native_names={font_key(g['font']) for g in glyphs}
    described_names={font_key(row[3]) for row in page.get_fonts(full=True)}
    unexplained={g['unicode'] for g in glyphs if font_key(g['font']) not in described_names
        and len(g['unicode'])==1 and g['unicode'].isprintable() and not g['unicode'].isspace() and not unreadable(g)}
    for xref,extension,kind,basefont,resource_name,encoding,*rest in page.get_fonts(full=True):
        row={'xref':xref,'basefont':basefont,'resource_name':resource_name,'referencer_xref':rest[0] if rest else 0,
            'pdf_font_type':kind,
            'native_program_name':None,'font_program_sha256':None,
            'unicode_glyph_masks':{}}
        try:
            raw=page.parent.extract_font(xref)[3]
            if raw:
                actual=fitz.Font(fontbuffer=raw)
                row.update(native_program_name=actual.name,font_program_sha256=hashlib.sha256(raw).hexdigest())
                if font_key(basefont) not in native_names and font_key(actual.name) not in native_names:
                    for char in sorted(unexplained):
                        gid=actual.has_glyph(ord(char),fallback=False)
                        if gid:
                            shape=device.outline(actual.this,gid)
                            if shape:row['unicode_glyph_masks'][char]=shape
        except Exception:pass
        resources.append(row)
    return {'version': VERSION, 'glyphs': glyphs, 'images': images,'vector_paths':vector_paths,'font_resources':resources,
        'counts': dict(Counter(row['visibility'] for row in glyphs)),
        'scope': 'Actual native glyph masks at128/256em; every raw text paint remains in the ledger. Images and vector paths are enumerated with unresolved roles. This is not a complete PDF graphics interpreter; finite rendering identity is not exact vector, mathematical or semantic equivalence.'}


def content_unicode(row):
    """Verified single-character ActualText alias, otherwise raw native Unicode.

    An ActualText label alone never replaces an unknown or different glyph.
    Both canonical masks from the actual native font must agree, no fallback.
    """
    marked=row.get('marked_actual_text')
    if (row.get('marked_text_matches_native_mask') is True and isinstance(marked,str) and len(marked)==1
        and row.get('shape') is not None and row.get('marked_text_glyph_mask_sha256')==row['shape']):return marked
    proof=row.get('writer_font_alias')
    if (isinstance(proof,dict) and isinstance(marked,str) and len(marked)==1 and proof.get('unicode')==marked
        and proof.get('native_raw_unicode')==row['unicode'] and row.get('shape') is not None
        and proof.get('actual_mask_sha256')==row['shape'] and proof.get('font_asset_unicode_mask_sha256')==row['shape']
        and re.fullmatch('[0-9a-f]{64}',str(proof.get('font_asset_sha256')))):return marked
    return row['unicode']


def unreadable(row):
    char = content_unicode(row)
    return char == '\ufffd' or (unicodedata.category(char) == 'Cc' and row['shape'] is not None)
