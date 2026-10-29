#!/usr/bin/env python3
"""Offline experimental planner for declared integer affine constraint relations."""
import argparse
import hashlib
import json
from pathlib import Path

from property_search import integer, relative_file, read_json


def reference(root, ref):
    path = relative_file(root, ref['path'])
    lines = path.read_text().splitlines()
    start = integer(ref['start'], 1, len(lines), 'source start')
    end = integer(ref['end'], start, len(lines), 'source end')
    if ref['quote'] != '\n'.join(lines[start-1:end]):
        raise ValueError('source quotation mismatch')
    return {'path': ref['path'], 'start': start, 'end': end,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def number(value):
    return integer(value, -10**9, 10**9, 'constraint integer')


def intervals(values):
    if not isinstance(values, list) or not 1 <= len(values) <= 8:
        raise ValueError('expected 1..8 closed integer intervals')
    result = []
    for pair in values:
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError('interval needs lower and upper endpoints')
        lo, hi = map(number, pair)
        if lo > hi:
            raise ValueError('empty interval')
        result.append((lo, hi))
    merged = []
    for lo, hi in sorted(result):
        if merged and lo <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
        else:
            merged.append((lo, hi))
    return merged


def contains(ranges, n):
    return any(lo <= n <= hi for lo, hi in ranges)


def overlap(left, right):
    return sorted(set((max(a, c), min(b, d)) for a, b in left for c, d in right
                      if max(a, c) <= min(b, d)))


def covered(interval, ranges):
    cursor, end = interval
    for lo, hi in sorted(ranges):
        if hi < cursor:
            continue
        if lo > cursor:
            return False
        cursor = max(cursor, hi + 1)
        if cursor > end:
            return True
    return False


def candidate(card, root):
    if not isinstance(card.get('id'), str) or not card['id']:
        raise ValueError('relation needs id')
    refs = {k: reference(root, card[k]['source']) for k in
            ('contract', 'input', 'producer', 'consumer', 'route')}
    result = dict(id=card['id'], evidence=refs, declarations=card,
                  # Identity is sourced, not a user-assigned "novelty" score.
                  edge=[refs[k] for k in ('producer', 'consumer')])
    if card['contract']['status'] not in ('supported', 'unknown', 'conflict'):
        raise ValueError('unknown contract status')
    if card['contract']['status'] != 'supported':
        return dict(result, status='unresolved', reason='contract_' + card['contract']['status'])
    if card['contract'].get('obligation') != 'consumer_precondition':
        return dict(result, status='unsupported', reason='only consumer_precondition supported')
    if card['producer'].get('kind') != 'integer_affine':
        return dict(result, status='unsupported', reason='unsupported producer model')
    if card['consumer'].get('operator') != '<=':
        return dict(result, status='unsupported', reason='only upper-bound consumer supported')
    units = [card['input'].get('unit'), card['producer'].get('input_unit'),
             card['producer'].get('output_unit'), card['consumer'].get('unit')]
    if not all(isinstance(u, str) and u for u in units):
        raise ValueError('explicit units required')
    if units[0] != units[1] or units[2] != units[3]:
        return dict(result, status='unresolved', reason='unit_mismatch')
    scale, offset = number(card['producer']['scale']), number(card['producer']['offset'])
    bound = number(card['consumer']['bound'])
    if not scale:
        return dict(result, status='unsupported', reason='constant producer not implemented')
    public, guard = intervals(card['input']['valid']), intervals(card['route']['guard'])
    reachable = overlap(public, guard)
    if not reachable:
        return dict(result, status='unreachable', reason='empty_public_route_intersection', domain=[])
    claims = card['contract'].get('claims')
    if not isinstance(claims, list) or not 1 <= len(claims) <= 8:
        raise ValueError('contract requires 1..8 explicitly sourced allow/deny claims')
    allowed, denied = [], []
    for claim in claims:
        source = reference(root, claim['source'])
        refs.setdefault('claims', []).append(source)
        if claim['effect'] not in ('allow', 'deny'):
            raise ValueError('contract effect must be allow or deny')
        scope = intervals(claim['scope'])
        (allowed if claim['effect'] == 'allow' else denied).extend(scope)
    conflict = overlap(overlap(allowed, denied), reachable)
    if conflict:
        return dict(result, status='unresolved', reason='overlapping_contract_conflict',
                    conflict_intervals=conflict, domain=[])
    if overlap(denied, reachable):
        return dict(result, status='unresolved', reason='declared_valid_domain_includes_denied_input', domain=[])
    if not all(covered(part, allowed) for part in reachable):
        return dict(result, status='unresolved', reason='contract_scope_gap', domain=[])
    # Exact integer arithmetic handles positive/negative slopes, no float rounding.
    cut = (bound - offset) // scale
    domain = {n for lo, hi in reachable for n in (lo, hi)}
    domain.update(n for n in (cut-1, cut, cut+1, cut+2) if contains(reachable, n))
    domain = sorted(domain)
    safe = [n for n in domain if scale*n + offset <= bound]
    unsafe = [n for n in domain if scale*n + offset > bound]
    crossing = bool(safe and unsafe)
    return dict(result, status='ready',
                property=dict(kind='consumer_precondition',
                    premise='supported public input on declared route',
                    observation='actual value passed to the identified consumer',
                    predicate=f'observed[{units[3]}] <= {bound}',
                    oracle='declared contract; implementation model selects inputs only'),
                model=dict(scale=scale, offset=offset, bound=bound,
                           input_unit=units[0], output_unit=units[3]),
                domain=domain, reachable_intervals=reachable,
                control=safe[0] if safe else None,
                control_status='predicted_only_requires_execution' if safe else 'no_predicted_passing_control',
                boundary_status='reachable_crossing' if crossing else
                    ('all_predicted_safe' if safe else 'all_predicted_unsafe'),
                predicted_safe=safe, predicted_unsafe=unsafe,
                evidence_limit='Source quotes match; declarations, contract status and route completeness require human verification. No subject execution or bug confirmation.')


def same_edge(left, right):
    # Conservative span overlap, not claimed semantic root-cause deduplication.
    return all(a['path'] == b['path'] and a['sha256'] == b['sha256']
               and max(a['start'], b['start']) <= min(a['end'], b['end'])
               for a, b in zip(left['edge'], right['edge']))


def plan(spec, root):
    if spec.get('schema_version') != 1:
        raise ValueError('expected schema_version 1')
    cards = spec.get('relations')
    if not isinstance(cards, list) or not 1 <= len(cards) <= 16:
        raise ValueError('expected 1..16 relations')
    if len({c['id'] for c in cards}) != len(cards):
        raise ValueError('duplicate relation id')
    budget = integer(spec.get('search_slots', 2), 1, 4, 'search slots')
    point_budget = integer(spec.get('max_domain_points', 32), 1, 64, 'domain point budget')
    results = [candidate(c, root) for c in cards]
    for item in results:
        if item['status'] == 'ready' and len(item['domain']) > point_budget:
            item['status'] = 'budget_blocked'
            item['reason'] = 'domain_point_budget_insufficient_no_silent_truncation'
    # A candidate is selectable only if it has a predicted control AND a reachable
    # counter-partition. Others remain visible; no obligation to manufacture a bug.
    pool = [r for r in results if r['status'] == 'ready' and r['boundary_status'] == 'reachable_crossing']
    pool.sort(key=lambda r: (len(r['domain']), r['id']))
    selected, seen = [], []
    for item in pool:
        if not any(same_edge(item, previous) for previous in seen) and len(selected) < budget:
            selected.append(item['id'])
            seen.append(item)
    for r in results:
        r['selection'] = ('selected' if r['id'] in selected else
                          'same_edge_deferred' if r in pool and any(same_edge(r, previous) for previous in seen) else
                          'budget_deferred' if r in pool else 'not_eligible')
    return dict(schema_version=1, spec_sha256=hashlib.sha256(json.dumps(spec, sort_keys=True, allow_nan=False).encode()).hexdigest(), selected=selected, relations=results,
                selection_policy='eligible crossing + predicted control; one per overlapping sourced producer/consumer edge; smaller domain then stable id',
                limits='Finite supplied relation inventory only. No source extraction, semantic oracle proof, automatic execution or superiority claim.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--spec', required=True, type=Path)
    p.add_argument('--workspace', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    a = p.parse_args()
    try:
        if a.out.resolve().is_relative_to(a.workspace.resolve()):
            raise ValueError('output must be outside the source workspace')
        result = plan(read_json(a.spec.read_text()), a.workspace.resolve())
        # x mode refuses overwrite, preserving earlier plans.
        with a.out.open('x') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write('\n')
    except (ValueError, KeyError, TypeError, OSError) as exc:
        p.exit(2, f'error: {exc}\n')
    print(json.dumps(dict(selected=result['selected'], evidence=str(a.out.resolve()))))


if __name__ == '__main__':
    main()
