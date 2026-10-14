import json
import sys
from pathlib import Path

from skilllab.agent import parse_stream
from skilllab.cli import main
from skilllab.runner import plan
from skilllab.skills import find_skills, parse_frontmatter, source_label
from skilllab.tasks import load_suite, matches
from skilllab.verdict import summarize

FAKE = Path(__file__).parent / "fake_agent.py"


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def skill_md(name, description, body="Do the thing.\n"):
    return f"---\nname: {name}\ndescription: {description}\n---\n{body}"


# --- skills -------------------------------------------------------------------

def test_frontmatter_folded_and_quoted():
    fields, body = parse_frontmatter(
        '---\nname: "tdd"\ndescription: >\n  Use when writing\n  tests first.\n---\nBody\n')
    assert fields == {"name": "tdd", "description": "Use when writing tests first."}
    assert body.strip() == "Body"


def test_find_skills_dedupes_and_skips_tests(tmp_path):
    write(tmp_path, "skills/tdd/SKILL.md", skill_md("tdd", "Use when writing tests"))
    write(tmp_path, ".cursor/skills/tdd/SKILL.md", skill_md("tdd", "copy"))
    write(tmp_path, "tests/fixtures/x/SKILL.md", skill_md("x", "fixture"))
    write(tmp_path, "node_modules/y/SKILL.md", skill_md("y", "dep"))
    skills = find_skills(tmp_path, "me/pack")
    assert [(s.id, s.description) for s in skills] == [("me/pack/tdd", "Use when writing tests")]


def test_source_label():
    assert source_label("https://github.com/obra/superpowers") == "obra/superpowers"
    assert source_label("git@github.com:obra/superpowers.git") == "obra/superpowers"


# --- matching -----------------------------------------------------------------

def test_matching_uses_whole_words(tmp_path):
    tasks = {t.id: t for t in load_suite()}
    write(tmp_path, "a/SKILL.md", skill_md("systematic-debugging", "Use when hunting a bug"))
    write(tmp_path, "b/SKILL.md", skill_md("contest-helper", "Helps with attestation forms"))
    found = {s.name: s for s in find_skills(tmp_path, "p")}
    debugging, contest = found["systematic-debugging"], found["contest-helper"]
    assert matches(debugging, tasks["fix-pagination"])
    assert not matches(debugging, tasks["write-tests-slugify"])
    # "contest" and "attestation" contain "test" but are not the word "test".
    assert not matches(contest, tasks["write-tests-slugify"])


def test_plan_shares_baselines(tmp_path):
    write(tmp_path, "a/SKILL.md", skill_md("debug-a", "debugging"))
    write(tmp_path, "b/SKILL.md", skill_md("debug-b", "fix bugs"))
    write(tmp_path, "c/SKILL.md", skill_md("poetry", "writes poems"))
    tasks = [t for t in load_suite() if t.id == "fix-pagination"]
    runs, untested = plan(find_skills(tmp_path, "p"), tasks, repeats=3)
    assert sum(r.skill is None for r in runs) == 3
    assert sum(r.skill is not None for r in runs) == 6
    assert [s.name for s in untested] == ["poetry"]


# --- agent output ------------------------------------------------------------

def test_parse_stream_reads_skill_use_and_cost():
    lines = [
        {"type": "system", "subtype": "init"},
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "hi"},
            {"type": "tool_use", "name": "Skill", "input": {"skill": "tdd"}}]}},
        {"type": "result", "is_error": False, "total_cost_usd": 0.12, "num_turns": 7,
         "usage": {"input_tokens": 10, "cache_read_input_tokens": 90, "output_tokens": 5}},
    ]
    res = parse_stream("\n".join(json.dumps(x) for x in lines) + "\nnot json\n")
    assert res.skills_invoked == ["tdd"]
    assert (res.cost_usd, res.input_tokens, res.output_tokens, res.turns) == (0.12, 100, 5, 7)
    assert not res.infra_error and not res.note


def test_parse_stream_errors():
    assert parse_stream("").infra_error
    auth = json.dumps({"type": "result", "is_error": True, "result": "Invalid API key",
                       "num_turns": 0, "total_cost_usd": 0})
    assert "Invalid API key" in parse_stream(auth).infra_error
    max_turns = json.dumps({"type": "result", "is_error": True, "subtype": "error_max_turns",
                            "num_turns": 30, "total_cost_usd": 0.9})
    res = parse_stream(max_turns)
    assert not res.infra_error and res.note == "error_max_turns"


# --- verdicts -----------------------------------------------------------------

def _rec(arm, task, passed, skill=None, triggered=True, err=""):
    return {"arm": arm, "task": task, "skill": skill, "passed": passed,
            "skill_triggered": triggered, "infra_error": err, "cost_usd": 0.1}


SK = [{"id": "p/a", "name": "a", "description": "", "source": "p", "upfront_tokens": 150, "onuse_tokens": 10}]
TK = [{"id": "t1", "title": "", "tags": []}]


def test_verdict_helps_and_hurts():
    base = [_rec("baseline", "t1", False)] * 3
    helps = summarize(base + [_rec("skill", "t1", True, "p/a")] * 3, SK, TK, [])
    assert helps["skills"][0]["verdict"] == "helps"
    hurts = summarize([_rec("baseline", "t1", True)] * 3 + [_rec("skill", "t1", False, "p/a")] * 3, SK, TK, [])
    assert hurts["skills"][0]["verdict"] == "hurts"
    assert hurts["gaps"]["hurts"][0]["id"] == "p/a"


def test_verdict_one_run_difference_is_no_lift():
    recs = [_rec("baseline", "t1", False)] * 3 + [_rec("skill", "t1", True, "p/a")] + [_rec("skill", "t1", False, "p/a")] * 2
    s = summarize(recs, SK, TK, [])
    assert s["skills"][0]["verdict"] == "no lift"
    assert s["gaps"]["costly_no_lift"][0]["id"] == "p/a"


def test_verdict_lift_without_trigger_is_flagged():
    recs = [_rec("baseline", "t1", False)] * 3 + [_rec("skill", "t1", True, "p/a", triggered=False)] * 3
    s = summarize(recs, SK, TK, [])
    assert s["skills"][0]["verdict"] == "flagged"
    assert "difference is noise" in s["pairs"][0]["notes"]


def test_infra_errors_are_excluded():
    recs = [_rec("baseline", "t1", False)] * 3 + [_rec("skill", "t1", False, "p/a", err="boom")] * 3
    s = summarize(recs, SK, TK, [])
    assert s["errors"] == 3 and s["skills"] == []


def test_ceiling_and_unsolved_gaps():
    tk = TK + [{"id": "t2", "title": "", "tags": []}]
    recs = [_rec("baseline", "t1", True)] * 3 + [_rec("baseline", "t2", False)] * 3
    gaps = summarize(recs, SK, tk, ["p/a"])["gaps"]
    assert gaps["ceiling_tasks"] == ["t1"]
    assert gaps["unsolved_tasks"] == ["t2"]
    assert gaps["untested_claims"][0]["id"] == "p/a"


# --- end to end ---------------------------------------------------------------

def _pack(tmp_path):
    pack = tmp_path / "pack"
    write(pack, "skills/root-cause/SKILL.md", skill_md("root-cause", "Use when debugging a bug"))
    write(pack, "skills/poems/SKILL.md", skill_md("poems", "Writes poems"))
    return pack


def test_cli_run_end_to_end(tmp_path, capsys):
    out = tmp_path / "out"
    argv = ["run", str(_pack(tmp_path)), "--out", str(out), "--task", "fix-pagination",
            "--repeats", "3", "--workers", "3", "--yes",
            "--agent-cmd", f"{sys.executable} {FAKE} {{prompt_file}}"]
    assert main(argv) == 0
    records = [json.loads(l) for l in (out / "results.jsonl").read_text().splitlines()]
    assert len(records) == 6
    summary = json.loads((out / "summary.json").read_text())
    assert [(s["id"], s["verdict"]) for s in summary["skills"]] == [("pack/root-cause", "helps")]
    assert summary["gaps"]["untested_claims"][0]["id"] == "pack/poems"
    assert "helps" in (out / "report.md").read_text()
    assert "<title>Skill Lab Report</title>" in (out / "report.html").read_text()
    lab = (out / "lab.html").read_text()
    assert "<title>Skill Lab Replay</title>" in lab and "__DATA__" not in lab
    assert '"s": "pack/root-cause"' in lab  # runs are embedded for the replay

    # Rerunning resumes: nothing new is run.
    assert main(argv) == 0
    assert len((out / "results.jsonl").read_text().splitlines()) == 6


def test_budget_stops_new_runs(tmp_path, monkeypatch):
    from skilllab import cli
    from skilllab.agent import CommandAgent
    from skilllab.runner import run_all
    from skilllab.skills import find_skills as fs

    tasks = [t for t in load_suite() if t.id == "fix-pagination"]
    runs, _ = plan(fs(_pack(tmp_path), "pack"), tasks, repeats=3)
    agent = CommandAgent(f"{sys.executable} {FAKE} {{prompt_file}}")
    results = tmp_path / "r.jsonl"
    stats = run_all(runs, agent, "m", results, workers=1, budget_usd=0.5, log=lambda m: None)
    # Each fake run costs $0.25: two runs reach the budget, the other four never start.
    assert stats["ran"] == 2 and stats["stopped_for_budget"] == 4


def test_calibrate_with_fake_agent(tmp_path, capsys):
    out = tmp_path / "cal"
    assert main(["calibrate", "--tier", "easy", "--repeats", "1", "--yes", "--out", str(out),
                 "--agent-cmd", f"{sys.executable} {FAKE} {{prompt_file}}"]) == 0
    table = (out / "calibration.md").read_text()
    # The fake agent does nothing without a skill, so every easy task fails its baseline.
    assert table.count("very hard") == 5


def test_tiers():
    easy, standard = load_suite(tier="easy"), load_suite(tier="standard")
    assert easy and standard and not {t.id for t in easy} & {t.id for t in standard}


def test_needs_person_split():
    from skilllab.verdict import needs_person
    assert needs_person({"name": "grill-me", "description": "Interview the user about a plan"})
    assert needs_person({"name": "handoff", "description": "Compact the conversation for another agent"})
    assert not needs_person({"name": "pr", "description": "Use when writing a PR body."})
    sk = [{"id": "p/grill-me", "name": "grill-me", "description": "Grill me about specs", "source": "p",
           "upfront_tokens": 5, "onuse_tokens": 5},
          {"id": "p/pr", "name": "pr", "description": "Use when writing a PR body.", "source": "p",
           "upfront_tokens": 5, "onuse_tokens": 5}]
    gaps = summarize([], sk, TK, ["p/grill-me", "p/pr"])["gaps"]
    assert [s["id"] for s in gaps["needs_person"]] == ["p/grill-me"]
    assert [s["id"] for s in gaps["untested_claims"]] == ["p/pr"]


def test_fisher_and_wilson():
    from skilllab.verdict import fisher_p, wilson
    assert abs(fisher_p(3, 3, 0, 3) - 0.1) < 1e-9
    assert fisher_p(2, 3, 1, 3) == 1.0
    assert abs(fisher_p(5, 5, 1, 5) - 0.0476) < 1e-3
    assert fisher_p(0, 4, 0, 4) == 1.0
    lo, hi = wilson(3, 3)
    assert hi == 1.0 and 0.4 < lo < 0.6
    assert wilson(0, 0) is None


def test_big_but_insignificant_change_is_no_lift():
    # 1/3 -> 3/3 is +67 pts but p = 0.4: not enough evidence.
    recs = [_rec("baseline", "t1", True)] + [_rec("baseline", "t1", False)] * 2 + [_rec("skill", "t1", True, "p/a")] * 3
    p = summarize(recs, SK, TK, [])["pairs"][0]
    assert p["verdict"] == "no lift" and abs(p["p_value"] - 0.4) < 1e-9
    assert any("not significant" in n for n in p["notes"])


def test_env_note_lists_allowed_commands():
    from skilllab.agent import DEFAULT_TOOLS, env_note
    note = env_note(DEFAULT_TOOLS + ["Bash(git:*)"])
    assert "cat, git, ls, python, python3" in note and "no loops" in note


def test_new_task_scaffold(tmp_path):
    suite, tests = tmp_path / "suite", tmp_path / "t"
    assert main(["new-task", "fix-dates", "--suite", str(suite), "--tests", str(tests)]) == 0
    spec = json.loads((suite / "tasks" / "fix-dates.json").read_text())
    assert spec["status"] == "draft" and spec["check"] == "{python} check_fix_dates.py"
    assert (suite / "fixtures" / "fix-dates-hidden" / "check_fix_dates.py").exists()
    assert (tests / "solutions" / "fix-dates").is_dir() and (tests / "shallow" / "fix-dates").is_dir()
    assert load_suite(suite) == []  # drafts are ignored
    assert main(["new-task", "fix-dates", "--suite", str(suite), "--tests", str(tests)]) == 1
    assert main(["new-task", "Bad_Name", "--suite", str(suite)]) == 2


def test_consecutive_infra_errors_stop_batch(tmp_path):
    from skilllab.agent import AgentResult
    from skilllab.runner import MAX_CONSECUTIVE_ERRORS, run_all

    class Broken:
        def run(self, prompt, cwd, timeout, tools=None):
            return AgentResult(infra_error="usage limit")

    tasks = [t for t in load_suite() if t.id == "fix-pagination"]
    write(tmp_path, "s/a/SKILL.md", skill_md("debug-a", "debugging"))
    runs, _ = plan(find_skills(tmp_path / "s", "p"), tasks, repeats=10)
    stats = run_all(runs, Broken(), "m", tmp_path / "r.jsonl", workers=1, log=lambda m: None)
    assert stats["ran"] == MAX_CONSECUTIVE_ERRORS and stats["stopped_for_errors"] == 20 - MAX_CONSECUTIVE_ERRORS


def test_live_server_serves_results(tmp_path):
    import urllib.request
    from skilllab.cli import serve
    (tmp_path / "lab.html").write_text("<title>x</title>")
    (tmp_path / "results.jsonl").write_text('{"task": "t"}\n')
    httpd = serve(tmp_path, open_browser=False)
    try:
        port = httpd.server_address[1]
        body = urllib.request.urlopen(f"http://127.0.0.1:{port}/results.jsonl").read().decode()
        assert '"task": "t"' in body
    finally:
        httpd.shutdown()
