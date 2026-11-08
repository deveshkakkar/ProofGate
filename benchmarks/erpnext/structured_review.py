"""One-command review of the trusted checkout's recorded paired replay.

Reads reviewed repository evidence only; never executes candidates or contacts a
provider. A candidate-authored checkout is not an independent trust source.
"""
import argparse
import json

from framework.preservation import read_json
from framework.kernel import digest
from .structured import HERE, score


def summary(result):
    lines = ['Archived paired replay: ' + result['outcome']]
    if not result['valid_controls']:
        lines.append('Controls unverified: ' + json.dumps(result.get('reason', 'incomplete evidence'), ensure_ascii=True))
        if result.get('recorded_error'):
            lines.append('Recorded failure at ' + json.dumps(result.get('recorded_stage'), ensure_ascii=True) +
                         ': ' + json.dumps(result['recorded_error'], ensure_ascii=True))
        if result.get('log_diagnostic'):
            lines.append('Log-only diagnosis: ' + json.dumps(result['log_diagnostic'], ensure_ascii=True))
    else:
        lines.append('Controls: unchanged read-denial failure reproduced; upstream report passed 5/5.')
        for arm, label in (('baseline', 'Baseline author'), ('feedback', 'Feedback author')):
            row = result['arms'][arm]
            if row['status'] == 'inconclusive':
                lines.append(label + ': inconclusive; no passing result inferred.')
            else:
                passed = row['tests'] - len(row['failure_ids'])
                earlier = 'preserved' if row['earlier_four_preserved'] else 'failed'
                read = 'satisfied' if row['read_denial_satisfied'] else 'failed'
                lines.append(f'{label}: {passed}/{row["tests"]} passed; earlier four {earlier}; read denial {read}.')
        if result['outcome'] == 'passing-tie':
            lines.append('No observed repair advantage from failure feedback in this pair.')
    if result.get('record_sha256'):
        lines.append('Record SHA256: ' + result['record_sha256'])
    lines.extend(['One retrospectively selected pair; broader effectiveness and demand remain unvalidated.',
                  'Archived observations only: no fresh execution, producer authentication, policy admission or release authority.'])
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', choices=('structured', 'lifecycle'), default='structured',
                        help='Choose a retained attempt; default preserves the original structured replay')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--obligations', action='store_true', help='Show source-bound declared fixture coverage')
    parser.add_argument('--expected-obligations-sha256', help='Independently obtained coverage metadata pin; requires --obligations')
    parser.add_argument('--expected-record-sha256', help='Override the reviewed checkout record pin with an independently obtained pin')
    args = parser.parse_args()
    if args.expected_obligations_sha256 and not args.obligations:
        parser.error('--expected-obligations-sha256 requires --obligations')
    try:
        wrapper = read_json(HERE / (args.attempt + '-results.json'))
        pin = args.expected_record_sha256 or wrapper['record_sha256']
        producer = read_json(HERE / (args.attempt + '-producer.json'))
        manifest = read_json(HERE / 'structured-candidates.json')
        result = score(wrapper['report'], pin, producer, manifest)
        if digest(wrapper['report']) == pin and type(wrapper['report']) is dict:
            result['record_sha256'] = pin
            for key in ('stage', 'error'):
                value = wrapper['report'].get(key)
                if type(value) is str:
                    result['recorded_' + key] = value
            note = wrapper.get('log_diagnostic')
            if type(note) is dict and note.get('kind') == 'sanitized-log-only' and type(note.get('summary')) is str:
                result['log_diagnostic'] = note['summary']
        if args.obligations:
            from .obligations import EXPECTED_COVERAGE_SHA256, review, unavailable
            try:
                coverage = read_json(HERE / 'obligations.json')
            except (ValueError, TypeError, OSError, RecursionError) as exc:
                result['obligations'] = unavailable('Cannot read coverage metadata: ' + type(exc).__name__,
                                                  result['outcome'])
            else:
                result['obligations'] = review(wrapper['report'], pin, producer, manifest, coverage,
                                              args.expected_obligations_sha256 or EXPECTED_COVERAGE_SHA256)
    except (ValueError, TypeError, KeyError, OSError, RecursionError) as exc:
        parser.exit(2, 'Cannot read recorded replay: ' + type(exc).__name__ + '\n')
    output = json.dumps(result, indent=2) if args.json else summary(result)
    if args.obligations and not args.json:
        from .obligations import summary as coverage_summary
        output += '\n\n' + coverage_summary(result['obligations'])
    print(output)
    available = not args.obligations or result['obligations']['available']
    return 0 if result['valid_controls'] and available else 1


if __name__ == '__main__':
    raise SystemExit(main())
