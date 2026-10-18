"""Typed bounded bottom-up search; the neural model only prioritises candidates."""
import itertools
import json
import math
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from features import Context
from base_features import features as base_features


@dataclass
class Candidate:
    ast: dict
    values: tuple
    type: str
    size: int
    serial: int
    priority: float = 0.0


def value_key(kind, values, domain):
    # Decimal equality ignores its printed exponent: 1.0 and 1.00 are the same
    # observation. This key is also used for supervised positive/negative labels.
    def canonical(v):
        if isinstance(v, bool):
            return ('bool', v)
        if isinstance(v, (Decimal, int)):
            numerator, denominator = v.as_integer_ratio()
            return ('number', numerator, denominator)
        if isinstance(v, date):
            return ('date', v.isoformat())
        if hasattr(v, 'value') and hasattr(v, 'month'):
            return ('state', canonical(v.value), v.month)
        raise ValueError('Unsupported observed value')
    return (kind, tuple(canonical(v) for v in values))


def heuristic(f):
    # Indices are named in features.NAMES; this fixed policy is frozen before tests.
    return 3 * f[37] - f[38] + .2 * f[42] - .03 * f[30]


def literal_bank(domain):
    if hasattr(domain, 'literal_bank'):
        return domain.literal_bank()
    return domain.LITERALS


def solve(task, options=None, model=None, collect=False, teacher=None, on_group=None):
    from domain import domain
    o = dict(time_ms=1000, max_candidates=20000, max_size=7, beam=32,
             pending_per_type=512, fifo_fraction=.2, max_retained=5000, shortlist=64,
             mode='fifo')
    o.update(options or {})
    if o['mode'] not in ('fifo', 'heuristic', 'neural', 'hybrid'):
        raise ValueError('Unknown search mode')
    if o['mode'] in ('neural','hybrid') and model is None:
        raise ValueError('Neural mode requires a model')
    if not 0 < o['fifo_fraction'] <= 1 or o['beam'] < 1 or not 1 <= o['max_size'] <= 9:
        raise ValueError('Invalid search bounds')
    start = time.perf_counter()
    deadline = start + o['time_ms'] / 1000
    xs = [tuple(domain.decode(a) for a in e['args']) for e in task['examples']]
    ys = tuple(domain.decode(e['y']) for e in task['examples'])
    input_types, output_type = task['input_types'], task['output_type']
    context=Context(ys,output_type,input_types,xs)
    teacher_nodes=defaultdict(list)
    if teacher is not None:
        def walk(node):
            if node['k']=='call':
                kind=domain.infer_type(node,input_types);values=tuple(domain.eval_ast(node,x) for x in xs)
                if not (kind==output_type and values==ys):
                    teacher_nodes[domain.tree_size(node)].append(Candidate(node,values,kind,domain.tree_size(node),-1))
            for child in node.get('args',[]):walk(child)
        walk(teacher)
    pools, seen, trace = defaultdict(dict), set(), []
    tested = duplicate = errors = retained = serial = pruned = 0
    feature_ms = inference_ms = 0.0
    found, found_ms, reason = None, None, 'size-bound'
    layer_reached = 0

    def stopped():
        nonlocal reason
        if time.perf_counter() >= deadline:
            reason = 'timeout'
            return True
        if tested >= o['max_candidates']:
            reason = 'candidate-bound'
            return True
        if retained >= o['max_retained']:
            reason = 'retained-bound'
            return True
        return False

    def accept(ast, values, kind, size, pending):
        nonlocal tested, duplicate, serial, found, found_ms
        tested += 1
        if kind == output_type and values == ys:
            now = time.perf_counter()
            if now < deadline:
                found, found_ms = ast, (now - start) * 1000
            return
        key = value_key(kind, values, domain)
        if key in seen:
            duplicate += 1
            return
        if len(pending[kind]) >= o['pending_per_type']:
            return
        if ast['k'] == 'call' and proposals[ast['op']] >= quotas[ast['op']]:
            return
        seen.add(key)
        if ast['k'] == 'call':
            proposals[ast['op']] += 1
        serial += 1
        candidate = Candidate(ast, values, kind, size, serial)
        pending[kind].append(candidate)
        if collect:
            trace.append(candidate)

    def select(pending, size):
        nonlocal retained, feature_ms, inference_ms, pruned, serial
        # Training only: add missing teacher values, then force-retain them so
        # later groups contain realistic competitors for every teacher depth.
        positive_by_kind=defaultdict(set)
        for c in teacher_nodes[size]:
            key=value_key(c.type,c.values,domain);positive_by_kind[c.type].add(key)
            if not any(value_key(z.type,z.values,domain)==key for z in pending[c.type]):
                serial+=1;c.serial=serial;pending[c.type].append(c)
        for kind,items in pending.items():
            if stopped():return
            tick=time.perf_counter()
            scores=context.heuristic(items) if o['mode']!='fifo' or size==1 else [0]*len(items)
            feature_ms+=(time.perf_counter()-tick)*1000
            for c,score in zip(items,scores):c.priority=float(score)
            reserve=math.ceil(o['beam']*o['fifo_fraction'])
            fifo=items[:reserve];rest=sorted(items[reserve:],key=lambda c:(-c.priority,c.serial))
            if on_group is not None and size>1:
                keys=positive_by_kind[kind]
                labels=[value_key(c.type,c.values,domain) in keys for c in items]
                if any(labels) and not all(labels):on_group(items,labels,context,kind,size)
            if o['mode'] in ('neural','hybrid') and size>1:
                if o['mode']=='hybrid':
                    heurs=rest[:8];short=rest[8:8+o['shortlist']]
                else:heurs=[];short=items[reserve:]
                tick=time.perf_counter();matrix=context.batch(short);feature_ms+=(time.perf_counter()-tick)*1000
                if stopped():return
                from inference import score_batch
                tick=time.perf_counter();scores=score_batch(matrix,model) if len(short) else []
                inference_ms+=(time.perf_counter()-tick)*1000
                if stopped():return
                for c,score in zip(short,scores):c.priority=float(score)
                rest=heurs+sorted(short,key=lambda c:(-c.priority,c.serial))
            elif o['mode']=='fifo' and size>1:rest=items[reserve:]
            chosen=(fifo+rest)[:o['beam']]
            if teacher is not None:
                keys=positive_by_kind[kind]
                forced=[c for c in items if value_key(c.type,c.values,domain) in keys]
                ids={c.serial for c in forced}
                chosen=(forced+[c for c in chosen if c.serial not in ids])[:o['beam']]
            pools[kind][size]=chosen;retained+=len(chosen);pruned+=len(items)-len(chosen)

    signatures = domain.primitive_signatures()
    # Retain only explicit types and signatures, never a teacher AST.
    if isinstance(signatures, list):
        signatures = {s['name']: s for s in signatures}
    operators_per_type = Counter(s['output'] for s in signatures.values())
    quotas = {name: max(1, o['pending_per_type'] // operators_per_type[s['output']])
              for name, s in signatures.items()}
    for size in range(1, min(o['max_size'], task.get('max_size', o['max_size'])) + 1):
        if stopped() or found:
            break
        layer_reached = size
        pending = defaultdict(list)
        proposals = defaultdict(int)
        if size == 1:
            for i, kind in enumerate(input_types):
                if stopped() or found:
                    break
                accept({'k': 'param', 'i': i}, tuple(x[i] for x in xs), kind, 1, pending)
            for ast in literal_bank(domain):
                if stopped() or found:
                    break
                try:
                    v = domain.eval_ast(ast, xs[0])
                    kind = domain.infer_type(ast, input_types)
                    accept(ast, tuple(v for _ in xs), kind, 1, pending)
                except (ValueError, TypeError, ArithmeticError, OverflowError):
                    errors += 1
        else:
            for op, signature in signatures.items():
                if stopped() or found:
                    break
                types, kind = signature['inputs'], signature['output']
                arity = len(types)
                if arity < 1 or arity > 3:
                    raise ValueError('This bounded prototype supports arity one to three')
                if len(pending[kind]) >= o['pending_per_type'] or proposals[op] >= quotas[op]:
                    continue
                partitions = itertools.product(range(1, size), repeat=arity)
                for costs in partitions:
                    if sum(costs) != size - 1:
                        continue
                    choices = [pools[t].get(c, []) for t, c in zip(types, costs)]
                    if any(not c for c in choices):
                        continue
                    for args in itertools.product(*choices):
                        if (stopped() or found or len(pending[kind]) >= o['pending_per_type']
                                or proposals[op] >= quotas[op]):
                            break
                        try:
                            values = tuple(domain.eval_primitive(op, [c.values[i] for c in args])
                                           for i in range(len(xs)))
                            ast = {'k': 'call', 'op': op, 'args': [c.ast for c in args]}
                            accept(ast, values, kind, size, pending)
                        except (ValueError, TypeError, ArithmeticError, OverflowError, IndexError):
                            errors += 1
                            tested += 1
                    if (stopped() or found or len(pending[kind]) >= o['pending_per_type']
                            or proposals[op] >= quotas[op]):
                        break
        if not found and not stopped():
            select(pending, size)
    elapsed = (time.perf_counter() - start) * 1000
    result = {'task_id': task.get('id'), 'mode': o['mode'], 'status': 'fit' if found else reason,
              'ast': found, 'found_ms': found_ms, 'wall_ms': elapsed, 'tested': tested,
              'duplicates': duplicate, 'errors': errors, 'retained': retained,
              'pruned': pruned, 'max_size_reached': layer_reached,
              'feature_ms': feature_ms, 'inference_ms': inference_ms,
              'network_calls': 0}
    if collect:
        return result, trace
    return result
