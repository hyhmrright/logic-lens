"""Evaluator-only real-source obligations; never supplied to a review workspace."""
import os
import subprocess
import sys
from pathlib import Path


def probe(case, workspace, python):
    workspace = Path(workspace).absolute()
    python = str(Path(python).absolute())
    if case == 'dateutil-inequality':
        code = ('from dateutil.relativedelta import relativedelta\n'
                'd=relativedelta(days=1)\n'
                'assert (d == None) is False\n'
                'assert (d != None) is True\n'
                'assert (d != 19) is True\n')
    elif case == 'dateutil-midnight':
        code = ('from dateutil.parser import isoparse\nfrom datetime import datetime\n'
                'assert isoparse("2014-04-10T24:00") == datetime(2014,4,11)\n'
                'assert isoparse("2019-12-31T24:00") == datetime(2020,1,1)\n')
    elif case == 'semver-diff':
        code = ("const d=require('./functions/diff'); const a=require('node:assert/strict');"
                "a.equal(d('1.7.2-1','1.8.1'),'minor');"
                "a.equal(d('1.1.1-pre','2.1.1'),'major');")
    elif case == 'semver-build':
        code = ("const R=require('./classes/range');const a=require('node:assert/strict');"
                "const r=new R('4.17.0+'+'a'.repeat(250)+'3',{loose:true});"
                "a.equal(r.range,'4.17.0');a.equal(r.test('4.17.0'),true);")
    else:
        raise ValueError(case)
    if case.startswith('dateutil-'):
        code = ('import dateutil\nfrom pathlib import Path\n'
                'assert Path(dateutil.__file__).resolve().is_relative_to(Path.cwd().resolve())\n' + code)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
               PYTHONPATH=str(workspace / 'src') + os.pathsep + str(workspace))
    cmd = [python, '-c', code] if case.startswith('dateutil-') else ['node', '-e', code]
    result = subprocess.run(cmd, cwd=workspace, env=env, text=True, capture_output=True, timeout=10)
    return dict(command=cmd, returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)


if __name__ == '__main__':
    import json
    print(json.dumps(probe(*sys.argv[1:]), indent=2))
