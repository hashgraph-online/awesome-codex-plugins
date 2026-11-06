import json
from pathlib import Path
import sys
import unittest

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / 'scripts'))
from canvas_definition import loads, plan, transport
from canvas_layout import validate

FIXTURES = SKILL / 'assets' / 'fixtures'
BEFORE = (FIXTURES / 'existing.canvas').read_text()


class CanvasTests(unittest.TestCase):
    def test_three_layouts_have_stable_ids_and_evidence_labels(self):
        for name in ('project', 'research', 'process'):
            with self.subTest(name=name):
                request = loads((FIXTURES / f'{name}.json').read_text())
                report = plan(request)
                self.assertEqual(report, plan(request))
                document = loads(report['content'])
                self.assertFalse(validate(document)[1])
                self.assertFalse(report['extension_fields'])
                self.assertTrue(all(edge['label'].startswith(('Documented ·', 'Inferred ·'))
                                    for edge in document['edges']))
                self.assertTrue(all(edge['fromSide'] == 'right' and edge['toSide'] == 'left'
                                    for edge in document['edges']))
                if name == 'research':
                    self.assertIn('link', {item['type'] for item in document['nodes']})
                    self.assertIn('Café.md', report['references'][0]['path'])
                if name == 'project':
                    self.assertEqual(report['references'][0]['subpath'], '#Decision')
                    self.assertEqual(report['transport_escapes'], 1)

    def test_invalid_ids_edges_geometry_and_references(self):
        for key, value, message in (('id', 'group-a', 'duplicate ID'),
                                    ('width', True, 'invalid width'),
                                    ('file', '../Private.md', 'vault-relative'),
                                    ('subpath', 'Heading', 'subpath'),
                                    ('color', 'red', 'color must')):
            document = loads(BEFORE)
            document['nodes'][1][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, message):
                plan({'canvas': document})
        with self.assertRaisesRegex(ValueError, 'dangling'):
            plan({'before': BEFORE, 'remove': ['decision']})
        with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
            loads('{"nodes":[],"nodes":[]}')
        with self.assertRaisesRegex(ValueError, 'out of range'):
            loads('{"extension": 1e999}')

    def test_edit_preserves_order_extensions_and_raw_untouched_records(self):
        report = plan({'before': BEFORE, 'update': {'group-a': {'label': 'Reviewed decision'}}})
        expected = BEFORE.replace('"label":"Decision"', '"label":"Reviewed decision"').replace(
            r'\n', r'\u000a')
        self.assertEqual(report['content'], expected)
        before, after = loads(BEFORE), loads(report['content'])
        before['nodes'][0]['label'] = 'Reviewed decision'
        self.assertEqual(before, after)
        self.assertEqual(report['changes']['updated'], {'group-a': ['label']})
        self.assertTrue(report['extension_fields'])
        self.assertEqual(report['transport_escapes'], 1)

    def test_add_remove_maintains_existing_order(self):
        extra = {'id': 'extra', 'type': 'text', 'x': 530, 'y': 0, 'width': 360, 'height': 244,
                 'text': 'Literal ![[Private]]'}
        result = plan({'before': BEFORE, 'remove': ['next', 'edge-a'], 'add': {'nodes': [extra]}})
        doc = loads(result['content'])
        self.assertEqual([node['id'] for node in doc['nodes']], ['group-a', 'decision', 'extra'])
        self.assertEqual(doc['edges'], [])
        self.assertIn(r'\!\[\[Private\]\]', doc['nodes'][2]['text'])
        self.assertIn('"x-extension": {"owner": "preserve", "revision": 3}', result['content'])

    def test_new_layout_issues_block_and_existing_warnings_report(self):
        with self.assertRaisesRegex(ValueError, 'overlap'):
            plan({'before': BEFORE, 'update': {'next': {'x': 0}}})
        with self.assertRaisesRegex(ValueError, 'clipping'):
            plan({'before': BEFORE, 'update': {'next': {'height': 1}}})
        document = loads(BEFORE)
        document['nodes'][2]['x'] = 0
        self.assertTrue(validate(document)[1])
        project = loads(plan(loads((FIXTURES / 'project.json').read_text()))['content'])
        project['edges'][0]['label'] = 'Documented · ' + '長' * 32
        self.assertTrue(any('edge label clipping' in warning for warning in validate(project)[1]))

    def test_transport_preserves_json_newlines_tabs_and_literal_backslashes(self):
        data = {'line': 'one\ntwo\tthree', 'literal': r'C:\new\tab', 'other': r'a\b'}
        original = json.dumps(data)
        converted, count = transport(original)
        self.assertEqual(json.loads(converted), data)
        self.assertEqual(count, 4)
        self.assertNotIn(r'\n', converted)
        self.assertNotIn(r'\t', converted)

    def test_missing_reference_is_reported_for_live_resolution(self):
        report = plan(loads((FIXTURES / 'missing.json').read_text()))
        self.assertEqual(report['references'][0]['path'], 'Atlas/Intentionally Missing.md')
        self.assertEqual(report['references'][0]['subpath'], '#Missing')


if __name__ == '__main__':
    unittest.main()
