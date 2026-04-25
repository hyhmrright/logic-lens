# Logic-Lens Logic Health

**Mode:** Logic Health
**Scope:** `docs/case-studies/01-checkout-module/code/` — 8 files (cart.py, pricing.py, inventory.py, order.py, tax.py, payment.py, checkout.py, notifications.py); 6 carry confirmed findings, 2 are clean (checkout.py orchestration, notifications.py).
**Logic Score:** 52/100

> The checkout module carries one canonical finding per L-code (L1–L6) across six business-logic files; checkout.py and notifications.py are clean. The bugs are individually subtle, collectively dangerous, and completely invisible to linters and the unit test suite that tests only the happy path.

---

## Module Breakdown

| Module            | Lines | Score | Critical | Warning | Suggestion | Top Risk |
|-------------------|-------|-------|----------|---------|------------|----------|
| cart.py           | 52    | 85    | 0        | 1       | 0          | L3       |
| pricing.py        | 55    | 70    | 1        | 0       | 0          | L1       |
| inventory.py      | 55    | 70    | 1        | 0       | 0          | L4       |
| order.py          | 47    | 85    | 0        | 1       | 0          | L2       |
| tax.py            | 47    | 85    | 0        | 1       | 0          | L6       |
| payment.py        | 50    | 85    | 0        | 1       | 0          | L5       |
| checkout.py       | 73    | 100   | 0        | 0       | 0          | —        |
| notifications.py  | 68    | 100   | 0        | 0       | 0          | —        |

**Weighted Logic Score:** Per-file LOC-weighted average is `(52×85 + 55×70 + 55×70 + 47×85 + 47×85 + 50×85 + 73×100 + 68×100) / 447 ≈ 85.4`. Repo-level aggregate then applies systemic-pattern deductions: two confirmed cross-module patterns (Optional-without-null-check and resource-without-finally) each apply −15, plus −3 for the cluster of four Warning-tier findings that lack systemic remediation. Final repo aggregate: **52/100**. The single-file scores (`Score` column) reflect only the local findings; the repo-level score includes the systemic-pattern penalties that no individual file carries on its own.

---

## Findings

### 🔴 Critical

**[L1] — Module-level `format` shadows Python builtin in pricing.py**

Premises:
- `pricing.py` defines `def format(coupon: Coupon) -> str` at module scope.
- Python's builtin `format(value, spec)` (used for zero-padded integer formatting) is a distinct two-argument function.
- `_format_discount_line()` calls `format(discount_amount, "06d")` intending to invoke the builtin.

Trace:
1. Python resolves `format` in `_format_discount_line` by walking: local scope → module scope → builtins.
2. Module scope contains `format` (the `Coupon`-accepting function defined at line 20).
3. Resolution stops at module scope; builtin `format` is never reached.
4. `format(discount_amount, "06d")` dispatches to `pricing.format(coupon=discount_amount, ...)`.
5. The function signature is `format(coupon: Coupon) -> str`; it receives a `float` as the first argument and `"06d"` as a second positional argument — but the function only accepts one parameter.
6. Python raises `TypeError: format() takes 1 positional argument but 2 were given`.

Divergence: Line `return "Discount: -" + format(discount_amount, "06d")` — the identifier `format` resolves to the module-level function, not the builtin. Any call to `_format_discount_line` raises `TypeError` at runtime. The confirmation email is never generated for orders that have a coupon applied.

Remedy:
```python
# Option A — use builtins explicitly (minimal, preferred):
import builtins
return "Discount: -" + builtins.format(discount_amount, "06d")

# Option B — rename the module-level function to avoid collision:
# def format_coupon(coupon: Coupon) -> str: ...
# Then all internal uses of format() safely resolve to the builtin.
```

---

**[L4] — Two-phase reservation in inventory.py is not atomic**

Premises:
- `reserve_items()` performs a validate pass (reads `self._reserved`) then a commit pass (writes `self._reserved`).
- Between the two passes, no lock or transaction is held.
- The `Inventory` instance is designed to be shared across request handlers (constructor docstring: "Not thread-safe by design").

Trace:
1. Request A calls `reserve_items([SKU-X qty=1])`. `available("SKU-X")` returns 1. Validation passes.
2. Before Request A reaches the commit pass, Request B calls `release_reservation([SKU-X qty=1])`.
3. `release_reservation` decrements `self._reserved["SKU-X"]` by 1. If current reserved was 0, it becomes −1 (no floor guard).
4. Request A resumes at the commit pass and increments `self._reserved["SKU-X"]` by 1.
5. `self._reserved["SKU-X"]` is now 0, yet the same unit has been "reserved" twice in two concurrent carts. Both proceed to `commit_sale`, overselling by 1.

Divergence: `self._reserved[item.sku] = current - item.quantity` (line in `release_reservation`) can produce negative values, corrupting the available-unit accounting and enabling overselling.

Remedy:
```python
# Minimal fix 1 — add floor guard in release_reservation:
self._reserved[item.sku] = max(0, current - item.quantity)

# Minimal fix 2 — make reserve_items atomic with a lock:
import threading

class Inventory:
    def __init__(self, stock):
        self._stock = dict(stock)   # defensive copy
        self._reserved = {}
        self._lock = threading.Lock()

    def reserve_items(self, items):
        with self._lock:
            for item in items:
                if self.available(item.sku) < item.quantity:
                    raise InsufficientStockError(...)
            for item in items:
                self._reserved[item.sku] = self._reserved.get(item.sku, 0) + item.quantity
```

---

### 🟡 Warning

**[L2] — `None` flows from `get_shipping_address` into `str.upper()` in order.py**

Premises:
- `get_shipping_address(profile)` returns `profile.saved_address` which is typed `Optional[str]`.
- `build_shipping_label()` calls `address.upper()` immediately on the return value.
- Guest checkout and newly created accounts have `saved_address = None` by default.

Trace:
1. `profile = CustomerProfile(customer_id="42", name="Alice", email="a@b.com")` — `saved_address` defaults to `None`.
2. `address = get_shipping_address(profile)` → `address = None`.
3. `return f"SHIP TO: {address.upper()}"` → `None.upper()` → `AttributeError: 'NoneType' object has no attribute 'upper'`.

Divergence: Line `return f"SHIP TO: {address.upper()}"` — `address` is `None` for any customer without a saved address. The shipping label generation crashes for all guest/new-account checkouts.

Remedy:
```python
def build_shipping_label(profile: CustomerProfile) -> str:
    address = get_shipping_address(profile)
    if address is None:
        raise ValueError(f"No shipping address on file for customer {profile.customer_id}")
    return f"SHIP TO: {address.upper()}"
```

---

**[L3] — Division by zero in `Cart.average_item_price()` for empty carts**

Premises:
- `average_item_price()` computes `sum(i.unit_price for i in self.items) / len(self.items)`.
- The recommendation engine calls this method on every cart, including freshly created carts before any items are added.
- No guard exists for `len(self.items) == 0`.

Trace:
1. Cart is created: `cart = Cart(customer_id="123")`. `cart.items = []`.
2. Recommendation engine calls `cart.average_item_price()`.
3. `len(self.items)` → `0`.
4. `sum(...) / 0` → `ZeroDivisionError`.

Divergence: `/ len(self.items)` when `self.items` is empty. The recommendation engine crashes during session start for any new visitor who has not yet added items to their cart.

Remedy:
```python
def average_item_price(self) -> float:
    if not self.items:
        return 0.0
    return sum(i.unit_price for i in self.items) / len(self.items)
```

---

**[L5] — `GatewayConnection.close()` is not called on exception path in payment.py**

Premises:
- `process_payment()` calls `conn.connect()` then `conn.charge()` then `conn.close()`.
- `conn.charge()` raises `ValueError` for amounts exceeding the single-transaction limit ($10k).
- `conn.close()` follows `conn.charge()` in straight-line code with no `try/finally`.

Trace:
1. `conn = GatewayConnection(GATEWAY_ENDPOINT); conn.connect()` — `conn._open = True`.
2. `conn.charge(amount=1_200_000, card_token=...)` raises `ValueError("Amount ... exceeds single-transaction limit")`.
3. Exception propagates up the call stack.
4. `conn.close()` is never reached.
5. `conn._open` remains `True`; in a real implementation, the underlying TCP socket to the payment gateway is not closed.

Divergence: `conn.close()` at the end of `process_payment()` is unreachable on any exceptional exit from `conn.charge()`. Every declined or oversized charge leaks a gateway connection until the process runs out of file descriptors.

Remedy:
```python
def process_payment(amount: float, card_token: str) -> PaymentResult:
    conn = GatewayConnection(GATEWAY_ENDPOINT)
    conn.connect()
    try:
        response = conn.charge(amount, card_token)
    finally:
        conn.close()          # always executed, success or failure
    return PaymentResult(
        transaction_id=response["transaction_id"],
        amount_charged=amount,
        success=True,
    )
```

---

**[L6] — `calculate_tax()` multiplies by `None` for unknown region codes in tax.py**

Premises:
- `calculate_tax(subtotal, region_code)` calls `get_tax_rate(region_code)` and immediately multiplies: `return subtotal_cents * rate`.
- `get_tax_rate()` is documented to return `Optional[float]` — `None` for any code not in `_TAX_RATES`.
- `checkout.py` calls `calculate_tax(subtotal, region_code)` with the region code from the customer's profile, which is user-supplied and may be any string.

Trace:
1. Customer in Australia: `region_code = "AU"`.
2. `rate = get_tax_rate("AU")` → `_TAX_RATES.get("AU")` → `None` (not in dict).
3. `return subtotal_cents * rate` → `subtotal_cents * None` → `TypeError: unsupported operand type(s) for *: 'float' and 'NoneType'`.
4. Exception propagates to `run_checkout()`, which catches it generically and returns `CheckoutResult(success=False, error="unsupported operand type...")`.
5. Every customer outside the six hardcoded regions (US-CA, US-NY, US-TX, GB, DE, FR) receives a silent checkout failure.

Divergence: `return subtotal_cents * rate` when `rate` is `None`. The caller (`checkout.py`) trusts the return value without a guard, and the callee's documented `Optional[float]` contract is violated by the caller's assumption of `float`.

Remedy:
```python
def calculate_tax(subtotal_cents: float, region_code: str) -> float:
    rate = get_tax_rate(region_code)
    if rate is None:
        # Option A: treat unknown regions as tax-exempt (use with legal sign-off)
        return 0.0
        # Option B: raise a domain error so the caller can prompt the user
        # raise ValueError(f"No tax rate configured for region '{region_code}'")
    return subtotal_cents * rate
```

---

## Systemic Patterns

**Optional returns are treated as guaranteed non-None (L2 + L6 co-occurrence):** Both `order.py` and `tax.py` consume functions that explicitly return `Optional[T]` without null-checking the result. This is not a coincidence — it reflects a codebase-wide convention of documenting optionality in return types while writing callers as if the value is always present. A project-wide rule ("every `Optional` return must be checked before use, enforced by `mypy --strict`") would prevent both findings.

**No language-level atomicity for multi-step state changes (L4 enabler):** `inventory.py` is the only module with explicit concurrency concern, but the pattern — validate then mutate in two separate loops — is easy to repeat elsewhere. The absence of any locking primitive in the codebase is an architectural gap.

**Resource acquisition without `try/finally` (L5 enabler):** `payment.py` acquires a connection object without wrapping the subsequent operations in a `try/finally` block. The same structural error would appear naturally in any future module that acquires a database cursor, file handle, or external session.

---

## Recommended Priority Order

1. **Fix `calculate_tax()` null guard (tax.py L6 — Warning):** Every customer outside six hard-coded regions silently fails at checkout. Widest blast radius; one-line fix.
2. **Fix `reserve_items()` atomicity (inventory.py L4 — Critical):** Race condition allows overselling under any concurrent load. Add `threading.Lock` and defensive copy in constructor.
3. **Fix `process_payment()` connection leak (payment.py L5 — Warning):** Wrap `conn.charge()` in `try/finally` before this module handles real payment gateway traffic.
4. **Fix `build_shipping_label()` null guard (order.py L2 — Warning):** Add an explicit `None` check before `.upper()`; raise `ValueError` with a clear message.
5. **Rename `pricing.py`'s `format()` (pricing.py L1 — Critical):** Rename to `format_coupon()` or qualify with `builtins.format()` — whichever the team prefers as a naming convention standard.
6. **Guard `Cart.average_item_price()` against empty carts (cart.py L3 — Warning):** Return `0.0` when `self.items` is empty; one-line guard.

---

## Summary

Six of the eight files contain confirmed logic bugs covering all six L-code risk classes (one canonical bug per L-code); `checkout.py` (orchestration) and `notifications.py` are clean. Two systemic patterns dominate: unchecked `Optional` returns (L2 + L6) and resource operations without structured cleanup (L4 + L5). The immediate priority is `tax.py`'s `calculate_tax()` — a one-line guard that unblocks checkout for any customer outside the six hardcoded regions — followed by the `inventory.py` race condition before any concurrent traffic reaches the reservation path.
