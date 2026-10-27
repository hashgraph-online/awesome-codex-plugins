"""Answer-isolated semantic control construction and scoring; never invokes tools."""
import random
import semantic_review as semantic
import semantic_relations as relations
import source_repair


def validate_payload(pairs):
    semantic.checked_pairs(pairs);sources=[source_repair.prose_signature(row['source']) for row in pairs.values()]
    if any(not x for x in sources) or len(set(sources))!=len(sources):raise ValueError('BLIND_SAME_SOURCE_ALTERNATIVES_FORBIDDEN')
    return pairs


def build_arms(cases,seed):
    if not isinstance(cases,list) or not 4<=len(cases)<=64 or len(cases)%2:raise ValueError('INVALID_BLIND_CONTROL_COUNT')
    ids=[c['id'] for c in cases]
    if len(set(ids))!=len(ids) or any(c['good']==c['bad'] for c in cases):raise ValueError('INVALID_BLIND_CONTROLS')
    validate_payload({'pair_'+str(i):{'source':c['source'],'target':c['good']} for i,c in enumerate(cases)})
    rng=random.Random(seed);bad=set(rng.sample(ids,len(ids)//2));arms={};evaluation={}
    for name in ('A','B'):
        ordered=list(cases);rng.shuffle(ordered);aliases=rng.sample(range(100000,999999),len(cases));pairs={};truth={}
        for case,alias in zip(ordered,aliases):
            key='pair_'+str(alias);which='bad' if (case['id'] in bad)==(name=='A') else 'good'
            pairs[key]={'source':case['source'],'target':case[which]}
            truth[key]={'case_id':case['id'],'expected':'different' if which=='bad' else 'equivalent','kind':case.get('kind','control')}
        arms[name]=validate_payload(pairs);evaluation[name]=truth
    return arms,evaluation


def model_payload(pairs):
    validate_payload(pairs)
    return {'protocol':relations.PROTOCOL,'prompt':relations.prompt(pairs),'schema':relations.schema(pairs)}


def score(review,pairs,evaluation):
    semantic.checked(review,pairs)
    if set(evaluation)!=set(pairs) or any(x['expected'] not in {'different','equivalent'} for x in evaluation.values()):raise ValueError('INVALID_BLIND_EVALUATION')
    result={'pairs':len(pairs),'true_positive':0,'true_negative':0,'false_negative':0,'false_positive':0,'uncertain':0}
    for key,row in review['pairs'].items():
        actual=row['status'];expected=evaluation[key]['expected']
        if actual=='uncertain':result['uncertain']+=1
        elif expected=='different':result['true_positive' if actual=='different' else 'false_negative']+=1
        else:result['true_negative' if actual=='equivalent' else 'false_positive']+=1
    result['pilot_passed']=not any(result[k] for k in ('false_negative','false_positive','uncertain'))
    result['quality_passed']=False
    result['scope']='Control-set result only; not population accuracy, rendered PDF acceptance or cold-start evidence.'
    return result
