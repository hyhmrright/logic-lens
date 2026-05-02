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
from typing import Callable

REPO = Path(__file__).resolve().parent.parent
EVALS = json.load((REPO / "evals/v2/evals-v2.json").open())["evals"]
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
}


# ── Generic grader ─────────────────────────────────────────────────────────────

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

    rules: list[tuple[str, Callable[[str], bool]]] = []
    if is_zh_case:
        rules.append(("output is chinese (>=50 CJK chars, no English section headers)", is_chinese_output))
    if case["mode"] != "logic-explain":
        rules.append(_FOUR_FIELD_RULE)
    rules += _CASE_EXTRA_RULES.get(case_id, [])

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
