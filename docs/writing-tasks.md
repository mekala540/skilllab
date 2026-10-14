# Writing good tasks

A task is useful when it separates careful work from a quick patch, and a skill that
promotes careful work can move the pass rate.

## Checklist

- **Realistic.** Something a developer would actually ask an agent to do.
- **Self-contained.** Standard library (or Node built-ins) only; runs offline in seconds.
- **Specified.** The fixture states the rules: docstrings, a spec, an issue. The checker never
  tests something the agent couldn't know.
- **Hidden checks.** The agent sees a symptom, not the full test. Hidden files are copied in
  after it finishes, so it can't edit or read them.
- **Hard to game.** Ask: what would a lazy agent write? Make that fail.
  - writing tests → mutation testing (tests must fail on broken copies)
  - refactoring → compare with the original on thousands of random inputs
  - review → bullet caps, decoys that must not be reported
  - docs → run every example
- **Calibrated.** For the model you care about, the baseline should pass sometimes but not
  always: roughly 10-60%. Run `skilllab calibrate`.
- **Protected.** List files the agent must not change under `"protect"`.

## Task JSON

```json
{
  "id": "my-task",
  "tier": "standard",
  "title": "One line",
  "tags": ["words", "skills use"],
  "fixture": "fixtures/my-task",
  "hidden": "fixtures/my-task-hidden",
  "prompt": "What the agent is told.",
  "check": "{python} check_my_task.py",
  "protect": ["files/the/agent/must/not/change"],
  "tools": ["Bash(git:*)"],
  "requires": ["git"],
  "setup": "fixtures/my-task-setup",
  "timeout": 900
}
```

`{python}` is replaced with the running interpreter. `setup` (optional) is a folder with a
`_setup.py` run in the workspace before the agent starts, then removed (used to build a git
history). `tools` grants extra commands for this task only.

## Public and held-out tasks

Public tasks are for development and transparency: anyone can read their checkers, so a skill
or model could be tuned to them. Ratings meant to be trusted should also include held-out
tasks that aren't published. Keep a private suite and pass it with `--suite path/to/suite`.
