# Contributing to skilllab

The most valuable contribution is a **good task**: a small, realistic job with a checker that
can't be gamed. Bug reports about wrong verdicts are next.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e . pytest
pytest -q          # free: never calls a model
```

Python 3.9+, no runtime dependencies. Keep it that way.

## Adding a task

```bash
skilllab new-task my-task-id
```

This creates the skeleton: `suite/tasks/my-task-id.json`, a fixture folder (what the agent
starts with), a hidden folder (the checker, copied in after the agent finishes), and folders
for a reference solution and a shallow solution under `tests/`. Then:

1. **Write the fixture.** Realistic code with a clear spec: docstrings, a `SPEC.md`, an issue.
2. **Write the checker** as code, not AI judgment. Exit 0 = pass. Good patterns:
   hidden tests, mutation testing, comparison with a reference over random inputs, caps that
   stop "list everything" answers, decoys that must *not* be reported.
3. **Write a reference solution** in `tests/solutions/<id>/`. It must pass.
4. **Write a shallow solution** in `tests/shallow/<id>/`: the plausible quick fix a hurried
   agent would make. It must fail. This is what proves the task measures care, not luck.
5. **Tag it** with the words skills use to describe what they're for (`debugging`, `tdd`, ...).
   Tags propose candidates: every skill whose name or description contains one of them. A
   relevance check then keeps only skills the task is a fair test of (see `matches.json`), so
   broad tags are fine; they won't pair unrelated skills with your task.
6. Run `pytest -q`. Remove `"status": "draft"` when it passes.
7. If you can, run `skilllab calibrate --task my-task-id` and put the baseline pass rate in your
   PR. A task the baseline always passes can't show lift; make it harder.

Read [docs/writing-tasks.md](docs/writing-tasks.md) for what makes a task good.

## Reporting a wrong verdict

Open a "Wrong verdict" issue with the report row, model, number of repeats and, ideally,
`--keep` workspaces. Small samples are noisy, so rerunning with `--repeats 5` first helps.

## Contributing results back to skill authors

If skilllab shows a skill never triggers or doesn't help, tell its maintainer kindly, with
evidence: the task, model, repeats, pass rates and p-value. One issue per repo. Don't send
automated pull requests.

## Pull requests

- One task or one fix per PR.
- Keep README's "How it decides" in sync with behavior changes.
- `pytest -q` must pass; CI runs it on Python 3.9, 3.11 and 3.13.
