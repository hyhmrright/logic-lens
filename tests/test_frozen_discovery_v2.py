"""Partial evidence must preserve missingness and remain inspectable after resumption."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
NAME = 'codex-discovery-v2-partial-2026-10-28'


class FrozenDiscoveryV2(unittest.TestCase):
    def test_partial_matrix_cannot_be_mistaken_for_completed_improvement(self):
        data = json.loads((ROOT / 'benchmarks/runs' / f'{NAME}.json').read_text())
        self.assertEqual(data['status'], 'incomplete')
        self.assertEqual(data['summary']['status'], 'incomplete')
        self.assertFalse(data['success_criteria']['passed'])
        self.assertEqual(len(data['protocol']['runs']), 72)
        self.assertEqual(len(data['runs']), 35)
        planned = {r['run_id'] for r in data['protocol']['runs']}
        completed = {r['run_id'] for r in data['runs']}
        self.assertLess(completed, planned)
        self.assertEqual(len(completed), len(data['runs']))
        self.assertEqual(len(data['failed_attempts']), 8)
        self.assertTrue(all(f['run_id'] in planned for f in data['failed_attempts']))
        for arm in ('plain', 'baseline', 'candidate'):
            rows = [r for r in data['protocol']['runs'] if r['arm'] == arm]
            self.assertEqual(len({(r['case_id'],r['variant'],r['repeat']) for r in rows}), 24)
        report_root = ROOT / 'benchmarks/reports' / NAME
        for arm in ('baseline', 'candidate'):
            self.assertEqual(hashlib.sha256((report_root / 'instructions' / f'{arm}.md').read_bytes()).hexdigest(),
                             data['protocol']['instruction_sha256'][arm])
        for row in data['runs']:
            self.assertEqual(hashlib.sha256((ROOT / 'benchmarks' / row['report']).read_bytes()).hexdigest(),
                             row['published_report_sha256'])
            self.assertTrue(set(row['judgment']['confirmed_additional']) <= set(data['additional_checks']))
            self.assertFalse(set(row['judgment']['confirmed_additional']) & set(data['unestablished_probe_oracles']))
        for field, filename in [('target_probe_source_sha256','probes_v2.py'),
                                ('additional_probe_source_sha256','additional_probes_v2.py')]:
            self.assertEqual(data[field], hashlib.sha256((report_root / 'evaluator' / filename).read_bytes()).hexdigest())
        for pair in data['target_checks'].values():
            self.assertEqual(pair['buggy']['returncode'], 1)
            self.assertEqual(pair['fixed']['returncode'], 0)


if __name__ == '__main__':
    unittest.main()
