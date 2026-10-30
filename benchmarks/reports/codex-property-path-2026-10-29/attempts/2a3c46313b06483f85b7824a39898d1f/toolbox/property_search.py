#!/usr/bin/env python3
"""Experimental finite property search. Executes trusted local adapters, never an LLM."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import tempfile
import time

from llm_runner import copy_workspace, tree_digest


def read_json(text):
    def invalid(value):
        raise ValueError(f'non-finite JSON value: {value}')
    return json.loads(text, parse_constant=invalid)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def relative_file(root, name):
    p = Path(name)
    if p.is_absolute() or not p.parts or '..' in p.parts:
        raise ValueError(f'expected relative file: {name}')
    target = root / p
    if not target.is_file() or target.is_symlink() or not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'file outside scope or missing: {name}')
    return target


def integer(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{label} must be an integer in [{low}, {high}]')
    return value


def validate(spec, workspace, spec_dir):
    if not isinstance(spec, dict):
        raise ValueError('spec must be a JSON object')
    if spec.get('schema_version') != 1:
        raise ValueError('expected schema_version 1')
    for key in ('id', 'claim', 'domain', 'observation', 'violation'):
        if not isinstance(spec.get(key), str) or not spec[key].strip():
            raise ValueError(f'missing property description: {key}')
    if len(spec['id']) > 80:
        raise ValueError('property id must be at most 80 characters')
    sources = spec.get('contract')
    if not isinstance(sources, list) or not sources:
        raise ValueError('contract references are required; absence is not a bug')
    for source in sources:
        p = relative_file(workspace, source['path'])
        lines = p.read_text().splitlines()
        start = integer(source['start'], 1, len(lines), 'contract start')
        end = integer(source['end'], start, len(lines), 'contract end')
        if source['quote'] != '\n'.join(lines[start-1:end]):
            raise ValueError('contract quotation does not match source')
    adapter = spec['adapter']
    files = adapter.get('files')
    if not isinstance(files, list) or not files or len(set(files)) != len(files):
        raise ValueError('adapter.files must list unique local adapter dependencies')
    for name in files:
        relative_file(spec_dir, name)
    argv = adapter.get('argv')
    if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
        raise ValueError('adapter.argv must be a nonempty string array')
    if not any('{adapter_dir}' in x for x in argv):
        raise ValueError('argv must use the archived {adapter_dir}')
    domains = spec.get('domains')
    if not isinstance(domains, dict) or not domains or len(domains) > 8:
        raise ValueError('one to eight finite domains are required')
    for values in domains.values():
        if not isinstance(values, list) or not 1 <= len(values) <= 64:
            raise ValueError('each domain needs 1..64 explicit JSON values')
        encoded = [json.dumps(v, sort_keys=True, allow_nan=False) for v in values]
        if len(set(encoded)) != len(encoded):
            raise ValueError('duplicate domain values')
    if math.prod(map(len, domains.values())) > 1000000:
        raise ValueError('domain product exceeds prototype limit')
    control = spec.get('control')
    if not isinstance(control, dict) or set(control) != set(domains):
        raise ValueError('control must name every domain')
    # JSON equality distinguishes booleans from numbers.
    def key(v):
        return json.dumps(v, sort_keys=True, allow_nan=False)
    for k, v in control.items():
        if key(v) not in [key(x) for x in domains[k]]:
            raise ValueError('control outside declared domain')
    limits = spec.get('limits', {})
    if not isinstance(limits, dict) or set(limits) - {'max_cases', 'seconds', 'case_seconds', 'output_bytes', 'shrink_cases'}:
        raise ValueError('unknown or invalid limits')
    for k, default, low, high in [('max_cases', 32, 1, 128), ('seconds', 10, 1, 60),
                                 ('case_seconds', 1, 1, 10), ('output_bytes', 4096, 256, 65536),
                                 ('shrink_cases', 8, 0, 32)]:
        integer(limits.get(k, default), low, high, k)
    integer(spec.get('seed', 0), 0, 2147483647, 'seed')
    return dict(max_cases=32, seconds=10, case_seconds=1, output_bytes=4096,
                shrink_cases=8) | limits


def stop_process(proc):
    try:
        if os.name == 'nt':
            if proc.poll() is None:
                proc.kill()
        else:
            os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        # Some hosts reject signalling an already-exited process group.
        if proc.poll() is None:
            proc.kill()
    proc.wait()


def invoke(argv, case, work, env, timeout, limit, dest):
    """Bound elapsed execution and retained output, preserving protocol failures."""
    dest.mkdir(parents=True)
    payload = json.dumps({'case': case}, allow_nan=False).encode()
    if len(payload) > 65536:
        return dict(status='blocked', reason='case payload exceeds 65536 bytes')
    (dest/'input.json').write_bytes(payload)
    started = time.monotonic()
    reason = None
    try:
        with (dest/'input.json').open('rb') as inp, (dest/'stdout.txt').open('wb') as out, (dest/'stderr.txt').open('wb') as err:
            proc = subprocess.Popen(argv, cwd=work, env=env, stdin=inp, stdout=out, stderr=err,
                                    start_new_session=os.name != 'nt')
            try:
                while True:
                    if any((dest/n).stat().st_size > limit for n in ['stdout.txt', 'stderr.txt']):
                        reason = 'output_limit'
                        break
                    if proc.poll() is not None:
                        break
                    if time.monotonic()-started >= timeout:
                        reason = 'timeout'
                        break
                    time.sleep(0.01)
            finally:
                stop_process(proc)
    except OSError as exc:
        return dict(status='blocked', reason=f'adapter launch: {exc}')
    raw = {}
    for name in ['stdout.txt', 'stderr.txt']:
        p = dest/name
        with p.open('rb') as f:
            b = f.read(limit+1)
        if len(b) > limit:
            reason = reason or 'output_limit'
            p.write_bytes(b[:limit])
        raw[name] = b[:limit].decode(errors='replace')
    if reason or proc.returncode:
        return dict(status='blocked', reason=reason or f'adapter exit {proc.returncode}')
    try:
        result = read_json(raw['stdout.txt'])
        if not isinstance(result, dict) or result.get('status') not in ('pass', 'violation', 'invalid', 'blocked'):
            raise ValueError('expected pass/violation/invalid/blocked')
        if result['status'] in ('pass', 'violation'):
            if 'observation' not in result or not result.get('sources'):
                raise ValueError('missing observation or loaded source provenance')
            if not isinstance(result['sources'], list):
                raise ValueError('sources must be a relative path list')
            result['source_sha256'] = {n: digest(relative_file(work, n)) for n in result['sources']}
        elif not isinstance(result.get('reason'), str) or not result['reason'].strip():
            raise ValueError('invalid/blocked response needs a reason')
        return result
    except (ValueError, KeyError, TypeError) as exc:
        return dict(status='blocked', reason=f'adapter protocol: {exc}')


def run(spec_path, workspace, out):
    spec_path, workspace, out = Path(spec_path).resolve(), Path(workspace).resolve(), Path(out).absolute()
    spec = read_json(spec_path.read_text())
    limits = validate(spec, workspace, spec_path.parent)
    if out.resolve().is_relative_to(workspace) or workspace.is_relative_to(out.resolve()):
        raise ValueError('output and workspace must be separate trees')
    out.mkdir(parents=True, exist_ok=False)
    (out/'spec.json').write_bytes(spec_path.read_bytes())
    adapter_dir = out/'adapter'
    for name in spec['adapter']['files']:
        target = adapter_dir/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(relative_file(spec_path.parent, name).read_bytes())
    argv = [x.replace('{python}', sys.executable).replace('{adapter_dir}', str(adapter_dir)) for x in spec['adapter']['argv']]
    source_before = tree_digest(workspace)
    rows, counterexample = [], None
    counts = dict(pass_count=0, violation=0, invalid=0, blocked=0)
    names = list(spec['domains'])
    values = list(spec['domains'].values())
    control = spec['control']
    control_index = [next(i for i, v in enumerate(vs) if json.dumps(v, sort_keys=True) == json.dumps(control[k], sort_keys=True))
                     for k, vs in zip(names, values)]
    total = math.prod(map(len, values))
    def decode(index):
        result = []
        for vs in reversed(values):
            index, remainder = divmod(index, len(vs))
            result.append(remainder)
        return list(reversed(result))
    def case_at(indices):
        return {k: vs[i] for k, vs, i in zip(names, values, indices)}
    control_ordinal = 0
    for i, vs in zip(control_index, values):
        control_ordinal = control_ordinal*len(vs)+i
    rng = random.Random(spec.get('seed', 0))
    # The control is always first, followed by unique sampled combinations.
    selected = rng.sample(range(total-1), min(total-1, limits['max_cases']-1))
    candidates = [decode(i if i < control_ordinal else i+1) for i in selected]
    state = 'incomplete'
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='logic-lens-property-') as temp:
        work = Path(temp)/'workspace'
        copy_workspace(workspace, work)
        executed_before = tree_digest(work)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(work/'src')+os.pathsep+str(work))
        def check(indices, phase):
            remaining = limits['seconds']-(time.monotonic()-started)
            if len(rows) >= limits['max_cases'] or remaining <= 0:
                return None
            case = case_at(indices)
            result = invoke(argv, case, work, env, min(limits['case_seconds'], remaining),
                            limits['output_bytes'], out/f'cases/{len(rows):03d}')
            counts['pass_count' if result['status']=='pass' else result['status']] += 1
            row = dict(case=case, phase=phase, result=result)
            rows.append(row)
            return row
        first = check(control_index, 'control')
        if first is None:
            state = 'incomplete'
        elif first['result']['status'] != 'pass':
            state = 'control_failed'
        else:
            for indices in candidates:
                row = check(indices, 'search')
                if row is None:
                    state = 'incomplete'
                    break
                if row['result']['status'] == 'blocked':
                    state = 'blocked'
                    break
                if row['result']['status'] == 'violation':
                    state, counterexample = 'counterexample', row
                    current = list(indices)
                    # Finite coordinate reduction toward the declared control.
                    # This is not a globally minimal witness guarantee.
                    shrinking = 0
                    shrink_stopped = False
                    for axis, vs in enumerate(values):
                        order = [control_index[axis]] + [i for i in range(len(vs)) if i != control_index[axis]]
                        choices = order[:order.index(current[axis])]
                        tried = set()
                        for choice in choices:
                            if choice in tried or choice == current[axis]:
                                continue
                            tried.add(choice)
                            if shrinking >= limits['shrink_cases']:
                                break
                            proposed = current.copy(); proposed[axis] = choice
                            # Never revisit a combination already evaluated.
                            if any(json.dumps(r['case'], sort_keys=True) == json.dumps(case_at(proposed), sort_keys=True) for r in rows):
                                continue
                            reduced = check(proposed, 'shrink')
                            if reduced is None:
                                shrink_stopped = True
                                break
                            shrinking += 1
                            if reduced['result']['status'] == 'blocked':
                                shrink_stopped = True
                                break
                            if reduced['result']['status'] == 'violation':
                                current, counterexample = proposed, reduced
                                break
                        if shrink_stopped:
                            break
                    break
            else:
                state = 'exhausted' if total <= limits['max_cases'] else 'sampled'
        executed_after = tree_digest(work)
    source_after = tree_digest(workspace)
    integrity = dict(original_before=source_before, original_after=source_after,
                     executed_before=executed_before, executed_after=executed_after)
    if source_before != source_after or executed_before != executed_after:
        state = 'integrity_failure'
        counterexample = None
    summary = dict(schema_version=1, status=state, property_id=spec['id'], limits=limits,
                   domain_size=total, evaluations=len(rows), counts=counts,
                   counterexample=counterexample, integrity=integrity,
                   elapsed_seconds=time.monotonic()-started,
                   conclusion='Adapter results require contract, harness and reachability review; no confirmed bug or correctness claim.',
                   argv=argv)
    (out/'observations.json').write_text(json.dumps(rows, indent=2, allow_nan=False)+'\n')
    (out/'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False)+'\n')
    manifest = {str(p.relative_to(out)):digest(p) for p in sorted(out.rglob('*')) if p.is_file()}
    (out/'sha256.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--spec', type=Path, required=True)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    try:
        summary = run(args.spec, args.workspace, args.out)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        p.exit(2, f'error: {exc}\n')
    # No per-case success output or full-source dump enters model context.
    compact = {k:summary[k] for k in ['status','property_id','evaluations','counts','counterexample']}
    compact['evidence'] = str(args.out.resolve())
    if len(json.dumps(compact).encode()) > 4096:
        compact['counterexample'] = dict(details='summary.json',
            case_sha256=hashlib.sha256(json.dumps(summary['counterexample'], sort_keys=True).encode()).hexdigest())
    print(json.dumps(compact, allow_nan=False))
    return 2 if summary['status'] in ('control_failed','blocked','integrity_failure','incomplete') else 0


if __name__ == '__main__':
    sys.exit(main())
