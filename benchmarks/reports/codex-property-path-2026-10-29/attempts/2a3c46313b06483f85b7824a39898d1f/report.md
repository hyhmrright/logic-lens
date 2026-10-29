# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** [classes/range.js](/var/folders/kb/clk179sd5qq5htsth48gfk5c0000gn/T/logic-lens-run-ev_h5_xz/workspace/classes/range.js), supported by comparator/version implementations, public wrappers, README contracts, and targeted tests. Partial review within ten calls.  
**Logic Score:** 79/100

Three confirmed defects: two incorrect prerelease results and one exception on a supported constructor path.

## Findings

### 🟡 Warning

**[L4] — Wildcard simplification discards explicitly admitted prereleases**

**Premises:** README lines 174–176 define `A || B` as matching either branch. Lines 187–190 allow a comparator set to admit prereleases explicitly. Thus, `*` does not subsume every valid branch under default options.

**Trace:**  
1. Constructing `'* || 1.2.3-alpha'` produces a wildcard comparator set and an exact prerelease comparator set.
2. At `range.js:59–65`, finding the wildcard replaces `this.set` with that branch alone.
3. `test('1.2.3-alpha')` reaches `testSet`; the wildcard supplies no comparator admitting this prerelease, so it returns `false`.

Rebuttal check: the exact branch alone returns `true`; reversing branch order still fails. Enabling `includePrerelease` returns `true`.

**Divergence:** **L4**, at `this.set = [c]`: destructive simplification changes the documented union’s membership. Adding a wildcard branch makes an accepted version become rejected. The public `satisfies` wrapper also returns the incorrect result.

**Trigger:**

```js
new Range('1.2.3-alpha').test('1.2.3-alpha')      // true
new Range('* || 1.2.3-alpha').test('1.2.3-alpha') // false; expected true
```

**Remedy:** Replace the condition at line 62 with:

```js
if (c.length === 1 && isAny(c[0]) &&
    (this.includePrerelease || !this.set.some(set =>
      set.some(comp => !isAny(comp) && comp.semver.prerelease.length)))) {
```

Dry-run: preserves branches with explicit prerelease admission under default options while retaining wildcard collapse otherwise. Reasoned only; no patch executed.

**Verification:** ✅ Execution-verified on Node.js v26.13.0. The bounded union property found the witness in four evaluations, including control and reduction. [Search evidence](/var/folders/kb/clk179sd5qq5htsth48gfk5c0000gn/T/logic-lens-run-ev_h5_xz/harness/union-evidence/summary.json).

---

**[L6] — Intersection checks lose comparator-set prerelease admission**

**Premises:** README lines 456–457 require intersecting ranges to return `true`. The range `>=1.2.3-alpha <2.0.0` admits `1.2.3-alpha`, which also belongs to the exact range `1.2.3-alpha`; their intersection is therefore nonempty.

**Trace:**  
1. `Range.test('1.2.3-alpha')` accepts both bounds and finds prerelease admission in the lower-bound comparator.
2. `Range.intersects`, at lines 181–184, instead checks individual comparator pairs.
3. For `<2.0.0` versus exact `1.2.3-alpha`, `Comparator.intersects` constructs a standalone `Range('<2.0.0')` at `comparator.js:93`.
4. That standalone range lacks the lower bound’s prerelease admission and rejects the version, making the complete intersection return `false`.

Rebuttal check: both intersection directions and the public wrapper fail. A stable exact-version control passes, as does the prerelease case with `includePrerelease: true`.

**Divergence:** **L6**, at `range.js:183`: individual comparator intersection does not preserve prerelease admission supplied by the complete comparator set. The observable consequence is a false report that two overlapping ranges are disjoint.

**Trigger:**

```js
const a = new Range('>=1.2.3-alpha <2.0.0')
const b = new Range('1.2.3-alpha')

a.test('1.2.3-alpha') // true
a.intersects(b)      // false; expected true
b.intersects(a)      // false; expected true
```

**Remedy:** Replace the return expression at lines 175–189 with the following. An exact comparator fixes the only possible common version, so evaluate that version against both complete sets:

```js
const opts = parseOptions(options)
return this.set.some(a => range.set.some(b => {
  const exact = a.concat(b).find(c =>
    c.operator === '' && !isAny(c))
  if (exact) {
    return testSet(a, exact.semver, opts) &&
      testSet(b, exact.semver, opts)
  }
  return isSatisfiable(a, opts) &&
    isSatisfiable(b, opts) &&
    a.every(x => b.every(y => x.intersects(y, opts)))
}))
```

Dry-run: resolves the confirmed exact-version case and preserves the existing interval-only path. Reasoned only; broader intersection correctness remains unverified.

**Verification:** ✅ Execution-verified on Node.js v26.13.0. The singleton-intersection property found the witness in four evaluations. [Search evidence](/var/folders/kb/clk179sd5qq5htsth48gfk5c0000gn/T/logic-lens-run-ev_h5_xz/harness/intersection-evidence/summary.json).

---

**[L5] — Comparator constructor path skips required option initialization**

**Premises:** The constructor explicitly supports `Comparator` input; `test/classes/range.js:41–45` exercises that conversion. `Range.test` passes `this.options` to `testSet`, which reads `options.includePrerelease` when evaluating prereleases.

**Trace:**  
1. `new Range(new Comparator('>=1.2.3-alpha'))` takes the branch at `range.js:21`.
2. The return at line 26 skips initialization of `this.options`, `this.loose`, and `this.includePrerelease` at lines 29–31.
3. Testing `1.2.3-alpha` passes the comparator and enters the prerelease check.
4. At line 530, reading `options.includePrerelease` throws because `options` is `undefined`.

Rebuttal check: the equivalent string constructor returns `true`; a stable-version control passes. Supplying explicit options to the Comparator-input constructor still throws.

**Divergence:** **L5**, at the early return on line 26: a supported construction route omits state required by subsequent methods. Valid prerelease membership testing throws instead of returning `true`. The exception also escapes `satisfies`, whose catch covers construction only.

**Trigger:**

```js
new Range(new Comparator('>=1.2.3-alpha'))
  .test('1.2.3-alpha')
// TypeError: Cannot read properties of undefined
// (reading 'includePrerelease')
```

**Remedy:** Move these assignments from lines 29–31 to immediately before the Comparator branch at line 21:

```js
this.options = options
this.loose = !!options.loose
this.includePrerelease = !!options.includePrerelease
```

Dry-run: both construction routes initialize the fields before returning. Reasoned only; no fix executed.

**Verification:** ✅ Execution-verified against the original snapshot, including string, stable-version, explicit-option, and public-wrapper comparisons. [Direct evidence](/var/folders/kb/clk179sd5qq5htsth48gfk5c0000gn/T/logic-lens-run-ev_h5_xz/harness/direct-evidence.json).

## Summary

All three defects have concrete local reproductions and source-supported expected behavior. Source files remained unchanged; no dependencies, external services, or integration tests were used.

Verification used Node.js v26.13.0. Each property declared 24 combinations and stopped after finding a counterexample; neither exhausted its domain. Remedies were evaluated mentally, without execution or regression testing. The score describes confirmed findings in this inspected slice.

## Unresolved Investigations

Intersection behavior without an exact comparator, numeric expansion boundaries, loose parsing, and cache mutation were not fully investigated within the budget. No additional defect is claimed for those paths.