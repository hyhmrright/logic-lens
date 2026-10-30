# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `classes/range.js`, supported by comparator/version implementations, parsing helpers, public callers, README contracts, and relevant fixtures. Checked construction, shorthand expansion, prerelease matching, union simplification, and intersection. This was a bounded review, not exhaustive coverage.  
**Logic Score:** 79/100

Five confirmed defects. All reproductions imported the actual local implementation under Node.js v26.13.0.

## Findings

### 🟡 Warning

**[L5] — Construction from a Comparator skips required initialization**

**Premises:** Comparator input is explicitly supported by the constructor and exercised in `test/classes/range.js:41`. Prerelease matching requires initialized range options.

**Trace:** The [Comparator branch](classes/range.js:21) sets `raw` and `set`, then returns before initializing `this.options`. `Range.test()` parses a valid prerelease and passes that undefined value to `testSet()`. When comparator testing succeeds, [line 530](classes/range.js:530) reads `options.includePrerelease`. Rebuttal check: construction from the equivalent string succeeds; stable-version testing also succeeds.

**Divergence:** L5 — the early return skips initialization, causing a supported matching operation to throw instead of returning a boolean. It also ignores `{ loose: true }`: a leading-zero version accepted through string construction is rejected through Comparator construction.

**Trigger:**
```js
new Range(new Comparator('>=1.2.3-alpha')).test('1.2.3-beta')
// Expected: true
// Observed: TypeError reading 'includePrerelease'
```

**Remedy:** Move the existing assignments to `this.options`, `this.loose`, and `this.includePrerelease` at lines 29–31 before the Comparator branch. Dry-run: mentally restores both matching options and the prerelease guard.

**Verification:** Execution-verified, including string-construction and stable-version controls. Remedy not executed.

---

**[L6] — Wildcard union simplification discards explicitly permitted prereleases**

**Premises:** README.md:175–177 defines `||` as accepting a version accepted by either branch. README.md:187–190 allows explicitly targeted prereleases; default `*` excludes them.

**Trace:** Both branches of `* || 1.2.3-alpha` parse successfully. The [wildcard optimization](classes/range.js:60) replaces the entire union with `*`. `testSet()` then rejects the prerelease because no retained comparator opts into its tuple. Rebuttal check: the exact-version branch alone accepts it, and the union accepts stable versions.

**Divergence:** L6 — the constructor treats the wildcard comparator as universal, but the downstream range matcher gives it narrower prerelease semantics. The union loses a version explicitly included by one branch.

**Trigger:**
```js
new Range('* || 1.2.3-alpha').test('1.2.3-alpha')
// Expected: true
// Observed: false
```

**Remedy:** Change line 62 to:
```js
if (this.includePrerelease && c.length === 1 && isAny(c[0])) {
```
Dry-run: mentally preserves default-mode prerelease branches while retaining the optimization when `*` actually includes prereleases.

**Verification:** Execution-verified with individual-branch, stable-version, and `includePrerelease: true` controls. Remedy not executed.

---

**[L2] — Loose caret ranges apply the wrong compatibility boundary to padded zeroes**

**Premises:** Loose parsing accepts leading-zero components and normalizes them numerically. README.md:342–359 gives different caret limits for major zero and major/minor zero.

**Trace:** The loose caret regex captures `"00"` as a string. [The caret expansion](classes/range.js:345) compares it with the literal string `"0"`, selecting the nonzero branch. Subsequent Comparator/SemVer construction normalizes the lower bound numerically, but the overly broad upper bound is already generated. Rebuttal check: equivalent unpadded input produces the documented boundary.

**Divergence:** L2 — textual zero detection disagrees with numeric version interpretation, admitting incompatible releases.

**Trigger:**
```js
new Range('^00.2.3', { loose: true }).test('0.3.0')
// Expected: false, like ^0.2.3
// Observed: true; expands to >=0.2.3 <1.0.0-0
```
Likewise, `^0.00.3` accepts `0.0.4`, whereas `^0.0.3` rejects it.

**Remedy:** In `replaceCaret()`, replace every `M === '0'` with `Number(M) === 0`, and every `m === '0'` with `Number(m) === 0`. Dry-run: mentally selects the same branches for padded and canonical numeric zeroes.

**Verification:** Execution-verified for padded major/minor components, partial ranges, and an explicit prerelease. Remedy not executed.

---

**[L6] — Hyphen ranges lose their prerelease lower bound when build metadata is present**

**Premises:** SemVer comparisons exclude build metadata. The existing hyphen implementation and parsing fixture establish that `1.2.3 - 2.0.0` with `includePrerelease: true` starts at `1.2.3-0`.

**Trace:** For a fully specified lower endpoint, [line 503](classes/range.js:503) appends `-0` to the original text, producing `>=1.2.3+build-0`. `parseComparator()` then [removes build metadata](classes/range.js:258), deleting the appended marker along with `+build`. Rebuttal check: the metadata-free range accepts the prerelease; metadata on only the upper endpoint does not cause this failure.

**Divergence:** L6 — the generated prerelease marker occupies the build-metadata field and is discarded. Adding comparison-irrelevant metadata changes which versions match.

**Trigger:**
```js
new Range('1.2.3+build - 2.0.0', {
  includePrerelease: true,
}).test('1.2.3-alpha')
// Expected: true, like the metadata-free range
// Observed: false
```

**Remedy:** Replace line 503 with:
```js
from = `>=${fM}.${fm}.${fp}${incPr ? '-0' : ''}`
```
Dry-run: mentally places `-0` directly after the numeric tuple and preserves the stable lower bound when the option is false.

**Verification:** Execution-verified with multiple build identifiers, explicit-prerelease lower endpoints, and upper-endpoint metadata controls. Remedy not executed.

---

**[L6] — Pairwise comparator overlap does not establish range intersection**

**Premises:** Intersection requires at least one version accepted by both ranges. The README’s comparator-set and prerelease rules define that acceptance.

**Trace:** [Range.intersects()](classes/range.js:175) delegates to pairwise comparator checks:

1. A singleton null set passes `isSatisfiable()` because its loop never executes; the wildcard comparator then reports overlap.
2. `>1.0.0` and `<1.0.1` pass the ordering check in `Comparator.intersects()`, although no stable version lies between them and neither range admits prereleases.
3. For `>=1.0.0-alpha <2.0.0` versus `1.0.0-beta`, the `<2.0.0` comparator checks the equality version through a separate Range. That isolated range rejects the prerelease, losing the original set’s opt-in.

Rebuttal check: both argument orders reproduced these results; direct `test()` calls confirmed the shared witness in case 3.

**Divergence:** L6 — comparator-level decisions lose range-level satisfiability and prerelease context, producing both false positives and false negatives.

**Trigger:**

| Range A | Range B | Expected | Observed |
|---|---|---:|---:|
| `<0.0.0-0` | `*` | false | true |
| `>1.0.0` | `<1.0.1` | false | true |
| `>=1.0.0-alpha <2.0.0` | `1.0.0-beta` | true | false |

**Remedy:** For the null-set case, insert this at the start of `isSatisfiable()`:
```js
if (comparators.some(isNullSet)) {
  return false
}
```
Dry-run: mentally rejects the impossible sentinel. This is a **partial remedy**; a complete concrete repair for the other two failures was not established during this review.

**Verification:** All three original defects execution-verified through the public `ranges/intersects` function. Remedy not executed.

## Summary

The score deducts once per distinct L-code in this module, as required by the supplied scoring rules; it does not measure correctness probability. No source files were modified, dependencies installed, or service/integration tests run. Verification used targeted in-memory probes, not the full test suite.

## Unresolved Investigations

With `includePrerelease: true`, `~1.2` rejects `1.2.0-alpha`, while `1.2.x` accepts it. The README describes these shorthands as equivalent, but their intended option-specific expansion needs clarification before classifying this discrepancy as another defect.