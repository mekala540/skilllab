"""Add-ons (token savers, memory tools, prompt styles) and the cost/token savings verdict."""

import json
import os
import shlex
import shutil
import stat
import sys
from pathlib import Path

import pytest

from skilllab.addons import load_addon
from skilllab.agent import AgentResult, ClaudeAgent
from skilllab.cli import main
from skilllab.runner import Run, execute, plan_addons, run_all
from skilllab.tasks import load_suite
from skilllab.verdict import savings, summarize

FAKE = Path(__file__).parent / "fake_agent.py"


def addon(root: Path, spec: dict, files: dict = None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "addon.json").write_text(json.dumps(spec), encoding="utf-8")
    for rel, text in (files or {}).items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


def task(tid="fix-pagination"):
    return [t for t in load_suite() if t.id == tid][0]


# --- loading ------------------------------------------------------------------

def test_load_addon_validates(tmp_path):
    with pytest.raises(ValueError, match="no addon.json"):
        load_addon(tmp_path)
    with pytest.raises(ValueError, match="needs a name"):
        load_addon(addon(tmp_path / "a", {"description": "x"}))
    with pytest.raises(ValueError, match="unknown fields hooks"):
        load_addon(addon(tmp_path / "b", {"name": "b", "hooks": {}}))
    with pytest.raises(ValueError, match="settings file"):
        load_addon(addon(tmp_path / "c", {"name": "c", "settings": "missing.json"}))
    with pytest.raises(ValueError, match="claude_md"):
        load_addon(addon(tmp_path / "d", {"name": "d", "claude_md": "CLAUDE.md"}))
    a = load_addon(addon(tmp_path / "e", {"name": "e", "settings": {"hooks": {}}}))
    assert a.id == "addon:e" and json.loads(a.settings_arg()) == {"hooks": {}}


def test_addon_meta_counts_its_own_context(tmp_path):
    a = load_addon(addon(tmp_path / "a", {"name": "a", "claude_md": "CLAUDE.md",
                                          "append_system_prompt": "x" * 40}, {"CLAUDE.md": "y" * 400}))
    m = a.meta()
    assert m["upfront_tokens"] == 110 and m["addon"] and m["source"] == "addon"


def test_missing_program_is_reported(tmp_path):
    a = load_addon(addon(tmp_path / "a", {"name": "a", "requires": ["no-such-program-xyz"]}))
    assert a.missing() == ["no-such-program-xyz"]


# --- running ------------------------------------------------------------------

class Recorder:
    def __init__(self):
        self.calls = []

    def run(self, prompt, cwd, timeout, tools=None, plugin_dirs=None, settings=None, env=None,
            append_prompt=""):
        cwd = Path(cwd)
        self.calls.append({"tools": tools, "plugin_dirs": plugin_dirs, "settings": settings, "env": env,
                           "append_prompt": append_prompt,
                           "claude_md": (cwd / "CLAUDE.md").read_text() if (cwd / "CLAUDE.md").exists() else None,
                           "marker": (cwd / "setup-ran").exists(),
                           "skills": sorted(p.name for p in (cwd / ".claude" / "skills").glob("*"))})
        return AgentResult(cost_usd=0.1, turns=2)


def test_execute_switches_the_addon_on(tmp_path):
    root = addon(tmp_path / "saver", {
        "name": "saver", "settings": "settings.json", "plugin_dir": "plugin", "skills_dir": "skills",
        "claude_md": "CLAUDE.md", "append_system_prompt": "Be brief.",
        "env": {"ANTHROPIC_BASE_URL": "http://127.0.0.1:9"}, "tools": ["Bash(rtk:*)"],
        "setup": [f"{sys.executable} -c \"open('setup-ran', 'w').close()\""],
    }, {"settings.json": "{}", "plugin/.claude-plugin/plugin.json": "{}", "CLAUDE.md": "Keep it short.",
        "skills/terse/SKILL.md": "---\nname: terse\ndescription: d\n---\nbody\n"})
    a = load_addon(root)
    agent = Recorder()
    rec = execute(Run(task(), None, 0, addon=a), agent, "m")
    call = agent.calls[0]
    assert call["settings"] == str(root / "settings.json")
    assert call["plugin_dirs"] == [root / "plugin"]
    assert call["env"] == {"ANTHROPIC_BASE_URL": "http://127.0.0.1:9"}
    assert call["append_prompt"] == "Be brief."
    assert call["claude_md"] == "Keep it short." and call["marker"] and call["skills"] == ["terse"]
    assert "Bash(rtk:*)" in call["tools"]
    assert rec["arm"] == "addon" and rec["skill"] == "addon:saver" and rec["skill_triggered"]

    # The baseline gets none of it.
    execute(Run(task(), None, 0), agent, "m")
    base = agent.calls[1]
    assert base["settings"] is None and base["env"] is None and base["claude_md"] is None
    assert not base["marker"] and base["skills"] == [] and "Bash(rtk:*)" not in (base["tools"] or [])


def test_failed_setup_is_an_infrastructure_error(tmp_path):
    a = load_addon(addon(tmp_path / "bad", {"name": "bad", "setup": [f"{sys.executable} -c \"raise SystemExit(3)\""]}))
    runs = [r for r in plan_addons([a], [task()], 1, warmup=False) if r.addon]
    stats = run_all(runs, Recorder(), "m", tmp_path / "r.jsonl", workers=1, log=lambda m: None)
    rec = json.loads((tmp_path / "r.jsonl").read_text().splitlines()[0])
    assert stats["ran"] == 1 and "setup failed" in rec["infra_error"] and rec["skill"] == "addon:bad"


def test_plan_addons_shares_one_baseline():
    a1, a2 = (type("A", (), {"id": f"addon:{n}"})() for n in "xy")
    runs = plan_addons([a1, a2], [task()], 3, warmup=False)
    assert [r.arm for r in runs].count("baseline") == 3 and len(runs) == 9


def test_plan_addons_warms_up_then_interleaves():
    a1, a2 = (type("A", (), {"id": f"addon:{n}"})() for n in "xy")
    runs = plan_addons([a1, a2], [task()], 5)
    # One discarded warm-up per arm comes first, so no arm pays the cache write in a measured run.
    assert [r.arm for r in runs[:3]] == ["warmup"] * 3
    assert {r.subject for r in runs[:3]} == {None, "addon:x", "addon:y"}
    # Then every repeat runs each arm once: baselines are spread through the batch, not first.
    measured = runs[3:]
    for r in range(5):
        block = measured[r * 3:(r + 1) * 3]
        assert {x.repeat for x in block} == {r} and {x.subject for x in block} == {None, "addon:x", "addon:y"}
    orders = {tuple(x.subject for x in measured[r * 3:(r + 1) * 3]) for r in range(5)}
    assert len(orders) > 1  # shuffled, not the same order every time
    assert [r.key("m") for r in plan_addons([a1, a2], [task()], 5)] == [r.key("m") for r in runs]  # stable on resume
    assert len({r.key("m") for r in runs}) == len(runs)


def test_claude_agent_passes_settings_and_appends_prompt(tmp_path):
    argv_file = tmp_path / "argv.json"
    stub = tmp_path / "claude"
    stub.write_text(f"#!{sys.executable}\nimport json, os, sys\n"
                    f"json.dump({{'argv': sys.argv[1:], 'url': os.environ.get('ANTHROPIC_BASE_URL')}}, "
                    f"open({str(argv_file)!r}, 'w'))\n"
                    "print(json.dumps({'type': 'result', 'is_error': False, 'total_cost_usd': 0.1, "
                    "'num_turns': 2, 'usage': {}}))\n")
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    res = ClaudeAgent("m", binary=str(stub)).run("hi", tmp_path, 30, settings="/x/settings.json",
                                                 env={"ANTHROPIC_BASE_URL": "http://127.0.0.1:9"},
                                                 append_prompt="Be brief.")
    seen = json.loads(argv_file.read_text())
    argv = seen["argv"]
    assert not res.infra_error
    assert argv[argv.index("--settings") + 1] == "/x/settings.json"
    assert argv[argv.index("--append-system-prompt") + 1].endswith("\n\nBe brief.")
    assert seen["url"] == "http://127.0.0.1:9"
    assert "ANTHROPIC_BASE_URL" not in os.environ or os.environ["ANTHROPIC_BASE_URL"] != "http://127.0.0.1:9"


# --- savings verdict ----------------------------------------------------------

def _r(arm, cost, passed=True, tokens=1000, task="t1", subject=None):
    return {"arm": arm, "task": task, "skill": subject, "passed": passed, "skill_triggered": True,
            "infra_error": "", "cost_usd": cost, "input_tokens": tokens, "output_tokens": 50,
            "duration_s": 30.0, "turns": 4}


def test_savings_cheaper_when_whole_range_is_below_zero():
    base = [_r("baseline", c) for c in (0.30, 0.32, 0.28, 0.31, 0.29)]
    with_ = [_r("addon", c) for c in (0.12, 0.14, 0.11, 0.13, 0.15)]
    s = savings(with_, base, delta=0.0)
    assert s["verdict"] == "cheaper" and s["by"] == "cost_usd"
    c = s["metrics"]["cost_usd"]
    assert c["change"] == pytest.approx(0.13 / 0.30 - 1, abs=1e-3)
    assert c["ci"][1] < 0 and c["ci"][0] <= c["change"] <= c["ci"][1]


def test_savings_needs_pass_rate_to_hold():
    base = [_r("baseline", c) for c in (0.30, 0.32, 0.28, 0.31, 0.29)]
    with_ = [_r("addon", c) for c in (0.10, 0.11, 0.12, 0.10, 0.11)]
    assert savings(with_, base, delta=-0.10)["verdict"] == "cheaper"
    assert savings(with_, base, delta=-0.34)["verdict"] == "cheaper, fewer passes"


def test_savings_costlier_same_and_unknown():
    base = [_r("baseline", c) for c in (0.10, 0.11, 0.12, 0.10, 0.11)]
    assert savings([_r("addon", c) for c in (0.30, 0.31, 0.29, 0.30, 0.32)], base, 0.0)["verdict"] == "costlier"
    noisy = [_r("addon", c) for c in (0.05, 0.12, 0.20, 0.08, 0.15)]
    assert savings(noisy, base, 0.0)["verdict"] == "same cost"
    assert savings([_r("addon", 0.1)], base, 0.0)["verdict"] is None  # one run is not enough
    no_cost = [dict(_r("addon", None), input_tokens=t) for t in (400, 420, 410, 405, 415)]
    base_tokens = [dict(_r("baseline", None), input_tokens=t) for t in (1000, 1050, 990, 1010, 1020)]
    s = savings(no_cost, base_tokens, 0.0)
    assert s["by"] == "input_tokens" and s["verdict"] == "cheaper"


def test_three_runs_are_too_few_for_a_savings_verdict():
    # The pilot: 3 runs per arm gave a "cheaper" range that excluded zero for an add-on that
    # never loaded. Three points can't support a range, so no verdict below 5.
    base = [_r("baseline", c) for c in (0.008, 0.009, 0.008)]
    with_ = [_r("addon", c) for c in (0.006, 0.006, 0.007)]
    s = savings(with_, base, 0.0)
    assert s["verdict"] is None and "fewer than 5 runs" in s["note"]
    assert s["metrics"]["cost_usd"]["change"] < 0  # the numbers are still shown


def test_savings_is_deterministic():
    base = [_r("baseline", c) for c in (0.30, 0.20, 0.25, 0.40)]
    with_ = [_r("addon", c) for c in (0.15, 0.30, 0.18, 0.22)]
    assert savings(with_, base, 0.0) == savings(with_, base, 0.0)


def test_summary_pools_savings_across_tasks_of_different_size():
    sk = [{"id": "addon:x", "name": "x", "description": "", "source": "addon", "upfront_tokens": 0,
           "onuse_tokens": 0, "addon": True}]
    tk = [{"id": "small", "title": "", "tags": []}, {"id": "big", "title": "", "tags": []}]
    recs = ([_r("baseline", c, task="small") for c in (0.10, 0.11, 0.09, 0.10, 0.10)]
            + [_r("baseline", c, task="big") for c in (1.00, 1.10, 0.90, 1.00, 1.05)]
            + [_r("addon", c, task="small", subject="addon:x") for c in (0.05, 0.06, 0.05, 0.05, 0.06)]
            + [_r("addon", c, task="big", subject="addon:x") for c in (0.50, 0.55, 0.45, 0.50, 0.52)])
    s = summarize(recs, sk, tk, [])
    entry = s["skills"][0]
    assert entry["savings"]["verdict"] == "cheaper"
    assert entry["savings"]["change"] == pytest.approx(-0.5, abs=0.05)
    assert entry["pass_delta"] == 0.0
    # Always on: no trigger rate, and no "started by the user" note.
    assert all(p["trigger_rate"] is None and not any("started by" in n for n in p["notes"]) for p in s["pairs"])
    assert s["gaps"]["costly_no_lift"] == [] and s["gaps"]["never_triggered"] == []


def test_skill_that_saves_is_not_costly_no_lift():
    sk = [{"id": "p/a", "name": "a", "description": "", "source": "p", "upfront_tokens": 500, "onuse_tokens": 5000}]
    tk = [{"id": "t1", "title": "", "tags": []}]
    recs = ([_r("baseline", c) for c in (0.30, 0.31, 0.29, 0.30, 0.30)]
            + [_r("skill", c, subject="p/a") for c in (0.1, 0.11, 0.09, 0.10, 0.10)])
    s = summarize(recs, sk, tk, [])
    assert s["skills"][0]["verdict"] == "no lift" and s["skills"][0]["savings"]["verdict"] == "cheaper"
    assert s["gaps"]["costly_no_lift"] == []


# --- end to end ---------------------------------------------------------------

def test_cli_compare_end_to_end(tmp_path, capsys):
    cheap = addon(tmp_path / "cheap", {"name": "cheap", "description": "Claims 60% fewer tokens",
                                        "env": {"FAKE_AGENT_COST": "0.1", "FAKE_AGENT_INPUT": "40"}})
    pricey = addon(tmp_path / "pricey", {"name": "pricey", "env": {"FAKE_AGENT_COST": "0.5"}})
    out = tmp_path / "out"
    argv = ["compare", str(cheap), str(pricey), "--out", str(out), "--task", "fix-pagination",
            "--repeats", "5", "--workers", "3", "--yes",
            "--agent-cmd", f"{sys.executable} {FAKE} {{prompt_file}}"]
    assert main(argv) == 0
    printed = capsys.readouterr().out
    assert "cheap: cheaper · cost -60%" in printed and "pricey: costlier · cost +100%" in printed
    assert "control: same cost" in printed and "WARNING" not in printed
    summary = json.loads((out / "summary.json").read_text())
    by = {s["id"]: s for s in summary["skills"]}
    assert by["addon:cheap"]["savings"]["verdict"] == "cheaper"
    assert by["addon:pricey"]["savings"]["verdict"] == "costlier"
    pair = [p for p in summary["pairs"] if p["skill"] == "addon:cheap"][0]
    assert pair["savings"]["metrics"]["input_tokens"]["change"] == pytest.approx(-0.6)
    md = (out / "report.md").read_text()
    assert "## Cost and tokens" in md and "**cheaper**" in md
    assert "Cost and tokens" in (out / "report.html").read_text()
    rows = [json.loads(l) for l in (out / "results.jsonl").read_text().splitlines()]
    # 4 arms (baseline, cheap, pricey, control): 4 warm-ups + 4 x 5 measured runs
    assert len(rows) == 24 and sum(r["arm"] == "warmup" for r in rows) == 4
    assert by["addon:control"]["savings"]["verdict"] == "same cost"
    assert summary["control_warning"] is None
    assert main(argv) == 0  # resume: nothing new
    assert len((out / "results.jsonl").read_text().splitlines()) == 24


def test_cli_compare_refuses_missing_program(tmp_path, capsys):
    a = addon(tmp_path / "a", {"name": "a", "requires": ["no-such-program-xyz"]})
    assert main(["compare", str(a), "--yes", "--agent-cmd", "true"]) == 2
    assert "needs no-such-program-xyz" in capsys.readouterr().err


# --- example add-ons ------------------------------------------------------------

EXAMPLES = Path(__file__).parent.parent / "examples" / "addons"


@pytest.mark.parametrize("name", sorted(d.name for d in EXAMPLES.iterdir() if (d / "addon.json").is_file()))
def test_example_addon_loads(name, tmp_path):
    src = EXAMPLES / name
    spec = json.loads((src / "addon.json").read_text(encoding="utf-8"))
    root = src
    if spec.get("plugin_dir") and not (src / spec["plugin_dir"]).exists():
        # A plugin fetched by hand (gitignored); check everything else loads without it.
        root = tmp_path / name
        shutil.copytree(src, root)
        (root / spec["plugin_dir"]).mkdir()
    a = load_addon(root)
    assert a.name == name and a.description
    if a.requires:  # a real tool: its README records where the install steps came from
        assert (src / "README.md").is_file()
    if a.settings is not None:
        assert "hooks" in json.loads(Path(a.settings_arg()).read_text(encoding="utf-8"))


def test_cli_agent_cmd_with_relative_path_works_as_written(tmp_path, monkeypatch, capsys):
    # The README's command, run from the repo root. Each run happens in a throwaway
    # workspace, so the relative path must be made absolute before it gets there.
    monkeypatch.chdir(FAKE.parent.parent)
    cheap = addon(tmp_path / "cheap", {"name": "cheap", "env": {"FAKE_AGENT_COST": "0.1"}})
    argv = ["compare", str(cheap), "--out", str(tmp_path / "out"), "--task", "fix-pagination",
            "--repeats", "5", "--no-control", "--no-warmup", "--yes",
            "--agent-cmd", "python3 tests/fake_agent.py {prompt_file}"]
    assert main(argv) == 0
    assert "cheap: cheaper" in capsys.readouterr().out
    rows = [json.loads(l) for l in (tmp_path / "out" / "results.jsonl").read_text().splitlines()]
    assert rows and not any(r.get("infra_error") for r in rows)


def test_command_agent_keeps_program_names(tmp_path, monkeypatch):
    from skilllab.cli import _command_agent
    monkeypatch.chdir(tmp_path)
    (tmp_path / "python3").write_text("")  # a stray file named like the program
    (tmp_path / "agent.py").write_text("")
    a = _command_agent("python3 agent.py --flag {prompt_file}")
    assert shlex.split(a.template) == ["python3", str(tmp_path / "agent.py"), "--flag", "{prompt_file}"]


def test_relative_addon_path_reaches_the_agent_as_absolute(tmp_path, monkeypatch):
    # The pilot bug: `skilllab compare examples/addons/rtk` passed a relative --settings and
    # --plugin-dir to an agent running in the workspace, where they don't exist.
    addon(tmp_path / "addons" / "x", {"name": "x", "settings": "settings.json", "plugin_dir": "plugin"},
          {"settings.json": "{}", "plugin/.claude-plugin/plugin.json": "{}"})
    monkeypatch.chdir(tmp_path)
    a = load_addon(Path("addons/x"))
    ws = tmp_path / "elsewhere"
    ws.mkdir()
    monkeypatch.chdir(ws)
    extra = a.install(ws)
    assert Path(extra["settings"]).is_absolute() and Path(extra["settings"]).is_file()
    assert extra["plugin_dirs"][0].is_absolute() and extra["plugin_dirs"][0].is_dir()


def test_control_arm_catches_order_bias(tmp_path):
    # Fake an order effect: the first run of each task is expensive, the rest are cheap,
    # and the control (which changes nothing) happened to run late. It must be flagged.
    sk = [{"id": "addon:control", "name": "control", "description": "", "source": "addon",
           "upfront_tokens": 0, "onuse_tokens": 0, "addon": True, "control": True}]
    tk = [{"id": "t1", "title": "", "tags": []}]
    recs = ([_r("baseline", c) for c in (0.30, 0.31, 0.29, 0.30, 0.30)]
            + [_r("addon", c, subject="addon:control") for c in (0.20, 0.21, 0.19, 0.20, 0.20)])
    s = summarize(recs, sk, tk, [])
    assert "don't trust any cost verdict" in s["control_warning"]
    from skilllab.report import to_markdown
    assert "**Warning.**" in to_markdown(s, "m")


def test_warmup_runs_are_not_counted(tmp_path):
    sk = [{"id": "addon:x", "name": "x", "description": "", "source": "addon",
           "upfront_tokens": 0, "onuse_tokens": 0, "addon": True}]
    tk = [{"id": "t1", "title": "", "tags": []}]
    recs = ([_r("warmup", 5.0), _r("warmup", 5.0, subject="addon:x")]
            + [_r("baseline", 0.3)] * 5 + [_r("addon", 0.3, subject="addon:x")] * 5)
    s = summarize(recs, sk, tk, [])
    assert s["baseline"]["t1"]["n"] == 5 and s["pairs"][0]["n"] == 5
    assert s["skills"][0]["savings"]["verdict"] == "same cost"


def test_tool_calls_and_shell_commands_are_recorded():
    from skilllab.agent import parse_stream
    stream = "\n".join(json.dumps(e) for e in [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {"file_path": "a.py"}},
            {"type": "tool_use", "name": "Bash", "input": {"command": "ls -la"}},
            {"type": "tool_use", "name": "Bash", "input": {"command": "python3 test.py"}}]}},
        {"type": "result", "is_error": False, "total_cost_usd": 0.1, "num_turns": 2, "usage": {}}])
    res = parse_stream(stream)
    assert res.tool_calls == {"Read": 1, "Bash": 2} and res.bash_commands == ["ls", "python3"]

    sk = [{"id": "addon:x", "name": "x", "description": "", "source": "addon",
           "upfront_tokens": 0, "onuse_tokens": 0, "addon": True}]
    tk = [{"id": "t1", "title": "", "tags": []}]
    recs = ([dict(_r("baseline", 0.3), bash_commands=[]) for _ in range(5)]
            + [dict(_r("addon", 0.3, subject="addon:x"), bash_commands=["python3"]) for _ in range(5)])
    pair = summarize(recs, sk, tk, [])["pairs"][0]
    assert pair["bash_calls"] == 1 and pair["base_bash_calls"] == 0 and pair["bash_used"] == ["python3"]
    from skilllab.report import to_markdown
    assert "1 vs 0 (python3)" in to_markdown(summarize(recs, sk, tk, []), "m")
