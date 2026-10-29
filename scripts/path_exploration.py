#!/usr/bin/env python3
"""Experimental static entry/evidence inventory and bounded cross-call path explorer.

Never imports or executes the subject. Investigation windows are not valid-input
contracts. Exact test evidence is conditional on the original test environment.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys

from python_facts import Affine, Interpreter, Sequence, SubjectRaise, Unsupported, module_functions
from property_search import integer


def location(node):
    return dict(line=node.lineno, end=node.end_lineno)


def literal_int(node):
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None
    return value if type(value) is int else None


def inventory(text, tests='', module='subject'):
    tree = ast.parse(text)
    if len(text.encode()) > 131072 or sum(1 for _ in ast.walk(tree)) > 12000:
        raise ValueError('source size/AST budget exceeded')
    functions = {n.name:n for n in tree.body if isinstance(n, ast.FunctionDef)}
    duplicates = len(functions) != sum(isinstance(n, ast.FunctionDef) for n in tree.body)
    exports, unknown = set(), []
    initialization = [dict(**location(n),kind=type(n).__name__) for n in tree.body if not isinstance(n,(ast.FunctionDef,ast.Import,ast.ImportFrom)) and not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str))]
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id=='__all__' for t in n.targets):
            try:
                value = ast.literal_eval(n.value)
                if not isinstance(value, (list, tuple)) or not all(isinstance(x,str) for x in value):
                    raise ValueError()
                exports.update(value)
            except (ValueError, TypeError):
                unknown.append(dict(**location(n), reason='dynamic exports'))
    entries = {name:dict(name=name, **location(f), sources=['public_definition'] if not name.startswith('_') else [],
                         evidence=[], calls=[]) for name,f in functions.items()}
    for name in sorted(exports):
        if name in entries:
            entries[name]['sources'].append('literal_export')
        else:
            unknown.append(dict(name=name, reason='export not a local function'))
    for name,f in functions.items():
        for n in ast.walk(f):
            if isinstance(n, ast.Call):
                target = n.func.id if isinstance(n.func,ast.Name) else None
                entries[name]['calls'].append(dict(**location(n), expression=ast.unparse(n.func),
                    target=target, resolution='local' if target in functions else 'builtin' if target in ('len','type','ValueError') else 'unresolved'))
    if tests:
        if len(tests.encode()) > 131072:
            raise ValueError('test source size budget exceeded')
        test_tree=ast.parse(tests)
        if sum(1 for _ in ast.walk(test_tree)) > 12000:raise ValueError('test AST budget exceeded')
        aliases, modules = {}, set()
        for n in test_tree.body:
            if isinstance(n,ast.ImportFrom) and n.level==0 and n.module==module:
                aliases.update({a.asname or a.name:a.name for a in n.names if a.name in entries})
            if isinstance(n,ast.Import):
                modules.update(a.asname or a.name for a in n.names if a.name==module)
        bindings={}
        for n in test_tree.body:
            names=[]
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):names=[n.name]
            elif isinstance(n,(ast.Import,ast.ImportFrom)):names=[a.asname or a.name.split('.')[0] for a in n.names]
            for name in names:bindings[name]=bindings.get(name,0)+1
        shadowed={name for name,count in bindings.items() if count>1}
        shadowed.update(n.name for n in test_tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)))
        shadowed.update(n.id for n in ast.walk(test_tree) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store))
        shadowed.update(a.arg for n in ast.walk(test_tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.Lambda)) for a in n.args.args)
        aliases={k:v for k,v in aliases.items() if k not in shadowed}
        modules-=shadowed
        def target(call):
            if not isinstance(call,ast.Call) or call.keywords or len(call.args)!=1:
                return None
            f=call.func
            if isinstance(f,ast.Name):return aliases.get(f.id)
            if isinstance(f,ast.Attribute) and isinstance(f.value,ast.Name) and f.value.id in modules and f.attr in entries:return f.attr
            return None
        def record(call, outcome, expected, context):
            name=target(call)
            if name is None:return
            entry=entries[name]
            if 'test_call' not in entry['sources']:entry['sources'].append('test_call')
            n=literal_int(call.args[0])
            if n is None:
                unknown.append(dict(**location(call), reason='test input not a literal integer', entry=name));return
            entry['evidence'].append(dict(input=n,outcome=outcome,expected=expected,**location(call),
                context=context,scope='exact example only; conditional on test environment'))
        for f in test_tree.body:
            if not isinstance(f,ast.FunctionDef) or not f.name.startswith('test_'):continue
            simple = not f.decorator_list and not f.args.args and not f.args.defaults
            simple = simple and all(isinstance(n,(ast.Assert,ast.Expr,ast.With)) for n in f.body)
            if not simple:
                unknown.append(dict(**location(f),reason='test fixture/setup/decorator context unresolved'));continue
            for n in f.body:
                if isinstance(n,ast.Assert) and isinstance(n.test,ast.Compare) and len(n.test.ops)==1 and isinstance(n.test.ops[0],ast.Eq):
                    expected=literal_int(n.test.comparators[0])
                    if expected is not None:record(n.test.left,'returned',expected,f.name)
                elif isinstance(n,ast.Expr):record(n.value,'returned',None,f.name)
                elif isinstance(n,ast.With):
                    # Only syntax evidence: ownership/environment of raises is not proven.
                    c=n.items[0].context_expr if len(n.items)==1 else None
                    if (isinstance(c,ast.Call) and isinstance(c.func,ast.Attribute) and c.func.attr=='raises'
                        and len(c.args)==1 and isinstance(c.args[0],ast.Name) and c.args[0].id=='ValueError'
                        and len(n.body)==1 and isinstance(n.body[0],ast.Expr)):
                        record(n.body[0].value,'value_error',None,f.name)
                    else:unknown.append(dict(**location(n),reason='exception context unresolved'))
        captured={ev['line'] for e in entries.values() for ev in e['evidence']}
        for node in ast.walk(test_tree):
            if isinstance(node,ast.Call) and node.lineno not in captured:
                f=node.func
                name=aliases.get(f.id) if isinstance(f,ast.Name) else f.attr if isinstance(f,ast.Attribute) and isinstance(f.value,ast.Name) and f.value.id in modules and f.attr in entries else None
                if name:unknown.append(dict(**location(node),entry=name,reason='call lacks extractable exact test obligation'))
    for e in entries.values():
        by_input={}
        for ev in e['evidence']:
            by_input.setdefault(ev['input'],set()).add((ev['outcome'],ev['expected']))
        # A plain-return observation is compatible with an exact return assertion.
        e['conflicts']=[n for n,values in by_input.items() if len({o for o,v in values})>1 or len({v for o,v in values if v is not None})>1]
    return dict(entries=[e for e in entries.values() if e['sources']], internal_functions=[name for name,e in entries.items() if not e['sources']],
                unknown=unknown, duplicate_definitions=duplicates, unmodeled_initialization=initialization), functions


OPS={'Lt':lambda a,b:a<b,'LtE':lambda a,b:a<=b,'Gt':lambda a,b:a>b,'GtE':lambda a,b:a>=b,'Eq':lambda a,b:a==b,'NotEq':lambda a,b:a!=b}


def predicate(p,n):
    return OPS[p['op']](p['left'][0]*n+p['left'][1],p['right'][0]*n+p['right'][1])


class TracingInterpreter(Interpreter):
    def __init__(self,functions,n):
        super().__init__(functions,'',n)
        self.trace=[];self.stack=[];self.gaps=[];self.quantities=[];self.site=None

    def call(self,name,values,depth=0):
        self.stack.append(name)
        self.quantities.append(dict(function=name,caller=self.stack[-2] if len(self.stack)>1 else None,line=self.site,arguments=[pack(v,self.n) for v in values]))
        try:return super().call(name,values,depth)
        finally:self.stack.pop()

    def expr(self,node,env,depth):
        previous=self.site
        if isinstance(node,ast.Call):self.site=node.lineno
        try:return self.traced_expr(node,env,depth)
        finally:self.site=previous

    def traced_expr(self,node,env,depth):
        result=super().expr(node,env,depth)
        if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Mult):
            safe=all(not isinstance(c,ast.Call) for c in ast.walk(node))
            if safe:
                a=super().expr(node.left,env,depth);b=super().expr(node.right,env,depth)
                count=b if isinstance(a,Sequence) else a if isinstance(b,Sequence) else None
                if isinstance(count,Affine):
                    self.trace.append(dict(function=self.stack[-1],line=node.lineno,op='GtE',left=[count.a,count.b],right=[0,0],decision=count.at(self.n)>=0,implicit='sequence repetition clamps negative counts'))
            elif isinstance(result,Sequence):
                self.gaps.append(dict(line=node.lineno,reason='sequence repetition guard tracing unsupported'))
        if isinstance(node,ast.Compare):
            # Re-read pure operands only; never duplicate a user function call.
            safe=all(not isinstance(c,ast.Call) or isinstance(c.func,ast.Name) and c.func.id=='len' for c in ast.walk(node))
            if len(node.ops)==1 and type(node.ops[0]).__name__ in OPS and safe:
                a=super().expr(node.left,env,depth);b=super().expr(node.comparators[0],env,depth)
                if isinstance(a,Affine) and isinstance(b,Affine):
                    self.trace.append(dict(function=self.stack[-1],line=node.lineno,op=type(node.ops[0]).__name__,
                        left=[a.a,a.b],right=[b.a,b.b],decision=result))
                else:self.gaps.append(dict(line=node.lineno,reason='non-affine comparison'))
            else:self.gaps.append(dict(line=node.lineno,reason='comparison tracing unsupported'))
        return result


def pack(value,n):
    if isinstance(value,Affine):return dict(type='integer',value=value.at(n),affine=[value.a,value.b])
    if isinstance(value,Sequence):return dict(type=value.unit,length=value.length.at(n),affine=[value.length.a,value.length.b])
    return dict(type=type(value).__name__,value=value)


def closure(functions,name):
    seen=set();pending=[name]
    while pending:
        name=pending.pop()
        if name in seen:continue
        seen.add(name)
        pending.extend(n.func.id for n in ast.walk(functions[name]) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in functions)
    # Global/imported names are NOT substituted, imported or presumed constant.
    return module_functions('\n'.join(ast.unparse(functions[n]) for n in sorted(seen)))


def observe(functions,name,n):
    engine=TracingInterpreter(functions,n)
    value=None;outcome='returned';error=None
    try:value=engine.call(name,[Affine(1,0)])
    except SubjectRaise:outcome='value_error'
    except Unsupported as exc:outcome='unsupported';error=str(exc)
    return dict(input=n,outcome=outcome,value=pack(value,n),trace=engine.trace,gaps=engine.gaps,
                quantities=engine.quantities,error=error)


def seed_points(lo,hi):
    return sorted({lo,hi}|{n for n in (-1,0,1) if lo<=n<=hi})


def explore(text,tests='',module='subject',window=(0,100),point_budget=32,task_budget=32,slots=8,mode='paths'):
    lo,hi=window
    integer(lo,-10000,10000,'window lower');integer(hi,lo,min(10000,lo+127),'window upper')
    integer(point_budget,1,32,'point budget');integer(task_budget,1,32,'task budget');integer(slots,1,8,'entry slots')
    if mode not in ('seeds','evidence','paths'):raise ValueError('unknown mode')
    try:
        inv,functions=inventory(text,tests,module)
    except ValueError as exc:
        if str(exc) not in ('test source size budget exceeded','test AST budget exceeded'):raise
        inv,functions=inventory(text,'',module)
        inv['unknown'].append(dict(reason=str(exc),stage='test_evidence',status='budget_blocked'))
    roots=sorted(inv['entries'],key=lambda e:('test_call' not in e['sources'],'literal_export' not in e['sources'],e['name']))
    reports=[];states=[]
    for entry in roots:
        r=dict(entry=entry['name'],status='entry_budget_deferred',observations=[],pending=[],infeasible=[],dropped_tasks=0,conflicts=entry['conflicts'])
        reports.append(r)
        if inv['duplicate_definitions']:
            r.update(status='unsupported',reason='duplicate function definitions');continue
        if len(states)>=slots:continue
        try:
            fs=closure(functions,entry['name'])
            # Preserve original positions for diagnostics, even though validation used unparse.
            fs={n:functions[n] for n in fs}
            if len(functions[entry['name']].args.args)!=1:raise Unsupported('requires one integer parameter')
        except Unsupported as exc:
            r.update(status='unsupported',reason=str(exc));continue
        state=dict(entry=entry,functions=fs,report=r,verify=[],explore=[],known=set(),seen=set())
        states.append(state)
        r['status']='planned'
    # Bind all mutable closures to their own entry state.
    def add(s,n,queue,reason):
        if not lo<=n<=hi or n in s['known']:return
        if len(s['known'])>=task_budget:s['report']['dropped_tasks']+=1;return
        s['known'].add(n);s[queue].append(dict(input=n,queue=queue,reason=reason))
    for s in states:
        if mode!='seeds':
            for ev in s['entry']['evidence']:
                if ev['input'] not in s['entry']['conflicts']:add(s,ev['input'],'verify','exact test example; no interval extrapolation')
        for n in seed_points(lo,hi):add(s,n,'explore','window seed; validity unknown')
    dispatch=[];turn='verify'
    while True:
        progress=False
        for s in states:
            r=s['report']
            if len(s['seen'])>=point_budget:continue
            queue=turn if s[turn] else ('explore' if turn=='verify' else 'verify')
            if not s[queue]:continue
            task=s[queue].pop(0);n=task['input'];s['seen'].add(n);progress=True
            row=observe(s['functions'],s['entry']['name'],n)
            row['task']=task;r['observations'].append(row);dispatch.append(dict(entry=s['entry']['name'],**task))
            if row['gaps']:r['status']='partial_trace'
            if row['outcome']=='unsupported':
                r['status']='partial_unsupported';continue
            if mode!='paths':continue
            prefix=[]
            for p in row['trace']:
                candidates=[x for x in range(lo,hi+1) if all(predicate(q,x)==q['decision'] for q in prefix) and predicate(p,x)!=p['decision']]
                key=dict(function=p['function'],line=p['line'],decision=not p['decision'],prefix=prefix.copy())
                if candidates:
                    # Existing observations discharge alternative-path tasks, not proofs outside window.
                    if not any(x in s['seen'] for x in candidates):
                        add(s,min(candidates,key=lambda x:(abs(x-n),x)),'explore',dict(kind='branch_alternative',target=key))
                elif key not in r['infeasible']:r['infeasible'].append(key)
                prefix.append(p)
        turn='explore' if turn=='verify' else 'verify'
        if not progress:break
    for s in states:
        r=s['report'];r['pending']=s['verify']+s['explore']
        if r['status']=='planned':r['status']='budget_limited' if r['pending'] or r['dropped_tasks'] else 'bounded_complete'
        r['checks']=[]
        for ev in s['entry']['evidence']:
            row=next((o for o in r['observations'] if o['input']==ev['input']),None)
            status='conflict' if ev['input'] in s['entry']['conflicts'] else 'unassessed'
            if status!='conflict' and row and row['outcome']!='unsupported':
                status='matches_example' if row['outcome']==ev['outcome'] and (ev['expected'] is None or row['value'].get('value')==ev['expected']) else 'example_disagreement'
            r['checks'].append(dict(evidence=ev,status=status,claim='conditional test evidence; no automatically confirmed bug'))
    return dict(schema_version=1,source_sha256=hashlib.sha256(text.encode()).hexdigest(),tests_sha256=hashlib.sha256(tests.encode()).hexdigest(),
        inventory=inv,entries=reports,dispatch=dispatch,mode=mode,window=[lo,hi],execution_enabled=False,
        scope='isolated function slices; module initialization/import effects unmodeled; finite investigation window, not valid-input domain; never imports/executes subject',
        limits=dict(entries=slots,points_per_entry=point_budget,tasks_per_entry=task_budget),
        unresolved='unseen or unsupported paths remain unknown; test applicability requires review')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--tests',type=Path)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--window',type=int,nargs=2,default=[0,100])
    a=p.parse_args()
    try:
        if a.out.exists():raise ValueError('output exists')
        if a.out.resolve() in {a.source.resolve(),a.tests.resolve() if a.tests else None}:raise ValueError('source output overlap')
        r=explore(a.source.read_text(),a.tests.read_text() if a.tests else '',a.source.stem,a.window)
        a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,indent=2)+'\n')
    except (ValueError,OSError,SyntaxError,RecursionError) as exc:p.exit(2,str(exc)+'\n')
    print(json.dumps(dict(entries=len(r['inventory']['entries']),analyzed_points=len(r['dispatch']),evidence=str(a.out))))


if __name__=='__main__':main()
