"""Rebuild original engine paragraphs from verified native prose gaps.

No model calls, cache writes, coordinates or math transcriptions occur here.
Only complete, unique native prose groups can be linked. The caller must screen
meaning, bind the normal correction receipt, rerender and review the actual PDF.
Unsupported/ambiguous links are explicit decisions, never guessed replacements.
"""
from collections import Counter
import hashlib
import re
import unicodedata
import chat_bridge as bridge
import source_repair as source
import semantic_review as semantic

VERSION=1


def flatten(template):
    text=[];positions=[];cursor=0;markers=[]
    def plain(start,stop):
        for at in range(start,stop):
            for char in unicodedata.normalize('NFKC',template[at]):
                if not char.isspace():text.append(char);positions.append(at)
    for match in bridge.MARKER.finditer(template):
        plain(cursor,match.start());markers.append((match.start(),match.end()))
        if not match.group().startswith(('<style','</style')):
            text.append('\ufffc');positions.append(None)
        cursor=match.end()
    plain(cursor,len(template))
    return ''.join(text),positions,markers


def canonical(text):
    return ''.join(c for c in unicodedata.normalize('NFKC',text) if not c.isspace())


def rebuild(template,units,translations):
    if not isinstance(template,str) or not 1<=len(template)<=16000:raise ValueError('GAP_TEMPLATE_LIMIT')
    if not units or len(units)>96 or any(u.get('fidelity_scope')!='source_gap_v2' for u in units):
        raise ValueError('GAP_NATIVE_OWNERSHIP_REQUIRED')
    if len({u.get('paragraph') for u in units})!=1:raise ValueError('GAP_ONE_SOURCE_PARAGRAPH_REQUIRED')
    if not source.validate_paragraphs(units,translations):raise ValueError('GAP_TRANSLATION_FIDELITY')
    flat,positions,markers=flatten(template);used=set();matches=[]
    for index,(unit,replacement) in enumerate(zip(units,translations)):
        needle=canonical(unit['source'])
        if not needle or '\ufffc' in needle:raise ValueError('GAP_EMPTY_OR_OPAQUE_SOURCE')
        starts=[m.start() for m in re.finditer('(?='+re.escape(needle)+')',flat)]
        if len(starts)!=1:raise ValueError('GAP_PROSE_LINK_NOT_UNIQUE')
        start=starts[0];end=start+len(needle);selected=set(range(start,end))
        if used&selected or any(positions[n] is None for n in selected):raise ValueError('GAP_PROSE_LINK_OVERLAP')
        used|=selected;matches.append((positions[start],positions[end-1]+1,replacement,index))
    # Every remaining alphabetic source object must be supported by actual
    # native immutable context. Single-letter math bases may have scripts inside
    # {vN}; do not invent or decode the placeholder's contents.
    remaining=''.join(' ' if n in used else char for n,char in enumerate(flat))
    literals=' '.join(u.get('left_literal','')+' '+u.get('right_literal','') for u in units)
    allowed=Counter(re.findall(r'[A-Za-z]+',literals))
    for word,count in Counter(re.findall(r'[A-Za-z]+',remaining)).items():
        capacity=allowed[word] if len(word)>1 else sum(v for k,v in allowed.items() if k.startswith(word))
        if count>capacity:raise ValueError('GAP_UNACCOUNTED_SOURCE_PROSE')
    # Group order is native source order; engine order must agree. Never make a
    # successful marker-count check stand in for this ownership relationship.
    if [r[3] for r in sorted(matches)]!=list(range(len(units))):raise ValueError('GAP_SOURCE_ORDER_CHANGED')
    protected={n for start,stop in markers for n in range(start,stop)}
    remove=set();insert={}
    for start,stop,replacement,index in matches:
        insert[start]=replacement
        remove.update(n for n in range(start,stop) if n not in protected)
    target=''.join(insert.get(n,'')+('' if n in remove else char) for n,char in enumerate(template))
    if bridge.MARKER.findall(target)!=bridge.MARKER.findall(template):raise ValueError('GAP_MARKERS_CHANGED')
    semantic.checked_replacements({'replacements':{'pair_0':target}},{'pair_0':{'source':template,'target':template}})
    return target,{'version':VERSION,'native_paragraph':units[0].get('paragraph'),
        'slots':len(units),'source_sha256':hashlib.sha256(template.encode()).hexdigest(),
        'output_sha256':hashlib.sha256(target.encode()).hexdigest(),
        'all_native_prose_gaps_linked':True,'all_markers_preserved_in_order':True,
        'scope':'Original engine template with native prose ownership; geometry and math rendering still need actual PDF review.'}


def propose(pairs,units,translations,limit=8):
    semantic.checked_collection(pairs)
    if type(limit) is not int or not 1<=limit<=8:raise ValueError('GAP_ROW_LIMIT')
    if not source.validate_paragraphs(units,translations):raise ValueError('GAP_TRANSLATION_FIDELITY')
    groups={};proposals={};decisions=[]
    for unit,text in zip(units,translations):groups.setdefault(unit.get('paragraph'),[]).append((unit,text))
    if len(groups)>32:raise ValueError('GAP_GROUP_LIMIT')
    for paragraph,rows in groups.items():
        found=[];failures=Counter()
        for key,pair in pairs.items():
            try:target,proof=rebuild(pair['source'],[u for u,t in rows],[t for u,t in rows])
            except ValueError as exc:failures[str(exc)]+=1;continue
            found.append((key,target,proof))
        if len(found)!=1:
            decisions.append({'native_paragraph':paragraph,'status':'not_linked','candidate_count':len(found),'reasons':dict(failures)})
            continue
        key,target,proof=found[0]
        if key in proposals:raise ValueError('GAP_DUPLICATE_ENGINE_PARAGRAPH')
        if len(proposals)>=limit:raise ValueError('GAP_ROW_LIMIT')
        proposals[key]=target;decisions.append({'native_paragraph':paragraph,'pair_id':key,'status':'linked',**proof})
    return proposals,decisions


def patch(source_doc,before,after,number,known,issues,limit,folder,cfg,client,budget,records,invoke):
    """Optional cached engine backend for the existing bounded visual repair loop.

    All prior accepted corrections are re-screened with this candidate. Engine
    calls are cache-only; original jobs, native cache and PDFs are never replaced.
    A whole-page rerender is disclosed and all other page pixels must be equal.
    """
    import contextlib,copy,json,shutil,time
    from pathlib import Path
    import pymupdf as fitz
    import pdf_translate as translation
    import semantic_pipeline as pipeline
    import visual_review as visual
    folder=Path(folder)
    jobpath=Path(cfg['engine_job'])
    basejob,original,_,_=translation.prepare(jobpath)
    if original.resolve()!=Path(cfg['source']).resolve():raise ValueError('GAP_ENGINE_SOURCE_CHANGED')
    pairfile=basejob['provider'].get('translation_pairs_file')
    if not pairfile:raise ValueError('GAP_ENGINE_PAIR_RECEIPT_REQUIRED')
    pairs,metadata=semantic.load_translation_pairs(Path(pairfile))
    with fitz.open(before) as target:
        plans,decisions=source.prepare(source_doc[number-1],target[number-1],known,issues,limit)
        if not plans:return [],decisions
        active=[p for p in plans if p['units']]
        translated=visual.request_source_plan(active,source_doc,target,number,folder,
            {**cfg,'_source_followup_reserve':2,'_source_native_engine':True},client,budget,records,invoke)
    replacements=dict(cfg.get('_engine_replacements',{}));current={};links=[]
    for plan,texts in zip(active,translated):
        proposed,linked=propose(pairs,plan['units'],texts)
        if current.keys()&proposed.keys():raise ValueError('GAP_DUPLICATE_ENGINE_PARAGRAPH')
        current.update(proposed);links.extend(linked)
    visual.save_json(folder/'engine-gap-links.json',{'decisions':links,'proposed_rows':sorted(current)})
    if not current:return [],decisions+[{'reason':'ENGINE_GAP_NO_COMPLETE_PARAGRAPH_LINK'}]
    replacements.update(current)
    if len(replacements)>8:raise ValueError('GAP_ROW_LIMIT')
    selected={key:{'source':pairs[key]['source'],'target':text} for key,text in replacements.items()}
    semantic.checked_replacements({'replacements':replacements},{key:pairs[key] for key in replacements},
        basejob['provider'].get('protected_identifiers',()))
    # Reserve one real full-page follow-up before paying for semantic screening.
    budget.require(2)
    record={'purpose':'engine_gap_semantic_precheck','page':number,'model':cfg['provider']['model'],
        'backend':cfg['provider']['type'],'cache_hit':False,'native_usage':None,'cost_usd':None,'image_attachments':0}
    prompt=semantic.prompt(selected);record['request_sha256']=visual.digest(prompt.encode());started=time.monotonic()
    try:
        value,usage=invoke(client,prompt,[],cfg,budget,folder,record,schema=semantic.schema(selected))
        record['native_usage']=visual.usage_counters(usage);checked=semantic.checked(value,selected)
        checkpath=folder/'engine-gap-semantic.json';visual.save_json(checkpath,checked)
        if semantic.screening_status(checked,selected)!='semantic_model_screened':raise ValueError('GAP_ENGINE_SEMANTIC_PRECHECK_FAILED')
    except Exception as exc:
        record['error_code']=exc.code if isinstance(exc,bridge.BridgeError) else str(exc);raise
    finally:record['seconds']=round(time.monotonic()-started,3);records.append(record)
    receipt=pipeline.correction_receipt(pairs,metadata,replacements,cfg['provider'],
        visual.digest((folder/'source-prose-plan.json').read_bytes()),visual.digest(checkpath.read_bytes()),8)
    correction=folder/'engine-gap-corrections.json';visual.save_json(correction,receipt)
    job=copy.deepcopy(basejob);job['output']=str(folder/'engine')
    job['timeout_seconds']=max(5,int(budget.timeout(job.get('timeout_seconds',1800))))
    job['provider'].update(cache_only=True,quality_corrections_file=str(correction),
        diagnostics_dir=str(folder/'engine-diag'),translation_pairs_file=str(folder/'engine-pairs.json'))
    path=folder/'engine.job.json';visual.save_json(path,job)
    with (folder/'engine-driver.log').open('x',encoding='utf-8') as stream:
        with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
            result=translation.run_job(path,cfg.get('engine','babeldoc'),True)
    visual.save_json(folder/'engine-result.json',result)
    if result.get('status')=='failed':raise ValueError('GAP_ENGINE_RERENDER_FAILED')
    after_pairs,after_metadata=semantic.load_translation_pairs(folder/'engine-pairs.json')
    binding=pipeline.link_rerender(pairs,metadata,after_pairs,after_metadata,replacements)
    visual.save_json(folder/'engine-pair-binding.json',binding)
    mono=list((folder/'engine').glob('*.mono.pdf'))
    if len(mono)!=1:raise ValueError('GAP_ENGINE_MONO_OUTPUT_NOT_UNIQUE')
    if Path(after).exists():raise ValueError('GAP_ENGINE_CANDIDATE_ALREADY_EXISTS')
    shutil.copyfile(mono[0],after)
    with fitz.open(before) as old,fitz.open(after) as new:
        if len(old)!=len(new):raise ValueError('GAP_ENGINE_PAGE_COUNT_CHANGED')
        area=list(new[number-1].rect)
    if not visual.regression_check(before,after,number,[area]):raise ValueError('GAP_ENGINE_CHANGED_OTHER_PAGE_PIXELS')
    return [{'region':{'id':active[0]['issue']['region_id'],'bbox':area},'issue':active[0]['issue'],
        'method':'native_engine_gap_rerender','scope':'Whole-page native engine rerender of bounded paragraph corrections; full-page follow-up required',
        'corrected_pair_ids':sorted(current),'engine_replacements':replacements,'engine_pair_binding':binding,
        'source_gap_links':links,'cache_only':True,'other_page_pixels_unchanged':True}],decisions
