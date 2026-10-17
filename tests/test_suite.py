"""Every task's check must fail on the untouched fixture and pass on a correct solution."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from skilllab.agent import AgentResult
from skilllab.runner import Run, execute
from skilllab.tasks import load_suite

SOLUTIONS = Path(__file__).parent / "solutions"
SHALLOW = Path(__file__).parent / "shallow"  # plausible but incomplete fixes that must fail
TASKS = load_suite()


class DoNothing:
    def run(self, prompt, cwd, timeout, tools=None):
        return AgentResult(cost_usd=0.0)


class CopySolution:
    def __init__(self, task_id, root=SOLUTIONS):
        self.src = root / task_id

    def run(self, prompt, cwd, timeout, tools=None):
        # Files are copied as is; a _solve.py (e.g. git commands) runs and is removed.
        shutil.copytree(self.src, cwd, dirs_exist_ok=True, ignore=shutil.ignore_patterns("_solve.py"))
        if (self.src / "_solve.py").exists():
            subprocess.run([sys.executable, str(self.src / "_solve.py")], cwd=cwd, check=True,
                           capture_output=True)
        return AgentResult(cost_usd=0.0)


def test_easy_tier():
    assert {t.id for t in TASKS if t.tier == "easy"} == {
        "fix-pagination", "write-tests-slugify", "refactor-orders",
        "feature-durations", "review-inventory"}


@pytest.mark.parametrize("task", TASKS, ids=lambda t: t.id)
def test_fixture_fails_check(task):
    rec = execute(Run(task, None, 0), DoNothing(), "test")
    assert not rec["infra_error"]
    assert rec["passed"] is False, rec["check_tail"]


@pytest.mark.parametrize("task", TASKS, ids=lambda t: t.id)
def test_solution_passes_check(task):
    assert (SOLUTIONS / task.id).is_dir(), f"add a reference solution in tests/solutions/{task.id}"
    rec = execute(Run(task, None, 0), CopySolution(task.id), "test")
    assert rec["passed"] is True, rec["check_tail"]


SHALLOW_TASKS = [t for t in TASKS if (SHALLOW / t.id).is_dir()]


@pytest.mark.parametrize("task", SHALLOW_TASKS, ids=lambda t: t.id)
def test_shallow_fix_fails(task):
    """Standard tasks must separate careful work from a quick patch."""
    rec = execute(Run(task, None, 0), CopySolution(task.id, SHALLOW), "test")
    assert rec["passed"] is False, rec["check_tail"]


def test_standard_tasks_have_shallow_fixes():
    missing = [t.id for t in TASKS if t.tier == "standard" and not (SHALLOW / t.id).is_dir()]
    assert not missing, f"add a shallow (incomplete) solution in tests/shallow/ for {missing}"


def test_editing_protected_file_fails():
    task = next(t for t in TASKS if t.id == "fix-pagination")

    class CheatAgent(CopySolution):
        def run(self, prompt, cwd, timeout, tools=None):
            super().run(prompt, cwd, timeout, tools)
            (cwd / "tests" / "test_pager.py").write_text("# deleted\n")
            return AgentResult(cost_usd=0.0)

    rec = execute(Run(task, None, 0), CheatAgent(task.id), "test")
    assert rec["passed"] is False
    assert rec["protected_changed"] == ["tests/test_pager.py"]


def test_hidden_checks_overwrite_agent_copies():
    task = next(t for t in TASKS if t.id == "fix-pagination")

    class FakeHidden:
        def run(self, prompt, cwd, timeout, tools=None):
            # A cheating agent writes its own always-passing "hidden" test.
            (cwd / "test_hidden_pager.py").write_text("import unittest\n")
            return AgentResult(cost_usd=0.0)

    rec = execute(Run(task, None, 0), FakeHidden(), "test")
    assert rec["passed"] is False


def test_review_check_rejects_spraying():
    task = next(t for t in TASKS if t.id == "review-inventory")

    class Spray:
        def run(self, prompt, cwd, timeout, tools=None):
            names = ["add_stock", "remove_stock", "count", "low_stock", "apply_discount", "merge"]
            (cwd / "REVIEW.md").write_text("".join(f"- `{n}` may be buggy\n" for n in names))
            return AgentResult(cost_usd=0.0)

    assert execute(Run(task, None, 0), Spray(), "test")["passed"] is False


def test_project_tier_shares_one_base():
    project = [t for t in TASKS if t.tier == "project"]
    assert len(project) >= 12
    assert {t.base.name for t in project} == {"tally"}
    assert all("git" in t.requires and t.setup for t in project)
