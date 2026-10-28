"""Evaluator-only behavioral checks arising in revision-2 reviews."""
from pathlib import Path
import os
import subprocess

# These diagnostic assertions reproduce observations but have an unsettled oracle.
UNESTABLISHED = {'semver-minor-graduation'}

CHECKS = {
    'dateutil-ordinal-space': ('dateutil-midnight', "from dateutil.parser import isoparse\nfrom datetime import datetime\na=isoparse('2017123 1230');b=isoparse('2017-123 1230')\nassert b==datetime(2017,5,3,12,30)\nassert a==b, (a,b)"),
    'semver-intersection-prerelease': ('semver-build', "const R=require('./classes/range'),a=require('node:assert/strict');a.equal(new R('*').intersects(new R('1.2.3-alpha')),false);"),
    'semver-intersection-prerelease-gap': ('semver-build', "const R=require('./classes/range'),a=require('node:assert/strict');a.equal(new R('>1.0.0-alpha',{includePrerelease:true}).intersects(new R('<1.0.0-alpha.0',{includePrerelease:true}),{includePrerelease:true}),false);"),
    'semver-intersection-witness': ('semver-build', "const R=require('./classes/range'),a=require('node:assert/strict');const x=new R('>=1.2.3-alpha <2.0.0'),y=new R('1.2.3-beta');a.equal(x.test('1.2.3-beta')&&y.test('1.2.3-beta'),true);a.equal(x.intersects(y),true);"),
    'semver-zero-lower-bound': ('semver-build', "const R=require('./classes/range'),a=require('node:assert/strict');a.equal(new R('>=0.0.0 <=0.0.0-alpha').test('0.0.0-alpha'),false);"),
    'semver-intersection-asymmetry': ('semver-build', "const R=require('./classes/range'),a=require('node:assert/strict');const x=new R('*'),y=new R('1.2.3-alpha');a.equal(x.intersects(y),y.intersects(x));"),
    'semver-diff-loose': ('semver-diff', "const d=require('./functions/diff'),a=require('node:assert/strict');a.equal(d('1.02.3','1.3.0',{loose:true}),'minor');"),
    'semver-intersection-gap': ('semver-build', "const R=require('./classes/range'),a=require('node:assert/strict');a.equal(new R('>1.0.0 <1.0.1').intersects(new R('*')),false);"),
    'semver-intersection-empty': ('semver-build', "const R=require('./classes/range'),a=require('node:assert/strict');a.equal(new R('<0.0.0-0').intersects(new R('*')),false);"),
    'semver-padded-caret': ('semver-build', "const R=require('./classes/range'),a=require('node:assert/strict');a.equal(new R('^00.0.1',{loose:true}).test('0.5.0'),false);"),
    'semver-hyphen-build': ('semver-build', "const R=require('./classes/range'),a=require('node:assert/strict');a.equal(new R('1.2.3+build - 2.0.0',{includePrerelease:true}).test('1.2.3-alpha'),true);"),
    'dateutil-time-midnight': ('dateutil-midnight', "from dateutil.parser.isoparser import isoparser\nfrom datetime import time\nassert isoparser().parse_isotime('24:00') == time(0,0)"),
    'dateutil-mixed-delimiters': ('dateutil-midnight', "from dateutil.parser import isoparse\ntry: isoparse('20120425T01:2000')\nexcept ValueError: pass\nelse: raise AssertionError('explicit expected-rejection fixture accepted')"),
    'semver-minor-graduation': ('semver-diff', "const d=require('./functions/diff'),a=require('node:assert/strict');a.equal(d('1.1.0-pre','1.1.1'),'minor');"),
    'semver-numeric-precision': ('semver-diff', "const d=require('./functions/diff'),a=require('node:assert/strict');a.equal(d('1.2.3-9007199254740992','1.2.3-9007199254740993'),'prerelease');"),
    'semver-comparator-options': ('semver-build', "const R=require('./classes/range'),C=require('./classes/comparator'),a=require('node:assert/strict');a.equal(new R(new C('>=1.2.3-alpha')).test('1.2.3-beta'),true);"),
    'semver-or-prerelease': ('semver-build', "const R=require('./classes/range'),a=require('node:assert/strict');a.equal(new R('* || >=1.2.3-alpha').test('1.2.3-beta'),true);"),
    'semver-invalid-build': ('semver-build', "const valid=require('./ranges/valid'),a=require('node:assert/strict');a.equal(valid('+build'),null);a.equal(valid('1.2.3+foo+bar'),null);"),
    'dateutil-byte-separator': ('dateutil-midnight', "from dateutil.parser.isoparser import isoparser\nfrom datetime import datetime\nassert isoparser(sep=b'T').isoparse('2017-12-06T12:30:45') == datetime(2017,12,6,12,30,45)"),
    'dateutil-weekday-hash': ('dateutil-inequality', "from dateutil.relativedelta import relativedelta,MO\na=relativedelta(weekday=MO);b=relativedelta(weekday=MO(1))\nassert a==b\nassert {a:'present'}.get(b)=='present'"),
    'dateutil-yearday366': ('dateutil-inequality', "from dateutil.relativedelta import relativedelta\nfrom datetime import date\nassert date(2024,1,1)+relativedelta(yearday=366)==date(2024,12,31)"),
    'dateutil-fractional-scaling': ('dateutil-inequality', "from dateutil.relativedelta import relativedelta\nfrom datetime import datetime\na=datetime(2024,1,1);d=relativedelta(days=0.5)\nassert a+d*1==a+d\nassert a+d/1==a+d"),
}


def run_check(behavior, workspace, python):
    case, code = CHECKS[behavior]
    workspace = Path(workspace).absolute()
    if case.startswith('dateutil-'):
        code = ('import dateutil\nfrom pathlib import Path\n'
                'assert Path(dateutil.__file__).resolve().is_relative_to(Path.cwd().resolve())\n' + code)
    command = ([str(Path(python).absolute()), '-c', code] if case.startswith('dateutil-')
               else ['node', '-e', code])
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
               PYTHONPATH=str(workspace/'src')+os.pathsep+str(workspace))
    result = subprocess.run(command, cwd=workspace, env=env, capture_output=True,
                            text=True, timeout=10)
    return dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
