"""64 bounded search features, from public examples and candidate code only."""
import calendar
import datetime as dt
import math
from decimal import Decimal, InvalidOperation

TYPES = ('money', 'date', 'int', 'state', 'bool', 'other')
ROOTS = ('param', 'literal', 'add', 'sub', 'mul', 'divide', 'round', 'min',
         'max', 'if', 'le', 'month', 'day', 'business', 'weekday', 'state_init',
         'state_premium', 'state_fee', 'state_management', 'state_growth',
         'state_value', 'state_month', 'call', 'other')
NAMES = ([f'type_{t}' for t in TYPES] + [f'root_{t}' for t in ROOTS] +
         ['size_log', 'depth_log', 'parameter_fraction', 'literal_fraction',
          'unary_fraction', 'multi_argument_fraction', 'compatible_type',
          'exact_fraction', 'relative_mae_log', 'relative_rmse_log',
          'relative_max_error_log', 'relative_bias', 'correlation', 'abs_correlation',
          'affine_mae_log', 'affine_rmse_log', 'prediction_mean_log', 'target_mean_log',
          'prediction_std_log', 'target_std_log', 'std_log_ratio', 'range_log_ratio',
          'prediction_zero_fraction', 'target_zero_fraction', 'sign_agreement',
          'prediction_unique_fraction', 'target_unique_fraction', 'ordered_prediction',
          'date_weekday_agreement', 'date_day_agreement', 'date_month_agreement',
          'prediction_month_end', 'state_clock_agreement', 'prediction_cent_fraction'])
assert len(NAMES) == 64


def positive_log(x):
    z = math.log1p(min(1e100, max(0.0, float(x))))
    return z / (1.0 + z)


def squash(x):
    return x / (1.0 + abs(x))


def signed_log(x):
    return math.copysign(positive_log(abs(x)), x) if x else 0.0


def scalar(x):
    if isinstance(x, dt.date):
        return float(x.toordinal())
    if hasattr(x, 'value') and hasattr(x, 'month'):
        return scalar(x.value)
    z = float(x)
    if not math.isfinite(z):
        raise ValueError('Nonfinite public value')
    return max(-1e100, min(1e100, z))


def root_category(ast):
    if ast['k'] == 'param':
        return 'param'
    if ast['k'] == 'lit':
        return 'literal'
    name = ast.get('op', '').lower()
    if name.startswith('state_'):
        if name == 'state_credit':
            return 'state_premium'
        if name == 'state_grow':
            return 'state_growth'
        for key in ('init', 'premium', 'fee', 'management', 'growth', 'value', 'month'):
            if key in name:
                return 'state_' + key
    for key, patterns in [('business', ('business', 'following', 'weekday_shift')),
                          ('round', ('round', 'truncate', 'half_')),
                          ('month', ('month',)), ('weekday', ('weekday',)),
                          ('day', ('day',)), ('add', ('add', 'credit')),
                          ('sub', ('sub', 'deduct')), ('mul', ('mul',)),
                          ('divide', ('div',)), ('min', ('min', 'cap')),
                          ('max', ('max', 'floor')), ('if', ('if', 'choose')),
                          ('le', ('less', '_le', 'le_', 'before'))]:
        if any(p in name for p in patterns):
            return key
    return 'call'


def structure(ast):
    total = depth = params = literals = unary = multi = 0
    pending = [(ast, 1)]
    while pending:
        node, level = pending.pop()
        total += 1
        depth = max(depth, level)
        params += node['k'] == 'param'
        literals += node['k'] == 'lit'
        children = node.get('args', [])
        unary += len(children) == 1
        multi += len(children) >= 2
        pending.extend((child, level + 1) for child in children)
    return total, depth, params, literals, unary, multi


def features(ast, values, targets, candidate_type, output_type):
    if not values or len(values) != len(targets):
        raise ValueError('Public vectors must have equal nonzero length')
    n = len(values)
    total, depth, params, literals, unary, multi = structure(ast)
    kind = candidate_type if candidate_type in TYPES else 'other'
    root = root_category(ast)
    x, y = [scalar(v) for v in values], [scalar(v) for v in targets]
    # Relative date features measure days, instead of comparing large ordinals.
    if candidate_type == output_type == 'date':
        origin = min(y)
        x, y = [v - origin for v in x], [v - origin for v in y]
    sx_scale, sy_scale = max(1.0, max(map(abs, x))), max(1.0, max(map(abs, y)))
    xn, yn = [v / sx_scale for v in x], [v / sy_scale for v in y]
    mx, my = sum(xn) / n, sum(yn) / n
    vx = sum((v - mx) ** 2 for v in xn) / n
    vy = sum((v - my) ** 2 for v in yn) / n
    covariance = sum((a - mx) * (b - my) for a, b in zip(xn, yn)) / n
    correlation = max(-1.0, min(1.0, covariance / math.sqrt(vx * vy))) if vx and vy else 0.0
    errors = [(a - b) / (1.0 + abs(b)) for a, b in zip(x, y)]
    std_x, std_y = math.sqrt(vx) * sx_scale, math.sqrt(vy) * sy_scale
    slope = covariance / vx if vx else 0.0
    affine = [((my + slope * (v - mx)) * sy_scale - b) / (1.0 + abs(b))
              for v, b in zip(xn, y)]
    compatible = candidate_type == output_type
    is_date = compatible and candidate_type == 'date'
    is_state = compatible and candidate_type == 'state'
    frac = lambda predicate: sum(predicate(a, b) for a, b in zip(values, targets)) / n
    def cents(v):
        if not isinstance(v, Decimal):
            return False
        try:
            return v == v.quantize(Decimal('.01'))
        except InvalidOperation:
            return False
    result = ([float(kind == t) for t in TYPES] + [float(root == t) for t in ROOTS] +
              [positive_log(total), positive_log(depth), params / total, literals / total,
               unary / total, multi / total, float(compatible),
               frac(lambda a, b: compatible and a == b),
               positive_log(sum(map(abs, errors)) / n),
               positive_log(math.sqrt(sum(v * v for v in errors) / n)),
               positive_log(max(map(abs, errors))), squash(sum(errors) / n),
               correlation, abs(correlation), positive_log(sum(map(abs, affine)) / n),
               positive_log(math.sqrt(sum(v * v for v in affine) / n)),
               signed_log(mx * sx_scale), signed_log(my * sy_scale),
               positive_log(std_x), positive_log(std_y),
               squash(math.log1p(std_x) - math.log1p(std_y)),
               squash(math.log1p(max(x) - min(x)) - math.log1p(max(y) - min(y))),
               sum(v == 0 for v in x) / n, sum(v == 0 for v in y) / n,
               sum((a > 0) - (a < 0) == (b > 0) - (b < 0) for a, b in zip(x, y)) / n,
               len(set(map(repr, values))) / n, len(set(map(repr, targets))) / n,
               float(all(a <= b for a, b in zip(x, x[1:]))),
               frac(lambda a, b: is_date and a.weekday() == b.weekday()),
               frac(lambda a, b: is_date and a.day == b.day),
               frac(lambda a, b: is_date and a.month == b.month),
               sum(isinstance(a, dt.date) and a.day == calendar.monthrange(a.year, a.month)[1]
                   for a in values) / n,
               frac(lambda a, b: is_state and a.month == b.month),
               sum(cents(v.value if hasattr(v, 'value') else v) for v in values) / n])
    if len(result) != 64 or not all(math.isfinite(v) for v in result):
        raise ValueError('Invalid feature vector')
    return result
