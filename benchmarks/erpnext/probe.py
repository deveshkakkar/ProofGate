"""Restricted source-helper probe, executed only in a bounded source namespace.

Full ERPNext/Frappe imports do not execute. Numeric/date shims only model the
explicit finite fixture types; this is not an application or dependency run.
"""
import ast
import datetime as dt
import json
import sys
from types import SimpleNamespace

SERIES = {'steady': [100, 100, 100], 'ending_zero': [20, 40, 0], 'empty': [0, 0, 0]}


def flt(value):
    if value is None:
        return 0.0
    if type(value) not in (int, float):
        raise ValueError('numeric fixture type required')
    return float(value)


def getdate(value):
    if type(value) is not dt.date:
        raise ValueError('date fixture type required')
    return value


with open('/source.py') as source:
    tree = ast.parse(source.read())
classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and
           node.name == 'ExponentialSmoothingForecast']
if len(classes) != 1:
    raise ValueError('expected one source helper class')
node = classes[0]
if (node.bases or node.keywords or node.decorator_list or len(node.body) != 1 or
        not isinstance(node.body[0], ast.FunctionDef) or node.body[0].name != 'forecast_future_data'):
    raise ValueError('unexpected helper class shape')
namespace = {'flt': flt, 'getdate': getdate}
exec(compile(ast.Module(body=[node], type_ignores=[]), '/source.py', 'exec'), namespace)
helper_class = namespace['ExponentialSmoothingForecast']
rows = json.load(sys.stdin)
observed = []
for row in rows:
    values = SERIES[row['series']]
    nonzero = [value for value in values if value]
    average = sum(nonzero) / len(nonzero) if nonzero else 0.0
    seed = average if row['seed'] == 'mean_nonzero' else 50.0
    count = 3 + row['horizon']
    helper = helper_class()
    helper.filters = SimpleNamespace(from_date=dt.date(2020, 1, 4),
                                     smoothing_constant=float(row['alpha']))
    helper.period_list = [SimpleNamespace(key='p' + str(i), from_date=dt.date(2020, 1, 1) +
                                          dt.timedelta(days=i)) for i in range(count)]
    data = {'avg': seed, **{'p' + str(i): value for i, value in enumerate(values)}}
    helper.period_wise_data = {'fixture': data}
    helper.forecast_future_data()
    indices = range(3) if row['phase'] == 'past' else range(3, count)
    output = [data.get('forecast_p' + str(i), 0.0) for i in indices]
    observed.append({'input': row, 'output': output})
print(json.dumps(observed, allow_nan=False))
