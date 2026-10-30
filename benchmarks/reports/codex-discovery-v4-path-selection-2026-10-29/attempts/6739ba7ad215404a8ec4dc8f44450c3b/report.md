# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `classes/range.js`; supporting comparator, SemVer, parsing, range-helper, README, and fixture files. Targeted review of construction, normalization, matching, and intersections.  
**Logic Score:** 86/100 — Warning deductions capped per unique L-code in this module.

> Four confirmed findings produce incorrect matching results, an exception, and incorrect intersection results.

## Findings

### 🟡 Warning — [L5] Comparator construction skips required initialization

**Premises:** `Comparator` input is explicitly supported by the constructor and `test/classes/range.js`. Range matching reads `this.options`, including its `includePrerelease` setting.

**Trace:** In [classes/range.js:21](/private/var/folders/kb/clk179sd5qq5htsth48gfk5c0000gn/T/logic-lens-run-ajlj9l50/workspace/classes/range.js:21), comparator construction returns at line 26, before initializing `options`, `loose`, and `includePrerelease` at lines 29–31. `test('1.2.3-beta')` parses the version and calls `testSet`; the comparator `>=1.2.3-alpha` passes. Line 530 then reads `options.includePrerelease` from `undefined`. Rebuttal check: stable versions avoid that dereference, explaining why construction can appear functional.

**Divergence:** **L5:** the constructor’s early return skips required initialization. A supported range input subsequently throws instead of returning a matching boolean.

**Trigger:**

```js
new Range(new Comparator('>=1.2.3-alpha')).test('1.2.3-beta')
```

Expected: `true`. Observed: `TypeError: Cannot read properties of undefined (reading 'includePrerelease')`. Passing the comparator’s string value returns `true`. `satisfies()` also propagates this exception because its catch covers construction only.

**Remedy:** Move the existing assignments at lines 29–31 immediately before the comparator branch at line 21. Dry-run: both constructor routes receive initialized options; comparator storage remains unchanged. Reasoned only.

**Verification:** ✅ Execution-verified with actual constructors, `test()`, and `satisfies()`, including stable-version controls.

### 🟡 Warning — [L6] Wildcard simplification removes explicitly allowed prereleases

**Premises:** README lines 174–176 define `||` as alternatives: satisfying either branch is sufficient. Lines 187–215 explain prerelease opt-in; `*` excludes prereleases by default.

**Trace:** Both branches are parsed. At [classes/range.js:59](/private/var/folders/kb/clk179sd5qq5htsth48gfk5c0000gn/T/logic-lens-run-ajlj9l50/workspace/classes/range.js:59), detecting a wildcard replaces all alternatives with that branch alone. `testSet` subsequently rejects prereleases because the remaining wildcard comparator provides no prerelease opt-in. Rebuttal check: both branch orders fail; stable-version matching still succeeds.

**Divergence:** **L6:** wildcard syntax is treated as guaranteeing universal acceptance, although its matching contract excludes prereleases. Adding an OR alternative removes a previously valid match.

**Trigger:**

```js
new Range('1.2.3-alpha').test('1.2.3-alpha')      // true
new Range('* || 1.2.3-alpha').test('1.2.3-alpha') // false
new Range('1.2.3-alpha || *').test('1.2.3-alpha') // false
```

Both combined ranges should return `true`.

**Remedy:** Replace lines 59–67 with a single `}` to retain the preceding null-set fallback while removing wildcard collapse. Dry-run: `test()` can evaluate the explicit prerelease branch; standalone wildcards retain their behavior. Reasoned only.

**Verification:** ✅ Execution-verified in both orders, with standalone wildcard, explicit-version, and stable-version controls.

### 🟡 Warning — [L6] Build metadata erases the hyphen range’s prerelease lower bound

**Premises:** Build metadata is excluded from version comparison (`internal/re.js`, full-version commentary). The hyphen parsing fixture explicitly establishes that, with `includePrerelease: true`, `1.0.0 - 2.0.0` begins at `>=1.0.0-0`.

**Trace:** At [classes/range.js:503](/private/var/folders/kb/clk179sd5qq5htsth48gfk5c0000gn/T/logic-lens-run-ajlj9l50/workspace/classes/range.js:503), `hyphenReplace` appends `-0` to the entire lower endpoint. For `1.2.3+build`, that produces `>=1.2.3+build-0`. `parseComparator` at line 258 removes build metadata, including the appended `-0`, leaving `>=1.2.3`. Rebuttal check: metadata on only the upper endpoint does not cause this failure.

**Divergence:** **L6:** the hyphen expansion assumes later metadata removal preserves its added prerelease bound. Instead, adding comparison-irrelevant metadata changes accepted versions.

**Trigger:**

```js
const opts = { includePrerelease: true }
new Range('1.2.3 - 2.0.0', opts).test('1.2.3-alpha')       // true
new Range('1.2.3+build - 2.0.0', opts).test('1.2.3-alpha') // false
```

Expected: both `true`. The second range normalizes to `>=1.2.3 <2.0.1-0`.

**Remedy:** Replace line 503 with:

```js
from = `>=${fM}.${fm}.${fp}${incPr ? '-0' : ''}`
```

Dry-run: the prerelease suffix follows the numeric tuple; the existing branch for explicitly prereleased endpoints remains intact. Reasoned only.

**Verification:** ✅ Execution-verified against metadata-free, upper-metadata, stable-version, and explicit-prerelease controls.

### 🟡 Warning — [L6] Pairwise comparator intersections do not establish range intersection

**Premises:** README lines 170–176 define comparator sets as conjunctions. `intersects()` should identify a version satisfying both ranges, with prerelease eligibility evaluated in each complete set.

**Trace:** [classes/range.js:175](/private/var/folders/kb/clk179sd5qq5htsth48gfk5c0000gn/T/logic-lens-run-ajlj9l50/workspace/classes/range.js:175) delegates satisfiability and intersection to pairwise `Comparator.intersects()` calls.

For an exact prerelease, `Comparator.intersects()` constructs a range from one opposing comparator (`classes/comparator.js:88–93`). Testing against `<1.0.0` alone discards the neighboring `>=1.0.0-alpha` prerelease opt-in.

Conversely, for `>1.0.0 <1.0.1`, comparator intersection accepts the ordered bounds without establishing an admissible version between them. Rebuttal check: enabling prereleases makes this interval nonempty, so the default exclusion is decisive.

**Divergence:** **L6:** pairwise callee results are assumed to prove whole-set semantics. This yields both false negatives and false positives.

**Trigger:**

```js
const a = new Range('1.0.0-alpha')
const b = new Range('>=1.0.0-alpha <1.0.0')
a.test('1.0.0-alpha') // true
b.test('1.0.0-alpha') // true
a.intersects(b)       // false; expected true
b.intersects(a)       // false; expected true

new Range('>1.0.0 <1.0.1').intersects(new Range('*'))
// true; expected false
```

The last interval contains no stable version and permits no prereleases.

**Remedy:** Replace lines 175–189 with this correction for exact-version and stable-only sets:

```js
const opts = parseOptions(options)
return this.set.some(a => range.set.some(b => {
  const both = [...a, ...b]
  const exact = both.find(c =>
    c.operator === '' && c.semver !== Comparator.ANY)
  if (exact) {
    return testSet(a, exact.semver, opts) &&
      testSet(b, exact.semver, opts)
  }
  if (!opts.includePrerelease && both.every(c =>
    c.semver === Comparator.ANY || !c.semver.prerelease.length)) {
    const candidate = require('../ranges/min-version')(
      both.map(String).join(' '), opts)
    return candidate !== null &&
      testSet(a, candidate, opts) && testSet(b, candidate, opts)
  }
  return isSatisfiable(a, opts) && isSatisfiable(b, opts) &&
    a.every(x => b.every(y => x.intersects(y, opts)))
}))
```

Dry-run: the shared exact witness passes both complete sets; the empty stable interval has no minimum satisfying version. This is a scoped correction; the remaining prerelease interval route retains existing logic. Reasoned only.

**Verification:** ✅ Execution-verified for both intersection orders, the shared witness, the empty interval, and its prerelease-enabled control.

## Summary

All findings were reproduced using the actual local implementation under Node.js v26.13.0. Direct execution of 271 existing inclusion, exclusion, and range-intersection fixture cases passed. No files were modified, dependencies installed, or external services accessed; proposed remedies were not executed or regression-tested.

## Unresolved Investigations

General prerelease interval intersections without exact comparators remain unproven. The next check should establish an actual witness satisfying both complete sets, including each set’s prerelease eligibility. This review was targeted, not exhaustive; the score reflects confirmed findings in the inspected paths.