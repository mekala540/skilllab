# Pilot 3: token savers on one short task, 17 October 2026

The pilot run before the [project-tier comparison](../2026-10-17-project-tier/). Published on
21 November 2026 because caveman's maintainers asked for its split of output saving vs input
overhead ([caveman#1323](https://github.com/JuliusBrussee/caveman/issues/1323)).

- **Date:** 17 October 2026
- **Agent:** Claude Code, headless (`claude -p`)
- **Model:** `claude-haiku-5-5`
- **Task:** `fix-pagination` (standard tier, a short sample task), 5 runs per arm, plus 5 shared
  baseline runs, one discarded warm-up per arm and the no-op control arm: 30 runs, $0.18
- **Add-ons:** the same set-ups as the project-tier run (definitions in
  [`examples/addons/`](../../../examples/addons/)): rtk 1.0.1 (hook), Headroom 0.41.0 (proxy,
  `--no-cache`), caveman 4.0.1 (plugin, `CAVEMAN_DEFAULT_MODE=caveman`)

## caveman: output saving vs input overhead

Mean per run (every run passed in both arms):

| | Baseline | caveman | Change |
| --- | ---: | ---: | ---: |
| Output tokens | 2,227 | 1,544 | −683 (−31%) |
| Input tokens (fresh + cache reads + cache writes) | 163,298 | 198,949 | +35,651 (+22%) |
| Turns | 8.8 | 8.6 | −0.2 |
| Cost | $0.00650 | $0.00709 | +$0.00059 (+9%) |

In dollars, per run:

- **Output saving:** 683 fewer output tokens at Haiku 5.5's $0.50 per million is about
  **−$0.00034**.
- **Input overhead:** the rest of the cost change, about **+$0.00093**. This is derived (total
  change minus the output saving) because this run didn't record cache reads and writes
  separately; most of the extra input is billed at the cache-read rate. Runs now record that split.

So the voice did shorten replies by about a third, but the extra input it brings cost more than
that saved. The plugin was loaded with `--plugin-dir`, which also loads every bundled skill's
description, so this input overhead includes more than the voice itself. A voice-only arm is the
next run.

The no-op control arm for comparison: output +8%, input +7%, cost +3% (means), and the report's
median verdict is *same cost*.

**Mode check:** `caveman-watch.log` lists caveman's state files as they changed. All 6 caveman
sessions (5 runs and the warm-up) wrote a `.mode` file reading `caveman`.

## Files

- `report.md`, `report.html`: the report skilllab wrote (verdicts, cost and tokens, shell commands).
- `summary.json`: the same numbers, machine-readable.
- `results.jsonl`: one line per run (cost, tokens, turns, tool calls, pass/fail).
- `caveman-watch.log`: caveman's state files under `~/.claude` during the run.
- `headroom-stats.json`: the Headroom proxy's `GET /stats` at the end. Its lifetime counters
  include earlier pilots on the same machine.

Home-directory paths are replaced with `<home>`.

## Caveats

One short task, Haiku only, 5 runs per arm: a pilot, not a result. Per-run means in the table
above, medians in the report. The project-tier run is the published comparison.
