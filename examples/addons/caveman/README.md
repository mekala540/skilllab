# caveman

- **Repo:** https://github.com/JuliusBrussee/caveman
- **Followed:** release `v4.0.1` (commit `d262ab3`, 13 October 2026): `README.md` ("Install", "Say less", "Other ways in") and the plugin manifest `.claude-plugin/plugin.json`.
- **Claims:** "cuts 65% of tokens by talking like a caveman" (repo description). The README is more careful: on ten questions, `/caveman` cut output tokens 3% more than a plain "Answer concisely." (35% for `/ultracave`), the rules cost about 1,160 input tokens, and JetBrains measured 8.5% fewer output tokens on 86 real coding tasks.

## Fetch the plugin first

The plugin is the whole repo at the release tag. It isn't committed here (`plugin/` is gitignored):

```bash
git clone --depth 1 --branch v4.0.1 https://github.com/JuliusBrussee/caveman examples/addons/caveman/plugin
```

Its hooks need Node.js and use only Node's built-in modules, so there is no `npm install`.

## How it installs, and what this add-on tests

caveman 4.0 has six parts ("rocks"). The main install, `npx @caveman-ai/cli@latest`, sets up every agent on your machine, runs a local proxy for "Read less", and its "Auto" model routing needs an account. skilllab can't reproduce that per workspace, so it's **not** what this add-on tests.

This add-on tests the documented Claude Code plugin install:

```bash
claude plugin marketplace add JuliusBrussee/caveman && claude plugin install caveman@caveman
```

Here it's loaded with `--plugin-dir plugin` instead, so it's on for the add-on arm only.

**`env: CAVEMAN_DEFAULT_MODE=caveman`.** skilllab runs Claude Code headless (`claude -p`). caveman's `INSTALL.md` says scripted runs "start with caveman off whatever that file says" unless `CAVEMAN_DEFAULT_MODE` is set (`caveman`, `ultracave`, `megacave` or `off`). An interactive user gets the voice by default, so the add-on sets `caveman` to match. Without it, the plugin loads but stays silent. Hooks are included, as skilllab's rules require for packs that ship as plugins. From `plugin.json`:

| Hook | Runs |
| --- | --- |
| `SessionStart` | `src/hooks/caveman-activate.js`: turns caveman mode on for the session |
| `UserPromptSubmit` | `src/hooks/caveman-mode-tracker.js`: tracks mode switches |
| `SubagentStart` | `caveman-activate.js --subagent` |
| `SessionEnd` | `src/hooks/caveman-stats.js --record` |

The plugin also brings its skills (`caveman`, `ultracave`, `megacave`, `caveman-review` and others), whose names and descriptions add up-front tokens to every session.

## Pilot 2: the plugin with its voice off

In skilllab pilot 2 (17 October 2026, Haiku 5.5, `fix-pagination`, 5 runs per arm) this add-on had no `env` line, so caveman's mode was `off` in every session. The plugin alone, with its skills and hooks loaded and no shorter replies, cost **+18%** [2 to 25] vs the baseline (input tokens +20%). That's the overhead a headless user pays if the voice never switches on, not a measure of the voice.

## Is it a fair test here?

Yes. The voice changes what the agent writes, so skilllab's Bash allowlist doesn't limit it, and skilllab measures output tokens and cost directly. The tasks are small, so the ~1,160-token rule cost is a large share of each run. That's part of what a real user pays, so it's fair to count.

## Side effects on your machine

The hooks write state into `~/.claude` (or `$CLAUDE_CONFIG_DIR`):

| Path | Written when | Source |
| --- | --- | --- |
| `.caveman-sessions/` (folder, one `<session-id>.mode` file per session) | every session, even with the mode off | seen in pilot 2; `caveman-config.js` |
| `.caveman-active` | mode on (a mirror of the current mode) | `caveman-config.js` `legacyFlagPath` |
| `.caveman-mode-log.jsonl` | mode on (one line per mode change) | `caveman-config.js` `recordModeChange` |
| `.caveman-nudge-shown` | mode on, once | `caveman-activate.js` |
| `.caveman-history.jsonl`, `.caveman-statusline-suffix` | session end (`--record`) | `caveman-stats.js` |

Only `.caveman-sessions/` has been seen in a real batch so far; the rest come from reading the hook code. Parallel runs share these files. The fake agent doesn't run hooks, so free tests leave nothing behind.

**After each real batch**, remove them (`-r`, because `.caveman-sessions` is a folder), so the next batch starts clean and your own sessions don't pick up a leftover caveman mode:

```bash
rm -rf "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/.caveman-*
```
