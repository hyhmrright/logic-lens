"""Trusted synthetic execution only. Real subjects are never imported/executed."""
import ast
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from path_exploration import explore, inventory, predicate

EXAMPLE=ROOT/'examples/path-exploration'
TEXT=(EXAMPLE/'subject.py').read_text()
TESTS=(EXAMPLE/'test_subject.py').read_text()


def actual_table(text=TEXT,window=range(16)):
    """Independent real Python semantics/branch tracing, evaluator only."""
    namespace={};filename='<trusted-path-synthetic>'
    exec(compile(text,filename,'exec'),namespace)
    branches={(n.name,c.lineno):c.body[0].lineno for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)
              for c in ast.walk(n) if isinstance(c,ast.If)}
    result={}
    for name in namespace['__all__']:
        for n in window:
            previous={};decisions=[];calls=[]
            def tracer(frame,event,arg):
                if frame.f_code.co_filename!=filename:return tracer
                if event=='call':
                    arguments=[]
                    for key in frame.f_code.co_varnames[:frame.f_code.co_argcount]:
                        v=frame.f_locals[key]
                        arguments.append(dict(type='byte' if isinstance(v,bytes) else 'character',length=len(v)) if isinstance(v,(bytes,str)) else dict(type='integer',value=v))
                    calls.append(dict(function=frame.f_code.co_name,arguments=arguments))
                if event=='line':
                    key=(frame.f_code.co_name,frame.f_lineno)
                    prior=previous.get(id(frame))
                    if prior in branches:decisions.append((prior[0],prior[1],frame.f_lineno==branches[prior]))
                    previous[id(frame)]=key
                elif event=='return':previous.pop(id(frame),None)
                return tracer
            previous_tracer=sys.gettrace()
            sys.settrace(tracer)
            try:row=dict(outcome='returned',value=namespace[name](n))
            except ValueError:row=dict(outcome='value_error',value=None)
            finally:sys.settrace(previous_tracer)
            row['trace']=decisions;row['calls']=calls;result[name,n]=row
    return result


class PathExploration(unittest.TestCase):
    def run_mode(self,mode='paths',**kw):
        return explore(TEXT,TESTS,window=(0,15),mode=mode,**kw)

    def test_automatic_entries_and_exact_evidence_no_contract_ranges(self):
        r=self.run_mode();entries={e['name']:e for e in r['inventory']['entries']}
        self.assertEqual(len(entries),8)
        self.assertNotIn('_sink',entries)
        self.assertEqual(entries['hidden']['evidence'][0]['input'],0)
        self.assertNotIn('valid',entries['hidden'])
        self.assertEqual(entries['conflicting']['conflicts'],[2])
        root=next(e for e in r['entries'] if e['entry']=='conflicting')
        self.assertEqual({c['status'] for c in root['checks']},{'conflict'})
        self.assertFalse(r['execution_enabled'])

    def test_cross_function_hidden_path_and_affine_coordinates(self):
        r=self.run_mode()
        for name in ('hidden','converted'):
            rows=next(e['observations'] for e in r['entries'] if e['entry']==name)
            self.assertTrue(any(o['input']==7 and o['outcome']=='value_error' for o in rows))
            self.assertTrue(any(p['left']==[3,2] for o in rows for p in o['trace'] if p['function']=='_hidden'))
        seed=self.run_mode('seeds')
        for name in ('hidden','converted'):
            self.assertFalse(any(o['outcome']=='value_error' for e in seed['entries'] if e['entry']==name for o in e['observations']))

    def test_exhaustive_independent_runtime_agreement_and_finite_coverage(self):
        table=actual_table();r=self.run_mode()
        for e in r['entries']:
            for row in e['observations']:
                if row['outcome']=='unsupported':continue
                actual=table[e['entry'],row['input']]
                self.assertEqual(row['outcome'],actual['outcome'])
                if row['outcome']=='returned':self.assertEqual(row['value']['value'],actual['value'])
                quantities=[dict(function=q['function'],arguments=[{k:v for k,v in arg.items() if k!='affine'} for arg in q['arguments']]) for q in row['quantities']]
                self.assertEqual(quantities,actual['calls'])
                self.assertEqual([(p['function'],p['line'],p['decision']) for p in row['trace'] if 'implicit' not in p],actual['trace'])
        for name in ('hidden','converted','multiple','alternate','permitted','impossible'):
            observed={tuple((p['function'],p['line'],p['decision']) for p in o['trace'] if 'implicit' not in p) for e in r['entries'] if e['entry']==name for o in e['observations']}
            exhaustive={tuple(v['trace']) for (root,n),v in table.items() if root==name}
            self.assertEqual(observed,exhaustive,name)

    def test_multiple_call_sites_preserved_representation_units(self):
        rows=next(e['observations'] for e in self.run_mode()['entries'] if e['entry']=='multiple')
        values=[q['arguments'][0] for row in rows for q in row['quantities'] if q['function']=='_sink']
        self.assertEqual({tuple(v['affine']) for v in values},{(1,0),(2,0)})
        self.assertEqual({v['type'] for v in values},{'byte'})
        self.assertEqual(len({c['line'] for e in self.run_mode()['inventory']['entries'] if e['name']=='multiple' for c in e['calls'] if c['target']=='_sink'}),2)

    def test_correct_alternative_allowed_refusal_and_unknown_do_not_make_bugs(self):
        r=self.run_mode()
        permitted=next(e for e in r['entries'] if e['entry']=='permitted')
        self.assertEqual(permitted['checks'][0]['status'],'matches_example')
        alternate=next(e for e in r['entries'] if e['entry']=='alternate')
        self.assertTrue(all(o['outcome']=='returned' for o in alternate['observations']))
        hidden=next(e for e in r['entries'] if e['entry']=='hidden')
        self.assertTrue(any(o['outcome']=='value_error' for o in hidden['observations']))
        self.assertNotIn('confirmed_bug',json.dumps(r))
        self.assertEqual(hidden['checks'][0]['status'],'matches_example')

    def test_infeasible_is_scoped_and_unsupported_stays_unknown(self):
        r=self.run_mode()
        e=next(e for e in r['entries'] if e['entry']=='impossible')
        self.assertTrue(e['infeasible'])
        self.assertEqual(r['window'],[0,15])
        dynamic=next(e for e in r['entries'] if e['entry']=='dynamic')
        self.assertEqual(dynamic['status'],'partial_unsupported')
        self.assertTrue(all(o['outcome']=='unsupported' for o in dynamic['observations']))

    def test_queue_alternation_round_robin_and_budget_evidence(self):
        r=self.run_mode(point_budget=2,task_budget=4,slots=2)
        names=[d['entry'] for d in r['dispatch']]
        self.assertEqual(len(set(names[:2])),2)
        self.assertEqual(r['dispatch'][0]['queue'],'verify')
        self.assertEqual(r['dispatch'][2]['queue'],'explore')
        self.assertTrue(any(e['pending'] or e['dropped_tasks'] for e in r['entries']))
        self.assertTrue(any(e['status']=='entry_budget_deferred' for e in r['entries']))
        self.assertTrue(all(len(e['observations'])<=2 for e in r['entries']))

    def test_metamorphic_rename_split_equivalent_arithmetic(self):
        variants=[TEXT.replace('_hidden','_renamed'),TEXT.replace('3*n+2','n+n+n+2'),
                  TEXT.replace('return _hidden(3*n+2)','return _split(3*n+2)')+'\ndef _split(x):\n    return _hidden(x)\n']
        for text in variants:
            r=explore(text,TESTS,window=(0,15))
            rows=next(e['observations'] for e in r['entries'] if e['entry']=='hidden')
            self.assertTrue(any(o['input']==7 and o['outcome']=='value_error' for o in rows))

    def test_fixture_dynamic_input_alias_shadowing_and_import_ownership(self):
        tests='''from subject import hidden as f
from other import hidden

def test_ok():
    assert f(0) == 2

def test_fixture(x):
    assert f(x) == 2

def test_other():
    assert hidden(0) == 2
'''
        inv,_=inventory(TEXT,tests)
        e=next(e for e in inv['entries'] if e['name']=='hidden')
        self.assertEqual(len(e['evidence']),1)
        self.assertTrue(inv['unknown'])
        inv,_=inventory(TEXT,tests+'\nf = fake\n')
        self.assertFalse(next(e for e in inv['entries'] if e['name']=='hidden')['evidence'])

    def test_no_real_module_import_or_execution_during_planning(self):
        text="import missing_dependency\nraise RuntimeError('never execute')\ndef public(n):\n    return n+1\n"
        r=explore(text,window=(0,5))
        self.assertTrue(r['inventory']['unmodeled_initialization'])
        self.assertFalse(r['execution_enabled'])
        self.assertEqual(r['entries'][0]['observations'][0]['outcome'],'returned')
        self.assertIn('isolated function slices',r['scope'])

    def test_boolean_negative_affine_and_no_global_unreachability(self):
        text='def entry(n):\n    return helper(10-2*n)\ndef helper(x):\n    if x > 2 and x < 8:\n        return 1\n    return 0\n'
        r=explore(text,window=(0,10))
        rows=next(e['observations'] for e in r['entries'] if e['entry']=='entry')
        self.assertEqual({o['value']['value'] for o in rows},{0,1})
        for row in rows:
            for p in row['trace']:self.assertEqual(predicate(p,row['input']),p['decision'])

    def test_piecewise_repetition_guard_prevents_false_infeasibility(self):
        text="def entry(n):\n    if len(b'x'*n) > 2:\n        return 1\n    return 0\n"
        r=explore(text,window=(-5,5))
        rows=r['entries'][0]['observations']
        self.assertEqual({o['value']['value'] for o in rows},{0,1})
        self.assertTrue(any('implicit' in p for o in rows for p in o['trace']))

    def test_rebound_import_is_not_contract_evidence(self):
        tests="from subject import hidden as f\nfrom other import hidden as f\ndef test_x():\n    assert f(0) == 2\n"
        inv,_=inventory(TEXT,tests)
        self.assertFalse(next(e for e in inv['entries'] if e['name']=='hidden')['evidence'])

    def test_test_budget_block_preserves_entry_inventory(self):
        tests='\n'.join('x=1' for _ in range(4000))
        r=explore('def entry(n):\n    return n\n',tests)
        self.assertEqual(r['inventory']['entries'][0]['name'],'entry')
        self.assertTrue(any(u.get('stage')=='test_evidence' and u['status']=='budget_blocked' for u in r['inventory']['unknown']))

    def test_invalid_limits_and_duplicate_definitions(self):
        with self.assertRaises(ValueError):explore(TEXT,window=(0,128))
        with self.assertRaises(ValueError):explore(TEXT,slots=9)
        r=explore('def f(n):\n    return n\ndef f(n):\n    return n+1\n')
        self.assertTrue(r['inventory']['duplicate_definitions'])
        self.assertFalse(r['dispatch'])


if __name__=='__main__':unittest.main()
