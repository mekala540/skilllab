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

## First real batch: 35 skills on Claude Haiku 5.5

[obra/superpowers](https://github.com/obra/superpowers) and
[mattpocock/skills](https://github.com/mattpocock/skills), every skill that matches a task,
3 runs each with and without the skill: 234 runs, $2.97.

- **Pass rate:** 223/234. Every pair is "no lift", because the baseline already passes.
- **Trigger rate: 33 of 35 skills were never invoked**, even on tasks matching their own
  description. Only `mattpocock/skills/pr` (2/3) and `writing-for-agents` (1/3) were used.
  The skills were installed and their descriptions loaded (they add tokens to every session),
  but the agent didn't choose them.
- **Cost:** median cost per pass with a skill was 0.96× the baseline. Individual differences
  (0.4× to 1.45×) aren't significant at 3 runs.

The trigger result is the actionable one: a skill whose description doesn't make the agent
reach for it costs context and does nothing. It's worth retesting with other models and
longer tasks before telling any maintainer their skill is unused.
