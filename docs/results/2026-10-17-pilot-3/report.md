# skilllab report

Model `claude-haiku-5-5` · 30 runs · 0 infrastructure errors (excluded) · $0.18 spent · a verdict needs a change of at least 30 pts and Fisher's exact p ≤ 0.1

## Verdicts

| Skill | Verdict | Tasks | Triggered | Tokens up front | Tokens on use |
| --- | --- | --- | --- | --- | --- |
| `addon:caveman` | **no lift** | fix-pagination | – | ≈0 | ≈0 |
| `addon:control` | **no lift** | fix-pagination | – | ≈0 | ≈0 |
| `addon:headroom` | **no lift** | fix-pagination | – | ≈0 | ≈0 |
| `addon:rtk` | **no lift** | fix-pagination | – | ≈0 | ≈0 |

## Per task

Pass rates show a 90% confidence interval in brackets. Cost per pass = total spend / passing runs.

| Skill | Task | n | Pass with | Pass without | Lift | p | Cost/pass with | Cost/pass without | Why this pair | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `addon:rtk` | fix-pagination | 5 | 100% [65–100] | 100% [65–100] | 0 pts | 1.00 | $0.006 | $0.006 | – | ceiling: passes without the skill too |
| `addon:headroom` | fix-pagination | 5 | 100% [65–100] | 100% [65–100] | 0 pts | 1.00 | $0.005 | $0.006 | – | ceiling: passes without the skill too |
| `addon:caveman` | fix-pagination | 5 | 100% [65–100] | 100% [65–100] | 0 pts | 1.00 | $0.007 | $0.006 | – | ceiling: passes without the skill too |
| `addon:control` | fix-pagination | 5 | 100% [65–100] | 100% [65–100] | 0 pts | 1.00 | $0.007 | $0.006 | – | ceiling: passes without the skill too |

## Cost and tokens

Median per run, with vs without, over all valid runs (passed or not). The range is a 90% bootstrap interval for the change. **cheaper** needs the whole range below zero and a pass rate that didn't drop by more than 15 pts.

The `addon:control` row changes nothing; it should say *same cost*. If it doesn't, the batch is biased.

| Subject | Cost/tokens verdict | Change | Pass rate change | Tasks |
| --- | --- | --- | --- | --- |
| `addon:rtk` | **same cost** | cost -16% [-20 to 0] | 0 pts | 1 |
| `addon:headroom` | **cheaper** | cost -33% [-36 to -13] | 0 pts | 1 |
| `addon:caveman` | **same cost** | cost +7% [-6 to 29] | 0 pts | 1 |
| `addon:control` | **same cost** | cost +2% [-14 to 22] | 0 pts | 1 |

*Shell commands*: median Bash calls per run, with vs without, and the programs run. An add-on that acts on shell output (a command rewriter) can only save anything where this is above zero.

| Subject | Task | Cost | Input tokens | Output tokens | Time | Turns | Shell commands | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `addon:rtk` | fix-pagination | $0.006 vs $0.007 (-16%) | 127,491 vs 184,162 (-31%) | 1,818 vs 2,287 (-21%) | 14s vs 16s (-9%) | 8 vs 9 (-11%) | 2 vs 3 (python3) | same cost |
| `addon:headroom` | fix-pagination | $0.005 vs $0.007 (-33%) | 98,604 vs 184,162 (-46%) | 2,124 vs 2,287 (-7%) | 16s vs 16s (+1%) | 9 vs 9 (0%) | 2 vs 3 (python3) | cheaper |
| `addon:caveman` | fix-pagination | $0.007 vs $0.007 (+7%) | 219,710 vs 184,162 (+19%) | 1,456 vs 2,287 (-36%) | 16s vs 16s (+1%) | 9 vs 9 (0%) | 3 vs 3 (ls, python3) | same cost |
| `addon:control` | fix-pagination | $0.007 vs $0.007 (+2%) | 189,196 vs 184,162 (+3%) | 2,582 vs 2,287 (+13%) | 21s vs 16s (+36%) | 9 vs 9 (0%) | 3 vs 3 (env, python3) | same cost |


## Gaps

### Tasks too easy to measure (1)

Baseline already passes every time, so no skill can show lift. Add a harder task.

- `fix-pagination`

## How to read this

- Each run starts from a fresh copy of the task's files. The skill is installed in `.claude/skills/` for the *with* arm only (a whole pack loads as a plugin, with its hooks). Pass/fail comes from hidden checks copied in after the agent finishes.
- A skill is only run on tasks judged a fair test of it (see *Why this pair* and matches.json). Skills only a person can start (`disable-model-invocation`) are started with `/name` and have no trigger rate.
- **Small samples.** With 3 repeats, only a 3-of-3 vs 0-of-3 split is significant. Use `--repeats 5` or more before telling a maintainer their skill doesn't help.
- **Many comparisons.** Testing many skills means a few will look significant by chance. Rerun surprising results before acting on them.
- **Cost and tokens** are what Claude Code reports for each run (input counts cached reads). They are measured on every run, so a saving shows even when both arms always pass. Prices and caching change, so compare within one report, not across months.
- A verdict is about *these tasks on this model*, not the skill in general. Other models (larger or smaller) may use skills differently.
- Built-in tasks are short samples (a few files, a clear prompt, a fixed check), not real project work. Long, vague, multi-step work on a real codebase may give different results.
