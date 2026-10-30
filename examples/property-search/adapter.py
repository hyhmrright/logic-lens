"""Trusted adapter for the synthetic signed-axis example; no model/service calls."""
import json
from pathlib import Path
import sys

import axis

assert Path(axis.__file__).resolve() == Path.cwd() / 'axis.py'
case = json.load(sys.stdin)['case']
origin, delta = case['origin'], case['delta']
actual = axis.move(axis.move(origin, delta), -delta)
print(json.dumps(dict(status='pass' if actual == origin else 'violation',
                     observation=dict(expected=origin, actual=actual), sources=['axis.py'])))
