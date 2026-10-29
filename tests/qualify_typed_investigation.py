#!/usr/bin/env python3
"""Only reviewed hashed synthetic fixtures may be executed; no real-module stage."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from python_facts import Unsupported
from typed_calls import Project, bind, decode, encode
from typed_investigation import investigate, observe

FIXTURES=ROOT/'examples/typed-investigation'


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n')


class Budget:
    def __init__(self,out):self.out=out;self.counts=dict(dispatch=0,evaluator=0)
    def spend(self,kind,case):
        cap=dict(dispatch=64,evaluator=128)[kind]
        if self.counts[kind]>=cap:raise RuntimeError('execution budget exhausted: '+kind)
        self.counts[kind]+=1
        with (self.out/'attempts.jsonl').open('a') as file:
            file.write(json.dumps(dict(event='attempt',kind=kind,index=self.counts[kind],case=case))+'\n')
        write(self.out/'counters.json',dict(counts=self.counts,limits=dict(dispatch=64,evaluator=128)))


def trusted():
    expected=json.loads((FIXTURES/'trusted-sha256.json').read_text())
    actual={str(p.relative_to(FIXTURES)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(FIXTURES.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='trusted-sha256.json'}
    if actual!=expected:raise RuntimeError('trusted synthetic fixture hash drift')


@contextmanager
def fixture_modules(path,project):
    names=set(project.sources)
    names.update('.'.join(m.split('.')[:n]) for m in project.sources for n in range(1,len(m.split('.'))))
    previous={name:sys.modules[name] for name in names if name in sys.modules}
    for name in names:sys.modules.pop(name,None)
    sys.path.insert(0,str(path));old_bytecode=sys.dont_write_bytecode;sys.dont_write_bytecode=True
    try:yield
    finally:
        sys.dont_write_bytecode=old_bytecode;sys.path.pop(0)
        for name in names:sys.modules.pop(name,None)
        sys.modules.update(previous)


def actual(function,args,kwargs,project):
    calls=[];previous=sys.gettrace()
    def trace(frame,event,arg):
        module=frame.f_globals.get('__name__')
        if event=='call' and module in project.sources:
            names=frame.f_code.co_varnames[:frame.f_code.co_argcount+frame.f_code.co_kwonlyargcount]
            calls.append(dict(module=module,name=frame.f_code.co_name,values={name:encode(frame.f_locals[name]) for name in names}))
        return trace
    sys.settrace(trace)
    value=None;outcome='returned'
    try:value=function(*args,**dict(kwargs))
    except ValueError:outcome='value_error'
    finally:sys.settrace(previous)
    return dict(outcome=outcome,value=encode(value),calls=calls)


def compare(observation,actual_result):
    if observation['outcome']!=actual_result['outcome'] or observation['value']!=actual_result['value']:raise AssertionError('actual/static outcome/value disagreement')
    calls=[dict(module=c['target']['module'],name=c['target']['name'],values=c['binding']['values']) for c in observation['calls']]
    if calls!=actual_result['calls']:raise AssertionError('actual/static call argument disagreement')


def explicit_args(project,target,values):
    f=project.function(target)
    return ([decode(values[a.arg]) for a in f.args.posonlyargs+f.args.args],[(a.arg,decode(values[a.arg])) for a in f.args.kwonlyargs])


def run(out,execute=False):
    if out.exists() or out.resolve().is_relative_to(FIXTURES.resolve()):raise ValueError('new output outside source required')
    out.mkdir(parents=True);budget=Budget(out);status='planning_only';dispatch_results=[];evaluator_results=[];binding_results=[];failure=None
    projects={};plans={};static_used=0
    try:
        trusted();portfolio=json.loads((FIXTURES/'portfolio.json').read_text())
        for name in portfolio['projects']:
            project=Project.directory(FIXTURES/name);projects[name]=project
            # Frozen static budgets; no result-driven budget changes/case substitutions.
            plan=investigate(project,['test_subject'],total_limit=min(8,64-static_used),point_limit=8)
            static_used+=len(plan['dispatch']);plans[name]=plan;write(out/'plans'/f'{name}.json',plan)
        shutil.copytree(FIXTURES,out/'source-text',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        write(out/'implementation-sha256.json',{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
            ('scripts/typed_calls.py','scripts/typed_investigation.py','scripts/path_exploration.py','tests/qualify_typed_investigation.py','tests/test_typed_investigation.py','docs/experiments/typed-calls-offline-plan.md')})
        if execute:
            status='complete'
            for name,plan in plans.items():
                project=projects[name]
                with fixture_modules(FIXTURES/name,project):
                    for index,row in enumerate(plan['dispatch']):
                        label=dict(project=name,index=index)
                        if row['outcome']=='unsupported':
                            dispatch_results.append(dict(**label,status='unsupported_not_executed'));continue
                        trusted();target=row['target'];fn=getattr(importlib.import_module(target['module']),target['name'])
                        args,kwargs=explicit_args(project,target,row['task']['values'])
                        if row['task']['queue']=='verify':
                            ev=next(r for e in plan['evidence'] for r in e['records'] if r['source']==row['task']['evidence_source'] and r['status']=='exact_conditional')
                            args=[decode(v) for v in ev['arguments']['args']];kwargs=[(k['name'],decode(k['value'])) for k in ev['arguments']['keywords']]
                        bound=inspect.signature(fn).bind(*args,**dict(kwargs));bound.apply_defaults()
                        if {k:encode(v) for k,v in bound.arguments.items()}!=row['task']['values']:raise AssertionError('Python parameter binding disagreement')
                        budget.spend('dispatch',label);result=actual(fn,args,kwargs,project);compare(row,result)
                        dispatch_results.append(dict(**label,status='agrees',result=result))
                        write(out/'dispatch-results.json',dispatch_results)
            # Independent finite universe, fixed before model outputs; no labels fed back.
            universe=[('01-bytes-default','subject','attach',b'A',{}),
                ('02-unittest-binding','subject','attach',b'A',dict(enabled=True)),
                ('02-unittest-binding','subject','attach',b'A',dict(enabled=False)),
                ('03-allowed-refusal','subject','check',b'A',{}),
                ('04-relative-source','pkg.api','attach',b'A',{}),
                ('05-reexport-source','backend','attach',b'A',dict(suffix=b'?')),
                ('12-equal-length-content','subject','classify',b'A',{}),
                ('12-equal-length-content','subject','classify',b'B',{})]
            for name,module,function,fill,kw in universe:
                project=projects[name];target=project.symbol(module,[function])
                with fixture_modules(FIXTURES/name,project):
                    fn=getattr(importlib.import_module(module),function)
                    for length in range(9):
                        args=[fill*length];kwargs=list(kw.items());values=bind(project.function(target),args,kwargs)['values']
                        prediction=observe(project,target,values)
                        if prediction['outcome']=='unsupported':raise AssertionError('independent evaluator model unsupported')
                        trusted();label=dict(project=name,module=module,function=function,length=length,fill=encode(fill),keywords={k:encode(v) for k,v in kw.items()})
                        budget.spend('evaluator',label);result=actual(fn,args,kwargs,project);compare(prediction,result)
                        evaluator_results.append(dict(case=label,status='agrees',result=result));write(out/'evaluator-results.json',evaluator_results)
            name='02-unittest-binding';project=projects[name];target=project.symbol('subject',['attach']);f=project.function(target)
            cases=[([b'A'],[]),([b'A',b'!'],[]),([b'A'],[('enabled',False)]),([b'A'],[('marker',None)]),
                ([],[]),([],[('data',b'A')]),([b'A',b'!'],[('suffix',b'?')]),([b'A'],[('unknown',1)]),
                ([b'A',b'!',b'extra'],[]),([b'A'],[('marker',b'bad')])]
            with fixture_modules(FIXTURES/name,project):
                fn=getattr(importlib.import_module('subject'),'attach')
                for index,(args,kwargs) in enumerate(cases):
                    error=False;prediction=None
                    try:binding=bind(f,args,kwargs);prediction=observe(project,target,binding['values'])
                    except ValueError:error=True
                    trusted();budget.spend('evaluator',dict(kind='binding',index=index))
                    try:result=actual(fn,args,kwargs,project)
                    except TypeError:
                        if not error:raise
                        result=dict(outcome='python_binding_error')
                    else:
                        if error:raise AssertionError('Python accepted statically rejected binding')
                        compare(prediction,result)
                    binding_results.append(dict(index=index,status='agrees',result=result));write(out/'binding-results.json',binding_results)
    except Exception as exc:
        status='stopped';failure=dict(type=type(exc).__name__,reason=str(exc));write(out/'failure.json',failure)
    finally:
        summary=dict(status=status,model_calls=0,real_subject_executions=0,static_tasks=static_used,
            actual_attempts=budget.counts,limits=dict(dispatch=64,evaluator=128),dispatch_agreements=sum(r['status']=='agrees' for r in dispatch_results),
            dispatch_unsupported=sum(r['status']=='unsupported_not_executed' for r in dispatch_results),
            independent_universe_agreements=len(evaluator_results),binding_agreements=len(binding_results),failure=failure,
            undispatched_static_tasks=static_used-len(dispatch_results),
            entry_evidence={name:{status:sum(r['status']==status for e in plan['evidence'] for r in e['records']) for status in sorted({r['status'] for e in plan['evidence'] for r in e['records']})} for name,plan in plans.items()},
            scope='one bounded trusted-synthetic diagnostic; regression tests separate; no real modules selected or run; no retries')
        write(out/'summary.json',summary)
        write(out/'sha256.json',{str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()})
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('out',type=Path);parser.add_argument('--execute-trusted-synthetic',action='store_true');args=parser.parse_args()
    result=run(args.out,args.execute_trusted_synthetic);print(json.dumps(result,indent=2));sys.exit(1 if result['status']=='stopped' else 0)
