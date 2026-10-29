# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `classes/range.js`: construction, OR simplification, matching, and intersection; supporting comparator/version implementations, README contracts, and local fixtures. Partial review.  
**Logic Score:** 72/100

Four confirmed Warning defects. The score reflects confirmed findings in the inspected paths, not overall correctness.

## Findings

### 🟡 Warning — [L2] Comparator construction leaves options undefined

**Premises:** Constructing a `Range` from a `Comparator` is explicitly supported by `test/classes/range.js:41`. Matching an allowed prerelease should return a boolean, as it does with equivalent string input.

**Trace:** At [range.js:21](/private/var/folders/kb/clk179sd5qq5htsth48gfk5c0000gn/T/logic-lens-run-x2p8o874/workspace/classes/range.js:21), the `Comparator` branch sets `raw` and `set`, then returns before initializing `this.options`. `test()` passes that undefined value to `testSet()`. Once the comparator accepts a prerelease, line 530 evaluates `options.includePrerelease`.

**Divergence:** **L2:** An undefined options value reaches code requiring an object, producing `TypeError: Cannot read properties of undefined (reading 'includePrerelease')`. This also escapes through `satisfies()`, whose catch covers construction only.

**Trigger:**

```js
new Range(new Comparator('>=1.2.3-alpha')).test('1.2.3-beta')
```

Expected `true`; observed the exception. Equivalent string construction returns `true`. Stable `1.2.3` succeeds, explaining why ordinary matching misses the defect. Explicitly supplying `{ includePrerelease: true }` still throws.

**Remedy:** Move these existing assignments before the `range instanceof Comparator` branch:

```js
this.options = options
this.loose = !!options.loose
this.includePrerelease = !!options.includePrerelease
```

Dry-run: mentally checked against prerelease and stable inputs; no fix executed.

**Verification:** Execution-verified with string and `SemVer` version inputs, default and explicit options, and the public `satisfies()` function.

### 🟡 Warning — [L5] Wildcard simplification deletes explicitly allowed prereleases

**Premises:** README lines 174–176 define `||` as union. Lines 187–190 allow prereleases explicitly named by a comparator set, while lines 312–314 say default `*` matches only non-prerelease versions.

**Trace:** Both branches of `* || 1.2.3-alpha` parse successfully. At [range.js:60](/private/var/folders/kb/clk179sd5qq5htsth48gfk5c0000gn/T/logic-lens-run-x2p8o874/workspace/classes/range.js:60), the constructor encounters the wildcard, replaces the entire branch list with it, and breaks. `testSet()` subsequently rejects `1.2.3-alpha` because the retained wildcard contains no prerelease opt-in.

**Divergence:** **L5:** The early simplification discards a branch required to preserve the union’s accepted versions.

**Trigger:**

```js
new Range('* || 1.2.3-alpha').test('1.2.3-alpha')
```

Expected `true`; observed `false`. The exact prerelease branch alone returns `true`. Reversing branch order produces the same failure; `>=0.0.0 || 1.2.3-alpha` also fails.

**Remedy:** Change line 62 to:

```js
if (this.includePrerelease && c.length === 1 && isAny(c[0])) {
```

This preserves other branches when the wildcard excludes prereleases. Dry-run: mentally checked; with `includePrerelease: true`, the wildcard remains universal and simplification is valid.

**Verification:** Execution-verified in both branch orders, with the normalized wildcard alias, stable controls, and `includePrerelease: true`.

### 🟡 Warning — [L6] Intersection loses comparator-set prerelease authorization

**Premises:** Prerelease authorization applies to the complete comparator set (README lines 187–190). Two ranges sharing a version must intersect (README lines 456–457).

**Trace:** Both `>=1.2.3-alpha <2.0.0` and `1.2.3-beta` individually accept `1.2.3-beta`. However, [range.js:181](/private/var/folders/kb/clk179sd5qq5htsth48gfk5c0000gn/T/logic-lens-run-x2p8o874/workspace/classes/range.js:181) checks every comparator pair separately. `Comparator.intersects()` at `classes/comparator.js:93` converts `<2.0.0` into a standalone range and tests the exact prerelease against it. That isolated range lacks the authorization supplied by `>=1.2.3-alpha`, so it returns `false`.

**Divergence:** **L6:** The caller assumes individual comparator intersections preserve whole-set matching semantics. The resulting intersection incorrectly reports no shared version.

**Trigger:**

```js
intersects('>=1.2.3-alpha <2.0.0', '1.2.3-beta')
```

Expected `true`; observed `false` in both argument orders. The common witness passes both ranges’ `test()` methods. A stable exact-version control succeeds.

**Remedy:** For equality-constrained branch pairs, evaluate the exact candidate against both complete sets before pairwise checks. Replace lines 175–189 with:

```js
const opts = parseOptions(options)
return this.set.some(a => range.set.some(b => {
  const exact = a.concat(b).find(c =>
    c.operator === '' && !isAny(c))
  if (exact) {
    return testSet(a, exact.semver, opts) &&
      testSet(b, exact.semver, opts)
  }
  return isSatisfiable(a, options) &&
    isSatisfiable(b, options) &&
    a.every(x => b.every(y => x.intersects(y, options)))
}))
```

Dry-run: mentally checked for the trigger and conflicting equalities. This addresses equality-constrained pairs; it is not a general intersection repair.

**Verification:** Execution-verified original failure, common witness, isolated comparator decisions, argument symmetry, and option controls. Remedy unexecuted.

### 🟡 Warning — [L3] Satisfiability checks accept empty ranges

**Premises:** `<0.0.0-0` is explicitly the implementation’s null-set sentinel. Also, under default prerelease exclusion, no version satisfies `>1.0.0 <1.0.1`: there is no stable release between those endpoints.

**Trace:** At [range.js:238](/private/var/folders/kb/clk179sd5qq5htsth48gfk5c0000gn/T/logic-lens-run-x2p8o874/workspace/classes/range.js:238), `isSatisfiable()` initializes `true`. A singleton sentinel undergoes no checks. For the adjacent-release gap, comparator ordering reports compatible bounds without establishing an admissible version. Against `*`, `Comparator.intersects()` returns `true` through its wildcard shortcut.

**Divergence:** **L3:** Both empty ranges are reported as intersecting a wildcard.

**Trigger:**

```js
intersects('<0.0.0-0', '*')       // observed true; expected false
intersects('>1.0.0 <1.0.1', '*') // observed true; expected false
```

The first is empty even with `includePrerelease: true`. The second is empty under default options. Changing its upper bound to `<=1.0.1` correctly supplies witness `1.0.1`.

**Remedy:** For the sentinel case, insert at the beginning of `isSatisfiable()`:

```js
if (comparators.some(isNullSet)) {
  return false
}
```

Dry-run: mentally checked for the sentinel and normal ranges. This does **not** repair discrete release gaps; a complete witness-based replacement was not established during this review.

**Verification:** Execution-verified both false positives and the inclusive-upper-bound control. Emptiness follows from version ordering and documented prerelease exclusion, not merely sampled candidates.

## Summary

All four defects were reproduced using the actual implementation on Node.js v26.13.0. Separately, 325 assertions drawn from existing include, exclude, and intersection fixtures passed, demonstrating that those fixtures miss the reported cases.

Eight tool calls were used, including one blocked heredoc invocation. No files were written, dependencies installed, or external services contacted. Remedies were reasoned through only; comprehensive intersection behavior, remaining parser boundaries, and remedy regression coverage remain outside the verified scope.