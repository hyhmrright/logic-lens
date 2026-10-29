#!/usr/bin/env python3
"""Bounded typed test-call evidence, AST signature binding and static provenance.

Never imports, evaluates or executes subject/test modules. Resolution is source
identity, not proof of import availability or dependency behavior.
"""
import ast
import hashlib
import json
from pathlib import Path

from python_facts import Unsupported


def encode(value,depth=0):
    if depth>4:raise Unsupported('value nesting budget')
    t=type(value)
    if value is None:return dict(type='none')
    if t is bool:return dict(type='bool',value=value)
    if t is int and value.bit_length()<=128:return dict(type='int',value=value)
    if t is bytes and len(value)<=64:return dict(type='bytes',hex=value.hex(),length=len(value))
    if t is str and len(value)<=64:return dict(type='str',value=value,length=len(value))
    if t is tuple and len(value)<=8:return dict(type='tuple',items=[encode(v,depth+1) for v in value])
    raise Unsupported('value type/size unsupported')


def decode(value):
    kind=value['type']
    if kind=='none':return None
    if kind=='bytes':return bytes.fromhex(value['hex'])
    if kind=='tuple':return tuple(decode(v) for v in value['items'])
    if kind in ('int','bool','str'):return value['value']
    raise Unsupported('unknown typed value')


def literal(node,env=None):
    env=env or {}
    if isinstance(node,ast.Name) and node.id in env:return env[node.id]
    if isinstance(node,ast.Constant):value=node.value
    elif isinstance(node,ast.Tuple):value=tuple(literal(n,env) for n in node.elts)
    elif isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.USub,ast.UAdd)):
        v=literal(node.operand,env)
        if type(v) is not int:raise Unsupported('signed literal requires integer')
        value=-v if isinstance(node.op,ast.USub) else v
    else:raise Unsupported('not a supported immutable literal/local constant')
    encode(value)
    return value


def bind(function,args,keywords):
    """Inputs/outputs are concrete immutable values; duplicate keywords stay visible."""
    spec=function.args
    if spec.vararg or spec.kwarg:raise Unsupported('variadic signature unsupported')
    positional=spec.posonlyargs+spec.args
    names=[a.arg for a in positional+spec.kwonlyargs]
    if len(names)!=len(set(names)):raise Unsupported('duplicate formal parameter')
    if len(args)>len(positional):raise ValueError('too many positional arguments')
    defaults={a.arg:literal(v) for a,v in zip(positional[len(positional)-len(spec.defaults):],spec.defaults)}
    defaults.update({a.arg:literal(v) for a,v in zip(spec.kwonlyargs,spec.kw_defaults) if v is not None})
    values=dict(zip((a.arg for a in positional),args));origins={name:'positional' for name in values}
    for name,value in keywords:
        if name is None:raise Unsupported('dynamic **kwargs unsupported')
        if name in {a.arg for a in spec.posonlyargs}:raise ValueError('positional-only passed by keyword')
        if name not in names:raise ValueError('unexpected keyword')
        if name in values:raise ValueError('multiple values for parameter')
        values[name]=value;origins[name]='keyword'
    for name in names:
        if name not in values:
            if name not in defaults:raise ValueError('missing required parameter: '+name)
            values[name]=defaults[name];origins[name]='default'
    return dict(values={name:encode(values[name]) for name in names},origins=origins)


def span(module,node):return dict(module=module,line=node.lineno,end=node.end_lineno)


class Project:
    def __init__(self,sources,packages=()):
        if not hasattr(self,'packages'):self.packages=set(packages)
        if not 1<=len(sources)<=16:raise ValueError('1..16 explicit source files required')
        self.sources=sources;self.trees={};self.bindings={};self.issues=[]
        for module,text in sorted(sources.items()):
            tree=ast.parse(text)
            if len(text.encode())>131072 or sum(1 for _ in ast.walk(tree))>12000:raise ValueError('source/AST budget exceeded: '+module)
            self.trees[module]=tree;bindings={}
            def put(name,value):
                value['location']=span(module,node)
                bindings[name]=dict(kind='unknown',reason='rebound or ambiguous name') if name in bindings else value
            for node in tree.body:
                if isinstance(node,(ast.FunctionDef,ast.ClassDef)):
                    put(node.name,dict(kind='definition',node=node))
                elif isinstance(node,ast.Import):
                    for alias in node.names:put(alias.asname or alias.name.split('.')[0],dict(kind='module',module=alias.name if alias.asname else alias.name.split('.')[0]))
                elif isinstance(node,ast.ImportFrom):
                    base=self.import_base(module,node)
                    for alias in node.names:
                        if alias.name=='*':put('*',dict(kind='unknown',reason='star import'))
                        else:put(alias.asname or alias.name,dict(kind='alias',module=base,name=alias.name))
                else:
                    # Never execute initialization; conservative bindings from any conditional/store.
                    for child in ast.walk(node):
                        if isinstance(child,ast.Name) and isinstance(child.ctx,ast.Store):put(child.id,dict(kind='unknown',reason='module assignment/conditional binding'))
                        elif isinstance(child,(ast.FunctionDef,ast.ClassDef)):
                            put(child.name,dict(kind='unknown',reason='conditional definition'))
                        elif isinstance(child,(ast.Import,ast.ImportFrom)):
                            for alias in child.names:put(alias.asname or alias.name.split('.')[0],dict(kind='unknown',reason='conditional import'))
            self.bindings[module]=bindings

    def import_base(self,module,node):
        if not node.level:return node.module or ''
        # Package identities have an explicit __init__ source sentinel in paths.
        package=module.split('.') if self.is_package(module) else module.split('.')[:-1]
        if node.level>len(package):return '<outside-root>'
        return '.'.join(package[:len(package)-node.level+1]+([node.module] if node.module else []))

    def is_package(self,module):return module in getattr(self,'packages',set())

    @classmethod
    def directory(cls,root):
        root=Path(root).resolve();sources={};paths={};packages=set()
        files=sorted(p for p in root.rglob('*.py') if '__pycache__' not in p.parts)
        if len(files)>16:raise ValueError('source-file budget exceeded')
        for path in files:
            if path.is_symlink() or not path.resolve().is_relative_to(root):raise ValueError('source outside explicit root')
            rel=path.relative_to(root).with_suffix('');parts=list(rel.parts)
            if parts[-1]=='__init__':parts.pop();packages.add('.'.join(parts))
            module='.'.join(parts)
            if not module or module in sources:raise ValueError('ambiguous module path')
            if path.stat().st_size>131072:raise ValueError('source file budget exceeded')
            sources[module]=path.read_text();paths[module]=str(path.relative_to(root))
        # Relative imports must know package identities before indexing bindings.
        obj=cls.__new__(cls);obj.packages=packages;cls.__init__(obj,sources);obj.paths=paths
        return obj

    def resolve(self,module,expression,blocked=(),seen=()):
        if len(seen)>8:return dict(status='unknown',reason='resolution depth budget',chain=list(seen))
        if isinstance(expression,ast.Name):parts=[expression.id]
        elif isinstance(expression,ast.Attribute):
            attrs=[];node=expression
            while isinstance(node,ast.Attribute):attrs.insert(0,node.attr);node=node.value
            if not isinstance(node,ast.Name):return dict(status='unknown',reason='dynamic target')
            parts=[node.id]+attrs
        else:return dict(status='unknown',reason='dynamic target')
        if parts[0] in blocked:return dict(status='unknown',reason='local/parameter shadowing')
        result=self.symbol(module,parts,seen)
        result['provenance']=[]
        for token in result.get('chain',[]):
            mod,_,name=token.partition(':')
            binding=self.bindings.get(mod,{}).get(name.split('.')[0],{})
            if 'location' in binding:result['provenance'].append(binding['location'])
        return result

    def symbol(self,module,parts,seen=()):
        token=module+':'+'.'.join(parts)
        if token in seen:return dict(status='unknown',reason='cyclic alias',chain=list(seen)+[token])
        if len(seen)>=8:return dict(status='unknown',reason='resolution depth budget',chain=list(seen))
        chain=tuple(seen)+(token,)
        if module not in self.bindings:
            if len(parts)>1 and module+'.'+parts[0] in self.sources:return self.symbol(module+'.'+parts[0],parts[1:],chain)
            if any(m.startswith(module+'.') for m in self.sources):return dict(status='unknown',reason='unresolved local namespace',chain=list(chain))
            return dict(status='external',module=module,name='.'.join(parts),chain=list(chain),behavior='unknown')
        table=self.bindings[module]
        if '*' in table:return dict(status='unknown',reason='star-import namespace',chain=list(chain))
        value=table.get(parts[0])
        if value is None:
            candidate=module+'.'+parts[0]
            if len(parts)>1 and candidate in self.sources:return self.symbol(candidate,parts[1:],chain)
            return dict(status='unknown',reason='unresolved name',chain=list(chain))
        if value['kind']=='unknown':return dict(status='unknown',reason=value['reason'],chain=list(chain))
        if value['kind']=='module':
            if len(parts)==1:return dict(status='module',module=value['module'],chain=list(chain))
            # import a.b, accessed as a.b.fn
            target=value['module'];rest=parts[1:]
            while target+'.'+rest[0] in self.sources and len(rest)>1:
                target+='.'+rest.pop(0)
            return self.symbol(target,rest,chain)
        if value['kind']=='alias':
            target=value['module'];name=value['name']
            if not parts[1:] and target+'.'+name in self.sources:return dict(status='module',module=target+'.'+name,chain=list(chain))
            if target+'.'+name in self.sources and parts[1:]:return self.symbol(target+'.'+name,parts[1:],chain)
            return self.symbol(target,[name]+parts[1:],chain)
        if len(parts)>1:return dict(status='unknown',reason='object/class attribute unsupported',chain=list(chain))
        node=value['node']
        return dict(status='local',module=module,name=parts[0],kind=type(node).__name__,location=span(module,node),chain=list(chain))

    def function(self,target):
        if target.get('status')!='local' or target.get('kind')!='FunctionDef':raise Unsupported('target not a local function')
        return self.bindings[target['module']][target['name']]['node']


def extract(project,test_module):
    records=[];unknown=[];tree=project.trees[test_module]
    def external(expr,module,name,blocked=()):
        r=project.resolve(test_module,expr,blocked)
        return r.get('status')=='external' and r.get('module')==module and r.get('name')==name
    def test_method(f,cls=None,context_reason=None):
        local_names={n.id for n in ast.walk(f) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store)}
        local_names.update(a.arg for a in f.args.posonlyargs+f.args.args+f.args.kwonlyargs)
        env={};captured=set()
        context=context_reason
        expected_args=['self'] if cls else []
        if f.decorator_list or f.returns is not None or any(a.annotation is not None for a in f.args.args) or [a.arg for a in f.args.args]!=expected_args or f.args.defaults or f.args.kwonlyargs or f.args.vararg or f.args.kwarg or f.args.posonlyargs:
            context='test fixture/signature/decorator unresolved'
        def record(call,outcome=None,expected=None,has_expected=False):
            if not isinstance(call,ast.Call):return
            target=project.resolve(test_module,call.func,local_names)
            if target.get('status')=='external' and target.get('module') in ('unittest','pytest'):return
            item=dict(source=span(test_module,call),context=(cls.name+'.' if cls else '')+f.name,
                call=ast.unparse(call),target=target,expectation=dict(outcome=outcome,has_value=has_expected,value=encode(expected) if has_expected else None),
                status='context_unknown' if context or outcome is None else 'exact_conditional',reason=context or ('no supported obligation' if outcome is None else 'exact example; test environment applicability not proven'))
            captured.add(id(call))
            try:
                if any(isinstance(a,ast.Starred) for a in call.args):raise Unsupported('dynamic *args unsupported')
                args=[literal(a,env) for a in call.args];kwargs=[(k.arg,literal(k.value,env)) for k in call.keywords]
                item['arguments']=dict(args=[encode(v) for v in args],keywords=[dict(name=k,value=encode(v)) for k,v in kwargs])
                item['binding']=bind(project.function(target),args,kwargs)
            except Unsupported as exc:item.update(status='unsupported' if target.get('status')=='local' else 'dependency_unknown',reason=str(exc))
            except ValueError as exc:item.update(status='binding_error',reason=str(exc))
            records.append(item)
        assertion_methods={n.name for n in cls.body if isinstance(n,ast.FunctionDef)} if cls else set()
        unittest_class=bool(cls and len(cls.bases)==1 and external(cls.bases[0],'unittest','TestCase'))
        for statement in f.body:
            try:
                if isinstance(statement,ast.Assign) and len(statement.targets)==1 and isinstance(statement.targets[0],ast.Name):
                    env[statement.targets[0].id]=literal(statement.value,env)
                elif isinstance(statement,ast.Assert) and isinstance(statement.test,ast.Compare) and len(statement.test.ops)==1 and isinstance(statement.test.ops[0],ast.Eq):
                    left=statement.test.left;right=statement.test.comparators[0]
                    if isinstance(left,ast.Call):record(left,'returned',literal(right,env),True)
                    elif isinstance(right,ast.Call):record(right,'returned',literal(left,env),True)
                    else:raise Unsupported('assertion shape')
                elif isinstance(statement,ast.Expr) and isinstance(statement.value,ast.Call):
                    call=statement.value
                    if (unittest_class and isinstance(call.func,ast.Attribute) and isinstance(call.func.value,ast.Name) and call.func.value.id=='self'
                        and call.func.attr=='assertEqual' and 'assertEqual' not in assertion_methods and len(call.args)==2 and not call.keywords):
                        captured.add(id(call))
                        if isinstance(call.args[0],ast.Call):record(call.args[0],'returned',literal(call.args[1],env),True)
                        elif isinstance(call.args[1],ast.Call):record(call.args[1],'returned',literal(call.args[0],env),True)
                        else:raise Unsupported('assertEqual arguments')
                    else:
                        record(call,'returned')
                        active=[n for n in f.body if not isinstance(n,ast.Assign) and not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str))]
                        if len(active)>1:context='unmodeled expression-call setup/effects'
                elif isinstance(statement,ast.With) and len(statement.items)==1 and len(statement.body)==1 and isinstance(statement.body[0],ast.Expr):
                    c=statement.items[0].context_expr
                    standard=bool(isinstance(c,ast.Call) and isinstance(c.func,ast.Attribute) and isinstance(c.func.value,ast.Name) and c.func.value.id=='self' and c.func.attr=='assertRaises' and unittest_class and 'assertRaises' not in assertion_methods)
                    pytest=bool(isinstance(c,ast.Call) and external(c.func,'pytest','raises',local_names))
                    if not (standard or pytest) or c.keywords or len(c.args)!=1 or not isinstance(c.args[0],ast.Name) or c.args[0].id!='ValueError' or 'ValueError' in local_names or 'ValueError' in project.bindings[test_module]:raise Unsupported('exception ownership/context unresolved')
                    captured.add(id(c))
                    record(statement.body[0].value,'value_error')
                elif isinstance(statement,ast.Expr) and isinstance(statement.value,ast.Constant) and isinstance(statement.value.value,str):pass
                else:raise Unsupported('test setup/control flow unsupported')
            except Unsupported as exc:
                if isinstance(statement,ast.Assign):
                    for t in statement.targets:
                        if isinstance(t,ast.Name):env.pop(t.id,None)
                context='test context unresolved: '+str(exc)
                unknown.append(dict(source=span(test_module,statement),reason=context))
                # Any setup/effect can affect earlier obligations too; downgrade below.
        if context:
            for r in records:
                if r['context']==(cls.name+'.' if cls else '')+f.name and r['status']=='exact_conditional':r.update(status='context_unknown',reason=context)
        for call in ast.walk(f):
            if isinstance(call,ast.Call) and id(call) not in captured:
                target=project.resolve(test_module,call.func,local_names)
                if target.get('status') in ('local','unknown'):record(call)
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name.startswith('test_'):test_method(node)
        elif isinstance(node,ast.ClassDef):
            is_unit=len(node.bases)==1 and external(node.bases[0],'unittest','TestCase')
            if not node.name.startswith('Test') and not is_unit:continue
            reason=None
            if node.decorator_list or node.keywords or node.bases and not is_unit:reason='test inheritance/decorator unresolved'
            if any(not isinstance(n,(ast.FunctionDef,ast.Pass)) for n in node.body):reason='test class initialization/state unresolved'
            if any(isinstance(n,ast.FunctionDef) and (not n.name.startswith('test_') or n.decorator_list) for n in node.body):reason='test lifecycle/helper/override unresolved'
            for method in node.body:
                if isinstance(method,ast.FunctionDef) and method.name.startswith('test_'):test_method(method,node,reason)
    mark_conflicts(records)
    return dict(records=records,unknown=unknown,scope='conditional exact calls only; no valid-domain inference')


def mark_conflicts(records):
    """Conservative conflicts across test files, using actual equality semantics."""
    groups={}
    for r in records:
        if r['status']=='exact_conditional' and 'binding' in r:
            key=json.dumps([r['target']['module'],r['target']['name'],r['binding']['values']],sort_keys=True)
            groups.setdefault(key,[]).append(r)
    for rows in groups.values():
        outcomes={r['expectation']['outcome'] for r in rows}
        expected=[decode(r['expectation']['value']) for r in rows if r['expectation']['has_value']]
        if len(outcomes)>1 or any(v!=expected[0] for v in expected):
            for r in rows:r.update(status='conflict',reason='contradictory exact expectations for same bound call')
