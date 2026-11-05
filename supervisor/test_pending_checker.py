"""Adversarial histories for a reservation whose HTTP response was lost."""

import unittest

from supervisor.pending_checker import check_pending
from supervisor.realtime_checker import MAX_OPERATIONS, MAX_AMOUNT


def pending(amount=30):
    return {"id": "lost", "kind": "pending_reserve", "request_id": "a",
            "amount": amount, "start_ns": 1, "stop_ns": 10}


def status(op_id, start, balance):
    return {"id": op_id, "kind": "status", "start_ns": start,
            "end_ns": start + 1, "status": 200, "body": {"balance": balance}}


def reserve(op_id, request_id, amount, start, balance, success=True):
    return {"id": op_id, "kind": "reserve", "request_id": request_id,
            "amount": amount, "start_ns": start, "end_ns": start + 1,
            "status": 200, "body": {"requestId": request_id, "amount": amount,
            "success": success, "granted": amount if success else 0,
            "balance": balance, "reason": "granted" if success else "insufficient_credits"}}


class PendingCheckerTests(unittest.TestCase):
    def test_after_commit_status_requires_applied_effect(self):
        history = [pending(), status("observed", 11, 70)]
        self.assertEqual(check_pending(history),
                         {"linearizable": True, "order": ["lost", "observed"],
                          "pending_applied": True})
        self.assertFalse(check_pending(history, force_effect=False)["linearizable"])

    def test_before_commit_status_requires_omission(self):
        history = [pending(), status("observed", 11, 100)]
        self.assertEqual(check_pending(history),
                         {"linearizable": True, "order": ["observed"],
                          "pending_applied": False})
        self.assertFalse(check_pending(history, force_effect=True)["linearizable"])

    def test_replay_alone_does_not_classify_original(self):
        history = [pending(), reserve("replay", "a", 30, 11, 70)]
        result = check_pending(history)
        self.assertTrue(result["linearizable"])
        self.assertIsNone(result["pending_applied"])
        for effect in (False, True):
            self.assertTrue(check_pending(history, force_effect=effect)["linearizable"])

    def test_no_duplicate_charge_after_applied_effect(self):
        history = [pending(), reserve("replay", "a", 30, 11, 70),
                   status("later", 13, 70)]
        self.assertTrue(check_pending(history, force_effect=True)["linearizable"])
        history[-1] = status("double_charge", 13, 40)
        self.assertFalse(check_pending(history)["linearizable"])

    def test_status_before_replay_resolves_original_effect(self):
        applied = [pending(), status("before_replay", 11, 70),
                   reserve("replay", "a", 30, 13, 70), status("final", 15, 70)]
        self.assertTrue(check_pending(applied, force_effect=True)["linearizable"])
        self.assertFalse(check_pending(applied, force_effect=False)["linearizable"])
        omitted = [pending(), status("before_replay", 11, 100),
                   reserve("replay", "a", 30, 13, 70), status("final", 15, 70)]
        self.assertTrue(check_pending(omitted, force_effect=False)["linearizable"])
        self.assertFalse(check_pending(omitted, force_effect=True)["linearizable"])

    def test_conflicting_replay_requires_record_or_another_first_write(self):
        conflict = {"id": "conflict", "kind": "reserve", "request_id": "a",
                    "amount": 31, "start_ns": 11, "end_ns": 12,
                    "status": 409, "body": {"error": "conflict"}}
        self.assertTrue(check_pending([pending(), conflict], force_effect=True)["linearizable"])
        self.assertFalse(check_pending([pending(), conflict], force_effect=False)["linearizable"])

    def test_rejected_decision_is_persisted(self):
        lost = pending(101)
        replay = reserve("replay", "a", 101, 14, 100, success=False)
        history = [lost, status("before", 11, 100), replay]
        self.assertIsNone(check_pending(history)["pending_applied"])
        history.insert(2, reserve("other", "b", 30, 12, 70))
        self.assertTrue(check_pending(history, force_effect=True)["linearizable"])
        self.assertFalse(check_pending(history, force_effect=False)["linearizable"])

    def test_bounded_schema_and_process_order_are_enforced(self):
        good = pending()
        bad_histories = [[], [good, good.copy()],
                         [{**good, "amount": MAX_AMOUNT + 1}],
                         [{**good, "request_id": "bad id"}],
                         [{**good, "start_ns": 11}],
                         [{**good, "stop_ns": True}],
                         [{**good, "status": None}],
                         [good, status("lost", 11, 100)],
                         [good, status("early", 9, 100)],
                         [good, {**status("bad", 11, 100), "body": {"balance": True}}],
                         [good, *[status(str(i), 11 + 2 * i, 100)
                                  for i in range(MAX_OPERATIONS)]]]
        for history in bad_histories:
            with self.subTest(history=history), self.assertRaises(ValueError):
                check_pending(history)
        for invalid in (0, 1, "true"):
            with self.subTest(force_effect=invalid), self.assertRaises(ValueError):
                check_pending([good], force_effect=invalid)


if __name__ == "__main__":
    unittest.main()
