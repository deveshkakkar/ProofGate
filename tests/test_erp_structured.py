"""Static synthetic transport/scoring checks; no upstream source execution."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from benchmarks.erpnext.structured import (BASE_SHA, HEAD_SHA, TEST_SHA, FILES,
                                          prepare_candidates, candidate_verdict, score)
from framework.kernel import digest

HERE = Path(__file__).resolve().parents[1] / 'benchmarks/erpnext'


class FixedCandidateInputTests(unittest.TestCase):
    def fixture(self):
        source = 'def value():\n    return 1\n'
        pin = hashlib.sha256(source.encode()).hexdigest()
        candidate = source.replace('return 1', 'return 2')
        row = {'eligible': True, 'proposal': {'schema': 1, 'source_sha256': pin,
               'edits': [{'old': 'return 1', 'new': 'return 2'}]},
               'module_sha256': hashlib.sha256(candidate.encode()).hexdigest()}
        manifest = {'schema': 1, 'protocol': 'structured-exact-text-v2', 'source_sha256': pin,
                    'base_revision': '04afe19d8ef067eec3852f4ac8007af42718d0b6',
                    'arms': {'baseline': copy.deepcopy(row), 'feedback': copy.deepcopy(row)}}
        return source, pin, candidate, manifest

    def test_fixed_paths_and_both_candidates_validated_before_any_write(self):
        source, pin, candidate, manifest = self.fixture()
        with tempfile.TemporaryDirectory() as temporary, patch('benchmarks.erpnext.structured.BASE_SHA', pin):
            root = Path(temporary)
            prepare_candidates(source, manifest, root)
            self.assertEqual((root / 'baseline-report.py').read_text(), candidate)
            self.assertEqual((root / 'feedback-report.py').read_text(), candidate)
            self.assertEqual(json.loads((root / 'structured-variants.json').read_text()),
                             ['base', 'head', 'baseline', 'feedback'])
        manifest['arms']['feedback']['module_sha256'] = '0' * 64
        with tempfile.TemporaryDirectory() as temporary, patch('benchmarks.erpnext.structured.BASE_SHA', pin):
            root = Path(temporary)
            with self.assertRaises(ValueError): prepare_candidates(source, manifest, root)
            self.assertEqual(list(root.iterdir()), [])

    def test_wrong_base_ineligible_unknown_arm_and_malformed_proposals_reject(self):
        for mutation in ('source', 'ineligible', 'arm', 'proposal', 'bool-schema'):
            source, pin, _, manifest = self.fixture()
            if mutation == 'source': source += '# changed\n'
            if mutation == 'ineligible': manifest['arms']['feedback']['eligible'] = False
            if mutation == 'arm': manifest['arms']['other'] = manifest['arms'].pop('feedback')
            if mutation == 'proposal': manifest['arms']['feedback']['proposal']['path'] = '../other.py'
            if mutation == 'bool-schema': manifest['schema'] = True
            with tempfile.TemporaryDirectory() as temporary, patch('benchmarks.erpnext.structured.BASE_SHA', pin):
                root = Path(temporary)
                with self.assertRaises(ValueError, msg=mutation): prepare_candidates(source, manifest, root)
                self.assertEqual(list(root.iterdir()), [])


class StructuredScoreTests(unittest.TestCase):
    """Four-variant synthetic observations extend the archived two-control fixture."""
    def setUp(self):
        self.manifest = json.loads((HERE / 'structured-candidates.json').read_text())
        self.report = copy.deepcopy(json.loads((HERE / 'intermediate-results.json').read_text())['report'])
        r = self.report
        r['profile'] = 'structured';r['candidate_manifest_sha256'] = digest(self.manifest)
        r['site_lifecycle'] = {'schema': 1, 'sites': {name: {'free_bytes_before': 100, 'free_bytes_after': 1000,
            'database_removed': True, 'active_site_removed': True} for name in ('base', 'head', 'baseline', 'feedback')}}
        r['verifier'] = {name: hashlib.sha256((HERE / ('intermediate_case.json' if name == 'app_case.json' else name)).read_bytes()).hexdigest()
                         for name in FILES}
        for arm in ('baseline', 'feedback'):
            sha = self.manifest['arms'][arm]['module_sha256']
            r['sources'][arm + '-report.py'] = {'sha256': sha}
            r['observations'][arm] = copy.deepcopy(r['observations']['head'])
            for key in ('source_before', 'source_after'):
                r['observations'][arm][key]['module_sha256'] = sha
        self.producer = {'schema': 1, 'revision': 'a' * 40, 'case': r['case'], 'verifier': copy.deepcopy(r['verifier']),
                         'candidate_manifest_sha256': digest(self.manifest), 'environment_sha256': digest(r['environment']),
                         'isolation_sha256': digest(r['isolation']),
                         'control_predicate_source_sha256': json.loads((HERE / 'producer-profiles.json').read_text())['profiles'][0]['control_predicate_source_sha256']}

    def check(self): return score(self.report, digest(self.report), self.producer, self.manifest)

    def test_complete_synthetic_pair_and_all_authority_flags(self):
        result = self.check()
        self.assertTrue(result['valid_controls'], result)
        self.assertEqual(result['outcome'], 'passing-tie')
        for row in result['arms'].values():
            self.assertTrue(row['earlier_four_preserved']);self.assertTrue(row['read_denial_satisfied'])
        for key in ('producer_authenticated', 'fresh_source_execution', 'policy_admitted', 'release_authority'):
            self.assertFalse(result[key])

    def test_failed_candidate_does_not_invalidate_good_controls_or_count_as_pass(self):
        row = self.report['observations']['baseline']['runs'][0]
        row['failure_ids'] = [row['test_ids'][-1]]
        result = self.check()
        self.assertTrue(result['valid_controls'], result)
        self.assertEqual(result['outcome'], 'feedback-only-passed')
        self.assertTrue(result['arms']['baseline']['earlier_four_preserved'])
        self.assertFalse(result['arms']['baseline']['read_denial_satisfied'])
        row['failure_ids'] = [row['test_ids'][0]]
        result = self.check()
        self.assertFalse(result['arms']['baseline']['earlier_four_preserved'])
        self.assertTrue(result['arms']['baseline']['read_denial_satisfied'])

    def test_missing_duplicate_errors_skips_bool_counts_and_bad_exit_are_inconclusive(self):
        original = copy.deepcopy(self.report['observations']['baseline'])
        for mutation in ('missing', 'duplicate', 'errors', 'skips', 'xfail', 'bool', 'bad-exit'):
            obs = copy.deepcopy(original);row = obs['runs'][0]
            if mutation == 'missing': row['test_ids'].pop()
            if mutation == 'duplicate': row['test_ids'][-1] = row['test_ids'][0]
            if mutation == 'errors': row['error_ids'] = row['test_ids'][:1]
            if mutation == 'skips': row['skipped_ids'] = row['test_ids'][:1]
            if mutation == 'xfail': row['expected_failure_ids'] = row['test_ids'][:1]
            if mutation == 'bool': row['tests'] = True
            if mutation == 'bad-exit': obs['transport_exit'] = 1
            self.report['observations']['baseline'] = obs
            result = self.check()
            self.assertTrue(result['valid_controls'], result)
            self.assertEqual(result['outcome'], 'inconclusive', mutation)

    def test_wrong_record_reviewed_manifest_environment_verifier_source_and_controls_reject(self):
        self.assertFalse(score(self.report, '0' * 64, self.producer, self.manifest)['valid_controls'])
        original = copy.deepcopy(self.report)
        for mutation in ('manifest', 'environment', 'verifier', 'source', 'control', 'missing-arm', 'test', 'lifecycle'):
            self.report = copy.deepcopy(original);r = self.report
            if mutation == 'manifest': r['candidate_manifest_sha256'] = '0' * 64
            if mutation == 'environment': r['environment']['packages'] = []
            if mutation == 'verifier': r['verifier']['app_bootstrap.py'] = '0' * 64
            if mutation == 'source': r['observations']['baseline']['source_after']['module_sha256'] = '0' * 64
            if mutation == 'control': r['observations']['base']['runs'][0]['failure_ids'] = []
            if mutation == 'missing-arm': r['observations'].pop('feedback')
            if mutation == 'test': r['sources']['heldout.py']['sha256'] = '0' * 64
            if mutation == 'lifecycle': r['site_lifecycle']['sites']['feedback']['database_removed'] = False
            self.assertFalse(self.check()['valid_controls'], mutation)

    def test_malformed_top_level_inputs_fail_closed(self):
        for value in (None, [], True, {}):
            self.assertFalse(score(value, digest(value), self.producer, self.manifest)['valid_controls'])
            self.assertFalse(score(self.report, digest(self.report), value, self.manifest)['valid_controls'])
            self.assertFalse(score(self.report, digest(self.report), self.producer, value)['valid_controls'])


class StructuredReviewTests(unittest.TestCase):
    """Presentation fixtures are synthetic; actual CLI evidence follows runtime."""
    def test_invalid_controls_never_show_passing_candidates(self):
        from benchmarks.erpnext.structured_review import summary
        text = summary({'valid_controls': False, 'outcome': 'inconclusive', 'reason': 'wrong pin'})
        self.assertNotIn('passed', text)
        self.assertIn('Controls unverified', text)
        self.assertIn('no fresh execution', text)

    def test_complete_pair_separates_control_and_author_success_from_advantage(self):
        from benchmarks.erpnext.structured_review import summary
        row = {'status': 'passed', 'tests': 5, 'failure_ids': [],
               'earlier_four_preserved': True, 'read_denial_satisfied': True}
        result = {'valid_controls': True, 'outcome': 'passing-tie', 'arms': {'baseline': row, 'feedback': row},
                  'record_sha256': 'a' * 64}
        text = summary(result)
        self.assertIn('Baseline author: 5/5 passed', text)
        self.assertIn('Feedback author: 5/5 passed', text)
        self.assertIn('No observed repair advantage', text)
        self.assertIn('no fresh execution, producer authentication, policy admission or release authority', text)
        result['arms']['feedback'] = {'status': 'inconclusive'};result['outcome'] = 'inconclusive'
        text = summary(result)
        self.assertIn('Feedback author: inconclusive', text)
        self.assertNotIn('Feedback author: 5/5', text)
        self.assertNotIn('No observed repair advantage', text)


class FailureCaptureTests(unittest.TestCase):
    def test_partial_results_survive_missing_later_site_without_inventing_success(self):
        from benchmarks.erpnext.app_trial import capture_observations, classify
        old = json.loads((HERE / 'intermediate-results.json').read_text())['report']
        payloads = {name: json.dumps(row).encode() for name, row in old['observations'].items()}
        partial = {'schema': 1, 'runs': [], 'transport_exit': 1}
        payloads['baseline'] = json.dumps(partial).encode()
        def read(name):
            if name not in payloads: raise FileNotFoundError(name)
            return payloads[name]
        observations, errors = capture_observations(('base', 'head', 'baseline', 'feedback'), read)
        self.assertEqual(set(observations), {'base', 'head', 'baseline'})
        self.assertEqual(observations['baseline'], partial)
        self.assertEqual(errors, {'feedback': 'FileNotFoundError'})
        self.assertFalse(classify(old['case'], observations['baseline'], 'head'))

    def test_malformed_oversized_or_deep_data_records_errors_without_aborting_capture(self):
        from benchmarks.erpnext.app_trial import capture_observations
        for bad in (b'not JSON', b'[]', b'x' * (1048576 + 1), b'[' * 2000 + b']' * 2000):
            def read(name): return bad if name == 'base' else b'{"schema":1,"runs":[]}'
            observations, errors = capture_observations(('base', 'head'), read)
            self.assertEqual(set(observations), {'head'})
            self.assertEqual(set(errors), {'base'})

    def test_arbitrary_variant_names_never_reach_reader(self):
        from benchmarks.erpnext.app_trial import capture_observations
        called = []
        with self.assertRaises(ValueError):
            capture_observations(('base', '../config'), lambda name: called.append(name))
        self.assertEqual(called, [])


class ActualIncompleteReplayTests(unittest.TestCase):
    """Actual failed run, never promoted from partial logs to valid controls."""
    def test_failed_application_report_stays_inconclusive(self):
        wrapper = json.loads((HERE / 'structured-results.json').read_text())
        producer = json.loads((HERE / 'structured-producer.json').read_text())
        manifest = json.loads((HERE / 'structured-candidates.json').read_text())
        self.assertEqual(digest(wrapper['report']), wrapper['record_sha256'])
        self.assertFalse(wrapper['report']['completed'])
        self.assertNotIn('observations', wrapper['report'])
        result = score(wrapper['report'], wrapper['record_sha256'], producer, manifest)
        self.assertFalse(result['valid_controls'])
        self.assertEqual(result['outcome'], 'inconclusive')
        self.assertNotIn('arms', result)

    def test_actual_review_cli_reports_failure_and_wrong_pin_never_shows_passes(self):
        import subprocess
        import sys
        for flags, expected in (([], 'application-controls exit=1'),
                                (['--expected-record-sha256', '0' * 64], 'record identity mismatch')):
            proc = subprocess.run([sys.executable, '-B', '-m', 'benchmarks.erpnext.structured_review', *flags],
                                  cwd=HERE.parents[1], text=True, capture_output=True, timeout=10)
            self.assertEqual(proc.returncode, 1, proc.stderr)
            self.assertIn('Archived paired replay: inconclusive', proc.stdout)
            self.assertIn(expected, proc.stdout)
            self.assertNotIn('5/5 passed', proc.stdout)
