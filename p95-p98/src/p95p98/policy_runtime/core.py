"""Restricted policy grammar and bounded source-only JSON transport."""
import ast
import json
import math
import re

MAX_REQUEST = 256000
MAX_RESPONSE = 65536
MAX_RSS = 256 * 1024 * 1024
SAFE = {n: v for n, v in zip(
    ('abs', 'bool', 'dict', 'float', 'int', 'len', 'list', 'max', 'min', 'range', 'round', 'str', 'sum', 'tuple'),
    (abs, bool, dict, float, int, len, list, max, min, range, round, str, sum, tuple))}
FORBIDDEN = (ast.Import, ast.ImportFrom, ast.Attribute, ast.ClassDef,
    ast.AsyncFunctionDef, ast.Await, ast.With, ast.AsyncWith, ast.Global,
    ast.Nonlocal, ast.Delete, ast.Try, ast.Lambda, ast.Yield, ast.YieldFrom)
NAMES = {'breakpoint', 'compile', 'eval', 'exec', 'getattr', 'globals', 'help',
    'input', 'locals', 'memoryview', 'open', 'setattr', 'vars'}


class PolicyRuntimeError(RuntimeError):
    pass


def validate_source(source):
    if type(source) is not str or len(source.encode()) > 64000:
        raise PolicyRuntimeError('source exceeds 64KB')
    try:
        tree = ast.parse(source)
    except (SyntaxError, RecursionError) as e:
        raise PolicyRuntimeError('invalid source syntax') from e
    nodes = list(ast.walk(tree))
    if len(nodes) > 8000 or len(tree.body) != 1 or type(tree.body[0]) is not ast.FunctionDef:
        raise PolicyRuntimeError('source must define only decide(view)')
    fn = tree.body[0]
    a = fn.args
    if (fn.name != 'decide' or fn.decorator_list or fn.returns or a.posonlyargs or
        len(a.args) != 1 or a.args[0].arg != 'view' or a.args[0].annotation or
        a.vararg or a.kwarg or a.kwonlyargs or a.defaults):
        raise PolicyRuntimeError('source must define only decide(view)')
    for node in nodes:
        if isinstance(node, FORBIDDEN) or isinstance(node, ast.FunctionDef) and node is not fn:
            raise PolicyRuntimeError('forbidden syntax: ' + type(node).__name__)
        if isinstance(node, ast.Name) and (node.id.startswith('__') or node.id in NAMES):
            raise PolicyRuntimeError('forbidden name')
        if isinstance(node, ast.Call) and (not isinstance(node.func, ast.Name) or node.func.id not in SAFE):
            raise PolicyRuntimeError('only direct safe builtin calls allowed')
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str) and len(node.value) > 10000:
                raise PolicyRuntimeError('oversized string literal')
            if type(node.value) is int and abs(node.value) > 10000000:
                raise PolicyRuntimeError('oversized integer literal')


def encode(value, limit):
    try:
        data = json.dumps(value, allow_nan=False, separators=(',', ':')).encode() + b'\n'
    except (ValueError, TypeError, RecursionError) as e:
        raise PolicyRuntimeError('finite JSON required') from e
    if len(data) > limit:
        raise PolicyRuntimeError('message exceeds byte bound')
    return data


def decode(data):
    def unique(pairs):
        out = {}
        for k, v in pairs:
            if k in out:
                raise PolicyRuntimeError('duplicate JSON key')
            out[k] = v
        return out
    def bad(_):
        raise PolicyRuntimeError('nonfinite JSON')
    return json.loads(data, object_pairs_hook=unique, parse_constant=bad)


def _source_value(value, depth=0):
    if depth > 20:
        raise PolicyRuntimeError('source nesting too deep')
    if value is None or type(value) is bool:
        return value
    if type(value) in (float, int):
        if not math.isfinite(value):
            raise PolicyRuntimeError('nonfinite source field')
        return value
    if type(value) is str:
        if not re.fullmatch(r'[A-Za-z0-9_:+. -]{0,80}', value):
            raise PolicyRuntimeError('source strings must be bounded tokens, not paths')
        return value
    if type(value) is list:
        return [_source_value(v, depth + 1) for v in value]
    if type(value) is dict:
        out = {}
        for k, v in value.items():
            if type(k) is not str or len(k) > 80:
                raise PolicyRuntimeError('invalid source field')
            low = k.lower()
            if any(x in low for x in ('target', 'rmsd', 'path', 'pdb', 'heldout', 'validation', 'test_quality')) or low in {'case', 'case_id', 'logical_id', 'task_id', 'parent_id', 'component', 'identifier', 'filename', 'protein_id'}:
                raise PolicyRuntimeError('non-source field: ' + k)
            out[k] = _source_value(v, depth + 1)
        return out
    raise PolicyRuntimeError('source view must contain plain JSON')


def project_source(observation, fields):
    if type(observation) is not dict or set(observation) != set(fields):
        raise PolicyRuntimeError('observation differs from host source whitelist')
    # Whitelist must be frozen by the host projector, not supplied by candidate.
    sequence = observation.get('sequence')
    if 'sequence' in observation:
        if type(sequence) is not str or not 1 <= len(sequence) <= 5000 or any(aa not in 'ACDEFGHIKLMNPQRSTVWYBXZJUO' for aa in sequence):
            raise PolicyRuntimeError('source sequence must contain 1..5000 amino acids')
    projected = _source_value({k: v for k, v in observation.items() if k != 'sequence'})
    if 'sequence' in observation:
        projected['sequence'] = sequence
    encode(projected, MAX_REQUEST)
    return projected
