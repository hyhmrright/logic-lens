# Case Study 01 — Checkout Module

A synthetic but realistic Python checkout service used to demonstrate Logic-Lens `/logic-health` across all six L-code risk classes.

## Contents

| File | Description |
|------|-------------|
| `code/cart.py` | Shopping cart — L3 boundary blindspot (empty cart division) |
| `code/pricing.py` | Coupon pricing — L1 shadow override (builtin `format` shadowed) |
| `code/inventory.py` | Stock reservation — L4 state mutation hazard (non-atomic two-phase reserve) |
| `code/order.py` | Order creation — L2 type contract breach (`None` into `.upper()`) |
| `code/tax.py` | Tax calculation — L6 callee contract mismatch (`None` return unchecked) |
| `code/payment.py` | Payment processing — L5 control flow escape (connection leak on exception) |
| `code/checkout.py` | Orchestration — intentionally clean; score 100 |
| `code/notifications.py` | Email / SMS dispatch — intentionally clean; score 100 |
| `logic-health-report.md` | Full `/logic-health` output following v0.4.x Report Template |
| `blog-post.md` | Blog post for Dev.to / cross-posting |

## Reproduce the Analysis

With Logic-Lens v0.5.0+ installed in Claude Code:

```
/logic-health docs/case-studies/01-checkout-module/code/
```

Expected result: Logic Score 52/100, 2 Critical, 4 Warning, Module Breakdown table matching `logic-health-report.md`.

## Risk Coverage

| Risk Code | Module | Severity |
|-----------|--------|----------|
| L1 — Shadow Override | pricing.py | Critical |
| L2 — Type Contract Breach | order.py | Warning |
| L3 — Boundary Blindspot | cart.py | Warning |
| L4 — State Mutation Hazard | inventory.py | Critical |
| L5 — Control Flow Escape | payment.py | Warning |
| L6 — Callee Contract Mismatch | tax.py | Warning |
