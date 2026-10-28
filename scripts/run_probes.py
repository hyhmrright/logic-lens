#!/usr/bin/env python3
"""Run legacy real-code probes through a generic provider; inspect reports manually."""
import json
import os
from pathlib import Path
import tempfile

from llm_runner import execute
from skill_bundle import ROOT, snapshot


def main():
    provider=os.getenv('PROVIDER','codex')
    model=os.getenv('MODEL','gpt-6.1-sol')
    out=Path(os.getenv('OUT',str(ROOT/'skills-workspace/real-world-probes')))
    out.mkdir(parents=True,exist_ok=False)
    adapter=json.loads(Path(os.environ['ADAPTER']).read_text()) if os.getenv('ADAPTER') else None
    for probe in sorted((ROOT/'evals/real-world/probes').iterdir()):
        if not probe.is_dir() or os.getenv('PROBES_FILTER','') not in probe.name:continue
        for variant in ('buggy','fixed'):
            files=list(probe.glob(variant+'.*'))
            if not files:continue
            with tempfile.TemporaryDirectory(prefix='logic-lens-probe-') as temp:
                work=Path(temp)
                name='target'+files[0].suffix
                (work/name).write_bytes(files[0].read_bytes())
                result=execute(provider=provider,workspace=work,prompt=f'Review {name} for behavioral bugs.',
                    instructions=snapshot(),model=model,effort=os.getenv('EFFORT','high'),timeout=360,
                    artifacts=out/(probe.name+'.'+variant),adapter=adapter)
            (out/f'{probe.name}.{variant}.out.md').write_text(result['report'])
            print(f'{probe.name} {variant}: report ready for human inspection',flush=True)


if __name__=='__main__':main()
