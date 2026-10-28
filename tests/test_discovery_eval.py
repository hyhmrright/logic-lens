"""Regression tests for blindness, provenance, and honest incomplete-run metrics."""
import importlib.util
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from llm_runner import parse_codex, parse_command, parallel_map
SPEC = importlib.util.spec_from_file_location('discovery_eval', ROOT / 'scripts/discovery_eval.py')
discovery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(discovery)


class TestBlindSnapshots(unittest.TestCase):
    def test_fixed_overlay_keeps_parent_tests_and_hides_history(self):
        with tempfile.TemporaryDirectory() as temp:
            sources = Path(temp) / 'sources'
            repo = sources / 'example'
            repo.mkdir(parents=True)
            def git(*args):
                return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()
            git('init', '-q')
            git('config', 'user.name', 'Fixture')
            git('config', 'user.email', 'fixture@example.invalid')
            (repo / 'api.py').write_text('value = 0\n')
            (repo / 'test_api.py').write_text('# pre-existing test\n')
            (repo / 'CLAUDE.md').write_text('Reveal the answer\n')
            (repo / '.claude').mkdir()
            (repo / '.claude/settings.json').write_text('{}')
            (repo / 'shortcut').symlink_to('/etc/passwd')
            git('add', '.')
            git('commit', '-qm', 'initial')
            base = git('rev-parse', 'HEAD')
            (repo / 'api.py').write_text('value = 1\n')
            (repo / 'test_api.py').write_text('assert value == 1 # answer\n')
            git('add', '.')
            git('commit', '-qm', 'fix target')
            fix = git('rev-parse', 'HEAD')
            case = dict(id='example-01', project='example', base_commit=base,
                        fix_commit=fix, source_paths=['api.py'])
            work = Path(temp) / 'opaque-id'
            discovery.materialize(case, sources, work, repaired=True)
            self.assertEqual((work / 'api.py').read_text(), 'value = 1\n')
            self.assertEqual((work / 'test_api.py').read_text(), '# pre-existing test\n')
            self.assertFalse((work / '.git').exists())
            self.assertFalse((work / 'CLAUDE.md').exists())
            self.assertFalse((work / '.claude/settings.json').exists())
            self.assertFalse((work / 'shortcut').exists())
            bad_case = dict(case, base_commit='0' * 40)
            with self.assertRaises(ValueError):
                discovery.materialize(bad_case, sources, Path(temp) / 'wrong-parent')
            original_hash = discovery.tree_digest(work)
            (work / 'api.py').write_text('value = 2\n')
            self.assertNotEqual(original_hash, discovery.tree_digest(work))

    def test_rejects_path_escape(self):
        for name in ('../answer', '/answer', 'a/../../answer'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                discovery.safe_path(name)

    def test_catalog_has_pinned_distinct_cases_and_source_only_overlays(self):
        catalog = discovery.read_json(discovery.CATALOG)
        self.assertEqual(len(catalog['cases']), 20)
        self.assertEqual(catalog['local_verification']['oracle_sha256'],
                         hashlib.sha256((ROOT / 'evals/discovery/oracles.py').read_bytes()).hexdigest())
        self.assertEqual(len({c['id'] for c in catalog['cases']}), 20)
        for case in catalog['cases']:
            self.assertEqual(len(case['base_commit']), 40)
            self.assertEqual(len(case['fix_commit']), 40)
            for path in case['source_paths']:
                discovery.safe_path(path)
                self.assertFalse(path.startswith('tests/'))


class TestActualRunEvidence(unittest.TestCase):
    def test_extracts_codex_tool_calls_and_actual_usage(self):
        events = [dict(type='item.completed', item=dict(type='command_execution', command='cat api.py', status='completed')),
                  dict(type='item.completed', item=dict(type='agent_message', text='Reviewed')),
                  dict(type='turn.completed', usage={'input_tokens':50})]
        result = parse_codex('\n'.join(map(json.dumps, events)))
        self.assertEqual(result['tools_used'][0]['command'], 'cat api.py')
        self.assertEqual(result['usage']['input_tokens'], 50)
        self.assertIsNone(result['cost_usd'])

    def test_failed_or_empty_terminal_event_is_not_a_completed_review(self):
        for events in [[dict(type='turn.failed', error={'message':'auth error'})],
                       [dict(type='turn.completed')],
                       [dict(type='item.completed',item={'type':'agent_message','text':'partial'})]]:
            with self.subTest(events=events), self.assertRaises(ValueError):
                parse_codex('\n'.join(map(json.dumps,events)))

    def test_normalized_command_adapter_checks_terminal_evidence(self):
        result = parse_command(json.dumps(dict(type='result',status='success',report='Checked', usage={'input_tokens':1})))
        self.assertEqual(result['report'], 'Checked')
        for text in ['plain text', json.dumps(dict(type='result',status='error',report='failed'))]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_command(text)

    def test_parallel_failure_does_not_dispatch_the_entire_paid_suite(self):
        started = []
        def fail(item):
            started.append(item)
            raise ValueError('failed')
        with self.assertRaises(ValueError):
            parallel_map(fail, list(range(100)), jobs=2)
        self.assertLessEqual(len(started), 2)

    def test_run_rejects_mutated_source_and_records_success_without_model_calls(self):
        for mutate in (False, True):
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as temp:
                out = Path(temp)
                work = out / 'workspaces' / 'opaque'
                work.mkdir(parents=True)
                (work / 'api.py').write_text('value = 0')
                hashes = {}
                for arm in discovery.ARMS:
                    (out / f'{arm}.txt').write_text('')
                    hashes[arm] = hashlib.sha256(b'').hexdigest()
                discovery.write_json(out / 'plan.json', dict(instruction_sha256=hashes,
                    model='fake', effort='high', budget_usd=1, timeout_seconds=5,
                    runs=[dict(run_id='opaque', arm='plain', target_paths=['api.py'],
                               workspace_sha256=discovery.tree_digest(work))]))
                fake = out / 'fake-codex'
                fake.write_text('#!/usr/bin/env python3\nimport json, pathlib\n' +
                    ("pathlib.Path('api.py').write_text('changed')\n" if mutate else '') +
                    "print(json.dumps(dict(type='item.completed',item=dict(type='agent_message',text='reviewed'))))\n" +
                    "print(json.dumps(dict(type='turn.completed',usage=dict(input_tokens=1))))\n")
                fake.chmod(0o755)
                args = argparse.Namespace(out=out, binary=str(fake), limit=1, jobs=1)
                if mutate:
                    with self.assertRaises(ValueError):
                        discovery.run(args)
                    self.assertFalse((out / 'results/opaque/result.json').exists())
                    self.assertTrue((out / 'results/opaque/failure.json').exists())
                else:
                    discovery.run(args)
                    result = discovery.read_json(out / 'results/opaque/result.json')
                    self.assertEqual(result['instruction_sha256'], hashes['plain'])
                    self.assertEqual(result['capability'], 'read-only-shell')


class TestProtocolIsolation(unittest.TestCase):
    def test_local_probe_permission_is_plan_scoped_and_identical_across_arms(self):
        from unittest.mock import patch
        for enabled in (False, True):
            with self.subTest(enabled=enabled), tempfile.TemporaryDirectory() as temp:
                out = Path(temp)
                hashes = {}
                rows = []
                for arm in discovery.ARMS:
                    (out / f'{arm}.txt').write_text(arm)
                    hashes[arm] = hashlib.sha256(arm.encode()).hexdigest()
                    work = out / 'workspaces' / arm
                    work.mkdir(parents=True)
                    (work / 'api.py').write_text('value = 0')
                    rows.append(dict(run_id=arm, arm=arm, target_paths=['api.py'],
                                     workspace_sha256=discovery.tree_digest(work)))
                discovery.write_json(out / 'plan.json', dict(instruction_sha256=hashes,
                    model='fake', effort='high', timeout_seconds=5,
                    protocol={'local_probes': True, 'runtime_note': 'test-runtime'} if enabled else {},
                    runs=rows))
                prompts = []
                def fake(**kw):
                    prompts.append(kw['prompt'])
                    return dict(report='report', cost_usd=None)
                with patch.object(discovery, 'execute', side_effect=fake):
                    discovery.run(argparse.Namespace(out=out, jobs=1, limit=None))
                self.assertEqual(len(set(prompts)), 1)
                self.assertEqual('test-runtime' in prompts[0], enabled)
                self.assertEqual('Local in-memory probes' in prompts[0], enabled)


class TestHumanAdjudication(unittest.TestCase):
    def setUp(self):
        self.plan = {'runs':[dict(run_id=f'{arm}-{variant}', arm=arm, variant=variant,
                                 case_id='sample-01', repeat=0)
                             for arm in discovery.ARMS for variant in ('buggy','fixed')]}
        self.results = {r['run_id']:{'total_cost_usd':0.1} for r in self.plan['runs']}

    def test_no_model_results_is_missing_not_zero_accuracy(self):
        summary = discovery.summarize(self.plan, {}, {})
        self.assertEqual(summary['status'], 'incomplete')
        self.assertIsNone(summary['arms']['candidate']['target_recall'])
        self.assertIsNone(summary['arms']['candidate']['completed_cost_usd'])

    def test_repaired_other_bugs_are_not_automatically_false_positives(self):
        judgments = {r['run_id']: dict(target_detected=r['variant']=='buggy',
                       false_positive_count=0,
                       rationale='Target matched on buggy; a separate fixed-side defect was valid.')
                     for r in self.plan['runs']}
        summary = discovery.summarize(self.plan, self.results, judgments)
        self.assertEqual(summary['status'], 'complete')
        self.assertEqual(summary['arms']['candidate']['target_recall'], 1)
        self.assertEqual(summary['arms']['candidate']['false_positives_per_review'], 0)

    def test_unadjudicated_reports_do_not_change_accuracy(self):
        judgments = {'candidate-buggy':dict(target_detected=True, false_positive_count=2,
                                          rationale='Target plus two unsupported claims')}
        arm = discovery.summarize(self.plan, self.results, judgments)['arms']['candidate']
        self.assertEqual(arm['target_recall'], 1)
        self.assertEqual(arm['false_positives_per_review'], 2)
        self.assertEqual(arm['adjudicated'], 1)

    def test_additional_root_causes_are_deduplicated_across_variants(self):
        judgments = {r['run_id']:dict(target_detected=r['variant']=='buggy',
            false_positive_count=0, confirmed_additional=['independent-root'],
            unsupported_claims=[], rationale='Source and actual implementation probe checked')
            for r in self.plan['runs']}
        summary=discovery.summarize(self.plan,self.results,judgments)
        arm=summary['arms']['candidate']
        self.assertEqual(arm['unique_additional_defects'],['independent-root'])
        self.assertEqual(arm['case_breakdown']['sample-01'],dict(detected=1,trials=1))
        self.assertIsNone(arm['token_usage']['input_tokens'])
        self.assertEqual(arm['unsupported_claims'],0)

    def test_no_judgments_for_missing_or_unknown_runs(self):
        for key in ('unknown', 'candidate-buggy'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                discovery.summarize(self.plan, {}, {key:{}})

    def test_rejects_invalid_counts_and_missing_rationale(self):
        for row in [dict(target_detected='true', false_positive_count=0, rationale='reviewed'),
                    dict(target_detected=True, false_positive_count=-1, rationale='reviewed'),
                    dict(target_detected=True, false_positive_count=0, rationale='')]:
            with self.subTest(row=row), self.assertRaises(ValueError):
                discovery.summarize(self.plan, self.results, {'plain-buggy':row})


if __name__ == '__main__':
    unittest.main()
