#!/usr/bin/env python3
"""Tool-neutral content/routing evals. Codex is the default; no plugin cache needed."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from llm_runner import execute, parallel_map
from skill_bundle import ROOT, SKILLS, snapshot


def run_content(args):
    cases = json.loads((ROOT/'evals/content/v2/evals-v2.json').read_text())['evals']
    if args.smoke:
        selected = [next(c for c in cases if c['mode']=='logic-'+s) for s in SKILLS]
    else:
        selected = [c for c in cases if not args.cases or c['id'] in args.cases]
    if not selected or (args.cases and set(args.cases) != {c['id'] for c in selected}):
        raise ValueError('Unknown or empty case selection')
    args.out.mkdir(parents=True, exist_ok=True)
    adapter = json.loads(args.adapter.read_text()) if args.adapter else None
    instructions = {s:snapshot(s) for s in SKILLS}
    config = dict(provider=args.provider, model=args.model, effort=args.effort,
                  case_source_sha256=hashlib.sha256((ROOT/'evals/content/v2/evals-v2.json').read_bytes()).hexdigest(),
                  instruction_sha256={s:hashlib.sha256(t.encode()).hexdigest() for s,t in instructions.items()},
                  adapter=adapter)
    manifest = args.out/'run.json'
    if manifest.exists() and json.loads(manifest.read_text()) != config:
        raise ValueError('Output directory belongs to a different provider/model/skill snapshot')
    manifest.write_text(json.dumps(config,indent=2)+'\n')
    def one(case):
        out = args.out/f"eval-{case['id']}"
        if (out/'output.md').exists() and (out/'result.json').exists():
            return
        out.mkdir(parents=True,exist_ok=True)
        (out/'prompt.md').write_text(case['prompt'])
        with tempfile.TemporaryDirectory(prefix='logic-lens-content-') as temp:
            result = execute(provider=args.provider, workspace=Path(temp), prompt=case['prompt'],
                instructions=instructions[case['mode'].removeprefix('logic-')], model=args.model,
                effort=args.effort, timeout=args.timeout, artifacts=out, adapter=adapter)
        (out/'output.md').write_text(result.pop('report'))
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(f"Completed eval-{case['id']}",flush=True)
    parallel_map(one, selected, args.jobs)
    if not args.skip_grade:
        subprocess.run([sys.executable,str(ROOT/'scripts/grade-iteration.py'),str(args.out)],check=True)


def run_routing(args):
    # This tests description routing, not a host's actual native activation mechanism.
    names = args.skills or list(SKILLS)
    descriptions = '\n'.join((ROOT/f'skills/logic-{s}/SKILL.md').read_text().split('---',2)[1]
                             for s in SKILLS)
    args.out.mkdir(parents=True,exist_ok=False)
    results = []
    adapter = json.loads(args.adapter.read_text()) if args.adapter else None
    for name in names:
        cases = json.loads((ROOT/f'evals/trigger/v2/trigger-evals-{name}.json').read_text())
        for i, case in enumerate(cases):
            out = args.out/f'{name}-{i}'
            prompt = ('Choose the best matching skill for this request, or none. Reply with only '
                      'logic-review, logic-explain, logic-diff, logic-locate, logic-health, '
                      'logic-fix-all, or none.\nREQUEST: '+case['query'])
            with tempfile.TemporaryDirectory() as temp:
                result = execute(provider=args.provider,workspace=Path(temp),prompt=prompt,
                    instructions=descriptions,model=args.model,effort=args.effort,
                    timeout=args.timeout,artifacts=out,adapter=adapter)
            answer = result['report'].strip()
            expected = 'logic-'+name
            passed = ((answer == expected) == case['should_trigger']) and answer in ['none',*['logic-'+s for s in SKILLS]]
            results.append(dict(skill=name,case=i,answer=answer,passed=passed))
            (args.out/'routing.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(dict(cases=len(results),passed=sum(r['passed'] for r in results))))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite',choices=['content','routing'])
    parser.add_argument('--provider',choices=['codex','command'],default=os.getenv('PROVIDER','codex'))
    parser.add_argument('--model',default=os.getenv('MODEL','gpt-6.1-sol'))
    parser.add_argument('--effort',default=os.getenv('EFFORT','high'))
    parser.add_argument('--adapter',type=Path,default=os.getenv('ADAPTER'))
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--cases',nargs='+',type=int)
    parser.add_argument('--skills',nargs='+',choices=SKILLS)
    parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--jobs',type=int,default=2)
    parser.add_argument('--timeout',type=int,default=360)
    parser.add_argument('--skip-grade',action='store_true')
    args=parser.parse_args()
    args.out=args.out.resolve()
    if args.jobs<1 or args.timeout<1: parser.error('jobs and timeout must be positive')
    if args.provider=='command' and not args.adapter: parser.error('command provider requires --adapter')
    try:
        (run_content if args.suite=='content' else run_routing)(args)
    except (ValueError,OSError,subprocess.SubprocessError) as exc:
        parser.exit(1,f'error: {exc}\n')


if __name__=='__main__': main()
