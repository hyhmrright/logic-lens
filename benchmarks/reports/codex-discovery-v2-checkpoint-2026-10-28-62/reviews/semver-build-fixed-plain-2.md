<!-- run 02b7c60a6073421896461f8deb3caab6; model gpt-6.1-sol; source links normalized only -->

Found five confirmed defects. Examples below use default options.

1. **[P2] Comparator-backed ranges throw during prerelease checks** — [classes/range.js:21](https://github.com/npm/node-semver/blob/17aa702d91166472b197a2ea768f085083bee2e4/classes/range.js#L21)

   The constructor returns before initializing `this.options`, `this.loose`, and `this.includePrerelease`.

   ```js
   new Range(new Comparator('>=1.2.3-alpha')).test('1.2.3-beta')
   ```

   Expected: `true`, matching the equivalent string-backed range. Observed: `TypeError: Cannot read properties of undefined (reading 'includePrerelease')` in `testSet`. Passing `{ includePrerelease: true }` also leaves options uninitialized. The exception propagates through `satisfies()` because it catches construction errors only.

2. **[P2] Build-metadata stripping turns malformed input into valid ranges** — [classes/range.js:102](https://github.com/npm/node-semver/blob/17aa702d91166472b197a2ea768f085083bee2e4/classes/range.js#L102)

   `BUILDSTRIPRE` removes matching substrings globally before validating the range. It therefore erases evidence of invalid syntax:

   ```js
   validRange('1.2.3+foo+bar') // observed: '1.2.3'
   validRange('+foo')        // observed: '*'
   satisfies('9.9.9', '+foo') // observed: true
   ```

   Expected: strict construction rejects these inputs, and `validRange()` returns `null`. The supplied grammar permits one build suffix attached to a version; both `SemVer` and `Comparator` reject these examples. Consequence: malformed constraints pass validation, and a standalone metadata fragment becomes an unrestricted stable-version range.

3. **[P2] Wildcard OR simplification discards explicitly allowed prereleases** — [classes/range.js:60](https://github.com/npm/node-semver/blob/17aa702d91166472b197a2ea768f085083bee2e4/classes/range.js#L60)

   Whenever an OR branch contains only `*`, the constructor discards all other branches.

   ```js
   new Range('1.2.3-alpha').test('1.2.3-alpha')      // true
   new Range('* || 1.2.3-alpha').test('1.2.3-alpha') // false
   ```

   Expected: both return `true`, since the explicit equality branch matches. Observed: the combined range normalizes to the empty wildcard representation and rejects the prerelease. Reversing branch order produces the same failure. Under default prerelease rules, `*` does not subsume a branch that explicitly admits prereleases.

4. **[P2] Removing `>=0.0.0` can admit versions below that bound** — [classes/range.js:141](https://github.com/npm/node-semver/blob/17aa702d91166472b197a2ea768f085083bee2e4/classes/range.js#L141)

   ```js
   new Range('>=0.0.0 <=0.0.0-alpha').test('0.0.0-alpha')
   ```

   Expected: `false`; the version is below `0.0.0`, and the two bounds are contradictory. Observed: `true`.

   `replaceGTE0` removes the lower bound, leaving `<=0.0.0-alpha`. That remaining comparator explicitly permits prereleases for the `0.0.0` tuple. A direct `Comparator('>=0.0.0').test('0.0.0-alpha')` returns `false`, confirming that normalization changes membership.

5. **[P2] Intersection checks report nonexistent overlap and can be asymmetric** — [classes/range.js:178](https://github.com/npm/node-semver/blob/17aa702d91166472b197a2ea768f085083bee2e4/classes/range.js#L178)

   ```js
   const a = new Range('*')
   const b = new Range('1.2.3-alpha')
   a.intersects(b) // observed: true
   b.intersects(a) // observed: false
   ```

   Expected: both return `false`. The exact range permits only `1.2.3-alpha`, which `a.test()` rejects.

   Also reproduced:

   ```js
   new Range('>1.0.0').intersects(new Range('<1.0.1')) // true
   ```

   Expected: `false`; no stable version lies strictly between those releases, and neither range admits prereleases. `Range.intersects` and `isSatisfiable` rely on pairwise comparator checks without establishing a common admissible version. Supporting behavior in `Comparator.intersects` explains the wildcard asymmetry and the interval false positive.

Verification used local Node execution of the actual implementation. All five defects were reproduced with assertions. Direct evaluation of 379 existing fixture rows passed, including both intersection directions; those fixtures do not cover these cases.

Used nine shell calls. No files were modified, dependencies installed, external services accessed, or service/integration tests run. The full test runner was not executed. No additional unverified leads are reported.