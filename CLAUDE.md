# skilllab

CLI that measures whether an agent skill helps: runs a fixed task suite with and without
each skill (Claude Code headless), checks results with hidden tests, and reports verdicts
and gaps. Sibling of skillprint, which measures what a skill costs; this one measures lift.

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
- `skilllab/tasks.py`: load the suite, match skills to tasks by tag words.
- `skilllab/agent.py`: `ClaudeAgent` (headless, tool allowlist) and `CommandAgent`; both parsed from stream-json by `parse_stream`.
- `skilllab/runner.py`: `plan` (shared baselines), `execute` (one run in a temp workspace), `run_all` (parallel, budget, resume).
- `skilllab/verdict.py`: verdicts and gaps. `skilllab/report.py`: markdown and HTML. `skilllab/lab.py`: the animated `lab.html` replay (canvas, no dependencies). `skilllab/cli.py`: commands only.
- `skilllab/suite/`: tasks, fixtures, hidden checks. `tests/solutions/`: a reference solution per task.

## Rules

- **Every task needs a reference solution** in `tests/solutions/<id>/`, and `tests/test_suite.py`
  must show the fixture fails the check and the solution passes it. Standard-tier tasks also need a
  plausible-but-incomplete attempt in `tests/shallow/<id>/` that must fail. A solution may include
  `_solve.py` (run in the workspace) for steps like git commits.
- Calibrate new tasks (`skilllab calibrate`) before relying on them: a task the baseline always passes can't show lift.
- **Checks are code, not AI judgment.** Hidden files are copied in after the agent finishes.
  Prefer checks that can't be gamed by spraying (mutation testing, behavior comparison, bullet caps).
- Tests never call the real Claude CLI or spend money. Use `CommandAgent` with `tests/fake_agent.py`.
- Infra errors are excluded and retried; timeouts and max-turn stops count as failures. Don't change one into the other.
- A difference when the skill never triggered is noise and must stay `flagged`.
- Keep README's "How it decides" section in sync with any behavior change.
