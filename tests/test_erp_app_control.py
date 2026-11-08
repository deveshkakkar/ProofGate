import copy
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from benchmarks.erpnext.app_trial import classify, extract


class AppControlTests(unittest.TestCase):
    def setUp(self):
        self.case = json.loads((Path(__file__).resolve().parents[1] /
                                'benchmarks/erpnext/app_case.json').read_text())
        prefix = self.case['test_module'] + '.' + self.case['test_class'] + '.'
        self.ids = [prefix + name for name in self.case['test_names']]
        self.row = {'test_ids': self.ids, 'tests': len(self.ids), 'failure_ids': [],
                    'error_ids': [], 'skipped_ids': [], 'expected_failure_ids': [], 'unexpected_success_ids': []}

    def test_generic_rejection_is_not_a_reproduced_control(self):
        self.assertTrue(classify(self.case, {'schema': 1, 'transport_exit': 0, 'runs': [self.row]}, 'head'))
        self.assertFalse(classify(self.case, {'schema': 1, 'transport_exit': 0, 'runs': [self.row]}, 'base'))
        row = copy.deepcopy(self.row)
        prefix = self.case['test_module'] + '.' + self.case['test_class'] + '.'
        row['failure_ids'] = [prefix + n for n in self.case['original_failure_names']]
        self.assertTrue(classify(self.case, {'schema': 1, 'transport_exit': 0, 'runs': [row]}, 'base'))
        row['failure_ids'][0] = self.ids[0]
        self.assertFalse(classify(self.case, {'schema': 1, 'transport_exit': 0, 'runs': [row]}, 'base'))

    def test_missing_duplicate_skipped_errors_and_xfails_never_pass(self):
        for mutation in ('missing', 'duplicate', 'skip', 'error', 'xfail', 'extra-run', 'bool-count', 'bool-schema'):
            row = copy.deepcopy(self.row);obs = {'schema': 1, 'transport_exit': 0, 'runs': [row]}
            if mutation == 'missing': row['test_ids'].pop()
            if mutation == 'duplicate': row['test_ids'][-1] = row['test_ids'][0]
            if mutation == 'skip': row['skipped_ids'] = row['test_ids'][:1]
            if mutation == 'error': row['error_ids'] = row['test_ids'][:1]
            if mutation == 'xfail': row['expected_failure_ids'] = row['test_ids'][:1]
            if mutation == 'extra-run': obs['runs'].append(copy.deepcopy(row))
            if mutation == 'bool-count': row['tests'] = True
            if mutation == 'bool-schema': obs['schema'] = True
            self.assertFalse(classify(self.case, obs, 'head'), mutation)

    def test_unsafe_archive_entries_rejected(self):
        for kind in ('traversal', 'symlink', 'absolute'):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary);archive = root / 'bad.tar'
                with tarfile.open(archive, 'w') as tar:
                    name = {'traversal': 'root/../../escape', 'symlink': 'root/link', 'absolute': '/escape'}[kind]
                    entry = tarfile.TarInfo(name)
                    if kind == 'symlink': entry.type = tarfile.SYMTYPE;entry.linkname = '/etc/passwd'
                    tar.addfile(entry, io.BytesIO(b''))
                with self.assertRaises(ValueError): extract(archive, root / 'source')
                self.assertFalse((root / 'escape').exists())
