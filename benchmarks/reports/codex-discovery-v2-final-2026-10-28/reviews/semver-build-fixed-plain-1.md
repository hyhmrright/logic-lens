<!-- run 640560f58f9b429f80c0816fd8e344b2; model gpt-6.1-sol; source links normalized only -->

Found four reproducible defects in `classes/range.js`. All findings below are confirmed by local Node probes.

1. **Wildcard OR simplification removes explicitly allowed prereleases.**  
   At [range.js:60](https://github.com/npm/node-semver/blob/17aa702d91166472b197a2ea768f085083bee2e4/classes/range.js#L60), any `*` branch causes every other branch to be discarded. However, `*` excludes prereleases by default, so it does not subsume an explicit prerelease branch.

   ```js
   new Range('1.2.3-alpha').test('1.2.3-alpha')       // true
   new Range('* || 1.2.3-alpha').test('1.2.3-alpha')  // false
   ```

   Expected: both return `true`, because either OR branch may satisfy the range. Observed: adding `*` removes a previously accepted version. Reversing the branches produces the same failure. This conflicts with the OR and prerelease rules documented in `README.md`.

2. **Constructing a Range from a Comparator leaves options uninitialized.**  
   The constructor returns at [range.js:21](https://github.com/npm/node-semver/blob/17aa702d91166472b197a2ea768f085083bee2e4/classes/range.js#L21), before assigning `this.options`, `this.loose`, and `this.includePrerelease`.

   ```js
   new Range(new Comparator('>=1.2.3-alpha'))
     .test('1.2.3-beta')
   // TypeError: Cannot read properties of undefined
   //            (reading 'includePrerelease')
   ```

   Expected: `true`, matching construction from the equivalent string. Observed: `testSet()` dereferences the missing options at line 537 and throws.

   Options also silently fail without a crash: constructing from `new Comparator('>=1.2.3')` with `{loose: true}` rejects `'01.03.00'`; constructing from the equivalent string with the same options accepts it.

3. **Build metadata stripping turns invalid ranges into accepted constraints.**  
   At [range.js:100](https://github.com/npm/node-semver/blob/17aa702d91166472b197a2ea768f085083bee2e4/classes/range.js#L100), the unanchored global `BUILDSTRIPRE` removes build-like substrings before validating their context. Its definition uses the build fragment from `internal/re.js`, which does not require an attached version.

   ```js
   validRange('+build')                     // '*'
   new Range('+build || 1.2.3').test('9.0.0') // true
   validRange('1.2.3+one+two')               // '1.2.3'
   ```

   Expected: strict parsing rejects these malformed inputs; `validRange()` returns `null`. The documented grammar requires build metadata to qualify a version and permits only one `+build` suffix. Observed: standalone metadata becomes an empty wildcard branch, and multiple suffixes are erased. Consequently, malformed input can broaden a constraint to every stable version.

4. **Intersection checks disagree with actual range membership.**  
   [range.js:178](https://github.com/npm/node-semver/blob/17aa702d91166472b197a2ea768f085083bee2e4/classes/range.js#L178) determines intersections through pairwise Comparator checks, which do not consistently preserve the prerelease rules of complete comparator sets.

   ```js
   const a = new Range('>=1.0.0 >=1.2.3-alpha')
   const b = new Range('1.2.3-alpha')

   a.test('1.2.3-alpha') // true
   b.test('1.2.3-alpha') // true
   a.intersects(b)      // false
   ```

   Expected: `true`, with `'1.2.3-alpha'` as a concrete shared version. Observed: `false` in both directions. The comparison against `>=1.0.0` separately rejects the prerelease despite the other comparator explicitly allowing it.

   There are also false positives: `new Range('>1.0.0 <1.0.1').intersects(new Range('*'))` returns `true`, although that first range accepts no versions under default prerelease rules. Wildcard/prerelease intersection is asymmetric too: `'*'` intersecting `'1.2.3-alpha'` returns `true`, while reversing them returns `false`. The wildcard shortcut in `Comparator.intersects()` contributes to that behavior.

Verification used seven tool calls. All 379 existing include, exclude, parse, and intersection fixture cases matched their expectations; 14 targeted assertions reproduced the defects and positive controls. I did not run the full test harness, service tests, or integration tests. No files were modified, dependencies installed, or external services accessed. No unverified leads are included.