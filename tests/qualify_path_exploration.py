#!/usr/bin/env python3
"""Reproduce synthetic qualification then read-only stdlib integration.

Only the repository's explicitly trusted synthetic fixture is compiled/executed.
Selected real files are parsed/read/hashed only. No target imports or real tests.
"""
import ast
import hashlib
import json
from pathlib import Path
import sys
import sysconfig

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from path_exploration import explore
from test_path_exploration import actual_table, TEXT, TESTS


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n')


def signature(row):
    return tuple((p['function'],p['line'],p['decision']) for p in row['trace'] if 'implicit' not in p)


def run(out):
    if out.exists():raise ValueError('output exists')
    out.mkdir(parents=True)
    table=actual_table()  # 8 roots *16 concrete integers; evaluator-only exhaustive reference.
    write(out/'evaluator.json',[dict(entry=name,input=n,**r) for (name,n),r in table.items()])
    modes={}
    for mode in ('seeds','evidence','paths'):
        r=explore(TEXT,TESTS,window=(0,15),mode=mode)
        write(out/f'{mode}.json',r)
        coverage={}
        for e in r['entries']:
            name=e['entry']
            reference={tuple(row['trace']) for (root,n),row in table.items() if root==name}
            observed={signature(row) for row in e['observations'] if row['outcome']!='unsupported'}
            coverage[name]=dict(observed=len(observed),reference=len(reference),missing=len(reference-observed),
                points=len(e['observations']),status=e['status'])
        modes[mode]=dict(points=len(r['dispatch']),coverage=coverage)
    # Replay only selected full-mode tasks; fixed cap includes every attempted call.
    # The evaluator table is not given to planning/exploration.
    namespace={};filename='<trusted-path-replay>';exec(compile(TEXT,filename,'exec'),namespace)
    dispatch=json.loads((out/'paths.json').read_text())
    replay=[];stopped=False
    by_key={(e['entry'],r['input']):r for e in dispatch['entries'] for r in e['observations']}
    for task in dispatch['dispatch'][:64]:
        row=by_key[task['entry'],task['input']]
        if row['outcome']=='unsupported':
            replay.append(dict(**task,status='unsupported_not_executed'));continue
        actual=namespace[task['entry']]
        try:value=actual(task['input']);outcome='returned'
        except ValueError:value=None;outcome='value_error'
        matches=outcome==row['outcome'] and (outcome!='returned' or value==row['value'].get('value'))
        replay.append(dict(**task,outcome=outcome,value=value,status='agrees' if matches else 'blocked_disagreement'))
        if not matches:stopped=True;break
    if stopped:raise AssertionError('synthetic replay disagreement; no retry')
    if any(modes['paths']['coverage'][name]['missing'] for name in ('hidden','converted','multiple','alternate','permitted','impossible')):
        raise AssertionError('synthetic path qualification failed; do not inspect real modules')
    write(out/'replay.json',dict(records=replay,executed=sum(r['status']=='agrees' for r in replay),
        evaluator_calls=len(table),unexecuted_tasks=max(0,len(dispatch['dispatch'])-len(replay)),stopped=stopped,
        scope='trusted fixture only; evaluator calls separate from <=64 dispatch cap'))
    # Selection rule frozen in docs before outcomes. Never import any selected module.
    stdlib=Path(sysconfig.get_path('stdlib'));selected=[];selection=[]
    for path in sorted(stdlib.glob('*.py')):
        if path.name.startswith('_') or path.stat().st_size>131072:continue
        text=path.read_text()
        try:tree=ast.parse(text)
        except SyntaxError:continue
        exports=[]
        for node in tree.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='__all__' for t in node.targets):
                try:value=ast.literal_eval(node.value)
                except (ValueError,TypeError):continue
                if isinstance(value,(list,tuple)) and all(isinstance(v,str) for v in value):exports=value
        public=[n for n in tree.body if isinstance(n,ast.FunctionDef) and not n.name.startswith('_')]
        eligible=bool(exports) and len(public)>=3
        selection.append(dict(name=path.name,public_functions=len(public),literal_exports=len(exports),eligible=eligible))
        if eligible:selected.append(path)
        if len(selected)==2:break
    if len(selected)!=2:raise ValueError('two eligible local modules unavailable; do not substitute')
    integration=[]
    for path in selected:
        before=hashlib.sha256(path.read_bytes()).hexdigest();text=path.read_text()
        test=stdlib/'test'/f'test_{path.stem}.py'
        tests=test.read_text() if test.is_file() else ''
        r=explore(text,tests,path.stem,window=(0,100))
        write(out/'real'/f'{path.stem}.json',r)
        # Pin exact read-only material, not an executable workspace.
        snapshot=out/'real'/'source-text'/path.name;snapshot.parent.mkdir(parents=True,exist_ok=True);snapshot.write_text(text)
        if tests:(snapshot.parent/test.name).write_text(tests)
        after=hashlib.sha256(path.read_bytes()).hexdigest()
        if before!=after:raise ValueError('real source changed during read-only check')
        inv=r['inventory']['entries'];roots=r['entries']
        examples=[]
        for e in (inv[:1]+inv[-1:]):examples.append(dict(category='public_inventory',record=e))
        for status in ('bounded_complete','partial_unsupported','unsupported','entry_budget_deferred'):
            e=next((e for e in roots if e['status']==status),None)
            if e:examples.append(dict(category=status,record=e))
        unresolved=next((dict(entry=e['name'],**c) for e in inv for c in e['calls'] if c['resolution']=='unresolved'),None)
        if unresolved:examples.append(dict(category='unresolved_call',record=unresolved))
        write(out/'real'/f'{path.stem}-audit-sample.json',examples)
        integration.append(dict(module=path.stem,path=str(path),source_sha256=before,unchanged=before==after,
            tests_path=str(test) if tests else None,tests_status='present' if tests else 'absent',
            entries=len(inv),exact_examples=sum(len(e['evidence']) for e in inv),
            statuses={s:sum(e['status']==s for e in roots) for s in sorted({e['status'] for e in roots})},
            interpreted_points=len(r['dispatch']),subject_executions=0))
    license_path=next((parent/'LICENSE' for parent in stdlib.resolve().parents if (parent/'LICENSE').is_file()),None)
    if license_path:(out/'real'/'PSF-LICENSE.txt').write_bytes(license_path.read_bytes())
    summary=dict(python=sys.version,stdlib=str(stdlib),license_source=str(license_path) if license_path else None,synthetic=modes,replay_calls=sum(r['status']=='agrees' for r in replay),evaluator_calls=len(table),
        integration=integration,selection=selection,model_calls=0,real_subject_executions=0,
        limitations='isolated slices; imported/global context unknown; exact examples only; bounded supported paths; no bug-yield claim')
    write(out/'summary.json',summary)
    write(out/'implementation-sha256.json',{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
        ('scripts/path_exploration.py','scripts/python_facts.py','tests/qualify_path_exploration.py','tests/test_path_exploration.py','docs/experiments/path-exploration-offline-plan.md','examples/path-exploration/subject.py','examples/path-exploration/test_subject.py')})
    write(out/'sha256.json',{str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()})
    return summary


if __name__=='__main__':
    print(json.dumps(run(Path(sys.argv[1])),indent=2))
