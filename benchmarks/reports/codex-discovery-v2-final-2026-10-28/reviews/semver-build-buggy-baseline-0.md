<!-- run aa3c21c4c6d34d3684c5df8418aaceb6; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `classes/range.js`, supported by comparator/version implementations, public wrappers, README contracts, and range fixtures. Focus: construction, OR normalization, and intersection behavior. Other parsing boundaries were not exhaustively tested.  
**Logic Score:** 79/100

Three confirmed defects. The score describes confirmed findings in the inspected paths, not whole-project correctness.

## Findings

### 🟡 Warning — [L5] Comparator construction skips required initialization

**Premises:** `test/classes/range.js:41–45` establishes that constructing a `Range` from a `Comparator` is supported. README.md:418–430 documents options for classes, including `loose` and `includePrerelease`.

**Trace:**

1. `new Range(new Comparator('1.2.3-alpha'))` enters the Comparator branch at `classes/range.js:21`.
2. It assigns `raw` and `set`, then returns at line 26, skipping `options`, `loose`, and `includePrerelease` initialization.
3. `.test('1.2.3-alpha')` parses the version and successfully evaluates the equality comparator.
4. `testSet()` reaches line 530 and reads `options.includePrerelease`, but `options` is `undefined`.

Rebuttal check: `functions/satisfies.js` catches constructor failures only; this later exception escapes.

**Divergence:** **L5:** the early return skips initialization required by subsequent methods. A valid, matching prerelease throws instead of returning `true`. Explicit loose options are also ignored: a Comparator-derived range rejects `01.02.04`, while its string-derived equivalent accepts it.

**Trigger:**

```js
new Range(new Comparator('1.2.3-alpha')).test('1.2.3-alpha')
// Expected: true
// Observed: TypeError reading 'includePrerelease'
```

**Remedy:** In `classes/range.js`, move these existing assignments from lines 29–31 immediately before the Comparator branch at line 21:

```js
this.options = options
this.loose = !!options.loose
this.includePrerelease = !!options.includePrerelease
```

Dry-run: executed in memory; matching prereleases, loose parsing, explicit prerelease inclusion, and default prerelease exclusion behaved as expected.

**Verification:** Reproduced on the actual implementation using Node.js v26.12.1, including through public `satisfies()`.

### 🟡 Warning — [L4] Wildcard simplification discards accepted prereleases

**Premises:** README.md:174–176 defines `||` as accepting a version when any alternative accepts it. README.md:187–190 permits explicitly opted-in prereleases; lines 312–314 specify that default `*` accepts only releases.

**Trace:**

1. `new Range('* || 1.2.3-alpha')` initially produces a wildcard alternative and an exact prerelease alternative.
2. At `classes/range.js:61–64`, finding the wildcard replaces the entire set with that alternative alone.
3. `.test('1.2.3-alpha')` passes the wildcard comparator, but `testSet()` rejects it because the remaining set contains no prerelease opt-in.

Rebuttal check: the exact alternative alone accepts this version. Reversing the OR operands still loses it.

**Divergence:** **L4:** replacing the alternatives changes the accepted version set. Adding `*` makes an already accepted prerelease fail.

**Trigger:**

```js
new Range('1.2.3-alpha').test('1.2.3-alpha')      // true
new Range('* || 1.2.3-alpha').test('1.2.3-alpha') // false; expected true
```

`>=0.0.0 || 1.2.3-alpha` exhibits the same failure after normalization.

**Remedy:** Replace the condition at `classes/range.js:62` with:

```js
if (c.length === 1 && isAny(c[0]) &&
    (this.includePrerelease || !this.set.some(cs => cs.some(cmp =>
      !isAny(cmp) && cmp.semver.prerelease.length)))) {
```

This preserves alternatives containing prerelease opt-ins when default matching applies, while retaining wildcard collapse for the other cases. Dry-run: executed in memory; both operand orders, ordinary releases, and unrelated prerelease rejection passed.

**Verification:** Reproduced on the actual implementation.

### 🟡 Warning — [L6] Pairwise comparator intersections misrepresent range intersection

**Premises:** README.md:170–176 defines comparator sets as conjunctions. README.md:456–457 documents intersection of supplied ranges. Prerelease admission applies to the whole comparator set, not each comparator separately.

**Trace:**

1. Let `A = '>=1.2.3-alpha <1.2.3'` and `B = '1.2.3-beta'`. Both actual `Range.test()` calls accept `1.2.3-beta`, establishing a shared version.
2. `Range.intersects()` at `classes/range.js:175–183` delegates to individual `Comparator.intersects()` calls.
3. Comparing A’s `<1.2.3` comparator with B’s equality enters `classes/comparator.js:89–93`.
4. That callee creates an isolated `Range('<1.2.3')`. Its prerelease check rejects `1.2.3-beta`, having lost A’s `>=1.2.3-alpha` opt-in. The enclosing intersection returns `false`.

Rebuttal check: the reverse intersection also returns `false`; direct membership confirms the witness belongs to both original ranges.

**Divergence:** **L6:** the caller assumes comparator-level intersection establishes satisfiability under whole-set rules. It produces both false negatives and false positives:

| Inputs, default options | Expected | Observed |
|---|---:|---:|
| `>=1.2.3-alpha <1.2.3` and `1.2.3-beta` | `true` | `false` |
| `>1.2.3 <1.2.4` and `*` | `false` | `true` |
| `>=1.2.3-alpha <1.2.3` and `*` | `false` | `true` |

In the second case no release exists between consecutive patch versions, and prereleases are excluded. In the third, only A admits the possible prereleases.

**Trigger:** Call `require('./ranges/intersects')(a, b)` with the table’s strings.

**Remedy:** Replace `Range.intersects()` with a shared-witness check that evaluates each complete comparator set:

```js
intersects (range, options) {
  if (!(range instanceof Range)) throw new TypeError('a Range is required')
  options = parseOptions(options)
  const max = Number.MAX_SAFE_INTEGER
  return this.set.some(a => range.set.some(b => {
    const candidates = [new SemVer('0.0.0'), new SemVer('0.0.0-0')]
    for (const c of [...a, ...b]) {
      if (isAny(c)) continue
      const v = new SemVer(c.semver.version)
      const core = v.major + '.' + v.minor + '.' + v.patch
      candidates.push(v, new SemVer(core), new SemVer(core + '-0'))
      const next = new SemVer(v.version)
      if (next.prerelease.length) next.prerelease.push(0)
      else {
        if (next.patch < max) next.patch++
        else if (next.minor < max) { next.minor++; next.patch = 0 }
        else if (next.major < max) {
          next.major++; next.minor = next.patch = 0
        } else continue
        candidates.push(new SemVer(
          next.major + '.' + next.minor + '.' + next.patch))
        next.prerelease = [0]
      }
      next.format()
      candidates.push(next)
    }
    return candidates.some(v =>
      testSet(a, v, options) && testSet(b, v, options))
  }))
}
```

Dry-run: executed in memory against the reported cases, reversed operands, prerelease-enabled controls, empty-range boundaries, and numeric rollover.

**Verification:** Reproduced on the actual implementation through the public intersection wrapper. Remedy checks used an in-memory compiled replacement.

## Summary

The inspected code can throw during supported Comparator-derived matching, discard explicitly accepted prereleases, and incorrectly report range intersections.

All 433 selected existing fixture assertions passed on the original implementation. The final proposed remedies passed those assertions plus 31 targeted checks in memory. No files were modified, dependencies installed, external services accessed, or service/integration tests run. Full test-runner execution and exhaustive parsing-boundary coverage remain outside this review; no additional lead is presented as a confirmed defect.