Independent measurement: Headroom with Claude Code: 12% lower cost, pass rate unchanged (preliminary)
---
Hi! We're building skilllab (https://github.com/mekala540/skilllab), an open-source harness that measures agent add-ons by running the same coding tasks with and without them, checking the work with hidden tests, and comparing what Claude Code reports as cost.

**Setup:** Claude Code (headless) with claude-haiku-5-5, Headroom 0.41.0 as a local proxy (`headroom proxy --host 127.0.0.1 --port 8787 --no-cache`, `HEADROOM_BEACON=off`), `ANTHROPIC_BASE_URL` pointed at it. We disabled the response cache because our benchmark repeats each task, which would let replayed responses inflate savings. 12 coding tasks, 3 runs per task per arm, interleaved, with warm-up runs and a no-op control arm.

**What we saw:**
- Cost per run vs. no proxy: **−12%** (90% range −17% to −7%), pass rate 32/36 vs 32/36.
- In an earlier single-task pilot (not in the linked data) we saw −33%, so the saving seems to shrink as tasks get bigger.
- The proxy restarted once (the batch hit a usage limit and resumed), so `/stats` comes in two files. Together they report ~3.2M tokens removed by compression and ~71M tokens of tool definitions held back by tool search, so most of the effect comes from deferring tool definitions.
- One thing we'd like to understand: `/stats` reports **$4.12 + $6.49 ≈ $10.61 saved** (`summary.cost.total_saved_usd`, mostly `tool_search_savings_usd`). Those counters cover the 48 runs that went through the proxy (36 measured runs plus 12 warm-ups), which cost about **$0.90** in total on the bill. Over the 36 measured runs, the saving against the same runs without the proxy was roughly **$0.05–0.08**. Our guess is that the counter prices deferred tool tokens at the full input rate, while Claude Code would mostly have read them from the prompt cache at a fraction of that price. Is that right? This may be what #4238 (savings redesign) is addressing; happy to move the question there.

**Data and method:** https://github.com/mekala540/skilllab/tree/main/docs/results/2026-10-17-project-tier

This is preliminary (one model, 12 tasks). Could you check whether this is the setup you'd recommend for Claude Code, and whether `--no-cache` is fair for a benchmark like this? Happy to rerun with any change you suggest.
