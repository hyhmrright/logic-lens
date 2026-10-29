"""Offline synthetic closed-loop scheduler tests. No model calls or real-case fixtures."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
import investigation
from constraint_plan import plan as real_plan
from llm_runner import tree_digest

EXAMPLE=ROOT/'examples/investigation'


class Investigation(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.work=self.root/'source';self.work.mkdir()
        for name in ('subject.py','CONTRACTS.txt'):
            (self.work/name).write_bytes((EXAMPLE/'workspace'/name).read_bytes())
        self.spec=json.loads((EXAMPLE/'request.json').read_text())

    def change(self, old, new):
        p=self.work/'subject.py';p.write_text(p.read_text().replace(old,new))
        self.spec['trusted_source_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()

    def run_plan(self, execute=False):
        self.out=self.root/'output'
        report=investigation.run(self.spec,self.work,self.out,execute)
        self.relations=json.loads((self.out/'relations.json').read_text())
        self.facts=json.loads((self.out/'facts.json').read_text())
        return report

    def test_automatic_inventory_no_suspicious_consumer_supplied(self):
        report=self.run_plan()
        self.assertEqual({r['entry'] for r in self.relations},{e['name'] for e in self.spec['entries']})
        self.assertNotIn('unused_consumer',{r['consumer'] for r in self.relations})
        self.assertEqual(len(report['selected']),2)
        self.assertEqual({r['entry'] for r in self.relations if r['selection']=='selected'},{'first','second'})
        self.assertTrue(all(e['status']=='planned_only' for e in report['executions']))
        self.assertFalse((self.out/'executions').exists())

    def test_closed_loop_actual_search_oracle_and_manifest(self):
        before=tree_digest(self.work)
        report=self.run_plan(True)
        self.assertEqual([e['status'] for e in report['executions']],['counterexample','counterexample'])
        self.assertTrue(all(1<e['evaluations']<=32 for e in report['executions']))
        self.assertEqual(tree_digest(self.work),before)
        for rid in report['selected']:
            folder=self.out/'executions'/rid
            prop=json.loads((folder/'property.json').read_text())
            self.assertEqual(prop['claim'],'Contract-valid entry input must return normally')
            self.assertNotIn('scale',json.loads((folder/'execution.json').read_text()))
            summary=json.loads((folder/'search/summary.json').read_text())
            self.assertEqual(summary['counterexample']['result']['observation']['outcome'],'value_error')
        for f,h in json.loads((self.out/'sha256.json').read_text()).items():
            self.assertEqual(hashlib.sha256((self.out/f).read_bytes()).hexdigest(),h)

    def test_valid_rejection_and_guarded_alternate_are_not_bug_oracles(self):
        self.run_plan()
        reasons={r['entry']:r['reason'] for r in self.relations}
        self.assertIn('no distinguishing must-return oracle',reasons['tolerated'])
        self.assertIn('no predicted contract-distinguishing',reasons['guarded'])
        self.assertIn('not globally unreachable',reasons['unreachable'])

    def test_second_pass_adds_inverse_boundary_outside_seed(self):
        self.run_plan()
        first=self.facts['first']
        self.assertNotIn(6,first['seed_points'])
        self.assertIn(6,first['checked_points'])
        for r in self.relations:
            if r['status']=='ready':
                self.assertTrue(set(r['domain'])<=set(r['points']))
                self.assertTrue(all(0<=n<=10 for n in r['domain']))

    def test_distinct_entry_selection_defers_related_candidates(self):
        # Entry-level rejection and consumer mismatch are two candidates for one
        # entry. They must not consume both slots while another entry is ready.
        self.change('not 0 <= n <= 10','not 0 <= n <= 8')
        self.spec['entries']=self.spec['entries'][:2]
        report=self.run_plan()
        chosen=[r for r in self.relations if r['id'] in report['selected']]
        self.assertEqual(len({r['entry'] for r in chosen}),2)
        self.assertTrue(any(r['selection']=='same_entry_deferred' for r in self.relations))

    def test_all_predicted_unsafe_uses_direct_probe_without_fake_control(self):
        self.change('3 * n + 2','3 * n + 20')
        self.spec['entries']=self.spec['entries'][:1]
        report=self.run_plan(True)
        self.assertEqual(len(report['executions']),1)
        self.assertEqual(report['executions'][0]['mode'],'direct')
        self.assertEqual(report['executions'][0]['status'],'violation')
        self.assertEqual(report['executions'][0]['evaluations'],1)
        self.assertIsNone(next(r for r in self.relations if r['selection']=='selected')['control'])

    def test_premature_rejection_keeps_contract_valid_inputs(self):
        self.change('not 0 <= n <= 10','not 0 <= n <= 1')
        self.spec['entries']=self.spec['entries'][:1]
        report=self.run_plan(True)
        self.assertEqual(report['executions'][0]['status'],'counterexample')
        chosen=next(r for r in self.relations if r['id'] in report['selected'])
        self.assertIn('reject before',chosen['reason'])
        self.assertEqual(chosen['contract']['valid'],[[0,10]])

    def test_unknown_contract_and_unsupported_source_do_not_dispatch(self):
        for e in self.spec['entries']:e['expectation']='unknown'
        self.assertEqual(self.run_plan(True)['executions'],[])
        self.assertTrue(all(r['status']=='deferred' for r in self.relations))

    def test_unsupported_encoding_retains_partial_failure_no_execution(self):
        self.change("b'x' * (3 * n + 2)","('界' * n).encode('utf-8')")
        report=self.run_plan(True)
        self.assertEqual(report['executions'],[])
        self.assertTrue(any(r['status']=='unsupported' for r in self.relations))

    def test_independent_ready_entry_survives_unsupported_peer(self):
        self.change('return packet_a(encode(n))','return opaque(n)')
        report=self.run_plan(True)
        chosen={r['entry'] for r in self.relations if r['id'] in report['selected']}
        self.assertEqual(chosen,{'second'})
        self.assertEqual([e['status'] for e in report['executions']],['counterexample'])
        self.assertEqual(self.facts['first']['status'],'unsupported')

    def test_wrong_planner_coefficient_unit_and_route_are_blocked(self):
        for field,value in [('scale',1),('output_unit','character'),('reachable_intervals',[[0,0]])]:
            def corrupted(*args,**kwargs):
                p=real_plan(*args,**kwargs)
                for r in p['relations']:
                    if r['status']=='ready':
                        if field=='reachable_intervals':r[field]=value
                        else:r['model'][field]=value
                return p
            with tempfile.TemporaryDirectory() as tmp:
                with patch('investigation.plan',side_effect=corrupted):
                    report=investigation.run(self.spec,self.work,Path(tmp)/'out',True)
                self.assertEqual(report['executions'],[])

    def test_unchecked_planner_domain_is_not_executed(self):
        def corrupted(*args,**kwargs):
            p=real_plan(*args,**kwargs)
            for r in p['relations']:
                if r['status']=='ready':r['domain']=[999]
            return p
        with patch('investigation.plan',side_effect=corrupted):
            self.assertEqual(self.run_plan(True)['executions'],[])
        self.assertTrue(any('not source-checked' in r.get('reason','') for r in self.relations))

    def test_blocking_stops_dispatch_without_retry(self):
        with patch('investigation.search',return_value=dict(status='blocked',evaluations=1)) as engine:
            report=self.run_plan(True)
        self.assertEqual(engine.call_count,1)
        self.assertEqual(report['status'],'stopped')
        self.assertEqual(len(report['unexecuted_selected']),1)

    def test_engine_setup_exception_preserved_and_not_retried(self):
        with patch('investigation.search',side_effect=ValueError('setup failure')) as engine:
            report=self.run_plan(True)
        self.assertEqual(engine.call_count,1)
        self.assertEqual(report['status'],'stopped')
        self.assertEqual(len(report['unexecuted_selected']),1)
        rid=report['executions'][0]['id']
        self.assertEqual(json.loads((self.out/'executions'/rid/'failure.json').read_text())['reason'],'setup failure')

    def test_actual_execution_disagreement_is_blocked_not_bug(self):
        original=investigation.write
        def tamper(path,value):
            if path.name=='execution.json':
                value=copy.deepcopy(value)
                for row in value['fact_observations'].values():row['outcome']='impossible'
            original(path,value)
        with patch('investigation.write',side_effect=tamper):
            report=self.run_plan(True)
        self.assertEqual(report['status'],'stopped')
        self.assertEqual(len(report['executions']),1)
        self.assertEqual(report['executions'][0]['status'],'control_failed')
        rid=report['executions'][0]['id']
        observations=json.loads((self.out/'executions'/rid/'search/observations.json').read_text())
        self.assertEqual(observations[0]['result']['status'],'blocked')

    def test_budget_does_not_silently_truncate(self):
        self.spec['point_budget']=4
        report=self.run_plan(True)
        self.assertEqual(report['executions'],[])
        self.assertTrue(any(a['status']=='budget_blocked' for a in self.facts.values()))

    def test_renaming_equivalence_and_unrelated_function_move_preserve_discovery(self):
        self.change('packet_a','renamed_receiver')
        self.change('3 * n + 2','2 + n * 3')
        self.change("\n\ndef unused_consumer(packet):\n    if len(packet) > 7:\n        raise ValueError('unused')\n    return len(packet)\n",'')
        report=self.run_plan(True)
        chosen={r['entry'] for r in self.relations if r['id'] in report['selected']}
        self.assertEqual(chosen,{'first','second'})
        self.assertTrue(all(e['status']=='counterexample' for e in report['executions']))

    def test_provenance_unknown_fields_overwrite_and_no_source_output(self):
        self.spec['trusted_source_sha256']='0'*64
        with self.assertRaises(ValueError):self.run_plan(True)
        self.spec=json.loads((EXAMPLE/'request.json').read_text())
        self.spec['entries'][0]['suspicious_consumer']='packet_a'
        with self.assertRaises(ValueError):self.run_plan(True)
        del self.spec['entries'][0]['suspicious_consumer']
        self.run_plan()
        with self.assertRaises(ValueError):investigation.run(self.spec,self.work,self.out)
        with self.assertRaises(ValueError):investigation.run(self.spec,self.work,self.work/'out')
