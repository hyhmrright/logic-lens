#!/usr/bin/env python3
"""
Grade iteration-N outputs against the assertion rules in evals-v2.json.

Usage:
  python3 scripts/grade-iteration.py skills-workspace/iteration-2

Writes:
  <iter_dir>/summary.json  — per-case pass_rate + overall stats
  Prints a summary table to stdout.
"""

from __future__ import annotations
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EVALS = json.load((REPO / "evals/v2/evals-v2.json").open())["evals"]
EVALS_BY_ID = {e["id"]: e for e in EVALS}

# Chinese character detection
CJK = re.compile(r'[一-鿿]')


def count_chinese(text: str) -> int:
    return len(CJK.findall(text))


def is_chinese_output(text: str) -> bool:
    """Chinese output if CJK >= 50 chars AND no line-start English section headers."""
    if count_chinese(text) < 50:
        return False
    # Check for disallowed English section headers as full lines
    bad_headers = [
        r'^#\s*Findings\s*$',
        r'^##\s*Findings\s*$',
        r'^#\s*Summary\s*$',
        r'^##\s*Summary\s*$',
        r'^#\s*Scope\s*$',
        r'^#\s*Mode\s*$',
    ]
    for line in text.splitlines():
        for pat in bad_headers:
            if re.match(pat, line.strip()):
                return False
    return True


def check(text: str, rules: list[tuple[str, callable]]) -> list[dict]:
    """Run list of (description, predicate) rules against text."""
    results = []
    for desc, pred in rules:
        try:
            ok = bool(pred(text))
        except Exception as e:
            ok = False
            desc = f"{desc} [grader error: {e}]"
        results.append({"text": desc, "passed": ok})
    return results


def grade_case(case_id: int, output_path: Path) -> dict:
    case = EVALS_BY_ID.get(case_id)
    if not case:
        return {"eval_id": case_id, "error": "no such case in evals-v2.json"}
    if not output_path.exists():
        return {
            "eval_id": case_id,
            "name": case["name"],
            "mode": case["mode"],
            "error": f"missing: {output_path}",
            "expectations": [],
            "pass_rate": 0.0,
        }
    text = output_path.read_text(encoding="utf-8")
    name = case["name"]
    is_zh_case = name.startswith("zh-")

    rules: list[tuple[str, callable]] = []

    # Language assertion for Chinese cases
    if is_zh_case:
        rules.append(("output is chinese (>=50 CJK chars, no English section headers)", is_chinese_output))

    # Universal: four-field labels present
    if case["mode"] != "logic-explain":
        rules.append((
            "has Premises + Trace + Divergence labels (EN or ZH)",
            lambda t: (("Premises" in t or "前提" in t) and
                       ("Trace" in t or "追踪" in t) and
                       ("Divergence" in t or "偏差" in t))
        ))

    # Per-case specific rules
    if case_id == 1:
        rules += [
            ("contains 'L1'", lambda t: "L1" in t),
            ("mentions module-level format", lambda t: re.search(r'module[- ]level|模块级|module\.format|formatter\.py', t, re.I) is not None),
            ("mentions (formatted) suffix or appended suffix", lambda t: "(formatted)" in t or "formatted" in t.lower()),
        ]
    elif case_id == 5:
        rules += [
            ("explains var scoping/hoisting", lambda t: re.search(r'\bvar\b|hoist|hoisted|function[- ]scoped', t, re.I) is not None),
            ("mentions closure reference to i", lambda t: re.search(r'closure|reference|same variable|共享|引用', t, re.I) is not None),
            ("states final value is 3 or similar", lambda t: re.search(r'\b3\b.*clicked|Button 3|all three.*3|loop end|termination value|i = 3', t, re.I) is not None),
            ("no Logic Score line", lambda t: not re.search(r'Logic Score|逻辑评分', t)),
        ]
    elif case_id == 6:
        rules += [
            ("contains verdict", lambda t: re.search(r'Semantically Equivalent|Conditionally Equivalent|Semantically Divergent|语义等价|条件等价|语义分歧', t) is not None),
            ("conditionally equivalent identified", lambda t: re.search(r'Conditionally Equivalent|条件等价', t, re.I) is not None),
            ("describes divergence scenario", lambda t: re.search(r'generator|non-list|custom|IndexError|__getitem__|__len__', t) is not None),
        ]
    elif case_id == 7:
        rules += [
            ("computes start = 6 from 2*3", lambda t: re.search(r'\b2\s*\*\s*3\s*=\s*6\b|start\s*=\s*6\b|偏移\s*=\s*6', t) is not None),
            ("identifies 0/1-based indexing mismatch", lambda t: re.search(r'0[-\s]?based|1[-\s]?based|zero-indexed|one-indexed|从 0 开始|从 1 开始', t, re.I) is not None),
            ("contains L3 or L6", lambda t: "L3" in t or "L6" in t),
            ("has Fault Confidence", lambda t: re.search(r'Fault Confidence|故障置信度|Confidence:', t) is not None),
        ]
    elif case_id == 8:
        rules += [
            ("has Module Breakdown", lambda t: re.search(r'Module Breakdown|模块分布', t) is not None),
            ("identifies SQL f-string interpolation", lambda t: re.search(r"f[\"']|f-string|interpolat|SQL 注入|字符串拼接|user_id\s*=\s*\{", t, re.I) is not None),
            ("Logic Score below 100", lambda t: bool(re.search(r'Logic Score[:\s]*([0-9]{1,2})/100|逻辑评分[:\s]*([0-9]{1,2})/100', t))),
            ("identifies unconditional True in delete_user", lambda t: re.search(r'unconditional|always return|无条件|总是返回.*True|delete_user', t, re.I) is not None),
        ]
    elif case_id == 9:
        rules += [
            ("has Fix Log", lambda t: re.search(r'Fix Log|修复记录', t) is not None),
            ("has before and after score", lambda t: re.search(r'before[:\s]+[0-9]+|Logic Score \(before\)|改前', t, re.I) is not None and re.search(r'after[:\s]+[0-9]+|Logic Score \(after\)|改后', t, re.I) is not None),
            ("fixes null guard in get_session", lambda t: re.search(r'get_session.*(?:None|null|guard|check)|is not None|!= None', t, re.I | re.DOTALL) is not None),
        ]
    elif case_id == 100:
        rules += [
            ("contains L4", lambda t: "L4" in t),
            ("mentions skip/consecutive elements", lambda t: re.search(r'skip|skipped|跳过|相邻|连续', t, re.I) is not None),
            ("identifies mutation during iteration", lambda t: re.search(r'modif|mutat|edit|change.*during|iter.*remove|遍历.*删除|迭代.*修改', t, re.I) is not None),
        ]
    elif case_id == 102:
        rules += [
            ("explains lazy evaluation / generator semantics", lambda t: re.search(r'lazy|generator|yield|StopIteration|惰性|生成器', t, re.I) is not None),
            ("no Logic Score line", lambda t: not re.search(r'Logic Score|逻辑评分', t)),
        ]
    elif case_id == 104:
        rules += [
            ("contains verdict", lambda t: re.search(r'Semantically Equivalent|Conditionally Equivalent|Semantically Divergent|语义等价|条件等价|语义分歧', t) is not None),
            ("identifies = NULL issue", lambda t: re.search(r'= NULL|IS NULL|三值|UNKNOWN|永假|always false|NULL 比较|三值逻辑', t) is not None),
        ]
    elif case_id == 106:
        rules += [
            ("identifies undefined access", lambda t: re.search(r'undefined|null|空|未定义', t, re.I) is not None),
            ("has Fault Confidence", lambda t: re.search(r'Fault Confidence|故障置信度', t) is not None),
        ]
    elif case_id == 108:
        rules += [
            ("has Module Breakdown", lambda t: re.search(r'Module Breakdown|模块分布', t) is not None),
            ("Logic Score below 100", lambda t: bool(re.search(r'Logic Score[:\s]*([0-9]{1,2})/100|逻辑评分[:\s]*([0-9]{1,2})/100', t))),
            ("identifies at least 3 findings", lambda t: sum(1 for _ in re.finditer(r'(?m)^### (?:🔴|🟡|🟢)', t)) >= 3),
        ]
    elif case_id == 110:
        rules += [
            ("has Fix Log", lambda t: re.search(r'Fix Log|修复记录', t) is not None),
            ("has before and after score", lambda t: re.search(r'before|改前|修复前|之前', t, re.I) is not None and re.search(r'after|改后|修复后|之后', t, re.I) is not None),
        ]

    expectations = check(text, rules)
    passed = sum(1 for e in expectations if e["passed"])
    pass_rate = passed / len(expectations) if expectations else 0.0

    return {
        "eval_id": case_id,
        "name": case["name"],
        "mode": case["mode"],
        "is_zh": is_zh_case,
        "char_count": len(text),
        "chinese_chars": count_chinese(text),
        "expectations": expectations,
        "passed": passed,
        "total": len(expectations),
        "pass_rate": pass_rate,
    }


def main(iter_dir: Path):
    case_ids = []
    for d in sorted(iter_dir.glob("eval-*")):
        m = re.match(r"eval-(\d+)(?:-.*)?$", d.name)
        if m:
            case_ids.append(int(m.group(1)))

    results = []
    for cid in case_ids:
        # support both eval-<id> and eval-<id>-<name> directory names
        candidates = list(iter_dir.glob(f"eval-{cid}/output.md")) + list(iter_dir.glob(f"eval-{cid}-*/output.md"))
        output_path = candidates[0] if candidates else iter_dir / f"eval-{cid}" / "output.md"
        r = grade_case(cid, output_path)
        results.append(r)
        (output_path.parent / "grading.json").write_text(json.dumps(r, ensure_ascii=False, indent=2))

    # Summary
    by_mode: dict[str, list] = {}
    for r in results:
        if "error" in r and "mode" not in r:
            continue
        by_mode.setdefault(r["mode"], []).append(r)

    per_mode = {}
    for mode, rs in by_mode.items():
        rates = [r["pass_rate"] for r in rs if "pass_rate" in r]
        per_mode[mode] = {
            "n": len(rs),
            "avg_pass_rate": sum(rates) / len(rates) if rates else 0.0,
        }

    zh_results = [r for r in results if r.get("is_zh")]
    zh_lang_pass = sum(1 for r in zh_results for e in r.get("expectations", [])
                       if "chinese" in e["text"].lower() and e["passed"])
    zh_lang_total = sum(1 for r in zh_results for e in r.get("expectations", [])
                        if "chinese" in e["text"].lower())

    overall_rates = [r["pass_rate"] for r in results if "pass_rate" in r]

    summary = {
        "iteration_dir": str(iter_dir.relative_to(REPO)),
        "cases_graded": len(results),
        "overall_pass_rate": sum(overall_rates) / len(overall_rates) if overall_rates else 0.0,
        "per_mode": per_mode,
        "chinese_language_pass": f"{zh_lang_pass}/{zh_lang_total}",
        "per_case": [
            {"id": r["eval_id"], "name": r["name"], "mode": r["mode"],
             "pass_rate": r.get("pass_rate", 0.0),
             "passed": r.get("passed", 0), "total": r.get("total", 0)}
            for r in results
        ],
    }

    (iter_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    # Human-readable table
    print(f"\n{'case':<6} {'mode':<16} {'pass':<8} {'details'}")
    print("-" * 80)
    for r in results:
        if "error" in r and not r.get("expectations"):
            print(f"{r['eval_id']:<6} {'MISSING':<16} {'--':<8} {r.get('error', '')}")
            continue
        zh_tag = "[ZH]" if r.get("is_zh") else "    "
        rate = f"{r['passed']}/{r['total']}"
        print(f"{r['eval_id']:<6} {r['mode']:<16} {rate:<8} {zh_tag} {r['name']}")

    print(f"\nOverall pass_rate: {summary['overall_pass_rate']:.3f} (n={len(overall_rates)})")
    print(f"Chinese language assertion: {summary['chinese_language_pass']}")
    print(f"Summary written to: {iter_dir / 'summary.json'}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: grade-iteration.py <iteration-dir>")
    main(Path(sys.argv[1]).resolve())
