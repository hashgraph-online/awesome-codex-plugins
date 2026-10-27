"""Native glyph fragments for source repair; no paper coordinates or model boxes.

These are source-literal ownership rules, not a certificate of math semantics.
All original characters stay represented. Unknown fonts keep the old conservative
literal treatment; ordinary prose surrounding a symbol is no longer frozen.
"""
import re
import pymupdf as fitz

VERSION = 1
TOKENS = re.compile(r'</?[A-Za-z][A-Za-z0-9_-]*\s*/?>|\(cid:\d+\)|\(\d+[a-z]?\)|\[[A-Za-z0-9/]+\]|\b[IVXLCDM]+\.|'
                    r'\s+|[A-Za-z][A-Za-z0-9_-]*|[{}]|[^A-Za-z\s{}]+')


def slice_span(span, start, stop):
    chars = span['chars'][start:stop]
    box = fitz.Rect(chars[0]['bbox'])
    for char in chars[1:]:
        box |= fitz.Rect(char['bbox'])
    return {**span, 'text': span['text'][start:stop], 'chars': chars,
            'bbox': list(box), 'origin': chars[0]['origin']}


def script_after(previous, current, body_size):
    """Only a smaller, displaced, adjacent run can extend a literal math base."""
    if not previous or previous.get('_source_literal') not in {
            'math_font', 'math_character', 'italic_letter', 'script', 'brace_group'}:
        return False
    if not re.fullmatch(r'[A-Za-z0-9]+', current['text']):
        return False
    size, base = current['size'], previous['size']
    if not 0 < size <= body_size * .85 or size > base * 1.10:
        return False
    gap = current['bbox'][0] - previous['bbox'][2]
    displacement = abs(current['origin'][1] - previous['origin'][1])
    return (-base * .35 <= gap <= base * .35 + .5
            and max(.3, base * .12) <= displacement <= base * .9)


def fragments(line, math_font, math_chars, contact, state=None):
    state = state if state is not None else {'brace_depth': 0}
    body_size = max((s['size'] for s in line['spans']), default=0)
    result = []
    previous = None
    for span in line['spans']:
        text, chars = span['text'], span.get('chars', [])
        if not text:
            continue
        reason = ('math_font' if math_font.match(span['font']) else
                  'monospace' if 'Mon' in span['font'] else
                  'contact' if contact.search(text) else
                  'unresolved_text' if len(chars) != len(text) else None)
        if reason:
            result.append({**span, '_source_literal': reason})
            for char in text:
                if char == '{':
                    state['brace_depth'] += 1
                    if state['brace_depth'] > 32:
                        raise ValueError('SOURCE_LITERAL_NESTING_LIMIT')
                elif char == '}' and state['brace_depth']:
                    state['brace_depth'] -= 1
            if text.strip():
                previous = result[-1]
            continue
        words = re.findall(r'[A-Za-z]+', text)
        italic_letters = bool(span.get('flags', 0) & 2 and words
                              and all(len(word) == 1 for word in words))
        for match in TOKENS.finditer(text):
            token = slice_span(span, *match.span())
            value = token['text']
            reason = None
            if value == '{':
                state['brace_depth'] += 1
                if state['brace_depth'] > 32:
                    raise ValueError('SOURCE_LITERAL_NESTING_LIMIT')
            if state['brace_depth']:
                reason = 'brace_group'
            elif span.get('flags', 0) & 1:
                reason = 'script'
            elif math_chars.search(value):
                reason = 'math_character'
            elif italic_letters and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', value):
                reason = 'italic_letter'
            elif script_after(previous, token, body_size):
                reason = 'script'
            if value == '}' and state['brace_depth']:
                state['brace_depth'] -= 1
            if reason:
                token['_source_literal'] = reason
            result.append(token)
            if value.strip():
                previous = token
    return result


def annotate_block(block, math_font, math_chars, contact):
    state = {'brace_depth': 0}
    for line in block['lines']:
        line['_source_fragments'] = fragments(line, math_font, math_chars, contact, state)
    block['_source_literal_scope_unclosed'] = bool(state['brace_depth'])
