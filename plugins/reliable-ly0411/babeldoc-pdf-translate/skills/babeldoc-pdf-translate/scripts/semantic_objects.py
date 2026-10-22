"""Native text accounting and explicit graphics blockers for semantic review.

Source IR supplies source object membership, never a guessed final translation.
Geometry only proposes complete text review pairs. Every native text paint has
an explicit disposition; images and vector paths remain unresolved blockers.
Semantic truth, raster transcription and 2D formula fidelity are not certified.
"""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata

import pymupdf as fitz
import engine_source_map as engine
import pdf_objects as objects
import prose_completeness
import clipping_relations

VERSION='0.3.0-draft.1'
CONTEXT_VERSION='0.1.0-draft.1'
ACTIVE={'visible_candidate','partially_clipped'}
RETAINED_ROLES={'author_names','affiliations','references','publisher','copyright','license','source_urls','doi','original_english_scope'}
MATH_FONT=re.compile(r'CMMI|CMSY|CMEX|MSAM|MSBM|STIX.*Math|MathJax|Symbol',re.I)
MATH_INVENTORY_FONT=re.compile(r'CMR|CMMI|CMSY|CMEX|MSAM|MSBM|STIX.*Math|MathJax|Symbol',re.I)
POSSIBLE_MATH_FONT=re.compile(r'^(?:CM|MSAM|MSBM|STIX|Math|Symbol)',re.I)
CALL=re.compile(r'(?<![A-Za-z])[A-Za-z]{1,4}\([^\n()]{1,50}\)')
NUMBER=re.compile(r'[+-]?\s*(?:\d+(?:[.,]\d+)*|\.\d+)(?:[eE][+-]?\d+)?')
IDENTIFIER=re.compile(r'(?<![A-Za-z0-9])[A-Za-z][A-Za-z0-9_.]*(?:[-\u2010\u2011][A-Za-z0-9_.]+)+')


def digest(value):return objects.digest(value)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def compact(value):return ''.join(unicodedata.normalize('NFC',value).split())


def date_facts(text):
    import date_literals
    return date_literals.extract(text)


def identifier_hyphens(text):
    # Keep every sign. Only Unicode typographic hyphens within an alphanumeric
    # identifier are rendered as the ASCII hyphen used by the numeric lexer.
    # Mathematical minus, en dash, plus and free-standing signs are untouched.
    def replace(match):
        value=match[0]
        return value.replace('\u2010','-').replace('\u2011','-') if re.search(r'\d',value) else value
    return IDENTIFIER.sub(replace,text)


def retained_text(text):return compact(identifier_hyphens(text))


def preservation_grants(quote):
    """Closed, affirmative original-English grant grammar; unsupported fails.

    A controller-supplied role is still trusted classification input. Merely
    quoting arbitrary prompt text (including a command to translate) is never
    authorization to leave a paragraph untranslated.
    """
    match=re.fullmatch(r'\s*(?:Preserve|Keep|Retain)\s+(.+?)\s+in\s+(?:their\s+)?(?:original\s+)?English[.!]?\s*',quote,re.I)
    if not match:return set()
    phrases={'authors':'author_names','their names':'author_names','author names':'author_names',
        'affiliations':'affiliations','reference entries':'references','references':'references',
        'source urls':'source_urls','urls':'source_urls','doi':'doi','copyright':'copyright',
        'copyright statements':'copyright','license statements':'license','licenses':'license','publisher statements':'publisher'}
    result=set()
    for piece in re.split(r',\s*|\s+and\s+',match[1].lower()):
        piece=re.sub(r'^all\s+','',piece.strip())
        if piece not in phrases:return set()
        result.add(phrases[piece])
    return result


def protected(group,inventory,formula_members=()):
    by_id={g['id']:g for g in inventory['glyphs']};tokens=[];formula=set(formula_members)
    for gid in group['glyph_ids']:
        g=by_id[gid];char=objects.content_unicode(g);category=unicodedata.category(char)
        if objects.unreadable(g):tokens.append('opaque:'+str(g['shape']))
        # The inventory is symmetric on source and actual target. Source-only
        # IR role membership must not add tokens on just one side. CMR remains
        # conservative here; it is no longer excluded from the prose screen.
        elif char.strip() and (MATH_INVENTORY_FONT.search(g['font']) or category in {'Sm','No','Nl'} or 'GREEK' in unicodedata.name(char,'')):
            tokens.append('math:'+unicodedata.normalize('NFC',char))
    dates,text=date_facts(unicodedata.normalize('NFC',group['text']))
    tokens.extend('date:'+date for date in dates)
    tokens.extend('number:'+compact(match[0]) for match in NUMBER.finditer(identifier_hyphens(text)))
    tokens.extend('call:'+compact(token) for token in CALL.findall(text))
    return dict(Counter(tokens))


def validate_context(context,source,mono,pages,contract):
    if context is None:return {},None
    if (not isinstance(context,dict) or set(context)!={'version','source_sha256','target_sha256','pages'}
        or context['version']!=CONTEXT_VERSION or context['source_sha256']!=sha(source)
        or context['target_sha256']!=sha(mono) or not isinstance(context['pages'],list)):
        raise ValueError('SEMANTIC_MAPPING_CONTEXT_BINDING_CHANGED')
    result={};canonical=[]
    for entry in context['pages']:
        if (not isinstance(entry,dict) or set(entry)-{'page','engine_source','engine_target','retained_source_roles'}
            or type(entry.get('page')) is not int or entry['page'] not in pages or entry['page'] in result):
            raise ValueError('INVALID_SEMANTIC_MAPPING_CONTEXT_PAGE')
        copy=json.loads(json.dumps(entry))
        for side in ('source','target'):
            ir=copy.get('engine_'+side)
            if ir is None:continue
            allowed={'path','sha256','engine_page'}|({'font_assets'} if side=='target' else set())
            if (not isinstance(ir,dict) or set(ir)-allowed or not {'path','sha256','engine_page'}<=set(ir)
                or type(ir['engine_page']) is not int or ir['engine_page']<0
                or sha(ir['path'])!=ir['sha256']):raise ValueError('ENGINE_'+side.upper()+'_ARTIFACT_CHANGED')
            ir.pop('path')
            if 'font_assets' in ir:
                if not isinstance(ir['font_assets'],dict):raise ValueError('INVALID_TARGET_FONT_ASSETS')
                for identifier,asset in ir['font_assets'].items():
                    if (not isinstance(identifier,str) or not isinstance(asset,dict)
                        or set(asset)!={'path','sha256'} or not re.fullmatch('[0-9a-f]{64}',str(asset['sha256']))
                        or sha(asset['path'])!=asset['sha256']):raise ValueError('TARGET_FONT_ASSET_CHANGED')
                    asset.pop('path')
        roles=entry.get('retained_source_roles',[])
        if not isinstance(roles,list):raise ValueError('INVALID_RETAINED_SOURCE_ROLES')
        seen=set()
        for role in roles:
            if (not isinstance(role,dict) or set(role)!={'role','contract_quote','source_glyph_ids'}
                or role['role'] not in RETAINED_ROLES or not isinstance(role['contract_quote'],str)
                or len(role['contract_quote'].strip())<12 or contract is None
                or role['contract_quote'] not in contract.get('prompt','')
                or not isinstance(role['source_glyph_ids'],list) or not role['source_glyph_ids']
                or any(not isinstance(g,str) for g in role['source_glyph_ids'])
                or len(set(role['source_glyph_ids']))!=len(role['source_glyph_ids'])
                or seen.intersection(role['source_glyph_ids'])):raise ValueError('RETAINED_ROLE_REQUIRES_ORIGINAL_CONTRACT')
            grants=preservation_grants(role['contract_quote'])
            sentences=[s.strip() for s in re.split(r'(?<=[.!?])\s+|[\r\n]+',contract.get('prompt',''))]
            if (role['contract_quote'].strip() not in sentences or not grants
                or (role['role']!='original_english_scope' and role['role'] not in grants)):
                raise ValueError('RETAINED_ROLE_NOT_AUTHORIZED_BY_CONTRACT')
            seen.update(role['source_glyph_ids'])
        result[entry['page']]=entry;canonical.append(copy)
    return result,digest({'version':context['version'],'source_sha256':context['source_sha256'],
        'target_sha256':context['target_sha256'],'pages':canonical})


def same_paint(g):
    return (g['shape'],unicodedata.normalize('NFC',objects.content_unicode(g)),round(g['size'],4),
        tuple(round(v,3) for v in g['origin']),g['paint_type'],tuple(g['color']),g['opacity'])


def retained_roles(left,right,entries,original,target):
    """Verify actual unchanged glyphs under an explicit original role contract.

    IDs select objects only. Acceptance needs actual font masks, Unicode, size,
    position and paint attributes; an English region is never inferred a role.
    """
    source={g['id']:g for g in left['glyphs'] if g['visibility'] in ACTIVE}
    candidates=defaultdict(list)
    for g in right['glyphs']:
        if g['visibility'] in ACTIVE:candidates[same_paint(g)].append(g['id'])
    source_ids=set();target_ids=set();proof=[];errors=[]
    for entry in entries:
        pairs=[];pending_targets=set();failed=[]
        for gid in entry['source_glyph_ids']:
            if gid not in source or gid in source_ids:raise ValueError('RETAINED_SOURCE_MEMBER_INVALID')
            available=[t for t in candidates.get(same_paint(source[gid]),[]) if t not in target_ids|pending_targets]
            if len(available)!=1:failed.append(gid);continue
            pending_targets.add(available[0]);pairs.append([gid,available[0]])
        if failed:
            # The original instruction preserves English content; it may be
            # re-typeset. An explicit whole native group can alternatively be
            # bound to a unique complete target group with identical ordered
            # readable content. Never infer the role from unchanged English.
            source_groups,_=engine.projection(original,left);target_groups,_=engine.projection(target,right)
            requested=set(entry['source_glyph_ids']);sg=[g for g in source_groups if set(g['glyph_ids'])<=requested]
            covered={gid for g in sg for gid in g['glyph_ids']};content_pairs=[];selected=set()
            readable=all(not objects.unreadable(source[g]) for g in requested)
            if covered==requested and readable:
                available=[g for g in target_groups if not set(g['glyph_ids'])&target_ids
                    and any((fitz.Rect(g['bbox'])&fitz.Rect(s['bbox'])).get_area()>0 for s in sg)]
                complete=True;covered_source=set()
                for component in pair_groups(sg,available):
                    sources=[g for side,g in component if side=='source'];targets=[g for side,g in component if side=='target']
                    if not sources:continue
                    source_text=retained_text(''.join(g['text'] for g in sources));target_text=retained_text(''.join(g['text'] for g in targets))
                    if not targets or source_text!=target_text:complete=False;break
                    gids_a=[gid for g in sources for gid in g['glyph_ids']];gids_b=[gid for g in targets for gid in g['glyph_ids']]
                    if any(objects.unreadable(g) for g in right['glyphs'] if g['id'] in set(gids_b)):complete=False;break
                    selected.update(gids_b);covered_source.update(gids_a)
                    content_pairs.append({'source_groups':[g['id'] for g in sources],'target_groups':[g['id'] for g in targets],
                        'source_glyph_ids':gids_a,'target_glyph_ids':gids_b,
                        'canonical_content_sha256':hashlib.sha256(source_text.encode()).hexdigest()})
                if complete and covered_source==requested:
                    source_ids.update(requested);target_ids.update(selected)
                    proof.append({'role':entry['role'],'contract_quote':entry['contract_quote'],
                        'content_identity_groups':content_pairs,'proof':'Explicit original English scope; complete, ordered actual native Unicode identity. Whitespace and typed identifier hyphens normalized; unknown glyphs forbidden. Font/layout may differ.'})
                    continue
            errors.append({'code':'RETAINED_SOURCE_CONTENT_NOT_IDENTICAL','role':entry['role'],
                'source_glyph_ids':failed,'candidate_member_count':len(entry['source_glyph_ids'])});continue
        target_ids.update(pending_targets);source_ids.update(entry['source_glyph_ids'])
        proof.append({'role':entry['role'],'contract_quote':entry['contract_quote'],'identical_native_pairs':pairs,
            'proof':'Actual same-position canonical glyph masks, native Unicode and paint attributes; not semantic approval.'})
    return source_ids,target_ids,proof,errors


def prose_text(group,inventory,formula_members=()):
    members=set(formula_members);by_id={g['id']:g for g in inventory['glyphs']}
    def plain(gid):return gid not in members and not MATH_FONT.search(by_id[gid]['font']) and not objects.unreadable(by_id[gid])
    return ''.join(piece['text'] if not piece['glyph_ids'] or any(plain(gid) for gid in piece['glyph_ids']) else ' '
        for piece in group['reading_segments'])


def formula_role_candidate(groups,inventory,text_a,text_b):
    """Identify an unresolved source role, never approve unchanged English.

    Roman math fonts also carry ordinary prose. Even an identical expression
    remains blocked unless its source formula membership is established.
    """
    if compact(text_a)!=compact(text_b) or not re.search(r'[=≜≔∑∫≤≥]',text_a):return False
    if re.search(r'\b(?:the|this|is|are|was|were|with|if|when|for|from|which|that|implies|denotes|ensures)\b',text_a,re.I):return False
    lookup={g['id']:g for g in inventory['glyphs']}
    letters=[lookup[gid] for group in groups for gid in group['glyph_ids'] if re.search('[A-Za-z]',lookup[gid]['unicode'])]
    printed_tag=bool(re.search(r'\(\d{1,3}[a-z]?\)',text_a))
    greek=any('GREEK' in unicodedata.name(c,'') for c in text_a)
    return bool(letters) and (all(POSSIBLE_MATH_FONT.search(g['font']) for g in letters) or printed_tag or greek)


def pair_groups(left,right):
    nodes=[('source',row) for row in left]+[('target',row) for row in right]
    links={i:set() for i in range(len(nodes))}
    for i,a in enumerate(left):
        for j,b in enumerate(right,len(left)):
            if (fitz.Rect(a['bbox'])&fitz.Rect(b['bbox'])).get_area()>0:links[i].add(j);links[j].add(i)
    seen=set();components=[]
    for index in range(len(nodes)):
        if index in seen:continue
        pending=[index];component=[]
        while pending:
            at=pending.pop()
            if at in seen:continue
            seen.add(at);component.append(at);pending.extend(links[at]-seen)
        components.append(component)
    return [[nodes[i] for i in sorted(component)] for component in components]


def pair_engine_groups(left,right,source_ir,target_ir):
    """Propose complete paragraph pairs from two actually bound engine views.

    A shared debug identifier is a controller-supplied correspondence, never a
    semantic/formula verdict. Unowned native paints retain geometric review
    groups; no suffix, text similarity or page-coordinate heuristic invents
    an engine identifier. Each group is consumed once and remains complete.
    """
    if source_ir is None or target_ir is None:return pair_groups(left,right)
    source_ids={p['id'] for p in source_ir['paragraphs']}
    target_ids={p['id'] for p in target_ir['paragraphs']}
    ids=source_ids&target_ids
    a={row['id'][7:]:row for row in left if row['id'].startswith('engine_') and row['id'][7:] in ids}
    b={row['id'][7:]:row for row in right if row['id'].startswith('engine_') and row['id'][7:] in ids}
    common=sorted(a.keys()&b.keys());taken_a={a[k]['id'] for k in common};taken_b={b[k]['id'] for k in common}
    paired=[[('source',a[k]),('target',b[k])] for k in common]
    return paired+pair_groups([r for r in left if r['id'] not in taken_a],[r for r in right if r['id'] not in taken_b])


def page_units(original,target,number,*,chinese=True,max_characters=1200,context=None):
    context=context or {};left=objects.inventory(original);right=objects.inventory(target);errors=[]
    ir=None;target_ir=None
    if context.get('engine_source'):
        spec=context['engine_source'];ir=engine.load(spec['path'],spec['engine_page'],left,original.rect.height)
        errors.extend(ir['errors'])
    if context.get('engine_target'):
        spec=context['engine_target'];target_ir=engine.load_target(spec['path'],spec['engine_page'],right,target.rect.height,
            font_assets=spec.get('font_assets'))
        errors.extend(target_ir['errors'])
        right=engine.apply_verified_aliases(right,target_ir)
    omit_a,omit_b,role_proof,role_errors=retained_roles(left,right,context.get('retained_source_roles',[]),original,target)
    errors.extend(role_errors)
    shapes=sorted({g['shape'] for v in (left,right) for g in v['glyphs'] if objects.unreadable(g) and g['shape']})
    tokens={shape:'[g%02d]'%(i+1) for i,shape in enumerate(shapes)}
    opaque={g['id']:tokens.get(g['shape'],'[unknown]') for g in left['glyphs'] if objects.unreadable(g)}
    opaque_b={g['id']:tokens.get(g['shape'],'[unknown]') for g in right['glyphs'] if objects.unreadable(g)}
    a,projection_a=engine.projection(original,left,omit_ids=omit_a,opaque=opaque,
        source_paragraphs=ir['paragraphs'] if ir else None)
    b,projection_b=engine.projection(target,right,omit_ids=omit_b,opaque=opaque_b,
        source_paragraphs=target_ir['paragraphs'] if target_ir else None)
    for side,inventory,projection in [('source',left,projection_a),('target',right,projection_b)]:
        missing=[g['id'] for g in inventory['glyphs'] if g['visibility'] in ACTIVE and not g.get('logical_only')
            and not g['unicode'].isspace() and g['shape'] is None]
        if missing:errors.append({'code':'NATIVE_GLYPH_MASK_UNAVAILABLE','side':side,'glyph_ids':missing})
        if projection['unbound_extraction']:errors.append({'code':'NATIVE_READING_ORDER_AMBIGUOUS','side':side,
            'count':len(projection['unbound_extraction'])})
        if any(g['clip_uncertain'] or g['group_uncertain'] for g in inventory['glyphs'] if g['visibility'] in ACTIVE):
            errors.append({'code':'UNSUPPORTED_NATIVE_VISIBILITY','side':side})
        clipped=[g['id'] for g in inventory['glyphs'] if g['visibility']=='partially_clipped'
            and not g.get('clip_ink_evidence',{}).get('all_sampled_ink_inside_clip')]
        if clipped:errors.append({'code':'PARTIALLY_CLIPPED_NATIVE_INK','side':side,'glyph_ids':clipped})
        if any(g['visibility']=='opaque_paint_alias' for g in inventory['glyphs']):
            errors.append({'code':'DUPLICATE_TEXT_BLOCK','side':side})
        for image in inventory['images']:
            errors.append({'code':'RASTER_TEXT_REQUIRES_TRANSCRIPTION','side':side,'image_id':image['id'],
                'pixel_digest_md5':image['pixel_digest_md5']})
    formulas=[gid for row in (ir['formulas'] if ir else []) for gid in row['glyph_ids']]
    for group in a:group['protected']=protected(group,left,formulas)
    target_formulas=[gid for row in (target_ir['formulas'] if target_ir else []) for gid in row['glyph_ids']]
    for group in b:group['protected']=protected(group,right,target_formulas)
    if any(re.search(r'\(cid:\d+\)',group['text']) for group in [*a,*b]):errors.append({'code':'UNREADABLE_GLYPH','page':number})
    units=[];unpaired=[];unverified_formula_roles=[]
    for component in pair_engine_groups(a,b,ir,target_ir):
        sa=[row for side,row in component if side=='source'];sb=[row for side,row in component if side=='target']
        if not sa or not sb:
            unpaired.append({'code':'UNMAPPED_SOURCE_OR_TARGET_BLOCK','page':number,
                'side':'source' if sa else 'target','blocks':sa or sb});continue
        text_a='\n'.join(row['text'] for row in sa);text_b='\n'.join(row['text'] for row in sb)
        math_a=Counter();math_b=Counter()
        for row in sa:math_a.update(row['protected'])
        for row in sb:math_b.update(row['protected'])
        if math_a!=math_b:errors.append({'code':'PROTECTED_MATH_GLYPH_INVENTORY_CHANGED','page':number,
            'source_blocks':[r['id'] for r in sa],'target_blocks':[r['id'] for r in sb],
            'source_only':dict(math_a-math_b),'target_only':dict(math_b-math_a)})
        if max(len(text_a),len(text_b))>max_characters:errors.append({'code':'COMPLETE_UNIT_TOO_LARGE','page':number,
            'source_characters':len(text_a),'target_characters':len(text_b)})
        plain_a=' '.join(prose_text(row,left,formulas) for row in sa);plain_b=' '.join(prose_text(row,right,target_formulas) for row in sb)
        kind='semantic' if re.search(r'[A-Za-z]{3,}|[\u3400-\u9fff]{2,}',plain_a+plain_b) else 'protected_identity'
        exact_english=(compact(plain_a)==compact(plain_b) and not re.search(r'[\u3400-\u9fff]',plain_b)
            and len(re.findall('[A-Za-z]+',text_b))>=5)
        if chinese and kind=='semantic' and (exact_english or any(prose_completeness.unchanged_english(plain_a,prose_text(row,right)) for row in sb)):
            candidate=formula_role_candidate(sa,left,text_a,text_b)
            code='SOURCE_FORMULA_ROLE_UNVERIFIED' if candidate else 'UNCHANGED_ENGLISH_PROSE'
            errors.append({'code':code,'page':number,'source_blocks':[r['id'] for r in sa]})
            if candidate:unverified_formula_roles.append({'source_blocks':[r['id'] for r in sa],
                'source_glyph_ids':[gid for r in sa for gid in r['glyph_ids']],
                'target_glyph_ids':[gid for r in sb for gid in r['glyph_ids']],
                'status':'Source formula IR/verified lineage required; identical text is insufficient for a role waiver.'})
        if kind=='protected_identity' and compact(text_a)!=compact(text_b):errors.append({'code':'NONPROSE_IDENTITY_UNPROVEN','page':number})
        units.append({'id':'p%03d-u%03d'%(number,len(units)+1),'page':number,'kind':kind,'source':text_a,'target':text_b,
            'source_blocks':sa,'target_blocks':sb,'mapping_basis':
                'Complete native paints bound to both engine paragraph identifiers; controller correspondence candidate only.'
                if ir and target_ir and len(sa)==len(sb)==1 and sa[0]['id']==sb[0]['id'] and sa[0]['id'].startswith('engine_')
                else 'Complete native reading groups with overlapping actual ink bounds; correspondence candidate only.'})
    errors.extend(unpaired)
    raw_a=Counter(gid for u in units for row in u['source_blocks'] for gid in row['glyph_ids'])
    raw_b=Counter(gid for u in units for row in u['target_blocks'] for gid in row['glyph_ids'])
    expected_a={g['id'] for g in left['glyphs'] if g['visibility'] in ACTIVE}-omit_a
    expected_b={g['id'] for g in right['glyphs'] if g['visibility'] in ACTIVE}-omit_b
    paired=(set(raw_a)==expected_a and set(raw_b)==expected_b and all(n==1 for n in [*raw_a.values(),*raw_b.values()]))
    accounting=projection_a['coverage_complete'] and projection_b['coverage_complete']
    text_complete=not errors and paired
    for side,inventory in [('source',left),('target',right)]:
        if inventory.get('vector_paths'):errors.append({'code':'UNCLASSIFIED_VECTOR_CONTENT','side':side,
            'count':len(inventory['vector_paths']),'vector_ids':[r['id'] for r in inventory['vector_paths']]})
    nonempty=any(g['visibility'] in ACTIVE for inv in (left,right) for g in inv['glyphs']) or left['images'] or right['images'] or left.get('vector_paths') or right.get('vector_paths')
    if nonempty and not units and not role_proof:errors.append({'code':'NONEMPTY_PAGE_WITHOUT_SEMANTIC_DISPOSITION','page':number})
    return {'page':number,'source_block_count':len(a),'target_block_count':len(b),'units':units,'errors':errors,
        'text_mapping_complete':text_complete,'coverage_complete':not errors and paired,'native_accounting_complete':accounting,
        'paired_visible_coverage_complete':paired,'retained_role_proof':role_proof,
        'engine_source':ir,'engine_target':target_ir,'source_projection':projection_a,'target_projection':projection_b,
        'opaque_native_glyph_tokens':{token:shape for shape,token in tokens.items()},
        'unverified_source_formula_roles':unverified_formula_roles,
        'clipping_relations':clipping_relations.describe(left,right),
        'source_native_ledger':left,'target_native_ledger':right,
        'image_accounting':{'source':left['images'],'target':right['images'],'semantic_transcription_verified':False}}


def build(source,mono,pages,*,chinese=True,context=None,translation_contract=None):
    if not isinstance(pages,list) or not pages or pages!=sorted(set(pages)):raise ValueError('INVALID_SEMANTIC_SCOPE')
    contexts,context_hash=validate_context(context,source,mono,pages,translation_contract)
    result=[];before=[sha(source),sha(mono)]
    with fitz.open(source) as original,fitz.open(mono) as translated:
        if len(original)!=len(translated):raise ValueError('SEMANTIC_PAGE_COUNT_CHANGED')
        for number in pages:
            if type(number) is not int or not 1<=number<=len(original):raise ValueError('INVALID_SEMANTIC_PAGE')
            result.append(page_units(original[number-1],translated[number-1],number,chinese=chinese,context=contexts.get(number)))
    if before!=[sha(source),sha(mono)]:raise ValueError('SEMANTIC_MAPPING_INPUT_CHANGED')
    value={'version':VERSION,'translated_pages':pages,'pages':result,'mapping_context_sha256':context_hash,
        'source_sha256':before[0],'target_sha256':before[1],
        'text_mapping_complete':all(row['text_mapping_complete'] for row in result),
        'coverage_complete':all(row['coverage_complete'] for row in result),
        'native_accounting_complete':all(row['native_accounting_complete'] for row in result),
        'scope':'Every native text paint has an explicit disposition. Images and vector paths are enumerated; unclassified graphics, empty semantic disposition on a nonempty page, unknown masks, uncertain correspondence and oversized complete paragraphs block coverage. Native accounting means text accounting, not complete graphics or semantic certification. Source IR is used when supplied; the actual target PDF supplies target data. Geometry proposes review units, not semantic or mathematical approval.'}
    value['sha256']=digest(value);return value
