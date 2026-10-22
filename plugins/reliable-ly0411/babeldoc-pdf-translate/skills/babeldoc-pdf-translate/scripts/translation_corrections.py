"""Explicit source-bound paragraph corrections applied after immutable base cache.

The file is a separately recorded candidate receipt, never a rewritten native
cache. Applying it makes no model call and never certifies rendered PDF quality.
"""
import hashlib,json,os,re
from pathlib import Path

SHA=re.compile(r'^[0-9a-f]{64}$')


def digest(text):return hashlib.sha256(text.encode()).hexdigest()


def load(path):
    file=Path(path)
    if file.is_symlink() or not file.is_file() or file.stat().st_size>2*1024*1024:
        raise ValueError('INVALID_CORRECTION_FILE')
    if os.name=='posix' and file.stat().st_mode&0o077:raise ValueError('CORRECTIONS_MUST_BE_PRIVATE')
    raw=file.read_bytes();value=json.loads(raw)
    if not isinstance(value,dict) or set(value)!={'version','output_contract','max_corrected_rows','provenance','entries'}:
        raise ValueError('INVALID_CORRECTION_FILE_FIELDS')
    if value['version']!=1 or value['output_contract']!='paragraphs' or type(value['max_corrected_rows']) is not int or not 1<=value['max_corrected_rows']<=8:
        raise ValueError('INVALID_CORRECTION_FILE_VERSION_OR_LIMIT')
    provenance=value['provenance']
    required={'model','reasoning_effort','correction_response_sha256','semantic_recheck_sha256','status'}
    if not isinstance(provenance,dict) or set(provenance)!=required or provenance['status']!='semantic_screened':
        raise ValueError('INVALID_CORRECTION_PROVENANCE')
    if any(not isinstance(provenance[x],str) or not provenance[x].strip() or len(provenance[x])>128 for x in ('model','reasoning_effort')):
        raise ValueError('INVALID_CORRECTION_MODEL')
    if any(not isinstance(provenance[x],str) or not SHA.fullmatch(provenance[x]) for x in ('correction_response_sha256','semantic_recheck_sha256')):
        raise ValueError('INVALID_CORRECTION_RECEIPT_HASH')
    entries=value['entries']
    if not isinstance(entries,list) or not 1<=len(entries)<=8:raise ValueError('INVALID_CORRECTION_ENTRIES')
    seen=set();total=0
    for entry in entries:
        fields={'cache_request_sha256','base_content_sha256','source_rows_sha256','replacements'}
        if not isinstance(entry,dict) or set(entry)!=fields:raise ValueError('INVALID_CORRECTION_ENTRY_FIELDS')
        for name in fields-{'replacements'}:
            if not isinstance(entry[name],str) or not SHA.fullmatch(entry[name]):raise ValueError('INVALID_CORRECTION_BINDING')
        if entry['cache_request_sha256'] in seen:raise ValueError('DUPLICATE_CORRECTION_REQUEST')
        seen.add(entry['cache_request_sha256']);ids=[]
        if not isinstance(entry['replacements'],list) or not entry['replacements']:raise ValueError('EMPTY_CORRECTION_ENTRY')
        for row in entry['replacements']:
            if not isinstance(row,dict) or set(row)!={'id','source_sha256','previous_output_sha256','output'}:
                raise ValueError('INVALID_CORRECTION_ROW_FIELDS')
            if type(row['id']) not in (int,str) or (isinstance(row['id'],str) and not row['id']):raise ValueError('INVALID_CORRECTION_ROW_ID')
            identity=(type(row['id']).__name__,row['id'])
            if identity in ids:raise ValueError('DUPLICATE_CORRECTION_ROW')
            ids.append(identity)
            if any(not isinstance(row[x],str) or not SHA.fullmatch(row[x]) for x in ('source_sha256','previous_output_sha256')):
                raise ValueError('INVALID_CORRECTION_ROW_BINDING')
            if not isinstance(row['output'],str) or not row['output'].strip() or len(row['output'])>16000:
                raise ValueError('INVALID_CORRECTION_TEXT')
            total+=1
    if total>value['max_corrected_rows']:raise ValueError('CORRECTION_ROW_LIMIT')
    return {'data':value,'sha256':hashlib.sha256(raw).hexdigest()}


def apply(plan,key,request,content,identifiers=(),*,paragraphs=False):
    import chat_bridge as bridge
    entry=next((x for x in plan['data']['entries'] if x['cache_request_sha256']==key),None)
    if entry is None:return content,0
    if not paragraphs:raise ValueError('CORRECTIONS_REQUIRE_PARAGRAPH_CONTRACT')
    batch=bridge.translation_batch(request)
    if batch is None:raise ValueError('CORRECTIONS_REQUIRE_BATCH_SOURCE')
    sources=batch[2]
    if digest(content)!=entry['base_content_sha256'] or digest(bridge.canonical(sources))!=entry['source_rows_sha256']:
        raise ValueError('CORRECTION_BASE_OR_SOURCE_CHANGED')
    output=json.loads(content)
    source_by_id={(type(x['id']).__name__,x['id']):x['input'] for x in sources}
    target_by_id={(type(x['id']).__name__,x['id']):x for x in output}
    for corrected in entry['replacements']:
        identity=(type(corrected['id']).__name__,corrected['id'])
        if identity not in source_by_id or identity not in target_by_id:raise ValueError('CORRECTION_UNKNOWN_ROW')
        old=target_by_id[identity]
        if digest(source_by_id[identity])!=corrected['source_sha256'] or digest(old['output'])!=corrected['previous_output_sha256']:
            raise ValueError('CORRECTION_ROW_SOURCE_OR_TARGET_CHANGED')
        old['output']=corrected['output']
    changed=bridge.canonical(output)
    bridge.checked_content(changed,request,identifiers,paragraphs=True)
    return changed,len(entry['replacements'])
