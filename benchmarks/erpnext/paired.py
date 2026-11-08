"""Strict raw-diff validation for the frozen author protocol; no source execution.

This never repairs malformed author output. Structured edits use a separate,
unexecuted protocol in module_edits.py and cannot reclassify these sessions.
"""
import ast
import re


def parse_diff(patch):
    if type(patch) is not str or not 0 < len(patch.encode()) <= 65536:
        raise ValueError('unsupported patch size/type')
    lines = patch.splitlines(keepends=True)
    if lines and lines[0].strip() in ('```diff', '```patch'):
        if lines[-1].strip() != '```': raise ValueError('unterminated diff envelope')
        lines = lines[1:-1]
    if lines and lines[0].rstrip('\n') == 'diff --git a/report.py b/report.py': lines.pop(0)
    if lines and re.fullmatch(r'index [0-9a-f]+\.\.[0-9a-f]+(?: 100644)?\n', lines[0]): lines.pop(0)
    if len(lines) < 3 or lines.pop(0).rstrip('\n') not in ('--- report.py', '--- a/report.py'):
        raise ValueError('patch must target only report.py')
    if lines.pop(0).rstrip('\n') not in ('+++ report.py', '+++ b/report.py'):
        raise ValueError('patch must target only report.py')
    hunks = []
    while lines:
        header = re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n', lines.pop(0))
        if not header: raise ValueError('invalid unified hunk header')
        start, count, new_start, new_count = [int(x) if x is not None else 1 for x in header.groups()]
        if (count and start == 0) or (new_count and new_start == 0):
            raise ValueError('invalid hunk position')
        body = []
        while lines and not lines[0].startswith('@@ '):
            line = lines.pop(0)
            if not line or line[0] not in (' ', '+', '-'):
                raise ValueError('unsupported hunk line')
            body.append((line[0], line[1:]))
        actual = (sum(kind in (' ', '-') for kind, _ in body),
                  sum(kind in (' ', '+') for kind, _ in body))
        if actual != (count, new_count):
            raise ValueError(f'hunk count mismatch: declared {count}/{new_count}, supplied {actual[0]}/{actual[1]}')
        hunks.append((start, count, new_start, new_count, body))
    if not hunks: raise ValueError('empty patch')
    return hunks


def apply_diff(source, patch):
    """Apply exact locations/context only, without fuzz, recount or execution."""
    if type(source) is not str: raise ValueError('source must be text')
    original = source.splitlines(keepends=True)
    output = [];cursor = 0
    for start, count, new_start, new_count, body in parse_diff(patch):
        index = start - 1 if count else start
        if not cursor <= index <= len(original): raise ValueError('overlapping/out-of-range hunk')
        output.extend(original[cursor:index]);cursor = index
        if (len(output) + (1 if new_count else 0)) != new_start:
            raise ValueError('new hunk offset mismatch')
        for kind, text in body:
            if kind in (' ', '-'):
                if cursor >= len(original) or original[cursor] != text:
                    raise ValueError('hunk context mismatch')
                cursor += 1
            if kind in (' ', '+'): output.append(text)
    output.extend(original[cursor:]);candidate = ''.join(output)
    if candidate == source: raise ValueError('empty patch')
    ast.parse(candidate)  # Syntax only; no upstream code execution.
    return candidate
