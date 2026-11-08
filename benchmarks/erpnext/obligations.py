"""Declared fixture coverage over pinned archived observations; no new checks."""
import json
import re

from framework.kernel import digest, sha as valid_sha
from .structured import HERE, TEST_SHA, VARIANTS, score

EXPECTED_COVERAGE_SHA256 = '4c48c3a1e5843ae07e48cecc02cd75266a2a69036e4efe13ab0e197b619c74f4'


def readable(value):
    return type(value) is str and 0 < len(value) <= 512 and value.isprintable()


def unavailable(reason, archive_outcome):
    return {'mode': 'declared-fixture-coverage', 'available': False, 'rows': [],
            'producer_authenticated': False, 'fresh_source_execution': False,
            'policy_admitted': False, 'release_authority': False,
            'reason': reason, 'archive_outcome': archive_outcome}


def review(report, record_pin, producer, manifest, coverage, coverage_pin):
    """Keep metadata approval, archive validity and observed test verdicts distinct."""
    archive = score(report, record_pin, producer, manifest)
    result = unavailable('coverage metadata unavailable', archive['outcome'])
    try:
        valid_sha(coverage_pin)
        if digest(coverage) != coverage_pin: raise ValueError('coverage metadata identity mismatch')
        case = json.loads((HERE / 'intermediate_case.json').read_text())
        if (type(coverage) is not dict or set(coverage) != {'schema', 'test_source_sha256', 'groups', 'limits'} or
                type(coverage['schema']) is not int or coverage['schema'] != 1 or
                coverage['test_source_sha256'] != TEST_SHA or type(coverage['groups']) is not list or
                len(coverage['groups']) != len(case['test_names']) or type(coverage['limits']) is not list or
                not 0 < len(coverage['limits']) <= 8 or not all(readable(x) for x in coverage['limits'])):
            raise ValueError('unsupported declared coverage metadata')
        ids, tests = set(), set()
        for group in coverage['groups']:
            if (type(group) is not dict or set(group) != {'id', 'test', 'title', 'scope'} or
                    not all(readable(group[k]) for k in group) or
                    not re.fullmatch('[a-z][a-z0-9-]{0,63}', group['id']) or
                    group['id'] in ids or group['test'] in tests):
                raise ValueError('invalid or duplicate coverage binding')
            ids.add(group['id']);tests.add(group['test'])
        if tests != set(case['test_names']): raise ValueError('coverage test inventory mismatch')
        if not archive['valid_controls']:
            raise ValueError('archive controls unavailable: ' + archive.get('reason', 'incomplete observations'))
        if report['sources']['heldout.py']['sha256'] != coverage['test_source_sha256']:
            raise ValueError('coverage source identity mismatch')
        prefix = case['test_module'] + '.' + case['test_class'] + '.'
        rows = []
        for group in coverage['groups']:
            verdicts = {}
            for variant in VARIANTS:
                if variant in ('baseline', 'feedback') and archive['arms'][variant]['status'] == 'inconclusive':
                    verdicts[variant] = 'unknown'
                else:
                    failures = report['observations'][variant]['runs'][0]['failure_ids']
                    verdicts[variant] = 'failed' if prefix + group['test'] in failures else 'passed'
            rows.append({**group, 'test_id': prefix + group['test'], 'verdicts': verdicts})
        result.update(available=True, rows=rows, limits=coverage['limits'], coverage_sha256=coverage_pin,
                      record_sha256=record_pin, test_source_sha256=coverage['test_source_sha256'])
        result.pop('reason', None)
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as exc:
        result['reason'] = str(exc)
    return result


def summary(result):
    if not result['available']:
        return 'Declared fixture coverage unavailable: ' + json.dumps(result.get('reason', 'incomplete'), ensure_ascii=True)
    lines = ['Declared fixture coverage (whole test groups only):']
    for row in result['rows']:
        v = row['verdicts']
        lines.extend(['- ' + row['title'],
                      f'  unchanged={v["base"]}; upstream={v["head"]}; baseline author={v["baseline"]}; feedback author={v["feedback"]}',
                      '  Test: ' + row['test'],
                      '  Scope: ' + row['scope']])
    lines.extend('Limit: ' + value for value in result['limits'])
    return '\n'.join(lines)
