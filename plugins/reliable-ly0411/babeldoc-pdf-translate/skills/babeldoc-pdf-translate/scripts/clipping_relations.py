"""Describe clipping provenance without waiving an ink/visibility guard.

Same native paint attributes are only an inspectable correspondence candidate.
Explicit caller-supplied object links are trusted lineage input, not factual or
cryptographic authentication. Neither kind of link certifies visible damage.
"""
from collections import defaultdict
import math

VERSION='0.1.0-draft.1'
ACTIVE={'visible_candidate','partially_clipped'}


def signature(g):
    if g.get('shape') is None or g.get('clip_uncertain') or g.get('group_uncertain'):return None
    return (g['shape'],g['unicode'],g['size'],tuple(g['origin']),tuple(g['ink_bbox']),
        tuple(g['clip_bbox']),g['paint_type'],tuple(g['color']),g['opacity'])


def outside(g):
    a,b=g['ink_bbox'],g['clip_bbox']
    values=[max(0,b[0]-a[0]),max(0,b[1]-a[1]),max(0,a[2]-b[2]),max(0,a[3]-b[3])]
    if not all(math.isfinite(v) for v in values):raise ValueError('NONFINITE_CLIPPING_BOUNDS')
    return {'left_pt':values[0],'top_pt':values[1],'right_pt':values[2],'bottom_pt':values[3]}


def describe(source,target,*,glyph_links=None):
    """Return source-input properties separately from target-side risks.

    No epsilon, canonical-mask equality, original clipping or supplied link
    changes coverage_complete. Unlinked translated glyphs remain unclassified
    as to whether their clipping was newly introduced by the writer.
    """
    a={g['id']:g for g in source['glyphs'] if g['visibility'] in ACTIVE and not g.get('logical_only')}
    b={g['id']:g for g in target['glyphs'] if g['visibility'] in ACTIVE and not g.get('logical_only')}
    links={};used=set()
    if glyph_links is not None:
        if not isinstance(glyph_links,list):raise ValueError('INVALID_CLIPPING_LINEAGE')
        for pair in glyph_links:
            if (not isinstance(pair,list) or len(pair)!=2 or any(not isinstance(x,str) for x in pair)
                or pair[0] not in a or pair[1] not in b
                or pair[0] in used or pair[1] in links):raise ValueError('INVALID_CLIPPING_LINEAGE')
            used.add(pair[0]);links[pair[1]]=pair[0]
    by_signature=defaultdict(list)
    for g in a.values():
        key=signature(g)
        if key is not None:by_signature[key].append(g['id'])
    def row(g):
        return {'glyph_id':g['id'],'unicode':g['unicode'],'ink_bbox':g['ink_bbox'],'clip_bbox':g['clip_bbox'],
            'outside_native_bounds':outside(g),'clip_ink_evidence':g.get('clip_ink_evidence'),
            'acceptance':'Unresolved clipping evidence; never a waiver.'}
    sources=[{**row(g),'classification':'source_input_clipping'} for g in a.values() if g['visibility']=='partially_clipped']
    targets=[]
    for g in b.values():
        if g['visibility']!='partially_clipped':continue
        record=row(g);key=signature(g);candidates=by_signature.get(key,[]) if key is not None else []
        linked=a.get(links.get(g['id']));record['caller_lineage_supplied']=linked is not None
        record['source_candidate_ids']=candidates
        if key is None:kind='unsupported_or_unavailable_identity'
        elif linked is not None:
            record['linked_source_id']=linked['id']
            if linked['visibility']=='partially_clipped' and signature(linked)==key:kind='inherited_clipping_with_caller_link'
            elif linked['visibility']=='visible_candidate':kind='target_clipping_after_unclipped_source_with_caller_link'
            else:kind='changed_clipping_with_caller_link'
        elif len(candidates)==1:kind='unchanged_native_clipping_signature_lineage_unverified'
        elif len(candidates)>1:kind='ambiguous_source_clipping_correspondence'
        else:kind='target_clipping_origin_unverified'
        record['classification']=kind;targets.append(record)
    return {'version':VERSION,'source_input':sources,'target_risks':targets,'coverage_waiver':False,
        'scope':'Native bounds and finite mask evidence; no claim of exact outline equivalence or perceptible clipping damage.'}
