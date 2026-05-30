# Real-World Probes — second validation line

`content-evals` (`evals/content/v2/`) tests the skills on **small, constructed cases** with
known L1–L9 bugs and brittle string assertions. It is good for catching regressions, but it
systematically **underestimates** real detection ability and **does not test the two things
that matter most in real use**:

1. **Precision / false positives** — does the skill stay silent on *correct* code?
2. **Real, non-textbook bugs** — bugs that need cross-call state reasoning or failure-path
   tracing, not pattern matching.

Real-world probes are that second line. Each probe is a **real, self-contained code unit**
with a verified ground truth, in two versions:

- `buggy.*` — contains one real defect → logic-review should **DETECT** it.
- `fixed.*` — the defect removed → logic-review should be **SILENT** (no bug / `Divergence: None`).

The buggy/fixed pair is the key idea (mirrors a real bug-fix commit): a skill that "finds bugs"
by always reporting *something* fails the `fixed` half. Detection without precision is noise.

## Why this is NOT auto-scored

Real code is too varied for the brittle string assertions `grade-iteration.py` uses. The runner
surfaces two **signals** per probe and leaves the verdict to a human reading the outputs:

- `buggy`  → output carries a Critical/Warning finding (🔴 / ⚠️ / 🟡) → **DETECT** signal
- `fixed`  → output carries **no Critical/Warning** finding → **SILENT** signal

A 💡 Suggestion on the `fixed` side is acceptable and does **not** break SILENT: real code
always has improvable edges, and a strong reviewer surfaces them. Demanding absolute silence
sets an unrealistic bar and would punish the skill for being thorough. Only Critical/Warning
(a claimed real defect) on correct code counts as a false positive.

A green signal pair is necessary but not sufficient — read the actual `buggy` finding to confirm
it names the *real* defect (see each probe's `meta.json` → `expected_bug`), not an unrelated one.

## Layout

```
evals/real-world/
├── README.md
├── run-real-world.sh          # runner: claude -p logic-review on each buggy/fixed, signal check
├── probes/
│   └── <id>/
│       ├── meta.json          # source, language, expected_bug (ground truth), fixed_should_be_silent
│       ├── buggy.<ext>
│       └── fixed.<ext>
└── runs/                      # timestamped outputs (gitignored scratch; commit a summary if useful)
```

## Run

```bash
bash evals/real-world/run-real-world.sh            # all probes, costs API tokens (claude -p)
PROBES_FILTER=001 bash evals/real-world/run-real-world.sh   # one probe
```

## Adding a probe

1. Find a **self-contained, single-file/single-function** real defect (our own repo, a real
   open-source bug-fix commit, a CVE repro). Cross-file or huge cases don't fit logic-review's
   single-file scope — keep probes within it.
2. Create `probes/<id>/` with `buggy.<ext>`, `fixed.<ext>`, and `meta.json`.
3. Verify the ground truth yourself **before** running the skill — record it in `expected_bug`
   so the run is a fair test, not a post-hoc rationalization.
