from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / 'scripts'))
from base_definition import plan

FIXTURES = SKILL / 'assets' / 'fixtures'
REQUEST = json.loads((FIXTURES / 'dashboard-request.json').read_text())
YAML_AVAILABLE = importlib.util.find_spec('yaml') is not None


class DefinitionTests(unittest.TestCase):
    def test_scoped_table_filters_and_configuration(self):
        result = plan(REQUEST)
        base = json.loads(result['content'])
        self.assertEqual(result['operation'], 'create-only')
        self.assertEqual(base['filters']['and'], ['file.ext == "md"', 'file.inFolder("Atlas/Work")'])
        view = base['views'][0]
        self.assertEqual(view['filters']['and'], ['note.status != null && note.status != "done"'])
        self.assertEqual(view['sort'], [{'property': 'note.due', 'direction': 'ASC'}])
        self.assertEqual(view['groupBy'], {'property': 'note.status', 'direction': 'ASC'})
        self.assertEqual(view['summaries'], {'formula.weighted': 'Sum'})
        self.assertEqual(base['formulas'], {'weighted': 'note.hours * 2'})

    def test_rejects_unknown_cycles_and_incompatible_summary(self):
        for formula, message in (
            ({'left': 'note.absent', 'op': '+', 'right': 1}, 'unknown property'),
            ({'left': 'formula.weighted', 'op': '+', 'right': 1}, 'circular'),
            ({'left': 'note.owner', 'op': '+', 'right': 1}, 'numeric'),
            ({'left': 'note.hours', 'op': '/', 'right': 0}, 'literal zero'),
        ):
            request = deepcopy(REQUEST)
            request['formulas']['weighted'] = formula
            with self.subTest(formula=formula), self.assertRaisesRegex(ValueError, message):
                plan(request)
        request = deepcopy(REQUEST)
        request['views'][0]['summaries'] = {'note.owner': 'Sum'}
        with self.assertRaisesRegex(ValueError, 'incompatible'):
            plan(request)

    def test_values_cannot_inject_expressions(self):
        request = deepcopy(REQUEST)
        request['folder'] = 'Work "special"'
        request['views'][0]['where'][0]['value'] = 'a" || true || "b'
        base = json.loads(plan(request)['content'])
        self.assertEqual(base['filters']['and'][1], 'file.inFolder("Work \\"special\\"")')
        self.assertEqual(base['views'][0]['filters']['and'][0],
                         'note.status != null && note.status != "a\\" || true || \\"b"')


@unittest.skipUnless(YAML_AVAILABLE, 'scoped edit tests require optional PyYAML')
class EditTests(unittest.TestCase):
    def setUp(self):
        self.before = (FIXTURES / 'existing.base').read_text()
        self.request = {'before': self.before, 'view': 'Open', 'schema': {'owner': 'text', 'status': 'text'},
                        'changes': {'columns': ['file.name', 'note.status'],
                                    'sort': [{'property': 'note.status', 'direction': 'ASC'}]}}

    def test_scoped_edit_preserves_unrelated_source_bytes(self):
        result = plan(self.request)
        expected = self.before.replace('    name: Open\n',
                                       '    sort: [{"property": "note.status", "direction": "ASC"}]\n'
                                       '    name: Open\n')
        expected = expected.replace('      - file.name\n      - note.owner',
                                    '      ["file.name", "note.status"]')
        self.assertEqual(result['operation'], 'overwrite')
        self.assertEqual(result['content'], expected)
        self.assertIn('note.status', result['diff'])

    def test_edit_accepts_flow_style_generated_definition(self):
        source = plan(REQUEST)['content']
        result = plan({'before': source, 'view': 'All work', 'schema': {'status': 'text'},
                       'changes': {'limit': 2}})
        data = json.loads(result['content'])
        self.assertEqual(data['views'][1]['limit'], 2)
        self.assertEqual(data['views'][0], json.loads(source)['views'][0])

    def test_malformed_duplicate_view_and_alias_block(self):
        for source, message in (('views: [', 'invalid or unsupported YAML'),
                                (self.before.replace('name: Other', 'name: Open'), 'unambiguous'),
                                (self.before.replace('flags: [keep, unchanged]', 'flags: &flag [keep]'), 'aliases')):
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                plan({**self.request, 'before': source})

    def test_non_table_and_conflicting_group_order_block(self):
        with self.assertRaisesRegex(ValueError, 'only existing table'):
            plan({**self.request, 'before': self.before.replace('type: table', 'type: cards', 1)})
        with self.assertRaisesRegex(ValueError, 'groupOrder'):
            plan({**self.request, 'before': self.before.replace('name: Open', 'name: Open\n    groupOrder: [open]'),
                  'changes': {'group': {'property': 'note.status', 'direction': 'ASC'}}})


if __name__ == '__main__':
    unittest.main()
