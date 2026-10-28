#!/usr/bin/env python3
"""Prepare blind source snapshots, run three review arms, collect human judgments.

No model calls during prepare. See evals/discovery/README.md for limitations.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import random
import subprocess
import tarfile
import time
import uuid
import statistics
from llm_runner import execute, tree_digest, parallel_map
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / 'evals/discovery/catalog.json'
SKILL_FILES = ['skills/logic-review/SKILL.md',
               'skills/logic-review/logic-review-guide.md',
               *[f'skills/_shared/{n}.md' for n in (
                   'common', 'semiformal-guide', 'semiformal-checklist',
                   'logic-risks', 'report-template')]]
ARMS = ('plain', 'baseline', 'candidate')


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def safe_path(name):
    path = Path(name)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError(f'unsafe relative path: {name!r}')
    return path


def export_tree(repo, revision, destination):
    """Export tracked regular files only: no history, symlinks or future commits."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    archive = git(repo, 'archive', revision)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tf:
        for member in tf:
            relative = safe_path(member.name)
            if not member.isfile():
                continue
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(tf.extractfile(member).read())
            target.chmod(member.mode & 0o777)


def skill_snapshot(revision=None):
    parts = []
    for name in SKILL_FILES:
        text = (git(ROOT, 'show', f'{revision}:{name}').decode() if revision
                else (ROOT / name).read_text())
        parts.append(f'\n--- RESOURCE {name} ---\n{text}')
    return ''.join(parts)


def materialize(case, sources, destination, repaired=False):
    repo = Path(sources) / case['project']
    base = git(repo, 'rev-parse', f"{case['fix_commit']}^1").decode().strip()
    if base != case['base_commit']:
        raise ValueError(f"parent mismatch: {case['id']}")
    export_tree(repo, base, destination)
    # Overlay implementation changes only. Tests/docs/config stay at the parent,
    # so fixed snapshots do not leak the future regression test or changelog.
    if repaired:
        for name in case['source_paths']:
            path = Path(destination) / safe_path(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(git(repo, 'show', f"{case['fix_commit']}:{name}"))
    # Project agent instructions/hooks must not introduce arm-dependent behavior.
    for path in list(Path(destination).rglob('*')):
        if path.is_file() and (path.name in ('CLAUDE.md', 'AGENTS.md', 'GEMINI.md')
                               or '.claude' in path.relative_to(destination).parts):
            path.unlink()


def prepare(args):
    catalog = read_json(args.catalog)
    selected = [c for c in catalog['cases'] if not args.cases or c['id'] in args.cases]
    if not selected or (args.cases and set(args.cases) != {c['id'] for c in selected}):
        raise ValueError('unknown or empty case selection')
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    instructions = {}
    for arm, text in [('plain', ''),
                      ('baseline', skill_snapshot(catalog['baseline_skill_commit'])),
                      ('candidate', skill_snapshot())]:
        path = out / f'{arm}.txt'
        path.write_text(text)
        instructions[arm] = hashlib.sha256(text.encode()).hexdigest()
    plan = []
    rng = random.Random(args.seed)
    for case in selected:
        for repaired in (False, True):
            for repeat in range(args.repeats):
                for arm in ARMS:
                    run_id = uuid.uuid4().hex
                    work = out / 'workspaces' / run_id
                    materialize(case, args.sources, work, repaired)
                    plan.append(dict(run_id=run_id, case_id=case['id'],
                                     variant='fixed' if repaired else 'buggy',
                                     arm=arm, repeat=repeat,
                                     workspace_sha256=tree_digest(work),
                                     target_paths=case['review_paths']))
    rng.shuffle(plan)
    write_json(out / 'plan.json', dict(schema_version=2, seed=args.seed,
               provider=getattr(args, 'provider', 'codex'),
               adapter=read_json(args.adapter) if getattr(args, 'adapter', None) else None,
               model=args.model, effort=args.effort,
               timeout_seconds=args.timeout, instruction_sha256=instructions,
               catalog_sha256=hashlib.sha256(Path(args.catalog).read_bytes()).hexdigest(),
               baseline_skill_commit=catalog['baseline_skill_commit'],
               tools=['read-only-shell'] if getattr(args, 'provider', 'codex') == 'codex' else ['adapter-defined'], runs=plan))
    print(f'Prepared {len(plan)} runs; no model calls. Plan: {out / "plan.json"}')


def run(args):
    out = Path(args.out).resolve()
    plan = read_json(out / 'plan.json')
    for arm, digest in plan['instruction_sha256'].items():
        if hashlib.sha256((out / f'{arm}.txt').read_bytes()).hexdigest() != digest:
            raise ValueError(f'instruction drift: {arm}')
    provider = plan.get('provider', 'codex')
    adapter = plan.get('adapter')
    pending = [r for r in plan['runs']
               if not (out / 'results' / r['run_id'] / 'result.json').exists()]
    if args.limit is not None:
        pending = pending[:args.limit]

    def one(item):
        artifacts = out / 'results' / item['run_id']
        artifacts.mkdir(parents=True, exist_ok=True)
        work = out / 'workspaces' / item['run_id']
        if tree_digest(work) != item['workspace_sha256']:
            raise ValueError(f"workspace drift: {item['run_id']}")
        prompt = ('Review the behavior of ' + ', '.join(item['target_paths']) +
                  '. Find concrete bugs and investigate supporting files as needed. '
                  'State the actual expected/observed consequence and evidence for each '
                  'finding. Do not infer that a bug must exist. Do not modify files. '
                  'Do not use external services. Runtime integration tests are outside '
                  'this read-only discovery protocol; disclose verification limitations. '
                  'Investigation budget: at most 10 shell/tool calls; prioritize targeted reads. '
                  'Keep the final report under 1600 words and distinguish defects from open leads.')
        started = time.monotonic()
        try:
            result = execute(provider=provider, workspace=work, prompt=prompt,
                instructions=(out / f"{item['arm']}.txt").read_text(),
                model=plan['model'], effort=plan['effort'],
                timeout=plan['timeout_seconds'], artifacts=artifacts,
                binary=getattr(args, 'binary', None), adapter=adapter)
            (artifacts / 'report.md').write_text(result.pop('report'))
            result.update(instruction_sha256=plan['instruction_sha256'][item['arm']],
                          workspace_sha256=item['workspace_sha256'],
                          total_cost_usd=result.pop('cost_usd'))
            write_json(artifacts / 'result.json', result)
            (artifacts / 'failure.json').unlink(missing_ok=True)
            print(f"Completed {item['run_id']}", flush=True)
        except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
            write_json(artifacts / 'failure.json', dict(error=str(exc),
                       elapsed_seconds=time.monotonic()-started))
            raise ValueError(f"{item['run_id']}: {exc}") from exc
    parallel_map(one, pending, getattr(args, 'jobs', 1))



def summarize(plan, results, judgments):
    """Only source-adjudicated, completed runs contribute to accuracy metrics."""
    run_map = {r['run_id']: r for r in plan['runs']}
    if set(judgments) - run_map.keys():
        raise ValueError('judgment references unknown run')
    if set(judgments) - results.keys():
        raise ValueError('cannot adjudicate an incomplete/failed run')
    for j in judgments.values():
        if type(j.get('target_detected')) is not bool:
            raise ValueError('target_detected must be a boolean')
        if type(j.get('false_positive_count')) is not int or j['false_positive_count'] < 0:
            raise ValueError('false_positive_count must be a nonnegative integer')
        if not isinstance(j.get('rationale'), str) or not j['rationale'].strip():
            raise ValueError('adjudication rationale is required')
        for name in ('confirmed_additional', 'unsupported_claims'):
            if name in j and (not isinstance(j[name], list) or not all(isinstance(x,str) and x for x in j[name])):
                raise ValueError(f'{name} must be a list of nonempty identifiers')
    arms = {}
    for arm in ARMS:
        planned = [r for r in plan['runs'] if r['arm'] == arm]
        completed = [r for r in planned if r['run_id'] in results]
        judged = [r for r in completed if r['run_id'] in judgments]
        buggy = [r for r in judged if r['variant'] == 'buggy']
        recall = (sum(judgments[r['run_id']]['target_detected'] for r in buggy) / len(buggy)
                  if buggy else None)
        costs = [results[r['run_id']].get('total_cost_usd') for r in completed]
        times = [results[r['run_id']].get('elapsed_seconds') for r in completed]
        tokens = {}
        for key in ('input_tokens', 'cached_input_tokens', 'output_tokens'):
            values = [(results[r['run_id']].get('usage') or {}).get(key) for r in completed]
            tokens[key] = sum(values) if values and all(v is not None for v in values) else None
        case_breakdown = {}
        for row in buggy:
            entry = case_breakdown.setdefault(row['case_id'], dict(detected=0, trials=0))
            entry['trials'] += 1
            entry['detected'] += judgments[row['run_id']]['target_detected']
        additional_known = bool(judged) and all('confirmed_additional' in judgments[r['run_id']] for r in judged)
        additional = sorted({key for r in judged for key in judgments[r['run_id']].get('confirmed_additional',[])})
        unsupported_known = bool(judged) and all('unsupported_claims' in judgments[r['run_id']] for r in judged)
        arms[arm] = dict(case_breakdown=case_breakdown,
                         token_usage=tokens,
                         median_seconds=statistics.median(times) if times and all(t is not None for t in times) else None,
                         unique_additional_defects=additional if additional_known else None,
                         unsupported_claims=sum(len(judgments[r['run_id']]['unsupported_claims']) for r in judged) if unsupported_known else None,
                         planned=len(planned), completed=len(completed),
                         adjudicated=len(judged), buggy_adjudicated=len(buggy),
                         target_recall=recall,
                         false_positives_per_review=(sum(judgments[r['run_id']]['false_positive_count']
                                                        for r in judged) / len(judged) if judged else None),
                         completed_cost_usd=(sum(costs) if costs and all(c is not None for c in costs)
                                         else None))
    complete = bool(plan['runs']) and len(judgments) == len(plan['runs']) == len(results)
    return dict(status='complete' if complete else 'incomplete', arms=arms,
                note='No ship decision from incomplete or unmatched comparisons; '
                     'inspect per-case, paired repeats and project/family slices.')


def report(args):
    out = Path(args.out)
    plan = read_json(out / 'plan.json')
    results = {r['run_id']: read_json(out / 'results' / r['run_id'] / 'result.json')
               for r in plan['runs'] if (out / 'results' / r['run_id'] / 'result.json').exists()}
    judgments = read_json(args.judgments) if args.judgments else {}
    summary = summarize(plan, results, judgments)
    summary['failed_run_ids'] = [r['run_id'] for r in plan['runs']
        if r['run_id'] not in results and
        (out / 'results' / r['run_id'] / 'failure.json').exists()]
    summary['cost_note'] = 'Costs cover completed runs only; failed attempts may also be billable.'
    write_json(out / 'summary.json', summary)
    print(json.dumps(summary, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--catalog', type=Path, default=CATALOG)
    prep.add_argument('--sources', type=Path, required=True)
    prep.add_argument('--out', type=Path, required=True)
    prep.add_argument('--cases', nargs='+')
    prep.add_argument('--repeats', type=int, default=3)
    prep.add_argument('--seed', type=int, default=17)
    prep.add_argument('--model', required=True)
    prep.add_argument('--provider', choices=['codex', 'command'], default='codex')
    prep.add_argument('--adapter', type=Path, help='JSON argv adapter for provider=command')
    prep.add_argument('--effort', default='high')
    prep.add_argument('--timeout', type=int, default=300)
    call = sub.add_parser('run')
    call.add_argument('--out', type=Path, required=True)
    call.add_argument('--binary', help='Override the selected provider executable')
    call.add_argument('--jobs', type=int, default=1)
    call.add_argument('--limit', type=int)
    rep = sub.add_parser('summarize')
    rep.add_argument('--out', type=Path, required=True)
    rep.add_argument('--judgments', type=Path)
    args = p.parse_args()
    if args.action == 'prepare' and (args.repeats < 1 or args.timeout < 1):
        p.error('repeats and timeout must be positive')
    if args.action == 'prepare' and args.provider == 'command' and not args.adapter:
        p.error('--provider command requires --adapter')
    if args.action == 'run' and args.jobs < 1:
        p.error('jobs must be positive')
    if args.action == 'run' and args.limit is not None and args.limit < 1:
        p.error('limit must be positive')
    try:
        {'prepare': prepare, 'run': run, 'summarize': report}[args.action](args)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        p.exit(1, f'error: {exc}\n')


if __name__ == '__main__':
    main()
