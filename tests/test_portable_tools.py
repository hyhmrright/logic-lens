"""Behavioral tests for portable bundles and generic execution adapters."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from llm_runner import copy_workspace, execute, parse_codex
from skill_bundle import export, snapshot, SKILLS


class PortableTools(unittest.TestCase):
    def test_bundle_preserves_all_skill_resources_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'pack'
            export(out)
            for name in SKILLS:
                self.assertTrue((out/f'skills/logic-{name}/SKILL.md').exists())
                text=(out/f'prompts/logic-{name}.md').read_text()
                self.assertIn('--- RESOURCE skills/_shared/common.md ---',text)
                self.assertNotIn(str(ROOT),text)
            self.assertIn('skills/logic-review/SKILL.md',snapshot('health'))
            self.assertIn('skills/logic-locate/SKILL.md',snapshot('fix-all'))
            with self.assertRaises(FileExistsError):export(out)

    def test_source_copy_does_not_follow_external_symlinks_or_load_native_rules(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'source';source.mkdir()
            (root/'outside.txt').write_text('outside context')
            (source/'external').symlink_to(root/'outside.txt')
            (source/'AGENTS.md').write_text('host control')
            (source/'.cursor').mkdir()
            (source/'.cursor/rule.md').write_text('host rule')
            (source/'api.py').write_text('source')
            dest=root/'copy'
            copy_workspace(source,dest)
            self.assertFalse((dest/'external').exists())
            self.assertFalse((dest/'AGENTS.md').exists())
            self.assertFalse((dest/'.cursor/rule.md').exists())
            self.assertEqual((dest/'api.py').read_text(),'source')

    def test_child_help_is_forwarded_without_model_call(self):
        proc=subprocess.run([sys.executable,str(ROOT/'scripts/logic_lens.py'),'review','--help'],capture_output=True,text=True)
        self.assertEqual(proc.returncode,0)
        self.assertIn('--provider',proc.stdout)
        self.assertIn('--workspace',proc.stdout)

    def test_codex_parser_uses_final_message_not_progress(self):
        events=[dict(type='item.completed',item=dict(type='agent_message',text='Investigating')),
                dict(type='item.completed',item=dict(type='agent_message',text='Final evidence')),
                dict(type='turn.completed',usage=dict(input_tokens=10,output_tokens=2))]
        self.assertEqual(parse_codex('\n'.join(map(json.dumps,events)))['report'],'Final evidence')

    def test_recovered_codex_stream_error_does_not_override_successful_terminal_state(self):
        events=[dict(type='error',message='Reconnecting after transient disconnect'),
                dict(type='item.completed',item=dict(type='agent_message',text='Finished')),
                dict(type='turn.completed',usage=dict(input_tokens=1))]
        self.assertEqual(parse_codex('\n'.join(map(json.dumps,events)))['report'],'Finished')
        with self.assertRaises(ValueError):parse_codex(json.dumps(events[0]))

    def test_generic_command_receives_literal_prompt_and_opaque_workspace(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); source=root/'source'; source.mkdir()
            (source/'api.py').write_text('value=0')
            wrapper=root/'wrapper.py'
            wrapper.write_text('import json, pathlib, sys\n'
                'text=sys.stdin.read()\n'
                'assert "$(touch injected)" in text\n'
                'assert pathlib.Path("api.py").read_text()=="value=0"\n'
                'print(json.dumps(dict(type="result",status="success",report="evidence",usage=None)))\n')
            result=execute(provider='command',workspace=source,prompt='$(touch injected)',
                instructions='contract',model='model with spaces',effort='high',timeout=5,
                artifacts=root/'artifacts',adapter={'argv':[sys.executable,str(wrapper),'{model}']})
            self.assertEqual(result['report'],'evidence')
            self.assertEqual(result['evidence_source'],'command-adapter-reported')
            self.assertFalse((source/'injected').exists())
            self.assertEqual((source/'api.py').read_text(),'value=0')

    def test_command_bridge_preserves_nonzero_failure(self):
        proc=subprocess.run([sys.executable,str(ROOT/'scripts/command_bridge.py'),'--',
                             sys.executable,'-c','raise SystemExit(7)'],input='request',text=True,capture_output=True)
        self.assertEqual(proc.returncode,7)
        self.assertEqual(proc.stdout,'')


if __name__=='__main__':unittest.main()
