"""Synthetic pure guard tests; never import/run the container bootstrap locally."""
import ast
import copy
from pathlib import Path
import re
import unittest

from benchmarks.erpnext.structured import validate_lifecycle

HERE = Path(__file__).resolve().parents[1] / 'benchmarks/erpnext'


def load_retirement_guard():
    # Compile only our pure guard definition. The worker module's filesystem,
    # imports, database and command execution are never evaluated by this test.
    tree = ast.parse((HERE / 'app_bootstrap.py').read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'retirement_details')
    namespace = {'HOME': Path('/home/ci'), 're': re}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<pure-retirement-guard>', 'exec'), namespace)
    return namespace['retirement_details']


class SiteTargetTests(unittest.TestCase):
    def test_only_generated_local_databases_for_fixed_sites_are_eligible(self):
        guard = load_retirement_guard()
        config = {'db_socket': '/home/ci/mysql.sock', 'db_name': '_0123456789abcdef', 'db_user': '_0123456789abcdef'}
        for variant in ('base', 'head', 'baseline', 'feedback'):
            self.assertEqual(guard(variant, config), ('shadow-' + variant + '.localhost', config['db_name']))
        for variant, value in [('other', config), ('../base', config), ('base', None),
                               ('base', {**config, 'db_socket': '/var/run/mysqld.sock'}),
                               ('base', {**config, 'db_name': 'mysql'}),
                               ('base', {**config, 'db_user': 'other'}),
                               ('base', {**config, 'db_host': 'remote.example'})]:
            with self.assertRaises(ValueError): guard(variant, value)


class LifecycleTests(unittest.TestCase):
    def fixture(self):
        row = {'free_bytes_before': 100, 'free_bytes_after': 1000,
               'database_removed': True, 'active_site_removed': True}
        return {'schema': 1, 'sites': {name: dict(row) for name in ('base', 'head', 'baseline', 'feedback')}}

    def test_partial_data_is_retained_but_completion_requires_all_retired_sites(self):
        good = self.fixture()
        self.assertEqual(validate_lifecycle(good, True), good)
        partial = {'schema': 1, 'sites': {'base': good['sites']['base']}}
        self.assertEqual(validate_lifecycle(partial), partial)
        with self.assertRaises(ValueError): validate_lifecycle(partial, True)
        partial['sites']['base']['error_type'] = 'RuntimeError'
        self.assertEqual(validate_lifecycle(partial), partial)
        with self.assertRaises(ValueError): validate_lifecycle(partial, True)

    def test_wrong_shapes_types_extra_fields_and_failed_retirements_reject(self):
        for mutation in ('bool-schema', 'unknown-site', 'bad-row', 'bool-bytes', 'not-removed', 'extra-field', 'error'):
            value = copy.deepcopy(self.fixture());row = value['sites']['base']
            if mutation == 'bool-schema': value['schema'] = True
            if mutation == 'unknown-site': value['sites']['other'] = dict(row)
            if mutation == 'bad-row': value['sites']['base'] = None
            if mutation == 'bool-bytes': row['free_bytes_after'] = True
            if mutation == 'not-removed': row['database_removed'] = False
            if mutation == 'extra-field': row['unexpected_config_field'] = 'redacted'
            if mutation == 'error': row['error_type'] = 'RuntimeError'
            with self.assertRaises(ValueError, msg=mutation): validate_lifecycle(value, True)


class ActualLifecycleReplayTests(unittest.TestCase):
    """Read the actual hosted archive; this does not rerun ERPNext or a provider."""
    def test_actual_complete_pair_is_tied_and_has_no_authority(self):
        import json
        from benchmarks.erpnext.structured import score
        from framework.kernel import digest
        wrapper = json.loads((HERE / 'lifecycle-results.json').read_text())
        producer = json.loads((HERE / 'lifecycle-producer.json').read_text())
        manifest = json.loads((HERE / 'structured-candidates.json').read_text())
        self.assertEqual(digest(wrapper['report']), wrapper['record_sha256'])
        result = score(wrapper['report'], wrapper['record_sha256'], producer, manifest)
        self.assertTrue(result['valid_controls'], result)
        self.assertEqual(result['outcome'], 'passing-tie')
        for row in result['arms'].values():
            self.assertEqual(row['tests'], 5)
            self.assertTrue(row['earlier_four_preserved']);self.assertTrue(row['read_denial_satisfied'])
        for key in ('producer_authenticated', 'fresh_source_execution', 'policy_admitted', 'release_authority'):
            self.assertFalse(result[key])
        for row in wrapper['report']['site_lifecycle']['sites'].values():
            self.assertGreater(row['free_bytes_after'], row['free_bytes_before'])

    def test_actual_cli_selects_attempt_and_wrong_pin_never_shows_passes(self):
        import subprocess
        import sys
        argv = [sys.executable, '-B', '-m', 'benchmarks.erpnext.structured_review', '--attempt', 'lifecycle']
        result = subprocess.run(argv, cwd=HERE.parents[1], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('passing-tie', result.stdout)
        self.assertIn('Baseline author: 5/5 passed', result.stdout)
        self.assertIn('Feedback author: 5/5 passed', result.stdout)
        self.assertIn('No observed repair advantage', result.stdout)
        bad = subprocess.run(argv + ['--expected-record-sha256', '0' * 64],
                             cwd=HERE.parents[1], capture_output=True, text=True, timeout=10)
        self.assertEqual(bad.returncode, 1)
        self.assertIn('record identity mismatch', bad.stdout)
        self.assertNotIn('5/5 passed', bad.stdout)
