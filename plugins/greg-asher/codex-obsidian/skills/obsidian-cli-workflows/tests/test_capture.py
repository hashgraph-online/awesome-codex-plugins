import json
import subprocess
import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / 'scripts'))
from capture import plan

DATE = '2026-11-05'
FIXTURE = SKILL / 'assets/fixtures/capture'


class CaptureTests(unittest.TestCase):
    def test_five_recipes_have_expected_destinations_and_typed_properties(self):
        examples = {
            'idea': ('Inbox', {}),
            'meeting': ('Meetings', {'participants': ['Ana', 'João']}),
            'decision': ('Decisions', {'project_note': 'Atlas/Decision.md'}),
            'kickoff': ('Projects', {}),
            'source': ('Sources', {'url': 'https://example.org/article', 'published': '2025-04-16'}),
        }
        for recipe, (folder, fields) in examples.items():
            with self.subTest(recipe=recipe):
                item, = plan({'recipe': recipe, 'captured': DATE, 'fields': {
                    'title': 'Atlas / Café', 'body': 'A concrete outcome.', 'tags': ['atlas'], **fields,
                }})['items']
                self.assertEqual(item['path'], f'{folder}/{DATE} Atlas - Café.md')
                self.assertEqual(item['properties']['tags'], ['atlas'])
                self.assertIn('captured', item['date_properties'])
                self.assertEqual(item['policy'], 'create-only')
                if recipe == 'decision':
                    self.assertEqual(item['links'], ['Atlas/Decision.md'])
                    self.assertIn('[[Atlas/Decision.md|Project note]]', item['content'])

    def test_source_provenance_and_imported_syntax_stay_separate(self):
        excerpt = '![[Private/Payroll]]\n\n![image](https://example.invalid/a)\n```'
        item, = plan({'recipe': 'source', 'captured': DATE, 'fields': {
            'title': 'Example', 'body': 'My summary', 'url': 'https://example.org/article',
            'excerpt': excerpt,
        }})['items']
        self.assertEqual(item['properties']['source_title'], 'Example')
        self.assertEqual(item['properties']['source_url'], 'https://example.org/article')
        self.assertIn('Author: unknown.', item['content'])
        self.assertIn('## Summary\n\n    My summary', item['content'])
        self.assertIn('## Source excerpt\n\n    ![[Private/Payroll]]', item['content'])
        self.assertIn('\n\n    ![image]', item['content'])
        self.assertEqual(item['links'], [])
        with self.assertRaisesRegex(ValueError, 'wiki-link syntax'):
            plan({'recipe': 'source', 'captured': DATE, 'fields': {
                'title': 'Untrusted [[Private/Payroll]]', 'body': 'My summary',
                'url': 'https://example.org/article',
            }})

    def test_csv_unicode_quotes_newlines_and_blank_optional_cells(self):
        data = (FIXTURE / 'ideas.csv').read_text().replace('\n', '\r\n')
        request = {'recipe': 'idea', 'captured': DATE, 'batch': {
            'format': 'csv', 'data': '\ufeff' + data,
            'mapping': {'title': 'Headline', 'body': 'Notes', 'tags': 'Labels'},
        }}
        result = subprocess.run([sys.executable, '-B', str(SKILL / 'scripts/capture.py')],
                                input=json.dumps(request), text=True, capture_output=True, check=True)
        first, second = json.loads(result.stdout)['items']
        self.assertIn('Café', first['path'])
        self.assertIn('with "quotes".\n    Second line has $PATH and `ticks`.', first['content'])
        self.assertEqual(first['properties']['tags'], ['atlas', 'review'])
        self.assertNotIn('tags', second['properties'])

    def test_json_keeps_types_and_reports_row(self):
        data = (FIXTURE / 'meetings.json').read_text()
        request = {'recipe': 'meeting', 'captured': DATE, 'batch': {
            'format': 'json', 'data': data,
            'mapping': {'title': 'topic', 'body': 'minutes', 'participants': 'attendees', 'folder': 'folder'},
        }}
        self.assertEqual(plan(request)['items'][0]['properties']['participants'], ['Ana', 'João'])
        for value in ('null', 'false', '12', '"Ana"'):
            request['batch']['data'] = data.replace('["Ana"]', value)
            with self.assertRaisesRegex(ValueError, 'row 2.*participants'):
                plan(request)

    def test_json_optional_fields_can_be_omitted_per_row(self):
        request = {'recipe': 'idea', 'captured': DATE, 'batch': {
            'format': 'json',
            'data': '[{"title":"One","body":"First","tags":["atlas"]},{"title":"Two","body":"Second"}]',
            'mapping': {'title': 'title', 'body': 'body', 'tags': 'tags'},
        }}
        self.assertNotIn('tags', plan(request)['items'][1]['properties'])
        request['batch']['mapping']['tags'] = 'typo'
        with self.assertRaisesRegex(ValueError, 'mapped input key'):
            plan(request)

    def test_batch_rejects_collisions_and_duplicate_keys(self):
        request = {'recipe': 'idea', 'captured': DATE, 'batch': {
            'format': 'json',
            'data': json.dumps([{'title': 'Café', 'body': 'First'},
                                {'title': 'CAFE\u0301', 'body': 'Second'}]),
            'mapping': {'title': 'title', 'body': 'body'},
        }}
        with self.assertRaisesRegex(ValueError, 'rows 1 and 2'):
            plan(request)
        request['batch']['data'] = '[{"title":"a","title":"b","body":"c"}]'
        with self.assertRaisesRegex(ValueError, 'duplicate field'):
            plan(request)

    def test_batch_rejects_note_and_folder_collision_in_either_order(self):
        rows = [{'title': 'Café', 'body': 'First', 'folder': 'Inbox'},
                {'title': 'Child', 'body': 'Second', 'folder': f'inbox/{DATE} CAFE\u0301.md'}]
        request = {'recipe': 'idea', 'captured': DATE, 'batch': {
            'format': 'json',
            'mapping': {'title': 'title', 'body': 'body', 'folder': 'folder'},
        }}
        for ordered in (rows, rows[::-1]):
            request['batch']['data'] = json.dumps(ordered)
            with self.subTest(rows=ordered), self.assertRaisesRegex(ValueError, 'note and a folder'):
                plan(request)
        rows[1]['folder'] += '-archive'
        request['batch']['data'] = json.dumps(rows)
        self.assertEqual(len(plan(request)['items']), 2)

    def test_rejects_traversal_missing_fields_and_transport_ambiguity(self):
        request = {'recipe': 'idea', 'captured': DATE}
        for fields in ({'folder': '../Private'}, {'folder': 'C:/Windows'}, {'folder': 'Inbox/AUX'},
                       {'folder': '/root'}, {'body': 'literal \\n sequence'},
                       {'body': 'control\0text'}, {'tags': [3]}, {'unknown': 'value'}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                plan({**request, 'fields': {'title': 'Test', 'body': 'Content', **fields}})
        with self.assertRaisesRegex(ValueError, 'project_note'):
            plan({**request, 'recipe': 'decision', 'fields': {'title': 'Test', 'body': 'Content'}})


if __name__ == '__main__':
    unittest.main()
