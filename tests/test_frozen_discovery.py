"""Validate that published evidence can be inspected without local run artifacts."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent.parent


class FrozenDiscoveryEvidence(unittest.TestCase):
    def test_complete_matched_matrix_and_published_report_checksums(self):
        data=json.loads((ROOT/'benchmarks/runs/codex-discovery-2026-10-28.json').read_text())
        self.assertEqual(len(data['runs']),72)
        self.assertEqual(len({r['run_id'] for r in data['runs']}),72)
        for arm in ('plain','baseline','candidate'):
            rows=[r for r in data['runs'] if r['arm']==arm]
            self.assertEqual(len(rows),24)
            self.assertEqual(len({(r['case_id'],r['variant'],r['repeat']) for r in rows}),24)
            if arm!='plain':
                instructions=ROOT/f'benchmarks/reports/codex-discovery-2026-10-28/instructions/{arm}.md'
                self.assertEqual(hashlib.sha256(instructions.read_bytes()).hexdigest(),
                                 data['protocol']['instruction_sha256'][arm])
        known_checks={c['behavior'] for c in data['additional_checks']}
        for row in data['runs']:
            report=ROOT/'benchmarks'/row['report']
            self.assertEqual(hashlib.sha256(report.read_bytes()).hexdigest(),row['published_report_sha256'])
            self.assertTrue(set(row['judgment']['confirmed_additional'])<=known_checks)
        self.assertEqual(data['additional_probe_source_sha256'],
                         hashlib.sha256((ROOT/'evals/discovery/discovered_checks.py').read_bytes()).hexdigest())


if __name__=='__main__':unittest.main()
