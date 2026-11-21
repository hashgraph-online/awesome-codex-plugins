#!/usr/bin/env python3
"""Render or patch a bounded Bases table candidate. No vault access or writes."""
from datetime import date
import json
import math
from pathlib import Path
import re
import sys

CORE = Path(__file__).resolve().parents[2] / 'obsidian-official-cli' / 'scripts'
sys.path.insert(0, str(CORE))
from cli import content_argument
from json_protocol import emit_report
from revision import preview as candidate

MAX_DEFINITION = 12 * 1024
IDENTIFIER = re.compile(r'[A-Za-z_][A-Za-z0-9_]*\Z')
FILE_TYPES = {'file.name': 'text', 'file.path': 'text', 'file.folder': 'text',
              'file.ext': 'text', 'file.size': 'number'}
TYPES = {'text', 'number', 'date', 'boolean', 'list'}
OPERATORS = ('==', '!=', '<', '<=', '>', '>=')
SUMMARY_TYPES = {'Sum': 'number', 'Average': 'number', 'Min': 'number', 'Max': 'number',
                 'Earliest': 'date', 'Latest': 'date', 'Checked': 'boolean',
                 'Unchecked': 'boolean', 'Empty': None, 'Filled': None, 'Unique': None}
VIEW_FIELDS = {'columns', 'where', 'sort', 'group', 'summaries', 'limit'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, required=(), optional=()):
    require(isinstance(value, dict) and set(required) <= value.keys() <= set(required) | set(optional),
            f'expected fields {", ".join(sorted(required)) or "(none required)"}'
            f' with optional {", ".join(sorted(optional)) or "(none)"}')
    return value


def literal(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def text(value):
    return isinstance(value, str) and bool(value.strip()) and not any(
        ord(char) < 32 or 127 <= ord(char) < 160 or char in '\u2028\u2029' or
        0xD800 <= ord(char) <= 0xDFFF
        for char in value)


def number(value):
    return type(value) in (int, float) and abs(value) <= 2**53 - 1 and math.isfinite(value)


def property_types(schema):
    require(isinstance(schema, dict) and len(schema) <= 32, 'schema must map at most 32 note properties to types')
    require(all(IDENTIFIER.fullmatch(key) and isinstance(kind, str) and kind in TYPES
                for key, kind in schema.items()), 'schema requires simple note names and supported types')
    return {**FILE_TYPES, **{'note.' + key: kind for key, kind in schema.items()}}


def reference(value, types):
    require(isinstance(value, str) and value in types, f'unknown property reference {value!r}')
    return value


def formulas(specs, types):
    require(isinstance(specs, dict) and len(specs) <= 12, 'provide at most 12 formulas')
    require(all(IDENTIFIER.fullmatch(name) for name in specs), 'formula names must be simple identifiers')
    formula_types = {**types, **{'formula.' + name: 'number' for name in specs}}
    expressions, visiting = {}, set()

    def compile_one(name):
        if name in expressions:
            return
        require(name not in visiting, f'circular formula dependency at {name}')
        visiting.add(name)
        spec = fields(specs[name], ('left', 'op', 'right'))
        require(spec['op'] in ('+', '-', '*', '/'), 'formula operation must be +, -, * or /')

        def operand(value):
            if number(value):
                return literal(value)
            ref = reference(value, formula_types)
            require(formula_types[ref] == 'number', f'formula operand {ref} must be numeric')
            if ref.startswith('formula.'):
                compile_one(ref[8:])
            return ref

        left, right = operand(spec['left']), operand(spec['right'])
        require(spec['op'] != '/' or spec['right'] != 0, 'formula cannot divide by literal zero')
        expressions[name] = f'{left} {spec["op"]} {right}'
        visiting.remove(name)

    for name in specs:
        compile_one(name)
    return expressions, formula_types


def predicate(spec, types):
    spec = fields(spec, ('property', 'op', 'value'))
    prop, op, value = reference(spec['property'], types), spec['op'], spec['value']
    kind = types[prop]
    require(op in OPERATORS, 'unsupported filter operation')
    require(kind in ('number', 'date') or op in ('==', '!='), 'this property supports equality filters only')
    if kind == 'date':
        require(isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value),
                'date filter requires YYYY-MM-DD')
        operand = f'date({literal(date.fromisoformat(value).isoformat())})'
    else:
        require((kind == 'text' and text(value)) or (kind == 'number' and number(value)) or
                (kind == 'boolean' and type(value) is bool), f'filter value must match {kind}')
        operand = literal(value)
    return f'{prop} != null && {prop} {op} {operand}'


def ordering(spec, types):
    spec = fields(spec, ('property', 'direction'))
    require(spec['direction'] in ('ASC', 'DESC'), 'direction must be ASC or DESC')
    return {'property': reference(spec['property'], types), 'direction': spec['direction']}


def view_fields(spec, types):
    fields(spec, optional=VIEW_FIELDS)
    view = {}
    if 'columns' in spec:
        columns = spec['columns']
        require(isinstance(columns, list) and 1 <= len(columns) <= 20, 'provide 1–20 columns')
        order = [reference(column, types) for column in columns]
        require(len(order) == len(set(order)), 'duplicate view columns')
        view['order'] = order
    if 'where' in spec:
        require(isinstance(spec['where'], list) and 1 <= len(spec['where']) <= 12, 'provide 1–12 filters')
        view['filters'] = {'and': [predicate(item, types) for item in spec['where']]}
    if 'sort' in spec:
        require(isinstance(spec['sort'], list) and 1 <= len(spec['sort']) <= 5, 'provide 1–5 sort fields')
        view['sort'] = [ordering(item, types) for item in spec['sort']]
        require(len({item['property'] for item in view['sort']}) == len(view['sort']), 'duplicate sort fields')
    if 'group' in spec:
        view['groupBy'] = ordering(spec['group'], types)
    if 'summaries' in spec:
        summaries = spec['summaries']
        require(isinstance(summaries, dict) and len(summaries) <= 12, 'provide at most 12 summaries')
        for prop, summary in summaries.items():
            reference(prop, types)
            require(isinstance(summary, str) and summary in SUMMARY_TYPES, 'unsupported summary')
            require(SUMMARY_TYPES[summary] in (None, types[prop]), f'{summary} is incompatible with {prop}')
        view['summaries'] = summaries
    if 'limit' in spec:
        require(type(spec['limit']) is int and 1 <= spec['limit'] <= 500, 'limit must be 1–500')
        view['limit'] = spec['limit']
    return view


def create(request):
    fields(request, ('folder', 'schema', 'views'), ('formulas',))
    folder = request['folder']
    require(text(folder) and '\\' not in folder and
            all(part not in ('', '.', '..') for part in folder.split('/')) and
            not re.match(r'^[A-Za-z]:', folder), 'folder must be an exact vault-relative collection')
    expressions, types = formulas(request.get('formulas', {}), property_types(request['schema']))
    specs = request['views']
    require(isinstance(specs, list) and 1 <= len(specs) <= 8, 'provide 1–8 table views')
    views, names = [], set()
    for spec in specs:
        fields(spec, ('name', 'columns'), VIEW_FIELDS)
        name = spec['name']
        require(text(name) and name not in names, 'view names must be nonempty and unique')
        names.add(name)
        views.append({'type': 'table', 'name': name,
                      **view_fields({key: value for key, value in spec.items() if key != 'name'}, types)})
    document = {'filters': {'and': ['file.ext == "md"', f'file.inFolder({literal(folder)})']},
                'views': views}
    if expressions:
        document['formulas'] = expressions
    return json.dumps(document, ensure_ascii=False, indent=2) + '\n'


def edit(request):
    from view_patch import patch_view
    fields(request, ('before', 'view', 'schema', 'changes'), ('formula_types',))
    require(text(request['view']), 'provide the exact view name')
    before = request['before']
    require(isinstance(before, str) and 0 < len(before.encode('utf-8')) <= MAX_DEFINITION,
            'existing definition must fit within 12 KiB')
    types = property_types(request['schema'])
    observed = request.get('formula_types', {})
    require(isinstance(observed, dict) and all(IDENTIFIER.fullmatch(key) and isinstance(kind, str) and
            kind in TYPES for key, kind in observed.items()), 'invalid observed formula types')

    def changes(existing):
        require(observed.keys() <= existing.keys(), 'observed formula type refers to an absent formula')
        refs = {**types, **{'formula.' + name: observed.get(name, 'unknown')
                            for name in existing if IDENTIFIER.fullmatch(name)}}
        values = view_fields(request['changes'], refs)
        require(values, 'provide at least one editable field')
        return values

    return patch_view(before, request['view'], changes)


def plan(request):
    require(isinstance(request, dict), 'provide a JSON object')
    before = request.get('before')
    content = edit(request) if 'before' in request else create(request)
    require(len(content.encode('utf-8')) <= MAX_DEFINITION, 'candidate exceeds 12 KiB')
    content_argument(content)
    if before is None:
        return {'content': content, 'operation': 'create-only'}
    if before == content:
        return {'content': content, 'operation': 'unchanged'}
    # Use the shared exact-text candidate and fingerprint/diff contract.
    return {'operation': 'overwrite', **candidate(before, before, content)}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'duplicate request field {key!r}')
        result[key] = value
    return result


def main():
    try:
        data = sys.stdin.buffer.read(65537)
        require(len(data) <= 65536, 'request exceeds 64 KiB')
        return emit_report(plan(json.loads(data.decode('utf-8'), object_pairs_hook=unique_object)), 0)
    except (ValueError, RecursionError) as error:
        return emit_report({'error': str(error)}, 1)


if __name__ == '__main__':
    sys.exit(main())
