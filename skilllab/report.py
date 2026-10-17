"""Markdown and HTML reports from a summary."""

from __future__ import annotations

import html
from typing import Optional

from .verdict import SAVINGS_GUARD

GAP_TITLES = {
    "costly_no_lift": ("Costs context, no measurable lift",
                       "Loaded tokens without moving the pass rate. Candidates to trim or drop."),
    "never_triggered": ("Relevant but never used",
                        "The agent could have invoked the skill and the task was judged a fair test of "
                        "it, but the agent never did. The description may not say clearly when to use it."),
    "hurts": ("Made the agent worse", "Pass rate dropped with the skill on at least one task."),
    "ceiling_tasks": ("Tasks too easy to measure",
                      "Baseline already passes every time, so no skill can show lift. Add a harder task."),
    "unsolved_tasks": ("Nobody solves these",
                       "Fails without skills and no skill helped. An opening for a new skill."),
    "untested_claims": ("Claims with no task",
                        "No task in the suite is a fair test of these skills, so nothing is known about "
                        "them (not the same as \"not needed\"). Keyword candidates the relevance check "
                        "turned down are in matches.json. Run `skilllab suggest` to draft tasks."),
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


def _change(x: Optional[float], ci=None) -> str:
    """A relative change: -0.42 -> "-42% [-55 to -30]"."""
    if x is None:
        return "–"
    txt = f"{'+' if x > 0 else ''}{round(x * 100)}%"
    if ci:
        txt += f" [{round(ci[0] * 100)} to {round(ci[1] * 100)}]"
    return txt


def _num(x: Optional[float], metric: str) -> str:
    if x is None:
        return "–"
    if metric == "cost_usd":
        return f"${x:.3f}"
    if metric == "duration_s":
        return f"{x:.0f}s"
    return f"{x:,.0f}"


METRIC_LABELS = {"cost_usd": "Cost", "input_tokens": "Input tokens", "output_tokens": "Output tokens",
                 "duration_s": "Time", "turns": "Turns"}


def _bash(p: dict) -> str:
    """Median shell commands per run, with vs without, and which programs the with-arm ran."""
    if p.get("bash_calls") is None:
        return "–"
    used = ", ".join(p.get("bash_used") or [])
    return f"{p['bash_calls']:g} vs {p.get('base_bash_calls') or 0:g}" + (f" ({used})" if used else "")


def _has_savings(summary: dict) -> bool:
    return any((p.get("savings") or {}).get("metrics") for p in summary["pairs"])


def _savings_md(summary: dict) -> list:
    out = ["## Cost and tokens", ""]
    if summary.get("control_warning"):
        out += [f"> **Warning.** {summary['control_warning']}", ""]
    out += [
           "Median per run, with vs without, over all valid runs (passed or not). The range is a 90% "
           "bootstrap interval for the change. **cheaper** needs the whole range below zero and a pass "
           f"rate that didn't drop by more than {round(SAVINGS_GUARD * 100)} pts.", "",
           "The `addon:control` row changes nothing; it should say *same cost*. If it doesn't, the batch is biased.",
           "",
           "| Subject | Cost/tokens verdict | Change | Pass rate change | Tasks |",
           "| --- | --- | --- | --- | --- |"]
    for s in summary["skills"]:
        sv = s.get("savings") or {}
        what = {"cost_usd": "cost", "input_tokens": "input tokens"}.get(sv.get("by"), "")
        out.append(f"| `{s['id']}` | **{sv.get('verdict') or sv.get('note') or '–'}** | {what} {_change(sv.get('change'), sv.get('ci'))} | "
                   f"{_delta(s.get('pass_delta'))} | {len(s['tasks'])} |")
    out += ["", "*Shell commands*: median Bash calls per run, with vs without, and the programs run. "
            "An add-on that acts on shell output (a command rewriter) can only save anything where this is above zero.", "",
            "| Subject | Task | " + " | ".join(METRIC_LABELS.values()) + " | Shell commands | Verdict |",
            "| --- | --- | " + " | ".join("---" for _ in METRIC_LABELS) + " | --- | --- |"]
    for p in summary["pairs"]:
        sv = p.get("savings") or {}
        cells = []
        for m in METRIC_LABELS:
            d = (sv.get("metrics") or {}).get(m)
            cells.append(f"{_num(d['with'], m)} vs {_num(d['base'], m)} ({_change(d['change'])})" if d else "–")
        out.append(f"| `{p['skill']}` | {p['task']} | " + " | ".join(cells)
                   + f" | {_bash(p)} | {sv.get('verdict') or sv.get('note') or '–'} |")
    out.append("")
    return out


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
            "| Skill | Task | n | Pass with | Pass without | Lift | p | Cost/pass with | Cost/pass without | Why this pair | Notes |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for p in summary["pairs"]:
        out.append(f"| `{p['skill']}` | {p['task']} | {p['n']} | {_ci(p['with_rate'], p.get('ci'))} | "
                   f"{_ci(p['base_rate'], p.get('base_ci'))} | {_delta(p['delta'])} | {_p(p.get('p_value'))} | "
                   f"{_money(p.get('cost_per_pass'))} | {_money(p.get('base_cost_per_pass'))} | "
                   f"{p.get('match') or '–'} | {'; '.join(p['notes'])} |")
    if _has_savings(summary):
        out += [""] + _savings_md(summary)
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
            "`.claude/skills/` for the *with* arm only (a whole pack loads as a plugin, with its hooks). "
            "Pass/fail comes from hidden checks copied in after the agent finishes.",
            "- A skill is only run on tasks judged a fair test of it (see *Why this pair* and "
            "matches.json). Skills only a person can start (`disable-model-invocation`) are started "
            "with `/name` and have no trigger rate.",
            "- **Small samples.** With 3 repeats, only a 3-of-3 vs 0-of-3 split is significant. "
            "Use `--repeats 5` or more before telling a maintainer their skill doesn't help.",
            "- **Many comparisons.** Testing many skills means a few will look significant by chance. "
            "Rerun surprising results before acting on them.",
            "- **Cost and tokens** are what Claude Code reports for each run (input counts cached reads). "
            "They are measured on every run, so a saving shows even when both arms always pass. Prices "
            "and caching change, so compare within one report, not across months.",
            "- A verdict is about *these tasks on this model*, not the skill in general. Other models "
            "(larger or smaller) may use skills differently.",
            "- Built-in tasks are short samples (a few files, a clear prompt, a fixed check), not real "
            "project work. Long, vague, multi-step work on a real codebase may give different results.", ""]
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
        f"<td class=n>{_delta(p['delta'])}</td><td class=n>{_p(p.get('p_value'))}</td>"
        f"<td class=d>{e(p.get('match') or '–')}</td><td>{e('; '.join(p['notes']))}</td></tr>"
        for p in summary["pairs"])
    cost_html = ""
    if _has_savings(summary):
        srows = ""
        for s in summary["skills"]:
            sv = s.get("savings") or {}
            what = {"cost_usd": "cost", "input_tokens": "input tokens"}.get(sv.get("by"), "")
            v = sv.get("verdict") or sv.get("note") or "–"
            cls = {"cheaper": "helps", "costlier": "hurts", "cheaper, fewer passes": "flagged"}.get(v, "no-lift")
            srows += (f"<tr><td><code>{e(s['id'])}</code></td><td><span class='v v-{cls}'>{e(v)}</span></td>"
                      f"<td class=n>{e(what)} {e(_change(sv.get('change'), sv.get('ci')))}</td>"
                      f"<td class=n>{e(_delta(s.get('pass_delta')))}</td></tr>")
        prow = ""
        for p in summary["pairs"]:
            sv = p.get("savings") or {}
            cells = ""
            for m in METRIC_LABELS:
                d = (sv.get("metrics") or {}).get(m)
                cells += (f"<td class=n>{e(_num(d['with'], m))}<div class=d>vs {e(_num(d['base'], m))} · "
                          f"{e(_change(d['change']))}</div></td>") if d else "<td class=n>–</td>"
            prow += (f"<tr><td><code>{e(p['skill'])}</code></td><td>{e(p['task'])}</td>{cells}"
                     f"<td class=n>{e(_bash(p))}</td><td>{e(sv.get('verdict') or sv.get('note') or '–')}</td></tr>")
        heads = "".join(f"<th class=n>{e(l)}</th>" for l in METRIC_LABELS.values()) + "<th class=n>Shell commands</th>"
        warn = (f"<p class=gap><b>Warning.</b> {e(summary['control_warning'])}</p>"
                if summary.get("control_warning") else "")
        cost_html = (f"<h2>Cost and tokens</h2>{warn}<p class=meta>Median per run with vs without, all valid runs. "
                     f"Range: 90% bootstrap interval. <b>cheaper</b> needs the whole range below zero and a pass "
                     f"rate that held (drop ≤ {round(SAVINGS_GUARD * 100)} pts).</p>"
                     f"<div class=wrap><table><tr><th>Subject</th><th>Verdict</th><th class=n>Change</th>"
                     f"<th class=n>Pass rate</th></tr>{srows}</table></div>"
                     f"<div class=wrap><table><tr><th>Subject</th><th>Task</th>{heads}<th>Verdict</th></tr>{prow}</table></div>")
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
${summary['cost_usd']:.2f} spent · verdicts need ≥{round(summary['threshold'] * 100)} pts and Fisher p ≤ {summary.get('alpha', 0.1)}. Small samples show direction, not proof.
Verdicts hold for this model on these tasks only: other models may differ, and built-in tasks are short samples, not real project work.</p>
<h2>Verdicts</h2><div class=wrap><table><tr><th>Skill</th><th>Verdict</th><th>Tasks</th><th>Triggered</th><th class=n>Up front</th><th class=n>On use</th></tr>{rows}</table></div>
<h2>Per task</h2><div class=wrap><table><tr><th>Skill</th><th>Task</th><th class=n>With</th><th class=n>Without</th><th class=n>Lift</th><th class=n>p</th><th>Why this pair</th><th>Notes</th></tr>{pair_rows}</table></div>
{cost_html}
<h2>Gaps</h2>{gaps or '<p class=meta>None found.</p>'}
</main></body></html>
"""
