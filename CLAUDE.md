# skilllab

CLI that measures whether an agent skill or add-on helps: runs a fixed task suite with and
without it (Claude Code headless), checks results with hidden tests, and reports pass-rate
verdicts, measured cost/token savings and gaps. Sibling of skillprint, which estimates what a
skill costs before it runs; this one measures what it does.

## Setup and tests

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e . pytest
pytest -q   # free: uses tests/fake_agent.py, never calls Claude
```

No runtime dependencies; keep it that way. Python 3.9+, so no syntax newer than 3.9 outside
`from __future__ import annotations`.

## Code layout

- `skilllab/skills.py`: find `SKILL.md`, parse frontmatter, dedupe, clone git sources.
- `skilllab/tasks.py`: load the suite, propose skill/task candidates by tag words.
- `skilllab/relevance.py`: judge each candidate (fair test or not), cached in `matches.json`.
- `skilllab/addons.py`: `addon.json` add-ons (settings/hooks, plugin, skills, CLAUDE.md, system prompt, env, setup commands) for `skilllab compare`.
- `skilllab/agent.py`: `ClaudeAgent` (headless, tool allowlist) and `CommandAgent`; both parsed from stream-json by `parse_stream`.
- `skilllab/runner.py`: `plan` (shared baselines), `execute` (one run in a temp workspace), `run_all` (parallel, budget, resume).
- `skilllab/verdict.py`: pass-rate verdicts, cost/token savings (`savings`, bootstrap ranges), gaps. `skilllab/report.py`: markdown and HTML. `skilllab/lab.py`: the animated `lab.html` replay (canvas, no dependencies). `skilllab/cli.py`: commands only.
- `skilllab/suite/`: tasks, fixtures, hidden checks. `tests/solutions/`: a reference solution per task.
- Real tier: `tests/generators/real_tasks.py` writes `suite/tasks/<id>.json`, `suite/fixtures/real-<id>-hidden/` and `tests/solutions/<id>/_solve.py` from a list of upstream fix commits. `runner.ensure_commits`/`materialize` clone into `~/.cache/skilllab/repos` and extract one commit; `fixtures/real-check/check_real.py` is the shared checker. Never copy upstream code or tests into this repo; read them from the cache.
- `skilllab/suite/projects/tally/`: the shared base project for the `project` tier. A task names it as `"base"`; its fixture only holds the files it changes. Some hidden checks hold golden files made from the base (expected totals, outputs, saved files): if you change the base, regenerate them, and `pytest` will tell you which ones drifted.

## Rules

- **Every task needs a reference solution** in `tests/solutions/<id>/`, and `tests/test_suite.py`
  must show the fixture fails the check and the solution passes it. Standard-tier tasks also need a
  plausible-but-incomplete attempt in `tests/shallow/<id>/` that must fail. A solution may include
  `_solve.py` (run in the workspace) for steps like git commits.
- **Project tasks must stay realistic.** Visible tests pass in the fixture unless the task is about failing tests; the bug or gap is something a careful engineer finds, not something the tests point at. Keep the generator scripts for big fixtures (logs, histories) deterministic.
- **Real tasks** need no shallow attempt: the upstream tests are the arbiter. A real task's fix must make previously failing upstream tests pass, verified by the generator; the workspace must never contain upstream history after the snapshot.
- Calibrate new tasks (`skilllab calibrate`) before relying on them: a task the baseline always passes can't show lift.
- **Checks are code, not AI judgment.** Hidden files are copied in after the agent finishes.
  Prefer checks that can't be gamed by spraying (mutation testing, behavior comparison, bullet caps).
- Tests never call the real Claude CLI or spend money. Use `CommandAgent` with `tests/fake_agent.py`.
- Infra errors are excluded and retried; timeouts and max-turn stops count as failures. Don't change one into the other.
- A difference when the skill never triggered is noise and must stay `flagged`.
- **Only fair pairs count.** A skill is judged only on tasks that fairly test it (relevance check,
  `matches.json`). Untested means unknown, never "not needed". Skills with
  `disable-model-invocation: true` have no trigger rate and cost no up-front tokens.
- Packs that ship as plugins are tested as plugins (`--plugin-dir`, hooks included), the way users install them.
- **A saving needs the pass rate to hold.** `cheaper` requires the whole cost range below zero and a pass-rate drop of at most `SAVINGS_GUARD`; otherwise it's `cheaper, fewer passes`. Don't report a token saving without the pass rate next to it.
- **Cost comparisons must stay unbiased.** `compare` keeps the discarded warm-up per arm, the interleaved fixed-seed order and the no-op control arm; a cost verdict needs `MIN_SAVINGS_RUNS` per arm. Don't remove these to save runs.
- Add-ons run code (hooks, setup, proxies). Tests use local stand-ins only; never ship an `addon.json` for a real tool without checking its install steps against its own docs.
- Keep README's "How it decides" section in sync with any behavior change.
