"""Bind BabelDOC source or final typesetting members to actual PDF paints.

Source membership uses actual source ink. Optional final typesetting membership
uses actual final font resources, emitted baselines and glyph masks. A stale
translated IR is never relabeled as the final target. Unmatched, repeated or
ambiguous members remain explicit errors; no IR supplies semantic approval.
No document names, coordinates or corrective translations are supplied here.
"""
from collections import defaultdict
import copy
import hashlib
import json
import math
import re
import struct
from pathlib import Path
import unicodedata

import pymupdf as fitz
import pdf_objects

VERSION='0.3.0-draft.1'


def font_key(name):
    return pdf_objects.font_key(name)


def chars(composition):
    if composition.get('pdf_character'):yield composition['pdf_character']
    for key in ('pdf_line','pdf_same_style_characters','pdf_formula'):
        if composition.get(key):yield from composition[key].get('pdf_character',[])


def native_float(value):return struct.unpack('f',struct.pack('f',value))[0]


def float32_step(value):
    value=abs(native_float(value))
    if value==0:return 2**-149
    return 2**(math.floor(math.log2(value))-23)


def writer_baseline(char,height):
    # CharacterRenderUnit emits decimal Tm coordinates with six places. MuPDF
    # uses single-precision affine arithmetic. This is a writer-format bound,
    # not an ink-clipping epsilon or a relaxed source geometry match.
    box=char['box'];x=box['x2'] if char.get('vertical') else box['x']
    x=native_float(float(format(x,'.6f')));y=native_float(float(format(box['y'],'.6f')))
    return x,native_float(native_float(height)-y)


def load(path,page_number,inventory,height,*,rendered_final=False,font_assets=None):
    path=Path(path)
    if path.is_symlink() or path.stat().st_size>64*1024*1024:raise ValueError('ENGINE_SOURCE_MAP_FILE_LIMIT')
    raw=path.read_bytes();data=json.loads(raw.decode('utf-8'))
    pages=[p for p in data['page'] if p['page_number']==page_number]
    if len(pages)!=1:raise ValueError('ENGINE_SOURCE_PAGE_AMBIGUOUS')
    page=pages[0];fonts={(0,f['font_id']):f['name'] for f in page['pdf_font']};font_bindings=[]
    asset_fonts={};asset_masks={};verified_aliases={}
    if font_assets is not None:
        if not rendered_final or not isinstance(font_assets,dict):raise ValueError('INVALID_TARGET_FONT_ASSETS')
        for identifier,spec in font_assets.items():
            if (not isinstance(identifier,str) or not isinstance(spec,dict) or set(spec)!={'path','sha256'}
                or not isinstance(spec['sha256'],str) or not re.fullmatch('[0-9a-f]{64}',spec['sha256'])):raise ValueError('INVALID_TARGET_FONT_ASSETS')
            file=Path(spec['path'])
            if file.is_symlink():raise ValueError('TARGET_FONT_ASSET_LINK_UNSUPPORTED')
            with file.open('rb') as stream:raw_font=stream.read(32*1024*1024+1)
            if len(raw_font)>32*1024*1024 or hashlib.sha256(raw_font).hexdigest()!=spec['sha256']:raise ValueError('TARGET_FONT_ASSET_CHANGED')
            asset_fonts[identifier]=(fitz.Font(fontbuffer=raw_font),spec['sha256'])
    mask_document=fitz.open();mask_page=mask_document.new_page(width=20,height=20)
    mask_device=pdf_objects.GlyphDevice(mask_page)
    for xobject in page.get('pdf_xobject',[]):
        for font in xobject.get('pdf_font',[]):fonts[(xobject['xobj_id'],font['font_id'])]=font['name']
    aliases={}
    for name in sorted(set(fonts.values())):
        actual=[r for r in inventory.get('font_resources',[]) if r['basefont']==name and r['native_program_name']]
        candidates={font_key(r['native_program_name']) for r in actual}
        if len(candidates)==1:
            aliases[name]=next(iter(candidates))
            font_bindings.append({'ir_pdf_basefont':name,'native_program_name':actual[0]['native_program_name'],
                'actual_font_program_sha256':sorted({r['font_program_sha256'] for r in actual}),
                'scope':'Actual same-source embedded font program name; no guessed suffix removal.'})
    visible=[g for g in inventory['glyphs'] if g['visibility'] in {'visible_candidate','partially_clipped'}]
    grid=defaultdict(list)
    for g in visible:
        point=g['origin'] if rendered_final else fitz.Rect(g['ink_bbox']).tl
        grid[(int(point[0]//16),int(point[1]//16))].append(g)
    adjustments=[];mask_bindings=[];resource_bindings={}
    def locate(char):
        box=(char.get('visual_bbox') or {}).get('box') or char['box']
        area=fitz.Rect(box['x'],height-box['y2'],box['x2'],height-box['y'])
        if area.is_empty:return [],'empty'
        scope=char.get('xobj_id',0);font_id=char['pdf_style']['font_id']
        name=fonts.get((scope,font_id),fonts.get((0,font_id)))
        if name is None and scope==0:
            # The final typesetter adds fonts after the source pdf_font list
            # was made. Resolve an exact top-level PDF resource name, never
            # infer a native font by stripping a filename extension/suffix.
            actual=[r for r in inventory.get('font_resources',[]) if r.get('resource_name')==font_id
                and r.get('referencer_xref',0)==0 and r.get('font_program_sha256')]
            names={r['basefont'] for r in actual}
            if len(names)==1 and len({r['font_program_sha256'] for r in actual})==1:
                name=next(iter(names));resource_bindings[font_id]={'ir_font_id':font_id,'actual_pdf_basefont':name,
                    'actual_font_program_sha256':sorted({r['font_program_sha256'] for r in actual}),
                    'proof':'Exact actual top-level PDF font resource name; source list need not contain final typesetter fonts.'}
        name=name or ''
        font_candidates={font_key(name)}
        if name in aliases:font_candidates.add(aliases[name])
        resources=[r for r in inventory.get('font_resources',[]) if r['basefont']==name and r.get('font_program_sha256')]
        if len({r['font_program_sha256'] for r in resources})==1:
            native_names={font_key(r['native_program_name']) for r in resources if r.get('native_program_name')}
            if len(native_names)==1:font_candidates.update(native_names)
        candidates=[];alias_candidates={}
        baseline=writer_baseline(char,height) if rendered_final else None
        search=fitz.Rect(*baseline,*baseline) if baseline else area
        if rendered_final and any(r.get('pdf_font_type')=='Type3' for r in resources):return [],'unsupported_final_type3_transform'
        for x in range(int(search.x0//16)-1,int(search.x1//16)+2):
            for y in range(int(search.y0//16)-1,int(search.y1//16)+2):
                for g in grid.get((x,y),[]):
                    expected=char.get('char_unicode','')
                    mask_proof=[r for r in resources if len(expected)==1 and expected.isprintable() and not expected.isspace()
                        and expected==pdf_objects.content_unicode(g) and g['shape']
                        and r.get('unicode_glyph_masks',{}).get(expected)==g['shape']]
                    if font_key(g['font']) not in font_candidates and not mask_proof:continue
                    ink=fitz.Rect(g['ink_bbox']);overlap=(ink&area).get_area()
                    if len(expected)==1 and expected.isprintable() and pdf_objects.content_unicode(g).isprintable() and unicodedata.normalize('NFC',expected)!=unicodedata.normalize('NFC',pdf_objects.content_unicode(g)):
                        # Subsetting can discard a cmap alias such as ASCII '-'
                        # while the PDF's ToUnicode picks the shared NB hyphen.
                        # A writer-supplied full font asset and ActualText must
                        # independently reproduce this actual glyph mask. A
                        # filename/family match or metadata label is not enough.
                        asset=asset_fonts.get(font_id) if rendered_final and scope==0 else None
                        if not asset or g.get('marked_actual_text')!=expected or g['shape'] is None or font_key(asset[0].name) not in font_candidates:continue
                        key=(font_id,expected)
                        if key not in asset_masks:
                            gid=asset[0].has_glyph(ord(expected),fallback=False)
                            asset_masks[key]=mask_device.outline(asset[0].this,gid) if gid>0 else None
                        if asset_masks[key] is None or asset_masks[key]!=g['shape']:continue
                        alias_candidates[g['id']]={'native_id':g['id'],'unicode':expected,'native_raw_unicode':g['unicode'],
                            'font_asset_id':font_id,'font_asset_sha256':asset[1],'actual_mask_sha256':g['shape'],
                            'font_asset_unicode_mask_sha256':asset_masks[key],
                            'proof':'Actual single-character ActualText plus matching128/256em masks from the writer full font and actual subset paint; no fallback.'}
                    metric_delta=max(abs(a-b) for a,b in zip(ink,area))
                    mode='native_ink_overlap'
                    if rendered_final:
                        tolerances=[4*float32_step(v) for v in baseline]
                        expected_size=native_float(float(format(char['pdf_style']['font_size'],'.6f')))
                        if (any(abs(a-b)>t for a,b,t in zip(g['origin'],baseline,tolerances))
                            or abs(g['size']-expected_size)>4*float32_step(expected_size)
                            or tuple(g.get('direction',()))!=((0.,-1.) if char.get('vertical') else (1.,0.))):continue
                        mode='exact_writer_baseline_with_float32_rounding'
                    elif overlap<.7*min(ink.get_area(),area.get_area()):
                        # BabelDOC/PDFMiner source metrics can differ slightly
                        # from native kerning, especially for narrow l/i/1.
                        # This SAME-source binding still requires actual font,
                        # exact readable Unicode and a bounded ink-box delta.
                        if (len(expected)!=1 or not expected.isprintable() or expected.isspace()
                            or expected!=pdf_objects.content_unicode(g) or metric_delta>.15*char['pdf_style']['font_size']):continue
                        mode='bounded_source_metric_delta'
                    distance=sum(abs(a-b) for a,b in zip(g['origin'],baseline)) if rendered_final else sum(abs(a-b) for a,b in zip(ink,area))
                    candidates.append((distance,g['id'],mode,metric_delta))
                    if mask_proof and font_key(g['font']) not in font_candidates:
                        mask_bindings.append({'native_id':g['id'],'source_ir_font_id':char['pdf_style']['font_id'],
                            'source_ir_basefont':name,'native_font':g['font'],'unicode':expected,'glyph_mask_sha256':g['shape'],
                            'font_program_sha256':sorted({r['font_program_sha256'] for r in mask_proof}),
                            'proof':'Same-source embedded font bytes render this exact Unicode to the same canonical native glyph mask. No font suffix guessing.'})
        candidates=sorted(set(candidates))
        if not candidates:return [],'not_found'
        selected=[identity for distance,identity,mode,delta in candidates if distance-candidates[0][0]<.001]
        by_id={g['id']:g for g in visible}
        roots={by_id[identity].get('continuation_of',identity) for identity in selected}
        if len(roots)>1:return [],'ambiguous'
        members=sorted({g['id'] for g in visible if g.get('continuation_of',g['id']) in roots})
        expected=char.get('char_unicode','')
        if expected and expected.isprintable() and not re.fullmatch(r'\(cid:\d+\)',expected):
            actual=''.join(alias_candidates[identity]['unicode'] if identity in alias_candidates else pdf_objects.content_unicode(by_id[identity]) for identity in members)
            if unicodedata.normalize('NFKC',expected)!=unicodedata.normalize('NFKC',actual):return [],'text_mismatch'
        for identity in members:
            if identity in alias_candidates:verified_aliases[identity]=alias_candidates[identity]
        for distance,identity,mode,delta in candidates:
            if identity in selected and mode=='bounded_source_metric_delta':
                adjustments.append({'native_id':identity,'max_box_delta_pt':delta,'font_size_pt':char['pdf_style']['font_size'],
                    'bound_em':.15,'proof':'Same source font and exact readable Unicode; unique nearest native ink within bound.'})
        return members,None
    paragraphs=[];formulas=[];errors=[];owner={};debug=0;paragraph_ids=set();member_sites={}
    for paragraph in page['pdf_paragraph']:
        if paragraph.get('debug_id') is None:
            debug+=1;continue
        identifier=paragraph['debug_id'];members=[]
        if not isinstance(identifier,str) or not identifier or identifier in paragraph_ids:
            errors.append({'code':'ENGINE_SOURCE_PARAGRAPH_ID_AMBIGUOUS','paragraph':identifier})
            continue
        paragraph_ids.add(identifier)
        for number,composition in enumerate(paragraph['pdf_paragraph_composition']):
            objects=[]
            for position,char in enumerate(chars(composition)):
                if char.get('debug_info'):continue
                matched,reason=locate(char)
                if matched:
                    objects.extend(matched)
                    for member in matched:
                        site=(identifier,number,position)
                        if member in member_sites and member_sites[member]!=site:
                            errors.append({'code':'ENGINE_SOURCE_MEMBER_REPEATED','glyph':member,
                                'first_site':list(member_sites[member]),'repeated_site':list(site)})
                        member_sites[member]=site
                        if member not in members:members.append(member)
                        if member in owner and owner[member]!=identifier:errors.append({'code':'ENGINE_SOURCE_MEMBER_MULTIPLE_OWNERS','glyph':member})
                        owner[member]=identifier
                elif reason!='empty' and str(char.get('char_unicode','')).strip():
                    errors.append({'code':'ENGINE_SOURCE_MEMBER_'+str(reason).upper(),'paragraph':identifier,
                        'char_unicode':char.get('char_unicode'),'box':char.get('box')})
            formula=composition.get('pdf_formula')
            if formula and objects:
                formulas.append({'id':identifier+'-f%03d'%number,'glyph_ids':objects,
                    'curve_count':len(formula.get('pdf_curve',[])),'form_count':len(formula.get('pdf_form',[]))})
        if members:paragraphs.append({'id':identifier,'glyph_ids':members,'layout_label':paragraph.get('layout_label'),
            'source_unicode_sha256':hashlib.sha256(paragraph['unicode'].encode('utf-8')).hexdigest()})
    standalone=[]
    for char in page.get('pdf_character',[]):
        if char.get('debug_info'):continue
        matched,reason=locate(char)
        standalone.extend(member for member in matched if member not in owner and member not in standalone)
    mask_document.close()
    return {'version':VERSION,'file_sha256':hashlib.sha256(raw).hexdigest(),'engine_page_number':page_number,
        'paragraphs':paragraphs,'formulas':formulas,'errors':errors,'source_debug_records':debug,
        'standalone_source_glyph_ids':standalone,
        'bounded_source_metric_adjustments':adjustments,
        'actual_source_font_bindings':font_bindings,
        'actual_resource_font_bindings':[resource_bindings[k] for k in sorted(resource_bindings)],
        'verified_target_text_aliases':[verified_aliases[k] for k in sorted(verified_aliases)],
        'actual_source_glyph_mask_font_bindings':sorted(mask_bindings,key=lambda r:(r['native_id'],r['source_ir_font_id'])),
        'matched_source_glyphs':len(owner),'binding_mode':'final_writer_baseline' if rendered_final else 'source_native_ink',
        'scope':'Existing source IR object membership only; no translated IR or target approval is imported.'}


def load_target(path,page_number,inventory,height,*,font_assets=None):
    result=load(path,page_number,inventory,height,rendered_final=True,font_assets=font_assets)
    for error in result['errors']:error['code']=error['code'].replace('ENGINE_SOURCE_','ENGINE_TARGET_',1)
    result['matched_target_glyphs']=result.pop('matched_source_glyphs')
    result['scope']='Final typesetting IR bound to actual target font resources, Unicode, six-decimal writer baselines, size and direction. Not semantic approval; stale or unsupported target records fail.'
    return result


def apply_verified_aliases(inventory,result):
    """Project full-font alias proofs while preserving native raw Unicode.

    Called only with the local load_target result. This is a verified glyph
    decoding correction, never a formula role, translation or delivery grant.
    """
    adjusted=copy.deepcopy(inventory);by_id={g['id']:g for g in adjusted['glyphs']};seen=set()
    for proof in result.get('verified_target_text_aliases',[]):
        identity=proof['native_id'];g=by_id.get(identity);expected=proof.get('unicode')
        if (g is None or identity in seen or not isinstance(expected,str) or len(expected)!=1
            or g.get('marked_actual_text')!=expected or g['unicode']!=proof.get('native_raw_unicode')
            or g.get('shape') is None or proof.get('actual_mask_sha256')!=g['shape']
            or proof.get('font_asset_unicode_mask_sha256')!=g['shape']
            or not re.fullmatch('[0-9a-f]{64}',str(proof.get('font_asset_sha256')))):
            raise ValueError('INVALID_VERIFIED_TARGET_ALIAS')
        seen.add(identity);g['writer_font_alias']=proof
    return adjusted


def projection(page,inventory,*,omit_ids=(),opaque=None,source_paragraphs=None):
    """Actual visible native paints in PDF reading blocks, optionally IL groups.

    Position/font ties only link two views of the SAME actual PDF. Cross-language
    source/target equivalence is never inferred here. Every raw native ID has an
    explicit visible, nonvisible, alias or omitted-role disposition.
    """
    opaque=opaque or {};omit=set(omit_ids);rows=inventory['glyphs'];lookup={g['id']:g for g in rows}
    active={g['id'] for g in rows if g['visibility'] in {'visible_candidate','partially_clipped'} and g['id'] not in omit}
    by_position=defaultdict(list)
    for g in rows:
        by_position[(round(g['origin'][0],2),round(g['origin'][1],2),font_key(g['font']))].append(g)
    assigned=set();groups=[];unbound=[];evidence=[];discrepancies=[]
    children=defaultdict(list)
    for g in rows:
        if g.get('continuation_of'):children[g['continuation_of']].append(g)
    expanded=[]
    def raw_characters(span):
        raw=span['chars'];value=''.join(c['c'] for c in raw);at=0
        while at<len(raw):
            match=re.match(r'\(cid:\d+\)',value[at:])
            if match:
                first=raw[at];key=(round(first['origin'][0],2),round(first['origin'][1],2),font_key(span['font']))
                candidates=[g for g in by_position.get(key,[]) if pdf_objects.unreadable(g) and g['id'] in active]
                if not candidates:candidates=[g for g in by_position.get(key,[]) if pdf_objects.unreadable(g)]
                # A CID proxy is expanded by the extractor from one native
                # glyph. Literal PDF text with those characters is not such a
                # proxy. Require a unique unknown native paint at its origin.
                if len(candidates)==1:
                    g=candidates[0];part=raw[at:at+len(match[0])]
                    if all(abs(c['origin'][1]-first['origin'][1])<.02
                        and first['origin'][0]-.02<=c['origin'][0]<=first['bbox'][2]+.02 for c in part):
                        evidence.append({'kind':'native_cid_proxy_expansion','native_ids':[g['id']],
                            'raw_proxy':match[0],'raw_origin':list(first['origin'])})
                        yield {**first,'c':pdf_objects.content_unicode(g)};at+=len(part);continue
            yield raw[at];at+=1
    for block_number,block in enumerate(page.get_text('rawdict')['blocks']):
        if block['type']!=0:continue
        pieces=[];ids=[]
        for line in block['lines']:
            line_parts=[]
            for span in line['spans']:
                for char in raw_characters(span):
                    key=(round(char['origin'][0],2),round(char['origin'][1],2),font_key(span['font']))
                    candidates=by_position.get(key,[])
                    # MuPDF rawdict advances a ligature's logical continuation
                    # to the next glyph origin. The native paint has one glyph
                    # and several logical codepoints. Bind that expansion
                    # explicitly, before looking up the next independent paint.
                    logical=[item for item in expanded if not item['consumed'] and item['unicode']==char['c']
                        and item['font']==key[2] and abs(item['baseline']-char['origin'][1])<.02
                        and item['x0']-.02<=char['origin'][0]<=item['x1']+.02]
                    if len(logical)==1:
                        logical[0]['consumed']=True
                        evidence.append({'kind':'ligature_logical_expansion','native_ids':logical[0]['ids'],
                            'raw_unicode':char['c'],'raw_origin':list(char['origin'])})
                        continue
                    if len(logical)>1:
                        unbound.append({'code':'AMBIGUOUS_LIGATURE_EXPANSION','block':block_number,'text':char['c']})
                        continue
                    chosen=[g for g in candidates if g['id'] in active and g['id'] not in assigned]
                    if not chosen:
                        if char['c'].isspace():line_parts.append((' ',[]))
                        elif not candidates:unbound.append({'block':block_number,'text':char['c'],'origin':list(char['origin'])})
                        continue
                    exact=[g for g in chosen if unicodedata.normalize('NFC',pdf_objects.content_unicode(g))==unicodedata.normalize('NFC',char['c'])]
                    if exact:chosen=exact
                    elif len(chosen)==1:
                        # This is a second view of the SAME PDF paint, at its
                        # exact origin and font, not cross-language text repair.
                        # Preserve native Unicode, even where rawdict normalizes
                        # a compatibility character or a nonbreaking hyphen.
                        discrepancies.append({'code':'RAWDICT_NORMALIZED_NATIVE_UNICODE','block':block_number,
                            'raw_unicode':char['c'],'native_unicode':chosen[0]['unicode'],'native_id':chosen[0]['id']})
                    elif len(chosen)>1:
                        unbound.append({'code':'AMBIGUOUS_NATIVE_ORIGIN','block':block_number,'text':char['c'],
                            'glyph_ids':[g['id'] for g in chosen]})
                        continue
                    bundle=[]
                    for g in chosen:
                        if g.get('continuation_of'):continue
                        bundle.append(g)
                        continuation=[c for c in children.get(g['id'],[]) if c['id'] in active and c['id'] not in assigned]
                        bundle.extend(continuation)
                        for c in continuation:
                            expanded.append({'unicode':c['unicode'],'ids':[g['id'],c['id']],'font':font_key(g['font']),
                                'baseline':g['origin'][1],'x0':g['origin'][0],'x1':g['bbox'][2], 'consumed':False})
                    chosen=bundle
                    # Ligature continuations and invalid-CMap glyphs retain
                    # their native IDs; source-proven opaque tokens replace text.
                    chosen_ids=[g['id'] for g in chosen]
                    evidence.append({'kind':'visible_native_paint','native_ids':chosen_ids,'raw_unicode':char['c'],'raw_origin':list(char['origin'])})
                    for gid in chosen_ids:assigned.add(gid);ids.append(gid)
                    tokens=[]
                    for g in chosen:
                        value=opaque.get(g['id'],pdf_objects.content_unicode(g))
                        if not tokens or tokens[-1]!=value or not value.startswith('[opaque:'):tokens.append(value)
                    line_parts.append((''.join(tokens),chosen_ids))
            if any(part_ids for _,part_ids in line_parts):pieces.extend(line_parts+[('\n',[])])
        if ids:groups.append({'id':'block_%d'%block_number,'pieces':pieces,'glyph_ids':ids})
    # Native paints omitted by text extraction still become explicit units.
    for gid in sorted(active-assigned):
        g=lookup[gid];groups.append({'id':'native_'+gid,'pieces':[(opaque.get(gid,pdf_objects.content_unicode(g)),[gid])],'glyph_ids':[gid]})
        assigned.add(gid)
    if source_paragraphs:
        owner={gid:p['id'] for p in source_paragraphs for gid in p['glyph_ids'] if gid in active}
        merged={};order=[]
        for group in groups:
            last=None
            for text,part_ids in group['pieces']:
                keys={owner.get(gid,'pdf_'+group['id']) for gid in part_ids}
                if not keys:
                    if last is not None:merged[last]['pieces'].append((text,[]))
                    continue
                if len(keys)!=1:
                    unbound.append({'code':'ENGINE_PROJECTION_MULTIPLE_OWNERS','glyph_ids':part_ids});continue
                key=next(iter(keys));last=key
                if key not in merged:
                    order.append(key);merged[key]={'id':'engine_'+key,'pieces':[],'glyph_ids':[]}
                merged[key]['pieces'].append((text,part_ids));merged[key]['glyph_ids'].extend(part_ids)
        groups=[merged[key] for key in order]
    for group in groups:
        boxes=[fitz.Rect(lookup[g]['ink_bbox']) for g in group['glyph_ids']]
        box=fitz.Rect(boxes[0])
        for other in boxes[1:]:box|=other
        pieces=group.pop('pieces');group['reading_segments']=[{'text':text,'glyph_ids':part_ids} for text,part_ids in pieces]
        group['bbox']=list(box);group['text']=''.join(text for text,_ in pieces).strip()
    return groups,{'raw_native_glyphs':len(rows),'visible_ids':len(active),'assigned_visible_ids':len(assigned),
        'omitted_role_ids':len(omit),'nonvisible_and_alias_ids':len(rows)-len(active)-len(omit),
        'coverage_complete':active==assigned,'unbound_extraction':unbound,
        'raw_native_discrepancies':discrepancies,
        'raw_projection_evidence':evidence,'unconsumed_ligature_expansions':[row for row in expanded if not row['consumed']]}
