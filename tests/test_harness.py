"""Offline runner integration; no model requests."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from llm_runner import execute, tree_digest


class HarnessIntegration(unittest.TestCase):
    def test_identical_access_real_engine_and_archive_for_both_arms(self):
        configurations = []
        for arm in ('baseline', 'candidate'):
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                source = ROOT / 'examples/property-search/workspace'
                before = tree_digest(source)
                def offline(command, text, cwd, env, timeout, stdout, stderr):
                    # Intercept only the model process. Execute the real local engine.
                    self.assertNotIn('--sandbox', command)
                    self.assertIn('default_permissions="local-harness"', command)
                    self.assertIn('permissions.local-harness.network.enabled=false', command)
                    configurations.append(text.split('COMMON LOCAL HARNESS ACCESS')[1].split('At most two searches')[1])
                    self.assertEqual(cwd.name, 'harness')
                    work = cwd.parent / 'workspace'
                    self.assertFalse(work.is_relative_to(cwd))
                    toolbox = cwd.parent / 'toolbox'
                    import shutil
                    for name in ('property.json', 'adapter.py'):
                        shutil.copy2(ROOT / 'examples/property-search' / name, cwd / name)
                    run = subprocess.run([sys.executable, str(toolbox / 'property_search.py'),
                        '--spec', str(cwd / 'property.json'), '--workspace', str(work),
                        '--out', str(cwd / 'evidence')], cwd=cwd, env=env, capture_output=True, text=True)
                    self.assertEqual(run.returncode, 0, run.stderr)
                    self.assertEqual(json.loads(run.stdout)['status'], 'exhausted')
                    Path(stdout).write_text('\n'.join(map(json.dumps, [
                        {'type': 'item.completed', 'item': {'type':'agent_message','text':'offline only'}},
                        {'type':'turn.completed','usage':{'input_tokens':0,'output_tokens':0}}])))
                    Path(stderr).write_text('')
                    return 0
                with patch('llm_runner.bounded_process', side_effect=offline):
                    result = execute(provider='codex', workspace=source, prompt='review',
                        instructions=arm, model='unused', effort='high', timeout=5,
                        artifacts=root / 'artifacts', harness=True)
                self.assertEqual(result['capability'], 'local-harness')
                self.assertTrue((root / 'artifacts/harness/evidence/summary.json').exists())
                self.assertTrue(json.loads((root / 'artifacts/integrity.json').read_text())['unchanged'])
                self.assertEqual(before, tree_digest(source))
        self.assertEqual(configurations[0], configurations[1])

    def test_failed_model_preserves_harness_and_integrity(self):
        with tempfile.TemporaryDirectory() as temp:
            def fail(command, text, cwd, env, timeout, stdout, stderr):
                (cwd / 'partial.txt').write_text('evidence')
                raise subprocess.TimeoutExpired(command, timeout)
            with patch('llm_runner.bounded_process', side_effect=fail):
                with self.assertRaises(subprocess.TimeoutExpired):
                    execute(provider='codex', workspace=ROOT / 'examples/property-search/workspace',
                        prompt='review', instructions='', model='unused', effort='high', timeout=1,
                        artifacts=Path(temp) / 'artifacts', harness=True)
            self.assertEqual((Path(temp) / 'artifacts/harness/partial.txt').read_text(), 'evidence')
            self.assertTrue((Path(temp) / 'artifacts/integrity.json').exists())

    @unittest.skipUnless(sys.platform == 'darwin' and __import__('shutil').which('codex'), 'native macOS Codex sandbox unavailable')
    def test_native_permissions_source_denied_harness_and_engine_work(self):
        import os
        import shutil
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'workspace'
            shutil.copytree(ROOT / 'examples/property-search/workspace', source)
            harness = root / 'harness'
            harness.mkdir()
            (harness / 'tmp').mkdir()
            for name in ('property.json', 'adapter.py'):
                shutil.copy2(ROOT / 'examples/property-search' / name, harness / name)
            before = tree_digest(source)
            code = ("from pathlib import Path\n"
                f"p=Path({str(source / 'axis.py')!r})\n"
                "try:\n p.write_text('changed')\n raise AssertionError('source writable')\n"
                "except PermissionError:\n print('SOURCE_DENIED')\n"
                "Path('allowed').write_text('ok')\n"
                "import subprocess,sys\n"
                f"subprocess.run([sys.executable,{str(ROOT / 'scripts/property_search.py')!r},"
                f"'--workspace',{str(source)!r},'--spec','property.json','--out','evidence'],check=True)\n")
            env = dict(os.environ, TMPDIR=str(harness / 'tmp'), PYTHONDONTWRITEBYTECODE='1')
            run = subprocess.run(['codex', 'sandbox', '-C', str(harness), '-P', 'local-harness',
                '-c', 'permissions.local-harness.filesystem={":root"="read",":workspace_roots"="write"}',
                '-c', 'permissions.local-harness.network.enabled=false', sys.executable, '-c', code],
                cwd=harness, env=env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn('SOURCE_DENIED', run.stdout)
            self.assertEqual(json.loads((harness / 'evidence/summary.json').read_text())['status'], 'exhausted')
            self.assertEqual(tree_digest(source), before)
