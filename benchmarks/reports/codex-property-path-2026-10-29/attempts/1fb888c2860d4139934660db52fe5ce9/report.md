# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** [classes/range.js](/var/folders/kb/clk179sd5qq5htsth48gfk5c0000gn/T/logic-lens-run-rtiignqt/workspace/classes/range.js), supported by Comparator, SemVer, regex/cache helpers, range callers, README contracts, and targeted fixtures.  
**Logic Score:** 72/100

Seven concrete defects were reproduced. The score reflects confirmed findings in the inspected paths, not overall correctness.

## Findings

All target line references below refer to `classes/range.js`. Each finding is **Warning, high confidence**.

### 1. **[L5] — Comparator construction skips required initialization**

**Premises:** Comparator input is explicitly supported at lines 21–27 and by `test/classes/range.js:41`. Matching consumes `this.options`; README documents both `loose` and `includePrerelease`.

**Trace:** (1) Constructing from a Comparator enters line 21. (2) Line 26 returns before assigning options and flags at lines 29–31. (3) A matching prerelease reaches `testSet`, where line 530 reads `options.includePrerelease`. Rebuttal check: ordinary release matching succeeds, concealing the missing initialization.

**Divergence:** **L5:** The early return leaves `options` undefined. Prerelease matching throws instead of returning a boolean; loose version parsing also silently uses strict defaults.

**Trigger:** `new Range(new Comparator('>=1.2.3-alpha')).test('1.2.3-beta')` should return `true`; observed `TypeError: Cannot read properties of undefined (reading 'includePrerelease')`.

**Remedy:** Move the three assignments at lines 29–31 immediately after line 8, before either constructor shortcut. Dry-run: mentally checked initialization and ordinary string construction.

**Verification:** Execution-verified, including stable, prerelease, explicit opt-in, and loose controls.

### 2. **[L6] — Wildcard simplification discards explicit prerelease alternatives**

**Premises:** README “Ranges” defines `||` as union. Its prerelease contract permits versions explicitly named by a matching branch; default `*` excludes prereleases.

**Trace:** (1) Parsing creates wildcard and exact-prerelease sets. (2) Lines 60–65 replace both sets with the wildcard alone. (3) `testSet` rejects the prerelease because its admitting comparator disappeared. Rebuttal check: the exact branch alone succeeds; both branch orders fail after simplification.

**Divergence:** **L6:** The shortcut assumes wildcard membership contains every alternative, contradicting the membership consumer’s prerelease rules.

**Trigger:** `new Range('* || 1.2.3-alpha').test('1.2.3-alpha')` should return `true`; observed `false`.

**Remedy:** Change line 59 to:
```js
} else if (this.set.length > 1 && this.includePrerelease) {
```
This preserves alternatives under default prerelease filtering. Dry-run: mentally checked both branch orders and ordinary releases.

**Verification:** Execution-verified.

### 3. **[L3] — Removing the zero lower bound admits versions below it**

**Premises:** Whitespace-separated comparators form an intersection. `0.0.0-0` sorts below `0.0.0`; a comparator carrying that tuple’s prerelease can enable prerelease membership.

**Trace:** (1) Line 139 passes `>=0.0.0` through `replaceGTE0`. (2) Lines 478–482 erase it. (3) The remaining `<0.0.0-alpha` comparator admits `0.0.0-0`, including through the tuple check at lines 542–547. Rebuttal check: the original lower Comparator independently rejects that version.

**Divergence:** **L3:** Treating the stable minimum as unrestricted loses its boundary constraint when another comparator enables prereleases.

**Trigger:** `satisfies('0.0.0-0', '>=0.0.0 <0.0.0-alpha')` should return `false`; observed `true`.

**Remedy:** Replace line 139 with:
```js
.map(comp => this.includePrerelease
  ? replaceGTE0(comp, this.options) : comp)
```
Dry-run: mentally checked the exclusion and ordinary release matching; default formatting may retain a redundant comparator.

**Verification:** Execution-verified.

### 4. **[L2] — Loose caret bounds compare numeric zero as text**

**Premises:** Loose parsing accepts leading zeros. `SemVer` converts component strings to numbers at `classes/semver.js:45–48`. README caret rules constrain a zero-major range by its first nonzero component.

**Trace:** (1) Loose caret regex captures `"00"` as the major component. (2) `replaceCaret` compares it with the string `'0'`, yielding false. (3) Lines 374–376 select the nonzero-major branch, producing `<1.0.0-0`. Rebuttal check: canonical `^0.2.3` correctly produces `<0.3.0-0`.

**Divergence:** **L2:** Lexical comparison changes numeric caret semantics and admits incompatible versions.

**Trigger:** `satisfies('0.5.0', '^00.2.3', {loose:true})` should match canonical `^0.2.3` and return `false`; observed `true`. Padded minor zero also broadens `^0.00.3`.

**Remedy:** Within `replaceCaret`, replace every `M === '0'` with `+M === 0`, and every `m === '0'` with `+m === 0`. Dry-run: mentally checked padded and canonical components.

**Verification:** Execution-verified for padded major and minor cases.

### 5. **[L6] — Build stripping repairs malformed strict input**

**Premises:** README requires strict range parsing. The local build grammar permits one `+` followed by dot-separated identifiers; both SemVer and Comparator reject repeated build separators.

**Trace:** (1) `parseComparator` receives `1.2.3+foo+bar`. (2) Line 258 removes the unanchored `+foo` substring. (3) Comparator accepts the resulting `1.2.3+bar` and normalizes it to `1.2.3`. Rebuttal check: valid single-suffix metadata works normally.

**Divergence:** **L6:** Preprocessing supplies the validator with repaired input, allowing a malformed strict range to match versions.

**Trigger:** `satisfies('1.2.3', '1.2.3+foo+bar')` should reject the invalid range and return `false`; observed `true`.

**Remedy:** Before line 258, add:
```js
if (comp.split('+').length > 2) {
  throw new TypeError(`Invalid comparator: ${comp}`)
}
```
Dry-run: mentally checked repeated and single separators. This remedy addresses the demonstrated malformed-input family.

**Verification:** Execution-verified against both validator controls and the public caller.

### 6. **[L6] — Hyphen lower-bound metadata consumes the prerelease suffix**

**Premises:** Build metadata does not affect comparison, as implemented by SemVer’s normalized version and comparison methods. Hyphen expansion explicitly adds `-0` when including prereleases.

**Trace:** (1) `hyphenReplace` receives lower endpoint `1.2.3+build`. (2) Line 503 produces `>=1.2.3+build-0`, placing `-0` inside build metadata. (3) Subsequent stripping leaves `>=1.2.3`, excluding the intended lower-tuple prereleases. Rebuttal check: the otherwise identical build-free range includes them.

**Divergence:** **L6:** Build metadata unexpectedly changes range membership.

**Trigger:** With `{includePrerelease:true}`, testing `1.2.3-alpha` against `1.2.3+build - 2.3.4` returns `false`; the equivalent build-free range returns `true`.

**Remedy:** Replace line 503 with:
```js
from = `>=${fM}.${fm}.${fp}${incPr ? '-0' : ''}`
```
Dry-run: mentally checked the metadata-bearing and build-free lower endpoints.

**Verification:** Execution-verified.

### 7. **[L6] — Pairwise intersection assumes an available version between bounds**

**Premises:** Default matching excludes prereleases unless explicitly admitted. No release version exists strictly between `1.0.0` and `1.0.1`.

**Trace:** (1) Each single-comparator set passes `isSatisfiable`. (2) Line 183 calls `Comparator.intersects`. (3) That helper returns true because the lower endpoint compares below the upper endpoint, without establishing an admissible witness. Rebuttal check: `minVersion('>1.0.0 <1.0.1')` returns `null`; widening the upper bound to `<1.0.2` yields witness `1.0.1`.

**Divergence:** **L6:** `Range.intersects` reports overlap although no version satisfies both ranges.

**Trigger:** `new Range('>1.0.0').intersects(new Range('<1.0.1'))`: expected `false`, observed `true`.

**Remedy:** For the demonstrated stable-only case, insert before line 179:
```js
const comps = thisComparators.concat(rangeComparators)
if (!(options && options.includePrerelease) &&
    comps.every(c => c.semver === Comparator.ANY ||
      c.semver.prerelease.length === 0)) {
  return require('../ranges/min-version')(
    comps.map(c => c.value).join(' '), options) !== null
}
```
Dry-run: mentally checked the empty gap and widened control. This is a scoped correction; general prerelease intersection needs further work.

**Verification:** Execution-verified original defect; remedy unexecuted.

## Summary

All seven defects reproduced using the actual implementation on Node.js v26.13.0. The retained [probe](/private/var/folders/kb/clk179sd5qq5htsth48gfk5c0000gn/T/logic-lens-run-rtiignqt/harness/range-review.cjs) and [results](/private/var/folders/kb/clk179sd5qq5htsth48gfk5c0000gn/T/logic-lens-run-rtiignqt/harness/range-review-results.txt) contain controls alongside the failures.

Ten tool calls were used. Source files were unchanged; no dependencies, external services, or integration tests were used. Remedies were reasoned through only, without regression verification.

## Unresolved Investigations

Prerelease-aware intersection behavior and a complete intersection remedy remain open. Exhaustive grammar, maximum-component arithmetic, and mutable-cache ownership contracts were not established within the budget; they are not additional findings.