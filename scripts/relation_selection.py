#!/usr/bin/env python3
"""Opt-in, AST-only affine relation inventory and bounded boundary selection.

No target imports, eval/exec, inferred public contracts, or model calls.
"""
import argparse
import ast
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from python_facts import Unsupported
from typed_calls import Project, bind, decode, encode, extract, literal, mark_conflicts, span
from typed_investigation import observe, key


@dataclass
class Quantity:
    terms: dict
    offset: int = 0
    kind: str = None


@dataclass
class Sequence:
    length: Quantity
    kind: str


def constant(value):
    if type(value) is int:return Quantity({}, value)
    if type(value) in (bytes, str, tuple):
        kind={bytes:'bytes', str:'str', tuple:'tuple'}[type(value)]
        return Sequence(Quantity({}, len(value), 'length:'+kind), kind)
    raise Unsupported('symbolic type unsupported')


def combine(a, b, sign=1):
    if not isinstance(a, Quantity) or not isinstance(b, Quantity):raise Unsupported('non-quantity arithmetic')
    if a.kind and b.kind and a.kind!=b.kind:raise Unsupported('incompatible quantity kinds')
    terms=dict(a.terms)
    for name,v in b.terms.items():terms[name]=terms.get(name,0)+sign*v
    result=Quantity({k:v for k,v in terms.items() if v}, a.offset+sign*b.offset, a.kind or b.kind)
    if any(abs(v).bit_length()>128 for v in [result.offset,*result.terms.values()]):raise Unsupported('coefficient budget')
    return result


def scale(a, factor):
    if type(factor) is not int:raise Unsupported('nonconstant scale')
    return combine(Quantity({},kind=a.kind), Quantity({k:v*factor for k,v in a.terms.items()},a.offset*factor,a.kind))


def decision(value, op):
    return {'Gt':value>0,'GtE':value>=0,'Lt':value<0,'LtE':value<=0,'Eq':value==0,'NotEq':value!=0}[op]


def interval(predicate, truth, lo, hi):
    """Exact integer restriction for a single affine comparison, including holes."""
    q=predicate['quantity'];op=predicate['operator'];terms=q['terms']
    if len(terms)>1:raise Unsupported('multi-parameter route')
    if not terms:return (lo,hi,[]) if decision(q['offset'],op)==truth else (1,0,[])
    a=next(iter(terms.values()));b=q['offset']
    # Complement first; normalize coefficient to positive.
    if not truth:op={'Gt':'LtE','GtE':'Lt','Lt':'GtE','LtE':'Gt','Eq':'NotEq','NotEq':'Eq'}[op]
    if a<0:a,b=-a,-b;op={'Gt':'Lt','GtE':'LtE','Lt':'Gt','LtE':'GtE','Eq':'Eq','NotEq':'NotEq'}[op]
    if op=='Gt':lo=max(lo,(-b)//a+1)
    elif op=='GtE':lo=max(lo,-(b//a))
    elif op=='Lt':hi=min(hi,-(b//a)-1)
    elif op=='LtE':hi=min(hi,(-b)//a)
    elif (-b)%a==0:
        root=(-b)//a
        if op=='Eq':lo,hi=max(lo,root),min(hi,root)
        else:return lo,hi,[root]
    elif op=='Eq':return 1,0,[]
    return lo,hi,[]


def packed(q):return dict(terms=q.terms,offset=q.offset,kind=q.kind)


def evaluate_predicate(predicate,values):
    q=predicate['quantity'];value=q['offset']
    for name,coefficient in q['terms'].items():
        raw=decode(values[name]);value+=coefficient*(raw if type(raw) is int else len(raw))
    return decision(value,predicate['operator'])


class Inventory:
    def __init__(self,project,entry):
        self.project=project;self.entry=entry;self.relations=[];self.issues=[];self.steps=0

    def tick(self):
        self.steps+=1
        if self.steps>2000:raise Unsupported('symbolic step budget')

    def builtin(self,module,name,env):
        return name not in env and name not in self.project.bindings[module] and '*' not in self.project.bindings[module]

    def expr(self,n,module,env,path,chain):
        self.tick()
        if isinstance(n,ast.Name) and n.id in env:return env[n.id]
        if isinstance(n,(ast.Constant,ast.Tuple)):return constant(literal(n))
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):
            q=self.expr(n.operand,module,env,path,chain)
            if not isinstance(q,Quantity):raise Unsupported('unary quantity')
            return scale(q,1 if isinstance(n.op,ast.UAdd) else -1)
        if isinstance(n,ast.BinOp):
            a=self.expr(n.left,module,env,path,chain);b=self.expr(n.right,module,env,path,chain)
            if isinstance(n.op,ast.Add) and isinstance(a,Sequence) and isinstance(b,Sequence) and a.kind==b.kind:return Sequence(combine(a.length,b.length),a.kind)
            if isinstance(n.op,(ast.Add,ast.Sub)):return combine(a,b,1 if isinstance(n.op,ast.Add) else -1)
            if isinstance(n.op,ast.Mult):
                if isinstance(a,Quantity) and not a.terms and a.kind is None:a,b=b,a
                if not isinstance(b,Quantity) or b.terms or b.kind is not None:raise Unsupported('nonlinear or dimensioned multiplication')
                if isinstance(a,Sequence):
                    if b.offset<0:raise Unsupported('negative sequence repetition')
                    return Sequence(scale(a.length,b.offset),a.kind)
                if isinstance(a,Quantity):return scale(a,b.offset)
            raise Unsupported('non-affine expression')
        if isinstance(n,ast.Call):
            args=[self.expr(x,module,env,path,chain) for x in n.args]
            kwargs=[(x.arg,self.expr(x.value,module,env,path,chain)) for x in n.keywords]
            if isinstance(n.func,ast.Name) and n.func.id=='len' and self.builtin(module,'len',env):
                if len(args)!=1 or kwargs or not isinstance(args[0],Sequence):raise Unsupported('len type/signature')
                return args[0].length
            target=self.project.resolve(module,n.func,env.keys())
            f=self.project.function(target)
            # Use the existing binder for signature validation/defaults, then
            # replace dummy explicit values with their symbolic counterparts.
            binding=bind(f,[0 for _ in args],[(k,0) for k,_ in kwargs])
            values={name:constant(decode(v)) for name,v in binding['values'].items()}
            for formal,value in zip(f.args.posonlyargs+f.args.args,args):values[formal.arg]=value
            values.update(kwargs)
            return self.call(target,values,path,chain+[dict(target=target,site=span(module,n))])
        raise Unsupported('symbolic expression: '+type(n).__name__)

    def predicate(self,n,module,env,path,chain):
        if not isinstance(n,ast.Compare) or len(n.ops)!=1 or type(n.ops[0]).__name__ not in ('Lt','LtE','Gt','GtE','Eq','NotEq'):raise Unsupported('simple comparison required')
        try:
            a=self.expr(n.left,module,env,path,chain);b=self.expr(n.comparators[0],module,env,path,chain)
            q=combine(a,b,-1)
        except Unsupported as exc:
            if len(self.relations)<32:
                self.relations.append(dict(entry=self.entry,source=span(module,n),producer=ast.unparse(n.left),consumer_predicate=ast.unparse(n),call_chain=chain,path_conditions=list(path),predicate=None,quantity_kind=None,evidence_scope='conditional isolated source semantics',oracle_status='none',normative_property=None,unsupported_reason=str(exc)))
            raise
        pred=dict(quantity=packed(q),operator=type(n.ops[0]).__name__)
        if len(self.relations)>=32:raise Unsupported('relation inventory budget')
        self.relations.append(dict(entry=self.entry,source=span(module,n),producer=ast.unparse(n.left),consumer_predicate=ast.unparse(n),
            call_chain=chain,path_conditions=list(path),predicate=pred,quantity_kind=q.kind,
            evidence_scope='conditional isolated source semantics',oracle_status='none',normative_property=None))
        return pred

    def block(self,body,module,env,path,chain):
        if not body:return [None]
        self.tick();n,*rest=body
        if isinstance(n,ast.If):
            pred=self.predicate(n.test,module,env,path,chain)
            results=[]
            for truth,branch in ((True,n.body),(False,n.orelse)):
                results.extend(self.block(branch+rest,module,dict(env),path+[dict(predicate=pred,truth=truth)],chain))
            return results
        if isinstance(n,ast.Return):return [self.expr(n.value,module,env,path,chain) if n.value else None]
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):env[n.targets[0].id]=self.expr(n.value,module,env,path,chain)
        elif isinstance(n,ast.Expr) and isinstance(n.value,ast.Call):self.expr(n.value,module,env,path,chain)
        elif isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and type(n.value.value) is str:pass
        else:raise Unsupported('symbolic statement: '+type(n).__name__)
        return self.block(rest,module,env,path,chain)

    def call(self,target,env,path,chain):
        self.tick()
        if len(chain)>5:raise Unsupported('call-depth budget')
        f=self.project.function(target)
        if f.decorator_list or f.returns is not None or any(a.annotation for a in f.args.posonlyargs+f.args.args+f.args.kwonlyargs):raise Unsupported('decorator/annotation context unsupported')
        values=self.block(f.body,target['module'],env,path,chain)
        if any(v!=values[0] for v in values):raise Unsupported('path-dependent return value')
        return values[0]


def qualify(relation,seed):
    result=dict(relation,searchability='unsupported',points=[],reason=None,reachable_outcomes=[])
    pred=relation['predicate']
    if pred is None:
        result['reason']=relation['unsupported_reason'];return result
    q=pred['quantity'];terms=q['terms']
    if len(terms)!=1:
        result['reason']='constant or multi-parameter predicate';return result
    name,a=next(iter(terms.items()));value=seed[name];kind=value['type']
    if kind=='int':lo,hi=-10000,10000
    elif kind in ('bytes','str','tuple'):lo,hi=0,64 if kind!='tuple' else 8
    else:result['reason']='unsupported input kind';return result
    holes=set()
    try:
        for route in relation['path_conditions']:
            original=route['predicate'];rq=original['quantity'];offset=rq['offset'];rt={}
            # Single-argument investigation: other parameters stay at the exact
            # seed binding. This is a conditional slice, not global reachability.
            for param,coefficient in rq['terms'].items():
                if param==name:rt[param]=coefficient
                else:
                    raw=decode(seed[param]);v=raw if type(raw) is int else len(raw)
                    offset+=coefficient*v
            reduced=dict(operator=original['operator'],quantity=dict(terms=rt,offset=offset))
            lo,hi,excluded=interval(reduced,route['truth'],lo,hi);holes.update(excluded)
    except Unsupported as exc:result['reason']=str(exc);return result
    result.update(parameter=name,input_validity='unknown',route_scope='isolated source conditions; other parameters fixed to seed',search_interval=[lo,hi],excluded=sorted(holes))
    if hi<lo or hi-lo+1<=sum(lo<=h<=hi for h in holes):
        result.update(searchability='unreachable',reason='empty route in bounded search domain');return result
    for truth in (False,True):
        left,right,excluded=interval(pred,truth,lo,hi);blocked=holes|set(excluded)
        if right>=left and right-left+1>sum(left<=h<=right for h in blocked):result['reachable_outcomes'].append(truth)
    floor=(-q['offset'])//a
    changes=[x for x in range(floor-1,floor+3) if decision(a*(x-1)+q['offset'],pred['operator'])!=decision(a*x+q['offset'],pred['operator'])]
    if not changes:
        result.update(searchability='constant',reason='no integer truth transition');return result
    cut=min(changes);points=[x for x in (cut,cut-1,cut+1) if lo<=x<=hi and x not in holes]
    result.update(cut=cut,points=points,searchability='searchable' if points else 'out_of_budget',reason=None if points else 'transition neighbors outside bounded route/domain')
    return result


def boundary_values(seed,name,n):
    values=dict(seed);raw=decode(seed[name]);kind=seed[name]['type']
    if kind=='int':changed=n
    else:
        fill=raw[:1] or {'bytes':b'\x00','str':'\x00','tuple':(0,)}[kind]
        changed=fill*n
    values[name]=encode(changed);return values


def select(project,test_modules=(),total_limit=64,point_limit=32):
    if type(total_limit) is not int or not 1<=total_limit<=64 or type(point_limit) is not int or not 1<=point_limit<=32:raise ValueError('dispatch bounds')
    evidence=[dict(test_module=m,**extract(project,m)) for m in test_modules]
    rows=[r for e in evidence for r in e['records']];mark_conflicts(rows)
    groups={}
    for row in rows:
        if row['status']=='exact_conditional':groups.setdefault((row['target']['module'],row['target']['name']),[]).append(row)
    entries=[];relations=[];issues=[];tasks=[];seen={};counts={};deferred=[]
    inventory=[]
    for module,table in sorted(project.bindings.items()):
        if module in test_modules:continue
        for name,binding in sorted(table.items()):
            if binding['kind']=='definition' and isinstance(binding['node'],ast.FunctionDef) and not name.startswith('_'):
                inventory.append((module,name))
    # Exact evidence targets are eligible even for private definitions. Untested
    # public definitions remain visible, but no input type/binding is invented.
    identities=sorted(set(inventory)|set(groups))
    active=0
    for identity in identities:
        module,name=identity;target=project.resolve(module,ast.Name(id=name));examples=groups.get(identity,[])
        entry=dict(target=target,status='missing_binding',relations=[])
        entries.append(entry)
        if not examples:
            f=project.function(target)
            entry['unbound_predicates']=[dict(source=span(module,n),consumer_predicate=ast.unparse(n),searchability='missing_binding',oracle_status='none') for n in ast.walk(f) if isinstance(n,ast.Compare)]
            params={a.arg for a in f.args.posonlyargs+f.args.args+f.args.kwonlyargs}
            entry['unbound_calls']=[dict(source=span(module,n),target=project.resolve(module,n.func,params),searchability='missing_binding') for n in ast.walk(f) if isinstance(n,ast.Call)]
            continue
        if active>=8:entry['status']='deferred';deferred.append(dict(entry=target,reason='entry budget'));continue
        active+=1;entry['status']='conditional';entry['seed']=examples[0]['binding']['values'];entry['examples']=examples
        inv=Inventory(project,target)
        try:
            env={}
            for param,value in entry['seed'].items():
                raw=decode(value);kind=value['type']
                if kind=='int':env[param]=Quantity({param:1},kind='integer')
                elif kind in ('bytes','str','tuple'):env[param]=Sequence(Quantity({param:1},kind='length:'+kind),kind)
                else:raise Unsupported('symbolic input kind: '+kind)
            inv.call(target,env,[],[dict(target=target,site=None)])
        except (Unsupported,ValueError) as exc:issues.append(dict(entry=target,reason=str(exc),status='unsupported'))
        for raw in inv.relations:
            relation=qualify(raw,entry['seed']);relation['id']=hashlib.sha256(json.dumps(raw,sort_keys=True).encode()).hexdigest()
            # Symbolic ranking only: do not spend unaccounted interpreter
            # dispatches before the bounded queue. This is predicted coverage.
            covered=set()
            if raw['predicate'] is not None:
                for row in examples:
                    values=row['binding']['values']
                    if all(evaluate_predicate(p['predicate'],values)==p['truth'] for p in raw['path_conditions']):covered.add(evaluate_predicate(raw['predicate'],values))
            relation['predicted_example_decisions']=sorted(covered)
            entry['relations'].append(relation);relations.append(relation)
    def admit(entry,values,reason,relation_id=None):
        ident=(entry['target']['module'],entry['target']['name']);token=(ident,key(values))
        if token in seen:
            if relation_id and relation_id not in seen[token]['relations']:seen[token]['relations'].append(relation_id)
            return
        if len(tasks)>=total_limit or counts.get(ident,0)>=point_limit:
            deferred.append(dict(entry=entry['target'],values=values,relation_id=relation_id,reason='dispatch budget'));return
        task=dict(target=entry['target'],values=values,reason=reason,relations=[relation_id] if relation_id else [])
        seen[token]=task;tasks.append(task);counts[ident]=counts.get(ident,0)+1
    eligible=[e for e in entries if e['status']=='conditional']
    # Reserve one exact example per entry; all remaining exact examples stay
    # explicitly deferred until every searchable relation gets its first turn.
    for entry in eligible:admit(entry,entry['seed'],'exact conditional example')
    per_entry=[[(entry,r) for r in sorted(entry['relations'],key=lambda r:(len(r['predicted_example_decisions'])>=2,r['id'])) if r['searchability']=='searchable'] for entry in eligible]
    families=[]
    for index in range(max((len(f) for f in per_entry),default=0)):
        families.extend(f[index] for f in per_entry if index<len(f))
    for turn in range(3):
        for entry,relation in families:
            if turn<len(relation['points']):admit(entry,boundary_values(entry['seed'],relation['parameter'],relation['points'][turn]),'relation boundary; validity unknown',relation['id'])
    for entry in eligible:
        for row in entry['examples'][1:]:admit(entry,row['binding']['values'],'exact conditional example')
    dispatch=[]
    for task in tasks:
        result=observe(project,task['target'],task['values']);checks=[]
        for entry in eligible:
            if entry['target']!=task['target']:continue
            for row in entry['examples']:
                if key(row['binding']['values'])!=key(task['values']):continue
                expected=row['expectation'];status='unassessed'
                if result['outcome']!='unsupported':status='matches_example' if result['outcome']==expected['outcome'] and (not expected['has_value'] or decode(result['value'])==decode(expected['value'])) else 'example_disagreement'
                checks.append(dict(source=row['source'],status=status,claim='conditional example, not confirmed bug'))
        dispatch.append(dict(task=task,observation=result,checks=checks,claim='boundary observation only; no new normative oracle'))
    return dict(schema_version=1,entries=entries,relations=relations,issues=issues,evidence=evidence,dispatch=dispatch,deferred=deferred,
        execution_enabled=False,source_sha256={m:hashlib.sha256(t.encode()).hexdigest() for m,t in project.sources.items()},
        limits=dict(static_dispatch=total_limit,points_per_entry=point_limit,entries=8,relations_per_entry=32,steps_per_entry=2000,call_depth=4,integer_window=[-10000,10000]),
        scope='conditional isolated source semantics; no public contract inference; no actual target execution')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--tests',nargs='*',default=[]);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    try:
        if args.out.exists() or args.out.resolve().is_relative_to(args.workspace.resolve()):raise ValueError('new output outside source required')
        report=select(Project.directory(args.workspace),args.tests)
        args.out.parent.mkdir(parents=True,exist_ok=True)
        with args.out.open('x') as stream:stream.write(json.dumps(report,indent=2)+'\n')
    except (Unsupported,ValueError,SyntaxError,OSError,KeyError,RecursionError) as exc:p.exit(2,str(exc)+'\n')
    print(json.dumps(dict(relations=len(report['relations']),static_dispatch=len(report['dispatch']),execution_enabled=False,out=str(args.out))))


if __name__=='__main__':main()
