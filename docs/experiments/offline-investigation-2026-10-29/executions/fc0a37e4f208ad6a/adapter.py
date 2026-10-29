#!/usr/bin/env python3
"""Fixed executor for explicitly trusted synthetic investigation fixtures only."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def main():
    config = json.loads((Path(__file__).parent / 'execution.json').read_text())
    n = json.loads(sys.stdin.read())['case']['n']
    source = Path.cwd() / config['source']
    if hashlib.sha256(source.read_bytes()).hexdigest()!=config['source_sha256']:
        raise ValueError('source hash drift in execution copy')
    spec = importlib.util.spec_from_file_location('investigation_subject', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    observed = []
    consumer = getattr(module, config['consumer'])

    def observer(value):
        unit = 'byte' if type(value) is bytes else 'character' if type(value) is str else 'unknown'
        observed.append(dict(unit=unit, quantity=len(value) if unit != 'unknown' else None))
        return consumer(value)

    setattr(module, config['consumer'], observer)
    outcome = 'returned'
    try:
        value = getattr(module, config['entry'])(n)
    except ValueError:
        outcome, value = 'value_error', None
    actual=dict(outcome=outcome,consumers=observed)
    if actual!=config['fact_observations'].get(str(n)):
        print(json.dumps(dict(status='blocked',reason='actual execution contradicts interpreted facts',observation=actual)))
        return
    permitted = outcome == 'returned' or config['expectation'] == 'return_or_value_error'
    # Oracle is the independently supplied entry contract. Derived affine values
    # and consumer thresholds do not enter the expected/observed comparison.
    print(json.dumps(dict(status='pass' if permitted else 'violation',
        observation=dict(outcome=outcome, value=value, consumers=observed, input=n),
        sources=[config['source']]), allow_nan=False))


if __name__ == '__main__':
    main()
