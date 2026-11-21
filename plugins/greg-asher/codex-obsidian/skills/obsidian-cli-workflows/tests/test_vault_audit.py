import json
from pathlib import Path
import subprocess
import sys
import unittest

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / 'scripts'))
from vault_audit import audit

FIXTURE = SKILL / 'assets' / 'fixtures' / 'audit'
SCOPE = {'folder': 'Atlas/Work', 'exclude_folders': ['Atlas/Work/Archive'],
         'exclude_files': ['Atlas/Work/Exception.md']}
SOURCE = 'Atlas/Work/Redirect review.md'
INVENTORY = sorted(path.relative_to(FIXTURE).as_posix() for path in FIXTURE.rglob('*.md'))
CONFIG = json.loads((FIXTURE / 'conventions.json').read_text())


class VaultAuditTests(unittest.TestCase):
    def test_scoped_selection_applies_boundaries_and_budget_before_reads(self):
        report = audit({'scope': {**SCOPE, 'max_notes': 1}, 'inventory': INVENTORY})
        self.assertEqual(report['selected'], ['Atlas/Work/ArchiveNotes/Vendor signoff - vendor.md'])
        self.assertEqual(report['excluded'], ['Atlas/Work/Archive/Previous rollout.md',
                                              'Atlas/Work/Exception.md'])
        self.assertEqual(report['deferred_count'], 5)
        self.assertEqual(report['unobserved'], report['selected'])
        with self.assertRaisesRegex(ValueError, 'outside selected scope'):
            audit({'scope': SCOPE, 'inventory': INVENTORY,
                   'observations': {'Atlas/Work/Exception.md': {}}})

    def test_fixture_metadata_subset_and_repeat(self):
        request = {'scope': SCOPE, 'inventory': INVENTORY, 'conventions': CONFIG,
                   'observations': {SOURCE: {'owner': "João O'Brien", 'hours': 2,
                                             'tags': ['atlas-old', 'security']},
                                    'Atlas/Work/Readiness.md': {'status': 'unknown', 'hours': 'two',
                                                                'due': '2026-02-30'}}}
        first = audit(request)['findings']
        self.assertEqual({(item['rule'], item['location']['property']) for item in first},
                         {('property.missing', 'status'), ('tag.alias', 'tags'),
                          ('property.type', 'hours'), ('property.type', 'due'),
                          ('property.value', 'status')})
        by_rule = {item['rule']: item for item in first}
        self.assertEqual(by_rule['tag.alias']['correction']['value'], ['atlas', 'security'])
        self.assertEqual(by_rule['property.missing']['correction']['value'], 'open')
        self.assertIsNone(by_rule['property.value']['correction'])
        request['observations'][SOURCE]['status'] = 'open'
        self.assertEqual(audit(request)['findings'],
                         [item for item in first if item['rule'] != 'property.missing'])
        del request['conventions']
        self.assertEqual(audit(request)['findings'], [])

    def test_null_differs_from_absence_and_valid_empty_values(self):
        observed = {'owner': '', 'hours': False, 'status': None, 'checked': False,
                    'labels': [], 'sizes': [0, 1.5, 'unknown']}
        properties = {**CONFIG['properties'], 'checked': {'type': 'checkbox', 'required': True},
                      'labels': {'type': 'list', 'required': True}, 'sizes': {'type': 'list'}}
        report = audit({'scope': {'paths': [SOURCE]}, 'inventory': [SOURCE],
                        'conventions': {'properties': properties},
                        'observations': {SOURCE: observed}})
        self.assertEqual([(item['rule'], item['location']['property']) for item in report['findings']],
                         [('property.type', 'hours'), ('property.type', 'status')])

    def test_tag_correction_preserves_other_values_and_avoids_duplicate(self):
        report = audit({'scope': SCOPE, 'inventory': INVENTORY, 'conventions': CONFIG,
                        'observations': {SOURCE: {'status': 'open', 'tags': ['atlas-old', 'ATLAS', 'sec']}}})
        self.assertEqual(report['findings'][0]['correction']['value'], ['ATLAS', 'sec'])

    def test_malformed_inputs_block(self):
        for override, message in (
            ({'scope': {'folder': '../Work'}}, 'vault-relative'),
            ({'scope': {'paths': ['Atlas/Work/Missing.md']}}, 'verify all selected'),
            ({'conventions': {'tag_aliases': {'a': 'b', 'b': 'a'}}}, 'chains or cycles'),
            ({'conventions': {'properties': {'hours': {'type': 'number', 'required': True,
                                                      'default': True}}}}, 'invalid missing-value default'),
        ):
            with self.subTest(override=override), self.assertRaisesRegex(ValueError, message):
                audit({'scope': SCOPE, 'inventory': INVENTORY, **override})
        result = subprocess.run([sys.executable, str(SKILL / 'scripts/vault_audit.py')],
                                input='{"scope": {}, "scope": {}}', text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('duplicate JSON key', json.loads(result.stdout)['error'])


if __name__ == '__main__':
    unittest.main()
