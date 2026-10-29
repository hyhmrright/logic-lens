# Tool compatibility and adapter protocol

Logic-Lens is Markdown reasoning instructions plus optional Python orchestration.
It does not require Claude, a vendor SDK, or a plugin marketplace. A tool can use
one of three integration levels; do not confuse packaging with tested execution.

| Level | Interface | What is established |
|---|---|---|
| Portable instructions | `logic_lens.py bundle --pack` or a compiled prompt | All six skills and shared references are exported; usable wherever Markdown/code context can be supplied |
| Codex CLI | `--provider codex` (default) | Local CLI authentication, JSONL events, isolated work/home directories, read-only execution, token telemetry |
| Other coding CLIs | `--provider command --adapter adapter.json` | Tested adapter protocol; the selected host's flags, authentication, isolation and capabilities must be configured and verified |

Codex, Cursor, GitHub Copilot, Gemini CLI, Aider, OpenCode, Windsurf and similar
assistants may consume the portable Markdown pack through their context/rules/skill
mechanisms. This does **not** claim native integration or working automation has
been tested for each product/version. Tools without CLI automation still get the
same skills through the pack. Native plugin metadata for previously supported
hosts is retained as optional compatibility packaging.

## Portable pack (no account or runtime dependency)

```bash
python3 scripts/logic_lens.py bundle --pack --out /tmp/logic-lens-pack
python3 scripts/logic_lens.py bundle --skill review --out /tmp/logic-review.md
```

The directory contains a `LOGIC-LENS.md` router, all `skills/` guides, compiled
`prompts/logic-*.md` and the license. Add the router/directory as context if your
assistant can read files; otherwise attach the corresponding compiled prompt with
the code. Prompt compilation includes the active guide and shared framework once;
health also includes review, and fix-all includes its invoked skills. Export refuses
to overwrite an existing destination. Put only the requested skill in active context.
The pack can be copied to another machine/editor; no host-specific paths are embedded.

## Codex execution

The runner uses the documented non-interactive interface:
[Codex automation](https://learn.chatgpt.com/docs/non-interactive-mode).
It selects `codex exec --json --ephemeral --ignore-user-config --ignore-rules`, a
read-only sandbox, no web search, and a temporary CODEX_HOME containing an auth
symlink only. The original user config, saved skills, project ancestors and plugin
cache are not used. Auth is never printed, copied into artifacts, or modified by
Logic-Lens. Commands and terminal token usage come from actual CLI events.

A temporary source copy separates review from the user's checkout. Git workspaces
copy tracked and non-ignored untracked files, preserving uncommitted contents;
exported snapshots copy regular source files. Native agent instruction files are
removed from the review copy so they cannot vary the experimental arm. No file
changes in the review copy are accepted. Read-only filesystem policy is **not** a
hermetic container or guaranteed restriction to workspace reads; the prompt forbids
outside reads and logs enable auditing. A stricter host/filesystem isolation layer
is required for adversarial repositories or stronger non-leakage claims.

Codex has no per-call dollar-limit flag in this runner. Budget by selected cases,
`--limit`, bounded concurrency and timeout; record token counts. Dollar cost is
`null` when the CLI does not report it, not an invented estimate. The discovery
plan's old `budget_usd` field is legacy metadata, not an enforced Codex spend cap.

## Any other CLI: normalized JSONL

Create an adapter JSON containing an argv array (never a shell command string):

```json
{"argv":["/absolute/path/to/my-review-wrapper","--model","{model}","--effort","{effort}"]}
```

`{model}`, `{effort}`, and `{workspace}` substitutions are literal argv replacements.
The runner sets cwd to an isolated source copy and passes the same complete request
and skill snapshot via stdin. Your wrapper handles authentication and host-specific
flags, then emits exactly one terminal event:

```json
{"type":"result","status":"success","report":"Review text","usage":null,"cost_usd":null,"tools_used":[]}
```

On failure, exit nonzero or emit a non-success status; no empty report or bare text
is accepted as a completed review. Tools and usage reported by this interface are
**adapter-reported**, not independently inferred from report words.

For a CLI that reads stdin and writes only its final report to stdout, the bundled
bridge can normalize a successful process exit:

```json
{"argv":["python3","/absolute/path/to/scripts/command_bridge.py","--","my-coding-cli","its-documented-stdin-mode","--model","{model}"]}
```

Use your tool's actual documented options. The bridge does not invent flags,
claim native tool telemetry, or enforce the other host's sandbox. It records unknown
usage/cost as null. A provider adapter must enforce its own no-write/network/context
policy before being used for a comparable experiment.

```bash
python3 scripts/logic_lens.py review --provider command --adapter /path/adapter.json \
  --model your-model --workspace /path/repo --prompt /path/request.txt --out /tmp/review
```

## Evaluation semantics

Compare plain/prior-skill/candidate on the **same** host, model, tools, effort,
source snapshots and limits. Cross-provider differences are separate experiments.
Explicit snapshots test the instructions; native skill discovery needs its own
activation test. Description-routing tests are not activation tests.

The read-only review CLI supports review/explain/diff/locate/health. It refuses
fix-all because it cannot perform the requested edits under that policy. The fix-all
skill itself is included in portable packs for authorized write-capable hosts; no
host capability or user consent is supplied merely by exporting it.
