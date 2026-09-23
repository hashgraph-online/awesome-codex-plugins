"""Export verified learning cards to Anki TSV; no network or scheduling."""
import argparse
import csv
import html
import io
import json
from pathlib import Path
import re
import sys


def text_field(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name} must be a non-empty string')
    if any(ord(c) < 32 and c not in '\r\n\t' for c in value):
        raise ValueError(f'{name} contains unsupported control characters')
    return value.strip().replace('\r\n', '\n').replace('\r', '\n')


def render(value):
    return html.escape(value, quote=True).replace('\t', '    ').replace('\n', '<br>')


def build_tsv(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get('cards'), list):
        raise ValueError('Expected an object with a cards array')
    if not payload['cards']:
        raise ValueError('At least one card is required')
    rows, ids, fronts = [], set(), set()
    for index, card in enumerate(payload['cards'], 1):
        if not isinstance(card, dict):
            raise ValueError(f'Card {index} must be an object')
        card_id = text_field(card.get('id'), 'id')
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', card_id):
            raise ValueError('id must contain 1-100 ASCII letters, digits, underscores or hyphens')
        front = text_field(card.get('front'), 'front')
        back = text_field(card.get('back'), 'back')
        rendered_front = render(front)
        if card_id in ids or rendered_front in fronts:
            raise ValueError(f'Duplicate id or front at card {index}')
        ids.add(card_id)
        fronts.add(rendered_front)
        source = card.get('source', '')
        if not isinstance(source, str):
            raise ValueError('source must be a string')
        source = text_field(source, 'source') if source.strip() else ''
        tags = card.get('tags', [])
        if not isinstance(tags, list) or any(
            not isinstance(t, str) or not re.fullmatch(r'[\w:-]+', t) for t in tags
        ):
            raise ValueError('tags must be letters/digits/underscore/colon/hyphen strings')
        rendered_back = render(back)
        if source:
            rendered_back += '<br><br>来源：' + render(source)
        rows.append([rendered_front, rendered_back,
                     ' '.join(dict.fromkeys(['learning', f'learning-id::{card_id}', *tags]))])
    output = io.StringIO(newline='')
    output.write('#separator:Tab\n#html:true\n#tags column:3\n#columns:Front\tBack\tTags\n')
    # Quote all rows so a question beginning with # is not read as an import comment.
    csv.writer(output, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_ALL).writerows(rows)
    return output.getvalue()


def export(source, destination, overwrite=False):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve() or (
        source.exists() and destination.exists() and source.samefile(destination)
    ):
        raise ValueError('Input and output must be different files')
    if source.suffix.lower() != '.json' or destination.suffix.lower() != '.tsv':
        raise ValueError('Use a .json input and a .tsv output')
    content = build_tsv(json.loads(source.read_text(encoding='utf-8-sig')))
    with destination.open('w' if overwrite else 'x', encoding='utf-8', newline='') as stream:
        stream.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    try:
        export(args.input, args.output, args.overwrite)
    except (OSError, ValueError) as error:
        print(f'Export failed: {error}', file=sys.stderr)
        return 1
    print(f'Created {args.output}. Import into Anki to schedule reviews; no import was performed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
