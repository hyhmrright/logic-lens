#!/usr/bin/env python3
"""
Grade iteration-N outputs against the assertion rules in evals/content/v2/evals-v2.json.

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
from typing import Callable

REPO = Path(__file__).resolve().parent.parent
_EVALS_CANDIDATES = [
    REPO / "evals/content/v2/evals-v2.json",
    REPO / "evals/v2/evals-v2.json",
]
for _evals_path in _EVALS_CANDIDATES:
    if _evals_path.exists():
        EVALS_SOURCE = _evals_path
        break
else:
    raise FileNotFoundError("could not find evals-v2.json in evals/content/v2 or evals/v2")

EVALS = json.load(EVALS_SOURCE.open())["evals"]
EVALS_BY_ID = {e["id"]: e for e in EVALS}

CJK = re.compile(r'[一-鿿]')

# Matches English section-header lines that disqualify Chinese output.
# Findings/Summary match both # and ##; Scope/Mode match only # — preserving
# the exact original bad_headers list (## Scope / ## Mode were not in it).
# strip() is applied to each line before matching to ignore leading/trailing space.
_BAD_HEADER_RE = re.compile(
    r'^(?:#{1,2}\s*(?:Findings|Summary)|#\s*(?:Scope|Mode))\s*$'
)

# Pre-compiled literal patterns for the case-201 leak-path counter.
_CASE201_PATH_PATTERNS = [
    re.compile(re.escape(p), re.I) for p in [
        'empty data', 'nothing to upload', 'UploadError',
        'exception handler', 'non-UploadError', 'open(', 'file handle',
    ]
]


def count_chinese(text: str) -> int:
    return len(CJK.findall(text))


def is_chinese_output(text: str) -> bool:
    """Chinese output if CJK >= 50 chars AND no line-start English section headers."""
    if count_chinese(text) < 50:
        return False
    return not any(_BAD_HEADER_RE.match(line.strip()) for line in text.splitlines())


def check(text: str, rules: list[tuple[str, Callable[[str], bool]]]) -> list[dict]:
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


# ── Per-case helper predicates (module-level for testability) ──────────────────

def _case200_await_boundary(t: str) -> bool:
    yield_pt = re.search(r'await|asyncio\.sleep|yield|挂起|suspend|让出', t, re.I)
    interleave = re.search(r'event[- ]?loop|other.{0,15}coroutin|interleav|交错|调度|reschedul', t, re.I)
    return bool(yield_pt) and bool(interleave)


def _case201_multiple_leak_paths(t: str) -> bool:
    hits = sum(1 for p in _CASE201_PATH_PATTERNS if p.search(t))
    release = re.search(
        r'(?:not\s+)?clos(?:e|ed)|release|leak|never.{0,15}(?:close|release)|未释放|泄漏', t, re.I)
    return hits >= 2 and release is not None


def _case204_not_ready_leak(t: str) -> bool:
    anchor = re.search(r'is_ready\(\)|not\s+job\.is_ready|if not job\.is_ready', t, re.I)
    release = re.search(r'(?:pool\.)?release|未释放', t, re.I)
    return anchor is not None and release is not None


def _case208_both_skip_paths(t: str) -> bool:
    unauth = re.search(r'unauthorized|_unauthorized|return.*401|authorization.*fail|未授权|授权.*失败', t, re.I)
    malformed = re.search(r'BadRequest|malformed|raise|400|请求.*格式|格式.*错误', t, re.I)
    audit = re.search(r'audit_log\.record|audit.*record|audit.*skip|audit.*log|审计.*跳过|skip.*audit', t, re.I)
    return unauth is not None and malformed is not None and audit is not None


def _no_logic_score(t: str) -> bool:
    return not re.search(r'Logic Score|逻辑评分', t)


def _no_bug_conclusion(t: str) -> bool:
    """Model concludes no significant logic bug exists."""
    return re.search(
        r'no\s+(?:significant\s+)?(?:logic\s+)?(?:bug|error|issue|problem|flaw|defect|finding)'
        r'|code\s+is\s+correct|this\s+is\s+(?:the\s+)?correct\s+(?:pattern|approach|idiom)'
        r'|no\s+(?:logic\s+)?(?:finding|divergence)\s+(?:found|identified|detected)'
        r'|concern\s+is\s+(?:unfounded|not\s+valid|incorrect)'
        r'|没有.*(?:问题|bug|错误|缺陷)|代码.*正确|这段代码.*正确'
        r'|Divergence\s*[:\-]\s*(?:None|无|没有|不存在)'
        r'|no\s+divergence\s+found|未发现.*(?:问题|错误)',
        t, re.I
    ) is not None


def _score_above_80(t: str) -> bool:
    """Logic Score is 80 or above. Accepts both '88/100' and '88 / 100'."""
    matches = re.findall(
        r'Logic Score[^0-9]{0,20}(\d{1,3})\s*/\s*100|逻辑评分[^0-9]{0,20}(\d{1,3})\s*/\s*100', t, re.I
    )
    for m in matches:
        score = int(m[0] or m[1])
        if score >= 80:
            return True
    return False


def _equivalent_verdict(t: str) -> bool:
    """Model gives Semantically Equivalent verdict (not Divergent)."""
    return re.search(
        r'Semantically Equivalent|语义等价|完全等价|semantically identical'
        r'|are\s+(?:semantically\s+)?equivalent|两者.*等价|行为.*(?:相同|一致)',
        t, re.I
    ) is not None and re.search(
        r'NOT\s+(?:semantically\s+)?equivalent|语义分歧|不等价|are\s+not\s+equivalent',
        t, re.I
    ) is None


def _case227_score_improved(t: str) -> bool:
    def _extract(label_pat: str) -> int | None:
        m = re.search(rf'{label_pat}[^\n0-9]{{0,25}}(\d{{1,3}})(?:/100)?', t, re.I)
        return int(m.group(1)) if m else None
    before = _extract(r'(?:Logic Score\s*\(?\s*(?:before|改前|修复前)\)?|改前|修复前)')
    after  = _extract(r'(?:Logic Score\s*\(?\s*(?:after|改后|修复后)\)?|改后|修复后)')
    if before is not None and after is not None:
        return after > before
    scores = [int(m.group(1)) for m in re.finditer(r'Logic Score[^0-9]{0,25}(\d{1,3})/100', t)]
    return len(scores) >= 2 and scores[-1] > scores[0]


# ── Shared rules reused across multiple cases ──────────────────────────────────

_VERDICT_RULE: tuple[str, Callable[[str], bool]] = (
    "contains verdict",
    lambda t: re.search(
        r'Semantically Equivalent|Conditionally Equivalent|Semantically Divergent'
        r'|语义等价|条件等价|语义分歧', t) is not None,
)

_NO_LOGIC_SCORE_RULE: tuple[str, Callable[[str], bool]] = (
    "no Logic Score line", _no_logic_score,
)

_FAULT_CONFIDENCE_RULE: tuple[str, Callable[[str], bool]] = (
    "has Fault Confidence",
    lambda t: re.search(r'Fault Confidence|故障置信度|Confidence:', t) is not None,
)

_FIX_LOG_RULE: tuple[str, Callable[[str], bool]] = (
    "has Fix Log",
    lambda t: re.search(r'Fix Log|修复记录|修复日志|变更说明|修复清单|修复汇总', t) is not None,
)

_LOGIC_SCORE_BELOW_100_RULE: tuple[str, Callable[[str], bool]] = (
    "Logic Score below 100",
    lambda t: bool(re.search(r'Logic Score[^0-9]{0,15}([0-9]{1,2})/100|逻辑评分[^0-9]{0,15}([0-9]{1,2})/100', t)),
)

_FOUR_FIELD_RULE: tuple[str, Callable[[str], bool]] = (
    "has Premises + Trace + Divergence labels (EN or ZH)",
    lambda t: (
        ("Premises" in t or "前提" in t) and
        ("Trace" in t or "追踪" in t) and
        ("Divergence" in t or "偏差" in t or
         re.search(r'\*\*发现|发现的逻辑|\*\*Findings?\b', t) is not None)
    ),
)

_BOTH_VERSIONS_RULE: tuple[str, Callable[[str], bool]] = (
    "analyzes both Version A and Version B",
    lambda t: (
        re.search(r'Version\s*A|版本\s*A|代码\s*A', t, re.I) is not None and
        re.search(r'Version\s*B|版本\s*B|代码\s*B', t, re.I) is not None
    ),
)

_DIVERGENT_RULE: tuple[str, Callable[[str], bool]] = (
    "gives Semantically Divergent verdict",
    lambda t: re.search(r'Semantically Divergent|语义分歧|语义.*不等价', t) is not None,
)


# ── Common assertion helpers ──────────────────────────────────────────────────

def _has_logic_score(t: str) -> bool:
    return re.search(r'Logic Score|逻辑评分', t, re.I) is not None


def _has_before_after_scores(t: str) -> bool:
    return (
        re.search(r'Logic Score\s*\(before\)|before[:\s]+[0-9]+|改前|修复前', t, re.I) is not None and
        re.search(r'Logic Score\s*\(after\)|after[:\s]+[0-9]+|改后|修复后', t, re.I) is not None
    )


def _score_improved(t: str) -> bool:
    return _case227_score_improved(t)


_LOGIC_SCORE_RULE: tuple[str, Callable[[str], bool]] = (
    "has Logic Score", _has_logic_score,
)


_BEFORE_AFTER_SCORE_RULE: tuple[str, Callable[[str], bool]] = (
    "has before and after Logic Score", _has_before_after_scores,
)


# ── Per-case extra rules (keyed by case id) ────────────────────────────────────

_CASE_EXTRA_RULES: dict[int, list[tuple[str, Callable[[str], bool]]]] = {
    1: [
        ("identifies L1 shadow override", lambda t: "L1" in t or re.search(
            r'shadow.*override|命名遮蔽|name.*shadow|builtin.*shadow|遮蔽.*内置|内置.*遮蔽|shadows.*built',
            t, re.I) is not None),
        ("mentions module-level format", lambda t: re.search(
            r'module[- ]level|模块级|module\.format|formatter\.py', t, re.I) is not None),
        ("mentions (formatted) suffix or appended suffix",
         lambda t: "(formatted)" in t or "formatted" in t.lower()),
    ],
    5: [
        ("explains var scoping/hoisting", lambda t: re.search(
            r'\bvar\b|hoist|hoisted|function[- ]scoped', t, re.I) is not None),
        ("mentions closure reference to i", lambda t: re.search(
            r'closure|reference|same variable|共享|引用', t, re.I) is not None),
        ("states final value is 3 or similar", lambda t: re.search(
            r'\b3\b.*clicked|Button 3|all three.*3|loop end|termination value|i = 3', t, re.I) is not None),
        _NO_LOGIC_SCORE_RULE,
    ],
    6: [
        _VERDICT_RULE,
        ("conditionally equivalent identified", lambda t: re.search(
            r'Conditionally Equivalent|条件等价|不完全等价|部分等价', t, re.I) is not None),
        ("describes divergence scenario", lambda t: re.search(
            r'generator|non-list|custom|IndexError|__getitem__|__len__', t) is not None),
    ],
    7: [
        ("computes start = 6 from 2*3", lambda t: re.search(
            r'\b2\s*[*×]\s*3\s*=\s*6\b|start\s*=\s*6\b|偏移\s*=\s*6'
            r'|2\s*×\s*3(?!\d)|page\s*\*\s*page_size.*=\s*6\b|items\[6[^\d]', t) is not None),
        ("identifies 0/1-based indexing mismatch", lambda t: re.search(
            r'0[-\s]?based|1[-\s]?based|zero-indexed|one-indexed|0-indexed|1-indexed|从 0 开始|从 1 开始', t, re.I) is not None),
        ("contains L3 or L6", lambda t: "L3" in t or "L6" in t),
        _FAULT_CONFIDENCE_RULE,
    ],
    8: [
        ("has Module Breakdown", lambda t: re.search(r'Module Breakdown|模块分布', t) is not None),
        ("identifies SQL f-string interpolation", lambda t: re.search(
            r'f["\']|f-string|interpolat|SQL 注入|字符串拼接|user_id\s*=\s*\{', t, re.I) is not None),
        _LOGIC_SCORE_BELOW_100_RULE,
        ("identifies unconditional True in delete_user", lambda t: re.search(
            r'unconditional|always return|无条件|总是返回.*True|delete_user', t, re.I) is not None),
    ],
    9: [
        _FIX_LOG_RULE,
        ("has before and after score", lambda t: (
            re.search(r'before[:\s]+[0-9]+|Logic Score \(before\)|改前', t, re.I) is not None and
            re.search(r'after[:\s]+[0-9]+|Logic Score \(after\)|改后', t, re.I) is not None)),
        ("fixes null guard in get_session", lambda t: re.search(
            r'get_session.*(?:None|null|guard|check)|is not None|!= None', t, re.I | re.DOTALL) is not None),
    ],
    10: [
        _FIX_LOG_RULE,
        ("identifies shared root cause across call sites", lambda t: re.search(
            r'shared root|call sites|root[- ]cause|同一根因|多个调用点|共享.*根因|root.*fix|one fix', t, re.I) is not None),
        ("acknowledges || 5000 fallback is correct (not a bug)", lambda t: re.search(
            r'not a bug|correct.*(?:default|fallback|pattern|intentional)|intentional.*(?:default|fallback)'
            r'|有意.*默认|正确.*默认|不是.*bug', t, re.I | re.S) is not None),
    ],
    100: [
        ("contains L4", lambda t: "L4" in t),
        ("mentions skip/consecutive elements", lambda t: re.search(
            r'skip|skipped|跳过|相邻|连续', t, re.I) is not None),
        ("identifies mutation during iteration", lambda t: re.search(
            r'modif|mutat|edit|change.*during|iter.*remove|遍历.*删除|迭代.*修改', t, re.I) is not None),
    ],
    101: [
        ("contains L6", lambda t: "L6" in t),
        ("traces cross-file into gateway", lambda t: re.search(
            r'gateway\.py|gateway\.charge|payments/|跨文件', t) is not None),
        ("identifies amount=0 returns None", lambda t: re.search(
            r'amount\s*=\s*0|amount == 0|amount is 0|amount equals 0|金额为 0', t, re.I) is not None),
    ],
    102: [
        ("explains lazy evaluation / generator semantics", lambda t: re.search(
            r'lazy|generator|yield|StopIteration|惰性|生成器', t, re.I) is not None),
        _NO_LOGIC_SCORE_RULE,
    ],
    103: [
        ("explains microtask / promise order", lambda t: re.search(
            r'microtask|event loop|promise.*queue|await', t, re.I) is not None),
        ("no Logic Score line (explain mode)", _no_logic_score),
    ],
    104: [
        _VERDICT_RULE,
        ("identifies = NULL issue", lambda t: re.search(
            r'= NULL|IS NULL|三值|UNKNOWN|永假|always false|NULL 比较|三值逻辑', t) is not None),
    ],
    105: [
        ("identifies nil-interface-vs-nil-pointer trap", lambda t: re.search(
            r'interface.*non-nil|non-nil.*interface|nil pointer wrapped|interface value is non-nil'
            r'|即使.*nil|接口值.*非 nil|interface != nil', t, re.I) is not None),
        _VERDICT_RULE,
    ],
    106: [
        ("identifies undefined access", lambda t: re.search(
            r'undefined|null|空|未定义', t, re.I) is not None),
        ("has Fault Confidence", lambda t: re.search(r'Fault Confidence|故障置信度', t) is not None),
    ],
    107: [
        ("contains L7 (concurrency hazard, not L4)", lambda t: "L7" in t),
        ("identifies race / non-atomic increment", lambda t: re.search(
            r'race|non-atomic|原子|数据竞争|并发|GIL|lock', t, re.I) is not None),
        ("has Fault Confidence", lambda t: re.search(r'Fault Confidence|故障置信度', t) is not None),
    ],
    108: [
        ("has Module Breakdown", lambda t: re.search(r'Module Breakdown|模块分布', t) is not None),
        _LOGIC_SCORE_BELOW_100_RULE,
        ("identifies at least 3 findings", lambda t: sum(
            1 for _ in re.finditer(r'(?m)^### (?:🔴|🟡|🟢)', t)) >= 3),
    ],
    109: [
        ("identifies systemic L6 pattern", lambda t: (
            re.search(r'systemic|Systemic Patterns|系统性', t, re.I) is not None) and ("L6" in t)),
        ("has Module Breakdown", lambda t: re.search(r'Module Breakdown|模块分布', t) is not None),
    ],
    110: [
        _FIX_LOG_RULE,
        ("has before and after score", lambda t: (
            re.search(r'before|改前|修复前|之前', t, re.I) is not None and
            re.search(r'after|改后|修复后|之后', t, re.I) is not None)),
    ],
    200: [
        ("contains L7 (concurrency hazard)", lambda t: "L7" in t),
        ("identifies await yield point + interleaving", _case200_await_boundary),
        ("recommends semaphore or async lock", lambda t: re.search(
            r'asyncio\.Semaphore|asyncio\.Lock|Semaphore|atomic.*slot|信号量', t, re.I) is not None),
    ],
    201: [
        ("contains L8 (resource lifecycle)", lambda t: "L8" in t),
        ("identifies multiple leak paths", _case201_multiple_leak_paths),
        ("recommends with-statement or try/finally", lambda t: re.search(
            r'with[- ]statement|with statement|context manager|try.*finally|try / finally|try-finally',
            t, re.I) is not None),
    ],
    202: [
        ("contains L9 (time/locale hazard)", lambda t: "L9" in t),
        ("identifies naive vs aware datetime", lambda t: re.search(
            r'naive|tzinfo|timezone[- ]aware|no timezone|missing.*zone|无时区|naive datetime',
            t, re.I) is not None),
        ("identifies DST transition effect", lambda t: re.search(
            r'DST|daylight saving|spring[- ]forward|wall[- ]clock|wall clock|23 hour|23-hour|夏令时|夏时制',
            t, re.I) is not None),
    ],
    203: [
        ("contains L7 (not L4)", lambda t: "L7" in t),
        ("identifies loop variable capture by closures", lambda t: re.search(
            r'loop variable|capture|shared.*variable|共享.*变量|闭包捕获|引用捕获|per[- ]iteration',
            t, re.I) is not None),
        ("recommends per-iteration shadow or parameter passing", lambda t: re.search(
            r'u := u|copy.*loop|shadow|pass.*as.*parameter|作为参数|局部变量|Go 1\.22', t, re.I) is not None),
    ],
    204: [
        ("contains L8 (resource lifecycle)", lambda t: "L8" in t),
        ("identifies not-ready early return as leak path", _case204_not_ready_leak),
        ("connects leak to pool exhaustion", lambda t: re.search(
            r'pool size|20 (?:slot|connection|jobs?)|exhaust|耗尽|连接池', t, re.I) is not None),
        _FAULT_CONFIDENCE_RULE,
    ],
    205: [
        ("verdict CE or Divergent (both defensible under en-US)", lambda t: re.search(
            r'Conditionally Equivalent|Semantically Divergent|条件等价|语义分歧', t) is not None),
        ("contains L9 (locale hazard)", lambda t: "L9" in t),
        ("explains UTF-16 codepoint vs locale collation", lambda t: re.search(
            r'UTF-?16|code[- ]?point|code unit|locale[- ]aware|collation|locale.*compar'
            r'|区分大小写|locale 排序|本地化排序', t, re.I) is not None),
    ],
    206: [
        ("contains L2 (type contract breach)", lambda t: "L2" in t),
        ("identifies operator-mix coercion fragility", lambda t: re.search(
            r'\+.*concat|concat.*\+|string concat|implicit.*coerc|numeric.*coerc|operator.*mix'
            r'|fragile|fragility|brittle|brittleness|silent.*string', t, re.I) is not None),
        ("recommends explicit Number() / parseFloat / boundary validation", lambda t: re.search(
            r'Number\(|parseFloat|parseInt|explicit.*coerc|boundary.*validat|input.*validat'
            r'|sanitize.*input|强制.*类型|显式.*转换', t, re.I) is not None),
    ],
    207: [
        ("contains L2 (type contract breach)", lambda t: "L2" in t),
        ("identifies str vs int comparison TypeError", lambda t: re.search(
            r"str.*int|int.*str|字符串.*整数|整数.*字符串|TypeError|'>='.*not supported"
            r"|不支持.*比较|类型.*不匹配", t, re.I) is not None),
        ("recommends int() coercion at boundary", lambda t: re.search(
            r"int\s*\(\s*age\s*\)|int\(.*\)|coerce|强制.*int|显式.*转换|入口.*校验|boundary.*validat",
            t, re.I) is not None),
    ],
    208: [
        ("contains L5 (control flow escape)", lambda t: "L5" in t),
        ("identifies both early exits skip audit_log.record", _case208_both_skip_paths),
        ("recommends move-to-entry or try/finally", lambda t: re.search(
            r"function\s+entry|move.*to\s+(?:the\s+)?entry|first\s+line|try.*finally|finally\s+block"
            r"|single\s+exit|前置|入口处|提到函数开头", t, re.I) is not None),
    ],
    209: [
        ("contains L5 (control flow escape)", lambda t: "L5" in t),
        ("identifies _error(400) early return as the skip path", lambda t: re.search(
            r"_error\(400\)|return.*_error|is_valid|400\b|invalid.*input|invalid.*request"
            r"|无效请求|提前返回|早返回", t, re.I) is not None),
        ("recommends moving the increment before the validation guard", lambda t: re.search(
            r"before.*(?:guard|validation|check|is_valid)|move.*(?:metric|increment).*entry"
            r"|function\s+entry|first\s+line|提到.*入口|放到.*开头|放到.*第一行", t, re.I) is not None),
        _FAULT_CONFIDENCE_RULE,
    ],
    210: [
        ("identifies L2", lambda t: "L2" in t),
        ("identifies as-cast is compile-time only with no runtime validation", lambda t: re.search(
            r'compile[- ]?time|no\s+runtime|runtime.*validat|as\s+User.*no|type.*assert'
            r'|no.*structural|不做.*运行时', t, re.I) is not None),
        ("identifies email undefined causes TypeError", lambda t: re.search(
            r'undefined|TypeError|toUpperCase.*undefined|email.*undefined|undefined.*email',
            t, re.I) is not None),
        ("recommends runtime validation or schema library", lambda t: re.search(
            r"'email'\s+in\s+data|zod|schema.*validat|runtime.*check|structural.*check"
            r"|运行时.*校验|校验.*结构", t, re.I) is not None),
    ],
    211: [
        ("identifies L2 or L3", lambda t: "L2" in t or "L3" in t),
        ("explains IEEE 754 float representation issue", lambda t: re.search(
            r'IEEE\s*754|float.*precis|binary.*float|floating[- ]?point.*repr|无法.*精确|精度.*问题',
            t, re.I) is not None),
        ("traces actual value ~0.09999 (not exactly 0.1)", lambda t: re.search(
            r'0\.0999|0\.09999|not.*exactly.*0\.1|0\.1.*not.*exact|1\.0\s*-\s*0\.9|不等于.*0\.1',
            t, re.I) is not None),
        ("recommends math.isclose or integer cents", lambda t: re.search(
            r'math\.isclose|isclose|rel_tol|epsilon|integer.*cent|整数.*分钱|round.*compar',
            t, re.I) is not None),
    ],
    212: [
        ("identifies L7", lambda t: "L7" in t),
        ("identifies opposite lock acquisition order", lambda t: re.search(
            r'opposite.*order|reverse.*order|lock.*order|cache.*mu.*logger.*mu|logger.*mu.*cache.*mu'
            r'|反向.*加锁|加锁.*顺序.*不同|different.*order', t, re.I) is not None),
        ("traces circular wait deadlock scenario", lambda t: re.search(
            r'circular.*wait|dead.?lock|goroutine.*hold.*wait|相互.*等待|死锁|circular dependency',
            t, re.I) is not None),
        ("recommends consistent global lock order", lambda t: re.search(
            r'consistent.*order|same.*order|global.*order|固定.*顺序|统一.*加锁|always.*(?:cache|logger).*first',
            t, re.I) is not None),
    ],
    213: [
        ("identifies L3 or L6", lambda t: "L3" in t or "L6" in t),
        ("identifies N+1 query pattern", lambda t: re.search(
            r'N\s*\+\s*1|n\+1|N\+1|per[- ]row.*quer|one.*quer.*per|loop.*quer|每.*(?:order|row).*查询',
            t, re.I) is not None),
        ("quantifies scale impact: ~10001 queries for 10000 orders", lambda t: re.search(
            r'10[,\s]?001|10001|10,?000.*\+\s*1|N\+1.*10,?000|1\s*\+\s*N.*10,?000',
            t, re.I) is not None),
        ("recommends JOIN or batch fetch", lambda t: re.search(
            r'\bJOIN\b|batch.*fetch|single.*quer|WHERE.*\bIN\b|ANY\s*\(|批量.*查询|联合.*查询',
            t, re.I) is not None),
    ],
    214: [
        ("identifies L6", lambda t: "L6" in t),
        ("identifies Optional.get() without isPresent throws NoSuchElementException", lambda t: re.search(
            r'Optional\.get|isPresent|NoSuchElement|get\(\).*empty|empty.*Optional',
            t, re.I) is not None),
        ("traces call chain: sendWelcome → getUserEmail → findById → throws", lambda t: re.search(
            r'sendWelcome|getUserEmail|findById', t, re.I) is not None),
        ("recommends safe Optional API", lambda t: re.search(
            r'orElseThrow|orElse|ifPresent|Optional.*map|isPresent\(\)|safe.*Optional',
            t, re.I) is not None),
    ],
    215: [
        ("identifies L3", lambda t: "L3" in t),
        ("identifies debug vs release overflow behavior difference", lambda t: re.search(
            r'debug.*(?:panic|release)|release.*(?:wrap|silent)|build[- ]?mode|--release'
            r'|debug 模式|release 模式|debug.*build|release.*build', t, re.I) is not None),
        ("identifies silent wrap in release mode", lambda t: re.search(
            r'silent.*wrap|wrap.*silently|modulo.*256|two.*complement|wraps.*around|静默.*回绕|overflow.*wrap',
            t, re.I) is not None),
        ("recommends wrapping_add or explicit overflow primitive", lambda t: re.search(
            r'wrapping_add|checked_add|saturating_add|Wrapping<u8>|显式.*溢出|wrapping.*add',
            t, re.I) is not None),
    ],
    216: [
        ("identifies L5 or describes exception swallowing control-flow risk", lambda t: "L5" in t or re.search(
            r'bare.*except|except:\s*pass|吞.*异常|异常.*吞|swallow.*exception|silence.*exception'
            r'|裸.*except', t, re.I) is not None),
        ("identifies KeyboardInterrupt swallowed preventing Ctrl+C exit", lambda t: re.search(
            r'KeyboardInterrupt|Ctrl.*C|ctrl.*c|系统.*中断|无法.*退出|不能.*退出|keyboard.*interrupt',
            t, re.I) is not None),
        ("recommends except Exception or specific exception type", lambda t: re.search(
            r'except\s+Exception|except\s+\w+Error|具体.*异常|精确.*异常|specific.*exception'
            r'|替换.*bare.*except', t, re.I) is not None),
    ],
    217: [
        ("explains deferred / lazy LINQ execution", lambda t: re.search(
            r'defer|lazy|deferred.*execution|lazy.*evaluation|lazily|惰性|延迟.*执行|not.*execut.*when.*called',
            t, re.I) is not None),
        ("states actual output is 4 5 6 (not 3 4 5)", lambda t: re.search(
            r'4\s+5\s+6|4,\s*5,\s*6|output.*4.*5.*6|prints.*4.*5.*6',
            t, re.I) is not None),
        ("explains Step 2 mutations affect query at enumeration time", lambda t: re.search(
            r'mutation|mutate|modif.*after|Step\s*2|numbers\.Add|numbers\.Remove|修改.*之后|集合.*修改',
            t, re.I) is not None),
        _NO_LOGIC_SCORE_RULE,
    ],
    218: [
        ("explains CPython small integer cache (-5 to 256)", lambda t: re.search(
            r'small.*int.*cache|cache.*small.*int|-5.*256|256.*-5|integer.*cache|intern|CPython.*cache'
            r'|小整数.*缓存|缓存.*小整数|-5\s+to\s+256', t, re.I) is not None),
        ("explains 257 outside cache range may create separate objects", lambda t: re.search(
            r'257.*outside|outside.*(?:range|cache)|beyond.*256|>\s*256|not.*cached|separate.*object'
            r'|不同.*对象|独立.*对象', t, re.I) is not None),
        ("explains same_object returns True because a and b bind to same argument n", lambda t: re.search(
            r'same.*argument|argument.*same|both.*bind.*same|both.*refer.*same|parameter.*same'
            r'|绑定.*同一|同一.*对象.*参数|a.*b.*same.*n', t, re.I) is not None),
        _NO_LOGIC_SCORE_RULE,
    ],
    219: [
        ("explains Dog.prototype = Animal.prototype shares the same object", lambda t: re.search(
            r'shared.*prototype|same.*object.*prototype|Dog\.prototype.*=.*Animal\.prototype'
            r'|引用.*赋值|同一.*对象|原型.*共享|不是.*副本', t, re.I) is not None),
        ("explains override on Dog.prototype.speak overwrites Animal.prototype.speak", lambda t: re.search(
            r'overwrit.*Animal|Animal.*overwrit|覆盖.*Animal|Animal.*speak.*覆盖|override.*Animal'
            r'|Animal\.prototype.*speak.*overrid', t, re.I) is not None),
        ("states actual cat.speak() returns 'Cat barks' not 'Cat makes a sound'", lambda t: re.search(
            r"Cat barks|cat.*barks|cat\.speak.*bark|cat.*bark", t, re.I) is not None),
        _NO_LOGIC_SCORE_RULE,
    ],
    220: [
        _VERDICT_RULE,
        _DIVERGENT_RULE,
        ("identifies == compares references not content in Java", lambda t: re.search(
            r'reference.*equali|object.*identity|reference.*compar|string.*intern|intern.*string'
            r'|== 比较.*引用|引用.*比较', t, re.I) is not None),
        ("identifies non-interned string scenario causes Version A to fail", lambda t: re.search(
            r'non[- ]?intern|new String|database.*(?:query|result)|external.*input|not.*intern'
            r'|非.*intern|未.*intern', t, re.I) is not None),
        _BOTH_VERSIONS_RULE,
    ],
    221: [
        _VERDICT_RULE,
        _DIVERGENT_RULE,
        ("identifies null causes TypeError in Version B", lambda t: re.search(
            r'null.*TypeError|TypeError.*null|null.*(?:crash|throw|error|length)|'
            r'Version B.*(?:throw|crash|TypeError)', t, re.I) is not None),
        ("identifies `as string` is compile-time only with no runtime effect", lambda t: re.search(
            r'compile[- ]?time|as string.*no.*runtime|type.*assert.*runtime|no.*runtime.*effect'
            r'|as.*类型断言.*编译', t, re.I) is not None),
        _BOTH_VERSIONS_RULE,
    ],
    222: [
        _VERDICT_RULE,
        ("identifies memory difference: list loads all lines vs generator is lazy", lambda t: re.search(
            r'O\s*\(\s*n\s*\)|O\s*\(\s*1\s*\)|内存.*O|generator.*lazy|inert|惰性|lazy.*eval'
            r'|列表.*内存|generator.*memory|全部.*加载', t, re.I) is not None),
        ("identifies large file OOM risk", lambda t: re.search(
            r'OOM|out.of.memory|large.*file|内存.*溢出|大文件|memory.*risk|内存.*不足',
            t, re.I) is not None),
        _BOTH_VERSIONS_RULE,
    ],
    223: [
        ("identifies L5", lambda t: "L5" in t),
        ("identifies missing .catch() on Promise.all chain", lambda t: re.search(
            r'\.catch\b|no.*catch|missing.*catch|catch.*handler|without.*catch|unhandled.*reject',
            t, re.I) is not None),
        ("explains Node.js 18+ exits on unhandled rejection", lambda t: re.search(
            r'Node\.?js.*18|18.*Node|unhandled.*reject.*exit|exit.*unhandled|terminate.*process'
            r'|进程.*退出|process.*(?:exit|crash|termin)', t, re.I) is not None),
        _FAULT_CONFIDENCE_RULE,
    ],
    224: [
        ("identifies L4", lambda t: "L4" in t),
        ("explains modCount structural modification counter mechanism", lambda t: re.search(
            r'modCount|modification.*count|structural.*modif|结构.*修改.*计数|iterator.*check.*modif',
            t, re.I) is not None),
        ("explains intermittent nature: only triggered when removal followed by next()", lambda t: re.search(
            r'intermit|偶发|不必现|occasionally|not.*always|last.*element|最后.*元素|hasNext',
            t, re.I) is not None),
        _FAULT_CONFIDENCE_RULE,
    ],
    225: [
        ("has Module Breakdown", lambda t: re.search(
            r'Module Breakdown|模块分布|方法分析|per[- ]method', t) is not None),
        ("identifies L8 resource leak (connection/statement not closed on all paths)", lambda t: (
            "L8" in t and re.search(
                r'(?:conn|stmt|rs|ResultSet|Connection|Statement).*(?:not.*clos|leak|never.*clos)',
                t, re.I) is not None)),
        ("identifies SQL string concatenation as logic risk", lambda t: re.search(
            r'SQL.*concat|string.*concat|SQL.*interpolat|user.*input.*SQL|SQL.*拼接'
            r'|userId\b.*\+|\+.*userId\b', t, re.I) is not None),
        _LOGIC_SCORE_BELOW_100_RULE,
        ("identifies countReports closes connection before reading ResultSet", lambda t: re.search(
            r'ResultSet.*after.*close|close.*before.*read|conn\.close.*rs\.|rs.*after.*conn'
            r'|关闭.*之后.*读|countReports.*close|close.*countReports', t, re.I) is not None),
    ],
    226: [
        ("has Module Breakdown or per-function analysis", lambda t: re.search(
            r'Module Breakdown|模块分解|函数分析|方法分析|fetchUserData|processPayment|loadUserAndPay',
            t, re.I) is not None),
        _LOGIC_SCORE_BELOW_100_RULE,
        ("identifies at least 3 distinct issues across the 3 functions", lambda t: (
            re.search(r'res\.ok|response\.ok|HTTP.*错误|HTTP error|res\.status', t, re.I) is not None and
            re.search(r'catch.*(?:swallow|吞|console\.log|log.*only|不重抛|不.*rethrow)|processPayment.*catch',
                      t, re.I) is not None and
            re.search(r'\.catch\(\)|unhandled.*reject|Promise.*no.*catch|no.*catch.*Promise|缺少.*catch',
                      t, re.I) is not None
        )),
    ],
    227: [
        _FIX_LOG_RULE,
        ("has before and after scores", lambda t: (
            re.search(r'before[:\s]+[0-9]+|Logic Score \(before\)|改前|修复前', t, re.I) is not None and
            re.search(r'after[:\s]+[0-9]+|Logic Score \(after\)|改后|修复后', t, re.I) is not None)),
        ("fixes resource leak with try-with-resources or explicit close", lambda t: re.search(
            r'try[- ]with[- ]resources|try\s*\(.*(?:stmt|conn|rs)|finally.*close'
            r'|stmt\.close|rs\.close|资源.*关闭|关闭.*资源', t, re.I) is not None),
        ("fixes SQL concatenation with PreparedStatement", lambda t: re.search(
            r'PreparedStatement|prepareStatement|setInt|setString|parameterized|参数化.*查询|预编译',
            t, re.I) is not None),
        ("score improved after fixes", _case227_score_improved),
    ],

    # ── v0.6.4: additional language coverage cases ───────────────────────────
    228: [
        ("identifies L1", lambda t: "L1" in t),
        ("identifies Ruby constant lookup shadowing stdlib Logger", lambda t: re.search(
            r'constant.*lookup|Payment::Logger|::Logger|stdlib.*Logger|Logger.*shadow', t, re.I) is not None),
        ("identifies missing info method / NoMethodError", lambda t: re.search(
            r'NoMethodError|undefined method.*info|\.info.*(?:missing|not.*defined)', t, re.I) is not None),
        ("recommends qualified top-level Logger or rename", lambda t: re.search(
            r'::Logger|top[- ]level.*Logger|rename.*Logger|qualif.*Logger', t, re.I) is not None),
    ],
    229: [
        ("identifies L7", lambda t: "L7" in t),
        ("identifies non-atomic read-modify-write", lambda t: re.search(
            r'non.?atomic|read.?modify.?write|lost update|activeRequests\+\+|activeRequests--', t, re.I) is not None),
        ("connects Dispatchers.Default to real concurrency", lambda t: re.search(
            r'Dispatchers\.Default|thread pool|multiple coroutines|并发|coroutines.*concurrent', t, re.I) is not None),
        ("recommends AtomicInteger or Mutex", lambda t: re.search(
            r'AtomicInteger|incrementAndGet|decrementAndGet|Mutex', t, re.I) is not None),
    ],
    230: [
        ("identifies L8", lambda t: "L8" in t),
        ("identifies exception path skips fclose", lambda t: re.search(
            r'fclose|InvalidArgumentException|throw.*(?:skip|before|without).*close|exception.*(?:skip|bypass|without).*fclose',
            t, re.I | re.S) is not None),
        ("connects leak to file descriptor exhaustion", lambda t: re.search(
            r'file descriptor|fd|OS limit|too many open files|descriptor.*exhaust|句柄', t, re.I) is not None),
        ("recommends try/finally or managed file object", lambda t: re.search(
            r'try.*finally|finally.*fclose|SplFileObject|generator.*lifecycle', t, re.I | re.S) is not None),
    ],
    231: [
        ("identifies L3", lambda t: "L3" in t),
        ("identifies size_t unsigned underflow", lambda t: re.search(
            r'size_t|unsigned.*underflow|underflow.*unsigned|wrap.*(?:SIZE_MAX|max)', t, re.I) is not None),
        ("identifies i >= 0 is always true for unsigned", lambda t: re.search(
            r'i\s*>=\s*0|always true|unsigned.*(?:cannot|never).*negative', t, re.I) is not None),
        ("recommends signed index or reverse iterator", lambda t: re.search(
            r'signed.*index|int\s+i|reverse iterator|rbegin|rend|std::find_if', t, re.I) is not None),
    ],
    232: [
        ("identifies L1", lambda t: "L1" in t),
        ("identifies constructor-scoped TAX_RATE not visible to method", lambda t: re.search(
            r'constructor.*TAX_RATE|TAX_RATE.*constructor|block.?scoped|method.*module.*TAX_RATE|lexical', t, re.I) is not None),
        ("identifies tax-exempt invoice still returns 108 / uses 0.08", lambda t: re.search(
            r'108|0\.08|taxExempt.*(?:still|not).*tax|module.?level.*TAX_RATE', t, re.I | re.S) is not None),
        ("recommends instance field", lambda t: re.search(
            r'this\.taxRate|instance field|instance property|store.*rate.*this', t, re.I) is not None),
    ],
    233: [
        ("identifies L1", lambda t: "L1" in t),
        ("identifies import alias shadows builtin len", lambda t: re.search(
            r'import alias|alias.*len|shadow.*built.?in.*len|builtin.*len.*shadow|universe block', t, re.I) is not None),
        ("identifies len resolves to package not function", lambda t: re.search(
            r'len\(words\)|resolves.*package|package.*not.*function|cannot call.*package|len.*constraints', t, re.I) is not None),
        ("recommends non-conflicting alias", lambda t: re.search(
            r'constraints\s+"github|non.?conflicting alias|rename.*alias|avoid.*len', t, re.I) is not None),
    ],
    234: [
        ("identifies L9", lambda t: "L9" in t),
        ("identifies TIMESTAMP without time zone", lambda t: re.search(
            r'TIMESTAMP(?:\s+WITHOUT\s+TIME\s+ZONE)?|without time zone|no timezone|no time zone', t, re.I) is not None),
        ("identifies session timezone dependency", lambda t: re.search(
            r'session.*TimeZone|TimeZone.*session|America/New_York|Europe/London|implicit.*cast', t, re.I) is not None),
        ("recommends TIMESTAMPTZ / with time zone", lambda t: re.search(
            r'TIMESTAMPTZ|TIMESTAMP WITH TIME ZONE|with time zone|UTC', t, re.I) is not None),
    ],
    235: [
        ("identifies L9", lambda t: "L9" in t),
        ("identifies strptime locale-dependent directives", lambda t: re.search(
            r'strptime|%A|%B|locale.*(?:dependent|sensitive)|process locale', t, re.I) is not None),
        ("identifies French locale failure", lambda t: re.search(
            r'fr_FR|French|France|lundi|mars|ValueError|Monday.*March', t, re.I) is not None),
        ("recommends fixed locale or numeric date parsing", lambda t: re.search(
            r'setlocale|fixed locale|C locale|en_US|numeric.*(?:date|month)|%m', t, re.I) is not None),
    ],
    236: [
        ("identifies L5", lambda t: "L5" in t),
        ("identifies || true suppresses migration failure", lambda t: re.search(
            r'\|\|\s*true|or true|suppress.*failure|exit code.*0|migrate.*(?:fail|failure)', t, re.I | re.S) is not None),
        ("identifies service restarts after failed migration", lambda t: re.search(
            r'systemctl restart|restart.*(?:failed|migration)|failed.*migration.*restart', t, re.I | re.S) is not None),
        ("identifies false success notification", lambda t: re.search(
            r'Slack|Deploy successful|false.*success|success.*(?:despite|even though).*fail', t, re.I | re.S) is not None),
        ("recommends explicit exit-code handling", lambda t: re.search(
            r'MIGRATE_EXIT|\$\?|exit code|if.*migrate|error.*branch|do not.*\|\|\s*true', t, re.I | re.S) is not None),
    ],
    237: [
        ("explains MutexGuard RAII", lambda t: re.search(
            r'MutexGuard|RAII|guard.*(?:holds|lock)|lock\(\).*guard', t, re.I) is not None),
        ("identifies guard drop points", lambda t: re.search(
            r'Drop|goes out of scope|drop.*(?:D|G)|end of.*(?:closure|block)', t, re.I) is not None),
        ("explains mutual exclusion", lambda t: re.search(
            r'mutual exclusion|exclusive|one.*(?:thread|block).*at a time|wait.*lock', t, re.I) is not None),
        ("states final value is 11", lambda t: re.search(r'\b11\b', t) is not None),
    ],
    238: [
        ("explains Elvis null path", lambda t: re.search(
            r'Elvis|\?:|no-email|null.*return', t, re.I) is not None),
        ("explains smart cast to non-null String", lambda t: re.search(
            r'smart.?cast|non.?null(?:able)?|String', t, re.I) is not None),
        ("identifies three outputs", lambda t: re.search(
            r'example\.com', t, re.I) is not None and re.search(r'no-email', t, re.I) is not None and re.search(r'malformed', t, re.I) is not None),
        ("explains missing @ malformed path", lambda t: re.search(
            r'indexOf\([^)]*@|atIndex.*-1|no @|malformed', t, re.I | re.S) is not None),
    ],
    239: [
        ("explains default evaluated once", lambda t: re.search(
            r'default.*(?:once|definition time)|definition time|evaluated once|函数定义', t, re.I) is not None),
        ("explains append mutates in place", lambda t: re.search(
            r'append|mutat.*in.?place|in.?place.*mutat|原地', t, re.I) is not None),
        ("identifies result1/result2 share same object", lambda t: re.search(
            r'result1.*result2.*same|same.*(?:list|object).*result1.*result2|shared default|共享', t, re.I | re.S) is not None),
        ("identifies result3 independent explicit list", lambda t: re.search(
            r'result3|explicit list|fastapi|starlette|independent|not.*default', t, re.I | re.S) is not None),
    ],
    240: [
        _BOTH_VERSIONS_RULE,
        _DIVERGENT_RULE,
        ("identifies find raises while find_by returns nil", lambda t: re.search(
            r'find_by.*nil|find.*RecordNotFound|RecordNotFound.*find|find.*raises', t, re.I | re.S) is not None),
        ("identifies nil email divergence", lambda t: re.search(
            r'nil.*email|email.*nil|NoMethodError|safe navigation|&\.', t, re.I) is not None),
        ("identifies no-@ behavior is same", lambda t: re.search(
            r'no.*@|without.*@|one.?element|full email|same.*(?:case|behavior)', t, re.I | re.S) is not None),
    ],
    241: [
        _BOTH_VERSIONS_RULE,
        ("gives Semantically Equivalent verdict", _equivalent_verdict),
        ("explains isset and ?? treat null/missing the same", lambda t: re.search(
            r'isset|null coalesc|missing.*(?:null|default)|null.*missing|\?\?', t, re.I) is not None),
        ("explains false/0/empty string are preserved", lambda t: re.search(
            r'false|0|empty string|\'\'|falsy|not.*empty\(\)', t, re.I) is not None),
        ("notes PHP 7+ requirement", lambda t: re.search(r'PHP\s*7|7\+', t, re.I) is not None),
    ],
    242: [
        _BOTH_VERSIONS_RULE,
        _DIVERGENT_RULE,
        ("identifies TypeError for aware issued_at in Version A", lambda t: re.search(
            r'TypeError|offset-naive|offset-aware|naive.*aware|aware.*naive', t, re.I) is not None),
        ("explains Version B assumes UTC for naive issued_at", lambda t: re.search(
            r'replace\(tzinfo=timezone\.utc\)|assum.*UTC|treat.*naive.*UTC|naive.*UTC', t, re.I) is not None),
        ("identifies L9 or timezone hazard", lambda t: "L9" in t or re.search(r'timezone|tzinfo|UTC', t, re.I) is not None),
    ],
    243: [
        ("has Module Breakdown", lambda t: re.search(r'Module Breakdown|模块分布|per.?method|method analysis', t, re.I) is not None),
        _LOGIC_SCORE_BELOW_100_RULE,
        ("identifies nil items risk", lambda t: re.search(
            r'order\[:items\].*(?:nil|NoMethodError)|nil.*order\[:items\]|items.*nil', t, re.I | re.S) is not None),
        ("identifies nil discount risk", lambda t: re.search(
            r'DISCOUNTS\[code\].*nil|discount.*nil|subtract.*nil|-=.*nil|unknown.*code', t, re.I | re.S) is not None),
        ("identifies mutation during iteration", lambda t: re.search(
            r'orders\.delete|mutat.*(?:during|while).*iter|delete.*each|skip.*element', t, re.I) is not None),
    ],
    244: [
        ("has Module Breakdown", lambda t: re.search(r'Module Breakdown|模块分布|per.?method|method analysis', t, re.I) is not None),
        _LOGIC_SCORE_BELOW_100_RULE,
        ("identifies missing rollback on execute false", lambda t: re.search(
            r'rollBack|rollback|execute\(\).*false|false.*(?:without|no).*rollback|transaction.*left', t, re.I | re.S) is not None),
        ("identifies tmpfile resource leak", lambda t: re.search(
            r'tmpfile|fclose|resource.*leak|handle.*leak|temporary file', t, re.I) is not None),
    ],
    245: [
        _FAULT_CONFIDENCE_RULE,
        ("locates force unwrap line/path", lambda t: re.search(
            r'line\s+1[12]|path!|force.?unwrap|unexpectedly found nil', t, re.I) is not None),
        ("identifies path returns nil when resource missing", lambda t: re.search(
            r'path\(forResource|returns?\s+nil|resource.*missing|not in.*bundle', t, re.I | re.S) is not None),
        ("identifies debug/release bundle discrepancy", lambda t: re.search(
            r'Debug|Release|build phase|bundle.*(?:missing|present)', t, re.I) is not None),
        ("identifies L6 contract mismatch", lambda t: "L6" in t or re.search(r'callee.*contract|contract.*mismatch', t, re.I) is not None),
        ("recommends guard let", lambda t: re.search(r'guard\s+let|if\s+let|optional.*handling', t, re.I) is not None),
    ],
    246: [
        _FAULT_CONFIDENCE_RULE,
        ("locates || true on pytest pipeline", lambda t: re.search(
            r'pytest.*\|\s*tee.*\|\|\s*true|\|\|\s*true.*pytest|pipeline.*\|\|\s*true', t, re.I | re.S) is not None),
        ("explains || true resets exit code", lambda t: re.search(
            r'exit code.*0|resets?.*exit|converts?.*0|always succeeds|masks?.*failure', t, re.I) is not None),
        ("identifies L5", lambda t: "L5" in t),
        ("recommends PIPESTATUS or trap cleanup", lambda t: re.search(
            r'PIPESTATUS|trap|cleanup|preserve.*exit|capture.*exit', t, re.I) is not None),
    ],
    247: [
        _FIX_LOG_RULE,
        _BEFORE_AFTER_SCORE_RULE,
        ("fixes L1 logger shadow", lambda t: re.search(
            r'::Logger|ReportLogger|rename.*Logger|stdlib.*Logger', t, re.I) is not None),
        ("fixes L8 file leak", lambda t: re.search(
            r'File\.open.*do|ensure.*close|file\.close|auto.?close|block form', t, re.I | re.S) is not None),
        ("score improved after fixes", _score_improved),
    ],
    248: [
        _FIX_LOG_RULE,
        _BEFORE_AFTER_SCORE_RULE,
        ("fixes L7 atomic increment", lambda t: re.search(
            r'AtomicInteger|incrementAndGet|Mutex|atomic.*increment', t, re.I) is not None),
        ("fixes L8 reader leak", lambda t: re.search(
            r'\.use\s*\{|use\s*\{|BufferedReader.*use|close\(\)|try.*finally', t, re.I | re.S) is not None),
        ("score improved after fixes", _score_improved),
    ],
    # ── No-bug review cases (false-positive suppression tests) ──────────────
    249: [
        ("concludes no logic error (None sentinel correct)", _no_bug_conclusion),
        ("explains None sentinel creates fresh list each call", lambda t: re.search(
            r'None.*sentinel|sentinel.*None|if.*None.*=.*\[\]|cache\s*=\s*\[\]'
            r'|fresh.*list|新.*列表|每次.*调用.*新', t, re.I) is not None),
        # only fails on confirmed/definitive bug claim, not mere mention of pattern name
        ("does not falsely flag mutable default as confirmed bug", lambda t: not re.search(
            r'(?:this\s+(?:is|creates?|has)|confirmed|缺陷|存在).*mutable.*default.*bug'
            r'|L4.*(?:confirmed|found|this\s+is\s+a\s+bug|这是.*bug)'
            r'|mutable.*default.*(?:issue|bug).*(?:exists?|found|confirmed)', t, re.I)),
    ],
    250: [
        ("concludes no lock leak or resource hazard", _no_bug_conclusion),
        ("explains defer releases lock on all exit paths", lambda t: re.search(
            r'defer.*(?:all|every).*(?:path|exit|return)|defer.*(?:run|execute).*return'
            r'|所有.*路径.*释放|defer.*解锁', t, re.I) is not None),
        # only fails on confirmed lock leak claim, not mere mention of the concept
        ("does not falsely flag L8 lock leak as confirmed", lambda t: not re.search(
            r'(?:mutex|lock)\s+(?:is\s+)?(?:leaked|not\s+released|未释放)'
            r'|L8.*(?:confirmed|this\s+code.*leak|lock.*bug)'
            r'|(?:lock|mutex).*leak.*(?:here|this|found|confirmed)', t, re.I)),
    ],
    251: [
        ("concludes no closure bug with let", _no_bug_conclusion),
        ("explains let creates per-iteration binding", lambda t: re.search(
            r'\blet\b.*(?:block[- ]scoped|per[- ]iter|new.*binding|块级|每次.*迭代)'
            r'|(?:block[- ]scoped|per[- ]iter).*\blet\b', t, re.I) is not None),
        ("contrasts with var (concern applies to var not let)", lambda t: re.search(
            r'\bvar\b.*(?:function[- ]scoped|hoist|shar(?:e|ed|es)|共享)'
            r'|concern.*\bvar\b|applies.*\bvar\b|with\s+var.*all.*clos', t, re.I) is not None),
    ],
    252: [
        ("concludes no resource leak (with closes file)", _no_bug_conclusion),
        ("explains with-statement __exit__ runs before return", lambda t: re.search(
            r'__exit__|with.*(?:close|cleanup|释放).*return|return.*(?:after|before).*close'
            r'|with.*(?:语句|块).*(?:关闭|close)|context.*manager.*close', t, re.I) is not None),
        # only fails on confirmed leak claim, not mere mention of "file leak" concept
        ("does not falsely flag L8 file leak as confirmed", lambda t: not re.search(
            r'file\s+(?:handle\s+)?(?:is\s+)?(?:leaked|not\s+closed|未关闭)'
            r'|L8.*(?:confirmed|file.*leak.*this|this.*is.*L8)'
            r'|handle.*(?:is\s+)?leaked.*(?:here|this|found)', t, re.I)),
    ],
    253: [
        ("concludes no SQL injection vulnerability", lambda t: re.search(
            r'no\s+(?:sql\s+)?injection|injection.*(?:prevent|safe|correct|parameteriz)'
            r'|parameteriz.*(?:safe|correct|prevent)|没有.*注入|注入.*安全', t, re.I) is not None),
        ("explains %s placeholders with tuple is parameterized", lambda t: re.search(
            r'%s.*(?:parameteriz|placeholder|tuple)|parameteriz.*%s'
            r'|(?:separate|独立).*(?:tuple|元组).*(?:safe|安全)', t, re.I) is not None),
        # only fails on confirmed injection claim, not mere mention of injection concept
        ("does not falsely flag injection as confirmed vulnerability", lambda t: not re.search(
            r'(?:this\s+(?:code\s+)?is\s+vulnerable|confirmed.*injection|injection.*confirmed)'
            r'|sql.*injection.*(?:found\s+here|exists?\s+in\s+this|present\s+in\s+this)', t, re.I)),
    ],
    # ── Clean health cases (score calibration tests) ─────────────────────────
    254: [
        ("Logic Score 80 or above", _score_above_80),
        ("no L8 resource leak finding", lambda t: not re.search(
            r'L8.*(?:confirmed|found|identified)|resource.*leak.*(?:confirmed|bug)', t, re.I)),
        ("acknowledges parameterized queries are safe", lambda t: re.search(
            r'parameteriz|placeholder.*\$1|\$1.*safe|防注入|没有.*注入', t, re.I) is not None),
    ],
    255: [
        ("Logic Score 80 or above", _score_above_80),
        ("acknowledges try-with-resources correct", lambda t: re.search(
            r'try[- ]with[- ]resources|AutoCloseable|correctly.*close|close.*correctly'
            r'|正确.*关闭|关闭.*正确', t, re.I) is not None),
        ("no high-severity confirmed bug", lambda t: not re.search(
            r'(?:L7|L8).*(?:confirmed|definite|found|bug)|confirmed.*(?:L7|L8)', t, re.I)),
    ],
    256: [
        ("Logic Score 80 or above", _score_above_80),
        ("acknowledges asynccontextmanager correct", lambda t: re.search(
            r'asynccontextmanager|async.*with.*(?:correct|release|return)'
            r'|连接.*正确.*归还|归还.*连接', t, re.I) is not None),
        ("no confirmed L7 or L8 bug", lambda t: not re.search(
            r'(?:L7|L8).*(?:confirmed|definite|bug|found)', t, re.I)),
    ],
    # ── Equivalent diff cases (balance ratio) ────────────────────────────────
    257: [
        _BOTH_VERSIONS_RULE,
        ("gives Semantically Equivalent verdict", _equivalent_verdict),
        ("explains filter condition matches comprehension if-clause", lambda t: re.search(
            r'filter.*x\s*>\s*0|x\s*>\s*0.*filter|same.*condition|条件.*相同|相同.*条件', t, re.I) is not None),
    ],
    258: [
        _BOTH_VERSIONS_RULE,
        ("gives Semantically Equivalent verdict", _equivalent_verdict),
        ("identifies map and collect as aliases", lambda t: re.search(
            r'(?:map|collect).*(?:alias|同名|别名|identical|same method)'
            r'|alias.*(?:map|collect)|别名|完全相同', t, re.I) is not None),
    ],
    259: [
        _BOTH_VERSIONS_RULE,
        ("gives Semantically Equivalent verdict", _equivalent_verdict),
        ("explains list comprehension vs generator expression difference", lambda t: re.search(
            r'(?:list.*comprehension|generator.*expression|列表.*推导|生成器.*表达式)'
            r'.*(?:differ|vs|versus|而|但)|generator.*no.*intermediate|中间.*列表', t, re.I) is not None),
    ],
    260: [
        _BOTH_VERSIONS_RULE,
        ("gives Semantically Equivalent verdict", _equivalent_verdict),
        ("explains len(s)==0 and s=='' are equivalent in Go", lambda t: re.search(
            r'len.*==.*0.*(?:equivalent|same|identical)|(?:equivalent|same|identical).*len.*==.*0'
            r'|两者.*等价|等价.*empty|empty.*string.*check.*(?:equivalent|same)', t, re.I) is not None),
    ],

    # ── v0.6.4: enrichment cases (261–275) ──────────────────────────────────────
    261: [
        _FIX_LOG_RULE,
        ("has before/after Logic Score", lambda t: re.search(r'Logic Score\s*\(before\)|Logic Score\s*\(after\)|逻辑评分.*前|逻辑评分.*后', t) is not None),
        ("fixes .unwrap panic on Option", lambda t: re.search(r'unwrap[^a-z].*panic|unwrap_or_default|cloned\(\).*unwrap_or|panic.*unwrap|None.*unwrap', t, re.I) is not None),
    ],
    262: [
        _FIX_LOG_RULE,
        ("has before/after Logic Score", lambda t: re.search(r'Logic Score\s*\(before\)|Logic Score\s*\(after\)', t) is not None),
        ("identifies HashMap concurrency hazard", lambda t: re.search(r'ConcurrentHashMap|computeIfAbsent|HashMap.*not.*thread.?safe|thread.?safe.*HashMap|synchronized', t, re.I) is not None),
        ("fixes FileWriter resource leak", lambda t: re.search(r'try-with-resources|try\s*\(\s*FileWriter|FileWriter.*try|leak.*FileWriter', t, re.I) is not None),
    ],
    263: [
        _FIX_LOG_RULE,
        ("has before/after Logic Score", lambda t: re.search(r'Logic Score\s*\(before\)|Logic Score\s*\(after\)', t) is not None),
        ("identifies naive vs aware datetime", lambda t: re.search(r'naive.*aware|aware.*naive|timezone\.utc|tzinfo|UTC|时区', t, re.I) is not None),
        ("flags float currency math", lambda t: re.search(r'Decimal|float.*currency|currency.*float|integer.*cents|divmod', t, re.I) is not None),
    ],
    264: [
        _FIX_LOG_RULE,
        ("has before/after Logic Score", lambda t: re.search(r'Logic Score\s*\(before\)|Logic Score\s*\(after\)', t) is not None),
        ("identifies inflight not cleared", lambda t: re.search(r'inflight.*(?:never\s*cleared|never\s*deleted|leak|finally|clear)|delete\s+inflight|finally.*delete', t, re.I) is not None),
    ],
    265: [
        _FIX_LOG_RULE,
        ("has before/after Logic Score", lambda t: re.search(r'Logic Score\s*\(before\)|Logic Score\s*\(after\)', t) is not None),
        ("fixes SQL string interpolation", lambda t: re.search(r'prepare|prepared statement|parameterized|参数化|预编译|bind.*param|execute\(\[', t, re.I) is not None),
        ("identifies fetch returns false on no-match", lambda t: re.search(r'fetch.*(?:false|===\s*false|no.?match|empty)|false.*fetch|\$row\s*===\s*false', t, re.I) is not None),
    ],
    266: [
        _FIX_LOG_RULE,
        ("has before/after Logic Score", lambda t: re.search(r'Logic Score\s*\(before\)|Logic Score\s*\(after\)', t) is not None),
        ("fixes SqlConnection leak", lambda t: re.search(r'SqlConnection.*(?:using|dispose|leak)|using\s*\(.*SqlConnection|Dispose.*SqlConnection', t, re.I) is not None),
        ("identifies List aliasing mutation", lambda t: re.search(r'(?:result\s*=\s*ids|alias).*mutat|mutat.*(?:result|input|caller)|defensive\s*copy|new\s+List<int>\(ids', t, re.I) is not None),
    ],
    267: [
        ("explains lifetime parameter \'a", lambda t: re.search(r"lifetime|'a|borrow.*checker|borrowed.*from.*slice", t, re.I) is not None),
        ("traces iterator yields &T references", lambda t: re.search(r'&T|&i32|reference.*into.*slice|slice::Iter|IntoIterator|each\s+item.*reference', t, re.I) is not None),
    ],
    268: [
        # 1 4 3 2 may be on one line ("Output: 1, 4, 3, 2") or spread across step-by-step lines —
        # re.S lets `.` cross newlines, so the existence of 1, then 4, then 3, then 2 (in order) suffices.
        ("states the order 1 4 3 2", lambda t: re.search(r'1.*4.*3.*2', t, re.S) is not None),
        ("explains microtask drains before macrotask", lambda t: re.search(r'microtask.*(?:before|drain|prior).*macrotask|macrotask.*after.*microtask|microtask.*queue|微任务.*宏任务', t, re.I) is not None),
    ],
    269: [
        ("explains decorator bottom-up application", lambda t: re.search(r'(?:bottom.?up|自下而上|由下向上).*(?:apply|application|装饰|应用)|装饰器.*应用.*顺序|italic.*(?:before|先).*bold', t, re.I) is not None),
        ("final output is <b><i>hello</i></b>", lambda t: re.search(r'<b><i>hello</i></b>|<b>\s*<i>\s*hello\s*</i>\s*</b>', t) is not None),
    ],
    270: [
        _FAULT_CONFIDENCE_RULE,
        ("identifies remove-during-foreach as cause", lambda t: re.search(r'(?:orders\.remove|remove).*(?:for.?each|enhanced.?for|iterator|iter)|ConcurrentModificationException.*remove|modCount|checkForComodification', t, re.I) is not None),
        ("recommends Iterator.remove or removeIf", lambda t: re.search(r'Iterator\.remove|removeIf|removeAll|it\.remove\(\)|collect.*to.*separate.*list', t, re.I) is not None),
    ],
    271: [
        _FAULT_CONFIDENCE_RULE,
        ("identifies nil-pointer-in-interface trap", lambda t: re.search(r'nil.*interface|interface.*nil|nil.*pointer.*wrap|typed.*nil|\(type=.*value=nil\)|non.?nil.*interface.*nil.*pointer', t, re.I) is not None),
        ("recommends var err error or explicit nil", lambda t: re.search(r'var\s+err\s+error|return\s+nil|explicit.*nil|declare.*err.*error', t, re.I) is not None),
    ],
    272: [
        _FAULT_CONFIDENCE_RULE,
        ("identifies implicit resolution as cause", lambda t: re.search(r'implicit.*(?:resolution|search|conversion)|(?:wrong|different).*implicit|implicit.*select|stringToInt.*not.*(?:called|selected|invoked)', t, re.I) is not None),
        ("recommends explicit conversion or -Xlog-implicits", lambda t: re.search(r'total\(input\)\(stringToInt\)|explicit.*conversion|pass.*explicit|Xlog-implicits|Xprint:typer', t, re.I) is not None),
    ],
    273: [
        ("has Module Breakdown", lambda t: re.search(r'Module Breakdown|模块分布|per.module|per-module', t, re.I) is not None),
        ("identifies systemic null-deref pattern", lambda t: re.search(r'(?:systemic|3.*module|all.*three.*module|系统性|跨.?模块).*(?:null|None|L6|callee.*contract|deref)|null.?deref.*(?:across|systemic|systemic|3.*module)', t, re.I) is not None),
    ],
    274: [
        ("has Module Breakdown", lambda t: re.search(r'Module Breakdown|模块分布', t, re.I) is not None),
        ("identifies map data race", lambda t: re.search(r'map.*(?:not.*thread.?safe|race|data.?race|concurrent)|sync\.Map|sync\.Mutex|unsynchronized.*map', t, re.I) is not None),
        ("identifies error-discard pattern", lambda t: re.search(r'(?:_,?\s*err|ignore.*error|discard.*error|error.*ignored|忽略.*error|错误.*忽略).*(?:both|systemic|across|systemic|两个|系统性)', t, re.I) is not None),
    ],
    275: [
        ("has Logic Score", lambda t: re.search(r'Logic Score|逻辑评分', t) is not None),
        ("identifies Agent.get on GenServer process", lambda t: re.search(r'Agent\.get.*GenServer|GenServer.*Agent|wrong.*process.*API|Agent.*not.*GenServer', t, re.I) is not None),
        ("identifies O(n) list append performance", lambda t: re.search(r'O\(n\).*append|append.*O\(n\)|prepend.*reverse|\+\+\s*\[.*\]|inefficient.*list.*append', t, re.I) is not None),
    ],

    # ── v0.6.4: research-anchored cases (276–285) ──────────────────────────────
    276: [
        ("has Logic Score", lambda t: re.search(r'Logic Score|逻辑评分', t) is not None),
        ("identifies missing volatile / JMM hazard", lambda t: re.search(r'volatile|JMM|memory model|reorder|publication', t, re.I) is not None),
        ("identifies loadFromDisk after publish race", lambda t: re.search(r'loadFromDisk.*(?:after|race|outside|partially).*(?:published|init|construct|assign)|partially.?initialized|holder.*idiom|holder.*class', t, re.I) is not None),
    ],
    277: [
        ("has Logic Score", lambda t: re.search(r'Logic Score|逻辑评分', t) is not None),
        ("identifies if-vs-while spurious wakeup", lambda t: re.search(r'spurious.*wakeup|while\s*\(\s*!\s*ready|while.*loop.*wait|wakeup.*while', t, re.I) is not None),
        ("addresses notify vs notifyAll or BlockingQueue", lambda t: re.search(r'notifyAll|notify\s+vs\s+notifyAll|BlockingQueue|higher.?level.*primitive', t, re.I) is not None),
    ],
    278: [
        _FAULT_CONFIDENCE_RULE,
        ("identifies missing extend of b[j:]", lambda t: re.search(r'b\[j:\]|extend.*b|missing.*extend|drop.*b|b.*remaining|right.*remaining|未.*flush.*b', t, re.I) is not None),
        ("recommends extend b[j:] fix", lambda t: re.search(r'result\.extend\(b\[j:\]\)|extend\(b\[j:\]\)|add.*extend.*b', t, re.I) is not None),
    ],
    279: [
        ("has Logic Score", lambda t: re.search(r'Logic Score|逻辑评分', t) is not None),
        ("identifies in-place mutation + return ambiguity", lambda t: re.search(r'(?:in.?place|mutat).*(?:return|ambig|both|contract)|return.*(?:also|and).*mutat|aliased.*mutation', t, re.I) is not None),
    ],
    280: [
        ("has Logic Score", lambda t: re.search(r'Logic Score|逻辑评分', t) is not None),
        ("identifies cross-thread flag race", lambda t: re.search(r'(?:cross.?thread|两个.?线程|跨.?线程).*(?:flag|race|状态)|race.*(?:flag|electron_mode|beam_filter)|flag.*(?:race|sync|atomic)', t, re.I) is not None),
        ("recommends atomic state / state machine", lambda t: re.search(r'(?:atomic|state.?machine|enum|single.*state).*(?:state|enum|machine|atomic)|状态机|enum.*ELECTRON|mutex.*enum', t, re.I) is not None),
    ],
    281: [
        _FAULT_CONFIDENCE_RULE,
        ("identifies narrowing cast hazard", lambda t: re.search(r'narrow|narrow.*cast|silent.*truncat|truncat.*high|short.*cast|cast.*short|超出.*范围|溢出', t, re.I) is not None),
        ("recommends bounds check or wider type", lambda t: re.search(r'bounds.*check|(?:check|validate).*(?:Short\.MAX|range)|wider.*type|return.*int|int.*instead.*short', t, re.I) is not None),
    ],
    282: [
        _FAULT_CONFIDENCE_RULE,
        ("identifies DST gap/overlap", lambda t: re.search(r'(?:DST|spring.?forward|fall.?back|gap|overlap).*(?:DST|spring.?forward|fall.?back|gap|overlap|skip|double|时区|夏令)|02:30.*(?:not.*exist|gap|skip)|不存在.*02:30', t, re.I) is not None),
        ("recommends getValidOffsets or UTC anchoring", lambda t: re.search(r'getValidOffsets|ZoneRules|UTC.*anchor|anchor.*UTC|UTC.*timestamp', t, re.I) is not None),
    ],
    283: [
        _FAULT_CONFIDENCE_RULE,
        ("identifies relative Location header", lambda t: re.search(r'(?:relative|absolute).*Location|Location.*(?:relative|absolute)|RFC\s*7231|/page.*relative|relative.*URL', t, re.I) is not None),
        ("recommends urljoin", lambda t: re.search(r'urljoin|urllib\.parse\.urljoin|resolve.*relative|join.*url.*location', t, re.I) is not None),
    ],
    284: [
        ("Logic Score is 100 or near-perfect (no fabricated bugs)", lambda t: re.search(r'Logic Score[^0-9]{0,15}(?:100|9[5-9])/100|逻辑评分[^0-9]{0,15}(?:100|9[5-9])/100|no.*confirmed.*bug|no.*logic.*bug.*found|未发现.*逻辑|未发现已确认', t, re.I) is not None),
        # A real Critical finding has 🔴 followed by a four-field block with an L-code title (e.g., `🔴 Critical\n**[L6] — title**\nPremises:`).
        # Bare 🔴 in a legend / "no Critical findings here" sentence is allowed.
        ("does not invent Critical findings", lambda t: re.search(r'🔴[^\n]{0,30}\n\s*\*\*\s*\[?\s*L[1-9]\b', t) is None),
        ("explains LRU correctness or affirms cleanness", lambda t: re.search(r'(?:LRU|insertion.?order|move.?to.?end|pop.*reinsert).*(?:correct|valid|proper)|implementation.*(?:correct|sound|clean)|实现.*(?:正确|无误)', t, re.I) is not None),
    ],
    285: [
        _FIX_LOG_RULE,
        ("has before/after Logic Score", lambda t: re.search(r'Logic Score\s*\(before\)|Logic Score\s*\(after\)', t) is not None),
        ("fixes lo = mid infinite loop", lambda t: re.search(r'lo\s*=\s*mid\s*\+\s*1|infinite.*loop.*lo\s*=\s*mid|mid\s*\+\s*1', t) is not None),
        ("fixes (lo+hi)/2 overflow", lambda t: re.search(r'lo\s*\+\s*\(\s*hi\s*-\s*lo\s*\)\s*/\s*2|overflow.*\(lo\s*\+\s*hi\)|integer overflow|Bentley|Bloch', t, re.I) is not None),
    ],
}


# ── Generic grader ─────────────────────────────────────────────────────────────

def rules_for_case(case: dict) -> list[tuple[str, Callable[[str], bool]]]:
    name = case["name"]
    is_zh_case = name.startswith("zh-")

    rules: list[tuple[str, Callable[[str], bool]]] = []
    if is_zh_case:
        rules.append(("output is chinese (>=50 CJK chars, no English section headers)", is_chinese_output))
    if case["mode"] != "logic-explain":
        rules.append(_FOUR_FIELD_RULE)
    rules += _CASE_EXTRA_RULES.get(case["id"], [])
    return rules


def grade_case(case_id: int, output_path: Path) -> dict:
    case = EVALS_BY_ID.get(case_id)
    if not case:
        return {"eval_id": case_id, "error": "no such case in evals/content/v2/evals-v2.json"}
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

    rules = rules_for_case(case)

    expectations = check(text, rules)
    passed = sum(1 for e in expectations if e["passed"])
    pass_rate = passed / len(expectations) if expectations else 0.0

    return {
        "eval_id": case_id,
        "name": name,
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
    missing_case_ids = sorted(set(EVALS_BY_ID) - set(case_ids))

    results = []
    for cid in case_ids:
        # support both eval-<id> and eval-<id>-<name> directory names
        candidates = (list(iter_dir.glob(f"eval-{cid}/output.md")) +
                      list(iter_dir.glob(f"eval-{cid}-*/output.md")))
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
        "schema_version": 2,
        "iteration_dir": str(iter_dir.relative_to(REPO)),
        "cases_graded": len(results),
        "evals_total": len(EVALS_BY_ID),
        "graded_all_evals": len(missing_case_ids) == 0,
        "missing_eval_ids": missing_case_ids,
        "evals_source": str(EVALS_SOURCE.relative_to(REPO)),
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
