"""Prospective, offline adjudication inbox. No stdin, models or PDF writes.

Hashes bind bytes, not reviewer identity or semantic truth. The trusted
controller owns this directory; models must never get write access to it.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import uuid

VERSION='0.1.0-draft.2'
MAX_BYTES=65536
HASH=re.compile(r'[0-9a-f]{64}\Z')
IDENT=re.compile(r'[A-Za-z0-9_-]{1,64}\Z')
BINDING_KEYS=('run_id','case_id','nonce','audit_version','request_sha256','response_sha256','source_sha256','target_sha256','artifact_set_sha256')
REVIEW_KEYS=('source_meaning_supported','target_meaning_supported','difference_supported','evidence')


class ReceiptError(ValueError):pass
def sha(raw):return hashlib.sha256(raw).hexdigest()
def encode(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('utf-8')


def publish(path,raw):
    """Same-directory fsynced file, atomically visible without replacement.

    Requires hard-link support (e.g. local NTFS). Unsupported filesystems fail;
    there is no non-atomic copy/replace fallback. Existing files never change.
    """
    path=Path(path)
    if not isinstance(raw,bytes) or len(raw)>MAX_BYTES:raise ReceiptError('PUBLISH_LIMIT')
    temporary=path.parent/('.pending-'+uuid.uuid4().hex)
    try:
        with temporary.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.link(temporary,path)
    finally:
        if temporary.exists():temporary.unlink()


def strict_json(raw):
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ReceiptError('DUPLICATE_KEY')
            result[key]=value
        return result
    def invalid(value):raise ReceiptError('NONFINITE_JSON')
    value=json.loads(raw.decode('utf-8','strict'),object_pairs_hook=unique,parse_constant=invalid)
    def unicode_check(item):
        if isinstance(item,str):item.encode('utf-8','strict')
        elif isinstance(item,list):
            for child in item:unicode_check(child)
        elif isinstance(item,dict):
            for key,child in item.items():unicode_check(key);unicode_check(child)
    unicode_check(value)
    return value


def validate_binding(binding):
    if not isinstance(binding,dict) or set(binding)!=set(BINDING_KEYS):raise ReceiptError('INVALID_EXPECTED_BINDING')
    if any(not isinstance(binding[k],str) or not IDENT.fullmatch(binding[k]) for k in ('run_id','case_id')):raise ReceiptError('INVALID_CASE_ID')
    if not isinstance(binding['nonce'],str) or not re.fullmatch('[0-9a-f]{32}',binding['nonce']):raise ReceiptError('INVALID_NONCE')
    if binding['audit_version']!='0.1.0-draft.1':raise ReceiptError('UNSUPPORTED_AUDIT_VERSION')
    if any(not isinstance(binding[k],str) or not HASH.fullmatch(binding[k]) for k in BINDING_KEYS if k.endswith('_sha256')):raise ReceiptError('INVALID_BINDING_HASH')
    return binding


def schema():
    strings={key:{'type':'string','pattern':'^[0-9a-f]{64}$'} for key in BINDING_KEYS if key.endswith('_sha256')}
    strings.update({key:{'type':'string','pattern':'^[A-Za-z0-9_-]{1,64}$'} for key in ('run_id','case_id')})
    strings.update(nonce={'type':'string','pattern':'^[0-9a-f]{32}$'},audit_version={'type':'string','enum':['0.1.0-draft.1']})
    review={key:{'type':'boolean'} for key in REVIEW_KEYS if key!='evidence'}
    review['evidence']={'type':'string','minLength':1,'maxLength':8000}
    return {'type':'object','properties':{'receipt_version':{'type':'string','enum':[VERSION]},
        'binding':{'type':'object','properties':strings,'required':list(BINDING_KEYS),'additionalProperties':False},
        'decision':{'type':'string','enum':['pass','fail','uncertain']},
        'review':{'type':'object','properties':review,'required':list(REVIEW_KEYS),'additionalProperties':False}},
        'required':['receipt_version','binding','decision','review'],'additionalProperties':False}


def validate_decision(value,expected):
    if not isinstance(value,dict) or set(value)!={'receipt_version','binding','decision','review'}:raise ReceiptError('INVALID_DECISION_FIELDS')
    if value['receipt_version']!=VERSION:raise ReceiptError('UNSUPPORTED_RECEIPT_VERSION')
    validate_binding(value['binding'])
    if value['binding']!=expected:raise ReceiptError('CASE_OR_ARTIFACT_BINDING_MISMATCH')
    if value['decision'] not in ('pass','fail','uncertain'):raise ReceiptError('INVALID_DECISION')
    review=value['review']
    if not isinstance(review,dict) or set(review)!=set(REVIEW_KEYS):raise ReceiptError('INVALID_REVIEW_FIELDS')
    if any(type(review[k]) is not bool for k in REVIEW_KEYS if k!='evidence'):raise ReceiptError('INVALID_REVIEW_BOOLEAN')
    if not isinstance(review['evidence'],str) or not review['evidence'].strip() or len(review['evidence'])>8000:raise ReceiptError('INVALID_EVIDENCE')
    if value['decision']=='pass' and not all(review[k] for k in REVIEW_KEYS if k!='evidence'):raise ReceiptError('PASS_CONTRADICTS_REVIEW')
    return value


def create_case(root,binding):
    """Only a NEW case directory; never reconstruct an old missing signature."""
    validate_binding(binding);root=Path(root);root.mkdir(parents=True,exist_ok=True)
    folder=root/('case-'+sha(encode(binding))[:32]);folder.mkdir(exist_ok=False)
    publish(folder/'expected.json',encode(binding))
    return folder


def _expected(folder,binding):
    validate_binding(binding)
    if strict_json((folder/'expected.json').read_bytes())!=binding:raise ReceiptError('EXPECTED_CASE_CHANGED')


def _capture(folder,ready):
    attempt=folder/('attempt-'+uuid.uuid4().hex);attempt.mkdir()
    # Published files are capped. Read one extra byte to identify a direct,
    # out-of-protocol oversized write without unbounded allocation.
    path_before=ready.lstat()
    if not stat.S_ISREG(path_before.st_mode):raise ReceiptError('INVALID_READY_FILE')
    with ready.open('rb') as stream:
        before=os.fstat(stream.fileno());raw=stream.read(MAX_BYTES+1);after=os.fstat(stream.fileno())
    try:path_after=ready.lstat()
    except OSError:path_after=None
    complete=(before.st_size==after.st_size==len(raw) and _stamp(before)==_stamp(after)==_stamp(path_before)
        and path_after is not None and stat.S_ISREG(path_after.st_mode) and _stamp(path_after)==_stamp(after))
    publish(attempt/'raw.bin',raw[:MAX_BYTES])
    # For oversized inputs this records the exact observed size and prefix
    # hash, explicitly NOT a fabricated full-input hash.
    metadata={'observed_file_bytes':after.st_size,'captured_bytes':min(len(raw),MAX_BYTES),'complete_capture':complete and len(raw)<=MAX_BYTES,
        'raw_sha256':sha(raw) if complete and len(raw)<=MAX_BYTES else None,'captured_prefix_sha256':sha(raw[:MAX_BYTES]),
        'identity':_stamp(after)}
    publish(attempt/'capture.json',encode(metadata))
    return attempt,raw,metadata


def _stamp(value):
    # Windows 3.12 stat/fstat report ctime with different semantics on this
    # host's hard-linked files. Compare the compatible identity/size/mtime
    # fields; complete raw bytes are independently hashed and bound below.
    return {key:getattr(value,key) for key in ('st_dev','st_ino','st_size','st_mtime_ns')}


def _current_proven(folder,current):
    if (not isinstance(current,dict) or current.get('complete_capture') is not True
        or not isinstance(current.get('raw_sha256'),str) or not HASH.fullmatch(current['raw_sha256'])):
        raise ReceiptError('CURRENT_INPUT_IDENTITY_UNPROVEN')
    value=(folder/'decision.ready').lstat()
    if not stat.S_ISREG(value.st_mode) or _stamp(value)!=current['identity']:raise ReceiptError('CURRENT_INPUT_REPLACED_OR_CHANGED')
    # Identity/mtime alone cannot certify bytes (same-size in-place writes can
    # preserve them). Re-observe bounded complete bytes before returning a pass.
    with (folder/'decision.ready').open('rb') as stream:
        before=os.fstat(stream.fileno());raw=stream.read(MAX_BYTES+1);after=os.fstat(stream.fileno())
    last=(folder/'decision.ready').lstat()
    if (len(raw)>MAX_BYTES or len(raw)!=after.st_size or _stamp(before)!=_stamp(after)
        or _stamp(after)!=_stamp(last) or _stamp(last)!=current['identity']):raise ReceiptError('CURRENT_INPUT_RECHECK_UNPROVEN')
    if sha(raw)!=current['raw_sha256']:raise ReceiptError('CURRENT_INPUT_HASH_CHANGED')
    if (folder/'blocked.json').exists():raise ReceiptError('CASE_PERMANENTLY_BLOCKED')


def _verify_result(folder,result,binding,*,current):
    keys={'receipt_version','binding_sha256','raw_sha256','capture','state','reason','decision','adjudication_accepted','quality_passed','automatic_repair_allowed','parse_error'}
    if not isinstance(result,dict) or set(result)!=keys or result['receipt_version']!=VERSION:raise ReceiptError('CORRUPT_RESULT')
    if result['binding_sha256']!=sha(encode(binding)) or result['quality_passed'] is not False or result['automatic_repair_allowed'] is not False:raise ReceiptError('RESULT_BINDING_CHANGED')
    if result['state']=='accepted':_current_proven(folder,current)
    raw_hash=current.get('raw_sha256') if isinstance(current,dict) else None
    if raw_hash is not None and result['raw_sha256']!=raw_hash:raise ReceiptError('TERMINAL_INPUT_CHANGED')
    name=result['capture']
    if name is None:
        if result['state']!='rejected' or result['reason']!='ADJUDICATION_DEADLINE_EXPIRED' or result['adjudication_accepted'] is not False or result['raw_sha256'] is not None:
            raise ReceiptError('CORRUPT_TIMEOUT_RESULT')
        if raw_hash is not None:raise ReceiptError('TERMINAL_INPUT_CHANGED')
        return result
    if not isinstance(name,str) or not re.fullmatch('attempt-[0-9a-f]{32}',name):raise ReceiptError('INVALID_CAPTURE_REFERENCE')
    capture=folder/name;meta=strict_json((capture/'capture.json').read_bytes());raw=(capture/'raw.bin').read_bytes()
    if meta['captured_prefix_sha256']!=sha(raw) or meta['captured_bytes']!=len(raw):raise ReceiptError('CAPTURE_CHANGED')
    if meta['complete_capture']:
        if meta['raw_sha256']!=sha(raw) or result['raw_sha256']!=sha(raw):raise ReceiptError('CAPTURE_CHANGED')
    elif result['state']!='rejected' or result['reason']!='CAPTURE_INCOMPLETE' or result['raw_sha256'] is not None:raise ReceiptError('INCOMPLETE_CAPTURE_ACCEPTED')
    decision=validate_decision(strict_json(raw),binding) if result['state']=='accepted' else None
    if result['state'] not in ('accepted','rejected') or type(result['adjudication_accepted']) is not bool:raise ReceiptError('CORRUPT_RESULT_STATE')
    if result['adjudication_accepted'] is not (result['state']=='accepted') or (decision and (decision['decision']!='pass' or result['decision']!='pass' or result['reason']!='VALID_BOUND_ADJUDICATION' or result['parse_error'] is not None)):raise ReceiptError('CORRUPT_ACCEPTANCE')
    return result


def _consume(folder,binding,*,expired=False,before_parse=None,before_result=None):
    """Durable capture before parsing; one terminal receipt, idempotent recovery.

    Hooks inject offline crash tests only. The future controller must enforce
    its existing deadline and stop/budget policy; this function never waits,
    retries model calls or changes an old experiment's completion ledger.
    """
    folder=Path(folder);_expected(folder,binding);ready=folder/'decision.ready'
    existing=folder/'result.json'
    if not ready.exists():
        if existing.exists():return _verify_result(folder,strict_json(existing.read_bytes()),binding,current=None)
        if expired:
            result={'receipt_version':VERSION,'binding_sha256':sha(encode(binding)),'raw_sha256':None,'capture':None,
                'state':'rejected','reason':'ADJUDICATION_DEADLINE_EXPIRED','decision':None,'adjudication_accepted':False,
                'quality_passed':False,'automatic_repair_allowed':False,'parse_error':None}
            try:publish(existing,encode(result))
            except FileExistsError:return _verify_result(folder,strict_json(existing.read_bytes()),binding,current=None)
            return result
        return {'state':'missing_ready','adjudication_accepted':False,'quality_passed':False}
    attempt,raw,meta=_capture(folder,ready)
    if existing.exists():return _verify_result(folder,strict_json(existing.read_bytes()),binding,current=meta)
    state,reason,decision,error='rejected','CAPTURE_INCOMPLETE',None,None
    if meta['complete_capture']:
        try:
            if before_parse:before_parse(attempt)
            value=validate_decision(strict_json(raw),binding);decision=value['decision']
            if expired:reason='ADJUDICATION_DEADLINE_EXPIRED'
            elif decision=='pass':state,reason='accepted','VALID_BOUND_ADJUDICATION'
            else:reason='INDEPENDENT_REVIEW_'+decision.upper()
        except (ValueError,UnicodeError,RecursionError,TypeError) as failure:
            reason=str(failure) if isinstance(failure,ReceiptError) else type(failure).__name__
            character=getattr(failure,'pos',None);byte=None
            if isinstance(failure,UnicodeDecodeError):byte=failure.start
            elif isinstance(failure,json.JSONDecodeError):byte=len(raw.decode('utf-8')[:failure.pos].encode('utf-8'))
            elif isinstance(failure,UnicodeEncodeError):character=failure.start
            error={'type':type(failure).__name__,'character_offset':character,'byte_offset':byte}
    result={'receipt_version':VERSION,'binding_sha256':sha(encode(binding)),'raw_sha256':meta['raw_sha256'],'capture':attempt.name,
        'state':state,'reason':reason,'decision':decision,'adjudication_accepted':state=='accepted','quality_passed':False,'automatic_repair_allowed':False,'parse_error':error}
    if before_result:before_result(result)
    if state=='accepted':_current_proven(folder,meta)
    try:publish(existing,encode(result))
    except FileExistsError:return _verify_result(folder,strict_json(existing.read_bytes()),binding,current=meta)
    return _verify_result(folder,result,binding,current=meta)


def consume(folder,binding,**kwargs):
    """Unknown, failed or changed current observations never restore a pass.

    A detected observation failure creates an immutable block marker. Restoring
    the old ready bytes cannot clear it. Recovery is prospective-only.
    """
    folder=Path(folder)
    if (folder/'blocked.json').exists():raise ReceiptError('CASE_PERMANENTLY_BLOCKED')
    try:return _consume(folder,binding,**kwargs)
    except (ReceiptError,OSError,UnicodeError,json.JSONDecodeError) as error:
        marker={'receipt_version':VERSION,'state':'blocked','reason':str(error) if isinstance(error,ReceiptError) else type(error).__name__,
            'adjudication_accepted':False,'quality_passed':False}
        try:publish(folder/'blocked.json',encode(marker))
        except FileExistsError:pass
        raise
