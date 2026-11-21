# caveman: full plugin vs voice only, and Headroom again, 21 November 2026

Follow-up asked for on [caveman#1323](https://github.com/JuliusBrussee/caveman/issues/1323):
does the caveman voice save anything once the plugin's bundled skills are taken out? Headroom
was rerun in the same batch, now with cache reads and writes recorded per run
([headroom#4260](https://github.com/headroomlabs-ai/headroom/issues/4260)).

- **Date:** 21 November 2026
- **Agent:** Claude Code 2.1.330, headless (`claude -p`). The 17 October run used 2.1.302.
- **Model:** `claude-haiku-5-5`
- **Tasks:** the 12 project-tier tasks (`tally`), 3 runs per arm, 3 shared baseline runs per
  task, one discarded warm-up per arm and task, and the no-op control arm: 240 runs, $5.29
- **Add-ons** (definitions in [`examples/addons/`](../../../examples/addons/)):
  - caveman 4.0.1 as its Claude Code plugin, `CAVEMAN_DEFAULT_MODE=caveman` (as on 17 October)
  - caveman-voice: only `skills/caveman` from the same release, each task started with
    `/caveman`, as caveman's README says for a skill-only install
  - Headroom 0.41.0 in proxy mode, `--no-cache` (as on 17 October)

Command:

```bash
skilllab compare examples/addons/caveman examples/addons/caveman-voice examples/addons/headroom \
  --tier project --repeats 3 --model claude-haiku-5-5 \
  --budget 6.6 --run-budget 0.75 --out results/savers-voice
```

## Results

Mean per run over the 36 measured runs of each arm (warm-ups excluded). Input is split into
fresh input, cache reads and cache writes.

| Arm | Passed | Cost | Fresh input | Cache reads | Cache writes | Output | Turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 34/36 | $0.0230 | 27 | 634,531 | 51,246 | 12,833 | 27.9 |
| control (no-op) | 35/36 | $0.0225 | 26 | 617,705 | 50,290 | 12,415 | 27.3 |
| caveman (plugin) | 33/36 | $0.0212 | 26 | 606,725 | 49,075 | 10,564 | 25.1 |
| caveman-voice | 35/36 | $0.0209 | 24 | 564,069 | 49,250 | 10,882 | 25.2 |
| Headroom | 35/36 | $0.0232 | 138 | 659,113 | 49,010 | 13,537 | 28.3 |

Cost change, as the mean of the 12 per-task changes, with a 90% bootstrap range over tasks:

| Arm | vs baseline | vs no-op control |
| --- | --- | --- |
| control | −2.1% [−5.5 to +1.0] | — |
| caveman (plugin) | −7.4% [−11.0 to −3.9] | −5.2% [−8.4 to −2.1] |
| caveman-voice | −8.6% [−13.7 to −3.1] | −5.6% [−13.3 to +3.7] |
| Headroom | +1.0% [−6.4 to +9.1] | +3.6% [−4.1 to +12.9] |

The report (`report.md`) uses medians per run and gives the same verdicts: caveman and
caveman-voice *cheaper*, Headroom *same cost*. Its control row is −6% [−10 to 0], on the edge of
*same cost*, so this batch's baseline ran slightly expensive. That is why the table above also
compares against the control arm.

## What changed since 17 October

- **caveman now saves a little.** On 17 October the plugin was −3% (*same cost*). Here both
  the plugin and the voice alone cut output by about 15–18% and turns by about 10%, for roughly
  5–9% lower cost. The voice alone costs about the same as the full plugin, so the bundled skills'
  input overhead is small on these tasks. The voice-only range against the control crosses zero,
  so that comparison is not settled at this sample size.
- **Headroom's saving is gone.** On 17 October it was −12%, mostly from deferring Claude Code's
  tool definitions (43M tokens by its own counter). Here its `tool_search` layer reports 0 tokens
  and 0 requests, its compression removed about 0.64M tokens, and the bill is unchanged. Claude
  Code was updated between the runs (2.1.302 to 2.1.330); Headroom only counts deferrals it makes
  itself, so a likely reason is that Claude Code now defers tool definitions on its own. **Not
  confirmed**; we're asking Headroom's maintainers.
- **Headroom's own counter is close to the bill this time:** `/stats` reports $0.13 saved
  (10.6%) on its proxied requests, with no tool-search savings to overstate.
- **Almost all input is cache reads** (about 27 fresh tokens per run against ~600K cache reads),
  which is why input savings move the bill much less than output savings.

**Mode check:** caveman's state folder held 48 `.mode` files after the batch (36 plugin runs and
12 warm-ups), all reading `caveman`. The voice-only arm has no hook, so it writes none.

## Files

- `report.md`, `report.html`: the report skilllab wrote.
- `summary.json`: the same numbers, machine-readable.
- `results.jsonl`: one line per run, now with `cache_read_tokens` and `cache_write_tokens`.
- `headroom-stats.json`: the proxy's `GET /stats` at the end of the batch.

Home-directory paths are replaced with `<home>`.

## Caveats

Haiku only, 12 tasks, 3 runs per arm per task. The baseline ran slightly expensive in this
batch (see the control row). Claude Code changed version between this run and 17 October, so
compare arms within one report, not across the two dates.
