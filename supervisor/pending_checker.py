"""Finite checker for one lost-response reservation across a process restart.

The pending reservation may have committed before the process stopped or may
have had no effect. Every completed operation belongs to the restarted process.
This models a process crash, not durability across machine or storage failure.
"""

from supervisor import realtime_checker as realtime


def _validate(history, force_effect):
    if force_effect is not None and type(force_effect) is not bool:
        raise ValueError("force_effect must be a boolean or None")
    if type(history) is not list or not 1 <= len(history) <= realtime.MAX_OPERATIONS:
        raise ValueError(f"history must contain 1 through {realtime.MAX_OPERATIONS} operations")
    pending = [op for op in history if type(op) is dict and op.get("kind") == "pending_reserve"]
    if len(pending) != 1:
        raise ValueError("history must contain exactly one pending_reserve")
    pending = pending[0]
    if set(pending) != {"id", "kind", "request_id", "amount", "start_ns", "stop_ns"}:
        raise ValueError("pending_reserve has missing or extra fields")
    if type(pending["id"]) is not str or not pending["id"]:
        raise ValueError("pending_reserve has invalid id")
    if type(pending["request_id"]) is not str or not realtime.REQUEST_ID.fullmatch(pending["request_id"]):
        raise ValueError("pending_reserve has invalid request_id")
    if type(pending["amount"]) is not int or abs(pending["amount"]) > realtime.MAX_AMOUNT:
        raise ValueError("pending_reserve has invalid amount")
    if any(type(pending[key]) is not int or pending[key] < 0 for key in ("start_ns", "stop_ns")):
        raise ValueError("pending_reserve has invalid timestamps")
    if pending["start_ns"] > pending["stop_ns"]:
        raise ValueError("pending_reserve stops before invocation")

    completed = [op for op in history if op is not pending]
    realtime._validate(completed, 100)
    if any(op["id"] == pending["id"] for op in completed):
        raise ValueError("pending_reserve id duplicates a completed operation")
    if any(op["start_ns"] < pending["stop_ns"] for op in completed):
        raise ValueError("completed operations must start after the process stops")
    return pending, completed


def _applied_state(pending):
    amount = pending["amount"]
    success = 0 < amount <= 100
    balance = 100 - amount if success else 100
    body = {"requestId": pending["request_id"], "amount": amount,
            "success": success, "granted": amount if success else 0,
            "balance": balance,
            "reason": "granted" if success else "invalid_amount" if amount <= 0
            else "insufficient_credits"}
    return balance, {pending["request_id"]: (amount, realtime._body_json(body))}


def _order(completed, balance, records):
    count = len(completed)
    predecessors = [sum(1 << other for other, earlier in enumerate(completed)
                        if other != index and earlier["end_ns"] < op["start_ns"])
                    for index, op in enumerate(completed)]
    failed = set()

    def search(mask, current_balance, current_records):
        if mask == (1 << count) - 1:
            return []
        state = (mask, current_balance, tuple(sorted(
            (key, amount, body) for key, (amount, body) in current_records.items())))
        if state in failed:
            return None
        for index, op in enumerate(completed):
            bit = 1 << index
            if mask & bit or predecessors[index] & ~mask:
                continue
            next_state = realtime._step(op, current_balance, current_records)
            if next_state is None:
                continue
            suffix = search(mask | bit, *next_state)
            if suffix is not None:
                return [op["id"], *suffix]
        failed.add(state)
        return None

    return search(0, balance, records)


def check_pending(history: list[dict], force_effect: bool | None = None) -> dict:
    """Return feasibility, a witness order, and the inferred pending effect.

    ``pending_applied`` is None when both effects are feasible (or neither is).
    With no forced effect, an ambiguous witness prefers omission. A forced
    effect restricts the search and reports that effect when feasible.
    """
    pending, completed = _validate(history, force_effect)
    omitted = _order(completed, 100, {}) if force_effect is not True else None
    applied = (_order(completed, *_applied_state(pending))
               if force_effect is not False else None)
    if omitted is not None and applied is not None:
        return {"linearizable": True, "order": omitted, "pending_applied": None}
    if omitted is not None:
        return {"linearizable": True, "order": omitted, "pending_applied": False}
    if applied is not None:
        return {"linearizable": True, "order": [pending["id"], *applied],
                "pending_applied": True}
    return {"linearizable": False, "order": None, "pending_applied": None}
