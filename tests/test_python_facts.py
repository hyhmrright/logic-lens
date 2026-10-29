"""Bounded AST facts checked against actual safe synthetic programs, without models."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from python_facts import analyze

SUBJECT = (ROOT / 'examples/constraint-plan/workspace/pipeline.py').read_text()


class PythonFacts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'pipeline.py').write_text(SUBJECT)
        self.spec = json.loads((ROOT / 'examples/python-facts/check.json').read_text())

    def result(self, source=None):
        if source is not None:
            (self.root / 'pipeline.py').write_text(source)
        return analyze(self.spec, self.root)

    def test_correct_declarations_with_business_units_unknown(self):
        r = self.result()
        self.assertEqual(r['status'], 'checked_with_unknowns')
        for field in ('scale', 'offset', 'route', 'output_unit', 'bound'):
            self.assertEqual(r['checks'][field]['status'], 'matched_in_scope')
        self.assertEqual(r['checks']['input_business_unit']['status'], 'unknown')
        self.assertEqual(r['facts']['reachable'], [[0, 5]])
        self.assertEqual(r['facts']['rejected_before_consumer'], [[-1, -1], [11, 11]])

    def test_wrong_coefficient_from_previous_negative_control_is_rejected(self):
        self.spec['entry'] = 'transfer'
        self.spec['declaration']['route'] = [[0, 10]]
        self.spec['declaration']['scale'] = 1
        r = self.result()
        self.assertEqual(r['status'], 'mismatch')
        self.assertEqual(r['checks']['scale']['status'], 'mismatch')
        witness = r['checks']['scale']['witness']
        self.assertNotEqual(witness['observed'], witness['declared_quantity'])
        self.assertEqual(r['facts']['variants'], [dict(scale=3, offset=2, unit='byte')])

    def test_offset_reassignment_constant_fold_and_equivalent_expression(self):
        source = SUBJECT.replace("return b'x' * (3 * n + 2)",
            "k = 9\n    k = 1 + 2\n    return b'x' * (2 + n * k)")
        self.assertEqual(self.result(source)['checks']['scale']['status'], 'matched_in_scope')
        self.spec['declaration']['offset'] = 1
        self.assertEqual(self.result()['checks']['offset']['status'], 'mismatch')

    def test_byte_literal_length_changes_both_coefficients(self):
        r = self.result(SUBJECT.replace("b'x'", "b'xy'"))
        self.assertEqual(r['facts']['variants'], [dict(scale=6, offset=4, unit='byte')])
        self.assertEqual(r['checks']['scale']['status'], 'mismatch')
        self.assertEqual(r['checks']['offset']['status'], 'mismatch')

    def test_character_and_byte_representation_mismatch(self):
        r = self.result(SUBJECT.replace("b'x'", "'界'"))
        self.assertEqual(r['checks']['output_unit']['status'], 'mismatch')
        self.assertEqual(r['checks']['output_unit']['observed'], ['character'])
        self.spec['declaration']['output_unit'] = 'character'
        self.assertEqual(self.result()['checks']['output_unit']['status'], 'matched_in_scope')
        self.spec['declaration']['output_unit'] = 'millisecond'
        self.assertEqual(self.result()['checks']['output_unit']['status'], 'unknown')

    def test_encoding_nonlinear_and_dynamic_calls_are_unsupported(self):
        for expression in ["('界' * n).encode('utf-8')", "b'x' * (n*n)", "factory(n)"]:
            r = self.result(SUBJECT.replace("b'x' * (3 * n + 2)", expression))
            self.assertEqual(r['status'], 'unsupported')
            self.assertNotIn('checks', r)

    def test_omitted_reachable_and_false_reachable_routes(self):
        self.spec['declaration']['route'] = [[0, 3]]
        r = self.result()
        self.assertEqual(r['checks']['route']['omitted_reachable'], [[4, 5]])
        self.spec['declaration']['route'] = [[0, 10]]
        self.assertEqual(self.result()['checks']['route']['falsely_reachable'], [[6, 10]])

    def test_rejecting_entry_does_not_change_contract_validity(self):
        self.spec['declaration']['route'] = [[0, 10]]
        r = self.result(SUBJECT.replace('not 0 <= n <= 10', 'not 0 <= n <= 3'))
        self.assertEqual(r['facts']['rejected_before_consumer'], [[-1, -1], [4, 11]])
        self.assertEqual(r['checks']['route']['falsely_reachable'], [[4, 10]])
        self.assertNotIn('valid', r['facts'])
        self.assertIn('does not redefine', r['contract'])

    def test_nested_branch_and_early_return(self):
        source = SUBJECT.replace('if n <= 5:\n        return consume(encode(n))',
            'if n > 5:\n        return len(encode(n))\n    if n != 2:\n        return consume(encode(n))')
        r = self.result(source)
        self.assertEqual(r['facts']['reachable'], [[0, 1], [3, 5]])
        self.assertEqual(r['checks']['route']['falsely_reachable'], [[2, 2]])

    def test_unreachable_retains_unknown_coefficient_not_false_match(self):
        self.spec['entry'] = 'unreachable_transfer'
        self.spec['declaration']['route'] = []
        r = self.result()
        self.assertEqual(r['facts']['reachable'], [])
        self.assertEqual(r['checks']['scale']['status'], 'unknown')
        self.assertEqual(r['checks']['route']['status'], 'matched_in_scope')

    def test_negative_repetition_not_extrapolated(self):
        self.spec['analysis_domain'] = [-2, 2]
        self.spec['entry'] = 'transfer'
        source = SUBJECT.replace('if type(n) is not int or not 0 <= n <= 10:',
                                 'if type(n) is not int:')
        r = self.result(source)
        self.assertIn(dict(scale=0, offset=0, unit='byte'), r['facts']['variants'])
        self.assertEqual(r['checks']['scale']['status'], 'mismatch')
        negative = next(o for o in r['observations'] if o['input'] == -2)
        self.assertEqual(negative['consumers'][0]['quantity'], 0)

    def test_builtin_and_function_shadowing_are_not_silently_resolved(self):
        for source in [SUBJECT + '\nlen = 1\n', SUBJECT.replace('return consume(encode(n))',
            'encode = 3\n    return consume(encode(n))'),
            SUBJECT.replace('def encode(n):', 'def encode(len):')]:
            self.assertEqual(self.result(source)['status'], 'unsupported')

    def test_scope_not_chosen_from_declaration_and_singleton_no_fake_witness(self):
        self.spec['declaration']['route'] = [[100, 100]]
        self.assertEqual(self.result()['facts']['reachable'], [[0, 5]])
        self.spec['analysis_domain'] = [0, 0]
        self.spec['declaration']['scale'] = 1
        r = self.result()
        self.assertEqual(r['checks']['scale']['status'], 'mismatch')
        self.assertIsNone(r['checks']['scale']['witness'])

    def test_unknown_unsupported_and_budgets(self):
        for source in ['import os\n'+SUBJECT, SUBJECT.replace('def encode(n):', 'def encode(n: int):'),
                       SUBJECT.replace("return b'x' * (3 * n + 2)", 'return encode(n)'),
                       SUBJECT.replace("return b'x' * (3 * n + 2)", 'while n > 0:\n        n = n - 1\n    return n')]:
            self.assertEqual(self.result(source)['status'], 'unsupported')
        self.spec['analysis_domain'] = [0, 128]
        with self.assertRaises(ValueError):
            self.result(SUBJECT)

    def test_independent_actual_execution_matches_every_interpreted_input(self):
        # Only trusted synthetic programs run, in terminable subprocesses. No
        # statement from a user declaration enters the independent observation.
        variants = [SUBJECT, SUBJECT.replace("b'x'", "b'xy'"), SUBJECT.replace("b'x'", "'界'"),
                    SUBJECT.replace('if n <= 5:', 'if n >= 3:')]
        for source in variants:
            r = self.result(source)
            command = source + '''
import json
seen=[]
original=consume
def observed(packet):
    seen.append(dict(unit='byte' if type(packet) is bytes else 'character',quantity=len(packet)))
    return original(packet)
consume=observed
rows=[]
for n in range(-1,12):
    seen=[]
    outcome='returned'
    try: routed_transfer(n)
    except ValueError: outcome='rejected_after_consumer' if seen else 'rejected_before_consumer'
    rows.append(dict(input=n,outcome=outcome,consumers=seen))
print(json.dumps(rows))
'''
            actual = subprocess.run([sys.executable, '-c', command], capture_output=True, text=True, timeout=5)
            self.assertEqual(actual.returncode, 0, actual.stderr)
            expected = json.loads(actual.stdout)
            reduced = [dict(input=o['input'],outcome=o['outcome'],consumers=[dict(unit=e['unit'],quantity=e['quantity']) for e in o['consumers']]) for o in r['observations']]
            self.assertEqual(reduced, expected)

    def test_cli_artifacts_overwrite_and_no_subject_execution(self):
        spec = self.root / 'check.json'
        spec.write_text(json.dumps(self.spec))
        out = self.root.parent / (self.root.name + '-facts.json')
        self.addCleanup(lambda: out.unlink(missing_ok=True))
        command = [sys.executable, str(ROOT / 'scripts/logic_lens.py'), 'facts', '--spec', str(spec),
                   '--workspace', str(self.root), '--out', str(out)]
        first = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        before = out.read_bytes()
        self.assertEqual(subprocess.run(command,capture_output=True).returncode, 2)
        self.assertEqual(out.read_bytes(), before)
        command[-1] = str(self.root / 'forbidden.json')
        self.assertEqual(subprocess.run(command,capture_output=True).returncode, 2)
        self.assertFalse((self.root / 'forbidden.json').exists())
        # Module-level side effects are unsupported and never executed by analyze.
        marker = self.root / 'not-created'
        r = self.result(SUBJECT + f'\nopen({str(marker)!r}, "w").write("bad")\n')
        self.assertEqual(r['status'], 'unsupported')
        self.assertFalse(marker.exists())
