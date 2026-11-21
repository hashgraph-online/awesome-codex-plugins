#!/usr/bin/env python3
"""Compare bounded CLI property observations against explicit audit conventions."""
from datetime import date, datetime
import hashlib
import json
import math
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'obsidian-official-cli' / 'scripts'))
from json_protocol import emit_report

TYPES = {'text', 'list', 'number', 'checkbox', 'date', 'datetime'}
PROPERTY = re.compile(r'[\w][\w .-]{0,79}')
TAG = re.compile(r'[\w/-]{1,80}')
MAX_VALUE_BYTES = 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def mapping(value, fields, label):
    require(isinstance(value, dict) and value.keys() <= fields, f'invalid {label}')
    return value


def path(value, note=False):
    require(isinstance(value, str) and 0 < len(value) <= 1024 and
            not any(char in value for char in ('\\', ':')) and
            all(ord(char) >= 32 and ord(char) != 127 for char in value) and
            all(part not in ('', '.', '..') for part in value.split('/')) and
            (not note or value.endswith('.md')), 'expected an exact vault-relative path')
    value.encode('utf-8')
    return value


def paths(values, limit, note=False):
    require(isinstance(values, list) and len(values) <= limit, f'expected at most {limit} paths')
    return {path(value, note) for value in values}


def within(note, folder):
    return note.startswith(folder + '/')


def select(scope, inventory):
    mapping(scope, {'folder', 'paths', 'exclude_folders', 'exclude_files', 'max_notes'}, 'scope')
    require(('folder' in scope) != ('paths' in scope), 'select one folder or an exact note list')
    limit = scope.get('max_notes', 12)
    require(type(limit) is int and 1 <= limit <= 25, 'max_notes must be between 1 and 25')
    discovered = paths(inventory, 1000, note=True)
    if 'folder' in scope:
        folder = path(scope['folder'])
        candidates = {note for note in discovered if within(note, folder)}
    else:
        requested = paths(scope['paths'], 25, note=True)
        require(requested and requested <= discovered, 'verify all selected note paths first')
        candidates = requested
    folders = paths(scope.get('exclude_folders', []), 25)
    files = paths(scope.get('exclude_files', []), 25, note=True)
    eligible = sorted(note for note in candidates - files
                      if not any(within(note, folder) for folder in folders))
    return {'selected': eligible[:limit], 'excluded': sorted(candidates - set(eligible)),
            'deferred_count': max(0, len(eligible) - limit)}


def matches(value, kind):
    if kind == 'text':
        return isinstance(value, str)
    if kind == 'list':
        return isinstance(value, list) and all(isinstance(item, str) or matches(item, 'number')
                                               for item in value)
    if kind == 'checkbox':
        return type(value) is bool
    if kind == 'number':
        return type(value) is int or (type(value) is float and math.isfinite(value))
    if not isinstance(value, str):
        return False
    try:
        if kind == 'date' and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            date.fromisoformat(value)
            return True
        if kind == 'datetime' and re.fullmatch(
                r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?', value):
            datetime.fromisoformat(value)
            return True
    except ValueError:
        pass
    return False


def tag_name(value):
    return (isinstance(value, str) and TAG.fullmatch(value) and not value.isdecimal() and
            all(value.split('/')))


def conventions(config):
    mapping(config, {'properties', 'tag_aliases'}, 'conventions')
    rules = config.get('properties', {})
    require(isinstance(rules, dict) and len(rules) <= 20, 'configure at most 20 properties')
    for key, rule in rules.items():
        require(PROPERTY.fullmatch(key), 'invalid property name')
        mapping(rule, {'type', 'required', 'allowed', 'default'}, f'rule for {key}')
        kind = rule.get('type')
        require(isinstance(kind, str) and kind in TYPES, f'unsupported type for {key}')
        require(type(rule.get('required', False)) is bool, f'required must be boolean for {key}')
        if 'allowed' in rule:
            allowed = rule['allowed']
            require(isinstance(allowed, list) and 1 <= len(allowed) <= 20 and
                    all(matches(value, kind) for value in allowed) and
                    len(json.dumps(allowed)) <= MAX_VALUE_BYTES, f'invalid allowed values for {key}')
        if 'default' in rule:
            require(rule.get('required') and matches(rule['default'], kind) and
                    len(json.dumps(rule['default'])) <= MAX_VALUE_BYTES and
                    ('allowed' not in rule or rule['default'] in rule['allowed']),
                    f'invalid missing-value default for {key}')
    aliases = config.get('tag_aliases', {})
    require(isinstance(aliases, dict) and len(aliases) <= 20, 'configure at most 20 tag aliases')
    for old, new in aliases.items():
        require(tag_name(old) and tag_name(new) and new not in aliases, 'tag aliases must be bare names without chains or cycles')
    return rules, aliases


def finding(rule, note, key, evidence, reason, correction=None):
    identifier = hashlib.sha256(json.dumps([rule, note, key]).encode()).hexdigest()[:16]
    if len(json.dumps(evidence)) > MAX_VALUE_BYTES:
        evidence = {'omitted': 'observed value exceeds report budget'}
    return {'id': identifier, 'rule': rule, 'path': note, 'location': {'property': key},
            'evidence': evidence, 'severity': 'warning', 'reason': reason,
            'correction': correction, 'ambiguity': 'needs-choice' if correction is None else 'none'}


def metadata(note, observed, rules, aliases):
    for key, rule in sorted(rules.items()):
        kind = rule['type']
        if key not in observed:
            if rule.get('required'):
                correction = {'value': rule['default'], 'type': kind} if 'default' in rule else None
                yield finding('property.missing', note, key, {'present': False},
                              'Required property is absent', correction)
            continue
        value = observed[key]
        if not matches(value, kind):
            yield finding('property.type', note, key, {'value': value, 'expected': kind},
                          'Value does not match the configured type')
        elif 'allowed' in rule and value not in rule['allowed']:
            yield finding('property.value', note, key, {'value': value, 'allowed': rule['allowed']},
                          'Value is outside the configured set')

    if aliases and 'tags' in observed:
        tags = observed['tags']
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            if rules.get('tags', {}).get('type') != 'list' or matches(tags, 'list'):
                yield finding('tag.type', note, 'tags', {'value': tags}, 'Frontmatter tags need a list of names')
        elif any(tag in aliases for tag in tags):
            present = {tag.casefold() for tag in tags if tag not in aliases}
            replacement = []
            for tag in tags:
                canonical = aliases.get(tag)
                if canonical is None:
                    replacement.append(tag)
                elif canonical.casefold() not in present:
                    replacement.append(canonical)
                    present.add(canonical.casefold())
            tag_rule = rules.get('tags', {})
            usable = (not tag_rule or (tag_rule['type'] == 'list' and
                      ('allowed' not in tag_rule or replacement in tag_rule['allowed'])))
            correction = ({'value': replacement, 'type': 'list'}
                          if usable and len(json.dumps(replacement)) <= MAX_VALUE_BYTES else None)
            yield finding('tag.alias', note, 'tags', {'value': tags}, 'Configured aliases are present',
                          correction)


def audit(request):
    mapping(request, {'scope', 'inventory', 'conventions', 'observations'}, 'audit request')
    selected = select(request.get('scope'), request.get('inventory'))
    rules, aliases = conventions(request.get('conventions', {}))
    observations = request.get('observations', {})
    mapping(observations, set(selected['selected']), 'observations outside selected scope')
    findings = []
    for note in sorted(observations):
        observed = observations[note]
        require(isinstance(observed, dict), 'properties must be a verified JSON object')
        findings.extend(metadata(note, observed, rules, aliases))
    return {**selected, 'observed': sorted(observations),
            'unobserved': sorted(set(selected['selected']) - observations.keys()),
            'metadata_rules_configured': bool(rules or aliases), 'findings': findings}


def strict_object(pairs):
    result = dict(pairs)
    require(len(result) == len(pairs), 'duplicate JSON key')
    return result


def invalid_number(value):
    raise ValueError(f'invalid JSON number {value}')


def finite_float(value):
    number = float(value)
    require(math.isfinite(number), 'JSON number is out of range')
    return number


def main():
    try:
        data = sys.stdin.buffer.read(262145)
        require(len(data) <= 262144, 'audit request exceeds 256 KiB')
        request = json.loads(data.decode('utf-8'), object_pairs_hook=strict_object,
                             parse_constant=invalid_number, parse_float=finite_float)
        return emit_report(audit(request), 0)
    except (ValueError, RecursionError) as error:
        return emit_report({'status': 'blocked', 'error': str(error)}, 1)


if __name__ == '__main__':
    sys.exit(main())
