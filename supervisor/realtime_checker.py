"""Finite linearizability checker for completed ProofGate HTTP histories.

This is an independent sequential specification, not an import of the server.
All operations must have complete HTTP responses. A failed transport or crash
requires a separate history model and is deliberately outside this checker.
"""

import json
import re


MAX_OPERATIONS = 12
MAX_AMOUNT = 281474976710655
REQUEST_ID = re.compile(r"[A-Za-z0-9._:-]{1,128}\Z")


def _integer(value):
    return type(value) is int


def _body_json(body):
    return json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _validate(history, initial_balance):
    if not _integer(initial_balance) or not 0 <= initial_balance <= 100:
        raise ValueError("initial_balance must be an integer from 0 through 100")
    if type(history) is not list or len(history) > MAX_OPERATIONS:
        raise ValueError(f"history must be a list of at most {MAX_OPERATIONS} operations")
    seen = set()
    for index, op in enumerate(history):
        if type(op) is not dict:
            raise ValueError(f"operation {index} must be an object")
        kind = op.get("kind")
        fields = {"id", "kind", "start_ns", "end_ns", "status", "body"}
        if kind == "reserve":
            fields |= {"request_id", "amount"}
        elif kind != "status":
            raise ValueError(f"operation {index} has invalid kind")
        if set(op) != fields:
            raise ValueError(f"operation {index} has missing or extra fields")
        if type(op["id"]) is not str or not op["id"] or op["id"] in seen:
            raise ValueError(f"operation {index} has invalid or duplicate id")
        seen.add(op["id"])
        if not all(_integer(op[key]) and op[key] >= 0 for key in ("start_ns", "end_ns")):
            raise ValueError(f"operation {index} has invalid timestamps")
        if op["start_ns"] > op["end_ns"]:
            raise ValueError(f"operation {index} ends before invocation")
        if not _integer(op["status"]) or type(op["body"]) is not dict:
            raise ValueError(f"operation {index} has invalid HTTP response")
        body = op["body"]
        if kind == "status":
            if op["status"] != 200 or set(body) != {"balance"} or not _integer(body["balance"]):
                raise ValueError(f"operation {index} has invalid status response")
        else:
            if type(op["request_id"]) is not str or not REQUEST_ID.fullmatch(op["request_id"]):
                raise ValueError(f"operation {index} has invalid request_id")
            if not _integer(op["amount"]) or abs(op["amount"]) > MAX_AMOUNT:
                raise ValueError(f"operation {index} has invalid amount")
            if op["status"] == 409:
                if body != {"error": "conflict"}:
                    raise ValueError(f"operation {index} has invalid conflict response")
            elif op["status"] == 200:
                if set(body) != {"requestId", "amount", "success", "granted", "balance", "reason"}:
                    raise ValueError(f"operation {index} has invalid reservation response fields")
                if (type(body["requestId"]) is not str or not _integer(body["amount"])
                    or type(body["success"]) is not bool or not _integer(body["granted"])
                    or not _integer(body["balance"]) or type(body["reason"]) is not str):
                    raise ValueError(f"operation {index} has invalid reservation response types")
            else:
                raise ValueError(f"operation {index} has unsupported HTTP status")


def _step(op, balance, records):
    if op["kind"] == "status":
        if op["body"] == {"balance": balance}:
            return balance, records
        return None

    request_id, amount = op["request_id"], op["amount"]
    prior = records.get(request_id)
    if prior is not None:
        old_amount, old_body = prior
        if amount != old_amount:
            return (balance, records) if op["status"] == 409 and op["body"] == {"error": "conflict"} else None
        return (balance, records) if op["status"] == 200 and _body_json(op["body"]) == old_body else None

    success = 0 < amount <= balance
    next_balance = balance - amount if success else balance
    expected = {
        "requestId": request_id,
        "amount": amount,
        "success": success,
        "granted": amount if success else 0,
        "balance": next_balance,
        "reason": "granted" if success else "invalid_amount" if amount <= 0 else "insufficient_credits",
    }
    if op["status"] != 200 or _body_json(op["body"]) != _body_json(expected):
        return None
    updated = dict(records)
    updated[request_id] = (amount, _body_json(expected))
    return next_balance, updated


def check(history: list[dict], initial_balance: int = 100) -> dict:
    """Return a valid sequential order, or report that none exists.

    A response completed strictly before another invocation must precede it.
    Equal clock readings are treated as unresolved ordering.
    Overlapping intervals may be ordered either way. Histories are bounded so
    exhaustive DFS with failed-state memoization remains finite.
    """
    _validate(history, initial_balance)
    count = len(history)
    predecessors = []
    for index, op in enumerate(history):
        predecessors.append(sum(1 << other for other, earlier in enumerate(history)
                                if other != index and earlier["end_ns"] < op["start_ns"]))
    failed = set()

    def search(mask, balance, records):
        if mask == (1 << count) - 1:
            return []
        state = (mask, balance, tuple(sorted((key, amount, body)
                                            for key, (amount, body) in records.items())))
        if state in failed:
            return None
        for index, op in enumerate(history):
            bit = 1 << index
            if mask & bit or predecessors[index] & ~mask:
                continue
            next_state = _step(op, balance, records)
            if next_state is None:
                continue
            suffix = search(mask | bit, *next_state)
            if suffix is not None:
                return [op["id"], *suffix]
        failed.add(state)
        return None

    order = search(0, initial_balance, {})
    return {"linearizable": order is not None, "order": order}
