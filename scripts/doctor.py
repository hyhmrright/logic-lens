#!/usr/bin/env python3
"""Check local runner capabilities without model calls or credential contents."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--provider',choices=['codex','command'],default='codex')
    p.add_argument('--adapter',type=Path)
    args=p.parse_args()
    result=dict(python=sys.version.split()[0],portable_pack=True,provider=args.provider)
    if args.provider=='command':
        if not args.adapter:p.error('command provider requires --adapter')
        config=json.loads(args.adapter.read_text())
        argv=config.get('argv',[])
        if not argv or not all(isinstance(v,str) for v in argv):p.error('adapter needs argv strings')
        result.update(executable=shutil.which(argv[0]),capabilities='adapter-defined; host policy must be validated')
    else:
        binary=shutil.which('codex')
        result['executable']=binary
        if binary:
            help_text=subprocess.check_output([binary,'exec','--help'],text=True)
            required=['--json','--ephemeral','--ignore-user-config','--ignore-rules','--sandbox']
            result['required_flags']={flag:flag in help_text for flag in required}
            result['version']=subprocess.check_output([binary,'--version'],text=True).strip()
            auth=subprocess.run([binary,'login','status'],capture_output=True,text=True)
            result['authenticated']=auth.returncode==0
    print(json.dumps(result,indent=2))
    return 0 if result.get('executable') and all(result.get('required_flags',{}).values()) else 1


if __name__=='__main__':sys.exit(main())
