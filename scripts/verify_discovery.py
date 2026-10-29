#!/usr/bin/env python3
"""Verify historical source pairs with evaluator-only oracles, without model calls."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from discovery_eval import CATALOG, ROOT, materialize, read_json, write_json


def classify_pair(buggy, fixed):
    if buggy == 77 or fixed == 77:
        return 'blocked-platform'
    if buggy == 0:
        return 'not-reproduced'
    return 'pair-passed-needs-failure-inspection' if fixed == 0 else 'blocked-or-failed'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, required=True)
    parser.add_argument('--python', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cases', nargs='+')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    # Resolving a venv symlink discards pyvenv.cfg and selects the system environment.
    python = str(Path(args.python).absolute())
    freeze = subprocess.run([python, '-m', 'pip', 'freeze'], capture_output=True, text=True, check=True)
    (args.out / 'environment.txt').write_text(freeze.stdout)
    cases = read_json(CATALOG)['cases']
    selected = [c for c in cases if not args.cases or c['id'] in args.cases]
    if not selected or (args.cases and set(args.cases) != {c['id'] for c in selected}):
        parser.error('unknown or empty case selection')
    summary = []
    for case in selected:
        results = {}
        for repaired in (False, True):
            variant = 'fixed' if repaired else 'buggy'
            with tempfile.TemporaryDirectory(prefix='logic-lens-oracle-') as temp:
                workspace = Path(temp) / 'source'
                materialize(case, args.sources, workspace, repaired)
                command = [python, str(ROOT / 'evals/discovery/oracles.py'), case['id'], str(workspace)]
                try:
                    proc = subprocess.run(command, cwd=workspace, capture_output=True, text=True, timeout=10)
                    code, output = proc.returncode, proc.stdout + proc.stderr
                except subprocess.TimeoutExpired as exc:
                    code, output = 124, f'TIMEOUT: {exc}'
                (args.out / f"{case['id']}.{variant}.txt").write_text(output)
                results[variant] = code
        status = classify_pair(results['buggy'], results['fixed'])
        row = dict(case_id=case['id'], status=status, exit_codes=results,
                   note='Inspect failure log: setup/import errors do not verify the target defect.')
        summary.append(row)
        print(f"{case['id']}: {status} {results}", flush=True)
        write_json(args.out / 'summary.json', summary)
    print(json.dumps({'cases': len(summary), 'output': str(args.out)}))


if __name__ == '__main__':
    main()
