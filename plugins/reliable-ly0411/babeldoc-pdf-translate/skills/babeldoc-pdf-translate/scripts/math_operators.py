"""Read-only audits for delimited inline Roman math calls, not prose words.

Support is deliberately limited to tested max/min/sin/log calls with a nearby
original math-font argument. Unknown fonts/2-D or unclosed arguments are not
mathematical equivalence evidence. Coordinates are read from the PDFs only.
"""
from collections import Counter
import re
import unicodedata
import pymupdf as fitz

OPERATORS=('max','min','sin','log')
MATH_FONT=re.compile(r'^(?:[A-Z]{6}\+)?(?:CM|MSAM|MSBM|STIX|Math|Symbol)',re.I)
WORD=re.compile(r'(?<![A-Za-z0-9_])(?:max|min|sin|log)(?![A-Za-z0-9_])')


def glyph_key(span,char):
    return (span['font'],char['c'],round(char['origin'][0],4),round(char['origin'][1],4),round(span['size'],4))


def functions(page):
    glyphs=[];candidates=[]
    for block in page.get_text('rawdict')['blocks']:
        if block['type']!=0:continue
        for line in block['lines']:
            if tuple(line['dir'])!=(1.,0.):continue
            for span in line['spans']:
                chars=span['chars'];text=''.join(c['c'] for c in chars)
                records=[{**c,'font':span['font'],'size':span['size'],'key':glyph_key(span,c)} for c in chars]
                glyphs.extend(c for c in records if c['c'].strip())
                # Never split a PDF glyph with a multi-character transcription.
                if len(text)!=len(chars):continue
                for match in WORD.finditer(text):candidates.append((match.group(),records[match.start():match.end()]))
    found=[];unknown=[]
    for operator,chars in candidates:
        box=fitz.Rect(chars[0]['bbox'])
        for char in chars[1:]:box|=fitz.Rect(char['bbox'])
        size=max(c['size'] for c in chars);baseline=chars[-1]['origin'][1]
        right=sorted([c for c in glyphs if c['origin'][0]>=box.x1-.1
            and c['origin'][0]<=min(page.rect.width,box.x1+min(240,page.rect.width*.45))
            and abs(c['origin'][1]-baseline)<=size*.85],key=lambda c:(c['origin'][0],c['origin'][1]))
        if not right or right[0]['c'] not in '({' or right[0]['bbox'][0]-box.x1>size*1.5:continue
        stack=[];argument=[];complete=False
        for char in right[:128]:
            if argument and char['bbox'][0]-argument[-1]['bbox'][2]>size*2:break
            token=char['c']
            if token in '([{':stack.append(token)
            elif token in ')]}':
                if not stack or '([{'.index(stack[-1])!=')]}'.index(token):break
                stack.pop()
            argument.append(char)
            if not stack:complete=True;break
        if not any(MATH_FONT.match(c['font']) for c in argument):continue
        signature=operator+''.join(c['c'] for c in argument)
        if not complete or '\ufffd' in signature or '(cid:' in signature:
            unknown.append({'operator':operator,'bbox':list(box),'reason':'UNCLOSED_OR_UNKNOWN_INLINE_ARGUMENT'});continue
        # A long ordinary Roman word inside parentheses is prose, not a call
        # merely because the surrounding font has math in its family name.
        prose=''.join(c['c'] if not MATH_FONT.match(c['font']) else ' ' for c in argument)
        if re.search(r'[A-Za-z]{3,}',prose):continue
        full=fitz.Rect(box)
        for char in argument:full|=fitz.Rect(char['bbox'])
        found.append({'operator':operator,'signature':unicodedata.normalize('NFC',signature),
            'bbox':list(full),'operator_bbox':list(box),'operator_glyph_keys':[c['key'] for c in chars]})
    return found,unknown


def protected_glyph_keys(page):
    return {tuple(key) for call in functions(page)[0] for key in call['operator_glyph_keys']}


def preceding_equation(page,box):
    box=fitz.Rect(box);half=page.rect.width/2;matches=[]
    for word in page.get_text('words'):
        if not re.fullmatch(r'\(\d+[a-z]?\)',word[4]) or word[0]%half<=half*.65:continue
        if (word[0]<half)!=(box.x0<half):continue
        distance=box.y0-word[3]
        if 0<=distance<=120:matches.append((distance,word[4]))
    matches.sort()
    return matches[0][1] if matches and (len(matches)==1 or matches[1][0]-matches[0][0]>1) else None


def audit(source,target,area=None):
    left,lu=functions(source);right,ru=functions(target)
    if area is not None:
        box=fitz.Rect(area)
        left=[c for c in left if box.contains(fitz.Rect(c['bbox']))]
        right=[c for c in right if box.contains(fitz.Rect(c['bbox']))]
        lu=[c for c in lu if box.intersects(fitz.Rect(c['bbox']))]
        ru=[c for c in ru if box.intersects(fitz.Rect(c['bbox']))]
    a=Counter(c['signature'] for c in left);b=Counter(c['signature'] for c in right)
    missing=list((a-b).elements());extra=list((b-a).elements())
    issues=[]
    for signature in sorted(set(missing)):
        call=next(c for c in left if c['signature']==signature)
        issues.append({'signature':signature,'operator':call['operator'],'bbox':call['bbox'],
            'equation_tag':preceding_equation(source,call['bbox']),'reason':'MATH_OPERATOR_OR_ARGUMENT_CHANGED'})
    if extra:issues.append({'signature':'','operator':'','bbox':None,'equation_tag':None,'reason':'EXTRA_MATH_OPERATOR_CALL'})
    return {'passed':not missing and not extra and not lu and not ru,
        'source':left,'target':right,'missing':missing,'extra':extra,'issues':issues,
        'not_checked':{'source':lu,'target':ru},'supported_operators':list(OPERATORS),
        'scope':'Delimited inline calls with math-font argument evidence; not all mathematics or semantic acceptance.'}


def review_findings(report):
    result=[]
    for issue in report['issues']:
        reference=(' Equation '+issue['equation_tag']+' following definition.') if issue['equation_tag'] else ''
        result.append({'region_id':'','category':'formula','severity':'critical','replacement':'',
            'reason':'Program mathematical operator/argument mismatch: '+issue['signature']+'.'+reference+' '+issue['reason']})
    for phase in ('source','target'):
        if report['not_checked'][phase]:
            result.append({'region_id':'','category':'formula','severity':'major','replacement':'',
                'reason':'Program operator audit could not check an unclosed/unknown '+phase+' argument; manual review required.'})
    return result
