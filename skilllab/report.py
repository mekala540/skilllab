"""Markdown and HTML reports from a summary."""

from __future__ import annotations

import html
from typing import Optional

GAP_TITLES = {
    "costly_no_lift": ("Costs context, no measurable lift",
                       "Loaded tokens without moving the pass rate. Candidates to trim or drop."),
    "never_triggered": ("Never triggered",
                        "The agent never invoked the skill on tasks that match its claim. "
                        "The description may not say when to use it."),
    "hurts": ("Made the agent worse", "Pass rate dropped with the skill on at least one task."),
    "ceiling_tasks": ("Tasks too easy to measure",
                      "Baseline already passes every time, so no skill can show lift. Add a harder task."),
    "unsolved_tasks": ("Nobody solves these",
                       "Fails without skills and no skill helped. An opening for a new skill."),
    "untested_claims": ("Claims with no task",
                        "No task in the suite matches these skills. Run `skilllab suggest` to draft tasks."),
    "needs_person": ("Needs a person in the loop",
                     "Built around a conversation (grilling, teaching, hand-offs). An unattended run "
                     "can't judge these; they need human evaluation."),
    "lookalikes": ("Look-alike skills across repos", "Descriptions overlap heavily. One good one may do."),
}


def _pct(x: Optional[float]) -> str:
    return "–" if x is None else f"{round(x * 100)}%"


def _delta(x: Optional[float]) -> str:
    return "–" if x is None else f"{'+' if x > 0 else ''}{round(x * 100)} pts"


def _ci(rate, ci) -> str:
    if rate is None:
        return "–"
    return f"{round(rate * 100)}%" + (f" [{round(ci[0] * 100)}–{round(ci[1] * 100)}]" if ci else "")


def _p(x: Optional[float]) -> str:
    return "–" if x is None else f"{x:.2f}"


def _money(x: Optional[float]) -> str:
    return "–" if x is None else f"${x:.3f}"


def _gap_item(key: str, item) -> str:
    if key in ("ceiling_tasks", "unsolved_tasks"):
        return f"`{item}`"
    if key == "lookalikes":
        return f"`{item['a']}` ≈ `{item['b']}` ({round(item['similarity'] * 100)}% word overlap)"
    return f"`{item['id']}` (≈{item['upfront_tokens']} tokens up front, ≈{item['onuse_tokens']} on use)"


def to_markdown(summary: dict, model: str) -> str:
    out = ["# skilllab report", ""]
    out.append(f"Model `{model}` · {summary['runs']} runs · {summary['errors']} infrastructure errors "
               f"(excluded) · ${summary['cost_usd']:.2f} spent · a verdict needs a change of at least "
               f"{round(summary['threshold'] * 100)} pts and Fisher's exact p ≤ {summary.get('alpha', 0.1)}")
    out += ["", "## Verdicts", "",
            "| Skill | Verdict | Tasks | Triggered | Tokens up front | Tokens on use |",
            "| --- | --- | --- | --- | --- | --- |"]
    for s in sorted(summary["skills"], key=lambda s: (s["verdict"], s["id"])):
        out.append(f"| `{s['id']}` | **{s['verdict']}** | {', '.join(s['tasks'])} | "
                   f"{_pct(s['trigger_rate'])} | ≈{s['upfront_tokens']} | ≈{s['onuse_tokens']} |")
    out += ["", "## Per task", "",
            "Pass rates show a 90% confidence interval in brackets. Cost per pass = total spend / passing runs.",
            "",
            "| Skill | Task | n | Pass with | Pass without | Lift | p | Cost/pass with | Cost/pass without | Notes |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for p in summary["pairs"]:
        out.append(f"| `{p['skill']}` | {p['task']} | {p['n']} | {_ci(p['with_rate'], p.get('ci'))} | "
                   f"{_ci(p['base_rate'], p.get('base_ci'))} | {_delta(p['delta'])} | {_p(p.get('p_value'))} | "
                   f"{_money(p.get('cost_per_pass'))} | {_money(p.get('base_cost_per_pass'))} | "
                   f"{'; '.join(p['notes'])} |")
    out += ["", "## Gaps", ""]
    for key, (title, why) in GAP_TITLES.items():
        items = summary["gaps"].get(key) or []
        if not items:
            continue
        out += [f"### {title} ({len(items)})", "", why, ""]
        out += [f"- {_gap_item(key, i)}" for i in items[:25]]
        if len(items) > 25:
            out.append(f"- …and {len(items) - 25} more")
        out.append("")
    out += ["## How to read this", "",
            "- Each run starts from a fresh copy of the task's files. The skill is installed in "
            "`.claude/skills/` for the *with* arm only. Pass/fail comes from hidden checks copied in "
            "after the agent finishes.",
            "- **Small samples.** With 3 repeats, only a 3-of-3 vs 0-of-3 split is significant. "
            "Use `--repeats 5` or more before telling a maintainer their skill doesn't help.",
            "- **Many comparisons.** Testing many skills means a few will look significant by chance. "
            "Rerun surprising results before acting on them.",
            "- A verdict is about *these tasks on this model*, not the skill in general.", ""]
    return "\n".join(out)


def to_html(summary: dict, model: str) -> str:
    e = html.escape
    rows = "".join(
        f"<tr><td><code>{e(s['id'])}</code><div class=d>{e(s['description'][:180])}</div></td>"
        f"<td><span class='v v-{e(s['verdict'].replace(' ', '-'))}'>{e(s['verdict'])}</span></td>"
        f"<td>{e(', '.join(s['tasks']))}</td><td>{_pct(s['trigger_rate'])}</td>"
        f"<td class=n>≈{s['upfront_tokens']}</td><td class=n>≈{s['onuse_tokens']}</td></tr>"
        for s in sorted(summary["skills"], key=lambda s: (s["verdict"], s["id"])))
    pair_rows = "".join(
        f"<tr><td><code>{e(p['skill'])}</code></td><td>{e(p['task'])}</td>"
        f"<td class=n>{_pct(p['with_rate'])}</td><td class=n>{_pct(p['base_rate'])}</td>"
        f"<td class=n>{_delta(p['delta'])}</td><td class=n>{_p(p.get('p_value'))}</td><td>{e('; '.join(p['notes']))}</td></tr>"
        for p in summary["pairs"])
    gaps = ""
    for key, (title, why) in GAP_TITLES.items():
        items = summary["gaps"].get(key) or []
        if items:
            lis = "".join(f"<li>{e(_gap_item(key, i)).replace('`', '')}</li>" for i in items[:25])
            gaps += f"<section class=gap><h3>{e(title)} <span>{len(items)}</span></h3><p>{e(why)}</p><ul>{lis}</ul></section>"
    return f"""<!doctype html>
<html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Skill Lab Report</title>
<style>
:root{{--bg:#fafaf9;--fg:#1c1917;--mut:#57534e;--line:#e7e5e4;--card:#fff;
--helps:#15803d;--hurts:#b91c1c;--flag:#b45309;--none:#57534e}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0c0a09;--fg:#f5f5f4;--mut:#a8a29e;--line:#292524;--card:#1c1917;
--helps:#4ade80;--hurts:#f87171;--flag:#fbbf24;--none:#a8a29e}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0;padding:24px 16px}}
main{{max-width:1100px;margin:auto}} h1{{margin:0 0 4px}} .meta{{color:var(--mut)}}
.wrap{{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:8px;margin:12px 0 28px}}
table{{border-collapse:collapse;width:100%}} th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut)}} .n{{text-align:right;white-space:nowrap}}
.d{{color:var(--mut);font-size:13px}} code{{font-size:13px}}
.v{{font-weight:600;white-space:nowrap}} .v-helps{{color:var(--helps)}} .v-hurts,.v-mixed{{color:var(--hurts)}}
.v-flagged{{color:var(--flag)}} .v-no-lift{{color:var(--none)}}
.gap{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:4px 16px;margin:12px 0}}
.gap h3 span{{color:var(--mut);font-weight:400}} .gap p{{color:var(--mut);margin-top:0}}
</style></head><body><main>
<h1>Skill Lab report</h1>
<p class=meta>Model {e(model)} · {summary['runs']} runs · {summary['errors']} infrastructure errors excluded ·
${summary['cost_usd']:.2f} spent · verdicts need ≥{round(summary['threshold'] * 100)} pts and Fisher p ≤ {summary.get('alpha', 0.1)}. Small samples show direction, not proof.</p>
<h2>Verdicts</h2><div class=wrap><table><tr><th>Skill</th><th>Verdict</th><th>Tasks</th><th>Triggered</th><th class=n>Up front</th><th class=n>On use</th></tr>{rows}</table></div>
<h2>Per task</h2><div class=wrap><table><tr><th>Skill</th><th>Task</th><th class=n>With</th><th class=n>Without</th><th class=n>Lift</th><th class=n>p</th><th>Notes</th></tr>{pair_rows}</table></div>
<h2>Gaps</h2>{gaps or '<p class=meta>None found.</p>'}
</main></body></html>
"""
