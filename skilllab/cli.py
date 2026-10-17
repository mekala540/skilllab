"""Command line: skills, plan, run, compare, report, suggest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .agent import ClaudeAgent, CommandAgent, find_claude
from . import relevance
from .lab import to_lab_html
from .report import to_html, to_markdown
from .addons import load_addon
from .runner import final_results, load_results, plan, plan_addons, run_all
from .skills import Skill, load_sources, packs
from .tasks import DEFAULT_SUITE, TIERS, Task, load_suites, matches
from .verdict import DEFAULT_ALPHA, DEFAULT_THRESHOLD, summarize

DEFAULT_MODEL = "claude-sonnet-5-5"
CACHE = Path.home() / ".cache" / "skilllab" / "sources"


def _select(args) -> tuple:
    skills = load_sources(args.sources, CACHE)
    if args.skill:
        skills = [s for s in skills if s.name in args.skill or s.id in args.skill]
    if args.limit_skills:
        skills = skills[: args.limit_skills]
    return skills, _tasks(args)


def _tasks(args) -> List[Task]:
    dirs = ([] if getattr(args, "no_builtin", False) else [DEFAULT_SUITE]) + [Path(p) for p in (args.suite or [])]
    tasks = load_suites(dirs, "all" if args.task else args.tier)
    if args.task:
        tasks = [t for t in tasks if t.id in args.task]
    for t in [t for t in tasks if t.missing()]:
        print(f"skipping {t.id}: needs {', '.join(t.missing())} on PATH", file=sys.stderr)
    return [t for t in tasks if not t.missing()]


def cmd_skills(args) -> int:
    skills, tasks = _select(args)
    for s in skills:
        hit = [t.id for t in tasks if matches(s, t)]
        who = "  (started by a person)" if s.user_invoked else ""
        print(f"{s.id}  ≈{s.upfront_tokens}/{s.onuse_tokens} tokens{who}  candidate tasks: {', '.join(hit) or '—'}")
    print(f"\n{len(skills)} skills, {sum(1 for s in skills if any(matches(s, t) for t in tasks))} with a "
          f"keyword candidate in this suite ({len(tasks)} tasks). `plan` and `run` check whether each "
          "candidate is a fair test before running it.")
    return 0


def _decide(skills: List[Skill], tasks: List[Task], args, path: Optional[Path]) -> Optional[dict]:
    """Relevance decisions for skill/task pairs, cached in matches.json (see relevance.py)."""
    if args.all_tasks or args.pack:
        return None
    known = relevance.load(path)
    judge = None
    if not args.no_judge and not getattr(args, "agent_cmd", None):
        if find_claude():
            judge = relevance.claude_judge()
        else:
            print("claude CLI not found: using keyword matches without a relevance check", file=sys.stderr)
    decisions, cost = relevance.decide(skills, tasks, known, judge, args.pair)
    if cost:
        print(f"Relevance check: ${cost:.3f}")
    if path:
        relevance.save(path, decisions)
    return decisions


def _plan_text(skills: List[Skill], tasks: List[Task], args, decisions: Optional[dict] = None) -> tuple:
    if args.pack:
        pack_list = packs(skills)
        runs, untested = plan(skills, tasks, args.repeats, pack_list=pack_list)
        base = sum(1 for r in runs if r.arm == "baseline")
        lines = [f"{len(pack_list)} packs (whole), each on all {len(tasks)} tasks",
                 f"{len(runs)} runs = {base} baseline + {len(runs) - base} with a pack ({args.repeats} repeats each)"]
        plugins = [p.source for p in pack_list if p.plugin]
        if plugins:
            lines.append(f"Loaded as Claude Code plugins, so their hooks run on this machine: "
                         f"{', '.join(plugins)}. Check them first (e.g. with skillprint).")
        return runs, untested, lines
    relevant = relevance.relevant_pairs(decisions) if decisions is not None else None
    runs, untested = plan(skills, tasks, args.repeats, args.all_tasks, relevant=relevant)
    base = sum(1 for r in runs if r.skill is None)
    tested = len(skills) - len(untested)
    lines = [f"{len(skills)} skills · {tested} with a task that fairly tests them · {len(untested)} untested"]
    if decisions is not None:
        turned_down = sum(1 for d in decisions.values() if not d.get("relevant"))
        lines.append(f"{turned_down} keyword candidates turned down as not a fair test (see matches.json)")
    lines.append(f"{len(runs)} runs = {base} baseline + {len(runs) - base} with a skill "
                 f"({args.repeats} repeats each)")
    return runs, untested, lines


def cmd_plan(args) -> int:
    skills, tasks = _select(args)
    decisions = _decide(skills, tasks, args, Path(args.matches) if args.matches else None)
    _, _, lines = _plan_text(skills, tasks, args, decisions)
    print("\n".join(lines))
    print("Every run is one full agent session. Set --budget on `run` to cap spend.")
    return 0


def _write_reports(out: Path, model: str, threshold: float, alpha: float = DEFAULT_ALPHA) -> dict:
    meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
    lines = load_results(out / "results.jsonl")
    records = final_results(lines)
    summary = summarize(records, meta["skills"], meta["tasks"], meta["untested"], threshold, alpha,
                        matches=meta.get("matches"))
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / "report.md").write_text(to_markdown(summary, model), encoding="utf-8")
    (out / "report.html").write_text(to_html(summary, model), encoding="utf-8")
    (out / "lab.html").write_text(to_lab_html(summary, records, meta, len(lines)), encoding="utf-8")
    return summary


def cmd_run(args) -> int:
    skills, tasks = _select(args)
    out = Path(args.out)
    decisions = _decide(skills, tasks, args, Path(args.matches) if args.matches else out / "matches.json")
    runs, untested, lines = _plan_text(skills, tasks, args, decisions)
    print("\n".join(lines))
    if not runs:
        print("Nothing to run: no task fairly tests these skills. See matches.json, use --pair "
              "skill:task, or `skilllab suggest`.")
        return 1
    if args.agent_cmd:
        agent = CommandAgent(args.agent_cmd)
    else:
        if not find_claude():
            print("claude CLI not found. Install Claude Code or pass --agent-cmd.", file=sys.stderr)
            return 2
        agent = ClaudeAgent(args.model, max_budget_usd=args.run_budget)
        print(f"Agent: Claude Code, model {args.model}, budget ${args.budget:.2f} for this batch")
    if not args.yes and sys.stdin.isatty():
        if input("Start? [y/N] ").strip().lower() != "y":
            return 1
    out.mkdir(parents=True, exist_ok=True)
    meta = {
        "model": args.model if not args.agent_cmd else f"cmd:{args.agent_cmd}",
        "mode": "pack" if args.pack else "skill",
        "skills": [p.meta() for p in packs(skills)] if args.pack else [s.meta() for s in skills],
        "tasks": [t.meta() for t in tasks],
        "untested": [s.id for s in untested],
        "matches": decisions or {},
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    budget = None if args.agent_cmd else args.budget
    (out / "results.jsonl").touch()
    _write_reports(out, meta["model"], args.threshold, args.alpha)  # so the live view has the ring
    if args.watch:
        serve(out)
    run_all(runs, agent, meta["model"], out / "results.jsonl", workers=args.workers,
            budget_usd=budget, keep=args.keep)
    summary = _write_reports(out, meta["model"], args.threshold, args.alpha)
    counts = {}
    for s in summary["skills"]:
        counts[s["verdict"]] = counts.get(s["verdict"], 0) + 1
    print("\n" + ", ".join(f"{v}: {n}" for v, n in sorted(counts.items())) if counts else "")
    print(f"Report: {out / 'report.md'}  ·  {out / 'report.html'}  ·  replay: {out / 'lab.html'}")
    return 0


def cmd_compare(args) -> int:
    """Each add-on on every task against a shared baseline: cost, tokens, time, pass rate."""
    try:
        addons = [load_addon(Path(p)) for p in args.addons]
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    names = [a.name for a in addons]
    if len(set(names)) != len(names):
        print("two add-ons share a name; names must be unique", file=sys.stderr)
        return 2
    missing = {a.name: a.missing() for a in addons if a.missing()}
    if missing:
        for name, progs in missing.items():
            print(f"add-on {name} needs {', '.join(progs)} on PATH", file=sys.stderr)
        return 2
    tasks = _tasks(args)
    if not tasks:
        print("no tasks selected", file=sys.stderr)
        return 1
    runs = plan_addons(addons, tasks, args.repeats)
    print(f"{len(addons)} add-on{'s' if len(addons) != 1 else ''} × {len(tasks)} tasks × {args.repeats} repeats, "
          f"plus {len(tasks) * args.repeats} shared baseline runs = {len(runs)} runs")
    if args.agent_cmd:
        agent = CommandAgent(args.agent_cmd)
    else:
        if not find_claude():
            print("claude CLI not found. Install Claude Code or pass --agent-cmd.", file=sys.stderr)
            return 2
        agent = ClaudeAgent(args.model, max_budget_usd=args.run_budget)
        print(f"Agent: Claude Code, model {args.model}, budget ${args.budget:.2f} for this batch")
    if not args.yes and sys.stdin.isatty():
        if input("Start? [y/N] ").strip().lower() != "y":
            return 1
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    meta = {
        "model": args.model if not args.agent_cmd else f"cmd:{args.agent_cmd}",
        "mode": "addon",
        "skills": [a.meta() for a in addons],
        "tasks": [t.meta() for t in tasks],
        "untested": [],
        "matches": {},
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (out / "results.jsonl").touch()
    _write_reports(out, meta["model"], args.threshold, args.alpha)
    if args.watch:
        serve(out)
    run_all(runs, agent, meta["model"], out / "results.jsonl", workers=args.workers,
            budget_usd=None if args.agent_cmd else args.budget, keep=args.keep)
    summary = _write_reports(out, meta["model"], args.threshold, args.alpha)
    print()
    for s in summary["skills"]:
        print(_savings_line(s))
    print(f"Report: {out / 'report.md'}  ·  {out / 'report.html'}  ·  replay: {out / 'lab.html'}")
    return 0


def _savings_line(s: dict) -> str:
    from .report import _change, _delta
    sv = s.get("savings") or {}
    if not sv.get("verdict"):
        return f"{s['name']}: not enough data for a cost comparison"
    what = "cost" if sv["by"] == "cost_usd" else "input tokens"
    return (f"{s['name']}: {sv['verdict']} · {what} {_change(sv['change'], sv['ci'])} · "
            f"pass rate {_delta(s.get('pass_delta'))} vs baseline")


# A task can only show lift if the agent sometimes fails it without help.
GOOD_BAND = (0.0, 0.6)


def cmd_calibrate(args) -> int:
    """Run tasks without any skill to see how hard they are for this model."""
    from .runner import Run
    tasks = _tasks(args)
    runs = [Run(t, None, r) for t in tasks for r in range(args.repeats)]
    print(f"{len(tasks)} tasks x {args.repeats} baseline runs = {len(runs)} runs, budget ${args.budget:.2f}")
    agent = CommandAgent(args.agent_cmd) if args.agent_cmd else ClaudeAgent(args.model, max_budget_usd=args.run_budget)
    if not args.agent_cmd and not find_claude():
        print("claude CLI not found. Install Claude Code or pass --agent-cmd.", file=sys.stderr)
        return 2
    if not args.yes and sys.stdin.isatty() and input("Start? [y/N] ").strip().lower() != "y":
        return 1
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    model = f"cmd:{args.agent_cmd}" if args.agent_cmd else args.model
    run_all(runs, agent, model, out / "results.jsonl", workers=args.workers,
            budget_usd=None if args.agent_cmd else args.budget)
    rows = []
    for t in tasks:
        recs = [r for r in final_results(load_results(out / "results.jsonl"))
                if r["task"] == t.id and r["arm"] == "baseline" and not r.get("infra_error")]
        rate = sum(r["passed"] for r in recs) / len(recs) if recs else None
        if rate is None:
            label = "no data"
        elif rate == 0:
            label = "very hard: check a solution exists, or keep as 'nobody solves'"
        elif rate <= GOOD_BAND[1]:
            label = "good: room for a skill to help"
        else:
            label = "too easy for this model"
        cost = sorted(r.get("cost_usd") or 0 for r in recs)
        rows.append((t.id, t.tier, len(recs), rate, cost[len(cost) // 2] if cost else None, label))
    lines = ["| Task | Tier | Runs | Baseline pass | Median cost | Verdict |", "| --- | --- | --- | --- | --- | --- |"]
    lines += [f"| {i} | {tier} | {n} | {'–' if r is None else f'{round(r * 100)}%'} | "
              f"{'–' if c is None else f'${c:.2f}'} | {label} |" for i, tier, n, r, c, label in rows]
    (out / "calibration.md").write_text(f"# Calibration ({model})\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nSaved {out / 'calibration.md'}")
    return 0


CHECK_TEMPLATE = '''"""Checker for {id}. Runs in the workspace after the agent finishes; exit 0 = pass.

Describe what a correct answer must do, and what a lazy one would do that must fail.
"""

import sys


def main():
    # TODO: check the agent's work. Print one line saying why it passed or failed.
    print("FAIL: checker not written yet")
    return 1


if __name__ == "__main__":
    sys.exit(main())
'''


def cmd_new_task(args) -> int:
    """Scaffold a task so contributors only write the interesting parts."""
    import re as _re
    tid = args.id
    if not _re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", tid):
        print("task id must be kebab-case, e.g. fix-date-parsing", file=sys.stderr)
        return 2
    suite = Path(args.suite or DEFAULT_SUITE)
    tests_root = Path(args.tests)
    spec_path = suite / "tasks" / f"{tid}.json"
    if spec_path.exists():
        print(f"{spec_path} already exists", file=sys.stderr)
        return 1
    fixture, hidden = suite / "fixtures" / tid, suite / "fixtures" / f"{tid}-hidden"
    for d in (fixture, hidden, tests_root / "solutions" / tid, tests_root / "shallow" / tid):
        d.mkdir(parents=True, exist_ok=True)
    (fixture / "README.md").write_text(f"# {tid}\n\nStarting files the agent sees. Replace this.\n", encoding="utf-8")
    check = hidden / f"check_{tid.replace('-', '_')}.py"
    check.write_text(CHECK_TEMPLATE.format(id=tid), encoding="utf-8")
    spec = {
        "id": tid, "status": "draft", "tier": "standard", "title": "TODO: one line",
        "tags": ["TODO: words skills use, e.g. debugging"],
        "fixture": f"fixtures/{tid}", "hidden": f"fixtures/{tid}-hidden",
        "prompt": "TODO: what the agent is told",
        "check": "{python} " + check.name, "protect": [], "timeout": 900,
    }
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    print(f"""Created task {tid} (status: draft, ignored until you remove that line).

  {spec_path}            prompt, tags, check command
  {fixture}/        what the agent starts with
  {check}  pass/fail logic
  {tests_root / 'solutions' / tid}/   a correct solution (must pass)
  {tests_root / 'shallow' / tid}/     a plausible quick fix (must fail)

Then: pytest -q, and `skilllab calibrate --task {tid}` to check it isn't too easy.""")
    return 0


def serve(out: Path, open_browser: bool = True):
    """Serve a results folder on localhost so lab.html can poll results.jsonl."""
    import functools
    import threading
    import webbrowser
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(out)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{httpd.server_address[1]}/lab.html?live"
    print(f"Live view: {url}")
    if open_browser:
        webbrowser.open(url)
    return httpd


def cmd_watch(args) -> int:
    out = Path(args.out)
    if not (out / "lab.html").exists():
        print(f"{out}/lab.html not found. Start a run with --out {out} first.", file=sys.stderr)
        return 1
    serve(out, not args.no_open)
    print("Watching. Ctrl-C to stop.")
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        return 0


def cmd_report(args) -> int:
    out = Path(args.out)
    meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
    _write_reports(out, meta["model"], args.threshold, args.alpha)
    print(f"Report: {out / 'report.md'}  ·  {out / 'report.html'}  ·  replay: {out / 'lab.html'}")
    return 0


def cmd_suggest(args) -> int:
    from .suggest import suggest
    skills, tasks = _select(args)
    known = relevance.load(Path(args.matches)) if args.matches else {}
    if known:  # a skill whose only candidates were turned down is untested too
        fair = {sid for sid, _ in relevance.relevant_pairs(known)}
        untested = [s for s in skills if s.id not in fair]
    else:
        untested = [s for s in skills if not any(matches(s, t) for t in tasks)]
    print(f"{len(untested)} skills have no matching task; drafting one each with {args.model}")
    n = suggest(untested, args.model, Path(args.out))
    print(f"{n} drafts in {args.out}. Each needs review: the fixture must fail the check and a "
          "correct solution must pass it. Then move it into the suite and drop \"status\": \"draft\".")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="skilllab", description=__doc__)
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("sources", nargs="+", help="skill folders or git URLs")
    common.add_argument("--suite", action="append",
                        help="extra task suite folder, added to the built-in one (repeatable)")
    common.add_argument("--no-builtin", action="store_true", help="don't load the built-in suite")
    common.add_argument("--task", action="append", help="only this task id (repeatable)")
    common.add_argument("--tier", choices=TIERS, default="standard",
                        help="task tier (default standard; easy is for smoke tests)")
    common.add_argument("--skill", action="append", help="only this skill name or id (repeatable)")
    common.add_argument("--limit-skills", type=int, help="only the first N skills")
    common.add_argument("--repeats", type=int, default=3)
    common.add_argument("--all-tasks", action="store_true",
                        help="test every skill on every task, skipping the relevance check")
    common.add_argument("--pack", action="store_true",
                        help="test each source as a whole pack, installed the way users install it "
                             "(as a Claude Code plugin with its hooks, when it is one), on every task")
    common.add_argument("--pair", action="append", metavar="SKILL:TASK",
                        help="run this skill on this task whatever the relevance check says (repeatable)")
    common.add_argument("--no-judge", action="store_true",
                        help="skip the relevance check; every keyword match counts")
    common.add_argument("--matches", help="relevance decisions file to read and update "
                                          "(run: default <out>/matches.json)")

    sub.add_parser("skills", parents=[common], help="list skills and the tasks that test them").set_defaults(fn=cmd_skills)
    sub.add_parser("plan", parents=[common], help="show how many runs a batch needs").set_defaults(fn=cmd_plan)

    r = sub.add_parser("run", parents=[common], help="run the batch and write reports")
    r.add_argument("--out", default="results")
    r.add_argument("--model", default=DEFAULT_MODEL)
    r.add_argument("--workers", type=int, default=4, help="agents running at once")
    r.add_argument("--budget", type=float, default=5.0, help="total USD for this results folder (earlier runs count); stops starting new runs once reached")
    r.add_argument("--run-budget", type=float, default=1.0, help="USD cap per single run")
    r.add_argument("--agent-cmd", help="use this command instead of Claude Code ({prompt_file})")
    r.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                   help="smallest pass-rate change that counts (default 0.3)")
    r.add_argument("--alpha", type=float, default=DEFAULT_ALPHA,
                   help="significance level for Fisher's exact test (default 0.1)")
    r.add_argument("--keep", action="store_true", help="keep workspaces for inspection")
    r.add_argument("--yes", action="store_true", help="don't ask before starting")
    r.add_argument("--watch", action="store_true", help="open the live lab view while it runs")
    r.set_defaults(fn=cmd_run)

    cal = sub.add_parser("calibrate", help="measure how hard each task is (baseline only)")
    cal.add_argument("--suite", action="append")
    cal.add_argument("--no-builtin", action="store_true")
    cal.add_argument("--task", action="append")
    cal.add_argument("--tier", choices=TIERS, default="standard")
    cal.add_argument("--repeats", type=int, default=3)
    cal.add_argument("--out", default="results/calibration")
    cal.add_argument("--model", default=DEFAULT_MODEL)
    cal.add_argument("--workers", type=int, default=4)
    cal.add_argument("--budget", type=float, default=5.0)
    cal.add_argument("--run-budget", type=float, default=1.0)
    cal.add_argument("--agent-cmd")
    cal.add_argument("--yes", action="store_true")
    cal.set_defaults(fn=cmd_calibrate)

    nt = sub.add_parser("new-task", help="scaffold a new task")
    nt.add_argument("id", help="kebab-case task id")
    nt.add_argument("--suite", help="suite folder (default: the built-in suite)")
    nt.add_argument("--tests", default="tests", help="where solutions/ and shallow/ live")
    nt.set_defaults(fn=cmd_new_task)

    w = sub.add_parser("watch", help="live lab view of a running (or finished) batch")
    w.add_argument("out")
    w.add_argument("--no-open", action="store_true", help="print the URL without opening a browser")
    w.set_defaults(fn=cmd_watch)

    rep = sub.add_parser("report", help="rebuild reports from a results folder")
    rep.add_argument("out")
    rep.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    rep.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    rep.set_defaults(fn=cmd_report)

    cmp_ = sub.add_parser("compare", help="measure add-ons (token savers, memory, prompts): cost, tokens, pass rate")
    cmp_.add_argument("addons", nargs="+", help="add-on folders, each with an addon.json")
    cmp_.add_argument("--suite", action="append", help="extra task suite folder (repeatable)")
    cmp_.add_argument("--no-builtin", action="store_true", help="don't load the built-in suite")
    cmp_.add_argument("--task", action="append", help="only this task id (repeatable)")
    cmp_.add_argument("--tier", choices=TIERS, default="standard")
    cmp_.add_argument("--repeats", type=int, default=5)
    cmp_.add_argument("--out", default="results/compare")
    cmp_.add_argument("--model", default=DEFAULT_MODEL)
    cmp_.add_argument("--workers", type=int, default=4)
    cmp_.add_argument("--budget", type=float, default=5.0)
    cmp_.add_argument("--run-budget", type=float, default=1.0)
    cmp_.add_argument("--agent-cmd", help="use this command instead of Claude Code ({prompt_file})")
    cmp_.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    cmp_.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    cmp_.add_argument("--keep", action="store_true")
    cmp_.add_argument("--yes", action="store_true")
    cmp_.add_argument("--watch", action="store_true")
    cmp_.set_defaults(fn=cmd_compare)

    sg = sub.add_parser("suggest", parents=[common], help="draft tasks for untested skills")
    sg.add_argument("--out", default="drafts")
    sg.add_argument("--model", default=DEFAULT_MODEL)
    sg.set_defaults(fn=cmd_suggest)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
