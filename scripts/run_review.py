#!/usr/bin/env python3
"""Run any Logic-Lens skill through Codex or a normalized command adapter."""
import argparse
import json
import os
from pathlib import Path
import sys

from llm_runner import execute
from skill_bundle import SKILLS, snapshot


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--provider', choices=['codex', 'command'], default=os.getenv('PROVIDER','codex'))
    p.add_argument('--model', default=os.getenv('MODEL','gpt-6.1-sol'))
    p.add_argument('--effort', default=os.getenv('EFFORT','high'))
    p.add_argument('--skill', choices=SKILLS, default='review')
    p.add_argument('--plain', action='store_true', help='No skill instructions')
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--prompt', type=Path, help='UTF-8 request file; stdin otherwise')
    p.add_argument('--adapter', type=Path, default=os.getenv('ADAPTER'))
    p.add_argument('--timeout', type=int, default=360)
    args = p.parse_args()
    if args.timeout <= 0:
        p.error('timeout must be positive')
    if args.provider == 'command' and not args.adapter:
        p.error('--provider command requires --adapter')
    if args.skill == 'fix-all':
        p.error('The read-only CLI runner cannot execute fix-all; use the exported skill in a write-capable host')
    args.out.mkdir(parents=True, exist_ok=False)
    prompt = args.prompt.read_text() if args.prompt else sys.stdin.read()
    result = execute(provider=args.provider, workspace=args.workspace, prompt=prompt,
        instructions='' if args.plain else snapshot(args.skill), model=args.model,
        effort=args.effort, timeout=args.timeout, artifacts=args.out,
        adapter=json.loads(args.adapter.read_text()) if args.adapter else None)
    (args.out / 'report.md').write_text(result['report'])
    (args.out / 'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(result['report'])


if __name__ == '__main__':
    main()
