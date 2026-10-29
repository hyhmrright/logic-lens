# Logic-Lens v0.7.0 — Portable execution and reproducible evaluation

Reviews and evaluation infrastructure now run without a Claude account or runtime.
Codex is the tested default CLI. Other coding tools can consume portable Markdown
packs or implement the documented command-adapter protocol; native compatibility
with every coding tool is not claimed.

- Portable six-skill packs and a provider-neutral Python CLI (Python 3.11+).
- Command adapters, capability checks, execution isolation, bounded concurrency,
  normalized events and preserved failure evidence.
- Pinned real-code discovery comparisons with source/instruction hashes and human
  adjudication; improved conclusion gating in the legacy content grader.

Default skill content is unchanged from main before this release. Experimental
skills, property search and offline investigation prototypes remain outside this
release in draft PR #16. No new model evaluations were run for this release.

The completed revision-2 comparison found 9/12 targets in each arm. This release
makes no claim of better bug discovery than plain Codex. Historical Claude results
retain their original provenance and do not measure Codex performance.

Version history: v0.6.9 and v0.6.10 already have Git tags but no GitHub Release;
v0.6.8 was a benchmark label, not a shipped version. Those tags are unchanged.
v0.7.0 includes the intervening main changes; CHANGELOG.md records their history.
