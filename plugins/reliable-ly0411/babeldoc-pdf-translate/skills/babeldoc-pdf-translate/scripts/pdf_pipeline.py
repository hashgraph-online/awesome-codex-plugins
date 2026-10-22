#!/usr/bin/env python3
"""Translation -> BabelDOC -> separately configured visual repair -> recheck.

No model is selected or upgraded implicitly. Astra development acceptance is
a separate review job, outside this production pipeline.
"""
import argparse
import copy
import json
from pathlib import Path
import shutil
import time
import pdf_translate as translate
import visual_review as visual
import translation_contract as contracts


def translation_preferences(job,path):
    """Snapshot the exact configured prompt and glossary for review/repair."""
    base=path.resolve().parent;parts=[]
    if job.get('prompt_file'):
        parts.append(translate.resolve(base,job['prompt_file']).read_text(encoding='utf-8-sig').strip())
    for name in job.get('glossaries',[]):
        parts.append('Glossary:\n'+visual.bridge.canonical(translate.glossary(translate.resolve(base,name))))
    context='\n\n'.join(parts)
    if len(context)>32000:raise ValueError('Review translation preferences exceed 32000 characters')
    return context


def prepare(path,engine):
    base=path.resolve().parent
    cfg=translate.read_json(path)
    if not isinstance(cfg,dict) or set(cfg)!={'translation_job','output','review'}:
        raise ValueError('Pipeline requires translation_job,output,review only')
    job_path=translate.resolve(base,cfg['translation_job'])
    job,source,translation_output,_=translate.prepare(job_path)
    if not job['provider'].get('model'):
        raise ValueError('Production translation model must be selected explicitly')
    if 'astra' in job['provider']['model'].casefold():
        raise ValueError('Astra is for development acceptance only, never production translation')
    if job.get('outputs','both')=='dual' or job.get('selected_pages_only') or job.get('watermark')=='both':
        raise ValueError('Pipeline needs a full-page-count mono variant and one watermark mode')
    output=translate.resolve(base,cfg['output'])
    if output.exists() or source.is_relative_to(output) or job_path.is_relative_to(output):
        raise ValueError('Pipeline needs a fresh output directory outside input paths')
    if output==translation_output or output.is_relative_to(translation_output):
        raise ValueError('Pipeline output cannot be inside the translation output directory')
    review=cfg['review']
    if not isinstance(review,dict) or set(review)-{'provider','limits','repair','dpi','pages','focused_recheck','preserve_contact_metadata','preserve_tiny_connectors','math_scale_guard','math_operator_guard','review_mode','chinese_prose_guard'}:
        raise ValueError('Unknown pipeline review field; source/translated/output are derived')
    review=copy.deepcopy(review)
    if str(job.get('target_language','zh-CN')).lower().replace('_','-') in {'zh','zh-cn','zh-hans','chinese','simplified chinese'}:
        review.setdefault('chinese_prose_guard',True)
    context=translation_preferences(job,job_path)
    if context:review['translation_context']=context
    review=visual.validate_options(review,base)
    count=translate.inspect_pdf(source)['page_count']
    review['translation_pages']=translate.selected_pages(job,count)
    if 'pages' in review:
        pages=review['pages']
        if (not isinstance(pages,list) or not pages or any(type(p) is not int or not 1<=p<=count for p in pages)
                or len(set(pages))!=len(pages)):
            raise ValueError('Invalid pipeline review pages')
    minimum=1 if review['review_mode']=='math_audits' else len(review.get('pages',range(1,count+1)))+1
    if review['limits']['max_model_calls']<minimum:
        raise ValueError('Review budget must cover selected pages plus one image capability probe')
    # Dry run probes engine flags and PDF structure, never calls a model.
    plan=translate.run_job(job_path,engine,execute=False)
    plan['translation_contract']=contracts.from_job(job,job_path,count)
    plan['requested_translation_pages']=translate.selected_pages(job,count)
    plan['review_pages']=list(review.get('pages',range(1,count+1)))
    return job_path,output,review,plan


def run(path,engine,execute=False,final_audit_hook=None):
    if 'semantic' in translate.read_json(path):
        import semantic_pipeline
        return semantic_pipeline.run(path,engine,execute,final_audit_hook=final_audit_hook)
    job_path,output,review,plan=prepare(path,engine)
    result={'status':'planned','execution_status':'planned','quality_status':'not_evaluated','quality_passed':False,
            'translation_model':plan['provider'].get('model'),
            'translation_backend':plan['provider']['type'],'review_model':review['provider']['model'],
            'review_backend':review['provider']['type'],'review_limits':review['limits'],
            'repair_enabled':review['repair'],'development_acceptance':'Separate explicit job; never a fallback',
            'cost_usd':None,'translation_pages':plan['requested_translation_pages'],
            'selected_pages':plan['requested_translation_pages'],
            'review_pages':plan['review_pages'],
            'translation_contract':copy.deepcopy(plan['translation_contract'])}
    result.update(final_audit_required=True,delivery_allowed=False,delivery_status='planned_final_audit_required')
    if final_audit_hook is not None:
        import final_audit
        result['final_audit_plan']=final_audit.plan_for(final_audit_hook)
        check_contract=final_audit.optional_attribute(final_audit_hook,'validate_contract')
        if callable(check_contract):check_contract(result['translation_contract'])
    result['translation_job_sha256']=translate.digest(job_path)
    result['translation_preferences_sha256']=visual.digest(review.get('translation_context','').encode())
    if not execute:
        return result
    output.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    try:
        result['stage']='translation'
        translated=translate.run_job(job_path,engine,execute=True)
        result['translation_status']=translated['status']
        if translated['status']!='needs-review':
            result['status']='failed'
            return result
        if translate.digest(job_path)!=result['translation_job_sha256']:
            raise ValueError('Translation configuration changed during execution')
        if visual.digest(translation_preferences(translate.read_json(job_path),job_path).encode())!=result['translation_preferences_sha256']:
            raise ValueError('Translation preferences changed during execution')
        variants=[r for r in translated['output_validation']['files'] if r['kind']=='mono' and r['valid']]
        if len(variants)!=1:
            raise ValueError('Ambiguous mono translation output')
        cfg={'source':plan['arguments'][plan['arguments'].index('--files')+1],'translated':variants[0]['file'],
             'output':str(output/'visual'),**review}
        # Load through the same PDF/geometry validator as standalone review.
        effective=output/'effective-review.json'
        visual.save_json(effective,cfg)
        checked=visual.load_config(effective)
        result['stage']='visual_review_and_repair'
        report=visual.run(checked)
        result.update(status=report['status'],review_status=report['status'],
                      model_calls=report['model_calls'],vision_capability_verified=report.get('vision_capability_verified',False))
        result.update(execution_status=report.get('execution_status'),quality_status=report.get('quality_status'),quality_passed=False)
        for name in ('best.mono.pdf','best.dual.pdf'):
            shutil.copyfile(checked['output']/name,output/name)
        result['stage']='complete'
        result['review_pages']=report.get('selected_pages',result['review_pages'])
        if contracts.from_job(translate.read_json(job_path),job_path,translate.inspect_pdf(checked['source'])['page_count'])!=result['translation_contract']:
            raise ValueError('TRANSLATION_CONTRACT_CHANGED_DURING_PIPELINE')
        import final_audit
        final_audit.attach_pipeline_report(result,checked['source'],
            {'mono':output/'best.mono.pdf','dual':output/'best.dual.pdf'},output/'final-audit',final_audit_hook)
        if contracts.from_job(translate.read_json(job_path),job_path,translate.inspect_pdf(checked['source'])['page_count'])!=result['translation_contract']:
            raise ValueError('TRANSLATION_CONTRACT_CHANGED_DURING_PIPELINE')
    except Exception as error:
        result['status']='failed'
        result.update(stage='failed',quality_passed=False,delivery_allowed=False,delivery_status='needs_manual_input_or_execution')
        result.pop('delivery_artifacts',None)
        result['error_code']=error.code if isinstance(error,visual.bridge.BridgeError) else str(error) if isinstance(error,ValueError) else type(error).__name__
    finally:
        result['execution_status']='completed' if result.get('stage')=='complete' else 'incomplete_or_failed'
        if result['quality_status']=='not_evaluated':result['quality_status']='blocked_execution'
        result['seconds']=round(time.monotonic()-started,3)
        visual.save_json(output/'pipeline-report.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('job',type=Path)
    parser.add_argument('--engine',default='babeldoc')
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--final-audit-config',type=Path)
    args=parser.parse_args()
    try:
        import final_audit
        hook=final_audit.from_config(args.final_audit_config) if args.final_audit_config else None
        result=run(args.job,args.engine,args.execute,final_audit_hook=hook)
        print(json.dumps(result,ensure_ascii=False))
        raise SystemExit(0 if result['status']=='planned' or result.get('delivery_allowed') is True else 2)
    except (ValueError,OSError) as error:
        parser.exit(2,'Pipeline error: '+str(error)+'\n')
