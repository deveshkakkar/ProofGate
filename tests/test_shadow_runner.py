import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from benchmarks.drf.ci import compare_control
from benchmarks.drf.resource_exec import ensure_unprivileged
from benchmarks.drf.replay import extract, read_regular, scope_command, evaluate


class ShadowRunnerTests(unittest.TestCase):
    def test_archive_rejects_escape_and_links(self):
        for name, kind in (('../escape', tarfile.REGTYPE), ('/escape', tarfile.REGTYPE),
                           ('link', tarfile.SYMTYPE), ('hardlink', tarfile.LNKTYPE)):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); archive = root / 'archive.tar'
                with tarfile.open(archive, 'w') as output:
                    member = tarfile.TarInfo(name); member.type = kind
                    member.linkname = '/etc/passwd'
                    output.addfile(member)
                with self.assertRaises(ValueError):
                    extract(archive, root / 'snapshot')
                self.assertFalse((root / 'escape').exists())

    def test_regular_file_size_and_symlink_checks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / 'source'
            source.write_bytes(b'abc')
            self.assertEqual(read_regular(source, 3), b'abc')
            with self.assertRaises(ValueError):
                read_regular(source, 2)
            (root / 'link').symlink_to(source)
            with self.assertRaises(OSError):
                read_regular(root / 'link', 4)

    def test_github_transport_drops_privileges_before_helper(self):
        with patch('os.getuid', return_value=1001), patch('os.getgid', return_value=1001), patch.dict(
                os.environ, {'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'github-hosted'}):
            argv = scope_command(['/usr/bin/bwrap'], 'github-hosted')
        self.assertIn('--reuid=1001', argv)
        self.assertIn('--regid=1001', argv)
        self.assertLess(argv.index('/usr/bin/setpriv'), argv.index('/usr/bin/python3'))
        self.assertIn('--no-new-privs', argv)

    def test_root_and_non_github_transport_are_rejected(self):
        with patch('os.getuid', return_value=0):
            with self.assertRaises(ValueError):
                scope_command([], 'user')
        with patch('os.getuid', return_value=1001), patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                scope_command([], 'github-hosted')

    def test_saved_root_and_effective_capabilities_are_rejected(self):
        zero = 'CapEff: 0000\nCapPrm: 0000\nCapAmb: 0000\n'
        with patch('os.getresuid', return_value=(1001, 1001, 0)), patch('os.getresgid', return_value=(1001, 1001, 1001)):
            with self.assertRaises(PermissionError):
                ensure_unprivileged()
        with patch('os.getresuid', return_value=(1001, 1001, 1001)), patch('os.getresgid', return_value=(1001, 1001, 1001)):
            with patch('pathlib.Path.read_text', return_value=zero):
                ensure_unprivileged()
            with patch('pathlib.Path.read_text', return_value=zero.replace('CapEff: 0000', 'CapEff: 0001')):
                with self.assertRaises(PermissionError):
                    ensure_unprivileged()

    def test_untrusted_descriptor_is_rejected_before_creating_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(ValueError):
                evaluate({'id': 'or_composition', 'module': '../escape', 'base_sha': 'a' * 40},
                         root, root, root, root, root / 'output')
            self.assertFalse((root / 'output').exists())

    def test_wrong_failure_pattern_is_not_a_historical_match(self):
        root = Path(__file__).resolve().parents[1]
        case = next(row for row in json.loads((root / 'benchmarks/drf/results.json').read_text())['cases']
                    if row['id'] == 'model_permissions')
        wrong = {'checks': {'heldout': {'status': 'failed'}, 'contract': {'status': 'passed'},
                            'compatibility': {'status': 'passed'}}, 'receipt': {'consistent': False}}
        self.assertFalse(compare_control(case, 'upstream', wrong)['control_matched'])
        correct = {'checks': {'heldout': {'status': 'passed'}, 'contract': {'status': 'passed'},
                              'compatibility': {'status': 'failed'}}, 'receipt': {'consistent': False}}
        self.assertTrue(compare_control(case, 'upstream', correct)['control_matched'])

    def test_heldout_identity_is_checked_before_creating_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); module = root / 'module.py'; module.write_bytes(b'pass')
            heldout = root / 'test.py'; heldout.write_bytes(b'changed')
            descriptor = {'id': 'or_composition', 'module': 'rest_framework/permissions.py',
                          'base_sha': 'a' * 40, 'test_file': 'test_permissions.py',
                          'test_class': 'PermissionsCompositionTests', 'heldout_test_sha256': 'b' * 64}
            with self.assertRaises(ValueError):
                evaluate(descriptor, root, module, heldout, root, root / 'output')
            self.assertFalse((root / 'output').exists())
