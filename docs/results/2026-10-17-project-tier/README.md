# Token savers on the project tier, 17 October 2026

`skilllab compare` of three token-saving add-ons against the same agent without them, on the 12
project-tier tasks (one realistic project, `tally`).

- **Date:** 17 October 2026
- **Agent:** Claude Code 2.1.302, headless (`claude -p`)
- **Model:** `claude-haiku-5-5`
- **Tasks:** 12 project-tier tasks × 3 runs per arm, plus 3 shared baseline runs per task, one
  discarded warm-up per arm and task, and the no-op control arm: 240 runs, $4.70
- **Add-ons** (definitions in [`examples/addons/`](../../../examples/addons/)):
  - rtk 1.0.1: PreToolUse hook (`rtk hook claude`)
  - Headroom 0.41.0 in proxy mode, started with
    `HEADROOM_BEACON=off headroom proxy --host 127.0.0.1 --port 8787 --no-cache`
    (response cache off, so it's measured on compression alone)
  - caveman 4.0.1 as a Claude Code plugin, with `CAVEMAN_DEFAULT_MODE=caveman`

Command:

```bash
skilllab compare examples/addons/rtk examples/addons/headroom examples/addons/caveman \
  --tier project --repeats 3 --model claude-haiku-5-5 \
  --budget 8 --run-budget 0.75 --out results/savers-project
```

## Files

- `report.md`, `report.html`: the report skilllab wrote (verdicts, cost and tokens per task, shell commands).
- `summary.json`: the same numbers, machine-readable.
- `headroom-stats.json`, `headroom-stats-part1.json`: the proxy's `GET /stats` output. The batch
  was interrupted after 117 runs by a Claude Code usage limit and resumed with the same command
  (skilllab skips finished runs and retries the 15 that hit the limit). The proxy was restarted
  between the parts, so `headroom-stats-part1.json` covers the first part and `headroom-stats.json`
  the second. Their `persistent_savings.lifetime` counters also include earlier pilots on the same machine.

Home-directory paths are replaced with `<home>`.

## Caveats

Haiku only, 3 runs per arm per task: per-task rows give no verdict (they need 5 runs per arm),
only the overall rows do. Prices and caching change, so compare within this report.
