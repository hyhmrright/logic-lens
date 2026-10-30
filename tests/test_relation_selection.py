"""Static synthetic relations; never imports or executes subject source."""
import ast
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from typed_calls import Project, decode
from typed_investigation import investigate
from relation_selection import select, interval


def project(body,test="assert f(b'A') == 0",extra=None):
    return Project(dict(subject=body,test_subject='from subject import f\ndef test_f():\n    '+test+'\n',**(extra or {})))


def source(expr,op,bound):
    return f'def f(data):\n    x=len(data)\n    if {expr} {op} {bound}:\n        return 0\n    return 0\n'


class Relations(unittest.TestCase):
    def test_frozen_cut_labels_and_equal_budget_correction(self):
        labels=json.loads((Path(__file__).resolve().parents[1]/'examples/relation-selection/portfolio.json').read_text())
        for label in labels['development'][:3]:
            p=project(source(label['expression'],label['operator'],label['bound']))
            report=select(p,['test_subject'],total_limit=4)
            relation=report['relations'][0]
            self.assertEqual(relation['cut'],label['cut'])
            self.assertEqual(relation['reachable_outcomes'],[False,True])
            selected=[len(decode(d['task']['values']['data'])) for d in report['dispatch']]
            baseline=investigate(p,['test_subject'],total_limit=4)
            old=[len(decode(d['task']['values']['data'])) for d in baseline['dispatch']]
            self.assertEqual(len(selected),len(old))
            self.assertIn(label['cut'],selected);self.assertNotIn(label['cut'],old)
            self.assertFalse(any(d['checks'] for d in report['dispatch'] if d['task']['relations']))

    def test_nested_call_provenance(self):
        p=project('def helper(n):\n    return 2*(n+3)\ndef f(data):\n    if helper(len(data)) > 32:\n        return 0\n    return 0\n')
        r=select(p,['test_subject'])['relations'][0]
        self.assertEqual(r['cut'],14)
        p=project('def helper(n):\n    if 2*n > 30:\n        return 0\n    return 0\ndef f(data):\n    return helper(len(data))\n')
        r=select(p,['test_subject'])['relations'][0]
        self.assertEqual(len(r['call_chain']),2)
        self.assertEqual(r['cut'],16)

    def test_route_and_infeasible_branch(self):
        p=project('def f(data):\n    x=len(data)\n    if x < 5:\n        if 3*x > 30:\n            return 0\n        return 0\n    return 0\n')
        r=select(p,['test_subject'])['relations'][1]
        self.assertEqual(r['reachable_outcomes'],[False]);self.assertFalse(r['points'])
        p=project('def f(data):\n    x=len(data)\n    if x < 5:\n        if x > 8:\n            if x > 10:\n                return 0\n    return 0\n')
        r=select(p,['test_subject'])['relations'][2]
        self.assertEqual(r['searchability'],'unreachable')

    def test_late_parameters_receive_first_turn(self):
        body='def f(a,b,c,d,e):\n'
        for index,name in enumerate('abcde'):
            body+=f'    if len({name}) > {10+index}:\n        return 0\n'
        body+='    return 0\n'
        p=project(body,"assert f(b'A',b'A',b'A',b'A',b'A') == 0")
        # 1 exact + 5 distinct relation first turns. Old admission can fill
        # 32 slots with earlier parameter families before e gets a turn.
        r=select(p,['test_subject'],total_limit=6)
        self.assertEqual(len(r['dispatch']),6)
        params={rel['parameter'] for rel in r['relations'] if any(rel['id'] in d['task']['relations'] for d in r['dispatch'])}
        self.assertEqual(params,set('abcde'))
        self.assertTrue(r['deferred'])

    def test_public_untested_inventory_never_guesses_binding(self):
        r=select(Project({'subject':source('3*x','>',30)}))
        self.assertEqual(r['entries'][0]['status'],'missing_binding')
        self.assertTrue(r['entries'][0]['unbound_predicates'])
        self.assertFalse(r['dispatch'])

    def test_unknowns_and_no_invented_contract(self):
        for expr in ('x*x','len(data)+n'):
            body=('def f(data,n=2):\n    x=len(data)\n    if '+expr+' > 30:\n        return 0\n    return 0\n')
            r=select(project(body),['test_subject'])
            self.assertEqual(r['relations'][0]['searchability'],'unsupported')
            self.assertIsNone(r['relations'][0]['normative_property'])
            self.assertTrue(r['issues'])
        p=project(source('x','>',100000));r=select(p,['test_subject'])
        self.assertEqual(r['relations'][0]['searchability'],'out_of_budget')
        self.assertFalse(r['relations'][0]['points'])

    def test_annotations_external_and_initialization_are_not_executed(self):
        p=project('raise RuntimeError("never run")\n'+source('x','>',12))
        self.assertFalse(select(p,['test_subject'])['execution_enabled'])
        p=project(source('x','>',12).replace('f(data)','f(data: bytes)'))
        r=select(p,['test_subject']);self.assertFalse(r['relations']);self.assertTrue(r['issues'])
        p=project('from external import helper\ndef f(data):\n    if helper(data)>2:\n        return 0\n    return 0\n')
        r=select(p,['test_subject']);self.assertEqual(r['relations'][0]['searchability'],'unsupported')

    def test_finite_independent_predicate_restrictions(self):
        # Brute arithmetic oracle does not call inversion or interval helpers.
        operations={'Gt':lambda x:x>0,'GtE':lambda x:x>=0,'Lt':lambda x:x<0,'LtE':lambda x:x<=0,'Eq':lambda x:x==0,'NotEq':lambda x:x!=0}
        for a in (-4,-1,1,3):
            for b in (-7,0,9):
                for op,fn in operations.items():
                    for truth in (False,True):
                        pred=dict(quantity=dict(terms={'x':a},offset=b),operator=op)
                        lo,hi,holes=interval(pred,truth,-24,24)
                        got=[x for x in range(-24,25) if lo<=x<=hi and x not in holes]
                        want=[x for x in range(-24,25) if fn(a*x+b)==truth]
                        self.assertEqual(got,want)

    def test_conflicts_block_and_limits(self):
        p=project(source('x','>',12),"assert f(b'A') == 0\n    assert f(b'A') == 1")
        r=select(p,['test_subject']);self.assertFalse(r['dispatch'])
        for kwargs in (dict(total_limit=65),dict(point_limit=33),dict(total_limit=True)):
            with self.assertRaises(ValueError):select(p,['test_subject'],**kwargs)

    def test_no_hidden_interpreter_dispatch_for_ranking(self):
        import relation_selection
        p=project(source('3*x','>',30))
        real=relation_selection.observe
        with patch('relation_selection.observe',wraps=real) as wrapped:
            report=select(p,['test_subject'],total_limit=4)
        self.assertEqual(wrapped.call_count,len(report['dispatch']))

    def test_bounded_entry_fairness_and_pending(self):
        body=''
        tests=''
        for i in range(3):
            body+=f'def f{i}(data):\n    if len(data)>{10+i}:\n        return 0\n    return 0\n'
            tests+=f'from subject import f{i}\ndef test_{i}():\n    assert f{i}(b"A")==0\n'
        r=select(Project(dict(subject=body,test_subject=tests)),['test_subject'],total_limit=6)
        served={d['task']['target']['name'] for d in r['dispatch'] if d['task']['relations']}
        self.assertEqual(served,{'f0','f1','f2'})
        self.assertTrue(r['deferred'])


if __name__=='__main__':unittest.main()
