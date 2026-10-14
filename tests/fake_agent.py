"""Stand-in for Claude Code in tests. Emits stream-json like the real CLI.

Behavior: if a skill is installed in .claude/skills, it "uses" it and copies the
solution for the task into the workspace; otherwise it does nothing. So every skill
should come out as "helps" on tasks whose baseline fails.

FAKE_AGENT_MODE=demo makes outcomes random but skill-dependent, to preview reports
and lab.html with varied verdicts. Demo results are fake: never publish them.
"""

import json
import os
import random
import shutil
import sys
from pathlib import Path

SOLUTIONS = Path(__file__).parent / "solutions"
FIXTURE_TO_TASK = {
    "pager.py": "fix-pagination",
    "slugify.py": "write-tests-slugify",
    "orders.py": "refactor-orders",
    "durations.py": "feature-durations",
    "inventory.py": "review-inventory",
}


def main():
    cwd = Path.cwd()
    skills_dir = cwd / ".claude" / "skills"
    installed = sorted(p.name for p in skills_dir.iterdir()) if skills_dir.is_dir() else []
    mode = os.environ.get("FAKE_AGENT_MODE", "")
    if mode == "demo":
        return demo(cwd, installed)
    for name in installed:
        print(json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": name}}]}}))
    if installed and mode != "never-help":
        for fixture, task in FIXTURE_TO_TASK.items():
            if (cwd / fixture).exists():
                shutil.copytree(SOLUTIONS / task, cwd, dirs_exist_ok=True)
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False,
                      "total_cost_usd": 0.25, "num_turns": 3,
                      "usage": {"input_tokens": 100, "output_tokens": 20}}))
    return 0


def demo(cwd, installed):
    # Each skill gets a stable "true effect" from its name; each run adds noise.
    effect = (sum(map(ord, installed[0])) % 100 / 100 - 0.35) if installed else 0.0
    triggered = bool(installed) and random.random() < 0.8
    if triggered:
        print(json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": installed[0]}}]}}))
    if random.random() < 0.35 + (effect if triggered else 0):
        for fixture, task in FIXTURE_TO_TASK.items():
            if (cwd / fixture).exists():
                shutil.copytree(SOLUTIONS / task, cwd, dirs_exist_ok=True)
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False,
                      "total_cost_usd": round(random.uniform(0.05, 0.14), 4), "num_turns": 5,
                      "usage": {"input_tokens": 60000, "output_tokens": 800}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
