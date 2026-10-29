#!/usr/bin/env python3
"""Static typed-call investigation: exact evidence and finite single-argument probes.

No subject import/execution. Reuses the existing alternating investigation queue.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path

from path_exploration import investigation_queue
from python_facts import Returned, SubjectRaise, Unsupported
from typed_calls import Project, bind, decode, encode, extract, literal, mark_conflicts, span


class Facts:
    """Bounded concrete AST semantics for typed immutable values, not Python eval."""
    def __init__(self,project):
        self.project=project;self.steps=0;self.calls=[];self.trace=[]

    def tick(self):
        self.steps+=1
        if self.steps>2000:raise Unsupported('AST step budget')

    def builtin(self,module,name,env):
        return name not in env and name not in self.project.bindings[module] and '*' not in self.project.bindings[module]

    def expr(self,node,module,env,depth):
        self.tick()
        if isinstance(node,(ast.Constant,ast.Tuple)):
            if isinstance(node,ast.Tuple):
                value=tuple(self.expr(n,module,env,depth) for n in node.elts);encode(value);return value
            return literal(node)
        if isinstance(node,ast.Name):
            if node.id in env:return env[node.id]
            raise Unsupported('unresolved value/global: '+node.id)
        if isinstance(node,ast.UnaryOp):
            v=self.expr(node.operand,module,env,depth)
            if isinstance(node.op,ast.Not):return not v
            if type(v) is int and isinstance(node.op,(ast.UAdd,ast.USub)):return v if isinstance(node.op,ast.UAdd) else -v
            raise Unsupported('unary operator/type')
        if isinstance(node,ast.BinOp):
            a=self.expr(node.left,module,env,depth);b=self.expr(node.right,module,env,depth)
            if isinstance(node.op,ast.Add) and type(a) is type(b) and type(a) in (int,bytes,str,tuple):value=a+b
            elif isinstance(node.op,ast.Sub) and type(a) is type(b) is int:value=a-b
            elif isinstance(node.op,ast.Mult):
                if type(a) is int and type(b) is int:value=a*b
                else:
                    seq,count=(a,b) if type(b) is int else (b,a)
                    if type(seq) not in (bytes,str) or type(count) is not int:raise Unsupported('multiplication types')
                    if len(seq)*max(0,count)>64:raise Unsupported('sequence size budget')
                    value=seq*count
            else:raise Unsupported('binary operator/type')
            encode(value);return value
        if isinstance(node,ast.BoolOp):
            for n in node.values:
                value=self.expr(n,module,env,depth)
                if isinstance(node.op,ast.Or) and value:return value
                if isinstance(node.op,ast.And) and not value:return value
            return value
        if isinstance(node,ast.Compare):
            a=self.expr(node.left,module,env,depth)
            for op,rhs in zip(node.ops,node.comparators):
                b=self.expr(rhs,module,env,depth)
                if isinstance(op,ast.Eq):result=a==b
                elif isinstance(op,ast.NotEq):result=a!=b
                elif isinstance(op,(ast.Is,ast.IsNot)):
                    if a is not None and b is not None:raise Unsupported('identity supported only with None')
                    result=(a is None and b is None)
                    if isinstance(op,ast.IsNot):result=not result
                elif isinstance(op,(ast.Lt,ast.LtE,ast.Gt,ast.GtE)) and type(a) is type(b) is int:
                    result={ast.Lt:lambda:a<b,ast.LtE:lambda:a<=b,ast.Gt:lambda:a>b,ast.GtE:lambda:a>=b}[type(op)]()
                else:raise Unsupported('comparison operator/type')
                self.trace.append(dict(**span(module,node),operator=type(op).__name__,left=encode(a),right=encode(b),decision=result))
                if not result:return False
                a=b
            return True
        if isinstance(node,ast.Call):
            if any(isinstance(n,ast.Starred) for n in node.args) or any(k.arg is None for k in node.keywords):raise Unsupported('dynamic unpacking')
            args=[self.expr(n,module,env,depth) for n in node.args]
            kwargs=[(k.arg,self.expr(k.value,module,env,depth)) for k in node.keywords]
            if isinstance(node.func,ast.Name) and node.func.id=='len' and self.builtin(module,'len',env):
                if len(args)!=1 or kwargs or type(args[0]) not in (bytes,str,tuple):raise Unsupported('len signature/type')
                return len(args[0])
            target=self.project.resolve(module,node.func,env.keys())
            return self.call(target,args,kwargs,depth+1,span(module,node))
        raise Unsupported('expression unsupported: '+type(node).__name__)

    def block(self,body,module,env,depth):
        for node in body:
            self.tick()
            if isinstance(node,ast.Return):raise Returned(self.expr(node.value,module,env,depth) if node.value else None)
            elif isinstance(node,ast.If):
                value=self.expr(node.test,module,env,depth)
                self.block(node.body if value else node.orelse,module,env,depth)
            elif isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):env[node.targets[0].id]=self.expr(node.value,module,env,depth)
            elif isinstance(node,ast.Raise):
                call=node.exc
                if node.cause or not isinstance(call,ast.Call) or not isinstance(call.func,ast.Name) or call.func.id!='ValueError' or not self.builtin(module,'ValueError',env) or call.keywords or not all(isinstance(a,ast.Constant) and type(a.value) is str for a in call.args):raise Unsupported('raise ownership/form')
                raise SubjectRaise()
            elif isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):pass
            else:raise Unsupported('statement unsupported: '+type(node).__name__)

    def call(self,target,args,kwargs,depth=0,site=None):
        self.tick()
        if depth>4:raise Unsupported('call-depth budget')
        function=self.project.function(target)
        if function.decorator_list or function.returns is not None or any(a.annotation is not None for a in function.args.posonlyargs+function.args.args+function.args.kwonlyargs):raise Unsupported('decorator/annotation context unsupported')
        binding=bind(function,args,kwargs)
        self.calls.append(dict(target=target,site=site,binding=binding))
        env={name:decode(value) for name,value in binding['values'].items()}
        try:self.block(function.body,target['module'],env,depth)
        except Returned as result:return result.value
        return None


def observe(project,target,values):
    engine=Facts(project);value=None;error=None;outcome='returned'
    try:
        function=project.function(target);pos=function.args.posonlyargs+function.args.args
        args=[decode(values[a.arg]) for a in pos]
        kwargs=[(a.arg,decode(values[a.arg])) for a in function.args.kwonlyargs]
        value=engine.call(target,args,kwargs)
        encode(value)
    except SubjectRaise:outcome='value_error'
    except (Unsupported,ValueError) as exc:outcome='unsupported';error=str(exc);value=None
    return dict(outcome=outcome,value=encode(value),error=error,calls=engine.calls,trace=engine.trace)


def key(values):return json.dumps(values,sort_keys=True,separators=(',',':'))


def investigate(project,test_modules,lengths=(0,1,2,3,4,5,6,7,8),total_limit=64,entry_limit=8,point_limit=32):
    if not 1<=total_limit<=64 or not 1<=entry_limit<=8 or not 1<=point_limit<=32:raise ValueError('queue bounds')
    if not isinstance(lengths,(tuple,list)) or not 1<=len(lengths)<=16 or any(type(n) is not int or not 0<=n<=16 for n in lengths):raise ValueError('length bounds')
    evidence=[dict(test_module=m,**extract(project,m)) for m in test_modules]
    records=[r for e in evidence for r in e['records']]
    mark_conflicts(records)
    groups={}
    for r in records:
        if r['status']=='exact_conditional':groups.setdefault((r['target']['module'],r['target']['name']),[]).append(r)
    states=[];deferred=[]
    for identity,rows in sorted(groups.items()):
        if len(states)>=entry_limit:
            deferred.append(dict(identity=identity,reason='entry budget'));continue
        state=dict(target=rows[0]['target'],verify=[],explore=[],known=set(),rows=rows,observations=[],overflow=0)
        def add(values,queue,reason,evidence_source):
            k=key(values)
            if k in state['known']:return
            if len(state['known'])>=32:state['overflow']+=1;return
            state['known'].add(k);state[queue].append(dict(values=values,queue=queue,reason=reason,evidence_source=evidence_source))
        for row in rows:add(row['binding']['values'],'verify','exact conditional test call',row['source'])
        for row in rows:
            bound=row['binding']['values']
            for name,value in bound.items():
                if value['type'] in ('bytes','str'):
                    raw=decode(value)
                    # Exact content retained; family uses fixed first element, never arbitrary same-length data.
                    fill=raw[:1] or (b'\x00' if value['type']=='bytes' else '\x00')
                    variants=[fill*n for n in lengths]
                elif value['type']=='int':variants=[-1,0,1]
                else:continue
                for changed in variants:
                    values=dict(bound);values[name]=encode(changed)
                    add(values,'explore',dict(vary=name,kind='finite single-argument family',validity='unknown',template=encode(fill) if value['type'] in ('bytes','str') else None),row['source'])
        states.append(state)
    dispatch=[]
    for state,task in investigation_queue(states,point_limit,total_limit):
        row=observe(project,state['target'],task['values'])
        row.update(target=state['target'],task=task)
        row['checks']=[]
        for ev in state['rows']:
            if key(ev['binding']['values'])!=key(task['values']):continue
            expected=ev['expectation'];status='unassessed'
            if row['outcome']!='unsupported':status='matches_example' if row['outcome']==expected['outcome'] and (not expected['has_value'] or decode(row['value'])==decode(expected['value'])) else 'example_disagreement'
            row['checks'].append(dict(source=ev['source'],status=status,claim='conditional exact example only; not a confirmed bug'))
        state['observations'].append(row);dispatch.append(row)
    return dict(schema_version=1,evidence=evidence,dispatch=dispatch,
        entries=[dict(target=s['target'],pending=s['verify']+s['explore'],overflow_attempts=s['overflow'],observations=len(s['observations'])) for s in states],
        deferred=deferred,source_sha256={m:hashlib.sha256(t.encode()).hexdigest() for m,t in project.sources.items()},
        limits=dict(static_dispatch=total_limit,entries=entry_limit,points_per_entry=point_limit,lengths=list(lengths)),
        execution_enabled=False,scope='isolated source semantics; module initialization/import availability unknown; exact test evidence conditional; generated-input validity unknown',
        limitations='finite content templates, one changed parameter, no string solver or inferred public contract; source identity does not establish dependency behavior')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace',type=Path,required=True);p.add_argument('--tests',nargs='+',required=True,help='module identities under explicit workspace')
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    try:
        if args.out.exists() or args.out.resolve().is_relative_to(args.workspace.resolve()):raise ValueError('new output outside source required')
        project=Project.directory(args.workspace)
        report=investigate(project,args.tests)
        args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2)+'\n')
    except (ValueError,Unsupported,SyntaxError,OSError,KeyError,RecursionError) as exc:p.exit(2,str(exc)+'\n')
    print(json.dumps(dict(static_tasks=len(report['dispatch']),execution_enabled=False,evidence=str(args.out))))


if __name__=='__main__':main()
