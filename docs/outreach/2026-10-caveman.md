Independent measurement: caveman with Claude Code: no cost change on coding tasks (preliminary)
---
Hi! We're building skilllab (https://github.com/mekala540/skilllab), an open-source harness that measures agent add-ons by running the same coding tasks with and without them, checking the work with hidden tests, and comparing what Claude Code reports as cost.

**Setup:** Claude Code (headless) with claude-haiku-5-5, caveman 4.0.1 loaded as a plugin with `--plugin-dir`, `CAVEMAN_DEFAULT_MODE=caveman` (per INSTALL.md, scripted runs start with the mode off otherwise). We confirmed the mode was "caveman" in every session. 12 coding tasks, 3 runs per task per arm, interleaved, with warm-up runs and a no-op control arm.

**What we saw:**
- Cost per run vs. no plugin: **−3%** (90% range −12% to +2%), pass rate 36/36 vs 32/36 (the no-op control also rose, so we treat that as noise).
- In an earlier single-task pilot, replies were 36% shorter, but the plugin's own instructions and skills added about 19% input, which cancelled the saving.
- With the mode off, the plugin alone cost about 18% more on that pilot task.

**Data and method:** https://github.com/mekala540/skilllab/tree/main/docs/results/2026-10-17-project-tier

This is preliminary (one model, 12 tasks). Is this the setup you'd recommend for Claude Code used non-interactively? Happy to rerun with any change you suggest.
