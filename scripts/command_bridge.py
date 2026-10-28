#!/usr/bin/env python3
"""Bridge a stdin/plain-stdout CLI to the generic result protocol.

Usage: python3 command_bridge.py -- my-cli its-args
The caller supplies sandbox/auth settings; no provider-specific flags are guessed.
"""
import json
import subprocess
import sys


def main():
    argv=sys.argv[1:]
    if argv and argv[0]=='--':argv=argv[1:]
    if not argv:raise SystemExit('usage: command_bridge.py -- CLI [ARGS...]')
    proc=subprocess.run(argv,input=sys.stdin.read(),text=True,capture_output=True)
    sys.stderr.write(proc.stderr)
    if proc.returncode:raise SystemExit(proc.returncode)
    if not proc.stdout.strip():raise SystemExit('CLI produced no report')
    print(json.dumps(dict(type='result',status='success',report=proc.stdout,
                         usage=None,cost_usd=None,tools_used=[],
                         evidence='process exit and stdout only; tool use unknown')))


if __name__=='__main__':main()
