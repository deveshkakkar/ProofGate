import copy
import hashlib
import json
from pathlib import Path
import unittest

from benchmarks.erpnext.module_edits import apply_edits, MAX_BYTES
from benchmarks.erpnext.paired import apply_diff, parse_diff
from framework.kernel import digest

ROOT = Path(__file__).resolve().parents[1] / 'benchmarks/erpnext'


class RawDiffTests(unittest.TestCase):
    def test_both_actual_author_outputs_stay_inconclusive(self):
        wrapper = json.loads((ROOT / 'paired-author-results.json').read_text())
        record = wrapper['record']
        self.assertEqual(digest(record), wrapper['record_sha256'])
        self.assertEqual(record['outcome'], 'inconclusive')
        self.assertEqual(record['hosted_attempts_used'], 0)
        self.assertFalse(record['application_execution'])
        self.assertEqual(set(record['arms']), {'baseline', 'feedback'})
        for row in record['arms'].values():
            self.assertEqual(hashlib.sha256(row['raw_patch'].encode()).hexdigest(), row['raw_output_sha256'])
            self.assertFalse(row['strict_eligible'])
            with self.assertRaisesRegex(ValueError, 'declared 6/8, supplied 5/7'):
                parse_diff(row['raw_patch'])

    def test_exact_diff_applies_with_no_source_execution(self):
        source = 'def value():\n    return 1\n'
        patch = '--- a/report.py\n+++ b/report.py\n@@ -1,2 +1,2 @@\n def value():\n-    return 1\n+    return 2\n'
        self.assertEqual(apply_diff(source, patch), 'def value():\n    return 2\n')
        with self.assertRaisesRegex(ValueError, 'context mismatch'):
            apply_diff(source.replace('return 1', 'return 3'), patch)

    def test_other_paths_extra_files_and_bad_counts_reject(self):
        patch = '--- a/report.py\n+++ b/report.py\n@@ -1 +1 @@\n-a = 1\n+a = 2\n'
        for changed in (patch.replace('report.py', '../other.py'), patch + patch,
                        patch.replace('@@ -1 +1 @@', '@@ -1,2 +1,2 @@')):
            with self.assertRaises(ValueError): apply_diff('a = 1\n', changed)

    def test_offsets_are_not_guessed_and_invalid_python_rejects(self):
        patch = '--- a/report.py\n+++ b/report.py\n@@ -2 +2 @@\n-a = 1\n+a = 2\n'
        with self.assertRaises(ValueError): apply_diff('a = 1\n', patch)
        with self.assertRaises(SyntaxError):
            apply_diff('a = 1\n', patch.replace('-2 +2', '-1 +1').replace('+a = 2', '+def :'))


class StructuredEditTests(unittest.TestCase):
    def setUp(self):
        self.source = 'first = 1\nsecond = 2\n'
        self.pin = hashlib.sha256(self.source.encode()).hexdigest()
        self.proposal = {'schema': 1, 'source_sha256': self.pin,
                         'edits': [{'old': 'first = 1', 'new': 'first = 3'}]}

    def test_exact_unique_edit_returns_text_without_writes(self):
        self.assertEqual(apply_edits(self.source, self.pin, self.proposal), 'first = 3\nsecond = 2\n')

    def test_all_edits_match_original_not_intermediate_text(self):
        self.proposal['edits'] = [{'old': 'first = 1', 'new': 'second = 2'},
                                  {'old': 'second = 2', 'new': 'last = 4'}]
        self.assertEqual(apply_edits(self.source, self.pin, self.proposal), 'second = 2\nlast = 4\n')
        self.proposal['edits'][1]['old'] = 'created by previous edit'
        with self.assertRaises(ValueError): apply_edits(self.source, self.pin, self.proposal)

    def test_wrong_source_and_untrusted_proposal_pin_reject(self):
        with self.assertRaises(ValueError): apply_edits(self.source + '# changed\n', self.pin, self.proposal)
        self.proposal['source_sha256'] = '0' * 64
        with self.assertRaises(ValueError): apply_edits(self.source, self.pin, self.proposal)

    def test_missing_ambiguous_overlapping_duplicate_or_noop_edits_reject(self):
        for edits in ([{'old': 'missing', 'new': 'x'}], [{'old': '=', 'new': ':'}],
                      [{'old': 'first', 'new': 'x'}, {'old': 'first =', 'new': 'y'}],
                      [self.proposal['edits'][0]] * 2, [{'old': 'first', 'new': 'first'}],
                      [{'old': '', 'new': 'x'}]):
            with self.assertRaises(ValueError):
                apply_edits(self.source, self.pin, {**self.proposal, 'edits': edits})

    def test_shape_types_paths_and_size_limits_reject(self):
        for mutation in ('bool-schema', 'extra-path', 'not-object', 'empty', 'too-many', 'bad-entry', 'bool-text', 'huge'):
            proposal = copy.deepcopy(self.proposal)
            if mutation == 'bool-schema': proposal['schema'] = True
            if mutation == 'extra-path': proposal['path'] = '/etc/config'
            if mutation == 'not-object': proposal = []
            if mutation == 'empty': proposal['edits'] = []
            if mutation == 'too-many': proposal['edits'] *= 9
            if mutation == 'bad-entry': proposal['edits'] = [None]
            if mutation == 'bool-text': proposal['edits'][0]['new'] = True
            if mutation == 'huge': proposal['edits'][0]['new'] = 'x' * (MAX_BYTES + 1)
            with self.assertRaises(ValueError, msg=mutation): apply_edits(self.source, self.pin, proposal)

    def test_overlapping_occurrences_and_oversized_result_reject(self):
        source = 'aaa';pin = hashlib.sha256(source.encode()).hexdigest()
        with self.assertRaises(ValueError):
            apply_edits(source, pin, {'schema': 1, 'source_sha256': pin, 'edits': [{'old': 'aa', 'new': 'b'}]})
        self.proposal['edits'][0]['new'] = 'x' * MAX_BYTES
        with self.assertRaises(ValueError): apply_edits(self.source, self.pin, self.proposal)
