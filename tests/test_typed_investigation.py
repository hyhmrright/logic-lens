"""Static synthetic qualification. No subject imports or actual target calls here."""
import ast
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from typed_calls import Project, bind, decode, encode, extract, literal
from typed_investigation import investigate, observe
from python_facts import Unsupported

EXAMPLES=ROOT/'examples/typed-investigation'


def fixture(name):return Project.directory(EXAMPLES/name)


def function(text):return ast.parse(text).body[0]


class TypedEvidence(unittest.TestCase):
    def test_types_content_units_and_limits(self):
        values=[None,True,1,b'A',b'B','A',(None,True,b'\x00')]
        self.assertEqual([decode(encode(v)) for v in values],values)
        self.assertNotEqual(encode(True),encode(1))
        self.assertNotEqual(encode(b'A'),encode('A'))
        self.assertNotEqual(encode(b'A'),encode(b'B'))
        self.assertEqual(encode(b'\xff')['hex'],'ff')
        for value in ([],{},b'a'*65,1<<129):
            with self.assertRaises(Unsupported):encode(value)
        with self.assertRaises(Unsupported):literal(ast.parse('make()',mode='eval').body)

    def test_binding_positional_only_keyword_only_defaults_and_explicit_none(self):
        f=function("def f(a, /, b=b'!', *, enabled=True, marker=None):\n    return a\n")
        r=bind(f,[b'A'],[])
        self.assertEqual({k:decode(v) for k,v in r['values'].items()},dict(a=b'A',b=b'!',enabled=True,marker=None))
        self.assertEqual(r['origins']['b'],'default')
        self.assertEqual(bind(f,[b'A'],[('marker',None)])['origins']['marker'],'keyword')
        self.assertEqual(bind(f,[b'A'],[('enabled',False)])['values']['enabled'],encode(False))
        self.assertEqual(bind(f,[b'A'],[('b',b'!')])['values'],r['values'])
        for args,kw in [([],[]),([b'A'],[('a',b'B')]),([b'A',b'B',b'C'],[]),([b'A'],[('other',1)]),([b'A'],[('b',1),('b',2)]),([b'A',b'B'],[('b',b'C')])]:
            with self.assertRaises(ValueError):bind(f,args,kw)
        with self.assertRaises(Unsupported):bind(f,[b'A'],[(None,1)])

    def test_immutable_tuple_and_unsupported_defaults(self):
        f=function('def f(x, labels=(1, True, None)):\n    return x\n')
        self.assertEqual(decode(bind(f,[1],[])['values']['labels']),(1,True,None))
        for default in ('[]','make()','GLOBAL','{}'):
            with self.assertRaises(Unsupported):bind(function('def f(x, option='+default+'):\n    return x\n'),[1],[])

    def test_test_classes_local_constants_bytes_and_unittest_aliases(self):
        for name,count in [('01-bytes-default',1),('02-unittest-binding',2),('03-allowed-refusal',1)]:
            p=fixture(name);r=extract(p,'test_subject')['records']
            self.assertEqual(len(r),count)
            self.assertTrue(all(e['status']=='exact_conditional' for e in r))
            self.assertTrue(all(e['arguments']['args'][0]['type']=='bytes' for e in r))
        r=extract(fixture('03-allowed-refusal'),'test_subject')['records'][0]
        self.assertEqual(r['expectation']['outcome'],'value_error')

    def test_relative_import_reexport_and_provenance(self):
        p=fixture('04-relative-source');r=extract(p,'test_subject')['records'][0]
        self.assertEqual((r['target']['module'],r['target']['name']),('pkg.api','attach'))
        self.assertGreaterEqual(len(r['target']['provenance']),3)
        row=observe(p,r['target'],r['binding']['values'])
        self.assertEqual(decode(row['value']),b'A!')
        self.assertEqual([c['target']['module'] for c in row['calls']],['pkg.api','pkg.worker'])
        r=extract(fixture('05-reexport-source'),'test_subject')['records'][0]
        self.assertEqual(r['target']['module'],'backend')
        self.assertGreaterEqual(len(r['target']['chain']),3)

    def test_unknown_context_shadowing_conflict_and_unsupported(self):
        expected={'06-shadowed-name':'dependency_unknown','07-fixture-context':'context_unknown','08-contract-conflict':'conflict','09-mutable-default':'unsupported'}
        for name,status in expected.items():
            p=fixture(name);records=extract(p,'test_subject')['records']
            self.assertTrue(any(e['status']==status for e in records),(name,records))
            self.assertFalse(investigate(p,['test_subject'])['dispatch'])
        for name in ('10-external-boundary','11-unsupported-content'):
            r=investigate(fixture(name),['test_subject'],total_limit=2)
            self.assertTrue(r['dispatch'])
            self.assertTrue(all(row['outcome']=='unsupported' for row in r['dispatch']))

    def test_same_length_bytes_keep_content_and_no_validity_generalization(self):
        r=investigate(fixture('12-equal-length-content'),['test_subject'],total_limit=8)
        known=[row for row in r['dispatch'] if row['task']['queue']=='verify']
        self.assertEqual([decode(row['value']) for row in known],[1,2])
        self.assertTrue(all(row['checks'][0]['status']=='matches_example' for row in known))
        self.assertTrue(any(not row['checks'] for row in r['dispatch'] if row['task']['queue']=='explore'))
        self.assertTrue(all(row['task']['reason']['validity']=='unknown' for row in r['dispatch'] if row['task']['queue']=='explore'))

    def test_queue_bounds_pending_and_single_changed_parameter(self):
        r=investigate(fixture('02-unittest-binding'),['test_subject'],total_limit=4)
        self.assertEqual(len(r['dispatch']),4)
        self.assertEqual([v['task']['queue'] for v in r['dispatch']],['verify','explore','verify','explore'])
        self.assertTrue(r['entries'][0]['pending'])
        baselines=[e['binding']['values'] for ev in r['evidence'] for e in ev['records'] if e['status']=='exact_conditional']
        for row in r['dispatch']:
            if row['task']['queue']=='explore':
                self.assertTrue(any(sum(row['task']['values'][k]!=v[k] for k in v)==1 for v in baselines))
        with self.assertRaises(ValueError):investigate(fixture('01-bytes-default'),['test_subject'],total_limit=65)

    def test_assertion_override_and_fake_libraries_never_trusted(self):
        subject="def f(data):\n    return data\n"
        cases=["import unittest\nfrom subject import f\nclass TestX(unittest.TestCase):\n    def assertEqual(self, a, b):\n        pass\n    def test_x(self):\n        self.assertEqual(f(b'A'),b'A')\n",
               "import pytest\nfrom subject import f\ndef test_x():\n    with pytest.raises(ValueError):\n        f(b'A')\n"]
        p=Project(dict(subject=subject,test_subject=cases[0]))
        self.assertFalse(any(r['status']=='exact_conditional' for r in extract(p,'test_subject')['records']))
        p=Project(dict(subject=subject,test_subject=cases[1],pytest='def raises(x):\n    return x\n'))
        self.assertFalse(any(r['status']=='exact_conditional' for r in extract(p,'test_subject')['records']))

    def test_cycle_conditionals_star_import_and_local_shadow(self):
        p=Project({'a':'from b import f\n','b':'from a import f\n','test_subject':'from a import f\n'})
        r=p.resolve('test_subject',ast.Name(id='f'))
        self.assertEqual(r['status'],'unknown');self.assertIn('cyclic',r['reason'])
        for text in ('if flag:\n    from a import f\n','from a import *\n','from a import f\nf=other\n'):
            p=Project({'a':'def f(x):\n    return x\n','test_subject':text})
            self.assertEqual(p.resolve('test_subject',ast.Name(id='f'))['status'],'unknown')
        p=fixture('01-bytes-default')
        self.assertEqual(p.resolve('test_subject',ast.Name(id='attach'),{'attach'})['status'],'unknown')

    def test_static_only_even_with_import_sentinel(self):
        p=Project({'subject':"raise RuntimeError('must never execute')\ndef f(data=b'A'):\n    return data\n",'test_subject':"from subject import f\ndef test_x():\n    assert f() == b'A'\n"})
        r=investigate(p,['test_subject'],total_limit=1)
        self.assertFalse(r['execution_enabled'])
        self.assertEqual(decode(r['dispatch'][0]['value']),b'A')
        self.assertIn('initialization',r['scope'])

    def test_metamorphic_alias_default_spelling_and_local_move(self):
        p=fixture('01-bytes-default');base=extract(p,'test_subject')['records'][0]
        sources=dict(p.sources);sources['test_subject']=sources['test_subject'].replace('from subject import attach','from subject import attach as renamed').replace('attach(data)','renamed(data, suffix=b\'!\')')
        changed=extract(Project(sources),'test_subject')['records'][0]
        self.assertEqual(base['binding']['values'],changed['binding']['values'])
        sources={'worker':p.sources['subject'],'subject':'from worker import attach\n','test_subject':p.sources['test_subject']}
        moved=extract(Project(sources),'test_subject')['records'][0]
        self.assertEqual(moved['target']['module'],'worker')
        self.assertEqual(observe(Project(sources),moved['target'],moved['binding']['values'])['value'],encode(b'A!'))

    def test_binding_errors_never_become_findings(self):
        p=Project({'subject':'def f(x, /):\n    return x\n','test_subject':"from subject import f\ndef test_bad():\n    assert f(x=b'A') == b'A'\n"})
        r=extract(p,'test_subject')['records'][0]
        self.assertEqual(r['status'],'binding_error')
        self.assertFalse(investigate(p,['test_subject'])['dispatch'])

    def test_no_content_model_from_length_and_builtin_shadowing(self):
        p=Project({'subject':"def f(data):\n    return len(data)\nlen=other\n",'test_subject':"from subject import f\ndef test_x():\n    assert f(b'A') == 1\n"})
        r=investigate(p,['test_subject'],total_limit=1)
        self.assertEqual(r['dispatch'][0]['outcome'],'unsupported')

    def test_cross_file_conflicts_and_unmodeled_setup_calls(self):
        sources={'subject':"def f(data, suffix=b'!'):\n    return data+suffix\n",
                 'test_a':"from subject import f\ndef test_x():\n    assert f(b'A') == b'A!'\n",
                 'test_b':"from subject import f\ndef test_y():\n    assert f(b'A', suffix=b'!') == b'bad'\n"}
        r=investigate(Project(sources),['test_a','test_b'])
        self.assertFalse(r['dispatch'])
        self.assertTrue(all(v['status']=='conflict' for e in r['evidence'] for v in e['records']))
        sources['test_a']="from subject import f\ndef test_x():\n    patch()\n    assert f(b'A') == b'A!'\n"
        r=extract(Project(sources),'test_a')
        self.assertFalse(any(v['status']=='exact_conditional' for v in r['records']))

    def test_tuple_bool_none_return_and_budget_block(self):
        p=Project({'subject':'def f(value=True, marker=None, labels=(1,2)):\n    return (value, marker, labels)\n','test_subject':'from subject import f\ndef test_x():\n    assert f() == (True, None, (1,2))\n'})
        r=investigate(p,['test_subject'],total_limit=1)
        self.assertEqual(decode(r['dispatch'][0]['value']),(True,None,(1,2)))
        self.assertEqual(r['dispatch'][0]['checks'][0]['status'],'matches_example')
        with self.assertRaises(ValueError):Project({'a':'x=1\n'*4000})


if __name__=='__main__':unittest.main()
