# How Logic-Lens Found Six Hidden Bugs in a Checkout Module That Passed Every Test

---

## The Setup: Green Lights, Quiet Confidence

You have a small checkout service. Eight Python files. Cart management, coupon pricing, inventory reservation, tax calculation, payment processing, order creation, notifications, and an orchestration layer that strings them together.

You ran the linter. Flake8 reports zero violations. Pylint gives you a 9.4 / 10. Black says the formatting is perfect. You have 38 unit tests. They all pass. Coverage is at 84%.

You ran `mypy`. It complains about a few missing type stubs for third-party libraries, but zero type errors in your own code.

So: what could go wrong?

As it turns out, quite a lot. Every one of those 38 tests was written by someone who understood the happy path. Every test calls functions with valid, in-range inputs from a populated cart. Every test was correct — and that is precisely the problem.

Logic-Lens found six bugs in this codebase. None of them were syntax errors. None of them were style violations. None of them would appear in a diff review without specific knowledge of what to look for. And all six are the category of bug that reaches production, lives there quietly for months, and then causes a customer-facing incident on a Tuesday afternoon when someone in Australia tries to check out.

This post walks through how Logic-Lens uses semi-formal execution tracing to surface these bugs — and why that approach finds things that static analysis and unit tests cannot.

---

## The Bugs: Four That Tell the Story

The full report covers all six risk classes (L1–L6). Here I will walk through four in enough detail to make the tracing methodology concrete.

### Bug 1 — The Name That Became the Wrong Thing (L1: Shadow Override)

`pricing.py` is responsible for coupon validation and formatting. Near the top of the file, there is a helper:

```python
def format(coupon: Coupon) -> str:
    """Return a human-readable coupon summary for receipts."""
    status = "USED" if coupon.used else "VALID"
    return f"{coupon.code} ({coupon.discount_pct:.1f}% off) [{status}]"
```

Forty lines later, a private helper tries to format a discount amount for the order confirmation email:

```python
def _format_discount_line(discount_amount: float) -> str:
    return "Discount: -" + format(discount_amount, "06d")
```

The author intended to call Python's builtin `format(value, spec)` — the two-argument form that produces zero-padded strings like `"001500"`. And that is exactly what they wrote. It looks correct. Every code reviewer who glances at this line sees a standard Python idiom.

Here is what Logic-Lens traces:

**Premises:** Python resolves identifiers by walking scopes outward — local, enclosing, module, then builtins. The builtin `format` accepts `(value, format_spec)`. The module-level `format` accepts `(coupon: Coupon)` — one positional argument.

**Trace:** `format` is called with two positional arguments: `(discount_amount, "06d")`. Python's scope chain finds `format` at module scope before it reaches builtins. The module-level `format` takes exactly one parameter. Python raises `TypeError: format() takes 1 positional argument but 2 were given`.

**Divergence:** The identifier `format` on the last line of `_format_discount_line` resolves to the module-level coupon formatter, not the builtin. Every confirmation email that includes a coupon discount line raises a `TypeError` before the email is dispatched.

What would a linter tell you? Nothing. The code is syntactically valid. The name `format` is perfectly legal as a function name. Pylint would not flag it because you are allowed to shadow a builtin. `mypy` would not flag it either — the call `format(discount_amount, "06d")` is type-consistent with a function accepting `(float, str)` if `mypy` does not trace the actual module-level definition, which it does not in this case because no `--strict` overload checking is configured.

The **remedy** is one of two options: rename the module-level function to `format_coupon`, or use `builtins.format(discount_amount, "06d")` explicitly. Either is a one-line fix. The bug was hiding in plain sight because the wrong name looked like the right call.

---

### Bug 2 — The None That Nobody Checked (L6: Callee Contract Mismatch)

`tax.py` contains a lookup function with a documented, explicit return type:

```python
def get_tax_rate(region_code: str) -> Optional[float]:
    """Return the applicable tax rate for a region, or None if unknown.

    Callers MUST check for None before using the return value.
    """
    return _TAX_RATES.get(region_code)
```

The comment is right there. The type hint is `Optional[float]`. The dictionary only contains six region codes: US-CA, US-NY, US-TX, GB, DE, and FR.

Twelve lines below, the same file contains:

```python
def calculate_tax(subtotal_cents: float, region_code: str) -> float:
    rate = get_tax_rate(region_code)
    return subtotal_cents * rate   # rate may be None
```

**Premises:** The caller assumes `get_tax_rate()` returns a `float`. The callee's contract is `Optional[float]`. Any region code not in `_TAX_RATES` produces `rate = None`.

**Trace:** A customer in Australia passes `region_code = "AU"`. `get_tax_rate("AU")` returns `None`. `subtotal_cents * None` raises `TypeError: unsupported operand type(s) for *: 'float' and 'NoneType'`. This exception propagates to the `run_checkout()` orchestrator, which catches it generically and returns a `CheckoutResult(success=False, error="unsupported operand type...")`. The customer sees "checkout failed" with no actionable message.

**Divergence:** Every customer outside the six hardcoded regions silently fails at the payment step. The exception message does not tell them why. The operator sees `TypeError` in the error log and has to trace it back to `tax.py`.

This is the L6 pattern in its clearest form: a callee that documents its contract honestly, and a caller that ignores it. Unit tests pass because they were written for US-CA and GB. The bug exists for every other country on Earth.

What would a linter tell you? Again, nothing. The return type annotation is correct. The call site is syntactically valid. `mypy` would flag this — `Optional[float]` cannot be multiplied by `float` without a guard — but only if you are running `mypy` with strict null checks, which many projects do not.

The **remedy** is a two-line guard:

```python
def calculate_tax(subtotal_cents: float, region_code: str) -> float:
    rate = get_tax_rate(region_code)
    if rate is None:
        return 0.0   # or raise ValueError for unknown regions
    return subtotal_cents * rate
```

---

### Bug 3 — The Connection That Was Never Closed (L5: Control Flow Escape)

`payment.py` processes card charges through a simulated gateway:

```python
def process_payment(amount: float, card_token: str) -> PaymentResult:
    conn = GatewayConnection(GATEWAY_ENDPOINT)
    conn.connect()

    response = conn.charge(amount, card_token)
    conn.close()   # only reached on happy path

    return PaymentResult(
        transaction_id=response["transaction_id"],
        amount_charged=amount,
        success=True,
    )
```

This looks like textbook sequential code. Connect, charge, close, return. Clean and readable.

`conn.charge()` raises `ValueError` for amounts over $10,000. That is an intentional gateway limit. The author knew about it — it is in the docstring. But when the exception is raised, execution jumps out of `process_payment()` entirely. `conn.close()` is unreachable.

**Premises:** `GatewayConnection` acquires a TCP connection in `connect()`. That connection must be released in `close()`. Every exit from the function — normal or exceptional — is a required post-condition.

**Trace:** `conn.connect()` sets `conn._open = True`. `conn.charge(1_200_000, token)` raises `ValueError`. Python unwinds the stack. `conn.close()` is never called. `conn._open` remains `True`. The underlying socket to the payment gateway is leaked. Each declined high-value transaction leaves one more open connection. Under enough load, the process exhausts its file descriptor limit.

**Divergence:** The required post-condition (connection closed) is not met on the exception exit path. The `close()` call is structurally tied to the success path only.

What would a linter tell you? Nothing. The code is valid. A linter does not model post-conditions. A unit test would only catch this if it explicitly checked that `conn.close()` was called in the failure case — most unit tests check the return value, not side effects on third-party objects.

The **remedy** is `try/finally`:

```python
conn = GatewayConnection(GATEWAY_ENDPOINT)
conn.connect()
try:
    response = conn.charge(amount, card_token)
finally:
    conn.close()
```

`finally` guarantees `conn.close()` runs regardless of whether `conn.charge()` raises. This is a standard Python pattern — and its absence here is the kind of thing you only notice if you are explicitly asking "does every exit from this function satisfy its post-conditions?"

---

### Bug 4 — The Race That Sold the Same Item Twice (L4: State Mutation Hazard)

`inventory.py` reserves stock before payment is attempted:

```python
def reserve_items(self, items: List[CartItem]) -> None:
    # Pass 1: validate
    for item in items:
        if self.available(item.sku) < item.quantity:
            raise InsufficientStockError(...)
    # Pass 2: commit
    for item in items:
        self._reserved[item.sku] = (
            self._reserved.get(item.sku, 0) + item.quantity
        )
```

The logic is correct in isolation: check availability, then commit the reservation. The problem is the gap between the two loops.

**Premises:** Both loops read and write `self._reserved`. No lock is held across the two loops. In a multi-threaded or async server, another request can call `release_reservation()` between the end of Pass 1 and the start of Pass 2.

**Trace:** Request A validates that 1 unit of SKU-X is available and passes the check. Before Request A enters the commit loop, Request B cancels its order and calls `release_reservation([SKU-X qty=1])`. `self._reserved["SKU-X"]` is decremented (and with no floor guard, can go negative). Request A resumes its commit loop and increments `self._reserved["SKU-X"]` by 1. The accounting is now corrupted: the same unit appears reserved twice in two separate carts. Both carts proceed to payment. Both pay. One shipment fails.

**Divergence:** The validate-then-commit pattern is not atomic. Any concurrent modification to `self._reserved` between the two passes produces an invalid reservation state.

What would a linter tell you? Nothing. This is not a syntax error. It is a semantic property of the function's interaction with concurrent callers — and static analysis tools that do not model time and interleaving cannot detect it.

The **remedy** is to hold a `threading.Lock` across both loops, and to make the constructor take a defensive copy of the input dict rather than aliasing the caller's mutable dict directly.

---

## The Logic Score: A Dashboard for the Whole Module

After tracing all eight files, Logic-Lens produces a Module Breakdown table:

| Module            | Score | Critical | Warning | Suggestion | Top Risk |
|-------------------|-------|----------|---------|------------|----------|
| cart.py           | 85    | 0        | 1       | 0          | L3       |
| pricing.py        | 70    | 1        | 0       | 0          | L1       |
| inventory.py      | 70    | 1        | 0       | 0          | L4       |
| order.py          | 85    | 0        | 1       | 0          | L2       |
| tax.py            | 85    | 0        | 1       | 0          | L6       |
| payment.py        | 85    | 0        | 1       | 0          | L5       |
| checkout.py       | 100   | 0        | 0       | 0          | —        |
| notifications.py  | 100   | 0        | 0       | 0          | —        |

**Overall Logic Score: 52/100.**

The scoring formula is straightforward: each module starts at 100, deducts 30 per confirmed Critical and 15 per confirmed Warning (Suggestions deduct 5, but none appear in this codebase). The repo-level aggregate is the LOC-weighted average of per-module scores, then takes additional deductions for systemic patterns that no single module owns — in this case −15 each for the two cross-module patterns (Optional-without-null-check, resource-without-finally) plus a small cluster penalty for clusters of un-systemically-remediated Warnings. That is how the LOC-weighted ~85 collapses to a repo-level 52.

The 100s in `checkout.py` and `notifications.py` are meaningful data points, not consolation prizes. Checkout is intentionally clean — it is the orchestration layer that trusts its callees. Notifications uses a straightforward try/except around logging calls with no shared state. Logic-Lens correctly assigns them perfect scores because no confirmed divergences were found after tracing.

The Systemic Patterns section is where a health check earns its value over individual reviews. Two patterns emerge across this codebase:

**Unchecked Optional returns (L2 + L6 co-occurrence).** Both `order.py` and `tax.py` receive `Optional[T]` values from callees and use them without null-checking. This is not two isolated oversights — it is evidence that the team's convention does not include "always check Optional before use." The remedy is not two individual fixes; it is enabling `mypy --strict` with `--disallow-any-generics` so that unchecked Optional access becomes a type error at CI time.

**Resource acquisition without `try/finally` (L5 enabler).** `payment.py` acquired a connection object using the pre-context-manager pattern. The same mistake will appear naturally in any future module that opens a database cursor or file handle the same way. A team-wide rule — "all resource acquisition uses `with` or `try/finally`" — prevents this class of bug permanently.

---

## Try It Yourself

The full codebase and this report are in the Logic-Lens repository under `docs/case-studies/01-checkout-module/`.

**Prerequisites:** Logic-Lens v0.5.0+ installed as a Claude Code plugin.

```bash
git clone https://github.com/hyhmrright/logic-lens
cd logic-lens
# Follow the First Clone Setup steps in CLAUDE.md
bash hooks/session-start
```

Then open Claude Code in the case study directory and run:

```
/logic-health docs/case-studies/01-checkout-module/code/
```

You should see the same Module Breakdown table, the same six findings, and the same 52/100 overall score. Every finding in this post is reproducible from the source files exactly as committed — no hidden setup, no special flags.

To explore individual files in depth, use `/logic-review` on a single module:

```
/logic-review docs/case-studies/01-checkout-module/code/tax.py
```

To trace the exact execution path from `checkout.py` down into `calculate_tax` and observe where the `None` appears:

```
/logic-explain docs/case-studies/01-checkout-module/code/checkout.py run_checkout region_code="AU"
```

To see the before/after diff after fixing the `tax.py` null guard and re-running the health check:

```
/logic-fix-all docs/case-studies/01-checkout-module/code/
```

All commands are documented in the [Logic-Lens v0.5.0 release notes](https://github.com/hyhmrright/logic-lens/releases/tag/v0.5.0). The source, evals, and plugin manifests for every supported AI runtime (Claude Code, Codex CLI, Gemini CLI) are in the same repository.

---

## Closing: What 52/100 Actually Means

A Logic Score of 52/100 does not mean the codebase is broken. The happy path works. A customer in California, buying three items with no coupon and a saved address, will check out successfully every time. Thirty-eight tests verify exactly that.

What 52/100 means is: this codebase has six confirmed locations where the code's execution diverges from its stated intent under conditions that are realistic, reproducible, and silent at development time. One of them will affect every customer outside six hard-coded regions. Another will create negative inventory counts under concurrent load. A third leaks a gateway connection on every high-value charge. All three are one-to-three-line fixes once you know where to look.

Logic-Lens does not replace your linter. It does not replace your unit tests. It does not replace code review. It does the specific thing that none of those tools do: it asks, for each function, "does this code actually do what it claims to do under every input the caller can provide?" — and it writes down the execution trace that proves the answer.

If you find a false positive in this case study — a finding where the trace does not hold — open an issue at [github.com/hyhmrright/logic-lens](https://github.com/hyhmrright/logic-lens). The scoring formula, the risk taxonomy, and the tracing methodology are all open and auditable. The goal is reproducible correctness analysis, and that means every claim in a Logic-Lens report should be checkable by anyone willing to follow the trace.
