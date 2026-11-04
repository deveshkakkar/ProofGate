"""Adversarial finite histories for the independent ProofGate checker."""

import unittest

from supervisor.realtime_checker import MAX_OPERATIONS, check


def response(request_id, amount, success, granted, balance, reason):
    return {"requestId": request_id, "amount": amount, "success": success,
            "granted": granted, "balance": balance, "reason": reason}


def reserve(op_id, request_id, amount, start, end, body, status=200):
    return {"id": op_id, "kind": "reserve", "request_id": request_id,
            "amount": amount, "start_ns": start, "end_ns": end,
            "status": status, "body": body}


def status(op_id, start, end, balance):
    return {"id": op_id, "kind": "status", "start_ns": start,
            "end_ns": end, "status": 200, "body": {"balance": balance}}


class CheckerTests(unittest.TestCase):
    def test_overlapping_reservations_and_status_have_a_valid_order(self):
        # Both reservations overlap the read. The read of 70 forces A first;
        # B may follow even though its invocation was earlier than A's reply.
        history = [
            reserve("A", "a", 30, 10, 70, response("a", 30, True, 30, 70, "granted")),
            reserve("B", "b", 40, 20, 80, response("b", 40, True, 40, 30, "granted")),
            status("S", 30, 60, 70),
            status("final", 90, 100, 30),
        ]
        result = check(history)
        self.assertTrue(result["linearizable"])
        self.assertEqual(result["order"], ["A", "S", "B", "final"])

    def test_completed_grant_cannot_be_followed_by_stale_status(self):
        history = [
            reserve("A", "a", 30, 1, 2, response("a", 30, True, 30, 70, "granted")),
            status("stale", 3, 4, 100),
        ]
        self.assertEqual(check(history), {"linearizable": False, "order": None})
        # The same apparent stale read is legal when intervals overlap: the
        # checker must not mistake invocation order for completion order.
        history[1]["start_ns"] = 1
        self.assertTrue(check(history)["linearizable"])

    def test_completed_grant_cannot_be_followed_by_stale_admission(self):
        history = [
            reserve("A", "a", 30, 1, 2, response("a", 30, True, 30, 70, "granted")),
            reserve("stale", "b", 80, 3, 4,
                    response("b", 80, True, 80, 20, "granted")),
        ]
        self.assertFalse(check(history)["linearizable"])
        # Even overlapping intervals cannot explain two grants totalling 110.
        history[1]["start_ns"] = 1
        history[1]["end_ns"] = 2
        self.assertFalse(check(history)["linearizable"])

    def test_replay_is_historical_and_conflict_does_not_change_balance(self):
        history = [
            reserve("first", "a", 30, 1, 2, response("a", 30, True, 30, 70, "granted")),
            reserve("second", "b", 20, 3, 4, response("b", 20, True, 20, 50, "granted")),
            reserve("replay", "a", 30, 5, 6, response("a", 30, True, 30, 70, "granted")),
            reserve("conflict", "a", 31, 7, 8, {"error": "conflict"}, 409),
            status("current", 9, 10, 50),
        ]
        self.assertTrue(check(history)["linearizable"])
        history[2]["body"] = response("a", 30, True, 30, 50, "granted")
        self.assertFalse(check(history)["linearizable"])

    def test_rejected_decision_is_persisted_for_replay_and_conflict(self):
        rejected = response("too-big", 101, False, 0, 100, "insufficient_credits")
        history = [
            reserve("reject", "too-big", 101, 1, 2, rejected),
            reserve("grant", "a", 30, 3, 4, response("a", 30, True, 30, 70, "granted")),
            reserve("replay", "too-big", 101, 5, 6, rejected.copy()),
            reserve("conflict", "too-big", 1, 7, 8, {"error": "conflict"}, 409),
            status("status", 9, 10, 70),
        ]
        self.assertTrue(check(history)["linearizable"])
        history[2]["body"] = response("too-big", 101, False, 0, 70, "insufficient_credits")
        self.assertFalse(check(history)["linearizable"])

    def test_wrong_reason_grant_or_conflict_is_rejected(self):
        bad = reserve("zero", "z", 0, 1, 2,
                      response("z", 0, False, 0, 100, "insufficient_credits"))
        self.assertFalse(check([bad])["linearizable"])
        bad["body"]["reason"] = "invalid_amount"
        self.assertTrue(check([bad])["linearizable"])
        bad["body"]["granted"] = 1
        self.assertFalse(check([bad])["linearizable"])
        self.assertFalse(check([reserve("orphan", "x", 1, 1, 2,
                                        {"error": "conflict"}, 409)])["linearizable"])

    def test_malformed_and_unbounded_histories_raise(self):
        good = status("s", 1, 2, 100)
        for history in ([good, good.copy()], [{**good, "start_ns": 3}],
                        [{**good, "body": {"balance": True}}],
                        [{**good, "status": 500}],
                        [status(str(i), i * 2, i * 2 + 1, 100)
                         for i in range(MAX_OPERATIONS + 1)]):
            with self.subTest(history=history), self.assertRaises(ValueError):
                check(history)
        with self.assertRaises(ValueError):
            check([], initial_balance=True)


if __name__ == "__main__":
    unittest.main()
