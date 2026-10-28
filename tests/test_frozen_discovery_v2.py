"""Partial evidence must preserve missingness and remain inspectable after resumption."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
NAME = 'codex-discovery-v2-partial-2026-10-28'


class FrozenDiscoveryV2(unittest.TestCase):
    def test_final_matrix_preserves_failures_and_recomputes_no_gain(self):
        name = 'codex-discovery-v2-final-2026-10-28'
        data = json.loads((ROOT / 'benchmarks/runs' / f'{name}.json').read_text())
        self.assertEqual(data['status'], 'complete')
        self.assertEqual(data['summary']['status'], 'complete')
        rows = data['runs']
        self.assertEqual(len(rows), 72)
        self.assertEqual({r['run_id'] for r in rows},
                         {r['run_id'] for r in data['protocol']['runs']})
        for row in rows:
            self.assertEqual(hashlib.sha256((ROOT / 'benchmarks' / row['report']).read_bytes()).hexdigest(),
                             row['published_report_sha256'])
            self.assertTrue(set(row['judgment']['confirmed_additional']) <= set(data['additional_checks']))
            self.assertFalse(set(row['judgment']['confirmed_additional']) & set(data['unestablished_probe_oracles']))
        for arm in ('plain', 'baseline', 'candidate'):
            hits = sum(r['judgment']['target_detected'] for r in rows
                       if r['arm'] == arm and r['variant'] == 'buggy')
            self.assertEqual(hits, 9)
            self.assertEqual(hashlib.sha256((ROOT / 'benchmarks/reports' / name /
                             'instructions' / f'{arm}.md').read_bytes()).hexdigest(),
                             data['protocol']['instruction_sha256'][arm])
        self.assertFalse(data['success_criteria']['passed'])
        failures = data['failed_attempts']
        self.assertEqual(len(failures), 14)
        counts = {}
        for failure in failures:
            key = failure['run_id']
            counts[key] = counts.get(key, 0) + 1
        self.assertEqual(len(counts), 13)
        self.assertLessEqual(max(counts.values()) + 1, 3)
        self.assertEqual(sum(v['completed'] for v in data['first_attempt_delivery'].values()), 59)
        known = [f['terminal_usage'] for f in failures if f['terminal_usage']]
        self.assertEqual(len(known), 2)
        self.assertEqual(sum(u['input_tokens'] for u in known), 911091)
        self.assertEqual(sum(u['output_tokens'] for u in known), 20446)
        for field, filename in [('target_probe_source_sha256', 'probes_v2.py'),
                                ('additional_probe_source_sha256', 'additional_probes_v2.py')]:
            self.assertEqual(data[field], hashlib.sha256((ROOT / 'benchmarks/reports' / name /
                             'evaluator' / filename).read_bytes()).hexdigest())

    def test_recovery_checkpoint_preserves_reports_and_honest_missingness_bounds(self):
        name = 'codex-discovery-v2-checkpoint-2026-10-28-62'
        data = json.loads((ROOT / 'benchmarks/runs' / f'{name}.json').read_text())
        self.assertEqual(data['status'], 'incomplete')
        rows = data['runs']
        self.assertEqual(len(rows), 62)
        self.assertEqual(len({r['run_id'] for r in rows}), 62)
        self.assertEqual(len(data['failed_attempts']), 14)
        for row in rows:
            self.assertEqual(hashlib.sha256((ROOT / 'benchmarks' / row['report']).read_bytes()).hexdigest(),
                             row['published_report_sha256'])
            self.assertTrue(set(row['judgment']['confirmed_additional']) <= set(data['additional_checks']))
            self.assertFalse(set(row['judgment']['confirmed_additional']) & set(data['unestablished_probe_oracles']))
        buggy = [r for r in rows if r['variant'] == 'buggy']
        plain = [r for r in buggy if r['arm'] == 'plain']
        candidate = [r for r in buggy if r['arm'] == 'candidate']
        self.assertEqual(len(plain), 12)
        plain_hits = sum(r['judgment']['target_detected'] for r in plain)
        candidate_max = sum(r['judgment']['target_detected'] for r in candidate) + 12 - len(candidate)
        self.assertLess(candidate_max - plain_hits, data['success_criteria']['minimum_extra_target_detections'])
        self.assertFalse(data['success_criteria']['passed'])
        report_root = ROOT / 'benchmarks/reports' / name
        for field, filename in [('target_probe_source_sha256', 'probes_v2.py'),
                                ('additional_probe_source_sha256', 'additional_probes_v2.py')]:
            self.assertEqual(data[field], hashlib.sha256((report_root / 'evaluator' / filename).read_bytes()).hexdigest())
        for variant in ('buggy', 'fixed'):
            self.assertNotEqual(data['additional_checks']['dateutil-ordinal-space'][variant]['returncode'], 0)

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
