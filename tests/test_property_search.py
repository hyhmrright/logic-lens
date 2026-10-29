"""Offline behavioral checks for bounded property search; no coding-model calls."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'scripts'))
from property_search import run


class PropertySearch(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root/'workspace'
        self.definition = self.root/'definition'
        shutil.copytree(ROOT/'examples/property-search/workspace', self.work)
        shutil.copytree(ROOT/'examples/property-search', self.definition,
                        ignore=shutil.ignore_patterns('workspace', '__pycache__'))
        self.spec = json.loads((self.definition/'property.json').read_text())
        self.adapter = self.definition/'adapter.py'
        self.out = self.root/'result'

    def search(self):
        p = self.definition/'property.json'
        p.write_text(json.dumps(self.spec))
        return run(p, self.work, self.out)

    def replace_adapter(self, body):
        self.adapter.write_text('import json,sys\n'
            'case=json.load(sys.stdin)["case"]\n' + body)

    def test_correct_implementation_exhausts_small_domain_and_records_hashes(self):
        before = (self.work/'axis.py').read_bytes()
        result = self.search()
        self.assertEqual(result['status'], 'exhausted')
        self.assertEqual(result['evaluations'], 10)
        self.assertEqual(result['counts']['pass_count'], 10)
        self.assertIsNone(result['counterexample'])
        self.assertEqual((self.work/'axis.py').read_bytes(), before)
        manifest = json.loads((self.out/'sha256.json').read_text())
        for name, expected in manifest.items():
            self.assertEqual(hashlib.sha256((self.out/name).read_bytes()).hexdigest(), expected)
        self.assertIn('adapter/adapter.py', manifest)
        self.assertIn('spec.json', manifest)

    def test_real_defect_is_found_reduced_and_disappears_after_fix(self):
        source = self.work/'axis.py'
        original = source.read_text()
        source.write_text(original.replace('position + delta', 'position + abs(delta)'))
        self.spec['seed'] = 0
        self.spec['domains']['delta'] = [0, 1, 3, 5]
        result = self.search()
        self.assertEqual(result['status'], 'counterexample')
        self.assertEqual(result['counterexample']['case'], {'origin': 0, 'delta': 1})
        self.assertEqual(result['counterexample']['result']['observation'], {'expected': 0, 'actual': 2})
        rows = json.loads((self.out/'observations.json').read_text())
        self.assertTrue(any(r['phase']=='shrink' for r in rows))
        self.assertLessEqual(len(rows), 16)
        source.write_text(original)
        self.out = self.root/'fixed-result'
        self.assertEqual(self.search()['status'], 'exhausted')

    def test_sampling_is_reproducible_control_first_and_not_exhaustive(self):
        self.spec['domains'] = {'origin': list(range(20)), 'delta': list(range(20))}
        self.spec['limits']['max_cases'] = 4
        first = self.search()
        rows = json.loads((self.out/'observations.json').read_text())
        self.assertEqual(first['status'], 'sampled')
        self.assertEqual(rows[0]['phase'], 'control')
        self.assertEqual(rows[0]['case'], self.spec['control'])
        cases = [r['case'] for r in rows]
        self.assertEqual(len({json.dumps(c, sort_keys=True) for c in cases}), 4)
        self.out = self.root/'second'
        self.search()
        self.assertEqual(cases, [r['case'] for r in json.loads((self.out/'observations.json').read_text())])

    def test_shrinking_shares_total_invocation_budget(self):
        p = self.work/'axis.py'
        p.write_text(p.read_text().replace('position + delta', 'position + abs(delta)'))
        self.spec['limits'].update(max_cases=2, shrink_cases=32)
        result = self.search()
        self.assertEqual(result['status'], 'counterexample')
        self.assertEqual(result['evaluations'], 2)

    def test_adapter_invalid_input_is_not_a_violation_or_a_pass(self):
        self.replace_adapter('print(json.dumps(dict(status="invalid",reason="fixture domain filter") if case["delta"] < 0 else dict(status="pass",observation=case,sources=["axis.py"])))\n')
        result = self.search()
        self.assertEqual(result['counts']['invalid'], 4)
        self.assertEqual(result['counts']['pass_count'], 6)
        self.assertEqual(result['counts']['violation'], 0)

    def test_failed_control_does_not_start_search_or_claim_a_bug(self):
        self.replace_adapter('print(json.dumps(dict(status="violation",observation=case,sources=["axis.py"])))\n')
        result = self.search()
        self.assertEqual(result['status'], 'control_failed')
        self.assertEqual(result['evaluations'], 1)
        self.assertIsNone(result['counterexample'])

    def test_adapter_crash_is_blocked_not_a_behavioral_defect(self):
        self.replace_adapter('raise SystemExit(7)\n')
        result = self.search()
        self.assertEqual(result['status'], 'control_failed')
        row = json.loads((self.out/'observations.json').read_text())[0]
        self.assertEqual(row['result'], {'status':'blocked','reason':'adapter exit 7'})
        self.assertEqual(result['counts']['violation'], 0)

    def test_timeout_uses_global_remaining_time(self):
        self.replace_adapter('import time\ntime.sleep(30)\n')
        self.spec['limits'].update(seconds=1, case_seconds=10)
        start = time.monotonic()
        result = self.search()
        self.assertLess(time.monotonic()-start, 4)
        self.assertEqual(result['status'], 'control_failed')
        self.assertEqual(result['counts']['blocked'], 1)
        self.assertEqual(json.loads((self.out/'observations.json').read_text())[0]['result']['reason'], 'timeout')

    def test_excessive_output_is_stopped_and_retained_output_is_capped(self):
        self.replace_adapter('print("x"*100000)\n')
        self.spec['limits']['output_bytes'] = 256
        result = self.search()
        self.assertEqual(result['counts']['blocked'], 1)
        for p in (self.out/'cases').rglob('*.txt'):
            self.assertLessEqual(p.stat().st_size, 256)
        row = json.loads((self.out/'observations.json').read_text())[0]
        self.assertEqual(row['result']['reason'], 'output_limit')

    def test_missing_provenance_and_malformed_json_are_blocked(self):
        for index, body in enumerate(['print("not json")\n', 'print(json.dumps(dict(status="pass",observation=1)))\n']):
            self.out = self.root/f'bad-{index}'
            self.replace_adapter(body)
            result = self.search()
            self.assertEqual(result['counts']['blocked'], 1)
            self.assertIsNone(result['counterexample'])

    def test_source_mutation_is_detected_in_copy_and_original_is_preserved(self):
        before = (self.work/'axis.py').read_bytes()
        self.replace_adapter('from pathlib import Path\nPath("axis.py").write_text("changed")\nprint(json.dumps(dict(status="pass",observation=0,sources=["axis.py"])))\n')
        result = self.search()
        self.assertEqual(result['status'], 'integrity_failure')
        self.assertEqual((self.work/'axis.py').read_bytes(), before)
        self.assertIsNone(result['counterexample'])

    def test_invalid_contract_control_and_limits_fail_before_execution(self):
        good = json.loads(json.dumps(self.spec))
        for modification in ['quote', 'control', 'budget']:
            self.spec = json.loads(json.dumps(good))
            if modification == 'quote':
                self.spec['contract'][0]['quote'] = 'an invented contract'
            elif modification == 'control':
                self.spec['control']['delta'] = 100
            else:
                self.spec['limits']['max_cases'] = True
            with self.assertRaises(ValueError):
                self.search()
            self.assertFalse(self.out.exists())

    def test_refuses_overwrite_and_workspace_nested_output(self):
        self.search()
        with self.assertRaises(FileExistsError):
            self.search()
        self.out = self.work/'result'
        with self.assertRaises(ValueError):
            self.search()

    @unittest.skipUnless(shutil.which('node'), 'Node.js is optional')
    def test_command_protocol_can_probe_a_real_javascript_module(self):
        (self.work/'axis.js').write_text('exports.move = (p, d) => p + d\n')
        (self.definition/'adapter.js').write_text(
            'const fs=require("node:fs"), path=require("node:path");\n'
            'const axis=require(path.join(process.cwd(),"axis.js"));\n'
            'const c=JSON.parse(fs.readFileSync(0,"utf8")).case;\n'
            'const actual=axis.move(axis.move(c.origin,c.delta),-c.delta);\n'
            'console.log(JSON.stringify({status:actual===c.origin?"pass":"violation",'
            'observation:{actual},sources:["axis.js"]}));\n')
        self.spec['adapter'] = {'files':['adapter.js'], 'argv':['node','{adapter_dir}/adapter.js']}
        result = self.search()
        self.assertEqual(result['status'], 'exhausted')
        self.assertEqual(result['counts']['pass_count'], 10)

    def test_cli_does_not_dump_large_witness_into_model_context(self):
        self.replace_adapter('print(json.dumps(dict(status="pass" if case["delta"]==0 else "violation",observation="x"*3000,sources=["axis.py"])))\n')
        self.spec['domains'] = {'origin':[0], 'delta':[0,1], 'padding':['y'*3000]}
        self.spec['control']['padding'] = 'y'*3000
        spec = self.definition/'property.json'
        spec.write_text(json.dumps(self.spec))
        proc = subprocess.run([sys.executable,str(ROOT/'scripts/logic_lens.py'),'search',
            '--workspace',str(self.work),'--spec',str(spec),'--out',str(self.out)],
            capture_output=True,text=True,timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertLess(len(proc.stdout.encode()), 4096)
        compact = json.loads(proc.stdout)
        self.assertEqual(compact['status'], 'counterexample')
        self.assertEqual(compact['counterexample']['details'], 'summary.json')
        full = json.loads((self.out/'summary.json').read_text())
        self.assertEqual(len(full['counterexample']['case']['padding']), 3000)

    def test_external_source_claim_is_not_accepted(self):
        self.replace_adapter('print(json.dumps(dict(status="violation",observation=0,sources=["../outside.py"])))\n')
        result = self.search()
        self.assertEqual(result['counts']['blocked'], 1)
        self.assertIsNone(result['counterexample'])


if __name__ == '__main__':
    unittest.main()
