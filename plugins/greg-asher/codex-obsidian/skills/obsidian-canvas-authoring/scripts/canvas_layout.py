"""Deterministic layouts and bounded JSON Canvas checks."""
from collections import Counter
from hashlib import sha256
from itertools import combinations
import re
from urllib.parse import urlsplit
import unicodedata

LANES = {
    'research': ('Sources', 'Synthesis', 'Open questions'),
    'project': ('Decisions', 'Dependencies and risks', 'Next actions'),
}
SIDES = ('top', 'right', 'bottom', 'left')
MAX_NODES, MAX_EDGES = 32, 40
WIDTH, HEIGHT, GAP, PADDING = 360, 244, 360, 32
GEOMETRY = {'x', 'y', 'width', 'height', 'color'}
NODE_FIELDS = {'file': {'file', 'subpath'}, 'text': {'text'}, 'link': {'url'},
               'group': {'label', 'background', 'backgroundStyle'}}
EDGE_FIELDS = {'fromNode', 'toNode', 'fromSide', 'toSide', 'fromEnd', 'toEnd', 'label', 'color'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, field, limit, multiline=False, allow_blank=False):
    valid = isinstance(value, str) and len(value) <= limit and (allow_blank or bool(value.strip()))
    require(valid, f'{field} must be {"text" if allow_blank else "nonempty text"} of at most {limit} characters')
    require(all(unicodedata.category(char) not in {'Cc', 'Cs', 'Zl', 'Zp'} or
                (multiline and char in '\n\t') for char in value), f'{field} has unsupported controls')
    return value


def vault_path(value, field):
    value = text(value, field, 240)
    require('\\' not in value and ':' not in value and
            all(part not in ('', '.', '..') for part in value.split('/')),
            f'{field} must be an exact vault-relative path')
    return value


def url(value):
    value = text(value, 'url', 400)
    parsed = urlsplit(value)
    require(parsed.scheme in ('http', 'https') and parsed.hostname and
            parsed.username is None and parsed.password is None and
            not any(c.isspace() or c in '<>\\' for c in value),
            'link must be an HTTP(S) URL without credentials')
    _ = parsed.port
    return value


def color(item):
    if 'color' in item:
        value = item['color']
        require(isinstance(value, str) and re.fullmatch(r'[1-6]|#[0-9A-Fa-f]{6}', value),
                'color must be a Canvas preset or six-digit hex')


def bounds(node):
    return node['x'], node['y'], node['x'] + node['width'], node['y'] + node['height']


def inside(inner, outer):
    return outer[0] <= inner[0] and outer[1] <= inner[1] and inner[2] <= outer[2] and inner[3] <= outer[3]


def intersects(a, b):
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])


def anchor(node, side):
    x, y, right, bottom = bounds(node)
    return {'top': ((x + right) / 2, y), 'right': (right, (y + bottom) / 2),
            'bottom': ((x + right) / 2, bottom), 'left': (x, (y + bottom) / 2)}[side]


def crosses(first, second):
    a, b = first
    c, d = second

    def turn(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    return turn(a, b, c) * turn(a, b, d) < 0 and turn(c, d, a) * turn(c, d, b) < 0


def display_columns(value):
    return sum(2 if unicodedata.east_asian_width(char) in "WF" else 1 for char in value)


def has_extensions(document):
    return bool(document.keys() - {'nodes', 'edges'}) or any(
        node.keys() - ({'id', 'type'} | GEOMETRY | NODE_FIELDS[node['type']])
        for node in document.get('nodes', [])
    ) or any(
        edge.keys() - ({'id'} | EDGE_FIELDS) for edge in document.get('edges', [])
    )


def validate(document):
    require(isinstance(document, dict), 'Canvas must be a JSON object')
    nodes, edges = document.get('nodes', []), document.get('edges', [])
    require(isinstance(nodes, list) and len(nodes) <= MAX_NODES, f'Canvas allows at most {MAX_NODES} nodes')
    require(isinstance(edges, list) and len(edges) <= MAX_EDGES, f'Canvas allows at most {MAX_EDGES} edges')
    ids = set()
    for item in [*nodes, *edges]:
        require(isinstance(item, dict), 'nodes and edges must be objects')
        identifier = text(item.get('id'), 'id', 100)
        require(identifier not in ids, f'duplicate ID {identifier}')
        ids.add(identifier)
        color(item)

    references, warnings = [], []
    by_id = {node['id']: node for node in nodes}
    for node in nodes:
        for key in ('x', 'y', 'width', 'height'):
            value = node.get(key)
            require(type(value) is int and abs(value) <= 100000 and
                    (key in ('x', 'y') or value > 0), f'invalid {key} on {node["id"]}')
        kind = node.get('type')
        if kind == 'file':
            path = vault_path(node.get('file'), 'file')
            subpath = node.get('subpath')
            if 'subpath' in node:
                text(subpath, 'subpath', 160)
                require(subpath.startswith('#') and len(subpath) > 1 and not subpath[1:].startswith('#'),
                        'subpath must select a heading or block')
            references.append({'id': node['id'], 'path': path, 'subpath': subpath})
        elif kind == 'link':
            url(node.get('url'))
        elif kind == 'text':
            text(node.get('text'), 'card text', 2000, multiline=True, allow_blank=True)
            # Conservative check for 16px text with padding and wrapped lines.
            columns = max(1, (node['width'] - 40) // 9)
            lines = sum(max(1, (display_columns(line) + columns - 1) // columns)
                        for line in node['text'].expandtabs(4).split('\n'))
            if lines * 22 + 36 > node['height']:
                warnings.append(f'possible text clipping on {node["id"]}')
        elif kind == 'group':
            if 'label' in node:
                text(node['label'], 'group label', 80, allow_blank=True)
            if 'background' in node:
                references.append({'id': node['id'], 'path': vault_path(node['background'], 'background'),
                                   'subpath': None})
            if 'backgroundStyle' in node:
                require(node['backgroundStyle'] in ('cover', 'ratio', 'repeat'), 'invalid group background style')
        else:
            raise ValueError(f'unsupported node type {kind!r}')

    for left, right in combinations(nodes, 2):
        a, b = bounds(left), bounds(right)
        if not intersects(a, b):
            continue
        if left['type'] == 'group' and inside(b, a):
            continue
        warnings.append(f'overlap or inconsistent group layering: {left["id"]}, {right["id"]}')

    degree, pairs, segments = Counter(), Counter(), {}
    for edge in edges:
        start = text(edge.get('fromNode'), 'fromNode', 100)
        end = text(edge.get('toNode'), 'toNode', 100)
        require(start in by_id and end in by_id, f'dangling edge {edge["id"]}')
        for key in ('fromSide', 'toSide'):
            if key in edge:
                require(edge[key] in SIDES, f'invalid {key}')
        for key in ('fromEnd', 'toEnd'):
            if key in edge:
                require(edge[key] in ('none', 'arrow'), f'invalid {key}')
        if 'label' in edge:
            text(edge['label'], 'edge label', 100, allow_blank=True)
        if start == end:
            warnings.append(f'self edge {edge["id"]}')
        pairs[start, end] += 1
        degree.update((start, end))
        if 'fromSide' in edge and 'toSide' in edge:
            segments[edge['id']] = (anchor(by_id[start], edge['fromSide']),
                                    anchor(by_id[end], edge['toSide']))
            if edge.get('label') and {edge['fromSide'], edge['toSide']} == {'left', 'right'}:
                a, b = segments[edge['id']]
                if display_columns(edge['label']) * 10 + 26 > abs(b[0] - a[0]):
                    warnings.append(f'possible edge label clipping on {edge["id"]}')
    warnings.extend(f'parallel edges: {start}, {end}' for (start, end), count in pairs.items() if count > 1)
    warnings.extend(f'dense connections on {node}' for node, count in degree.items() if count > 4)
    for a, b in combinations(segments, 2):
        if crosses(segments[a], segments[b]):
            warnings.append(f'possible crossing edges: {a}, {b}')
    return references, warnings


def stable_id(kind, key):
    return sha256(f'{kind}:{key}'.encode()).hexdigest()[:16]


def literal_markdown(value):
    return re.sub(r'([\\`*_{}\[\]()#+.!>|~$<>&:=^-])', r'\\\1', value)


def card(spec):
    require(isinstance(spec, dict), 'card must be an object')
    key = text(spec.get('key'), 'card key', 60)
    kind_fields = {'file', 'text', 'url'}
    selected = kind_fields.intersection(spec)
    require(len(selected) == 1 and spec.keys() <= {'key', 'lane', 'subpath'} | kind_fields,
            'card requires one of file, text or url')
    field = selected.pop()
    require(field == 'file' or 'subpath' not in spec, 'subpath requires a file card')
    if field == 'text':
        value = literal_markdown(text(spec[field], 'card text', 300, multiline=True))
    elif field == 'file':
        value = vault_path(spec[field], 'file')
    else:
        value = url(spec[field])
    return key, {'id': stable_id('card', key), 'type': 'link' if field == 'url' else field, field: value,
                 **({'subpath': spec['subpath']} if 'subpath' in spec else {})}


def build(request):
    require(request.keys() <= {'layout', 'cards', 'relationships'}, 'unsupported creation field')
    layout = request.get('layout')
    require(isinstance(layout, str) and layout in ('research', 'project', 'process'), 'unknown layout')
    specs = request.get('cards')
    require(isinstance(specs, list) and 1 <= len(specs) <= (5 if layout == 'process' else 9),
            'provide 1–5 process cards or 1–9 map cards')
    columns = {}
    cards, counts = {}, Counter()
    for index, spec in enumerate(specs):
        key, node = card(spec)
        require(key not in cards, f'duplicate card key {key}')
        if layout == 'process':
            require('lane' not in spec, 'process order comes from the card list')
            column = index
        else:
            lane = spec.get('lane')
            require(lane in LANES[layout], f'{layout} lanes are {LANES[layout]}')
            column = LANES[layout].index(lane)
            require(counts[column] < 3, 'allow at most three cards per lane')
        node.update(x=column * (WIDTH + GAP), y=counts[column] * (HEIGHT + 54),
                    width=WIDTH, height=HEIGHT)
        cards[key], columns[key] = node, column
        counts[column] += 1

    groups = []
    if layout in LANES:
        for column, lane in enumerate(LANES[layout]):
            if counts[column]:
                groups.append({'id': stable_id('group', f'{layout}:{lane}'), 'type': 'group',
                               'label': lane, 'x': column * (WIDTH + GAP) - PADDING, 'y': -PADDING,
                               'width': WIDTH + 2 * PADDING,
                               'height': counts[column] * (HEIGHT + 54) - 54 + 2 * PADDING})

    edges = []
    relationships = request.get('relationships', [])
    require(isinstance(relationships, list) and len(relationships) <= 12, 'provide at most 12 relationships')
    for relation in relationships:
        require(isinstance(relation, dict) and relation.keys() == {'from', 'to', 'label', 'evidence'},
                'relationship needs from, to, label and evidence')
        start, end = (text(relation[key], key, 60) for key in ('from', 'to'))
        require(start in cards and end in cards, 'relationship endpoint does not name a card')
        require(columns[end] == columns[start] + 1, 'use adjacent left-to-right cards or lanes')
        evidence = relation['evidence']
        require(evidence in ('documented', 'inferred'), 'relationship evidence must be documented or inferred')
        label = text(relation['label'], 'relationship label', 20)
        edges.append({'id': stable_id('edge', f'{cards[start]["id"]}:{cards[end]["id"]}'),
                      'fromNode': cards[start]['id'], 'fromSide': 'right',
                      'toNode': cards[end]['id'], 'toSide': 'left', 'toEnd': 'arrow',
                      'label': f'{evidence.title()} · {label}'})
    return {'nodes': groups + list(cards.values()), 'edges': edges}
