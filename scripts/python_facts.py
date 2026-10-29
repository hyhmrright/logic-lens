#!/usr/bin/env python3
"""Offline bounded Python AST interpretation and declaration checks. Never imports subject code."""
from dataclasses import dataclass
import argparse
import ast
import hashlib
import json
from pathlib import Path

from property_search import integer, read_json, relative_file


class Unsupported(Exception):
    pass


class SubjectRaise(Exception):
    pass


class Returned(Exception):
    def __init__(self, value):
        self.value = value


@dataclass(frozen=True)
class Affine:
    a: int
    b: int

    def __post_init__(self):
        if max(self.a.bit_length(), self.b.bit_length()) > 128:
            raise Unsupported('integer magnitude budget exceeded')

    def at(self, n):
        return self.a*n + self.b


@dataclass(frozen=True)
class Sequence:
    length: Affine
    unit: str


class Interpreter:
    def __init__(self, functions, consumer, n):
        self.functions, self.consumer, self.n = functions, consumer, n
        self.events = []
        self.steps = 0

    def tick(self):
        self.steps += 1
        if self.steps > 2000:
            raise Unsupported('AST step budget exceeded')

    def value(self, v):
        if isinstance(v, Affine):
            return v.at(self.n)
        return v

    def expr(self, node, env, depth):
        self.tick()
        if isinstance(node, ast.Constant):
            if type(node.value) is int:
                return Affine(0, node.value)
            if type(node.value) in (str, bytes):
                return Sequence(Affine(0, len(node.value)), 'byte' if type(node.value) is bytes else 'character')
            raise Unsupported('unsupported literal')
        if isinstance(node, ast.Name):
            if node.id not in env:
                raise Unsupported('unresolved name: ' + node.id)
            return env[node.id]
        if isinstance(node, ast.UnaryOp):
            v = self.expr(node.operand, env, depth)
            if isinstance(node.op, ast.Not):
                if type(v) is not bool:
                    raise Unsupported('only explicit boolean conditions supported')
                return not v
            if isinstance(v, Affine) and isinstance(node.op, (ast.USub, ast.UAdd)):
                sign = -1 if isinstance(node.op, ast.USub) else 1
                return Affine(sign*v.a, sign*v.b)
            raise Unsupported('unsupported unary expression')
        if isinstance(node, ast.BinOp):
            left, right = self.expr(node.left, env, depth), self.expr(node.right, env, depth)
            if isinstance(left, Affine) and isinstance(right, Affine):
                if isinstance(node.op, (ast.Add, ast.Sub)):
                    sign = -1 if isinstance(node.op, ast.Sub) else 1
                    return Affine(left.a+sign*right.a, left.b+sign*right.b)
                if isinstance(node.op, ast.Mult) and not (left.a and right.a):
                    return Affine(left.a*right.b + right.a*left.b, left.b*right.b)
            if isinstance(node.op, ast.Mult):
                seq, count = (left, right) if isinstance(left, Sequence) else (right, left)
                if isinstance(seq, Sequence) and isinstance(count, Affine) and not seq.length.a:
                    # Python negative repetition is zero; represent the actual piece,
                    # never extrapolate the positive affine expression across it.
                    if count.at(self.n) < 0:
                        return Sequence(Affine(0, 0), seq.unit)
                    return Sequence(Affine(seq.length.b*count.a, seq.length.b*count.b), seq.unit)
            raise Unsupported('nonlinear or unsupported binary expression')
        if isinstance(node, ast.BoolOp):
            for child in node.values:
                v = self.expr(child, env, depth)
                if type(v) is not bool:
                    raise Unsupported('only explicit boolean conditions supported')
                if isinstance(node.op, ast.Or) and v:
                    return True
                if isinstance(node.op, ast.And) and not v:
                    return False
            return isinstance(node.op, ast.And)
        if isinstance(node, ast.Compare):
            # Exact built-in integer type is known for the enumerated input only.
            if (len(node.ops) == 1 and isinstance(node.left, ast.Call)
                and isinstance(node.left.func, ast.Name) and node.left.func.id == 'type'
                and len(node.left.args) == 1 and not node.left.keywords
                and isinstance(node.comparators[0], ast.Name) and node.comparators[0].id == 'int'
                and isinstance(node.ops[0], (ast.Is, ast.IsNot))):
                value = self.expr(node.left.args[0], env, depth)
                is_int = isinstance(value, Affine)
                return is_int if isinstance(node.ops[0], ast.Is) else not is_int
            left = self.expr(node.left, env, depth)
            for op, rhs in zip(node.ops, node.comparators):
                right = self.expr(rhs, env, depth)
                if not isinstance(left, Affine) or not isinstance(right, Affine):
                    raise Unsupported('only integer comparison supported')
                a, b = self.value(left), self.value(right)
                if isinstance(op, ast.Lt): ok = a < b
                elif isinstance(op, ast.LtE): ok = a <= b
                elif isinstance(op, ast.Gt): ok = a > b
                elif isinstance(op, ast.GtE): ok = a >= b
                elif isinstance(op, ast.Eq): ok = a == b
                elif isinstance(op, ast.NotEq): ok = a != b
                else: raise Unsupported('unsupported comparison')
                if not ok:
                    return False
                left = right
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.keywords:
                raise Unsupported('keyword calls unsupported')
            name = node.func.id
            if name in env:
                raise Unsupported('local name shadows call target: ' + name)
            args = [self.expr(arg, env, depth) for arg in node.args]
            if name == 'len' and len(args) == 1 and isinstance(args[0], Sequence):
                return args[0].length
            if name in self.functions:
                if name == self.consumer:
                    if len(args) != 1:
                        raise Unsupported('consumer must have one argument')
                    v = args[0]
                    if len(self.events) >= 8:
                        raise Unsupported('consumer observation budget exceeded')
                    self.events.append(dict(line=node.lineno, expression=ast.unparse(node.args[0]), unit=v.unit if isinstance(v, Sequence) else 'unknown',
                        scale=v.length.a if isinstance(v, Sequence) else None,
                        offset=v.length.b if isinstance(v, Sequence) else None,
                        quantity=v.length.at(self.n) if isinstance(v, Sequence) else self.value(v)))
                return self.call(name, args, depth+1)
            raise Unsupported('unresolved or dynamic call: ' + name)
        raise Unsupported('unsupported expression: ' + type(node).__name__)

    def block(self, statements, env, depth):
        for node in statements:
            self.tick()
            if isinstance(node, ast.If):
                condition = self.expr(node.test, env, depth)
                if type(condition) is not bool:
                    raise Unsupported('nonboolean branch unsupported')
                self.block(node.body if condition else node.orelse, env, depth)
            elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                env[node.targets[0].id] = self.expr(node.value, env, depth)
            elif isinstance(node, ast.Return):
                raise Returned(self.expr(node.value, env, depth) if node.value else None)
            elif isinstance(node, ast.Raise):
                # Exception construction is not executed. Only explicit built-in
                # ValueError literals are accepted as a known rejecting exit.
                if (node.cause is not None or not isinstance(node.exc, ast.Call)
                    or not isinstance(node.exc.func, ast.Name) or node.exc.func.id != 'ValueError'
                    or node.exc.keywords or not all(isinstance(a, ast.Constant) and type(a.value) is str for a in node.exc.args)):
                    raise Unsupported('unsupported raise')
                raise SubjectRaise()
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                pass
            else:
                raise Unsupported('unsupported statement: ' + type(node).__name__)

    def call(self, name, values, depth=0):
        self.tick()
        if depth > 4:
            raise Unsupported('call-depth budget exceeded')
        f = self.functions[name]
        if (f.decorator_list or f.returns is not None or any(a.annotation is not None for a in f.args.args)
            or len({a.arg for a in f.args.args}) != len(f.args.args) or f.args.posonlyargs or f.args.kwonlyargs or f.args.vararg
            or f.args.kwarg or f.args.defaults or len(f.args.args) != len(values)):
            raise Unsupported('unsupported function signature')
        env = dict(zip((a.arg for a in f.args.args), values))
        try:
            self.block(f.body, env, depth)
        except Returned as ret:
            return ret.value
        return None


def ranges(points):
    out = []
    for n in sorted(set(points)):
        if out and n == out[-1][1]+1:
            out[-1][1] = n
        else:
            out.append([n, n])
    return out


def module_functions(text):
    tree = ast.parse(text)
    if sum(1 for _ in ast.walk(tree)) > 4000:
        raise Unsupported('AST size budget exceeded')
    functions = {}
    reserved = {'len', 'type', 'int', 'ValueError'}
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if not isinstance(node, ast.FunctionDef) or node.name in functions or node.name in reserved:
            raise Unsupported('module supports only unique functions and docstrings; no imports/global state/builtin shadowing')
        if (node.decorator_list or node.returns is not None or node.args.posonlyargs
            or node.args.kwonlyargs or node.args.vararg or node.args.kwarg or node.args.defaults
            or any(a.annotation is not None for a in node.args.args)
            or len({a.arg for a in node.args.args}) != len(node.args.args)):
            raise Unsupported('unsupported function definition/signature')
        if any(a.arg in reserved for a in node.args.args):
            raise Unsupported('builtin shadowing')
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store) and child.id in reserved:
                raise Unsupported('builtin shadowing')
        functions[node.name] = node
    return functions


def consumer_bound(f):
    # Recognize this sole guard form; never infer a normative contract from it.
    body = [n for n in f.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str))]
    if len(f.args.args) != 1 or len(body) != 2 or not isinstance(body[0], ast.If) or body[0].orelse:
        return None
    test = body[0].test
    if (not isinstance(test, ast.Compare) or len(test.ops) != 1 or not isinstance(test.ops[0], ast.Gt)
        or not isinstance(test.left, ast.Call) or not isinstance(test.left.func, ast.Name) or test.left.func.id != 'len'
        or len(test.left.args) != 1 or not isinstance(test.left.args[0], ast.Name) or test.left.args[0].id != f.args.args[0].arg
        or test.left.keywords or not isinstance(test.comparators[0], ast.Constant) or type(test.comparators[0].value) is not int
        or len(body[0].body) != 1 or not isinstance(body[0].body[0], ast.Raise)):
        return None
    rejection = body[0].body[0]
    if (rejection.cause is not None or not isinstance(rejection.exc, ast.Call)
        or not isinstance(rejection.exc.func, ast.Name) or rejection.exc.func.id != 'ValueError'
        or rejection.exc.keywords or not all(isinstance(a, ast.Constant) and type(a.value) is str for a in rejection.exc.args)
        or not isinstance(body[1], ast.Return)):
        return None
    return test.comparators[0].value


def analyze(spec, workspace):
    if not isinstance(spec, dict) or type(spec.get('schema_version')) is not int or spec.get('schema_version') != 1:
        raise ValueError('expected schema_version 1')
    path = relative_file(workspace, spec['source'])
    if path.stat().st_size > 131072:
        raise ValueError('source exceeds 128KiB')
    text = path.read_text()
    lo, hi = spec['analysis_domain']
    lo, hi = integer(lo, -10000, 10000, 'domain lower'), integer(hi, lo, 10000, 'domain upper')
    if hi-lo+1 > 128:
        raise ValueError('at most 128 integer inputs per analysis')
    result = dict(schema_version=1, source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  checked_scope=[lo, hi], scope='finite exact built-in integer inputs only; no claim outside this window',
                  spec_sha256=hashlib.sha256(json.dumps(spec, sort_keys=True, allow_nan=False).encode()).hexdigest())
    try:
        functions = module_functions(text)
        entry, consumer = spec['entry'], spec['consumer']
        if entry not in functions or consumer not in functions or entry == consumer:
            raise Unsupported('entry/consumer unresolved or identical')
        result['function_spans'] = {name:dict(start=f.lineno, end=f.end_lineno) for name,f in functions.items()}
        observations, errors = [], []
        for n in range(lo, hi+1):
            interpreter = Interpreter(functions, consumer, n)
            outcome = 'returned'
            try:
                interpreter.call(entry, [Affine(1, 0)])
            except SubjectRaise:
                outcome = 'rejected_after_consumer' if interpreter.events else 'rejected_before_consumer'
            except Unsupported as exc:
                errors.append(dict(input=n, reason=str(exc)))
                outcome = 'unsupported'
            observations.append(dict(input=n, outcome=outcome, consumers=interpreter.events))
        result['observations'] = observations
        if errors:
            return dict(result, status='unsupported', errors=errors,
                        limit='partial observations cannot qualify a declaration')
        reached = [o['input'] for o in observations if o['consumers']]
        events = [e for o in observations for e in o['consumers']]
        variants = sorted({(e['scale'], e['offset'], e['unit']) for e in events}, key=str)
        facts = dict(reachable=ranges(reached), rejected_before_consumer=ranges(o['input'] for o in observations if o['outcome']=='rejected_before_consumer'),
                     variants=[dict(scale=a, offset=b, unit=u) for a,b,u in variants],
                     implementation_consumer_bound=consumer_bound(functions[consumer]))
        result['facts'] = facts
        checks = {}
        declaration = spec['declaration']
        declared_a = integer(declaration['scale'], -10**9, 10**9, 'scale')
        declared_b = integer(declaration['offset'], -10**9, 10**9, 'offset')
        for field in ('scale', 'offset'):
            declared = integer(declaration[field], -10**9, 10**9, field)
            if not events:
                checks[field] = dict(status='unknown', reason='consumer not reached in checked scope')
            elif any(e[field] is None for e in events):
                checks[field] = dict(status='unknown', reason='quantity model unavailable')
            else:
                mismatch = next((o for o in observations if any(e[field] != declared for e in o['consumers'])), None)
                counterexample = next((dict(input=o['input'], observed=e['quantity'],
                    declared_quantity=declared_a*o['input']+declared_b)
                    for o in observations for e in o['consumers']
                    if e['quantity'] != declared_a*o['input']+declared_b), None) if mismatch else None
                checks[field] = dict(status='mismatch' if mismatch else 'matched_in_scope',
                                     witness=counterexample,
                                     comparison='source-derived affine coefficient, not regression fitting')
        declared_unit = declaration['output_unit']
        if not isinstance(declared_unit, str) or not declared_unit:
            raise ValueError('explicit output_unit required')
        known_units = {e['unit'] for e in events} - {'unknown'}
        if declared_unit not in ('byte', 'character', 'element') or not events or any(e['unit']=='unknown' for e in events):
            checks['output_unit'] = dict(status='unknown', reason='business/unknown unit cannot be established by code')
        else:
            checks['output_unit'] = dict(status='matched_in_scope' if known_units=={declared_unit} else 'mismatch', observed=sorted(known_units))
        intervals = declaration['route']
        if not isinstance(intervals, list) or len(intervals)>16:
            raise ValueError('route must contain at most 16 intervals')
        declared_points = set()
        for pair in intervals:
            a,b = pair
            a,b = integer(a, -10000, 10000, 'route lower'), integer(b, a, 10000, 'route upper')
            declared_points.update(range(max(a,lo), min(b,hi)+1))
        actual = set(reached)
        checks['route'] = dict(status='matched_in_scope' if actual==declared_points else 'mismatch',
                              omitted_reachable=ranges(actual-declared_points), falsely_reachable=ranges(declared_points-actual))
        if 'bound' in declaration:
            declared_bound = integer(declaration['bound'], -10**9, 10**9, 'bound')
            actual_bound = facts['implementation_consumer_bound']
            checks['bound'] = dict(status='unknown' if actual_bound is None else
                'matched_in_scope' if actual_bound == declared_bound else 'mismatch', observed=actual_bound)
        checks['input_business_unit'] = dict(status='unknown', reason='no business-unit inference')
        statuses = {c['status'] for c in checks.values()}
        return dict(result, status='mismatch' if 'mismatch' in statuses else 'checked_with_unknowns', checks=checks,
                    contract='Not extracted: runtime rejection does not redefine the public valid domain or prove a bug.')
    except (Unsupported, SyntaxError) as exc:
        return dict(result, status='unsupported', reason=str(exc))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--spec', type=Path, required=True)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    try:
        if a.out.resolve().is_relative_to(a.workspace.resolve()):
            raise ValueError('output must be outside source workspace')
        result = analyze(read_json(a.spec.read_text()), a.workspace.resolve())
        with a.out.open('x') as f:
            json.dump(result, f, indent=2, allow_nan=False)
            f.write('\n')
    except (ValueError, KeyError, TypeError, OSError, RecursionError) as exc:
        p.exit(2, f'error: {exc}\n')
    print(json.dumps(dict(status=result['status'], evidence=str(a.out.resolve()))))


if __name__ == '__main__':
    main()
