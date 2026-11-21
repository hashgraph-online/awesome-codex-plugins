#!/usr/bin/env python3
"""Validate capture inputs and render previews. No vault access or writes."""
import csv
from datetime import date
from hashlib import sha256
import io
import json
import re
from pathlib import Path
import sys
import unicodedata
from urllib.parse import urlsplit

CORE = Path(__file__).resolve().parents[2] / 'obsidian-official-cli' / 'scripts'
sys.path.insert(0, str(CORE))
from cli import content_argument
from json_protocol import emit_report
from decision_capture import UNSAFE_PATH_CHARS, literal_block, validate_segment

MAX_REQUEST = 256 * 1024
MAX_DATA = 64 * 1024
MAX_ITEMS = 20
MAX_NOTE = 8 * 1024
RECIPES = {
    'meeting': ('Meetings', 'Meeting notes', {'participants'}),
    'decision': ('Decisions', 'Decision and rationale', set()),
    'idea': ('Inbox', 'Idea', set()),
    'kickoff': ('Projects', 'Goals and next actions', set()),
    'source': ('Sources', 'Summary', {'url', 'author', 'published', 'excerpt'}),
}
COMMON = {'title', 'body', 'folder', 'tags', 'project_note'}
UNSAFE = re.compile('[' + re.escape(''.join(sorted(UNSAFE_PATH_CHARS | {'/', '%'}))) + ']')


def unique_object(pairs):
    values = {}
    for key, value in pairs:
        if key in values:
            raise ValueError(f'duplicate field {key!r}')
        values[key] = value
    return values


def invalid_constant(value):
    raise ValueError(f'{value} is not a JSON value')


def load_json(value):
    return json.loads(value, object_pairs_hook=unique_object, parse_constant=invalid_constant)


def text(value, field, multiline=False):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{field} must be nonempty text')
    if multiline:
        value = value.replace('\r\n', '\n')
    if any(unicodedata.category(char) in {'Cc', 'Cs'} and
           not (multiline and char in '\n\t') for char in value):
        raise ValueError(f'{field} contains unsupported control characters')
    return value


def iso_date(value, field):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
        raise ValueError(f'{field} must be YYYY-MM-DD')
    return date.fromisoformat(value).isoformat()


def safe_component(component, field):
    text(component, field)
    validate_segment(component, field)
    if '%' in component or len(component.encode('utf-8')) > 150:
        raise ValueError(f'{field} has an unsafe or oversized path component')
    return component


def vault_path(value, field):
    value = text(value, field)
    if len(value.encode('utf-8')) > 240:
        raise ValueError(f'{field} exceeds 240 UTF-8 bytes')
    return '/'.join(safe_component(part, field) for part in value.split('/'))


def note_title(title):
    title = text(title, 'title')
    cleaned = re.sub(r'\s+', ' ', UNSAFE.sub('-', unicodedata.normalize('NFC', title))).strip(' .')
    return safe_component(cleaned, 'title filename')


def text_list(value, field):
    if not isinstance(value, list) or len(value) > 20:
        raise ValueError(f'{field} must be a list of at most 20 strings')
    return [text(item, field) for item in value]


def source_url(value):
    value = text(value, 'url')
    parsed = urlsplit(value)
    if (parsed.scheme not in ('http', 'https') or not parsed.hostname or
            parsed.username is not None or parsed.password is not None or
            any(char.isspace() or char in '<>\\' for char in value)):
        raise ValueError('url must be an HTTP(S) URL without credentials or whitespace')
    # Accessing port validates explicit port syntax and range.
    _ = parsed.port
    return value



def render(recipe, captured, fields):
    folder_default, section, extra = RECIPES[recipe]
    if not isinstance(fields, dict) or fields.keys() - (COMMON | extra):
        raise ValueError('unknown recipe field or invalid fields object')
    title = text(fields.get('title'), 'title')
    body = text(fields.get('body'), 'body', multiline=True)
    folder = vault_path(fields.get('folder', folder_default), 'folder')
    path = vault_path(f'{folder}/{captured} {note_title(title)}.md', 'destination')
    properties = {'kind': recipe}
    dates = {'captured': captured}
    links = []
    if 'tags' in fields:
        tags = text_list(fields['tags'], 'tags')
        if any(not re.fullmatch(r'[\w/-]+', tag) or
               not any(char.isalpha() or char in '_-/' for char in tag) or
               any(not part for part in tag.split('/')) for tag in tags):
            raise ValueError('tags require valid bare Obsidian tag names')
        properties['tags'] = tags
    if recipe == 'meeting' and 'participants' in fields:
        properties['participants'] = text_list(fields['participants'], 'participants')
    if recipe == 'decision' or 'project_note' in fields:
        project = vault_path(fields.get('project_note'), 'project_note')
        if not project.endswith('.md'):
            raise ValueError('project_note must be an exact Markdown note path')
        if collision_key(project) == collision_key(path):
            raise ValueError('project_note cannot be the capture destination')
        links.append(project)

    provenance = ''
    excerpt = ''
    if recipe == 'source':
        properties['source_url'] = source_url(fields.get('url'))
        properties['source_title'] = title
        if 'author' in fields:
            properties['source_author'] = text(fields['author'], 'author')
        if 'published' in fields:
            dates['source_published'] = iso_date(fields['published'], 'published')
        provenance = ('## Provenance\n\n'
                      f'Author: {"see source_author" if "author" in fields else "unknown"}.\n'
                      f'Published: {"see source_published" if "published" in fields else "unknown"}.\n\n')
        if 'excerpt' in fields:
            excerpt = '\n\n## Source excerpt\n\n' + literal_block(text(fields['excerpt'], 'excerpt', multiline=True))

    for key, value in properties.items():
        if any('[[' in entry for entry in (value if isinstance(value, list) else [value])):
            raise ValueError(f'{key} contains wiki-link syntax; put literal material in the body or excerpt')
    frontmatter = [f'{key}: {json.dumps(value, ensure_ascii=False)}' for key, value in properties.items()]
    frontmatter += [f'{key}: {value}' for key, value in dates.items()]
    project_link = f'\n\n## Project\n\n[[{links[0]}|Project note]]' if links else ''
    markdown = ('---\n' + '\n'.join(frontmatter) + '\n---\n\n' +
                provenance + f'## {section}\n\n' + literal_block(body) + excerpt + project_link + '\n')
    encoded = markdown.encode('utf-8')
    if len(encoded) > MAX_NOTE:
        raise ValueError('rendered note exceeds 8 KiB')
    content_argument(markdown)  # Reuse the shared launcher transport preflight.
    return {'path': path, 'policy': 'create-only', 'content': markdown, 'links': links,
            'properties': {**properties, **dates}, 'date_properties': list(dates),
            'sha256': sha256(encoded).hexdigest()}


def collision_key(path):
    return unicodedata.normalize('NFC', path.casefold())


def batch_rows(batch, allowed):
    if not isinstance(batch, dict) or batch.keys() != {'format', 'data', 'mapping'}:
        raise ValueError('batch requires format, data and mapping')
    data = batch['data']
    mapping = batch['mapping']
    if not isinstance(data, str) or len(data.encode('utf-8')) > MAX_DATA:
        raise ValueError('batch data must be UTF-8 text up to 64 KiB')
    if (not isinstance(mapping, dict) or not mapping or mapping.keys() - allowed or
            any(not isinstance(key, str) or not key for key in mapping.values()) or
            len(set(mapping.values())) != len(mapping)):
        raise ValueError('mapping must pair distinct input keys with valid recipe fields')

    if batch['format'] == 'csv':
        reader = csv.reader(io.StringIO(data.removeprefix('\ufeff'), newline=''), strict=True)
        headers = next(reader, [])
        if not headers or any(not header for header in headers) or len(set(headers)) != len(headers):
            raise ValueError('CSV requires distinct nonempty headers')
        if set(mapping.values()) - set(headers):
            raise ValueError('CSV is missing a mapped header')
        rows = []
        for number, values in enumerate(reader, 1):
            if len(values) != len(headers) or number > MAX_ITEMS:
                raise ValueError(f'CSV row {number} has the wrong width or exceeds the item limit')
            rows.append(dict(zip(headers, values)))
    elif batch['format'] == 'json':
        rows = load_json(data)
    else:
        raise ValueError('batch format must be csv or json')

    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_ITEMS:
        raise ValueError('batch requires 1–20 input rows')
    for number, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f'row {number} must be an object')
    if set(mapping.values()) - {key for row in rows for key in row}:
        raise ValueError('batch is missing a mapped input key')
    for number, row in enumerate(rows, 1):
        try:
            fields = {}
            for field, key in mapping.items():
                if key not in row:
                    continue
                value = row[key]
                if batch['format'] == 'csv':
                    if value == '':
                        continue
                    if field in {'tags', 'participants'}:
                        value = load_json(value)
                fields[field] = value
            yield fields
        except ValueError as error:
            raise ValueError(f'row {number}: {error}') from error


def plan(request):
    if (not isinstance(request, dict) or request.keys() - {'recipe', 'captured', 'fields', 'batch'} or
            ('fields' in request) == ('batch' in request)):
        raise ValueError('expected recipe, captured and exactly one of fields or batch')
    recipe = request.get('recipe')
    if not isinstance(recipe, str) or recipe not in RECIPES:
        raise ValueError('recipe must be meeting, decision, idea, kickoff or source')
    captured = iso_date(request.get('captured'), 'captured')
    rows = batch_rows(request['batch'], COMMON | RECIPES[recipe][2]) if 'batch' in request else [request['fields']]
    items = []
    destinations = {}
    for number, fields in enumerate(rows, 1):
        try:
            item = render(recipe, captured, fields)
        except ValueError as error:
            raise ValueError(f'row {number}: {error}') from error
        key = collision_key(item['path'])
        if key in destinations:
            raise ValueError(f'rows {destinations[key]} and {number} produce the same destination')
        for other, other_row in destinations.items():
            if key.startswith(other + '/') or other.startswith(key + '/'):
                raise ValueError(f'rows {other_row} and {number} require the same path as a note and a folder')
        destinations[key] = number
        items.append({'row': number, **item})
    return {'recipe': recipe, 'items': items}


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_REQUEST + 1)
        if len(raw) > MAX_REQUEST:
            raise ValueError('request exceeds 256 KiB')
        return emit_report(plan(load_json(raw.decode('utf-8'))), 0)
    except (ValueError, csv.Error, RecursionError) as error:
        return emit_report({'error': str(error)}, 1)


if __name__ == '__main__':
    sys.exit(main())
