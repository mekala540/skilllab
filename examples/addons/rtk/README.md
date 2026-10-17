# rtk (Rust Token Killer)

- **Repo:** https://github.com/rtk-ai/rtk
- **Followed:** release `v1.0.1` (commit `4ef8730`, 14 October 2026): `INSTALL.md`, `README.md`, `docs/guide/pipelines/reference-pipelines.md`, and the hook entry written by `src/hooks/init/mod.rs`.
- **Claims:** "reduces LLM token consumption by 60-90% on common dev commands" (repo description); "up to 90% smaller" bash output (README). Its own `INSTALL.md` adds that this is a cut in bash output bytes, not in the whole bill.

## How it installs

```bash
brew install rtk          # macOS / Linux (README)
rtk gain                  # must show the savings dashboard; a different "rtk" exists on crates.io
rtk init -g               # patches ~/.claude/settings.json, adds ~/.claude/RTK.md
```

`rtk init -g` registers one hook in `~/.claude/settings.json`. With the default pipeline (`rtk:default`) that is `PreToolUse` on `Bash`, running `rtk hook claude`. It rewrites a command like `ls .` to `rtk ls .` before it runs. `PostToolUse` compression is opt-in (`rtk:posthook`) and not part of this add-on.

## How this add-on maps it

| Install step | Here |
| --- | --- |
| PreToolUse hook in `~/.claude/settings.json` | `settings.json`, passed per run with `--settings`, so your global settings are untouched |
| `~/.claude/RTK.md` awareness file (~10 tokens) | Left out. This matches the documented `rtk init -g --hook-only` mode |
| Rewritten commands run as `rtk …` | `"tools": ["Bash(rtk:*)"]` so the rewritten command is allowed |
| rtk's own permission check | `setup` writes allow rules into the workspace's `.claude/settings.json` (see Permissions below) |

## Is it a fair test here?

Partly. skilllab only lets the agent run `python3`, `ls` and `cat` in Bash. rtk rewrites `ls` (to `rtk ls`) and `cat` (to `rtk read`), so it does act on some commands. It has no rule for `python3`, and it never touches the `Read`, `Grep` and `Glob` tools, which the agent uses most here. rtk's biggest claimed wins (git, test runners, package managers) can't show up in this sandbox. Expect a small effect at most.

## Permissions: why `setup` writes `.claude/settings.json`

rtk only auto-allows a rewritten command when an allow rule matches the **original** command. It reads those rules from `<project>/.claude/settings.json` (and `.local`) and `~/.claude/settings.json`, found by walking up from the working directory (`src/hooks/permissions.rs`, `src/core/user_dirs.rs`). It never reads the file skilllab passes with `--settings`, or the `--allowedTools` list. So the allow rules can't go in this folder's `settings.json`.

Instead, `setup` writes them into each workspace's own `.claude/settings.json`:

```json
{"permissions": {"allow": ["Bash(ls:*)", "Bash(cat:*)", "Bash(rtk:*)"]}}
```

These match what skilllab's allowlist already permits, so the add-on arm gets no extra powers. rtk accepts the `Bash(ls:*)` form (it treats `:*` like ` *`).

Checked against rtk 1.0.1's real hook (`rtk hook claude`, fed a PreToolUse payload):

| Workspace | `ls .` | `cat pager.py` | `python3 test.py` |
| --- | --- | --- | --- |
| With these rules | rewritten to `rtk ls .`, `permissionDecision: "allow"` | rewritten to `rtk read pager.py`, `allow` | not rewritten |
| Without | rewritten, no decision: Claude Code then checks `rtk ls .` against its own allowlist | same | not rewritten |

Without the rules it would probably still work, since `tools` allows `Bash(rtk:*)`. With them, the result doesn't depend on how Claude Code treats a hook's rewritten command.

## Results so far

Pilot 3 (17 October 2026): `skilllab compare` with rtk, Headroom, caveman and the no-op control arm, `--task fix-pagination --repeats 5 --model claude-haiku-5-5`. 30 runs, all passed, 0 infrastructure errors, $0.18. The control arm came out *same cost* (+2% [-14 to 22]), so the batch shows no bias. One easy task (`fix-pagination`), Haiku 5.5 only, 5 repeats per arm, so read these as a first look, not a verdict on the tool.

| Verdict | Cost | Input tokens | Output tokens | Shell commands (median, with vs without) |
| --- | --- | --- | --- | --- |
| same cost | -16% [-20 to 0] | -31% | -21% | 2 vs 3, `python3` only |

The rtk arm ran only `python3`, which rtk doesn't rewrite, so rtk had nothing to act on. The -16% is noise (its range reaches 0).
