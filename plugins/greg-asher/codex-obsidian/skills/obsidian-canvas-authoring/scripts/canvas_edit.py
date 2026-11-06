"""Apply scoped JSON source splices without reserializing unrelated records."""
from copy import deepcopy
import json
import re

from canvas_layout import EDGE_FIELDS, GEOMETRY, NODE_FIELDS, literal_markdown, require, text

DECODE = json.JSONDecoder().raw_decode
SPACE = re.compile(r'[ \r\n\t]*')


def skip(source, offset):
    return SPACE.match(source, offset).end()


def members(source, start, object_mode):
    """Yield name and value spans for a previously validated object or array."""
    index = skip(source, start + 1)
    closing = '}' if object_mode else ']'
    while source[index] != closing:
        key = None
        if object_mode:
            key, end = DECODE(source, index)
            index = skip(source, skip(source, end) + 1)
        _, end = DECODE(source, index)
        yield key, index, end
        index = skip(source, end)
        if source[index] == ',':
            index = skip(source, index + 1)


def packed(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def set_fields(source, span, changes, patches):
    start, end = span
    existing = {key: (first, last) for key, first, last in members(source, start, True)}
    extra = []
    for key, value in changes.items():
        if key in existing:
            first, last = existing[key]
            patches.append((first, last, packed(value)))
        else:
            extra.append(f'{packed(key)}: {packed(value)}')
    if extra:
        patches.append((end - 1, end - 1, ', ' + ', '.join(extra)))


def removed_spans(spans, removed):
    index = 0
    while index < len(spans):
        if index not in removed:
            index += 1
            continue
        first = index
        while index < len(spans) and index in removed:
            index += 1
        if index < len(spans):
            yield spans[first][0], spans[index][0], ''
        elif first:
            yield spans[first - 1][1], spans[-1][1], ''
        else:
            yield spans[0][0], spans[-1][1], ''


def literal_text(record):
    if 'text' in record:
        record['text'] = literal_markdown(text(record['text'], 'card text', 300, multiline=True))
    return record


def editable(kind, record):
    if kind == 'edges':
        return EDGE_FIELDS
    node_type = record.get('type')
    require(isinstance(node_type, str) and node_type in NODE_FIELDS, 'unsupported added node type')
    return GEOMETRY | NODE_FIELDS[node_type]


def edit(before, document, request):
    require(request.keys() <= {'before', 'update', 'remove', 'add'}, 'unsupported edit field')
    expected = deepcopy(document)
    entries = {item['id']: (kind, index) for kind in ('nodes', 'edges')
               for index, item in enumerate(document.get(kind, []))}
    updates = request.get('update', {})
    removals = request.get('remove', [])
    additions = request.get('add', {})
    require(isinstance(updates, dict) and updates.keys() <= entries.keys(), 'update names an absent ID')
    require(isinstance(removals, list) and all(isinstance(key, str) and key in entries for key in removals)
            and len(set(removals)) == len(removals), 'remove requires distinct existing IDs')
    require(not updates.keys() & set(removals), 'cannot both update and remove the same ID')
    require(isinstance(additions, dict) and additions.keys() <= {'nodes', 'edges'},
            'add must be a nodes/edges object')
    require(updates or removals or any(additions.values()), 'provide at least one change')
    root = skip(before, 0)
    arrays = {key: (start, end) for key, start, end in members(before, root, True)}
    patches, new_arrays, changed, added = [], [], {}, []
    for kind in ('nodes', 'edges'):
        new = additions.get(kind, [])
        require(isinstance(new, list) and len(new) <= 12 and all(isinstance(item, dict) for item in new),
                'add accepts at most 12 records per collection')
        new = [literal_text(dict(item)) if kind == 'nodes' and item.get('type') == 'text' else dict(item)
               for item in new]
        for item in new:
            standard = {'id', 'type'} if kind == 'nodes' else {'id'}
            require(item.keys() <= standard | editable(kind, item), 'unsupported fields on a new record')
        ids = [text(item.get('id'), 'new ID', 100) for item in new]
        require(not set(ids) & (entries.keys() | set(added)) and len(set(ids)) == len(ids),
                'new IDs must be distinct from all existing and new IDs')
        added.extend(ids)
        groups = [item for item in new if kind == 'nodes' and item.get('type') == 'group']
        tail = [item for item in new if item not in groups]
        old = expected.get(kind, [])
        removed = {index for index, item in enumerate(old) if item['id'] in removals}
        if kind in arrays:
            start, end = arrays[kind]
            spans = [(first, last) for _, first, last in members(before, start, False)]
            patches.extend(removed_spans(spans, removed))
            for index, item in enumerate(old):
                identifier = item['id']
                if identifier not in updates:
                    continue
                values = updates[identifier]
                require(isinstance(values, dict) and values and values.keys() <= editable(kind, item),
                        f'invalid update fields for {identifier}')
                values = literal_text(dict(values)) if item.get('type') == 'text' else values
                set_fields(before, spans[index], values, patches)
                item.update(values)
                changed[identifier] = list(values)
            survivors = [index for index in range(len(old)) if index not in removed]
            if groups and survivors:
                position = spans[survivors[0]][0]
                patches.append((position, position, ', '.join(map(packed, groups)) + ', '))
            if tail or (groups and not survivors):
                append = tail if survivors else groups + tail
                position = end - 1
                patches.append((position, position, (', ' if survivors else '') +
                                ', '.join(map(packed, append))))
        elif new:
            new_arrays.append(f'{packed(kind)}: {packed(groups + tail)}')
        if kind in arrays or new:
            expected[kind] = groups + [item for index, item in enumerate(old) if index not in removed] + tail
    if new_arrays:
        position = before.rfind('}')
        patches.append((position, position, (', ' if document else '') + ', '.join(new_arrays)))
    result = before
    for start, end, replacement in sorted(patches, reverse=True):
        result = result[:start] + replacement + result[end:]
    require(json.loads(result) == expected, 'scoped edit could not preserve the JSON structure')
    return result, {'updated': changed, 'added': added, 'removed': removals}
