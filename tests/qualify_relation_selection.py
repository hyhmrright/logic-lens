#!/usr/bin/env python3
"""One-shot static qualification. Never imports/executes synthetic subjects.

Independent arithmetic checks are evaluator-only and do not feed the selector.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from typed_calls import Project, decode
from typed_investigation import investigate
from relation_selection import select


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if len(sys.argv)!=2:raise SystemExit('usage: qualify_relation_selection.py NEW_OUTPUT_DIRECTORY')
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    portfolio=ROOT/'examples/relation-selection/portfolio.json'
    labels=json.loads(portfolio.read_text())
    plan=dict(portfolio_sha256=digest(portfolio),execution_enabled=False,static_cap_per_arm=64,independent_arithmetic_cap=128,
              actual_scheduler_calls=0,actual_independent_subject_calls=0,
              implementation_sha256={p:digest(ROOT/p) for p in ('scripts/relation_selection.py','scripts/typed_calls.py','scripts/typed_investigation.py','tests/qualify_relation_selection.py')})
    def write(name,value):(out/name).write_text(json.dumps(value,indent=2)+'\n')
    write('plan.json',plan)
    cases=[]
    def add(name,body,call="f(b'A')",extra=None,cap=4):
        sources=dict(subject=body,test_subject='from subject import f\ndef test_f():\n    assert '+call+' == 0\n',**(extra or {}))
        cases.append((name,sources,cap))
    for label in labels['development'][:3]:
        add(label['family'],f"def f(data):\n    x=len(data)\n    if {label['expression']} {label['operator']} {label['bound']}:\n        return 0\n    return 0\n")
    add('nested','def helper(n):\n    return 2*(n+3)\ndef f(data):\n    if helper(len(data))>32:\n        return 0\n    return 0\n')
    add('impossible','def f(data):\n    x=len(data)\n    if x<5:\n        if 3*x>30:\n            return 0\n    return 0\n')
    body='def f(a,b,c,d,e):\n'
    for i,name in enumerate('abcde'):body+=f'    if len({name}) > {10+i}:\n        return 0\n'
    body+='    return 0\n'
    add('competition',body,"f(b'A',b'A',b'A',b'A',b'A')",cap=6)
    add('units','def f(data,n=2):\n    if len(data)+n>30:\n        return 0\n    return 0\n',cap=2)
    add('nonlinear','def f(data):\n    x=len(data)\n    if x*x>30:\n        return 0\n    return 0\n',cap=2)
    add('outside','def f(data):\n    if len(data)>100000:\n        return 0\n    return 0\n',cap=2)
    add('oracle','def f(data):\n    if len(data)>18:\n        return 0\n    return 0\n')
    # This transformation subset is inspected only after selector implementation.
    # No tuning after a failed result; any such change invalidates this holdout.
    held=labels['held_out_transformations']['constants']
    extra={'worker':f"def shifted(q):\n    return {held['offset']}+q*{held['scale']}\n"}
    add('held_out','from worker import shifted as moved\ndef f(renamed):\n    if moved(len(renamed))>'+str(held['bound'])+':\n        return 0\n    return 0\n',extra=extra)
    write('frozen-inputs.json',dict(cases=[dict(name=n,sources=s,cap=c) for n,s,c in cases],untested={'subject':'def public(data):\n    if len(data)>12:\n        return 0\n    return 0\n'}))
    baseline_count=selected_count=arithmetic_count=0;records=[];failures=[]
    # Separately authored brute predicates. No parser, selector inverse, cut label
    # or interval implementation is used by this finite-domain evaluator.
    predicates={'scale':lambda x:3*x>30,'shift':lambda x:2*x+5>=31,'negative':lambda x:40-2*x<10,
                'nested':lambda x:2*(x+3)>32,'held_out':lambda x:4*x+7>59}
    for name,sources,cap in cases:
        project=Project(sources)
        old=investigate(project,['test_subject'],total_limit=cap)
        new=select(project,['test_subject'],total_limit=cap)
        baseline_count+=len(old['dispatch']);selected_count+=len(new['dispatch'])
        if max(baseline_count,selected_count)>64:raise RuntimeError('static arm budget exceeded')
        write(name+'-baseline.json',old);write(name+'-relations.json',new)
        record=dict(family=name,baseline_dispatch=len(old['dispatch']),relation_dispatch=len(new['dispatch']),relations=len(new['relations']),normative_properties=0)
        if name in predicates:
            truth=[]
            for x in range(25):
                if arithmetic_count>=128:raise RuntimeError('independent arithmetic budget exceeded')
                arithmetic_count+=1;truth.append(predicates[name](x))
            cuts=[x for x in range(1,25) if truth[x]!=truth[x-1]]
            r=new['relations'][0];param=r['parameter']
            points=[len(decode(d['task']['values'][param])) for d in new['dispatch']]
            oldpoints=[len(decode(d['task']['values'][param])) for d in old['dispatch']]
            record.update(independent_truth=truth,independent_cuts=cuts,selected_points=points,baseline_points=oldpoints,
                          cut_agrees=r['cut'] in cuts,cut_selected=r['cut'] in points,baseline_cut_selected=r['cut'] in oldpoints)
            if not record['cut_agrees'] or not record['cut_selected']:failures.append(name)
        elif name=='impossible':
            if new['relations'][1]['reachable_outcomes']!=[False]:failures.append(name)
        elif name=='competition':
            served={r['parameter'] for r in new['relations'] if any(r['id'] in d['task']['relations'] for d in new['dispatch'])}
            record['served_parameters']=sorted(served)
            if served!=set('abcde'):failures.append(name)
        elif name in ('units','nonlinear'):
            if new['relations'][0]['searchability']!='unsupported':failures.append(name)
        elif name=='outside':
            if new['relations'][0]['points'] or new['relations'][0]['searchability']!='out_of_budget':failures.append(name)
        if any(r['normative_property'] is not None for r in new['relations']):failures.append(name+':invented oracle')
        records.append(record)
    untested=select(Project({'subject':'def public(data):\n    if len(data)>12:\n        return 0\n    return 0\n'}))
    write('untested-relations.json',untested)
    if untested['dispatch'] or not untested['entries'][0]['unbound_predicates']:failures.append('untested')
    summary=dict(status='pass' if not failures else 'fail',failures=failures,cases=records,baseline_static_dispatch=baseline_count,
                 relation_static_dispatch=selected_count,static_cap_per_arm=64,independent_arithmetic_evaluations=arithmetic_count,
                 actual_scheduler_calls=0,actual_independent_subject_calls=0,model_calls=0,
                 held_out_valid=False,held_out_note='Transformation inspected in initial batch before accounting fix; final replay is regression-only, not a fresh holdout.',
                 scope='synthetic selection mechanism only; no real bug-recall result')
    write('summary.json',summary)
    write('SHA256.json',{p.name:digest(p) for p in sorted(out.iterdir()) if p.is_file()})
    print(json.dumps(summary,indent=2))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
