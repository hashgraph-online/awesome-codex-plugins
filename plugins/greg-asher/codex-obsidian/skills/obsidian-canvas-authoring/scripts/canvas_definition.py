#!/usr/bin/env python3
"""Render, validate or revise a bounded JSON Canvas candidate. Never writes."""
import json
from math import isfinite
from pathlib import Path
import re
import sys

CORE = Path(__file__).resolve().parents[2] / 'obsidian-official-cli' / 'scripts'
sys.path.insert(0, str(CORE))
from cli import content_argument
from json_protocol import emit_report
from revision import digest, preview
from canvas_edit import edit
from canvas_layout import build, has_extensions, require, validate

MAX_BYTES = 12 * 1024
STRING = re.compile(r'"(?:\\.|[^"\\])*"')
CLI_ESCAPE = re.compile(r'\\(u[0-9a-fA-F]{4}|[\\/bfnrt"])')


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'duplicate JSON key {key!r}')
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError(f'{value} is not valid JSON')


def finite_float(value):
    number = float(value)
    require(isfinite(number), 'JSON number is out of range')
    return number


def loads(source):
    return json.loads(source, object_pairs_hook=unique_object,
                      parse_constant=invalid_constant, parse_float=finite_float)


def transport(source):
    """Escape only JSON tokens that the official CLI would otherwise decode."""
    count = 0

    def encode(match):
        raw = match.group()

        def escape(token):
            nonlocal count
            letter = token[1]
            if letter == 'n' or letter == 't':
                count += 1
                return '\\u000a' if letter == 'n' else '\\u0009'
            if letter == '\\' and raw[token.end():token.end() + 1] in ('n', 't'):
                count += 1
                return '\\u005c'
            return token[0]

        return CLI_ESCAPE.sub(escape, raw)

    converted = STRING.sub(encode, source)
    require(loads(converted) == loads(source), 'transport conversion changed JSON values')
    content_argument(converted)
    return converted, count


def plan(request):
    require(isinstance(request, dict), 'provide a JSON object')
    if 'canvas' in request:
        require(request.keys() == {'canvas'}, 'validate takes only canvas')
        references, warnings = validate(request['canvas'])
        return {'references': references, 'warnings': warnings,
                'extension_fields': has_extensions(request['canvas'])}
    if 'before' in request:
        before = request['before']
        require(isinstance(before, str) and 0 < len(before.encode()) <= MAX_BYTES,
                'before must be literal UTF-8 Canvas JSON up to 12 KiB')
        existing = loads(before)
        _, old_warnings = validate(existing)
        raw, changes = edit(before, existing, request)
    else:
        before = None
        old_warnings = []
        canvas = build(request)
        raw = json.dumps(canvas, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        changes = {'added': [item['id'] for item in canvas['nodes'] + canvas['edges']]}
    candidate = loads(raw)
    references, warnings = validate(candidate)
    new_warnings = [warning for warning in warnings if warning not in old_warnings]
    require(not new_warnings, 'layout needs revision: ' + '; '.join(new_warnings))
    result = {'references': references, 'warnings': warnings,
              'extension_fields': has_extensions(candidate)}
    if raw == before:
        return {'operation': 'unchanged', **result}
    content, escapes = transport(raw)
    require(len(content.encode()) <= MAX_BYTES, 'candidate exceeds 12 KiB')
    report = {'operation': 'create-only' if before is None else 'overwrite',
              'changes': changes, **result,
              'transport_escapes': escapes}
    if before is None:
        return {**report, 'content': content, 'after_sha256': digest(content)}
    return {**report, **preview(before, before, content)}


def main():
    try:
        data = sys.stdin.buffer.read(65537)
        require(len(data) <= 65536, 'request exceeds 64 KiB')
        return emit_report(plan(loads(data.decode('utf-8'))), 0)
    except (ValueError, RecursionError) as error:
        return emit_report({'error': str(error)}, 1)


if __name__ == '__main__':
    sys.exit(main())
