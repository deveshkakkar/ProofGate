"""Local guard regressions for the partial-body experiment."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('partial_body', Path(__file__).with_name('partial-body.py'))
partial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(partial)


class PartialBodyTests(unittest.TestCase):
    def test_cut_must_leave_body_incomplete(self):
        payload = {'requestId': 'x', 'amount': 30}
        with self.assertRaises(ValueError):
            partial.send_partial(1, payload, -1)
        with self.assertRaises(ValueError):
            partial.send_partial(1, payload, 999)

    def test_premature_admission_controls_are_rejected(self):
        partial.assert_negative_control()


if __name__ == '__main__':
    unittest.main()
