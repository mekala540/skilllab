# Calibration: October 2026

How often each standard task passes **without any skill**, 3 runs per task. A task can only
show a skill's lift if the baseline sometimes fails it.

| Task | Claude Sonnet 5.5 | Claude Haiku 5.5 |
| --- | --- | --- |
| debug-ledger | 3/3 | 3/3 |
| tests-ratelimiter | 2/3 | 3/3 |
| refactor-pricing | 3/3 | 3/3 |
| feature-cron | 3/3 | 3/3 |
| git-regression | 3/3 | 3/3 |
| js-lru-cache | 3/3 | 3/3 |
| 6 held-out tasks | 17/18 | 18/18 |

Median cost per run: about $0.12 on Sonnet 5.5 and $0.01 on Haiku 5.5.

## What this means

Current models, including the small one, reliably solve short, well-specified coding tasks,
even ones with several root causes, subtle specs or decoys. On tasks like these **a skill
cannot raise the pass rate; there's no headroom.** What a batch can still measure:

- **Trigger rate:** whether the agent uses a skill at all when the task matches its claim.
- **Cost and turns:** whether a skill makes the same result cheaper or more expensive.

To measure pass-rate lift, tasks need to be longer and messier: larger codebases, vague
requirements, multi-hour work. That's the main open direction; see CONTRIBUTING.md.

## Harness lessons (fixed)

- An allowlist of simple commands silently denies loops and chains. Agents then gave up on
  git work. skilllab now tells the agent the rules up front (both arms alike).
- Claude Code protects `.claude/`; writes there are denied in headless mode. Tasks write
  elsewhere (e.g. `claude-settings.json`) and say where it will be installed.
- Runs that fail before reaching the API (usage limit, logged out) are infrastructure errors:
  excluded, retried on resume, and 8 in a row stop the batch.

## First real batch (corrected)

> **Limits of these results.** Skills were tested only on **Claude Haiku 5.5**, the smallest current model. Sonnet 5.5 was used only to measure how hard the tasks are, and Opus wasn't tested. Larger models may use skills differently. The tasks are **short sample tasks** from this repo's suite, not real project work: a few files, a clear prompt and a fixed check. Real use (your codebase, vague requirements, long multi-step work) may give different results. Treat these numbers as an early signal, not a rating of any skill.

[obra/superpowers](https://github.com/obra/superpowers) and
[mattpocock/skills](https://github.com/mattpocock/skills) on Claude Haiku 5.5, public tasks,
3 runs per pair. Results: `skill` mode 42 runs ($0.56), `--pack` mode for superpowers on 4 tasks
12 more runs ($0.16).

| | Result |
| --- | --- |
| Skills found | 53 (23 can only be started by a person) |
| Keyword candidates | 48 pairs; the relevance check kept 10 and turned down 38 |
| Fairly tested | 8 skills (7 auto-pickable, 1 started with `/implement`) |
| Untested | 45: no fair task in this suite, so unknown |
| Single skill installed | 0 of 27 runs used the relevant skill |
| superpowers as a plugin | skills used in 7 of 12 runs: `systematic-debugging` 3/3 and 2/3 on the two debugging tasks, `test-driven-development` 2/3 on feature-cron, nothing on refactor-pricing |
| Pass rate | 100% with and without, every pair (ceiling) |
| Cost per pass | single skills 0.88–1.34× baseline; the plugin 1.09–1.31× (about 29% more input tokens) |

What this shows: how a pack is installed decides whether its skills get used. superpowers'
startup hook tells the agent to check its skills first, and with it the agent does. Testing one
skill alone, without the pack's hook, says little about a pack built to work as a whole.

What it doesn't show: whether any skill raises the pass rate. These tasks are too easy for that.

### Correction

The first version of this batch reported "33 of 35 skills never triggered, even on tasks
matching their own description". That was wrong, for three reasons:

1. Matching on one shared word paired skills with unrelated tasks (a skill that installs git
   hooks with a task about finding a regression). Not using those was correct behavior.
2. 9 of the counted skills set `disable-model-invocation: true`: only a person can start them,
   so a 0% trigger rate was guaranteed.
3. superpowers was tested without the startup hook it ships with.

skilllab now judges each candidate pair before running it (`matches.json`), starts user-only
skills with `/name`, and has `--pack` to load plugins with their hooks.
