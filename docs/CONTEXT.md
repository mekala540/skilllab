# Project context (read this first)

Where the project stands, why, and what's next, so any session (cloud or local) can pick up
without the history. Keep it current: update "State" and "Next" whenever something changes.

Last updated: 19 October 2026.

## The mission

An **independent lab for AI coding-agent add-ons**: token savers, memory tools, skill packs.
Their makers publish their own numbers ("60–95% fewer tokens"); nobody checks them. We run the
same tasks with and without each add-on, check the work with hidden tests, and compare the real
bill. Two tools:

- **skillprint** (github.com/mekala540/skillprint, on PyPI): the label on the box. Before you
  install a pack, what it loads into context and what code and hooks it runs. v0.2.0 is
  released (listing budget model, `--html` report, `--redact`, `skillprint diff OLD NEW`).
- **skilllab** (this repo): the test track. Measures pass rate and cost with vs without.

Not building a new general agent: we measure agents and their add-ons. Money later comes from
private evaluations on a company's own code, then a team tier.

## Rules that never change

- **Neutrality: never take money from a tool we rank.** It is the whole product.
- **Publish method, code and data.** Anyone can rerun us.
- **Always show the limits next to the numbers** (model, task count, versions, repeats).
- **Tell makers before publishing widely**, and rerun if they show we set their tool up wrong.
- **Credit goes to mekala540.** Commits as `mekala540 <341272277+mekala540@users.noreply.github.com>`,
  **no `Co-Authored-By` or `Claude-Session` lines** in commit messages (skilllab and skillprint).
  LICENSE "Copyright (c) 2026 mekala", package author "mekala".
- **Privacy:** never publish the owner's machine paths or username, or anything about their
  employer's internal systems. Scrub results (`<home>/...`) before committing them.
- Paid runs only with caps (`--budget`, `--run-budget`); say the expected cost first.

## How we work

- **Cloud session (claude.ai):** builds code and tasks, reviews, writes drafts and plans. Free.
- **Local Claude Code on the Mac (~/Documents/skilllab, ~/Documents/skillprint):** anything that
  runs real agents, costs money, needs the installed tools (rtk via Homebrew, Headroom 0.41.0 via
  uv, caveman 4.0.1 checkout in `examples/addons/caveman/plugin`), or posts as mekala540 (`gh`).
- **Never edit the same repo in both places at once.** Pull before starting.
- Owner is not a git/terminal expert: give plain, step-by-step instructions and exact prompts.

## State (18 October 2026)

**Method (done):** `skilllab compare` with one discarded warm-up per arm and task, interleaved
fixed-seed order, a built-in no-op **control** arm (warns if it isn't "same cost"), no cost
verdict below 5 runs per arm, pooled verdict across tasks, per-run tool-call and shell-command
counts. Add-ons are `addon.json` folders (`examples/addons/{rtk,headroom,caveman,terse}`).

**Task tiers:**
- `easy`, `standard`: short sample tasks (too easy for current models).
- `project`: 12 tasks inside one realistic project, *tally* (`suite/projects/tally`), with git,
  logs, test runs. Calibrated on Haiku: most pass every time (fine for cost, too easy for lift).
- `real`: 12 real upstream bug fixes from click, sqlparse, boltons, more-itertools (mostly 2026),
  checked by the tests that came with the real fix. Built by `tests/generators/real_tasks.py`.
  **Calibration on Haiku was started; its result hasn't been reviewed yet.**

**First results (project tier, Haiku 5.5, 12 tasks × 3 runs per arm, 240 runs, $4.70):**
published in `docs/results/2026-10-17-project-tier/`.

| Add-on | Cost change (90% range) | Pass rate |
| --- | --- | --- |
| Headroom 0.41.0 (proxy, `--no-cache`) | −12% (−17 to −7): cheaper | unchanged |
| rtk 1.0.1 (hook) | +2% (−1 to +5): same cost | unchanged |
| caveman 4.0.1 (`CAVEMAN_DEFAULT_MODE=caveman`) | −3% (−12 to +2): same cost | unchanged |
| control (no-op) | −3% (−5 to +5): same cost | — |

Findings: rtk rewrites commands and its own counter claims ~380K tokens saved, but the bill
doesn't move. Headroom's saving is mostly deferred tool definitions; its own `/stats` claims
~$10.61 saved while its 48 proxied runs cost ~$0.90. caveman shortens replies but its own
instructions cancel the saving on these tasks.

**Outreach (posted 18 October 2026, from mekala540):** rtk-ai/rtk#4640,
headroomlabs-ai/headroom#4260, JuliusBrussee/caveman#1323 (drafts in `docs/outreach/`). Related
upstream issues: rtk #2001, Headroom #4238.

Replies so far:
- rtk#4640: automated triage bot only (category "question"); points to rtk #582, where other
  users measured rtk *increasing* cost (+18% single run, +81% over 50 tasks). Our +2% fits.
  Optional follow-up drafted: rtk +10% input / +3% output / +1% turns vs control (medians).
- caveman#1323 (19 Oct): setup confirmed correct; flagged to the owner in caveman PR #1315.
  Asked for (1) the pilot data (output saving vs input overhead) and (2) a voice-only arm vs the
  full plugin, because `--plugin-dir` also loads all bundled skills. We said we'd do both.
- headroom#4260: no reply yet.

## Next, in order

1. Review the real-tier calibration (`results/calibration-real` on the Mac); fix unfair tasks.
2. Add real bugs from flask, requests and rich to the real tier (cloud; free).
3. Token-saver comparison on the real tier (Mac; budget from the calibration).
4. Answer maker replies on the three issues; rerun anything they show we set up wrong.
   Now: publish pilot-3 data; caveman full plugin vs voice-only comparison (Mac, ~$4).
5. Results page + Reddit post (r/ClaudeAI) 2–3 days after the issues, linking them; HN later.
6. Release skilllab on PyPI.
7. Second model (Sonnet), more tools (memory tools next), harder tasks so skills can show lift.
8. Later: private evaluations for companies (start with ~10 interviews).
