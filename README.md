# skilllab

**Does this agent skill actually help? Run it and see.**

[![The lab view replaying a real batch](https://mekala540.github.io/skilllab/lab.gif)](https://mekala540.github.io/skilllab/)

**[Watch the replay](https://mekala540.github.io/skilllab/)** of a real batch (Claude Haiku 5.5 only, short sample tasks, not real project work) · [full report](https://mekala540.github.io/skilllab/report.html)

Skill packs for Claude Code collect hundreds of thousands of stars. Stars measure popularity, and a static scan ([skillprint](https://github.com/mekala540/skillprint)) measures cost. Neither tells you whether the agent does better work with the skill installed.

skilllab answers that the way a lab would:

1. **Collect** skills from folders or git repos (every `SKILL.md`).
2. **Match** each skill's claim (its description) to tasks in a fixed suite, keeping only pairs where the task is a fair test of the skill.
3. **Run** every task without skills (baseline) and with each matching skill, several times, in parallel, each in a fresh throwaway workspace.
4. **Check** results with hidden tests that are copied in only after the agent finishes. No AI grading.
5. **Judge** each skill: `helps`, `no lift`, `hurts`, `mixed` or `flagged`.
6. **Measure cost**: median cost, input and output tokens, time and turns per run, with and without, with a 90% range. A skill or add-on that makes the agent cheaper at the same pass rate shows up even when both arms always pass.
7. **Report gaps**: skills that cost context without helping, skills the agent never triggers, tasks nobody solves, claims no task tests, and look-alike skills across repos.

It measures more than skills. **Add-ons** (token savers, memory tools, prompt styles, proxies) are anything described by an `addon.json`; `skilllab compare` runs them side by side on the same tasks.

## Install

```bash
git clone <this repo> && cd skilllab
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

No dependencies. Python 3.9+. Running real batches needs [Claude Code](https://claude.com/claude-code) logged in (`claude` on your PATH or in `~/.local/bin`).

## Use

```bash
skilllab skills https://github.com/obra/superpowers          # what's there, what each skill is tested on
skilllab plan   https://github.com/obra/superpowers          # which pairs are fair tests, how many runs (≈1 cent)
skilllab calibrate --repeats 3 --budget 5                    # how hard each task is for your model
skilllab run    https://github.com/obra/superpowers \
    --task fix-pagination --repeats 3 --budget 3 --out results/superpowers
skilllab run ... --pack                                      # test each repo as a whole pack (plugin + hooks)
skilllab run ... --watch                                     # live lab view in your browser while it runs
skilllab watch results/superpowers                           # live view of a batch running elsewhere
skilllab report results/superpowers                          # rebuild report.md / report.html / lab.html
skilllab new-task my-task                                    # scaffold a new task
skilllab suggest https://github.com/obra/superpowers --out drafts   # draft tasks for untested skills
```

Start small. One task, a few skills, `--repeats 3`, then grow. Every run is a full agent session and costs real money; `--budget` (default $5) stops new runs once spend reaches it, and rerunning the same command resumes where it left off.

Useful options for `run`: `--skill NAME` (repeatable), `--limit-skills N`, `--model`, `--workers` (agents running at once, default 4), `--run-budget` (USD cap per session), `--keep` (keep workspaces to inspect), `--pair SKILL:TASK` (run this pair whatever the relevance check says), `--no-judge` (count every keyword match), `--all-tasks` (test every skill on every task).

## Measure add-ons (token savers, memory, prompt styles)

Token savers claim 60–95% fewer tokens. Each one measures itself, on its own examples. `compare` runs each add-on and a plain baseline on the same tasks and reports cost, tokens and pass rate side by side:

```bash
skilllab compare examples/addons/terse path/to/other-addon --repeats 5 --budget 10 --out results/savers
```

An add-on is a folder with an `addon.json`. Every field except `name` is optional:

```json
{
  "name": "my-saver",
  "description": "What it claims to do",
  "settings": "settings.json",
  "plugin_dir": "plugin",
  "skills_dir": "skills",
  "claude_md": "CLAUDE.md",
  "append_system_prompt": "Be brief.",
  "env": {"ANTHROPIC_BASE_URL": "http://127.0.0.1:8787"},
  "tools": ["Bash(my-saver:*)"],
  "setup": ["my-saver init --local"],
  "requires": ["my-saver"]
}
```

- `settings` is passed with `claude --settings` (hooks and other settings; a file, or an inline object). `plugin_dir` loads with `--plugin-dir`. `skills_dir` subfolders go to `.claude/skills/`, `claude_md` to the workspace's `CLAUDE.md`.
- `env` is set for the agent only: point `ANTHROPIC_BASE_URL` at a local proxy, for example. Start the proxy yourself before the batch.
- `tools` adds to the allowlist (a command rewriter needs its own command allowed). `setup` runs in each fresh workspace before the agent starts; if it fails, the run is an infrastructure error and is retried on resume. `requires` stops the batch early if a program is missing.
- Settings, hooks, setup commands and proxies run code on your machine. Read an add-on's install steps before you write its `addon.json`.

The result, per add-on and per task:

| Verdict | Means |
| --- | --- |
| `cheaper` | The whole 90% range of the cost change is below zero, and the pass rate dropped by no more than 15 pts |
| `cheaper, fewer passes` | Cheaper, but the pass rate dropped by more than 15 pts. A saving that breaks work isn't a saving |
| `costlier` | The whole range is above zero |
| `same cost` | The range includes zero: no difference this sample can show |

Below 5 valid runs per arm there is no verdict, only the numbers: a range from 3 runs is far too narrow to trust. Pass-rate verdicts (`helps`, `no lift`, …) are reported too, the same way as for skills.

**Checks on the method itself.** Every `compare` batch also runs a **control** add-on that changes nothing. It should come out `same cost`; if it doesn't, the report warns that cost differences in that batch are bias, not savings. Each arm also gets one discarded warm-up run per task, and the measured runs are interleaved (every arm once per repeat, shuffled), so no arm benefits from a prompt cache another arm filled. `--no-control` and `--no-warmup` turn these off. Both exist because a pilot without them rated an add-on that never loaded as 24% cheaper.

## The lab view

Every `run` and `report` also writes `lab.html`: an animated replay of the batch, in the style of the "Paper Lab" demo.

- **The ring** revolves with one tick per skill. Color = verdict, length = tokens on use. Faint chords connect skills tested on the same task.
- **The wave**: each run streams from its skill on the ring (or from the centre, for baselines) to one of 12 agent lanes, then lands green (pass) or red (fail).
- **Panels**: live run feed, lift by task (best skill vs baseline), verdicts and gaps. Hover a tick for details.

It's one self-contained file with no network calls. Open it in a browser. `lab.html#t=20` starts 20 seconds in. With `run --watch` or `skilllab watch <folder>`, it's served on localhost and picks up new runs every few seconds while the batch is going. Retried runs count once.

To preview it without spending anything, run a batch with the fake agent in demo mode. Its outcomes are random, so never publish them:

```bash
FAKE_AGENT_MODE=demo skilllab run https://github.com/obra/superpowers --yes --out results/demo \
    --agent-cmd "python3 tests/fake_agent.py {prompt_file}"
```

Each run happens in a throwaway workspace, so skilllab turns relative file paths in `--agent-cmd` into absolute ones first. Run it from the repo root and `tests/fake_agent.py` resolves.

## First results

> **Limits of these results.** Skills were tested only on **Claude Haiku 5.5**, the smallest current model. Sonnet 5.5 was used only to measure how hard the tasks are, and Opus wasn't tested. Larger models may use skills differently. The tasks are **short sample tasks** from this repo's suite, not real project work: a few files, a clear prompt and a fixed check. Real use (your codebase, vague requirements, long multi-step work) may give different results. Treat these numbers as an early signal, not a rating of any skill.

Claude Haiku 5.5, obra/superpowers and mattpocock/skills, public tasks, 3 runs per pair ($0.72):

- **Coverage is the real limit.** Of 53 skills, only 8 have a task in this suite that fairly tests them. The rest are *untested*: unknown, not "not needed".
- **Installed one at a time, relevant skills went unused.** The agent never picked any of the 7 relevant, auto-pickable skills (0 of 27 runs).
- **Installed the way users install it, superpowers was used.** Loaded as a plugin with its startup hook, its skills were invoked in 7 of 12 runs (`systematic-debugging` on debugging tasks, `test-driven-development` on the feature task). How a pack is installed changes whether its skills are used.
- **No pass-rate lift either way**, because the baseline passes these tasks every time. The pack cost 9–31% more per passing task.

An earlier version of this section said 33 of 35 skills were never used. That count included skills paired with unrelated tasks by a shared word, skills only a person can start, and superpowers without its hook. All three are fixed. Details: [docs/calibration.md](docs/calibration.md).

## The task suite

Every task has a hidden checker, a reference solution that passes it, and (for standard tasks) a plausible-but-incomplete solution that must fail it, so a task can't quietly become easy.

**Standard tier** (default):

| Task | Tests claims about | What makes it hard |
| --- | --- | --- |
| `debug-ledger` | debugging, root cause | 4 separate root causes across a package; the failing test only shows some |
| `tests-ratelimiter` | testing, TDD | mutation testing with 12 subtle mutants (boundaries, clock going backwards) |
| `refactor-pricing` | refactoring, module design | hidden global state and exact error messages must survive; every function ≤ 15 lines |
| `feature-cron` | specs, planning, verification | cron's day-of-month/day-of-week OR rule, leap days, `7` = Sunday, steps |
| `git-regression` | git, branches | find the culprit in 30 commits, fix on a new branch, leave `main` untouched |
| `js-lru-cache` | JavaScript, debugging | TTL boundary, recency on get *and* set, expired entries counted as live |

Six more standard tasks (code review and security, hooks, PR writing, skill writing, docs, parallel fixes) are **held out**: not published, so results on them can't be gamed. See "Public and held-out tasks" below.

**Easy tier** (`--tier easy`): five small tasks for smoke tests. Current models usually pass them without help, so they can't show lift.

Tasks needing a program that isn't installed (`node`, `git`) are skipped with a message.

## Calibrate before you compare

A task can only show lift if the agent sometimes fails it without help. Measure that first:

```bash
skilllab calibrate --repeats 3 --budget 5      # baseline only, writes calibration.md
```

Tasks the baseline passes more than 60% of the time are marked "too easy for this model".

## How it decides

- **Workspaces.** Each run copies the task's fixture into a new temp folder. The *with* arm also gets the skill folder in `.claude/skills/`. Nothing else differs.
- **Whole packs (`--pack`).** Many packs are meant to be installed whole. superpowers, for example, ships as a plugin whose startup hook tells the agent to use its skills. Testing one skill alone misses that. With `--pack`, each repo that ships `.claude-plugin/plugin.json` is loaded with `claude --plugin-dir`, hooks included, and runs on every task. Other repos get all their skills installed at once. Plugin hooks run code on your machine, so check a pack first (for example with [skillprint](https://github.com/mekala540/skillprint)).
- **Skills only a person can start** (`disable-model-invocation: true`) never reach the agent's context, so they cost nothing up front and have no trigger rate. skilllab starts them the way a person would, with `/name` before the task, and measures only lift.
- **Agent.** Claude Code headless (`claude -p`) with `--permission-mode dontAsk` and an allowlist: read, edit, write, search, the Skill tool, and `python`/`ls`/`cat`. A skill's own scripts don't run unless a task allows them. Only project settings are loaded (`--setting-sources project`).
- **Pass/fail.** The task's check command, run after the agent finishes. Hidden check files are copied in last, overwriting anything the agent wrote with the same name. Changing a protected file fails the run.
- **Baselines are shared.** Each task runs `--repeats` times without skills, and every skill on that task is compared with the same baseline.
- **Lift** = pass rate with the skill minus pass rate without. `helps` needs both a lift of at least 30 points (`--threshold 0.3`) and a two-sided Fisher's exact test p ≤ 0.1 (`--alpha 0.1`). `hurts` is the mirror. Anything else is `no lift`, with a note when the change was large but not significant.
- **Sample size matters.** With 3 repeats, only 3-of-3 vs 0-of-3 is significant (p = 0.1). With 5 repeats, 4-of-5 vs 0-of-5 is (p ≈ 0.05). Reports show 90% Wilson intervals for each pass rate and warn about small samples.
- **Cost per pass** = total spend on a pair's runs ÷ passing runs, shown next to the baseline's, because a skill that makes the agent cheaper at the same pass rate is still worth knowing about.
- **Triggered** = the agent actually called the Skill tool for that skill (read from Claude Code's `stream-json` events). A difference when the skill never triggered is reported as `flagged`, not `helps`: it's noise. "Relevant but never used" only lists skills the agent could have picked, on tasks judged a fair test of them.
- **Errors.** Runs where the agent never really started (missing CLI, bad auth) are excluded and retried on resume. Timeouts and max-turn stops count as failed attempts, because a skill that makes the agent loop is a real result.
- **Matching, in two steps.** First, keywords propose candidates: a task tag appearing as a whole word in the skill's name or description (`contest` does not match `test`). A shared word is not enough, though: "git" pairs a skill that installs git hooks with a task about finding a regression. So, second, a cheap model (Claude Haiku, about a cent per batch, no tools) judges each candidate: is the skill's own "use when" condition met by this task as given? Its yes/no and a one-line reason go to `matches.json` in the results folder and into the report. Edit the file to overrule it; saved decisions are never re-judged. `--pair SKILL:TASK` forces a pair, and `--no-judge` skips the check.
- **Untested is not "not needed".** A skill with no fair task is listed as untested: nothing is known about it. Those built around a conversation with a person (grilling, teaching, hand-offs) are listed separately, because an unattended run can't judge them.
- **Setup and tools.** Some tasks run a setup script first (e.g. to build a git history) and allow extra tools (`git`, `node`) for that task only.
- **Token costs** of a skill (before running it) are characters ÷ 4: name + description up front, the body on use.
- **Measured cost and tokens** come from Claude Code's final `result` event for each run: `total_cost_usd`, input tokens (fresh + cache reads + cache writes), output tokens, turns, plus wall-clock time. Each is compared as the median per run with vs without, over all valid runs (passed or failed), with a 90% percentile-bootstrap interval (2,000 resamples, fixed seed, so a rebuilt report doesn't change). The verdict uses cost; if a run reports no cost (another agent via `--agent-cmd`), input tokens. Across several tasks, each run is first divided by its task's median baseline, so a big task doesn't drown out small ones. `cheaper` also needs the pass rate to hold (drop ≤ 15 pts). A skill that is `cheaper` is not listed under "Costs context, no measurable lift".
- **Add-ons** (`skilllab compare`) are always on, so they have no trigger rate. Each one runs on every selected task against the same shared baseline. Default `--repeats` is 5 for `compare`, because cost varies from run to run, and a cost verdict needs at least 5 valid runs per arm.
- **What the agent did.** Each run records how many times it called each tool and the first word of every shell command, read from the same `stream-json` events. The cost table shows median shell commands per run, with vs without, and which programs ran. An add-on that works on shell output (a command rewriter like rtk) can only save anything where that number is above zero; built-in tasks mostly use the Read and Edit tools, so such add-ons have little to act on there.
- **Cache and order.** Claude Code caches the prompt: the first run of an arm pays to write the cache and later runs read it for a fraction of the price. So `compare` gives every arm (the baseline too) one warm-up run per task that is discarded, then interleaves the measured runs in a fixed-seed shuffled order, the same on resume. A built-in **control** arm that changes nothing runs alongside; if it comes out anything but `same cost`, the report says the batch is biased. Add-on paths are made absolute when loaded, since the agent runs inside the workspace.

## Read results carefully

- Verdicts hold for *these tasks on this model*. A skill can help on work this suite doesn't cover.
- A few repeats show direction, not proof. Before telling a maintainer their skill doesn't help, rerun with more `--repeats`, and include the logs.
- If you use this to contribute upstream, open one issue per repo with the evidence and offer a small fix. Don't send automated pull requests.

## Adding a task

A task is `suite/tasks/<id>.json` plus a fixture folder and a hidden folder. Every task needs a reference solution in `tests/solutions/<id>/`; the test suite checks that the untouched fixture **fails** the check and the solution **passes** it. `skilllab suggest` drafts tasks with Claude, but drafts stay `"status": "draft"` (and are ignored) until a person has checked them that way.

## Public and held-out tasks

This repo ships the full engine, the easy tier and a set of **public** standard tasks. Anyone can read a public task's checker, which is good for transparency and contributions, but it also means a skill or model could be tuned to pass it.

Trustworthy ratings therefore also use **held-out tasks** that are never published. skilllab loads extra suites with `--suite path/to/private-suite` (repeatable), so you can keep your own held-out tasks next to the public ones.

## For teams

The engine is free and MIT-licensed. For companies that want answers about their own work rather than toy tasks, we're building:

- **Custom task suites from your codebase**: real bugs and features from your repos, with hidden checks, kept private
- **Held-out benchmark suites**: maintained tasks that aren't published, so results can't be gamed
- **Skill and model comparisons**: which skills, packs and models pay for themselves on your tasks, with cost per successful task
- **CI gating**: block a skill-pack update that makes your agents worse
- **Hosted runs and private reports**

Interested? Open an issue titled "Teams" (it can be a one-liner) and we'll follow up.

## Roadmap

- [x] With/without runs, hidden checks, parallel dispatch, budget, resume, verdicts, gap report
- [x] Standard tier: 12 harder tasks, calibration, Fisher's exact test, confidence intervals
- [x] Live lab view, task scaffolding, held-out suites
- [x] Relevance check for skill/task pairs, whole-pack testing with plugin hooks, user-only skills
- [ ] Test on larger models (Sonnet 5.5, Opus 5.5): so far skills were tested on Haiku 5.5 only
- [ ] Your own project instead of sample tasks: your codebase, your task list, past fixed bugs and PRs replayed as tasks, plus a report of tokens spent on skills your work doesn't need
- [ ] Longer, messier tasks where today's models fail without help (the main open problem)
- [ ] More languages (TypeScript, Go, frontend)
- [ ] Several models in one batch, side by side
- [ ] Pull skillprint footprints into the report
- [ ] Public ratings page

## License

MIT
