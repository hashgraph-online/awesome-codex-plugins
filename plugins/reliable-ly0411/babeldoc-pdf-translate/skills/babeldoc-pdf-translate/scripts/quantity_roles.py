"""Explicit source-role confirmations, never inferred from model/grammar output.

These records bind a trusted caller's independent semantic confirmation to
source bytes, physical page, region, text range and actual glyphs. Hashes bind
content; they do not authenticate a person or prove the confirmation is true.
No production path creates a confirmation automatically. Unknown mathematical
objects/fonts remain protected even when a role is confirmed.
"""
import hashlib
import json
from pathlib import Path

import pymupdf as fitz

VERSION = "1.0.0-draft.1"
AUTHORITY = "operator_confirmed_prose_quantity"


def digest(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()


def confirm_from_operator(source,physical_page,region_id,left_word,*,reason,occurrence=0):
    """Record independent confirmation that this word is prose before a scalar.

    Calling this function asserts caller knowledge; parsing does NOT establish
    that knowledge. Tests use declared positive-control intent as their oracle.
    This helper is deliberately absent from model/config schemas and CLI.
    """
    import repair_objects
    import visual_review
    if (type(physical_page) is not int or physical_page<1 or type(occurrence) is not int or occurrence<0
        or not isinstance(reason,str) or not reason.strip() or len(reason)>2000):
        raise ValueError('INVALID_INDEPENDENT_QUANTITY_ROLE')
    source=Path(source)
    with fitz.open(source) as doc:
        if physical_page>len(doc):raise ValueError('INVALID_QUANTITY_ROLE_PAGE')
        page=doc[physical_page-1]
        region=next((row for row in visual_review.regions(page) if row['id']==region_id),None)
        if region is None:raise ValueError('UNMAPPED_SOURCE_QUANTITY_ROLE')
        area=fitz.Rect(region['bbox'])+(-1,-1,1,1)
        raw=repair_objects.inspect(page,area)
        matches=[row for row in raw['text_contract']['unresolved_operator_roles'] if row['boundary_text']==left_word]
        if occurrence>=len(matches):raise ValueError('MISSING_AMBIGUOUS_SOURCE_ROLE')
        role=matches[occurrence]
        tail=repair_objects.text_contract(raw['text'][role['operator_start']:])
        first=next((token for token in tail['tokens'] if token['kind']!='space'),None)
        if not first or first['kind']!='decimal' or first.get('literal_role')!='standalone_quantity':
            raise ValueError('ROLE_CONFIRMATION_CANNOT_OVERRIDE_COMPOUND_EXPRESSION')
        record={'version':VERSION,'authority':AUTHORITY,'reason':reason,
            'source_sha256':digest(source.read_bytes()),'physical_page':physical_page,'region_id':region_id,
            'scan_bbox':list(area),'text_sha256':digest(raw['text'].encode()),'glyphs_sha256':raw['glyphs_sha256'],
            'boundary_span':role['boundary_span'],'boundary_text':left_word,'occurrence':occurrence,
            'quantity_identity':first['identity']}
    record['record_sha256']=digest(canonical(record))
    return record


def validate_for_source(source,records):
    if not isinstance(records,(list,tuple)):raise ValueError('INVALID_SOURCE_QUANTITY_ROLES')
    seen=set()
    for record in records:
        if not isinstance(record,dict) or record.get('authority')!=AUTHORITY:
            raise ValueError('UNTRUSTED_QUANTITY_ROLE_AUTHORITY')
        try:
            expected=confirm_from_operator(source,record['physical_page'],record['region_id'],record['boundary_text'],
                reason=record['reason'],occurrence=record['occurrence'])
            identity=(record['physical_page'],record['region_id'],tuple(record['boundary_span']))
        except (KeyError,TypeError,IndexError) as error:
            raise ValueError('INVALID_SOURCE_QUANTITY_ROLE') from error
        if record!=expected or identity in seen:raise ValueError('STALE_OR_UNBOUND_QUANTITY_ROLE')
        seen.add(identity)
    return list(records)


def boundaries(page,area,text,glyphs_sha256,records):
    """Match already source-validated records to exact local glyph evidence."""
    result=[]
    for record in records:
        if (record['physical_page']==page.number+1 and record['scan_bbox']==list(area)
            and record['text_sha256']==digest(text.encode()) and record['glyphs_sha256']==glyphs_sha256):
            start,end=record['boundary_span']
            if text[start:end]==record['boundary_text']:result.append((start,end))
    return result
