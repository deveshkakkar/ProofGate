"""Published historical reports must match the independently retained summary pins."""
import hashlib
import json
from pathlib import Path
import unittest

from framework.kernel import contract_digest, verify

ROOT = Path(__file__).resolve().parents[1]/'docs/framework'


class PublicAuditReportTests(unittest.TestCase):
    def test_exact_raw_bytes_and_finite_observations_match_original_summary(self):
        summary=json.loads((ROOT/'AUDIT-EXECUTION-RESULTS.json').read_text())
        for run in summary['runs']:
            for expected in run['reports']:
                with self.subTest(run=run['name'],variant=expected['variant']):
                    raw=(ROOT/'audit-reports'/(run['name']+'-'+expected['variant']+'.json')).read_bytes()
                    self.assertEqual(hashlib.sha256(raw).hexdigest(),expected['raw_report_sha256'])
                    report=json.loads(raw)
                    self.assertEqual(verify(report['contract'],contract_digest(report['contract']),
                                            report['inputs'],report['observations']),report['receipt'])
                    for row,want in zip(report['checks'],expected['checks']):
                        self.assertEqual(len(row['observed']),want['cases'])
                        mismatch=sum(json.dumps(a,sort_keys=True)!=json.dumps(b,sort_keys=True)
                                     for a,b in zip(row['expected'],row['observed']))
                        self.assertEqual(mismatch,want['mismatches'])
