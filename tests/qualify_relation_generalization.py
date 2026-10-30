#!/usr/bin/env python3
"""Frozen two-phase static qualification; never load target/test modules."""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import sys
import sysconfig

ROOT=Path(__file__).resolve().parents[1]
IMPLEMENTATION=('scripts/relation_selection.py','scripts/typed_calls.py','scripts/typed_investigation.py','scripts/python_facts.py')
PROTOCOL='docs/experiments/relation-generalization-preregistration.md'


def sha(data):return hashlib.sha256(data).hexdigest()


def write(root,name,value):
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as stream:stream.write(json.dumps(value,indent=2)+'\n')


def text(root,name,value):
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as stream:stream.write(value)


def seal(root):
    write(root,'SHA256.json',{str(p.relative_to(root)):sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()})


def fixtures():
    cases=[]
    families=('positive','negative','reverse','split','sequence','route','nonlinear')
    for family in families:
        h=hashlib.sha256(('e20f548:relation-generalization-v1:'+family).encode()).digest()
        m,t,c=2+h[0]%2,10+h[1]%5,2+h[2]%5
        bound=m*t+c
        if family=='negative':
            a=f'{bound}-({m}*x) <= {c}';b=f'-({m}*size)+{bound} <= {c}'
        elif family=='reverse':a=f'{m}*x+{c} > {bound}';b=f'{bound} < {c}+size*{m}'
        elif family=='nonlinear':a=f'x*x > {t*t}';b=f'size*size > {t*t}'
        else:a=f'{m}*x+{c} > {bound}';b=f'{c}+size*{m} > {bound}'
        body='def f(data):\n    x=len(data)\n    if '+a+':\n        return 0\n    return 0\n'
        changed='def entry(payload, /, *, suffix=b\'\'):\n    size=len(payload)\n    if '+b+':\n        return 0\n    return 0\n'
        extra={}
        if family=='split':
            changed=f'from worker import shifted as renamed\ndef entry(payload, /, *, suffix=b\'\'):\n    if renamed(len(payload)) > {bound}:\n        return 0\n    return 0\n'
            extra={'worker':f'def multiply(q):\n    return q*{m}\ndef shifted(r):\n    return {c}+multiply(r)\n'}
        if family=='sequence':
            body=f'def f(data):\n    if len(data*{m}+b"xx") > {m*t+2}:\n        return 0\n    return 0\n'
            changed=f'def entry(payload, /, *, suffix=b\'\'):\n    enlarged={m}*payload\n    if {m*t+2} < len(b"xx"+enlarged):\n        return 0\n    return 0\n'
        if family=='route':
            body=f'def f(data):\n    x=len(data)\n    if x < {t-2}:\n        if {m}*x+{c} > {bound}:\n            return 0\n    return 0\n'
            changed=f'from worker import guard as moved\ndef entry(payload, /, *, suffix=b\'\'):\n    size=len(payload)\n    if size < {t-2}:\n        return moved(size)\n    return 0\n'
            extra={'worker':f'def guard(q):\n    if {c}+q*{m} > {bound}:\n        return 0\n    return 0\n'}
        test='from subject import f\ndef test_value():\n    assert f(b"B") == 0\n'
        if family in ('negative','split','route'):
            transformed='import unittest as unit\nfrom subject import entry as invoke\nclass TestBoundary(unit.TestCase):\n    def test_value(self):\n        self.assertEqual(invoke(b"B", suffix=b""),0)\n'
        else:
            transformed='from subject import entry as invoke\nclass TestBoundary:\n    def test_value(self):\n        assert invoke(b"B", suffix=b"") == 0\n'
        cases.append(dict(family=family,coefficient=m,pivot=t,offset=c,cap=4,
            canonical=dict(subject=body,test_subject=test),transformed=dict(subject=changed,test_subject=transformed,**extra)))
    return cases


def prepare(out):
    out.mkdir(parents=True,exist_ok=False)
    stdlib=Path(sysconfig.get_path('stdlib'));ledger=[];selected=[]
    for path in sorted(stdlib.glob('*.py')):
        row=dict(name=path.stem,path=str(path));ledger.append(row)
        if path.stem.startswith('_') or path.stem in ('annotationlib','base64'):
            row['status']='excluded';continue
        data=path.read_bytes();row.update(size=len(data),sha256=sha(data))
        if len(data)>131072:row['status']='source_size_budget';continue
        try:tree=ast.parse(data)
        except (SyntaxError,ValueError) as exc:row.update(status='parse_error',error=str(exc));continue
        nodes=sum(1 for _ in ast.walk(tree));row['ast_nodes']=nodes
        if nodes>12000:row['status']='source_ast_budget';continue
        public=[n.name for n in tree.body if isinstance(n,ast.FunctionDef) and not n.name.startswith('_')]
        row['public_functions']=public
        if len(public)<3:row['status']='too_few_public';continue
        row['status']='selected';name=path.stem
        source_file='sources/'+name+'.py.txt';text(out,source_file,data.decode('utf-8'))
        test_path=stdlib/'test'/('test_'+name+'.py');test_file=None
        test_hash=None
        if test_path.is_file():
            raw=test_path.read_bytes();test_file='sources/test_'+name+'.py.txt';text(out,test_file,raw.decode('utf-8'));test_hash=sha(raw)
        selected.append(dict(name=name,source_file=source_file,source_sha256=sha(data),test_file=test_file,test_sha256=test_hash,original_source=str(path),original_test=str(test_path),upstream_git_revision='unknown'))
        if len(selected)==2:break
    write(out,'selection-ledger.json',ledger)
    write(out,'synthetic-inputs.json',fixtures())
    manifest=dict(candidate='e20f548',protocol_sha256=sha((ROOT/PROTOCOL).read_bytes()),driver_sha256=sha(Path(__file__).read_bytes()),
        implementation_sha256={p:sha((ROOT/p).read_bytes()) for p in IMPLEMENTATION},
        python=dict(version=sys.version,implementation=platform.python_implementation(),stdlib=str(stdlib)),
        selected=selected,selection_shortfall=2-len(selected),execution_enabled=False)
    write(out,'manifest.json',manifest)
    license_path=ROOT/'docs/experiments/offline-path-exploration-2026-10-29/real/PSF-LICENSE.txt'
    if license_path.is_file():text(out,'PSF-LICENSE.txt',license_path.read_text())
    else: text(out,'LICENSE-reference.txt','CPython source: PSF License https://docs.python.org/3/license.html\n')
    seal(out)
    print(json.dumps(dict(prepared=str(out),selected=[r['name'] for r in selected],selector_calls=0)))


def independent(case,x):
    # Handwritten arithmetic specification, never parse/eval target expressions.
    m,t,c=case['coefficient'],case['pivot'],case['offset'];family=case['family']
    if family=='negative':return m*t+c-m*x<=c
    if family=='sequence':return m*x+2>m*t+2
    return m*x+c>m*t+c


def normalize(relation,param):
    q=relation['predicate']['quantity'];a=q['terms'][param];b=q['offset'];op=relation['predicate']['operator']
    if a<0:
        a,b=-a,-b;op={'Lt':'Gt','LtE':'GtE','Gt':'Lt','GtE':'LtE','Eq':'Eq','NotEq':'NotEq'}[op]
    return dict(coefficient=a,offset=b,operator=op,cut=relation['cut'],status=relation['searchability'],reachable=relation['reachable_outcomes'],points=relation['points'])


def run(prepared,out):
    out.mkdir(parents=True,exist_ok=False)
    # Any failure leaves this file plus all preceding evidence. No retry loop.
    write(out,'attempt.json',dict(prepared=str(prepared),execution_enabled=False))
    try:
        for name,want in json.loads((prepared/'SHA256.json').read_text()).items():
            if sha((prepared/name).read_bytes())!=want:raise ValueError('prepared hash drift: '+name)
        manifest=json.loads((prepared/'manifest.json').read_text())
        for name,want in manifest['implementation_sha256'].items():
            if sha((ROOT/name).read_bytes())!=want:raise ValueError('implementation drift: '+name)
        if sha(Path(__file__).read_bytes())!=manifest['driver_sha256']:raise ValueError('driver drift')
        if sha((ROOT/PROTOCOL).read_bytes())!=manifest['protocol_sha256']:raise ValueError('protocol drift')
        sys.path.insert(0,str(ROOT/'scripts'))
        from typed_calls import Project, decode
        from typed_investigation import investigate
        from relation_selection import select
        cases=json.loads((prepared/'synthetic-inputs.json').read_text());results=[];counts=Counter();failures=[]
        for case in cases:
            family=case['family'];record=dict(family=family,variants=[])
            if family!='nonlinear':
                domain=list(range(case['pivot']-3,case['pivot']+5))
                truth=[independent(case,x) for x in domain];counts['independent_arithmetic']+=len(domain)
                transitions=[x for i,x in enumerate(domain[1:],1) if truth[i]!=truth[i-1]]
                record.update(domain=domain,independent_truth=truth,independent_transitions=transitions)
            for variant in ('canonical','transformed'):
                p=Project(case[variant]);old=investigate(p,['test_subject'],total_limit=4);new=select(p,['test_subject'],total_limit=4)
                counts['baseline_static']+=len(old['dispatch']);counts['relation_static']+=len(new['dispatch'])
                if counts['baseline_static']>56 or counts['relation_static']>56 or counts['independent_arithmetic']>48:raise ValueError('synthetic cap exceeded')
                write(out,f'synthetic/{family}-{variant}-baseline.json',old);write(out,f'synthetic/{family}-{variant}-relations.json',new)
                row=dict(variant=variant,baseline_dispatch=len(old['dispatch']),relation_dispatch=len(new['dispatch']),issues=new['issues'])
                # The designated consumer is the last recorded predicate in
                # these frozen programs, including reversed comparisons.
                targets=new['relations']
                if family=='nonlinear':
                    row['status']='invariant-but-unsupported' if targets and all(r['searchability']=='unsupported' for r in targets) else 'changed/fail'
                elif not targets or not targets[-1].get('parameter'):
                    row['status']='blocked';row['relations']=new['relations']
                else:
                    rel=targets[-1];param=rel['parameter'];normalized=normalize(rel,param)
                    points=[len(decode(d['task']['values'][param])) for d in new['dispatch']]
                    row.update(normalized=normalized,selected_quantities=points,selected_cut=rel['cut'] in points,
                        baseline_selected_quantities=[len(decode(d['task']['values'][param])) for d in old['dispatch']],call_chain=rel['call_chain'])
                    good=rel['cut'] in transitions
                    if family=='route':good=good and rel['reachable_outcomes']==[False] and not rel['points']
                    else:good=good and row['selected_cut'] and rel['reachable_outcomes']==[False,True]
                    row['status']='invariant/pass' if good else 'changed/fail'
                if any(r['normative_property'] is not None for r in new['relations']):row['status']='changed/fail'
                record['variants'].append(row)
            a,b=record['variants'];invariant=a.get('normalized')==b.get('normalized')
            record['normalized_invariant']=invariant
            record['status']='invariant-but-unsupported' if family=='nonlinear' and a['status']==b['status']=='invariant-but-unsupported' else ('invariant/pass' if invariant and a['status']==b['status']=='invariant/pass' else 'changed/fail')
            if record['status']=='changed/fail':failures.append(family)
            results.append(record)
            write(out,'synthetic/'+family+'-adjudication.json',record)
        real=[]
        for selected in manifest['selected']:
            name=selected['name'];source=(prepared/selected['source_file']).read_text();tree=ast.parse(source)
            public=[n for n in tree.body if isinstance(n,ast.FunctionDef) and not n.name.startswith('_')]
            record=dict(name=name,source_sha256=sha(source.encode()),public_functions=len(public),upstream_git_revision='unknown')
            snapshots={name:source};test_module='test_'+name
            if selected['test_file']:snapshots[test_module]=(prepared/selected['test_file']).read_text()
            record['raw_source_ast']=dict(comparisons=sum(isinstance(n,ast.Compare) for n in ast.walk(tree)),calls=sum(isinstance(n,ast.Call) for n in ast.walk(tree)))
            fallback=False
            try:
                if not selected['test_file']:raise ValueError('sibling test absent')
                p=Project(snapshots)
            except (ValueError,SyntaxError) as exc:
                record.update(paired_status='blocked',paired_error=str(exc));fallback=True;p=Project({name:source})
            test_modules=[] if fallback else [test_module]
            old=investigate(p,test_modules,total_limit=64);new=select(p,test_modules,total_limit=64)
            write(out,'real/'+name+'-baseline.json',old);write(out,'real/'+name+'-relations.json',new)
            evidence=[r for e in new['evidence'] for r in e['records']]
            record.update(mode='source-only inventory fallback' if fallback else 'paired static integration',
                evidence_states=dict(Counter(r['status'] for r in evidence)),exact_obligations=sum(r['status']=='exact_conditional' for r in evidence),
                relations=len(new['relations']),searchable_relations=sum(r['searchability']=='searchable' for r in new['relations']),
                unbound_comparisons=sum(len(e.get('unbound_predicates',[])) for e in new['entries']),
                unbound_calls=sum(len(e.get('unbound_calls',[])) for e in new['entries']),
                baseline_dispatch=len(old['dispatch']),relation_dispatch=len(new['dispatch']),deferred=len(new['deferred']),issues=new['issues'])
            if selected['test_file']:
                tt=ast.parse(snapshots[test_module]);record['raw_test_ast']=dict(nodes=sum(1 for _ in ast.walk(tt)),assertions=sum(isinstance(n,ast.Assert) for n in ast.walk(tt)),classes=sum(isinstance(n,ast.ClassDef) for n in ast.walk(tt)),test_functions=sum(isinstance(n,ast.FunctionDef) and n.name.startswith('test') for n in ast.walk(tt)))
            def segment(n):return dict(name=n.name,line=n.lineno,end=n.end_lineno,source=ast.get_source_segment(source,n))
            audit=dict(first_public=segment(public[0]),last_public=segment(public[-1]),first_exact=next((r for r in evidence if r['status']=='exact_conditional'),None),first_issue=next(iter(new['issues']),None),
                       first_unbound_comparison=next((r for e in new['entries'] for r in e.get('unbound_predicates',[])),None),first_unbound_call=next((r for e in new['entries'] for r in e.get('unbound_calls',[])),None))
            write(out,'real/'+name+'-audit-sample.json',audit)
            record['paired_status']=record.get('paired_status','completed')
            real.append(record);write(out,'real/'+name+'-summary.json',record)
        summary=dict(synthetic_status='fail' if failures else 'pass',synthetic_failures=failures,synthetic=results,counts=dict(counts),real=real,
            real_applicability='not_qualified' if not any(r['searchable_relations'] for r in real) else 'pending_manual_audit',
            actual_subject_calls=0,model_calls=0,selector_unchanged=True,
            scope='fresh synthetic transformations of frozen implementation; real static applicability, not bug recall')
        write(out,'summary.json',summary);seal(out)
        print(json.dumps(summary,indent=2))
    except Exception as exc:
        write(out,'failure.json',dict(type=type(exc).__name__,error=str(exc),retry=False));seal(out);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='phase',required=True)
    p=sub.add_parser('prepare');p.add_argument('out',type=Path)
    p=sub.add_parser('run');p.add_argument('prepared',type=Path);p.add_argument('out',type=Path)
    args=parser.parse_args()
    if args.phase=='prepare':prepare(args.out)
    else:run(args.prepared,args.out)
