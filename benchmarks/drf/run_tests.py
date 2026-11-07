"""Trusted test transport; run only inside the network-disabled source namespace."""
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import pytest

result = pytest.main(sys.argv[1:] + ['--junitxml=/tmp/proofgate-junit.xml'])
path = Path('/tmp/proofgate-junit.xml')
if path.exists():
    record = {'exit_code': int(result), 'tests': 0, 'failures': 0, 'errors': 0, 'skipped': 0}
    for suite in ET.parse(path).getroot().iter('testsuite'):
        for key in ('tests', 'failures', 'errors', 'skipped'):
            record[key] += int(suite.get(key, '0'))
    print('PROOFGATE_RESULT=' + json.dumps(record, sort_keys=True))
raise SystemExit(result)
