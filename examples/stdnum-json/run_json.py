"""Inspected JSON shim for upstream's published Luhn examples, not a new oracle."""
import json
import sys
from stdnum import luhn


def handle(row):
    operation = row['operation']
    if operation == 'is_valid':
        return luhn.is_valid(row['number'])
    if operation == 'checksum':
        return luhn.checksum(row['number'], row.get('alphabet', '0123456789'))
    if operation == 'check_digit':
        return luhn.calc_check_digit(row['number'])
    raise ValueError('Unsupported shim operation')


if __name__ == '__main__':
    print(json.dumps([handle(row) for row in json.load(sys.stdin)]))
