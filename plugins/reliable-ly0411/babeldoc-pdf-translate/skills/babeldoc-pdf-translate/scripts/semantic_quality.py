"""Explicit quality decisions and data-driven known-failure vetoes; no inference."""
import hashlib,json,re
from pathlib import Path
import semantic_review as semantic


def digest(text):return hashlib.sha256(text.encode()).hexdigest()


def load_corpora(paths):
    if not isinstance(paths,list) or len(paths)>16:raise ValueError('INVALID_REGRESSION_CORPORA')
    result=[]
    for name in paths:
        path=Path(name)
        if path.is_symlink() or not path.is_file() or path.stat().st_size>2*1024*1024:raise ValueError('INVALID_REGRESSION_CORPUS_FILE')
        raw=path.read_bytes();data=json.loads(raw)
        if not isinstance(data,dict) or set(data)-{'version','failures','provenance','source_document_sha256'} or type(data.get('version')) is not int or data.get('version')!=1:
            raise ValueError('INVALID_REGRESSION_CORPUS_SCHEMA')
        failures=data.get('failures')
        document=data.get('source_document_sha256')
        if document is not None and (not isinstance(document,str) or not re.fullmatch('[0-9a-f]{64}',document)):
            raise ValueError('INVALID_REGRESSION_DOCUMENT_BINDING')
        if not isinstance(failures,list) or not 1<=len(failures)<=512:raise ValueError('INVALID_REGRESSION_CORPUS_SIZE')
        seen=set();indexed={}
        for row in failures:
            if not isinstance(row,dict) or set(row)!={'id','source','target','reason'} or any(not isinstance(x,str) or not x.strip() for x in row.values()):
                raise ValueError('INVALID_REGRESSION_CORPUS_ROW')
            if row['id'] in seen or len(row['id'])>128 or len(row['reason'])>2000 or any(len(row[k])>16000 for k in ('source','target')):raise ValueError('INVALID_REGRESSION_CORPUS_ROW')
            seen.add(row['id']);key=(digest(row['source']),digest(row['target']))
            if key in indexed:raise ValueError('DUPLICATE_REGRESSION_FAILURE')
            indexed[key]={'id':row['id'],'reason':row['reason']}
        result.append({'path':path,'sha256':hashlib.sha256(raw).hexdigest(),'document_sha256':data.get('source_document_sha256'),
            'index':indexed})
    return result


def known_failures(pairs,corpora,document_sha256):
    semantic.checked_collection(pairs);hits=[]
    for corpus in corpora:
        if corpus['document_sha256'] and corpus['document_sha256']!=document_sha256:continue
        for key,row in pairs.items():
            identity=(digest(row['source']),digest(row['target']))
            failed=corpus['index'].get(identity)
            if failed:hits.append({'pair_id':key,'case_id':failed['id'],'reason':failed['reason'],
                'source_sha256':identity[0],'target_sha256':identity[1],'corpus_sha256':corpus['sha256']})
    return hits


def decide(*,execution_completed,model_status,requested_pages,image_pages,uncertain_count,
           relation_witness_coverage_complete,known_regressions,inputs_unchanged=True,protocol_validated=False):
    """Execution/model completion is never an independent quality certificate."""
    if uncertain_count is not None and (type(uncertain_count) is not int or uncertain_count<0):raise ValueError('INVALID_UNCERTAINTY_COUNT')
    if type(relation_witness_coverage_complete) is not bool:raise ValueError('INVALID_RELATION_COVERAGE_FLAG')
    missing=sorted(set(requested_pages)-set(image_pages))
    if not inputs_unchanged:status='blocked_input_change'
    elif known_regressions:status='blocked_known_regression'
    elif uncertain_count is None or uncertain_count>0:status='blocked_uncertainty'
    elif missing or not relation_witness_coverage_complete:status='blocked_incomplete_evidence'
    elif not execution_completed or model_status not in {'model_screened','sample_model_screened'}:status='blocked_model_or_execution'
    elif protocol_validated is not True:status='blocked_unvalidated_protocol'
    else:status='model_screened_pending_independent_acceptance'
    return {'quality_status':status,'quality_passed':False,'independent_acceptance_required':True,
        'candidate_ready_for_independent_validation':status=='model_screened_pending_independent_acceptance',
        'promotion_allowed':False,'protocol_validated':protocol_validated is True,
        'missing_image_pages':missing,'relation_witness_coverage_complete':bool(relation_witness_coverage_complete),
        'known_regressions':known_regressions,
        'scope':'Quoted relation witnesses and known-failure vetoes are evidence gates, not proof of semantic correctness.'}
