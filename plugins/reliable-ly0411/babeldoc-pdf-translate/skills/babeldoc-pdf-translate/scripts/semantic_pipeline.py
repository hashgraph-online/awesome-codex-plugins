#!/usr/bin/env python3
"""Bounded whole-paragraph semantic repair with actual-engine rerender and PDF QA.

An explicit native paragraph job and one explicitly selected quality model are
required. No document-specific wording, geometry or fallback model is supplied.
"""
import argparse,copy,hashlib,json,os,shutil,threading,time,tempfile
from pathlib import Path
import pymupdf as fitz
import chat_bridge as b
import pdf_translate as translation
import pdf_pipeline
import visual_review as v
import semantic_review as s
import source_repair as source_repair
import region_review as regions
import translation_corrections as corrections
import semantic_quality as quality
import semantic_relations as relations


def save(path,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    fd,name=tempfile.mkstemp(dir=path.parent,prefix='.'+path.name)
    temporary=Path(name)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path)
    finally:temporary.unlink(missing_ok=True)


def provider_identity(provider):
    return {k:provider.get(k) for k in ('type','model','base_url','reasoning_effort','codex_bin',
        'response_format','token_limit_field','max_tokens')}


class Session:
    """One durable budget shared by translation, semantics and visual repair."""
    def __init__(self,cfg,client=None,protocol='summary-v1'):
        self.cfg=cfg;self.budget=v.Budget(cfg['limits']);self.lock=threading.Lock()
        self.client=client or (v.NativeVision(cfg['provider']) if cfg['provider']['type']=='codex'
            else v.CompatibleVision(cfg['provider'],v.SCHEMA))
        self.client.version=self.client.doctor()['native_version']
        self.ledger={'version':1,'max_native_calls':cfg['limits']['max_model_calls'],'calls':[]}
        self.path=cfg['output']/'call-ledger.json'
        if self.path.exists():raise ValueError('SESSION_LEDGER_ALREADY_EXISTS')
        self.capability=None;self.records=[];save(self.path,self.ledger)
        self.protocol=protocol;self.last_relation_coverage=False

    def verify_provider(self,provider):
        if provider_identity(provider)!=provider_identity(self.cfg['provider']):
            raise ValueError('QUALITY_SESSION_PROVIDER_CHANGED')

    def start(self,record):
        with self.lock:
            self.budget.require();self.budget.calls+=1
            entry={**record,'invocation':self.budget.calls,'state':'started',
                'started_utc':b.datetime.now(b.timezone.utc).isoformat(),'native_usage':None,'cost_usd':None}
            self.ledger['calls'].append(entry);save(self.path,self.ledger)
            return entry

    def finish(self,entry,usage,error=None):
        with self.lock:
            entry.update(state='returned' if error is None else 'failed',native_usage=v.usage_counters(usage),
                ended_utc=b.datetime.now(b.timezone.utc).isoformat())
            if error:entry['error_code']=error
            save(self.path,self.ledger)

    def invoke(self,client,prompt,images,cfg,budget,folder,record,*,schema=None):
        self.verify_provider(cfg['provider'])
        if client is not self.client or budget is not self.budget:raise ValueError('QUALITY_SESSION_MISMATCH')
        timeout=budget.timeout(cfg['provider']['timeout_seconds'])
        entry=self.start({k:record.get(k) for k in ('purpose','page','model','backend','request_sha256')}|
            {'prompt_sha256':v.digest(prompt.encode()),'image_attachments':len(images)})
        save(folder/('request-%03d.json'%entry['invocation']),{'prompt':prompt,'schema':schema or v.SCHEMA,
            'images_sha256':[v.digest(p.read_bytes()) for p in images]})
        usage=None;error=None
        try:
            value,usage=(client.inspect(prompt,images,timeout) if schema is None else client.inspect(prompt,images,timeout,schema=schema))
            save(folder/('response-%03d.json'%entry['invocation']),value)
            if getattr(client,'last_transport',None):record['native_transport']=client.last_transport
            return value,usage
        except Exception as exc:
            usage=getattr(exc,'native_usage',None);error=exc.code if isinstance(exc,b.BridgeError) else type(exc).__name__
            raise
        finally:self.finish(entry,usage,error)

    def ensure_vision(self,cfg,records):
        self.verify_provider(cfg['provider'])
        if self.capability is None:
            proof=[];v.capability_probe(self.client,cfg,self.budget,proof,self.invoke)
            self.capability=proof[0];records.extend(proof)
        else:
            records.append({'purpose':'same_session_vision_capability_reuse','verified':True,'cache_hit':False,
                'native_usage':None,'cost_usd':None,'image_sha256':self.capability['image_sha256']})

    def text(self,prompt,schema,checker,folder,purpose,*,fresh=False):
        folder.mkdir(exist_ok=False)
        identity={'semantic_cache_version':2 if self.protocol==relations.PROTOCOL else 1,'provider':provider_identity(self.cfg['provider']),
            'native_version':self.client.version,'prompt':prompt,'schema':schema}
        key=v.digest(b.canonical(identity).encode());cache=self.cfg['provider'].get('cache_dir')
        path=Path(cache)/(key+'.json') if cache else None
        record={'purpose':purpose,'request_sha256':key,'model':self.cfg['provider']['model'],
            'backend':self.cfg['provider']['type'],'cache_hit':False,'native_usage':None,'cost_usd':None}
        try:
            if path and path.exists() and not fresh:
                if path.is_symlink() or path.stat().st_size>2*b.MAX_REPLY:raise ValueError('INVALID_SEMANTIC_CACHE')
                stored=translation.read_json(path)
                if stored['request_sha256']!=key or v.digest(b.canonical(stored['response']).encode())!=stored['response_sha256']:
                    raise ValueError('INVALID_SEMANTIC_CACHE')
                value=stored['response'];checked=checker(value);record['cache_hit']=True
            else:
                value,usage=self.invoke(self.client,prompt,[],self.cfg,self.budget,folder,record,schema=schema)
                record['native_usage']=v.usage_counters(usage);checked=checker(value)
                if path and not fresh:
                    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
                    if path.parent.is_symlink() or (os.name=='posix' and path.parent.stat().st_mode&0o077):raise ValueError('SEMANTIC_CACHE_MUST_BE_PRIVATE')
                    save(path,{'request_sha256':key,'response_sha256':v.digest(b.canonical(value).encode()),'response':value})
            save(folder/'validated.json',checked);save(folder/'record.json',record)
            return checked,v.digest(b.canonical(value).encode())
        finally:self.records.append(record)

    def screen(self,pairs,folder,purpose,*,fresh=False):
        folder.mkdir(exist_ok=False);value={'pairs':{}}
        self.last_relation_coverage=False
        for n,batch in enumerate(s.batches(pairs)):
            if self.protocol==relations.PROTOCOL:
                witness,_=self.text(relations.prompt(batch),relations.schema(batch),lambda x:relations.checked(x,batch),
                    folder/('batch-%03d'%n),purpose,fresh=fresh)
                result=relations.as_review(witness,batch)
            else:
                result,_=self.text(s.prompt(batch),s.schema(batch),lambda x:s.checked(x,batch),
                    folder/('batch-%03d'%n),purpose,fresh=fresh)
            value['pairs'].update(result['pairs'])
        s.checked(value,pairs);save(folder/'validated.json',value)
        self.last_relation_coverage=self.protocol==relations.PROTOCOL
        save(folder/'evidence-coverage.json',{'protocol':self.protocol,'lexical_relation_witness_coverage_complete':self.last_relation_coverage,
            'scope':'Quote coverage is not proof of semantic truth; legacy summaries do not establish relation coverage.'})
        return value,v.digest(b.canonical(value).encode())


def receipt_index(pairs,metadata):
    """Bind pair keys to complete actual request/typed-row identities."""
    if set(pairs)!=set(metadata):raise ValueError('PAIR_RECEIPT_COVERAGE_CHANGED')
    result={}
    for key,row in metadata.items():
        identity=(row['cache_request_sha256'],b.canonical(row['source_row_id']))
        if identity in result:raise ValueError('PAIR_RECEIPT_DUPLICATE_ORIGIN')
        for name in ('cache_request_sha256','base_content_sha256','source_rows_sha256','base_output_sha256'):
            if not isinstance(row.get(name),str) or not corrections.SHA.fullmatch(row[name]):raise ValueError('PAIR_RECEIPT_BINDING_MISSING')
        if row.get('source_sha256')!=corrections.digest(pairs[key]['source']) or row.get('target_sha256')!=corrections.digest(pairs[key]['target']):
            raise ValueError('PAIR_RECEIPT_TEXT_CHANGED')
        result[identity]=key
    return result


def link_rerender(before,before_meta,after,after_meta,replacements):
    left=receipt_index(before,before_meta);right=receipt_index(after,after_meta)
    if set(left)!=set(right):raise ValueError('RERENDER_PARAGRAPH_ORIGINS_CHANGED')
    result={};linked=[]
    for identity,key in left.items():
        actual=right[identity];old=before_meta[key];new=after_meta[actual]
        if before[key]['source']!=after[actual]['source'] or any(old[k]!=new[k] for k in
            ('base_content_sha256','source_rows_sha256','base_output_sha256','kind')):
            raise ValueError('RERENDER_SOURCE_OR_BASE_CHANGED')
        if after[actual]['target']!=replacements.get(key,before[key]['target']):raise ValueError('RERENDER_TARGET_CHANGED')
        result[key]=after[actual];linked.append({'original_pair':key,'rendered_pair':actual,'request_sha256':identity[0],'source_row_id':new['source_row_id']})
    return result,linked


def correction_receipt(pairs,metadata,replacements,provider,repair_hash,recheck_hash,limit):
    receipt_index(pairs,metadata);entries={}
    for key,target in replacements.items():
        row=metadata[key]
        if row['kind']!='batch':raise ValueError('SEMANTIC_REPAIR_REQUIRES_BATCH_PARAGRAPH')
        if corrections.digest(pairs[key]['target'])!=row['base_output_sha256']:
            raise ValueError('SEMANTIC_PIPELINE_REQUIRES_UNCORRECTED_BASE')
        item=entries.setdefault(row['cache_request_sha256'],{k:row[k] for k in
            ('cache_request_sha256','base_content_sha256','source_rows_sha256')}|{'replacements':[]})
        item['replacements'].append({'id':row['source_row_id'],'source_sha256':corrections.digest(pairs[key]['source']),
            'previous_output_sha256':row['base_output_sha256'],'output':target})
    return {'version':1,'output_contract':'paragraphs','max_corrected_rows':limit,
        'provenance':{'model':provider['model'],'reasoning_effort':provider.get('reasoning_effort','unspecified'),
            'status':'semantic_screened','correction_response_sha256':repair_hash,'semantic_recheck_sha256':recheck_hash},
        'entries':list(entries.values())}


def prepare(path,engine):
    path=path.resolve();raw=translation.read_json(path);base=path.parent
    if not isinstance(raw,dict) or set(raw)!={'translation_job','output','review','semantic'}:raise ValueError('INVALID_SEMANTIC_PIPELINE_FIELDS')
    policy=raw['semantic']
    if not isinstance(policy,dict) or set(policy)-{'max_rounds','max_corrected_rows','fresh_final','protocol','regression_corpora'}:raise ValueError('INVALID_SEMANTIC_POLICY')
    if policy.get('protocol','summary-v1') not in {'summary-v1',relations.PROTOCOL}:raise ValueError('INVALID_SEMANTIC_PROTOCOL')
    names=policy.get('regression_corpora',[])
    if not isinstance(names,list) or len(names)>16 or any(not isinstance(p,str) or not p.strip() for p in names):raise ValueError('INVALID_REGRESSION_CORPORA')
    policy['regression_corpora']=[str(translation.resolve(base,p)) for p in names]
    quality.load_corpora(policy['regression_corpora'])
    if type(policy.get('max_rounds',1)) is not int or policy.get('max_rounds',1)!=1:raise ValueError('SEMANTIC_PIPELINE_SUPPORTS_ONE_BOUNDED_ROUND')
    if type(policy.get('max_corrected_rows',8)) is not int or not 1<=policy.get('max_corrected_rows',8)<=8:raise ValueError('INVALID_SEMANTIC_ROW_LIMIT')
    if type(policy.get('fresh_final',True)) is not bool:raise ValueError('INVALID_FRESH_FINAL_OPTION')
    jobpath=translation.resolve(base,raw['translation_job']);job,source,_,_=translation.prepare(jobpath)
    if 'astra' in job['provider'].get('model','').casefold():raise ValueError('ASTRA_DEVELOPMENT_ACCEPTANCE_ONLY')
    if job.get('source_language','en').lower()!='en' or job['target_language'].lower().replace('_','-') not in {'zh','zh-cn','zh-hans'}:
        raise ValueError('SEMANTIC_PIPELINE_REQUIRES_ENGLISH_TO_CHINESE')
    if job['provider']['type'] not in {'codex','dsh'} or job['provider'].get('output_contract')!='paragraphs':raise ValueError('SEMANTIC_PIPELINE_REQUIRES_NATIVE_PARAGRAPH_JOB')
    if job['provider'].get('quality_corrections_file'):raise ValueError('SEMANTIC_PIPELINE_REQUIRES_UNCORRECTED_BASE')
    if job.get('selected_pages_only') or job.get('outputs','both')=='dual' or job.get('watermark')=='both':raise ValueError('SEMANTIC_PIPELINE_REQUIRES_FULL_COUNT_MONO')
    out=translation.resolve(base,raw['output'])
    if out.exists() or any(p.is_relative_to(out) for p in (source,jobpath,path)):raise ValueError('SEMANTIC_PIPELINE_NEEDS_FRESH_OUTPUT')
    review=copy.deepcopy(raw['review']);v.validate_options(review,base)
    if review['review_mode']!='math_audits':raise ValueError('SEMANTIC_PIPELINE_NEEDS_EXPLICIT_MATH_AUDITS_MODE')
    pages=translation.selected_pages(job,translation.inspect_pdf(source)['page_count'])
    if review.get('pages',pages)!=pages:raise ValueError('SEMANTIC_AND_TRANSLATION_PAGE_SCOPE_MUST_MATCH')
    review['pages']=pages;review['translation_pages']=pages;review['translation_context']=pdf_pipeline.translation_preferences(job,jobpath)
    review.update(source=source,output=out)
    plan=translation.run_job(jobpath,engine,execute=False)
    return path,jobpath,job,source,out,review,policy,plan


def run(path,engine='babeldoc',execute=False,client=None,translator=None,final_audit_hook=None):
    import translation_contract as contracts
    path,jobpath,job,source,out,cfg,policy,plan=prepare(path,engine)
    report={'status':'planned','execution_status':'planned','quality_status':'not_evaluated','quality_passed':False,
        'translation_model':job['provider'].get('model'),'quality_model':cfg['provider']['model'],
        'limits':cfg['limits'],'semantic':policy,'selected_pages':cfg['pages'],'cost_usd':None,
        'scope':'Bounded complete-paragraph semantics, edited-region image review and narrow math audits; independent acceptance separate.'}
    report.update(final_audit_required=True,delivery_allowed=False,delivery_status='planned_final_audit_required')
    report.update(translation_pages=list(cfg['pages']),review_pages=list(cfg['pages']),
        translation_contract=contracts.from_job(job,jobpath,translation.inspect_pdf(source)['page_count']))
    if final_audit_hook is not None:
        import final_audit
        report['final_audit_plan']=final_audit.plan_for(final_audit_hook)
        check_contract=final_audit.optional_attribute(final_audit_hook,'validate_contract')
        if callable(check_contract):check_contract(report['translation_contract'])
    if not execute:return report
    out.mkdir(parents=True,exist_ok=False,mode=0o700);session=Session(cfg,client,policy.get('protocol','summary-v1'));translator=translator or translation.run_job
    corpora=quality.load_corpora(policy['regression_corpora'])
    hashes={k:v.digest(p.read_bytes()) for k,p in [('source',source),('translation_job',jobpath),('pipeline_job',path)]}
    best=None;final_pairs=None;report['image_pages_checked']=[]
    try:
        def render(stage,correction=None):
            current=copy.deepcopy(job);current['input']=str(source);current['output']=str(out/('translation-'+stage))
            for name in ('prompt_file',):
                if name in current:current[name]=str(translation.resolve(jobpath.parent,current[name]))
            if current.get('glossaries'):current['glossaries']=[str(translation.resolve(jobpath.parent,p)) for p in current['glossaries']]
            provider=current['provider'];provider['max_model_calls']=min(provider.get('max_model_calls',512),max(1,cfg['limits']['max_model_calls']-session.budget.calls))
            provider.update(translation_pairs_file=str(out/('pairs-'+stage+'.jsonl')),diagnostics_dir=str(out/('translation-diagnostics-'+stage)))
            if correction:provider.update(quality_corrections_file=str(correction),cache_only=True)
            effective=out/('translation-'+stage+'.json');save(effective,current)
            result=translator(effective,engine,execute=True,native_observer=session)
            report.setdefault('translation_runs',[]).append(result)
            if result['status']!='needs-review':raise ValueError('SEMANTIC_PIPELINE_TRANSLATION_FAILED')
            mono=[x for x in result['output_validation']['files'] if x['kind']=='mono' and x['valid']]
            if len(mono)!=1:raise ValueError('AMBIGUOUS_MONO_OUTPUT')
            pairs,metadata=s.load_translation_pairs(provider['translation_pairs_file']);receipt_index(pairs,metadata)
            return Path(mono[0]['file']),pairs,metadata

        def math_stage(raw,stage,pairs):
            effective={**cfg,'translated':raw,'output':out/('math-'+stage),'chinese_prose_guard':False}
            effective['limits']={**cfg['limits'],'max_rounds':1}
            name=out/('math-'+stage+'.json');save(name,{k:str(x) if isinstance(x,Path) else x for k,x in effective.items()})
            checked=v.load_config(name);result=v.run(checked,session=session);report.setdefault('math_runs',[]).append(result)
            if not result['status'].endswith(('targeted_repairs_screened','program_math_audits_passed')):raise ValueError('MATH_STAGE_NEEDS_REVIEW')
            restored=[edit['source_restore']['semantic_pair'] for page in result['pages'] for edit in page['accepted_repairs'] if edit.get('source_restore',{}).get('semantic_pair')]
            final,links=s.reflect_source_restorations(pairs,restored)
            save(out/('source-restorations-'+stage+'.json'),{'links':links,'restorations':restored})
            return checked['output']/'best.mono.pdf',final

        raw,base_pairs,metadata=render('initial');best,initial=math_stage(raw,'initial',base_pairs)
        report['stage']='initial_complete_semantic_screen'
        before,before_hash=session.screen(initial,out/'semantic-initial','initial_complete_semantic_screen')
        if any(row['status']=='uncertain' for row in before['pairs'].values()):raise ValueError('SEMANTIC_SCREEN_UNCERTAIN')
        selected={key:initial[key] for key,row in before['pairs'].items() if row['status']=='different'}
        if selected:
            limit=policy.get('max_corrected_rows',8)
            if len(selected)>limit:raise ValueError('SEMANTIC_REPAIR_ROW_LIMIT')
            if any(initial[key]!=base_pairs[key] for key in selected):raise ValueError('SOURCE_RESTORED_PARAGRAPH_NEEDS_SOURCE_SLOT_REPAIR')
            locations={}
            with fitz.open(source) as original:
                for key in selected:
                    hits=[];ambiguous=False
                    for number in cfg['pages']:
                        item,error=source_repair.locate_source_prose(original[number-1],initial[key]['source'])
                        if error=='SOURCE_PROSE_AMBIGUOUS':ambiguous=True
                        if item:hits.append(number)
                    if ambiguous or len(hits)!=1:raise ValueError('SEMANTIC_SOURCE_PAGE_LINK_AMBIGUOUS')
                    locations[key]=hits[0]
            # Correction + complete recheck + focused images + fresh final audit.
            session.budget.require(1+len(cfg['pages'])+len(s.batches(initial))*(1+int(policy.get('fresh_final',True))))
            selected_review={'pairs':{key:before['pairs'][key] for key in selected}}
            replacement,repair_hash=session.text(s.repair_prompt(selected,selected_review,cfg.get('translation_context','')),
                s.repair_schema(selected),lambda x:s.checked_replacements(x,selected,job['provider'].get('protected_identifiers',())),
                out/'semantic-correction','complete_paragraph_correction')
            expected={key:dict(row,target=replacement.get(key,row['target'])) for key,row in initial.items()}
            checked,recheck_hash=session.screen(expected,out/'semantic-precheck','complete_candidate_semantic_recheck')
            if s.screening_status(checked,expected)!='semantic_model_screened':raise ValueError('CORRECTED_SEMANTICS_NEEDS_REVIEW')
            correction=correction_receipt(base_pairs,metadata,replacement,cfg['provider'],repair_hash,recheck_hash,limit)
            correction_path=out/'quality-corrections.json';save(correction_path,correction);corrections.load(correction_path)
            rerendered,actual,actual_meta=render('corrected',correction_path)
            linked,origins=link_rerender(base_pairs,metadata,actual,actual_meta,replacement);save(out/'rerender-origin-links.json',origins)
            candidate,final_pairs=math_stage(rerendered,'corrected',linked)
            if final_pairs!=expected:raise ValueError('FINAL_ACTUAL_PAIRS_DIFFER_FROM_REVIEWED_CANDIDATE')
            edits_by_page={}
            with fitz.open(source) as original,fitz.open(best) as old,fitz.open(candidate) as current:
                for key in selected:
                    number=locations[key];area=regions.prose_review_island(original[number-1],old[number-1],current[number-1],initial[key]['source'])
                    edit={'region':area,'method':'source_bound_complete_paragraph_correction',
                        'issue':{'region_id':key,'category':'translation','severity':'major','reason':before['pairs'][key]['summary'],'replacement':''},
                        'prose_trace':[{'paragraph':key,'source':initial[key]['source'],'candidate':final_pairs[key]['target']}]}
                    edits_by_page.setdefault(number,[]).append(edit)
                boxes={number:[e['region']['bbox'] for e in edits] for number,edits in edits_by_page.items()}
                # All pages are checked together, allowing only the program-owned edits.
                if not regression_many(best,candidate,boxes):raise ValueError('SEMANTIC_RERENDER_OUTSIDE_REGRESSION')
                for number,edits in edits_by_page.items():
                    folder=out/('focused-%03d'%number);folder.mkdir()
                    focused,areas=regions.compare(original,best,candidate,number,edits,folder,cfg,session.client,session.budget,session.records,v.SCHEMA,session.invoke,v.usage_counters,whole_page_context=True)
                    report['image_pages_checked'].append(number)
                    accepted,retained,_,decision=regions.assess({'issues':[]},focused,[],[],edits,v.improved)
                    save(folder/'acceptance.json',{'accepted':accepted,'remaining':retained,'decision':decision,'areas':areas})
                    if not accepted or retained['issues']:raise ValueError('FOCUSED_SEMANTIC_REPAIR_NEEDS_REVIEW')
            best=candidate;report['corrected_rows']=len(replacement);report['regression_outside_edited_regions']=True
        else:final_pairs=initial;report['corrected_rows']=0
        # Also inspect requested pages that had no semantic edit; otherwise a
        # clear text screen could silently skip the whole-page image check.
        with fitz.open(source) as original,fitz.open(best) as current:
            for number in cfg['pages']:
                if number in report['image_pages_checked']:continue
                folder=out/('full-page-%03d'%number);folder.mkdir()
                page_review,_=v.review_page(original,current,number,folder,cfg,session.client,session.budget,session.records,session.invoke)
                report['image_pages_checked'].append(number)
                if page_review['issues']:raise ValueError('UNEDITED_PAGE_IMAGE_NEEDS_REVIEW')
        save(out/'final-actual-pairs.json',final_pairs)
        final,_=session.screen(final_pairs,out/'semantic-final','final_actual_complete_semantic_screen',fresh=policy.get('fresh_final',True))
        report['final_semantic_summary']=s.summary(final)
        if s.screening_status(final,final_pairs)!='semantic_model_screened':raise ValueError('FINAL_SEMANTICS_NEEDS_REVIEW')
        with fitz.open(source) as original,fitz.open(best) as current:
            prose={number:__import__('prose_completeness').findings(original[number-1],v.regions(current[number-1])) for number in cfg['pages']}
        save(out/'final-program-prose.json',prose)
        if any(prose.values()):raise ValueError('FINAL_UNTRANSLATED_PROSE')
        report['status']='sample_model_screened' if len(cfg['pages'])<translation.inspect_pdf(source)['page_count'] else 'model_screened'
        report['stage']='complete'
    except Exception as error:
        code=error.code if isinstance(error,b.BridgeError) else str(error) if isinstance(error,ValueError) else type(error).__name__
        report.update(status='needs_manual_review',error_code=code)
    finally:
        report.update(model_calls=session.budget.calls,requests=session.records,native_version=session.client.version,
            seconds=round(time.monotonic()-session.budget.started,3),input_hashes=hashes)
        report['inputs_unchanged']=all(v.digest(p.read_bytes())==hashes[k] for k,p in [('source',source),('translation_job',jobpath),('pipeline_job',path)])
        report['inputs_unchanged'] &= all(v.digest(c['path'].read_bytes())==c['sha256'] for c in corpora)
        try:
            report['inputs_unchanged'] &= contracts.from_job(translation.read_json(jobpath),jobpath,
                translation.inspect_pdf(source)['page_count'])==report['translation_contract']
        except (ValueError,OSError):report['inputs_unchanged']=False
        if not report['inputs_unchanged']:report.update(status='failed',error_code='SEMANTIC_PIPELINE_INPUT_CHANGED')
        if best:
            shutil.copyfile(best,out/'best.mono.pdf');v.bilingual(source,out/'best.mono.pdf',out/'best.dual.pdf')
            report['output_sha256']=v.digest((out/'best.mono.pdf').read_bytes())
        report['model_screen_status']=report['status']
        report['execution_status']='completed' if report.get('stage')=='complete' else 'incomplete_or_failed'
        hits=quality.known_failures(final_pairs,corpora,hashes['source']) if final_pairs else []
        decision=quality.decide(execution_completed=report['execution_status']=='completed',model_status=report['model_screen_status'],
            requested_pages=cfg['pages'],image_pages=report['image_pages_checked'],uncertain_count=report.get('final_semantic_summary',{}).get('uncertain'),
            relation_witness_coverage_complete=session.last_relation_coverage,known_regressions=hits,inputs_unchanged=report['inputs_unchanged'])
        report.update(decision)
        report['status']='needs_manual_review' if decision['quality_status'].startswith('blocked_') else decision['quality_status']
        if best:
            import final_audit
            final_audit.attach_pipeline_report(report,source,{'mono':out/'best.mono.pdf','dual':out/'best.dual.pdf'},out/'final-audit',final_audit_hook)
            try:
                contract_unchanged=contracts.from_job(translation.read_json(jobpath),jobpath,
                    translation.inspect_pdf(source)['page_count'])==report['translation_contract']
            except (ValueError,OSError):contract_unchanged=False
            if not contract_unchanged:
                report.update(status='failed',error_code='TRANSLATION_CONTRACT_CHANGED_DURING_PIPELINE',
                    quality_passed=False,delivery_allowed=False,quality_status='blocked_input_changed')
                report.pop('delivery_artifacts',None)
        save(out/'pipeline-report.json',report)
    return report


def regression_many(before,after,boxes,dpi=150):
    """All page pixels, allowing separately derived regions on multiple pages."""
    import numpy as np,math
    with fitz.open(before) as left,fitz.open(after) as right:
        if len(left)!=len(right):return False
        for i,(a,c) in enumerate(zip(left,right),1):
            if a.rect!=c.rect or a.rotation!=c.rotation:return False
            x=a.get_pixmap(dpi=dpi,alpha=False);y=c.get_pixmap(dpi=dpi,alpha=False)
            diff=np.any(np.frombuffer(x.samples,dtype=np.uint8).reshape(x.height,x.width,x.n)!=np.frombuffer(y.samples,dtype=np.uint8).reshape(y.height,y.width,y.n),axis=2)
            for area in boxes.get(i,[]):
                r=fitz.Rect(area)*(dpi/72)
                diff[max(0,math.floor(r.y0)-3):min(x.height,math.ceil(r.y1)+3),max(0,math.floor(r.x0)-3):min(x.width,math.ceil(r.x1)+3)]=False
            if diff.any():return False
    return True


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('job',type=Path)
    parser.add_argument('--engine',default='babeldoc');parser.add_argument('--execute',action='store_true');parser.add_argument('--final-audit-config',type=Path);args=parser.parse_args()
    import final_audit
    hook=final_audit.from_config(args.final_audit_config) if args.final_audit_config else None
    result=run(args.job,args.engine,args.execute,final_audit_hook=hook);print(json.dumps({k:x for k,x in result.items() if k not in {'translation_runs','math_runs','requests'}},ensure_ascii=False))
    raise SystemExit(0 if result['status']=='planned' or result.get('delivery_allowed') is True else 2)
