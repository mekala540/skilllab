Independent measurement: Headroom with Claude Code: 12% lower cost, pass rate unchanged (preliminary)
---
Hi! We're building skilllab (https://github.com/mekala540/skilllab), an open-source harness that measures agent add-ons by running the same coding tasks with and without them, checking the work with hidden tests, and comparing what Claude Code reports as cost.

**Setup:** Claude Code (headless) with claude-haiku-5-5, Headroom 0.41.0 as a local proxy (`headroom proxy --host 127.0.0.1 --port 8787 --no-cache`, `HEADROOM_BEACON=off`), `ANTHROPIC_BASE_URL` pointed at it. We disabled the response cache because our benchmark repeats each task, which would let replayed responses inflate savings. 12 coding tasks, 3 runs per task per arm, interleaved, with warm-up runs and a no-op control arm.

**What we saw:**
- Cost per run vs. no proxy: **−12%** (90% range −17% to −7%), pass rate 32/36 vs 32/36.
- On a single small task earlier we saw −33%; the saving shrinks as tasks get bigger.
- From `/stats`: ~1.95M tokens removed by compression, ~43M tokens of tool definitions held back by tool search. So most of the saving comes from deferring tool definitions.

**Data and method:** <LINK>

This is preliminary (one model, 12 tasks). Could you check whether this is the setup you'd recommend for Claude Code, and whether `--no-cache` is fair for a benchmark like this? Happy to rerun with any change you suggest.
