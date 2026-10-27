"""Final native-object coverage and legacy block diagnostic helpers.

Geometry proposes correspondence, never semantic equivalence. Every extracted
block is assigned exactly once or the page is blocked; no paper coordinates,
filtering of math-font spans, truncation or fuzzy text recovery is permitted.
"""
from collections import Counter
import hashlib,json,re,unicodedata
import pymupdf as fitz
import prose_completeness

VERSION='0.1.0-draft.1'
MATH_FONT=re.compile(r'CMMI|CMSY|CMEX|MSAM|MSBM|STIX.*Math|MathJax|Symbol',re.I)
CALL=re.compile(r'(?<![A-Za-z])[A-Za-z]{1,4}\([^\n()]{1,50}\)')
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def compact(text):return ''.join(unicodedata.normalize('NFC',text).split())
def inventory(page):
    rows=[];errors=[];seen_spans=set()
    for index,block in enumerate(page.get_text('dict')['blocks']):
        if block['type']!=0:
            errors.append({'code':'UNEXTRACTED_IMAGE_CONTENT','block':index});continue
        lines=[];protected=[]
        for line in block['lines']:
            lines.append(''.join(span['text'] for span in line['spans']))
            for span in line['spans']:
                span_key=(tuple(span['bbox']),span['text'])
                if span['text'].strip() and span_key in seen_spans:errors.append({'code':'DUPLICATE_TEXT_BLOCK','block':index})
                seen_spans.add(span_key)
                if re.search(r'\(cid:\d+\)',span['text']) or any(unicodedata.category(c)=='Cc' and c not in '\t\n\r' for c in span['text']):
                    errors.append({'code':'UNREADABLE_GLYPH','block':index})
                if span['flags']&1 and not MATH_FONT.search(span['font']) and re.search(r'[A-Za-z]{3,}|[\u3400-\u9fff]',span['text']):
                    errors.append({'code':'SUPERSCRIPT_PROVENANCE_REQUIRES_REVIEW','block':index})
                for char in span['text']:
                    name=unicodedata.name(char,'');category=unicodedata.category(char)
                    if char=='\ufffd':errors.append({'code':'UNREADABLE_GLYPH','block':index})
                    if not char.isspace() and (MATH_FONT.search(span['font']) or category in {'Sm','No','Nl'} or 'GREEK' in name or span['flags']&1):
                        protected.append(char)
        text='\n'.join(lines)
        if not text.strip():continue
        for token in CALL.findall(text):protected.append('call:'+compact(token))
        for token in re.findall(r'[+-]?\s*(?:\d+(?:[.,]\d+)*|\.\d+)(?:[eE][+-]?\d+)?',text):
            protected.append('number:'+compact(token))
        row={'id':'block_'+str(index),'bbox':list(block['bbox']),'text':text,'protected':dict(Counter(protected))}
        if any(old['bbox']==row['bbox'] and old['text']==text for old in rows):errors.append({'code':'DUPLICATE_TEXT_BLOCK','block':index})
        rows.append(row)
    if not rows:errors.append({'code':'NO_EXTRACTED_TEXT'})
    return rows,errors
def prose(text):return bool(re.search(r'[A-Za-z]{3,}|[\u3400-\u9fff]{2,}',text))

def page_units(original,target,number,*,chinese=True,max_characters=1200):
    left,errors=inventory(original);right,other=inventory(target);errors+=[{**row,'side':'target'} for row in other]
    nodes=[('source',row) for row in left]+[('target',row) for row in right];links={i:set() for i in range(len(nodes))}
    for i,a in enumerate(left):
        for j,b in enumerate(right,len(left)):
            if (fitz.Rect(a['bbox'])&fitz.Rect(b['bbox'])).get_area()>0:links[i].add(j);links[j].add(i)
    components=[];seen=set()
    for index in range(len(nodes)):
        if index in seen:continue
        pending=[index];component=[]
        while pending:
            at=pending.pop()
            if at in seen:continue
            seen.add(at);component.append(at);pending.extend(links[at]-seen)
        components.append(component)
    units=[]
    for indexes in components:
        source=[row for side,row in (nodes[i] for i in sorted(indexes)) if side=='source']
        translated=[row for side,row in (nodes[i] for i in sorted(indexes)) if side=='target']
        if not source or not translated:
            errors.append({'code':'UNMAPPED_SOURCE_OR_TARGET_BLOCK','page':number,'nodes':[nodes[i][1]['id'] for i in indexes]});continue
        a='\n'.join(row['text'] for row in source);b='\n'.join(row['text'] for row in translated)
        math_a=Counter();math_b=Counter()
        for row in source:math_a.update(row['protected'])
        for row in translated:math_b.update(row['protected'])
        if math_a!=math_b:errors.append({'code':'PROTECTED_MATH_GLYPH_INVENTORY_CHANGED','page':number,
            'source_blocks':[row['id'] for row in source],'target_blocks':[row['id'] for row in translated],
            'source':dict(math_a),'target':dict(math_b)})
        if max(len(a),len(b))>max_characters:errors.append({'code':'COMPLETE_UNIT_TOO_LARGE','page':number})
        exact_english=(compact(a)==compact(b) and not re.search(r'[\u3400-\u9fff]',b) and len(re.findall('[A-Za-z]+',b))>=5)
        if chinese and (exact_english or any(prose_completeness.unchanged_english(a,row['text']) for row in translated)):errors.append({'code':'UNCHANGED_ENGLISH_PROSE','page':number})
        kind='semantic' if prose(a) or prose(b) else 'protected_identity'
        if kind=='protected_identity' and compact(a)!=compact(b):errors.append({'code':'NONPROSE_IDENTITY_UNPROVEN','page':number})
        units.append({'id':'p%03d-u%03d'%(number,len(units)+1),'page':number,'kind':kind,'source':a,'target':b,
            'source_blocks':source,'target_blocks':translated})
    return {'page':number,'source_block_count':len(left),'target_block_count':len(right),'units':units,'errors':errors,
        'coverage_complete':not errors and sum(len(row['source_blocks']) for row in units)==len(left) and sum(len(row['target_blocks']) for row in units)==len(right)}

def legacy_build(source,mono,pages,*,chinese=True):
    if not isinstance(pages,list) or not pages or pages!=sorted(set(pages)):raise ValueError('INVALID_SEMANTIC_SCOPE')
    result=[]
    with fitz.open(source) as original,fitz.open(mono) as translated:
        if len(original)!=len(translated):raise ValueError('SEMANTIC_PAGE_COUNT_CHANGED')
        for number in pages:
            if type(number) is not int or not 1<=number<=len(original):raise ValueError('INVALID_SEMANTIC_PAGE')
            result.append(page_units(original[number-1],translated[number-1],number,chinese=chinese))
    value={'version':VERSION,'translated_pages':pages,'pages':result,'coverage_complete':all(row['coverage_complete'] for row in result),
        'scope':'All extracted blocks in translation scope, grouped by generic overlap components. Geometry is a correspondence candidate; image text, ambiguous/unmapped/oversized units and explicit math loss block. 2D formula equivalence still requires visual and existing mathematical protection.'}
    value['sha256']=digest(value);return value


def build(source,mono,pages,*,chinese=True,context=None,translation_contract=None):
    # Keep the old inventory/page_units API for reproducing archived failures;
    # the delivery path always uses native paints and explicit source roles.
    import semantic_objects
    return semantic_objects.build(source,mono,pages,chinese=chinese,context=context,
        translation_contract=translation_contract)
