#!/usr/bin/env python3
"""Offline investigation scheduler for explicitly trusted synthetic Python modules."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from constraint_plan import intervals, contains, plan, reference
from llm_runner import copy_workspace, tree_digest
from property_search import integer, invoke, read_json, relative_file, run as search
from python_facts import Interpreter, Affine, SubjectRaise, Unsupported, analyze, consumer_bound, module_functions, ranges


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def ref(source, text, node):
    return dict(path=source, start=node.lineno, end=node.end_lineno,
                quote='\n'.join(text.splitlines()[node.lineno-1:node.end_lineno]))


def reachable_functions(functions, entry):
    found, pending = set(), [entry]
    while pending:
        name = pending.pop()
        if name in found:
            continue
        found.add(name)
        pending.extend(n.func.id for n in ast.walk(functions[name]) if isinstance(n, ast.Call)
                       and isinstance(n.func, ast.Name) and n.func.id in functions)
    return found


def observe(functions, entry, consumer, points):
    rows, errors = [], []
    for n in sorted(points):
        engine = Interpreter(functions, consumer, n)
        outcome = 'returned'
        try:
            engine.call(entry, [Affine(1, 0)])
        except SubjectRaise:
            outcome = 'value_error'
        except Unsupported as exc:
            errors.append(dict(input=n, reason=str(exc)))
            outcome = 'unsupported'
        rows.append(dict(input=n, outcome=outcome, consumers=engine.events))
    return rows, errors


def discover(spec, workspace):
    if set(spec)-{'schema_version','source','trusted_source_sha256','entries','slots','point_budget'}:
        raise ValueError('unknown request fields; no labels/declarations/samples accepted')
    source = relative_file(workspace, spec['source'])
    if source.stat().st_size > 131072:
        raise ValueError('source exceeds 128KiB')
    text = source.read_text()
    functions = module_functions(text)
    entries = spec['entries']
    if not isinstance(entries, list) or not 1 <= len(entries) <= 8 or len({e['name'] for e in entries}) != len(entries):
        raise ValueError('expected 1..8 unique entry contracts')
    point_budget = integer(spec.get('point_budget', 32), 4, 64, 'point budget')
    consumers = {name:consumer_bound(f) for name,f in functions.items() if consumer_bound(f) is not None}
    result, audits = [], {}
    for entry in entries:
        if set(entry)!={'name','valid','expectation','evidence'}:
            raise ValueError('entry accepts only name/valid/expectation/evidence')
        name = entry['name']
        if name not in functions:
            raise ValueError('entry unresolved')
        reference(workspace, entry['evidence'])
        if entry['expectation'] not in ('returns', 'return_or_value_error', 'unknown'):
            raise ValueError('unsupported entry expectation')
        valid = intervals(entry['valid'])
        if any(lo < -10000 or hi > 10000 for lo,hi in valid):
            raise ValueError('valid domain outside prototype integer bound')
        scope = reachable_functions(functions, name)
        # No manual suspicious consumer/producer, coefficient, boundary or sample.
        sites = [(caller, node) for caller in sorted(scope) for node in ast.walk(functions[caller])
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                 and node.func.id in consumers]
        if len(sites) > 16:
            raise ValueError('more than16 syntactic consumer sites per entry; no truncation')
        points = {n for lo,hi in valid for n in (lo, hi)}
        points.update(n for n in (-1,0,1) if contains(valid,n))
        # Entry-parameter guards only: internal quantity constants are not treated
        # as public input values. Helper-only hidden branches may remain unobserved.
        parameter = functions[name].args.args[0].arg if len(functions[name].args.args) == 1 else None
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Compare) and not any(isinstance(x,ast.Call) for x in ast.walk(node)):
                names = {x.id for x in ast.walk(node) if isinstance(x,ast.Name)}
                if names == {parameter}:
                    for literal in ast.walk(node):
                        if isinstance(literal,ast.Constant) and type(literal.value) is int:
                            points.update(n for n in (literal.value-1,literal.value,literal.value+1) if contains(valid,n))
        seed_points = sorted(points)
        if len(points)>point_budget:
            audits[name]=dict(status='budget_blocked',points=sorted(points),reason='initial point budget exceeded; no truncation')
            continue
        initial = {}
        for consumer in sorted({node.func.id for _,node in sites}):
            rows, errors = observe(functions,name,consumer,seed_points)
            initial[consumer] = (rows,errors)
            for row in rows:
                for event in row['consumers']:
                    if event['scale']:
                        cut = (consumers[consumer]-event['offset']) // event['scale']
                        points.update(n for n in (cut-1,cut,cut+1,cut+2) if contains(valid,n))
            if len(points)>point_budget:
                break
        if len(points) > point_budget:
            audits[name] = dict(status='budget_blocked', points=sorted(points), reason='no silent point truncation')
            continue
        if not sites:
            audits[name] = dict(status='unsupported',reason='no recognized consumer relation; entry not qualified')
            continue
        # Freeze the enlarged set before second-pass facts and declaration checks.
        points = sorted(points)
        audits[name] = dict(status='analyzed', seed_points=seed_points, checked_points=points, consumers={})
        rows_by_consumer = {}
        for consumer in sorted(initial):
            rows,errors = observe(functions,name,consumer,points)
            rows_by_consumer[consumer] = (rows,errors)
            audits[name]['consumers'][consumer] = dict(observations=rows,errors=errors)
        for caller,node in sites:
            consumer = node.func.id
            rid = hashlib.sha256(f'{name}:{caller}:{node.lineno}:{consumer}'.encode()).hexdigest()[:16]
            item = dict(id=rid, entry=name, consumer=consumer, caller=caller, line=node.lineno,
                        contract=entry, expectation=entry['expectation'], points=points,
                        source=spec['source'], source_evidence=ref(spec['source'],text,node))
            result.append(item)
            rows,errors = rows_by_consumer[consumer]
            if errors:
                item.update(status='unsupported',reason='partial facts never qualify',errors=errors)
                continue
            events = [(r,e) for r in rows for e in r['consumers'] if e['line']==node.lineno]
            models = {(e['scale'],e['offset'],e['unit']) for _,e in events}
            if not events:
                item.update(status='deferred',reason='not observed on checked points; not globally unreachable')
                continue
            if len(models)!=1 or next(iter(models))[0] is None:
                item.update(status='deferred',reason='multiple/unknown quantity models')
                continue
            a,b,unit = next(iter(models))
            reached = ranges(r['input'] for r,e in events)
            declaration = dict(scale=a,offset=b,output_unit=unit,bound=consumers[consumer],route=reached)
            audit = analyze(dict(schema_version=1,source=spec['source'],entry=name,consumer=consumer,
                                 analysis_points=points,declaration=declaration),workspace)
            item['fact_check'] = audit
            # Existing audit checks all call sites to this consumer. If those have
            # different variants it conservatively refuses this site too.
            if audit['status']=='unsupported' or any(audit.get('checks',{}).get(k,{}).get('status')!='matched_in_scope'
                    for k in ('scale','offset','output_unit','route','bound')):
                item.update(status='deferred',reason='required representation/model/route fact not matched')
                continue
            if entry['expectation']!='returns':
                item.update(status='deferred',reason='no distinguishing must-return oracle')
                continue
            if len(reached)>8:
                item.update(status='budget_blocked',reason='too many observed intervals')
                continue
            relation = dict(id=rid,contract=dict(source=entry['evidence'],status='supported',
                obligation='consumer_precondition',claims=[dict(effect='allow',scope=entry['valid'],source=entry['evidence'])]),
                input=dict(source=ref(spec['source'],text,functions[name]),unit='input_integer',valid=entry['valid']),
                producer=dict(source=ref(spec['source'],text,functions[caller]),kind='integer_affine',
                    input_unit='input_integer',output_unit=unit,scale=a,offset=b),
                consumer=dict(source=ref(spec['source'],text,functions[consumer]),unit=unit,operator='<=',bound=consumers[consumer]),
                route=dict(source=ref(spec['source'],text,node),guard=reached))
            # Planner models a structural investigation lead, NOT an independent
            # behavioral oracle. The executable oracle remains entry must-return.
            planned = plan(dict(schema_version=1,search_slots=1,max_domain_points=point_budget,relations=[relation]),workspace)['relations'][0]
            item['domain_plan'] = planned
            if planned['status']=='ready':
                model=planned['model']
                bridge=analyze(dict(schema_version=1,source=spec['source'],entry=name,consumer=consumer,
                    analysis_points=points,declaration=dict(scale=model['scale'],offset=model['offset'],
                    output_unit=model['output_unit'],bound=model['bound'],route=planned['reachable_intervals'])),workspace)
                item['bridge_check']=bridge
                if any(bridge.get('checks',{}).get(k,{}).get('status')!='matched_in_scope'
                       for k in ('scale','offset','output_unit','route','bound')):
                    item.update(status='deferred',reason='planner-to-source declaration mismatch or unknown')
                    continue
            item['lead_not_oracle'] = 'consumer precondition is implementation evidence; outcome oracle is independent entry contract'
            failures = [r['input'] for r in rows if r['outcome']=='value_error' and r['consumers']]
            if planned['status']!='ready':
                item.update(status='deferred',reason=planned.get('reason','domain plan unsupported'))
            elif not failures:
                item.update(status='deferred',reason='no predicted contract-distinguishing outcome on checked points')
            else:
                control = next((r['input'] for r in rows if r['outcome']=='returned'),None)
                domain = sorted(set(planned['domain']) | {failures[0]} | ({control} if control is not None else set()))
                if not set(domain)<=set(points) or not all(contains(valid,n) for n in domain):
                    item.update(status='deferred',reason='planner domain not source-checked/contract-valid')
                    continue
                if len(domain)>32:
                    item.update(status='budget_blocked',reason='execution domain exceeds32; no silent truncation')
                    continue
                item.update(status='ready',mode='search' if control is not None else 'direct',control=control,domain=domain,
                            reason='supported entry obligation + source-derived distinguishing outcome')
        # Valid-input rejection before any recognized consumer is an entry-level
        # relationship, not silently reclassified as invalid public input.
        baseline_rows,errors = next(iter(rows_by_consumer.values()))
        if not errors and entry['expectation']=='returns':
            rejects = [r['input'] for r in baseline_rows if r['outcome']=='value_error' and not r['consumers']]
            if rejects:
                control = next((r['input'] for r in baseline_rows if r['outcome']=='returned'),None)
                result.append(dict(id=hashlib.sha256((name+':entry-exit').encode()).hexdigest()[:16],entry=name,
                    consumer=next(iter(rows_by_consumer)),source=spec['source'],contract=entry,expectation='returns',
                    status='ready',mode='search' if control is not None else 'direct',control=control,
                    domain=sorted(set(rejects[:1]+([control] if control is not None else []))),
                    fact_gate='supported AST outcomes on checked points; no affine model required for entry outcome',
                    reason='contract-valid input predicted to reject before selected consumer; no causal attribution'))
    return result,audits


def run(spec, workspace, out, execute=False):
    workspace,out = Path(workspace).resolve(),Path(out).resolve()
    if out.is_relative_to(workspace) or workspace.is_relative_to(out):
        raise ValueError('output and source must be separate trees')
    if out.exists():
        raise ValueError('output exists')
    if spec.get('schema_version')!=1:
        raise ValueError('expected schema_version1')
    source = relative_file(workspace,spec['source'])
    if hashlib.sha256(source.read_bytes()).hexdigest()!=spec['trusted_source_sha256']:
        raise ValueError('source hash drift')
    before = tree_digest(workspace)
    try:
        relations,audits = discover(spec,workspace)
    except (Unsupported,SyntaxError) as exc:
        relations,audits = [],dict(module=dict(status='unsupported',reason=str(exc)))
    slots = integer(spec.get('slots',2),1,4,'execution slots')
    ready = sorted((r for r in relations if r['status']=='ready'),key=lambda r:(len(r['domain']),r['id']))
    selected,seen = [],set()
    for r in ready:
        if r['entry'] not in seen and len(selected)<slots:
            selected.append(r);seen.add(r['entry'])
    for r in relations:
        r['selection'] = 'selected' if r in selected else 'same_entry_deferred' if r['status']=='ready' and r['entry'] in seen else 'budget_deferred' if r['status']=='ready' else r['status']
    out.mkdir(parents=True)
    write(out/'request.json',spec)
    copy_workspace(workspace,out/'source-snapshot')
    write(out/'implementation-sha256.json',{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ('investigation.py','investigation_adapter.py','python_facts.py','constraint_plan.py','property_search.py','llm_runner.py')})
    write(out/'relations.json',relations)
    write(out/'facts.json',audits)
    evidence=[]
    for r in selected:
        if not execute:
            evidence.append(dict(id=r['id'],status='planned_only'));continue
        if tree_digest(workspace)!=before:
            raise ValueError('source drift before dispatch')
        folder=out/'executions'/r['id'];folder.mkdir(parents=True)
        shutil.copy2(Path(__file__).with_name('investigation_adapter.py'),folder/'adapter.py')
        expected={str(row['input']):dict(outcome=row['outcome'],consumers=[dict(unit=e['unit'],quantity=e['quantity']) for e in row['consumers']])
                  for row in audits[r['entry']]['consumers'][r['consumer']]['observations']}
        write(folder/'execution.json',dict(source=spec['source'],source_sha256=spec['trusted_source_sha256'],
            entry=r['entry'],consumer=r['consumer'],expectation=r['expectation'],fact_observations=expected))
        if r['mode']=='search':
            search_spec=dict(schema_version=1,id=r['id'],claim='Contract-valid entry input must return normally',
                domain='Finite source-derived and fact-checked integer points',observation='actual entry outcome',
                violation='ValueError contrary to independently sourced must-return contract',contract=[r['contract']['evidence']],
                adapter=dict(files=['adapter.py','execution.json'],argv=['{python}','{adapter_dir}/adapter.py']),
                domains=dict(n=r['domain']),control=dict(n=r['control']),seed=0,
                limits=dict(max_cases=min(32,len(r['domain'])+4),seconds=10,case_seconds=1,shrink_cases=4))
            write(folder/'property.json',search_spec)
            try:
                summary=search(folder/'property.json',workspace,folder/'search')
            except (ValueError,OSError,KeyError,TypeError) as exc:
                write(folder/'failure.json',dict(status='blocked',reason=str(exc)))
                evidence.append(dict(id=r['id'],mode='search',status='blocked',evaluations=None))
                break
            evidence.append(dict(id=r['id'],mode='search',status=summary['status'],evaluations=summary['evaluations']))
            if summary['status'] in ('blocked','incomplete','integrity_failure','control_failed'):
                break
        else:
            with tempfile.TemporaryDirectory(prefix='ll-investigation-') as temp:
                work=Path(temp)/'workspace';copy_workspace(workspace,work);digest=tree_digest(work)
                observation=invoke([sys.executable,str(folder/'adapter.py')],dict(n=r['domain'][0]),work,
                    dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),1,4096,folder/'direct')
                unchanged=tree_digest(work)==digest
                if not unchanged:observation=dict(status='blocked',reason='executed source mutation')
            write(folder/'direct-result.json',observation)
            evidence.append(dict(id=r['id'],mode='direct',status=observation['status'],evaluations=1))
            if observation['status']=='blocked':break
    unchanged=tree_digest(workspace)==before
    stopped=any(e['status'] in ('blocked','incomplete','integrity_failure','control_failed') for e in evidence)
    status='integrity_failure' if not unchanged else 'stopped' if stopped else 'unsupported' if 'module' in audits else 'complete'
    report=dict(schema_version=1,status=status,relations_discovered=len(relations),
        ready_relations=sum(r['status']=='ready' for r in relations),execution_enabled=execute,source_before=before,
        source_after=tree_digest(workspace),selected=[r['id'] for r in selected],executions=evidence,
        unexecuted_selected=[r['id'] for r in selected if r['id'] not in {e['id'] for e in evidence}],
        scope='trusted synthetic only; source leads are not bug oracles; finite checked points only',
        limits='one selected relation per entry, then smaller domain/stable ID; not semantic novelty or bug-yield ranking')
    write(out/'summary.json',report)
    write(out/'sha256.json',{str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()})
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--spec',type=Path,required=True)
    p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--execute-trusted-synthetic',action='store_true')
    a=p.parse_args()
    try:r=run(read_json(a.spec.read_text()),a.workspace,a.out,a.execute_trusted_synthetic)
    except (ValueError,KeyError,TypeError,OSError,RecursionError) as exc:p.exit(2,f'error: {exc}\n')
    print(json.dumps(dict(status=r['status'],selected=r['selected'],evidence=str(a.out.resolve()))))


if __name__=='__main__':main()
