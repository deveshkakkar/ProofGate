"""Inspected-code unittest transport, executed only inside the test container."""
import json
import sys
from pathlib import Path

# Frappe's real test runner initializes fixtures and hooks. Retain its result,
# rather than reimplementing fixture setup or interpreting human log summaries.
from frappe.testing.runner import TestRunner

original_run = TestRunner.run
reports = []


def flatten(suite):
    for item in suite:
        if hasattr(item, '__iter__'):
            yield from flatten(item)
        else:
            yield item.id()


def run(self, suite):
    inventory = list(flatten(suite))
    result = original_run(self, suite)
    reports.append({'test_ids': inventory, 'tests': result.testsRun,
                    'failure_ids': [test.id() for test, _ in result.failures],
                    'error_ids': [test.id() for test, _ in result.errors],
                    'skipped_ids': [test.id() for test, _ in result.skipped],
                    'expected_failure_ids': [test.id() for test, _ in result.expectedFailures],
                    'unexpected_success_ids': [test.id() for test in result.unexpectedSuccesses]})
    return result


TestRunner.run = run
if __name__ == '__main__':
    import frappe.utils.bench_helper
    output = Path(sys.argv[1])
    site, module = sys.argv[2:]
    sys.argv = ['bench', 'frappe', '--site', site, 'run-tests', '--app', 'erpnext', '--module', module]
    try:
        frappe.utils.bench_helper.main()
    finally:
        output.write_text(json.dumps({'schema': 1, 'runs': reports}, indent=2) + '\n')
