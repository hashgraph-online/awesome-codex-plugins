#!/usr/bin/env python3
"""Count-based SQP theme rollups. Python 3.10+, standard library, no network calls."""
import argparse
import calendar
from datetime import date, timedelta
import json
import math
from pathlib import Path
import sys
import unicodedata

DEFAULTS = {
    'minimum_market_impressions': 200,
    'minimum_asin_clicks': 20,
    'minimum_queries': 3,
    'minimum_asin_purchases': 5,
    'dominant_click_fraction': .7,
    'maximum_theme_index': .8,
    'minimum_remainder_index': 1.,
}
COUNTS = ('impressions', 'clicks', 'cart_adds', 'purchases')
SCOPE = ('marketplace_id', 'period', 'start', 'end', 'asin')
LABELS = ('exact', 'substitute', 'complement', 'irrelevant', 'unknown')


def normalized(text):
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())


def count(value, field):
    if value is not None and (type(value) is not int or value < 0):
        raise ValueError(f'{field}: expected a nonnegative integer or null')


def scope_key(row):
    return tuple(row[key] for key in SCOPE)


def validate_period(row):
    try:
        start, end = date.fromisoformat(row['start']), date.fromisoformat(row['end'])
    except ValueError as error:
        raise ValueError('start/end: expected ISO dates') from error
    period = row['period']
    valid = False
    if period == 'WEEK':
        valid = start.weekday() == 6 and end == start + timedelta(days=6)
    elif period in ('MONTH', 'QUARTER'):
        months = 1 if period == 'MONTH' else 3
        last_month = start.month + months - 1
        valid = (start.day == 1 and last_month <= 12
                 and (months == 1 or start.month in (1, 4, 7, 10))
                 and end == date(start.year, last_month,
                                 calendar.monthrange(start.year, last_month)[1]))
    if not valid:
        raise ValueError('period/start/end: use one complete WEEK (Sunday–Saturday), MONTH or QUARTER')


def prepare(data):
    if not isinstance(data, dict) or not isinstance(data.get('rows'), list) or not data['rows']:
        raise ValueError('rows: provide a nonempty array of normalized SQP rows')
    config = data.get('config', {})
    if not isinstance(config, dict) or set(config) - DEFAULTS.keys():
        raise ValueError('config: unknown threshold or invalid object')
    thresholds = {**DEFAULTS, **config}
    for key, value in thresholds.items():
        if type(value) not in (float, int) or not math.isfinite(value) or value < 0:
            raise ValueError(f'config.{key}: expected a finite nonnegative number')
        if key in ('minimum_queries', 'minimum_market_impressions', 'minimum_asin_clicks', 'minimum_asin_purchases') and type(value) is not int:
            raise ValueError(f'config.{key}: expected an integer')
    if thresholds['minimum_queries'] < 1 or not 0 < thresholds['dominant_click_fraction'] <= 1:
        raise ValueError('config: minimum_queries must be positive and dominant_click_fraction in (0, 1]')
    records, ids, markets, duplicates = {}, {}, {}, []
    for original in sorted(data['rows'], key=lambda r: str(r.get('row_id', '')) if isinstance(r, dict) else ''):
        if not isinstance(original, dict):
            raise ValueError('rows: each entry must be an object')
        row = dict(original)
        for key in (*SCOPE, 'query', 'row_id'):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f'{key}: nonempty string required')
        validate_period(row)
        if row.get('relevance') not in LABELS:
            raise ValueError(f"{row['row_id']}.relevance: use {', '.join(LABELS)}")
        count(row.get('query_volume'), 'query_volume')
        row.setdefault('query_volume', None)
        for owner in ('market', 'asin_counts'):
            if not isinstance(row.get(owner), dict):
                raise ValueError(f"{row['row_id']}.{owner}: counts object required")
            row[owner] = {key: row[owner].get(key) for key in COUNTS}
            for key, value in row[owner].items():
                count(value, f"{row['row_id']}.{owner}.{key}")
        for field in COUNTS:
            market_count, asin_count = row['market'][field], row['asin_counts'][field]
            if market_count is not None and asin_count is not None and asin_count > market_count:
                raise ValueError(f"{row['row_id']}.{field}: ASIN count exceeds corresponding market total; reconcile source counts")
        query_key = normalized(row['query'])
        tokens = row.get('tokens', query_key.split())
        if not isinstance(tokens, list) or not tokens or any(not isinstance(t, str) or not t.strip() or len(t.split()) != 1 for t in tokens):
            raise ValueError(f"{row['row_id']}.tokens: nonempty list of single-token strings required")
        row['tokens'] = [normalized(token) for token in tokens]
        key = (*scope_key(row), query_key)
        comparable = {k: row[k] for k in ('query_volume', 'market', 'asin_counts', 'relevance', 'tokens')}
        if row['row_id'] in ids and ids[row['row_id']] != (key, comparable):
            raise ValueError(f"row_id conflict: {row['row_id']}")
        ids[row['row_id']] = (key, comparable)
        market_key = (*scope_key(row)[:-1], query_key)
        market_value = (row['market'], row['query_volume'])
        if market_key in markets and markets[market_key] != market_value:
            raise ValueError(f"market count/volume conflict: {row['query']}")
        markets[market_key] = market_value
        if key in records:
            previous = records[key]
            if {k: previous[k] for k in comparable} != comparable:
                raise ValueError(f"duplicate query conflict: {row['query']}")
            duplicates.append({'row_id': row['row_id'], 'retained_id': previous['row_id']})
        else:
            records[key] = row
    return list(records.values()), thresholds, duplicates


def total(rows, owner, field):
    values = [row[owner][field] if owner else row[field] for row in rows]
    return sum(values) if all(v is not None for v in values) else None


def ratio(numerator, denominator):
    return numerator / denominator if numerator is not None and denominator is not None and denominator > 0 else None


def wilson(purchases, clicks):
    interval = {'method': 'Wilson binomial approximation', 'confidence_level': .95,
                'lower': None, 'upper': None, 'unavailable_reason': None}
    if purchases is None or clicks is None or clicks <= 0 or not 0 <= purchases <= clicks:
        interval['unavailable_reason'] = 'Requires known counts with 0 <= purchases <= clicks and positive clicks'
        return interval
    z = 1.959963984540054
    p = purchases / clicks
    divisor = 1 + z*z / clicks
    center = (p + z*z / (2*clicks)) / divisor
    half = z * math.sqrt(p*(1-p)/clicks + z*z/(4*clicks*clicks)) / divisor
    interval.update(lower=max(0., center-half), upper=min(1., center+half))
    return interval


def cohort(rows, config):
    counts = {owner: {field: total(rows, owner, field) for field in COUNTS}
              for owner in ('market', 'asin_counts')}
    market, asin = counts['market'], counts['asin_counts']
    a_ratio = ratio(asin['purchases'], asin['clicks'])
    m_ratio = ratio(market['purchases'], market['clicks'])
    def at_least(value, minimum):
        return value is not None and value >= minimum
    gates = {
        'volume': bool(rows) and at_least(market['impressions'], config['minimum_market_impressions']) and at_least(asin['clicks'], config['minimum_asin_clicks']),
        'recurrence': len(rows) >= config['minimum_queries'],
        'purchase_evidence': bool(rows) and at_least(asin['purchases'], config['minimum_asin_purchases']) and (market['clicks'] or 0) > 0 and (market['purchases'] or 0) > 0,
    }
    return {**counts, 'member_ids': sorted(row['row_id'] for row in rows),
            'query_count': len(rows), 'query_volume': total(rows, None, 'query_volume'),
            'purchase_per_click': {'asin': a_ratio, 'market': m_ratio},
            'ctr': {'asin': ratio(asin['clicks'], asin['impressions']), 'market': ratio(market['clicks'], market['impressions'])},
            'relative_conversion_index': ratio(a_ratio, m_ratio),
            'purchase_per_click_interval': wilson(asin['purchases'], asin['clicks']),
            'gates': gates, 'data_sufficient': all(gates.values())}


def analyze(data):
    rows, config, duplicates = prepare(data)
    groups = {}
    for row in rows:
        groups.setdefault(scope_key(row), []).append(row)
    themes, scope_totals = [], []
    for key, scoped in sorted(groups.items()):
        scope = dict(zip(SCOPE, key))
        scope_totals.append({'scope': scope, 'all_rows': cohort(scoped, config),
                             'eligible_union': cohort([r for r in scoped if r['relevance'] in ('exact', 'substitute')], config)})
        grams = {}
        for row in scoped:
            tokens = row['tokens']
            unique = {tuple(tokens[i:i+n]) for n in (1, 2, 3) for i in range(len(tokens)-n+1)}
            for gram in unique:
                grams.setdefault(gram, []).append(row)
        slices = {}
        for gram, members in grams.items():
            for label in ('exact', 'substitute'):
                eligible = [r for r in members if r['relevance'] == label]
                if not eligible:
                    continue
                ids = tuple(sorted(r['row_id'] for r in eligible))
                # Alias only identical full membership, including exclusions, to preserve provenance.
                signature = (label, ids, tuple(sorted(r['row_id'] for r in members)))
                slices.setdefault(signature, []).append((gram, eligible, members))
        for (label, ids, _), variants in sorted(slices.items()):
            variants.sort(key=lambda v: (-len(v[0]), ' '.join(v[0])))
            gram, members, all_members = variants[0]
            remainder_rows = [r for r in scoped if r['relevance'] == label and r['row_id'] not in ids]
            theme, remainder = cohort(members, config), cohort(remainder_rows, config)
            known_clicks = theme['asin_counts']['clicks']
            leader = min(members, key=lambda r: (-(r['asin_counts']['clicks'] or 0), r['row_id']))
            fraction = ratio(leader['asin_counts']['clicks'], known_clicks)
            dominant = fraction is not None and fraction > config['dominant_click_fraction']
            without = cohort([r for r in members if r['row_id'] != leader['row_id']], config) if dominant else None
            index, rest_index = theme['relative_conversion_index'], remainder['relative_conversion_index']
            localized = (theme['data_sufficient'] and remainder['data_sufficient']
                         and index is not None and rest_index is not None
                         and index <= config['maximum_theme_index'] and rest_index >= config['minimum_remainder_index'])
            if dominant:
                reduced_index = without['relative_conversion_index']
                localized = localized and without['data_sufficient'] and reduced_index is not None and reduced_index <= config['maximum_theme_index']
            themes.append({'scope': scope, 'gram': ' '.join(gram), 'n': len(gram),
                           'aliases': sorted(' '.join(v[0]) for v in variants[1:]),
                           'relevance': label, 'member_ids': list(ids),
                           'excluded_members': sorted([{'row_id': r['row_id'], 'relevance': r['relevance']} for r in all_members if r['relevance'] != label], key=lambda x: x['row_id']),
                           'theme': theme, 'remainder': remainder,
                           'concentration': {'leader_id': leader['row_id'], 'click_fraction': fraction, 'dominant': dominant, 'without_leader': without},
                           'localized_gap_candidate': bool(localized)})
    return {'schema_version': '2.1', 'effective_thresholds': config,
            'interval_note': 'Descriptive binomial approximation; SQP events do not establish independent click trials. Observed gaps may be noise, not causal effects.',
            'rows': sorted(rows, key=lambda r: (scope_key(r), r['row_id'])),
            'deduplicated_rows': duplicates, 'scope_totals': scope_totals,
            'theme_rollups': sorted(themes, key=lambda t: (*t['scope'].values(), t['gram'], t['relevance']))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = analyze(json.loads(args.input.read_text()))
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    except (ValueError, OSError) as error:
        print(f'SQP input/output error: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
