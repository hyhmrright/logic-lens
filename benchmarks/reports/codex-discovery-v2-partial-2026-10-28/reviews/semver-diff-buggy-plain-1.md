<!-- run 9331ca9d1da24a4e9d8d4b0ff5a69aee; model gpt-6.1-sol; source links normalized only -->

Found one confirmed defect.

**[P2] Prerelease-to-stable comparisons can understate the release type** — [functions/diff.js:32](https://github.com/npm/node-semver/blob/753e02b9d0cb3ac23e085dc33efcab3e08d61f2b/functions/diff.js#L32)

When the lower version is a prerelease, the special branch chooses `patch` if the higher version’s patch is nonzero, otherwise `minor` if its minor is nonzero. It returns before checking whether the major or minor actually changed.

Probes of the actual implementation produced:

| Lower version | Higher version | Expected | Observed |
|---|---|---|---|
| `1.2.3-rc.1` | `2.0.1` | `major` | `patch` |
| `1.2.3-rc.1` | `2.1.0` | `major` | `minor` |
| `1.2.3-rc.1` | `1.3.1` | `minor` | `patch` |

All three also reproduce with arguments reversed. The expected results follow the documented release-type contract in [README.md:473](https://github.com/npm/node-semver/blob/753e02b9d0cb3ac23e085dc33efcab3e08d61f2b/README.md#L473) and the implementation’s major-before-minor-before-patch checks at [functions/diff.js:49](https://github.com/npm/node-semver/blob/753e02b9d0cb3ac23e085dc33efcab3e08d61f2b/functions/diff.js#L49). Removing the prerelease suffix from these inputs produces the expected classifications.

The concrete consequence is that consumers receive a patch/minor classification for a change crossing a major/minor boundary. The special handling should account for changed version components before classifying prerelease promotion.

The existing tests cover cross-component transitions to targets ending in zeros, but omit these cases with nonzero trailing components. The separate `1.0.0-pre → 1.1.1` result of `major` is explicitly tested; I have not counted that as a defect.

**Verification and limitations:** All 30 existing assertions passed using an in-memory adapter for the test file. Additional local probes checked the reported cases, argument reversal, prerelease-only changes, build-only equality, and invalid input. This was not a full TAP or integration run. No files were modified, dependencies installed, or external services accessed. No additional open leads are reported.