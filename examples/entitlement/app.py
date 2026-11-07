"""One JSON batch per invocation. No sessions or persistent state."""
import json
import sys
from rule import allow

FIELDS = {'subject_tenant', 'resource_tenant', 'active', 'entitled', 'enabled'}


def handle(row):
    if not isinstance(row, dict) or set(row) != FIELDS:
        return {'error': 'invalid request'}
    for key in ('subject_tenant', 'resource_tenant'):
        if type(row[key]) is not int or row[key] not in range(3):
            return {'error': 'invalid request'}
    if any(type(row[key]) is not bool for key in ('active', 'entitled', 'enabled')):
        return {'error': 'invalid request'}
    return {'allowed': allow(**row)}


if __name__ == '__main__':
    print(json.dumps([handle(row) for row in json.load(sys.stdin)]))
