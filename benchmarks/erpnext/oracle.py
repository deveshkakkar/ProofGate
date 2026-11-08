"""Independent Decimal fixture oracle; never imports the upstream helper."""
from decimal import Decimal

SERIES = {'steady': [100, 100, 100], 'ending_zero': [20, 40, 0], 'empty': [0, 0, 0]}


def future(row):
    actuals = SERIES[row['series']]
    nonzero = [Decimal(value) for value in actuals if value]
    if not nonzero:
        level = Decimal(0)
    else:
        level = sum(nonzero) / len(nonzero) if row['seed'] == 'mean_nonzero' else Decimal(50)
        alpha = Decimal(row['alpha'])
        for actual in actuals:
            level = alpha * actual + (1 - alpha) * level
    return [float(level)] * row['horizon']
