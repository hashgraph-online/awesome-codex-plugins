"""Behavioral checks for the standalone SQP rollup CLI; no third-party packages."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RollupTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'evals/fixtures/theme-decisions.json').read_text())

    def run_rollup(self, data=None, valid=True):
        with tempfile.TemporaryDirectory() as directory:
            source, dest = Path(directory) / 'in.json', Path(directory) / 'out.json'
            source.write_text(json.dumps(self.data if data is None else data))
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/rollup_sqp.py'),
                                     '--input', str(source), '--output', str(dest)],
                                    text=True, capture_output=True)
            if not valid:
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(dest.exists())
                return result.stderr
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(dest.read_text())

    def theme(self, output, gram='large', relevance='exact', asin='B0TESTBED01'):
        return next(t for t in output['theme_rollups'] if gram in [t['gram'], *t['aliases']]
                    and t['relevance'] == relevance and t['scope']['asin'] == asin)

    def test_fixture_localizes_large_and_preserves_union_reach(self):
        out = self.run_rollup()
        large = self.theme(out)
        self.assertEqual(out['schema_version'], '2.1')
        self.assertEqual(large['member_ids'], ['q1', 'q2', 'q3'])
        self.assertEqual(large['theme']['asin_counts']['clicks'], 120)
        self.assertEqual(large['theme']['market']['impressions'], 12000)
        self.assertEqual(large['theme']['purchase_per_click']['asin'], .05)
        self.assertEqual(large['remainder']['purchase_per_click']['asin'], .1)
        self.assertEqual(large['theme']['relative_conversion_index'], .5)
        self.assertEqual(large['remainder']['relative_conversion_index'], 1)
        self.assertEqual([t['gram'] for t in out['theme_rollups'] if t['localized_gap_candidate']], ['large'])
        self.assertEqual(out['scope_totals'][0]['all_rows']['asin_counts']['clicks'], 240)
        self.assertFalse(self.theme(out, 'dog bed')['localized_gap_candidate'])
        self.assertEqual(self.theme(out, 'dog')['remainder']['member_ids'], [])

    def test_wilson_intervals(self):
        t = self.theme(self.run_rollup())
        for cohort, lower, upper in [('theme', .0231143644, .1048028854), ('remainder', .0581335920, .1666817411)]:
            ci = t[cohort]['purchase_per_click_interval']
            self.assertAlmostEqual(ci['lower'], lower)
            self.assertAlmostEqual(ci['upper'], upper)
            self.assertEqual(ci['confidence_level'], .95)
        for purchases, clicks in [(0, 20), (20, 20), (21, 20), (0, 0)]:
            data = copy.deepcopy(self.data)
            for row in data['rows']:
                row['asin_counts'].update(clicks=clicks, purchases=purchases)
                row['market'].update(clicks=100, purchases=100)
            ci = self.theme(self.run_rollup(data))['theme']['purchase_per_click_interval']
            if clicks == 0 or purchases > clicks:
                self.assertIsNone(ci['lower'])
                self.assertTrue(ci['unavailable_reason'])
            else:
                self.assertGreaterEqual(ci['lower'], 0)
                self.assertLessEqual(ci['upper'], 1)

    def test_duplicates_and_repeated_tokens_do_not_inflate(self):
        self.data['rows'][0]['query'] = 'large large dog bed'
        self.data['rows'].append(copy.deepcopy(self.data['rows'][0]))
        duplicate = copy.deepcopy(self.data['rows'][1]); duplicate['row_id'] = 'copy2'
        self.data['rows'].append(duplicate)
        out = self.run_rollup()
        self.assertEqual(self.theme(out)['theme']['asin_counts']['clicks'], 120)
        self.assertEqual(len(out['deduplicated_rows']), 2)
        conflict = copy.deepcopy(self.data['rows'][0]); conflict['asin_counts']['clicks'] += 1
        self.data['rows'].append(conflict)
        self.assertIn('conflict', self.run_rollup(valid=False).lower())

    def test_market_counts_separate_asins_and_validate_repeated_totals(self):
        other = copy.deepcopy(self.data['rows'])
        for row in other:
            row['asin'] = 'B0OTHER001'; row['row_id'] += '-other'
        self.data['rows'] += other
        out = self.run_rollup()
        self.assertEqual(self.theme(out, asin='B0OTHER001')['theme']['market']['clicks'], 600)
        other[0]['market']['clicks'] += 1
        self.assertIn('market', self.run_rollup(valid=False).lower())

    def test_scopes_do_not_mix(self):
        row = copy.deepcopy(self.data['rows'][0]); row['row_id'] = 'next-week'
        row.update(start='2026-10-11', end='2026-10-17')
        self.data['rows'].append(row)
        out = self.run_rollup()
        self.assertEqual(len(out['scope_totals']), 2)
        self.assertEqual(self.theme(out)['theme']['asin_counts']['clicks'], 120)

    def test_pools_thin_members_and_honors_overrides(self):
        for row in self.data['rows'][:3]:
            row['market']['impressions'] = 80; row['asin_counts'].update(impressions=40, clicks=10)
        out = self.run_rollup()
        self.assertTrue(self.theme(out)['theme']['gates']['volume'])
        self.data['config'] = {'minimum_market_impressions': 250}
        out = self.run_rollup()
        self.assertFalse(self.theme(out)['theme']['gates']['volume'])
        self.assertEqual(out['effective_thresholds']['minimum_market_impressions'], 250)

    def test_unknown_excluded_and_substitute_members_are_visible(self):
        self.data['rows'][0]['relevance'] = 'unknown'
        self.data['rows'][1]['relevance'] = 'irrelevant'
        out = self.run_rollup()
        t = self.theme(out)
        self.assertEqual(t['member_ids'], ['q3'])
        self.assertEqual(t['excluded_members'], [{'row_id': 'q1', 'relevance': 'unknown'}, {'row_id': 'q2', 'relevance': 'irrelevant'}])
        self.data['rows'][0]['relevance'] = 'substitute'
        out = self.run_rollup()
        self.assertEqual(self.theme(out, relevance='substitute')['member_ids'], ['q1'])
        self.assertNotIn('q1', self.theme(out)['remainder']['member_ids'])

    def test_aliases_and_order_are_deterministic(self):
        original = self.run_rollup()
        self.data['rows'].reverse()
        self.assertEqual(original, self.run_rollup())
        keys = [(tuple(t['member_ids']), t['relevance'], json.dumps(t['scope'], sort_keys=True)) for t in original['theme_rollups']]
        self.assertEqual(len(keys), len(set(keys)))

    def test_dominant_query_recomputed_and_not_recurring(self):
        self.data['rows'][0]['asin_counts']['clicks'] = 400
        self.data['rows'][0]['market'].update(clicks=800, purchases=80)
        t = self.theme(self.run_rollup())
        self.assertEqual(t['concentration']['leader_id'], 'q1')
        self.assertTrue(t['concentration']['dominant'])
        self.assertEqual(t['concentration']['without_leader']['member_ids'], ['q2', 'q3'])
        self.assertFalse(t['localized_gap_candidate'])

    def test_missing_counts_and_zero_market_denominator_withhold(self):
        self.data['rows'][0]['asin_counts']['purchases'] = None
        t = self.theme(self.run_rollup())
        self.assertIsNone(t['theme']['purchase_per_click']['asin'])
        self.assertFalse(t['localized_gap_candidate'])
        for row in self.data['rows']:
            row['market']['purchases'] = 0
            row['asin_counts']['purchases'] = 0
        self.assertIsNone(self.theme(self.run_rollup())['theme']['relative_conversion_index'])

    def test_malformed_input_is_actionable(self):
        for key, value in [('query_volume', -1), ('relevance', 'made_up'), ('end', '2026-10-11')]:
            data = copy.deepcopy(self.data); data['rows'][0][key] = value
            self.assertIn(key, self.run_rollup(data, valid=False))
        self.data['config'] = {'invented_threshold': 4}
        self.assertIn('config', self.run_rollup(valid=False))

    def test_asin_counts_cannot_exceed_same_stage_market_totals(self):
        for field in ('impressions', 'clicks', 'cart_adds', 'purchases'):
            data = copy.deepcopy(self.data)
            data['rows'][0]['market'][field] = 10
            data['rows'][0]['asin_counts'][field] = 11
            self.assertIn(field, self.run_rollup(data, valid=False))
        # Cross-stage event counts need not form a shopper-probability funnel.
        data = copy.deepcopy(self.data)
        for row in data['rows']:
            row['market'].update(clicks=10, purchases=30)
            row['asin_counts'].update(clicks=5, purchases=15)
        t = self.theme(self.run_rollup(data))
        self.assertEqual(t['theme']['purchase_per_click']['asin'], 3)
        self.assertIsNone(t['theme']['purchase_per_click_interval']['lower'])

    def test_supplied_tokens_preserve_constraints(self):
        self.data['rows'][0]['tokens'] = ['large', '40×30', 'dog', 'bed']
        self.assertEqual(self.theme(self.run_rollup(), '40×30')['member_ids'], ['q1'])


if __name__ == '__main__':
    unittest.main()
