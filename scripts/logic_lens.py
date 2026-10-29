#!/usr/bin/env python3
"""Logic-Lens: portable prompts and provider-neutral code review/evaluation."""
import argparse
from pathlib import Path
import subprocess
import sys

COMMANDS = {'review':'run_review.py', 'bundle':'skill_bundle.py',
            'eval':'run_evals.py', 'discovery':'discovery_eval.py',
            'verify':'verify_discovery.py', 'doctor':'doctor.py',
            'search':'property_search.py', 'constraints':'constraint_plan.py', 'facts':'python_facts.py', 'investigate':'investigation.py', 'explore':'path_exploration.py', 'typed-investigate':'typed_investigation.py'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=COMMANDS)
    args = p.parse_args(sys.argv[1:2])
    rest = sys.argv[2:]
    return subprocess.call([sys.executable,str(Path(__file__).parent/COMMANDS[args.command]),*rest])


if __name__=='__main__':sys.exit(main())
