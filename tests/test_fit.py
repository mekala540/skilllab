import json
import shutil
import sys
from pathlib import Path

from skilllab import cli, fit
from skilllab.skills import find_skills
from test_core import FAKE, skill_md, write

SUITE = Path(__file__).resolve().parent.parent / "skilllab" / "suite" / "fixtures"


def test_parse_tasks_headings_checks_and_plain_lines(tmp_path):
    tasks = fit.parse_tasks("# Fix login timeout\nUsers get logged out.\ncheck: pytest -q tests/a.py\n\n"
                            "## Fix login timeout\nAgain\n", tmp_path, default_check="make test")
    assert [t.id for t in tasks] == ["fix-login-timeout", "fix-login-timeout-2"]
    assert tasks[0].check == "pytest -q tests/a.py" and tasks[1].check == "make test"
    assert "check:" not in tasks[0].prompt and tasks[0].prompt.startswith("Fix login timeout")
    assert "node_modules" in tasks[0].ignore and tasks[0].fixture == tmp_path
    plain = fit.parse_tasks("- Add CSV export\n\n* Speed up search\n")
    assert [t.title for t in plain] == ["Add CSV export", "Speed up search"]


def test_profile_reads_languages_tools_tests_and_git(tmp_path):
    write(tmp_path, "app/main.py", "print(1)\n")
    write(tmp_path, "app/util.py", "x = 1\n")
    write(tmp_path, "tests/test_main.py", "def test(): pass\n")
    write(tmp_path, "requirements.txt", "fastapi==0.1\npytest>=8\n")
    write(tmp_path, "node_modules/x/index.js", "ignored")
    (tmp_path / ".git").mkdir()
    p = fit.profile_project(tmp_path)
    assert p["languages"] == ["Python"] and p["tools"] == ["fastapi", "pytest"]
    assert p["test_files"] == 1 and p["git"] and p["files"] == 4
    assert "Python" in fit.profile_text(p)


def _skills(tmp_path):
    write(tmp_path, "pack/debugging/SKILL.md", skill_md("debugging", "Use when hunting a bug"))
    write(tmp_path, "pack/ts-helper/SKILL.md", skill_md("ts-helper", "x" * 400))
    write(tmp_path, "pack/grill-me/SKILL.md", "---\nname: grill-me\ndescription: Interview me\n"
                                       "disable-model-invocation: true\n---\nAsk.\n")
    return find_skills(tmp_path / "pack", "me/pack")


def test_triage_keeps_decisions_until_task_or_project_changes(tmp_path):
    skills = _skills(tmp_path)
    calls = []

    def judge(task, skills_, profile=""):
        calls.append((task.id, profile))
        return ({"debugging": "a bug to find"} if "bug" in task.prompt else {}), 0.002

    tasks = fit.parse_tasks("# Fix the bug\n# Write docs\n")
    d1, cost = fit.triage(skills, tasks, {}, judge, "Python", log=lambda m: None)
    assert len(calls) == 2 and cost == 0.004
    d2, _ = fit.triage(skills, tasks, d1, judge, "Python", log=lambda m: None)
    assert len(calls) == 2 and d2 == d1
    fit.triage(skills, tasks, d1, judge, "Go", log=lambda m: None)
    assert len(calls) == 4  # project changed: judged again

    s = fit.summarize_fit(skills, tasks, d1, sessions_per_day=100, price_per_mtok=1.0)
    status = {r["name"]: r["status"] for r in s["skills"]}
    assert status == {"debugging": "fits", "ts-helper": "not needed", "grill-me": "user-only, unused"}
    waste = next(r["upfront_tokens"] for r in s["skills"] if r["name"] == "ts-helper")
    assert s["tokens"]["unneeded_per_session"] == waste
    assert s["tokens"]["unneeded_per_month"] == waste * 3000
    md = fit.to_markdown(s, "m")
    assert "fit none" in md and "`me/pack/ts-helper`" in md and "a bug to find" in md


def _project(tmp_path):
    project = tmp_path / "proj"
    shutil.copytree(SUITE / "pagination", project)
    shutil.copytree(SUITE / "pagination-hidden", project, dirs_exist_ok=True)
    return project


def test_fit_cli_triage_and_measure(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "find_claude", lambda: "/bin/true")
    def judge(task, skills, profile=""):
        return ({"debugging": "pagination bug"} if "page" in task.prompt else {}), 0.0

    monkeypatch.setattr(fit, "claude_fit_judge", lambda *a, **k: judge)
    _skills(tmp_path)
    tasks = tmp_path / "tasks.md"
    tasks.write_text("# Fix the first page skipping items\nUsers report missing items on page one.\n"
                     "check: {python} -m unittest -q test_hidden_pager\n\n# Rename the package\n")
    out = tmp_path / "out"
    argv = ["fit", str(tmp_path / "pack"), "--tasks", str(tasks), "--project", str(_project(tmp_path)),
            "--out", str(out), "--sessions-per-day", "50"]
    assert cli.main(argv) == 0
    report = (out / "fit.md").read_text()
    assert "1 fit at least one task" in report and "Python" in report
    assert json.loads((out / "fit.json").read_text())["counts"]["not_needed"] == 1

    argv += ["--measure", "--repeats", "3", "--yes", "--agent-cmd", f"{sys.executable} {FAKE} {{prompt_file}}"]
    assert cli.main(argv) == 0
    text = capsys.readouterr().out
    assert "skipping rename-the-package: no check" in text
    summary = json.loads((out / "summary.json").read_text())
    assert [(s["id"], s["verdict"]) for s in summary["skills"]] == [("pack/debugging", "helps")]


def test_measure_skips_tasks_whose_check_already_passes(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "find_claude", lambda: "/bin/true")
    monkeypatch.setattr(fit, "claude_fit_judge", lambda *a, **k: (lambda t, s, p="": ({}, 0.0)))
    _skills(tmp_path)
    project = tmp_path / "done"
    write(project, "ok.py", "x = 1\n")
    rc = cli.main(["fit", str(tmp_path / "pack"), "--task-text", "Nothing to do", "--project", str(project),
                   "--check", "true", "--out", str(tmp_path / "o"), "--measure", "--yes",
                   "--agent-cmd", "true"])
    assert rc == 1
    assert "already passes on the untouched project" in capsys.readouterr().out


# --- task formats: pasted stories, Jira text, CSV, JSON ------------------------

STORY = """SHOP-482: Discount applied to shipping instead of subtotal
As a customer, I want my discount code to reduce the item price,
so that I pay what the promotion promised.

Acceptance criteria:
- SAVE10 takes 10% off the item subtotal
- Shipping cost is unchanged
- Discount is applied before tax
check: pytest tests/test_checkout.py -q
"""


def test_pasted_jira_story_is_one_task_with_its_criteria():
    [t] = fit.parse_tasks(STORY)
    assert t.id == "shop-482" and t.title == "SHOP-482: Discount applied to shipping instead of subtotal"
    assert "Shipping cost is unchanged" in t.prompt and "Discount is applied before tax" in t.prompt
    assert t.check == "pytest tests/test_checkout.py -q" and "check:" not in t.prompt


def test_story_without_key_or_headings_is_one_task():
    [t] = fit.parse_tasks("Make search faster\n\nThe page takes 4 seconds.\n\n- filter in SQL\n- add an index\n")
    assert t.title == "Make search faster" and "add an index" in t.prompt


def test_several_issue_keys_and_separators_split_tasks():
    tasks = fit.parse_tasks("SHOP-1: First\nbody one\n- SHOP-9 is related\nSHOP-2 - Second\nbody two\n")
    assert [t.id for t in tasks] == ["shop-1", "shop-2"]
    assert "SHOP-9 is related" in tasks[0].prompt  # a bullet mentioning a key is not a new task
    parts = fit.parse_tasks("Fix login\nUsers are logged out.\n---\nAdd export\nCSV of orders.\n")
    assert [t.title for t in parts] == ["Fix login", "Add export"]


def test_jira_wiki_and_markdown_headings_with_keys():
    tasks = fit.parse_tasks("h1. SHOP-7: Wiki heading\n*bold* text\nh2. Plain wiki task\n")
    assert [(t.id, t.title) for t in tasks] == [("shop-7", "SHOP-7: Wiki heading"),
                                                ("plain-wiki-task", "Plain wiki task")]
    [md] = fit.parse_tasks("## [OPS-12] Rotate keys\nRotate the API keys.\n")
    assert md.id == "ops-12" and md.title == "OPS-12: Rotate keys"


def test_jira_csv_export():
    csv_text = ('\ufeffSummary,Issue key,Issue Type,Description,"Custom field (Acceptance Criteria)",Check\n'
                'Fix discount,SHOP-482,Bug,"Discount hits shipping.\nShould hit subtotal.",'
                '"- 10% off subtotal",pytest -q tests/test_checkout.py\n'
                ',SHOP-483,Bug,no summary so skipped,,\n'
                'Add export,SHOP-490,Story,CSV of orders,,\n')
    tasks = fit.parse_tasks(csv_text)
    assert [t.id for t in tasks] == ["shop-482", "shop-490"]
    assert "Should hit subtotal." in tasks[0].prompt and "10% off subtotal" in tasks[0].prompt
    assert tasks[0].check == "pytest -q tests/test_checkout.py" and tasks[1].check == ""
    import pytest
    with pytest.raises(ValueError):
        fit.parse_tasks("Key,Description\nA-1,x\n", fmt="csv")


def test_jira_json_v2_v3_and_search_results():
    v2 = {"key": "SHOP-1", "fields": {"summary": "Fix totals", "description": "Totals are off."}}
    [t] = fit.parse_tasks(json.dumps(v2))
    assert t.id == "shop-1" and "Totals are off." in t.prompt
    adf = {"type": "doc", "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": "First line"}]},
        {"type": "bulletList", "content": [
            {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "point A"}]}]}]}]}
    search = {"names": {"customfield_100": "Acceptance Criteria"}, "issues": [
        {"key": "SHOP-2", "fields": {"summary": "Cloud issue", "description": adf,
                                     "customfield_100": "Must log every refund"}},
        {"key": "SHOP-3", "fields": {"summary": ""}}]}
    [c] = fit.parse_tasks(json.dumps(search))
    assert "First line" in c.prompt and "- point A" in c.prompt and "Must log every refund" in c.prompt
    assert len(fit.parse_tasks(json.dumps([v2, v2]))) == 2


def test_story_task_keeps_multiline_text_together():
    [t] = fit.story_task(STORY, default_check="make test")
    assert t.id == "shop-482" and "Acceptance criteria" in t.prompt
    assert t.check == "pytest tests/test_checkout.py -q"


# --- CLI: formats, errors, hidden checks ----------------------------------------

def _no_fit_judge(monkeypatch):
    monkeypatch.setattr(cli, "find_claude", lambda: "/bin/true")
    monkeypatch.setattr(fit, "claude_fit_judge", lambda *a, **k: (lambda t, s, p="": ({}, 0.0)))


def test_cli_reads_csv_and_stories_and_makes_ids_unique(tmp_path, monkeypatch, capsys):
    _no_fit_judge(monkeypatch)
    _skills(tmp_path)
    sheet = tmp_path / "sprint.csv"
    sheet.write_text("Summary,Issue key\nFix discount,SHOP-482\n")
    out = tmp_path / "o"
    assert cli.main(["fit", str(tmp_path / "pack"), "--tasks", str(sheet), "--task-text", STORY,
                     "--out", str(out)]) == 0
    ids = [t["id"] for t in json.loads((out / "fit.json").read_text())["tasks"]]
    assert ids == ["shop-482", "shop-482-2"]
    bad = tmp_path / "bad.csv"
    bad.write_text("Key,Description\nA-1,x\n")
    assert cli.main(["fit", str(tmp_path / "pack"), "--tasks", str(bad), "--out", str(out)]) == 2
    assert "Summary" in capsys.readouterr().err
    assert cli.main(["fit", str(tmp_path / "pack"), "--task-text", "x", "--check-dir",
                     str(tmp_path / "missing"), "--out", str(out)]) == 2



def test_hidden_checks_are_unseen_and_cannot_be_faked(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "find_claude", lambda: "/bin/true")
    monkeypatch.setattr(fit, "claude_fit_judge", lambda *a, **k: (lambda t, s, p="": ({"debugging": "bug"}, 0.0)))
    _skills(tmp_path)
    project = tmp_path / "proj"
    shutil.copytree(SUITE / "pagination", project)  # the project, without the hidden test
    checks = SUITE / "pagination-hidden"            # test_hidden_pager.py lives only here
    seen = tmp_path / "seen.txt"
    cheat = tmp_path / "cheat.py"
    cheat.write_text(
        "import os, pathlib\n"
        f"pathlib.Path({str(seen)!r}).open('a').write(' '.join(sorted(os.listdir('.'))) + '\\n')\n"
        "pathlib.Path('test_hidden_pager.py').write_text('import unittest\\n"
        "class T(unittest.TestCase):\\n    def test_ok(self): pass\\n')\n"
        "print('{\"type\": \"result\", \"subtype\": \"success\", \"is_error\": false, \"total_cost_usd\": 0.01}')\n")
    out = tmp_path / "o"
    argv = ["fit", str(tmp_path / "pack"), "--task-text", "Fix the first page skipping items",
            "--project", str(project), "--check-dir", str(checks),
            "--check", "{python} -m unittest -q test_hidden_pager", "--out", str(out),
            "--measure", "--repeats", "2", "--yes", "--agent-cmd", f"{sys.executable} {cheat}"]
    assert cli.main(argv) == 0
    assert "test_hidden_pager.py" not in seen.read_text()  # the agent never saw the check
    records = [json.loads(l) for l in (out / "results.jsonl").read_text().splitlines()]
    assert len(records) == 4 and not any(r["passed"] for r in records)  # its fake test was overwritten


def test_measure_with_no_fitting_skill_says_so(tmp_path, monkeypatch, capsys):
    _no_fit_judge(monkeypatch)
    _skills(tmp_path)
    rc = cli.main(["fit", str(tmp_path / "pack"), "--task-text", "Fix paging", "--project",
                   str(_project(tmp_path)), "--check", "{python} -m unittest -q test_hidden_pager",
                   "--out", str(tmp_path / "o"), "--measure", "--yes", "--agent-cmd", "true"])
    assert rc == 1 and "nothing to compare" in capsys.readouterr().out


def test_hidden_check_counts_in_precheck(tmp_path):
    project = tmp_path / "proj"
    shutil.copytree(SUITE / "pagination", project)
    [t] = fit.story_task("Fix paging", project=project, hidden=SUITE / "pagination-hidden",
                         default_check="{python} -m unittest -q test_hidden_pager")
    passes, tail = fit.precheck(t)
    assert not passes  # the hidden test exists in the precheck copy and fails on the buggy code
    [no_hidden] = fit.story_task("Fix paging", project=project,
                                 default_check="{python} -m unittest -q test_hidden_pager")
    assert not fit.precheck(no_hidden)[0]  # missing test module also fails, but for the wrong reason


def test_fit_measure_pack_mode(tmp_path, monkeypatch):
    _no_fit_judge(monkeypatch)  # packs run on every task with a check, fitting or not
    _skills(tmp_path)
    out = tmp_path / "o"
    rc = cli.main(["fit", str(tmp_path / "pack"), "--task-text", "Fix the first page skipping items",
                   "--project", str(_project(tmp_path)), "--check", "{python} -m unittest -q test_hidden_pager",
                   "--out", str(out), "--measure", "--pack", "--repeats", "3", "--yes",
                   "--agent-cmd", f"{sys.executable} {FAKE} {{prompt_file}}"])
    assert rc == 0
    records = [json.loads(l) for l in (out / "results.jsonl").read_text().splitlines()]
    assert sorted({r["arm"] for r in records}) == ["baseline", "pack"]
    summary = json.loads((out / "summary.json").read_text())
    assert [(s["id"], s["verdict"]) for s in summary["skills"]] == [("pack:pack", "helps")]
    assert json.loads((out / "meta.json").read_text())["mode"] == "pack"
