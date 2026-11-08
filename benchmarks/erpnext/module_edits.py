"""Proposed source-bound exact-text edit protocol; static validation only.

Not used for the frozen raw-diff author replay. No file writes, code execution,
provider calls, fuzzy matching, or authority are supplied by this module.
"""
import hashlib

from framework.kernel import sha as valid_sha

MAX_BYTES = 256 * 1024
MAX_EDITS = 8


def apply_edits(source, expected_source_sha256, proposal):
    """Validate all edits against the original source, then return edited text."""
    valid_sha(expected_source_sha256)
    if type(source) is not str or not 0 < len(source.encode()) <= MAX_BYTES:
        raise ValueError('invalid source size/type')
    if hashlib.sha256(source.encode()).hexdigest() != expected_source_sha256:
        raise ValueError('source identity mismatch')
    if (type(proposal) is not dict or set(proposal) != {'schema', 'source_sha256', 'edits'} or
            type(proposal['schema']) is not int or proposal['schema'] != 1 or
            proposal['source_sha256'] != expected_source_sha256 or
            type(proposal['edits']) is not list or not 0 < len(proposal['edits']) <= MAX_EDITS):
        raise ValueError('invalid source-bound edit envelope')
    ranges = []
    for edit in proposal['edits']:
        if (type(edit) is not dict or set(edit) != {'old', 'new'} or
                type(edit['old']) is not str or type(edit['new']) is not str or
                not edit['old'] or edit['old'] == edit['new'] or
                len(edit['old'].encode()) > MAX_BYTES or len(edit['new'].encode()) > MAX_BYTES):
            raise ValueError('invalid edit')
        start = source.find(edit['old'])
        if start < 0 or source.find(edit['old'], start + 1) >= 0:
            raise ValueError('old text must match exactly once in original source')
        ranges.append((start, start + len(edit['old']), edit['new']))
    ranges.sort()
    if any(left[1] > right[0] for left, right in zip(ranges, ranges[1:])):
        raise ValueError('overlapping edits')
    cursor = 0;parts = []
    for start, end, replacement in ranges:
        parts.extend([source[cursor:start], replacement]);cursor = end
    parts.append(source[cursor:]);result = ''.join(parts)
    if not 0 < len(result.encode()) <= MAX_BYTES: raise ValueError('invalid result size')
    return result
