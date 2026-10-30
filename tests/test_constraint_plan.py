"""Synthetic actual-program checks for the offline relation planner; no model calls."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from constraint_plan import plan

EXAMPLE = ROOT / 'examples/constraint-plan'


class ConstraintPlanning(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((EXAMPLE / 'relations.json').read_text())
        self.card = self.spec['relations'][0]
        self.workspace = EXAMPLE / 'workspace'

    def function_ref(self, name):
        import ast
        text = (self.workspace / 'pipeline.py').read_text()
        node = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == name)
        return dict(path='pipeline.py', start=node.lineno, end=node.end_lineno,
                    quote='\n'.join(text.splitlines()[node.lineno-1:node.end_lineno]))

    def subject(self):
        module = importlib.util.spec_from_file_location('synthetic_pipeline', self.workspace / 'pipeline.py')
        pipeline = importlib.util.module_from_spec(module)
        module.loader.exec_module(pipeline)
        return pipeline

    def result(self):
        return plan(self.spec, self.workspace)['relations'][0]

    def test_unit_inverse_hits_actual_program_boundary(self):
        r = self.result()
        self.assertEqual(r['boundary_status'], 'reachable_crossing')
        self.assertTrue({4, 5, 6} <= set(r['domain']))
        self.assertNotIn(17, r['domain'])
        module = importlib.util.spec_from_file_location('synthetic_pipeline', self.workspace / 'pipeline.py')
        pipeline = importlib.util.module_from_spec(module)
        module.loader.exec_module(pipeline)
        self.assertEqual(pipeline.transfer(r['control']), 2)
        self.assertEqual(pipeline.transfer(5), 17)
        with self.assertRaises(ValueError):
            pipeline.transfer(6)
        self.assertEqual(len(pipeline.encode(6)), 20)
        actual_safe, actual_unsafe = [], []
        for n in r['domain']:
            try:
                pipeline.transfer(n)
                actual_safe.append(n)
            except ValueError:
                actual_unsafe.append(n)
        self.assertEqual(actual_safe, r['predicted_safe'])
        self.assertEqual(actual_unsafe, r['predicted_unsafe'])
        # Correct alternate routing handles the same public input. A consumer
        # obligation cannot be applied to an input that never reaches it.
        self.assertEqual(pipeline.routed_transfer(6), 20)

    def test_route_excludes_unreachable_boundary_and_does_not_claim_pass(self):
        self.card['route']['guard'] = [[0, 5]]
        self.card['route']['source'] = self.function_ref('routed_transfer')
        r = self.result()
        self.assertEqual(r['boundary_status'], 'all_predicted_safe')
        self.assertEqual(r['selection'], 'not_eligible')
        self.assertTrue(all(0 <= n <= 5 for n in r['domain']))
        self.assertNotIn('verified', r)
        self.assertEqual(r['control_status'], 'predicted_only_requires_execution')
        self.assertTrue(all(self.subject().routed_transfer(n) == 3*n+2 for n in range(11)))

    def test_empty_route(self):
        self.card['route']['guard'] = [[11, 20]]
        self.card['route']['source'] = self.function_ref('unreachable_transfer')
        self.assertTrue(all(self.subject().unreachable_transfer(n) == 3*n+2 for n in range(11)))
        self.assertEqual(self.result()['status'], 'unreachable')
        self.assertEqual(self.result()['domain'], [])

    def test_valid_domain_holes_and_guard_intersection(self):
        self.card['input']['valid'] = [[0, 2], [7, 10]]
        self.card['route']['guard'] = [[1, 8]]
        r = self.result()
        self.assertEqual(r['reachable_intervals'], [(1, 2), (7, 8)])
        self.assertEqual(r['domain'], [1, 2, 7, 8])

    def test_negative_scale_and_negative_inputs_exactly(self):
        self.card['input']['valid'] = [[-10, 10]]
        self.card['route']['guard'] = [[-10, 10]]
        self.card['contract']['claims'][0]['scope'] = [[-10, 10]]
        self.card['producer'].update(scale=-3, offset=2)
        r = self.result()
        self.assertTrue({-6, -5, -4} <= set(r['domain']))
        self.assertIn(-6, r['predicted_unsafe'])
        self.assertIn(-5, r['predicted_safe'])

    def test_no_passing_control_is_not_dispatched(self):
        self.card['consumer']['bound'] = -1
        r = self.result()
        self.assertEqual(r['boundary_status'], 'all_predicted_unsafe')
        self.assertIsNone(r['control'])
        self.assertEqual(r['selection'], 'not_eligible')

    def test_computed_contract_conflict_blocks_search(self):
        self.card['contract']['claims'].append(dict(effect='deny', scope=[[6, 10]],
            source=dict(path='pipeline.py', start=3, end=3,
                        quote=(self.workspace / 'pipeline.py').read_text().splitlines()[2])))
        r = self.result()
        self.assertEqual(r['reason'], 'overlapping_contract_conflict')
        self.assertEqual(r['conflict_intervals'], [(6, 10)])
        self.assertEqual(r['selection'], 'not_eligible')
        # A conflict on a different route does not invalidate this route.
        self.card['route']['guard'] = [[0, 5]]
        self.assertEqual(self.result()['status'], 'ready')

    def test_contract_scope_gap_and_denied_valid_domain(self):
        self.card['contract']['claims'][0]['scope'] = [[0, 5]]
        self.assertEqual(self.result()['reason'], 'contract_scope_gap')
        self.card['contract']['claims'].append(dict(effect='deny', scope=[[6, 10]],
            source=dict(path='pipeline.py', start=3, end=3,
                        quote=(self.workspace / 'pipeline.py').read_text().splitlines()[2])))
        self.assertEqual(self.result()['reason'], 'declared_valid_domain_includes_denied_input')

    def test_unknown_contract_and_unsupported_model_or_unit(self):
        for status in ('unknown', 'conflict'):
            self.card['contract']['status'] = status
            self.assertEqual(self.result()['status'], 'unresolved')
        self.card['contract']['status'] = 'supported'
        self.card['producer']['output_unit'] = 'character'
        self.assertEqual(self.result()['reason'], 'unit_mismatch')
        self.card['producer']['output_unit'] = 'byte'
        self.card['producer']['kind'] = 'nonlinear'
        self.assertEqual(self.result()['status'], 'unsupported')

    def test_selection_preserves_distinct_edges_before_cost(self):
        duplicate = copy.deepcopy(self.card)
        duplicate['id'] = 'b-nearby-same-edge'
        lines = (self.workspace / 'pipeline.py').read_text().splitlines()
        duplicate['consumer']['source'] = dict(path='pipeline.py', start=13, end=15,
            quote='\n'.join(lines[12:15]))
        distinct = copy.deepcopy(self.card)
        distinct['id'] = 'z-distinct-edge'
        # Different actual consumer source span means a different sourced edge.
        lines = (self.workspace / 'pipeline.py').read_text().splitlines()
        distinct['consumer']['source'] = dict(path='pipeline.py', start=33, end=36,
            quote='\n'.join(lines[32:36]))
        self.card['id'] = 'a-first'
        self.spec['relations'].extend([duplicate, distinct])
        p = plan(self.spec, self.workspace)
        self.assertEqual(p['selected'], ['a-first', 'z-distinct-edge'])
        self.assertEqual(p['relations'][1]['selection'], 'same_edge_deferred')
        self.spec['search_slots'] = 1
        self.assertEqual(plan(self.spec, self.workspace)['selected'], ['a-first'])

    def test_selection_does_not_fill_slots_with_invalid_candidates(self):
        duplicate = copy.deepcopy(self.card)
        duplicate['id'] = 'unresolved'
        duplicate['contract']['status'] = 'unknown'
        self.spec['relations'].append(duplicate)
        self.assertEqual(plan(self.spec, self.workspace)['selected'], ['packet-capacity'])

    def test_matching_quote_does_not_prove_declared_semantics(self):
        # Deliberate negative control: accurate source quote, inaccurate annotation.
        # Planner cannot infer the coefficient; document rather than hide this gap.
        self.card['producer']['scale'] = 1
        r = self.result()
        self.assertEqual(r['boundary_status'], 'all_predicted_safe')
        self.assertEqual(r['selection'], 'not_eligible')
        with self.assertRaises(ValueError):
            self.subject().transfer(6)

    def test_domain_budget_does_not_silently_drop_boundary_points(self):
        self.spec['max_domain_points'] = 2
        r = self.result()
        self.assertEqual(r['status'], 'budget_blocked')
        self.assertEqual(r['selection'], 'not_eligible')
        self.assertTrue({4, 5, 6} <= set(r['domain']))

    def test_quotes_paths_types_and_limits_fail_closed(self):
        for mutate in [lambda c: c['producer']['source'].update(quote='wrong'),
                       lambda c: c['consumer']['source'].update(path='../outside'),
                       lambda c: c['producer'].update(scale=True),
                       lambda c: c['input'].update(valid=[[4, 2]])]:
            self.setUp()
            mutate(self.card)
            with self.assertRaises(ValueError):
                self.result()
        self.setUp()
        self.spec['search_slots'] = 5
        with self.assertRaises(ValueError):
            self.result()

    def test_small_affine_partitions_match_independent_exhaustive_domain(self):
        # An independent finite enumeration is the oracle for generated partition
        # coverage. This says nothing about extracting these facts from real code.
        for scale in (-3, -1, 1, 3):
            for offset in (-2, 0, 2):
                for bound in (-8, 0, 8):
                    self.card['input']['valid'] = [[-6, -2], [0, 6]]
                    self.card['route']['guard'] = [[-5, 5]]
                    self.card['contract']['claims'][0]['scope'] = [[-6, 6]]
                    self.card['producer'].update(scale=scale, offset=offset)
                    self.card['consumer']['bound'] = bound
                    r = self.result()
                    valid = [n for n in range(-5, 6) if n <= -2 or n >= 0]
                    self.assertEqual({scale*n+offset <= bound for n in r['domain']},
                                     {scale*n+offset <= bound for n in valid})
                    self.assertTrue(set(r['domain']) <= set(valid))

    def test_portable_cli_preserves_source_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'plan.json'
            before = (self.workspace / 'pipeline.py').read_bytes()
            command = [sys.executable, str(ROOT / 'scripts/logic_lens.py'), 'constraints',
                '--spec', str(EXAMPLE / 'relations.json'), '--workspace', str(self.workspace), '--out', str(out)]
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)['selected'], ['packet-capacity'])
            original = out.read_bytes()
            repeat = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(repeat.returncode, 2)
            self.assertEqual(out.read_bytes(), original)
            self.assertEqual((self.workspace / 'pipeline.py').read_bytes(), before)
            command[-1] = str(self.workspace / 'must-not-write.json')
            denied = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(denied.returncode, 2)
            self.assertFalse((self.workspace / 'must-not-write.json').exists())
