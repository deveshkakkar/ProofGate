import copy
import json
from pathlib import Path
import unittest

from benchmarks.erpnext.app_evidence import inspect
from framework.kernel import digest


class ArchivedAppEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / 'benchmarks/erpnext/app-results.json'
        cls.recorded = json.loads(path.read_text())
        cls.good = next(row for row in cls.recorded['attempts'] if row['run_id'] == 42443539018)

    def test_real_application_record_binds_without_release_authority(self):
        result = inspect(self.good['report'], self.good['record_sha256'])
        self.assertTrue(result['consistent'], result)
        self.assertEqual(result['receipt']['checks'],
                         ['original-regressions-reproduced', 'upstream-fixed-tests'])
        for name in ('producer_authenticated', 'fresh_source_execution', 'policy_admitted', 'release_authority'):
            self.assertFalse(result[name])

    def test_retained_setup_failures_are_not_reproduced_controls(self):
        for row in self.recorded['attempts']:
            if row['run_id'] != 42443539018:
                self.assertFalse(inspect(row['report'], digest(row['report']))['consistent'])

    def test_record_pin_prevents_coherent_source_rewrite(self):
        report = copy.deepcopy(self.good['report'])
        report['sources']['head-report.py']['sha256'] = 'a' * 64
        for name in ('source_before', 'source_after'):
            report['observations']['head'][name]['module_sha256'] = 'a' * 64
        self.assertFalse(inspect(report, self.good['record_sha256'])['consistent'])

    def test_invalid_controls_metadata_and_verifier_reject_even_with_matching_pin(self):
        for mutation in ('partial', 'source-drift', 'verifier', 'revision', 'network', 'environment', 'false-success'):
            report = copy.deepcopy(self.good['report'])
            if mutation == 'partial': report['observations']['head']['runs'][0]['test_ids'].pop()
            if mutation == 'source-drift': report['observations']['head']['source_after']['module_sha256'] = '0' * 64
            if mutation == 'verifier': report['verifier']['app_collect.py'] = '0' * 64
            if mutation == 'revision': report['sources']['frappe']['revision'] = '0' * 40
            if mutation == 'network': report['isolation']['network_attachments'] = {'bridge': {}}
            if mutation == 'environment': report['environment']['packages'] = []
            if mutation == 'false-success': report['observations']['base']['runs'][0]['failure_ids'] = []
            self.assertFalse(inspect(report, digest(report))['consistent'], mutation)

    def test_wrong_json_shapes_fail_closed(self):
        for report in ([], None, True, {'schema': True}, {'schema': 1}):
            self.assertFalse(inspect(report, digest(report))['consistent'])

    def test_nested_malformed_environment_inventory_fails_closed(self):
        for mutation in ('packages-null', 'package-version', 'binary-list', 'binary-entry',
                         'missing-tree', 'boolean-count', 'invalid-tree-digest'):
            report = copy.deepcopy(self.good['report'])
            environment = report['environment']
            if mutation == 'packages-null': environment['packages'] = [None]
            if mutation == 'package-version': environment['packages'][0]['version'] = 0
            if mutation == 'binary-list': environment['binaries'] = list(environment['binaries'])
            if mutation == 'binary-entry': environment['binaries']['bench'] = None
            if mutation == 'missing-tree': environment.pop('site_packages')
            if mutation == 'boolean-count': environment['site_packages']['files'] = True
            if mutation == 'invalid-tree-digest': environment['site_packages']['sha256'] = 'invalid'
            self.assertFalse(inspect(report, digest(report))['consistent'], mutation)
