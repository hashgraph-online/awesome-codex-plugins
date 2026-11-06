"""Use YAML source marks to change only approved fields in one existing view."""
import json

try:
    import yaml
except ImportError as error:
    raise ValueError('editing existing YAML requires PyYAML 6 in the selected Python environment') from error


def mapping(node):
    if not isinstance(node, yaml.MappingNode):
        raise ValueError('expected a YAML mapping')
    result = {}
    for key, value in node.value:
        if (not isinstance(key, yaml.ScalarNode) or key.tag != 'tag:yaml.org,2002:str' or
                key.value in result):
            raise ValueError('duplicate or unsupported YAML mapping key')
        result[key.value] = (key, value)
    return result


def parsed(source):
    for token in yaml.scan(source):
        if isinstance(token, (yaml.AnchorToken, yaml.AliasToken, yaml.TagToken)):
            raise ValueError('YAML anchors, aliases, and explicit tags block a scoped edit')
    tree = yaml.compose(source, Loader=yaml.SafeLoader)

    def inspect(node):
        if isinstance(node, yaml.MappingNode):
            for _, value in mapping(node).values():
                inspect(value)
        elif isinstance(node, yaml.SequenceNode):
            for child in node.value:
                inspect(child)

    inspect(tree)
    return tree, yaml.safe_load(source)


def last_mark(node):
    # Block collections can end at the next key. Only replace actual value bytes.
    if isinstance(node, yaml.MappingNode) and not node.flow_style and node.value:
        return last_mark(node.value[-1][1])
    if isinstance(node, yaml.SequenceNode) and not node.flow_style and node.value:
        return last_mark(node.value[-1])
    if isinstance(node, yaml.ScalarNode) and node.style in ('|', '>'):
        raise ValueError('replacing a block scalar is unsupported')
    return node.end_mark.index


def patch_view(before, name, make_changes):
    try:
        return splice_view(before, name, make_changes)
    except yaml.YAMLError as error:
        raise ValueError(f'invalid or unsupported YAML: {error}') from error


def splice_view(before, name, make_changes):
    root, expected = parsed(before)
    top = mapping(root)
    if 'views' not in top or not isinstance(top['views'][1], yaml.SequenceNode):
        raise ValueError('base needs a views sequence')
    sequence = top['views'][1]
    names = [item.get('name') if isinstance(item, dict) else None for item in expected['views']]
    if any(not isinstance(label, str) or not label for label in names) or len(set(names)) != len(names):
        raise ValueError('view names must be unambiguous')
    if name not in names:
        raise ValueError(f'view {name!r} does not exist')
    index = names.index(name)
    view = expected['views'][index]
    if view.get('type') != 'table':
        raise ValueError('only existing table views are editable')
    existing = expected.get('formulas', {})
    if not isinstance(existing, dict) or not all(isinstance(value, str) for value in existing.values()):
        raise ValueError('existing formulas must map names to expression strings')
    changes = make_changes(existing)
    if 'groupOrder' in view and 'groupBy' in changes and changes['groupBy'] != view.get('groupBy'):
        raise ValueError('existing groupOrder requires a separately reviewed change before regrouping')

    node = sequence.value[index]
    keys = mapping(node)
    patches, missing = [], []
    for key, value in changes.items():
        if key in view and view[key] == value:
            continue
        rendered = json.dumps(value, ensure_ascii=False, allow_nan=False)
        if key in keys:
            old = keys[key][1]
            start, end = old.start_mark.index, last_mark(old)
            patches.append((start, end, rendered))
        else:
            missing.append((key, rendered))
    if missing and node.flow_style:
        insert = node.end_mark.index - 1  # closing brace
        separator = '' if before[:insert].rstrip().endswith(',') else ','
        patches.append((insert, insert, separator + ' ' + ', '.join(
            f'{json.dumps(key)}: {rendered}' for key, rendered in missing)))
    elif missing:
        # The second key is on a regular mapping line, outside the sequence marker.
        mark = list(keys.values())[1][0].start_mark
        insert = mark.index - mark.column
        if before[insert:mark.index] != ' ' * mark.column:
            raise ValueError('cannot safely insert a field in this view layout')
        patches.append((insert, insert, ''.join(
            f'{" " * mark.column}{key}: {rendered}\n' for key, rendered in missing)))
    proposed = before
    for start, end, replacement in sorted(patches, reverse=True):
        proposed = proposed[:start] + replacement + proposed[end:]
    _, actual = parsed(proposed)
    view.update(changes)
    if actual != expected:
        raise ValueError('scoped edit could not preserve the existing YAML structure')
    return proposed
