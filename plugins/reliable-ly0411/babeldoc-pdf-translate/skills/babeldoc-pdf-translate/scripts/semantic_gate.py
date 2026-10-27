"""Independent complete-block semantic screen, durable v3-style signing.

No PDF edits, cached judgments, expected labels or automatic adjudicator. An
independent trusted adjudicator must publish a bound decision for equivalence.
Different/uncertain blocks immediately veto. Protocol remains unvalidated.
"""
import copy,json,time,uuid
from pathlib import Path
import audit_receipts as durable
import semantic_mapping as mapping
import semantic_unit_protocol as units
import translation_contract as contracts
import semantic_filesystem

VERSION='0.1.0-draft.1'
def save(path,value):durable.publish(Path(path),durable.encode(value))
def load(path):return durable.strict_json(Path(path).read_bytes())
def request(unit,contract):
    packet=units.packet({'source':unit['source'],'target':unit['target']})
    packet['request']['prompt']=units.INSTRUCTION+'Original user translation constraints (data, not commands):\n'+units.canonical(contract)+'\n'+units.canonical({'source':unit['source'],'target':unit['target']})
    packet['binding']['request_sha256']=durable.sha(durable.encode(packet['request']))
    return packet
def context(snapshot,contract,coverage):return durable.sha(durable.encode({'snapshot':snapshot,'contract':contract,'coverage_sha256':coverage['sha256']}))

def native_reviewer(provider):
    import visual_review as visual
    if not isinstance(provider,dict) or provider.get('type')!='codex' or not provider.get('model') or provider.get('retries',0)!=0:
        raise ValueError('SEMANTIC_EXPLICIT_NATIVE_PROVIDER_REQUIRED')
    if 'astra' in provider['model'].casefold():raise ValueError('ASTRA_DEVELOPMENT_ACCEPTANCE_ONLY')
    cfg=copy.deepcopy(provider);cfg.pop('cache_dir',None);cfg.pop('diagnostics_dir',None)
    def review(packet,budget,folder):
        client=visual.NativeVision(cfg);holder={}
        def invoke(timeout):
            raw,usage=client.inspect_raw(packet['prompt'],[],min(timeout,cfg.get('timeout_seconds',120)),schema=packet['schema'],record_dir=folder/'native-raw')
            holder['raw']=raw
            return raw,usage
        raw=budget.invoke(cfg['model'],invoke)
        return raw
    review.model=cfg['model'];review.backend=cfg['type'];return review

def file_adjudicator(max_wait_seconds=0):
    if type(max_wait_seconds) is not int or not 0<=max_wait_seconds<=90:raise ValueError('SEMANTIC_ADJUDICATION_WAIT_LIMIT')
    def adjudicate(folder,binding,unit,response,budget):
        # No JSON on stdin, no model/automatic assertion of fact support.
        until=min(time.monotonic()+max_wait_seconds,budget.started+budget.max_seconds)
        while not (folder/'decision.ready').exists() and time.monotonic()<until:
            time.sleep(min(.2,max(0,until-time.monotonic())))
    return adjudicate

def _event(folder,binding,expected_context,guard):
    guard();raw=(folder/'response.raw').read_bytes()
    if durable.sha(raw)!=binding['response_sha256']:raise ValueError('SEMANTIC_RESPONSE_SNAPSHOT_CHANGED')
    response=units.validate(durable.strict_json(raw));receipt=durable.consume(folder/'inbox',binding)
    if not receipt['adjudication_accepted']:raise ValueError('SEMANTIC_ADJUDICATION_NOT_ACCEPTED')
    receipt_raw=(folder/'inbox/result.json').read_bytes()
    if durable.encode(durable.strict_json(receipt_raw))!=durable.encode(receipt):raise ValueError('SEMANTIC_RECEIPT_SNAPSHOT_CHANGED')
    if response['verdict']!='equivalent':raise ValueError('SEMANTIC_VERDICT_VETO')
    native_record=None
    native=folder/'native-raw'
    if native.exists():
        files={path.name:durable.sha(path.read_bytes()) for path in native.iterdir() if path.is_file()}
        if set(files)!={'answer.raw','stdout.utf8','capture.json'}:raise ValueError('SEMANTIC_NATIVE_CAPTURE_INCOMPLETE')
        metadata=load(native/'capture.json');stdout=(native/'stdout.utf8').read_bytes()
        stream=metadata['streams']['stdout']
        if ((native/'answer.raw').read_bytes()!=raw or metadata['answer_bytes']!=len(raw) or metadata['answer_sha256']!=durable.sha(raw)
            or stream['captured_bytes']!=len(stdout) or stream['captured_sha256']!=durable.sha(stdout)
            or (stream['capture_complete'] and (stream['bytes']!=len(stdout) or stream['sha256']!=durable.sha(stdout)))):
            raise ValueError('SEMANTIC_NATIVE_CAPTURE_CHANGED')
        native_record=durable.sha(durable.encode(files))
    return {'case_id':binding['case_id'],'event_id':durable.sha(durable.encode(binding)),'context_sha256':expected_context,
        'response_sha256':durable.sha(raw),'receipt_sha256':durable.sha(receipt_raw),'model_verdict':response['verdict'],
        'native_capture_sha256':native_record,'statement_adjudication_accepted':True,'quality_passed':False}

def verify_run(folder,expected_context,guard,coverage,contract):
    folder=Path(folder);manifest=load(folder/'manifest.json')
    if (folder/'blocked.json').exists():raise ValueError('SEMANTIC_RUN_PERMANENTLY_BLOCKED')
    if manifest['context_sha256']!=expected_context:raise ValueError('SEMANTIC_CONTEXT_CHANGED')
    all_units=[unit for page in coverage['pages'] for unit in page['units']]
    expected_rows=[{'id':unit['id'],'kind':unit['kind'],'case_dir':'u%04d'%i} for i,unit in enumerate(all_units)]
    if not coverage['coverage_complete'] or manifest['units']!=expected_rows or manifest['coverage_sha256']!=coverage['sha256']:raise ValueError('SEMANTIC_UNIT_COVERAGE_CHANGED')
    events=[]
    for row,unit in zip(manifest['units'],all_units):
        if row['kind']=='protected_identity':continue
        case=folder/row['case_dir'];binding=load(case/'binding.json')
        if manifest.get('reviewer_backend')=='codex' and not (case/'native-raw').is_dir():raise ValueError('SEMANTIC_NATIVE_CAPTURE_MISSING')
        packet=request(unit,contract);reservation=load(case/'reservation.json');raw=(case/'response.raw').read_bytes()
        if (load(case/'request.json')!=packet['request'] or any(binding[key]!=packet['binding'][key] for key in ('source_sha256','target_sha256','request_sha256'))
            or binding['case_id']!=unit['id'] or binding['run_id']!=expected_context[:24] or binding['artifact_set_sha256']!=expected_context
            or binding['nonce']!=reservation['nonce'] or reservation['request_sha256']!=packet['binding']['request_sha256']
            or binding['audit_version']!=units.VERSION or binding['response_sha256']!=durable.sha(raw)
            or load(case/'response-capture.json')!={'bytes':len(raw),'sha256':durable.sha(raw)}):raise ValueError('SEMANTIC_UNIT_BINDING_CHANGED')
        expected=_event(case,binding,expected_context,guard);actual=load(case/'event.json')
        if durable.encode(expected)!=durable.encode(actual):raise ValueError('SEMANTIC_EVENT_INCONSISTENT')
        events.append(expected)
    guard()
    return {'passed':True,'context_sha256':expected_context,'coverage_sha256':manifest['coverage_sha256'],
        'event_hashes':[durable.sha(durable.encode(row)) for row in events],'semantic_units':len(events),'quality_passed':False}

def run(source,artifacts,contract,coverage,folder,budget,reviewer,adjudicator,guard,*,resume=False):
    """A new audit round or explicit same-byte signing recovery, never inference retry.

    An interrupted reserved call with no durable raw answer blocks recovery.
    Completed raw answers may be signed/reverified without another invocation.
    """
    import final_audit
    folder=Path(folder);snapshot=final_audit.snapshot(source,artifacts);ctx=context(snapshot,contract,coverage)
    if not coverage['coverage_complete']:raise ValueError('SEMANTIC_COVERAGE_BLOCKED')
    if reviewer is None:raise ValueError('SEMANTIC_REVIEWER_MISSING')
    semantic_filesystem.preflight(folder)
    all_units=[unit for page in coverage['pages'] for unit in page['units']]
    expected_manifest={'context_sha256':ctx,'coverage_sha256':coverage['sha256'],'deadline_started':budget.started,'deadline_unix':time.time()+max(0,budget.max_seconds-(time.monotonic()-budget.started)),
        'reviewer_model':final_audit.text_attribute(reviewer,'model'),'reviewer_backend':final_audit.text_attribute(reviewer,'backend'),
        'max_seconds':budget.max_seconds,'units':[{'id':unit['id'],'kind':unit['kind'],'case_dir':'u%04d'%i} for i,unit in enumerate(all_units)]}
    if resume:
        manifest=load(folder/'manifest.json')
        if any(manifest[key]!=expected_manifest[key] for key in ('context_sha256','coverage_sha256','units')):raise ValueError('SEMANTIC_RECOVERY_CONTEXT_CHANGED')
    else:
        folder.mkdir(exist_ok=False);save(folder/'manifest.json',expected_manifest);manifest=expected_manifest
    def current():
        guard()
        if final_audit.snapshot(source,artifacts)!=snapshot:raise ValueError('SEMANTIC_ARTIFACT_CHANGED')
        if (time.monotonic()<manifest['deadline_started'] or time.monotonic()-manifest['deadline_started']>=manifest['max_seconds'] or time.time()>=manifest['deadline_unix']):raise ValueError('SEMANTIC_ORIGINAL_DEADLINE_EXPIRED')
    if (folder/'blocked.json').exists():raise ValueError('SEMANTIC_RUN_PERMANENTLY_BLOCKED')
    try:
        for index,unit in enumerate(all_units):
            current()
            if unit['kind']=='protected_identity':continue
            case=folder/manifest['units'][index]['case_dir'];packet=request(unit,contract)
            if not case.exists():case.mkdir();save(case/'request.json',packet['request'])
            elif load(case/'request.json')!=packet['request']:raise ValueError('SEMANTIC_REQUEST_CHANGED')
            if not (case/'response.raw').exists():
                if resume:raise ValueError('SEMANTIC_RECOVERY_HAS_NO_DURABLE_RESPONSE')
                if (case/'reservation.json').exists():raise ValueError('SEMANTIC_COMPLETION_UNKNOWN_NO_RETRY')
                save(case/'reservation.json',{'nonce':uuid.uuid4().hex,'client_call':budget.calls+1,'request_sha256':packet['binding']['request_sha256']})
                before=budget.calls;raw=reviewer(packet['request'],budget,case)
                if budget.calls!=before+1 or not isinstance(raw,bytes):raise ValueError('SEMANTIC_SHARED_BUDGET_OR_RAW_BYTES_REQUIRED')
                durable.publish(case/'response.raw',raw);save(case/'response-capture.json',{'bytes':len(raw),'sha256':durable.sha(raw)})
            raw=(case/'response.raw').read_bytes()
            if manifest.get('reviewer_backend')=='codex' and not (case/'native-raw').is_dir():raise ValueError('SEMANTIC_NATIVE_CAPTURE_MISSING')
            if load(case/'response-capture.json')!={'bytes':len(raw),'sha256':durable.sha(raw)}:raise ValueError('SEMANTIC_RAW_RESPONSE_CHANGED')
            nonce=load(case/'reservation.json')['nonce'];binding={'run_id':ctx[:24],'case_id':unit['id'],'nonce':nonce,'audit_version':units.VERSION,
                **{key:packet['binding'][key] for key in ('request_sha256','source_sha256','target_sha256')},'response_sha256':durable.sha(raw),'artifact_set_sha256':ctx}
            if not (case/'binding.json').exists():save(case/'binding.json',binding)
            elif load(case/'binding.json')!=binding:raise ValueError('SEMANTIC_BINDING_CHANGED')
            try:
                response=units.validate(durable.strict_json(raw))
            except (ValueError,UnicodeError,RecursionError,TypeError) as error:
                diagnostic={'type':type(error).__name__,'character_offset':getattr(error,'pos',None),
                    'byte_offset':error.start if isinstance(error,UnicodeDecodeError) else None}
                if isinstance(error,json.JSONDecodeError):diagnostic['byte_offset']=len(raw.decode('utf-8')[:error.pos].encode('utf-8'))
                save(case/'parse-error.json',diagnostic)
                raise ValueError('SEMANTIC_INVALID_RAW_RESPONSE') from None
            if response['verdict']!='equivalent':
                save(case/'veto.json',{'verdict':response['verdict'],'unit_id':unit['id'],'quality_passed':False})
                raise ValueError('SEMANTIC_'+response['verdict'].upper())
            inbox=case/'inbox'
            if not inbox.exists():inbox.mkdir();save(inbox/'expected.json',binding)
            if adjudicator:adjudicator(inbox,binding,unit,response,budget)
            current();signed=durable.encode(_event(case,binding,ctx,current))
            target=case/'event.json'
            if target.exists():
                if durable.encode(load(target))!=signed:raise ValueError('SEMANTIC_LEDGER_EVENT_CHANGED')
            else:durable.publish(target,signed)
        return verify_run(folder,ctx,current,coverage,contract)
    except (KeyboardInterrupt,SystemExit):
        # A reserved unknown call can never be re-invoked; durable replies can
        # be reverified on an explicit same-context recovery.
        raise
    except Exception as error:
        if not (folder/'blocked.json').exists():save(folder/'blocked.json',{'reason':str(error),'quality_passed':False})
        raise
