<!-- run 839f79ac449c452ca6685a6a6f03b525; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `classes/range.js`: construction, parsing, matching, and intersection; supporting comparator/version implementations, wrappers, README contracts, and fixtures. Bounded to 10 tool calls; no files modified.  
**Logic Score:** 72/100

Four concrete defects were reproduced. The score describes confirmed findings in this inspected slice.

## Findings

### 🟡 Warning

**[L5] — Comparator-backed ranges skip required initialization**

**Premises:** Comparator input is explicitly supported by `test/classes/range.js:41`. Matching uses the Range’s options to enforce the documented prerelease policy.

**Trace:**

1. At `classes/range.js:21–26`, `new Range(new Comparator('>=1.2.3'))` sets `raw` and `set`, then returns.
2. This skips initialization of `options`, `loose`, and `includePrerelease` at lines 29–31.
3. Testing `1.2.4-alpha` passes the numeric comparator, then reaches `testSet` at line 537 and reads `options.includePrerelease` from `undefined`.

Rebuttal check: the constructor’s supported Comparator route has no subsequent initialization; the exception occurs outside the string-parsing catch.

**Divergence:** **L5:** the early return leaves an incompletely initialized Range. Matching throws instead of returning a boolean.

**Trigger:** `new Range(new Comparator('>=1.2.3')).test('1.2.4-alpha')` should return `false`; it throws `TypeError`. With `{ includePrerelease: true }`, it should return `true` but also throws.

**Remedy:** Move these existing assignments from lines 29–31 to immediately before the Comparator branch at line 21:

```js
this.options = options
this.loose = !!options.loose
this.includePrerelease = !!options.includePrerelease
```

Dry-run: both prerelease expectations and stable-version controls passed in memory.

**Verification:** Reproduced on the actual implementation with Node.js v26.12.1.

---

**[L4] — Wildcard simplification deletes explicitly permitted prereleases**

**Premises:** README lines 174–176 define `||` as alternative comparator sets. Lines 187–190 permit prereleases explicitly named by a matching set. Thus `1.2.3-alpha` must satisfy `* || 1.2.3-alpha`.

**Trace:**

1. Parsing produces two sets: wildcard ANY and exact `1.2.3-alpha`.
2. At `classes/range.js:59–64`, encountering ANY replaces the entire set list with only the wildcard set.
3. `testSet`, lines 537–560, excludes `1.2.3-alpha` because the retained set contains no explicit prerelease comparator.

Rebuttal check: wildcard matching excludes prereleases by default; it therefore cannot subsume the deleted branch.

**Divergence:** **L4:** mutating `this.set` changes the documented OR semantics and rejects an explicitly permitted version.

**Trigger:** `satisfies('1.2.3-alpha', '* || 1.2.3-alpha')` returns `false`; expected `true`. The exact branch alone returns `true`.

**Remedy:** Replace the condition at line 59 with:

```js
} else if (this.set.length > 1 && (this.includePrerelease ||
  !this.set.some(cs => cs.some(c => c.semver !== Comparator.ANY &&
    c.semver.prerelease.length)))) {
```

This retains prerelease-bearing alternatives when wildcard matching cannot cover them. Dry-run: both OR orders, unrelated prerelease rejection, stable matches, and empty-OR formatting passed.

**Verification:** Reproduced on actual code; the in-memory remedy passed targeted checks and existing fixtures.

---

**[L3] — Build stripping accepts malformed strict ranges**

**Premises:** README lines 402–407 permit one build suffix containing dot-separated identifiers; `+` is not an identifier character. Lines 432–433 require strict Range parsing.

**Trace:**

1. `new Range('1.2.3+foo+bar')` reaches `parseRange`.
2. At `classes/range.js:102`, global `BUILDSTRIPRE` removes both `+foo` and `+bar`, leaving `1.2.3`.
3. The Comparator constructed at line 157 validates only that sanitized version. `validRange` consequently returns `1.2.3`, and `satisfies('1.2.3', input)` returns `true`.

Rebuttal check: direct `new Comparator('1.2.3+foo+bar')` rejects the original input; Range’s preprocessing bypasses that defense.

**Divergence:** **L3:** malformed metadata crosses the strict-parser boundary and becomes a valid matching range.

**Trigger:** `validRange('1.2.3+foo+bar')` should return `null`; observed `1.2.3`.

**Remedy:** Insert this guard at the beginning of `parseRange`, before stripping metadata:

```js
if (!this.options.loose) {
  for (const token of range.split(' ')) {
    const plus = token.indexOf('+')
    if (plus !== -1 &&
        !/^\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*$/.test(token.slice(plus))) {
      throw new TypeError('Invalid build metadata: ' + token)
    }
  }
}
```

Dry-run: malformed exact, caret, wildcard, and hyphen inputs were rejected; valid metadata controls passed.

**Verification:** Reproduced on actual code; remedy verified in memory.

---

**[L6] — Pairwise comparator intersection accepts empty stable intervals**

**Premises:** README lines 151–176 define ranges as sets of matching versions. Default matching excludes prereleases unless explicitly permitted. Consequently, `>1.0.0 <1.0.1` contains no matching version.

**Trace:**

1. At `classes/range.js:180`, `isSatisfiable` checks the comparator pair.
2. `classes/comparator.js:127–130` reports overlap because the upper endpoint `1.0.1` exceeds the lower endpoint `1.0.0`.
3. Neither that comparison nor subsequent checks establish an admissible version between those endpoints. Range intersection returns `true`.

Rebuttal check: both endpoints are excluded, no stable version lies between them, and the set permits no prereleases. The existing `minVersion` helper independently returns `null`.

**Divergence:** **L6:** Range treats pairwise bound compatibility as proof that a matching version exists, producing false intersection results.

**Trigger:** Both `intersects('>1.0.0 <1.0.1', '*')` and `intersects('>1.0.0', '<1.0.1')` return `true`; expected `false`.

**Remedy:** Insert this focused stable-only check inside the `rangeComparators` callback, immediately before its existing `return` at line 182:

```js
const all = [...thisComparators, ...rangeComparators]
if (!(options && options.includePrerelease) &&
    all.every(c => c.semver === Comparator.ANY ||
      !c.semver.prerelease.length)) {
  let min = new SemVer('0.0.0')
  for (const c of all) {
    if (c.semver === Comparator.ANY ||
        c.operator.startsWith('<')) continue
    let v = c.semver
    if (c.operator === '>') {
      const parts = [v.major, v.minor, v.patch]
      let i = 2
      while (i >= 0 && parts[i] === Number.MAX_SAFE_INTEGER) {
        parts[i--] = 0
      }
      if (i < 0) return false
      parts[i]++
      v = new SemVer(parts.join('.'))
    }
    if (v.compare(min) > 0) min = v
  }
  return all.every(c => c.test(min))
}
```

Dry-run: both failures passed, alongside inclusive endpoints, wider intervals, component carry, and all 54 existing intersection fixtures.

**Verification:** Reproduced on actual code; the focused remedy was verified in memory. Prerelease-bearing intersection cases require separate investigation.

## Summary

All four defects have concrete expected/observed consequences and executed reproductions. The first three remedies passed 379 existing fixture cases together; the intersection remedy was checked separately.

Verification used local modules and in-memory copies only. No dependencies were installed, files written, or service/integration tests run. An initial heredoc probe was blocked by the read-only shell; subsequent probes used `node -e`. Full test-runner execution and comprehensive prerelease-intersection coverage remain outside this review.