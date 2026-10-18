# skilllab report

Model `claude-haiku-5-5` · 240 runs · 0 infrastructure errors (excluded) · $4.70 spent · a verdict needs a change of at least 30 pts and Fisher's exact p ≤ 0.1

## Verdicts

| Skill | Verdict | Tasks | Triggered | Tokens up front | Tokens on use |
| --- | --- | --- | --- | --- | --- |
| `addon:caveman` | **no lift** | tally-bisect, tally-csv-import, tally-double-charge, tally-export-security, tally-invoice-mismatch, tally-red-build, tally-remove-fmt, tally-report-json, tally-slow-export, tally-storage, tally-timezone, tally-why-cap | – | ≈0 | ≈0 |
| `addon:control` | **no lift** | tally-bisect, tally-csv-import, tally-double-charge, tally-export-security, tally-invoice-mismatch, tally-red-build, tally-remove-fmt, tally-report-json, tally-slow-export, tally-storage, tally-timezone, tally-why-cap | – | ≈0 | ≈0 |
| `addon:headroom` | **no lift** | tally-bisect, tally-csv-import, tally-double-charge, tally-export-security, tally-invoice-mismatch, tally-red-build, tally-remove-fmt, tally-report-json, tally-slow-export, tally-storage, tally-timezone, tally-why-cap | – | ≈0 | ≈0 |
| `addon:rtk` | **no lift** | tally-bisect, tally-csv-import, tally-double-charge, tally-export-security, tally-invoice-mismatch, tally-red-build, tally-remove-fmt, tally-report-json, tally-slow-export, tally-storage, tally-timezone, tally-why-cap | – | ≈0 | ≈0 |

## Per task

Pass rates show a 90% confidence interval in brackets. Cost per pass = total spend / passing runs.

| Skill | Task | n | Pass with | Pass without | Lift | p | Cost/pass with | Cost/pass without | Why this pair | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `addon:rtk` | tally-bisect | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.013 | $0.012 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:rtk` | tally-csv-import | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.041 | $0.043 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:rtk` | tally-double-charge | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.023 | $0.019 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:rtk` | tally-export-security | 3 | 100% [53–100] | 33% [8–75] | +67 pts | 0.40 | $0.021 | $0.060 | – | difference not significant (p=0.40); small sample: only large effects detectable |
| `addon:rtk` | tally-invoice-mismatch | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.021 | $0.019 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:rtk` | tally-red-build | 3 | 33% [8–75] | 67% [25–92] | -33 pts | 1.00 | $0.047 | $0.026 | – | difference not significant (p=1.00); small sample: only large effects detectable |
| `addon:rtk` | tally-remove-fmt | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.022 | $0.021 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:rtk` | tally-report-json | 3 | 100% [53–100] | 67% [25–92] | +33 pts | 1.00 | $0.024 | $0.030 | – | difference not significant (p=1.00); small sample: only large effects detectable |
| `addon:rtk` | tally-slow-export | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.022 | $0.020 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:rtk` | tally-storage | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.020 | $0.022 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:rtk` | tally-timezone | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.016 | $0.017 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:rtk` | tally-why-cap | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.008 | $0.007 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:headroom` | tally-bisect | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.011 | $0.012 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:headroom` | tally-csv-import | 3 | 67% [25–92] | 100% [53–100] | -33 pts | 1.00 | $0.053 | $0.043 | – | difference not significant (p=1.00); small sample: only large effects detectable |
| `addon:headroom` | tally-double-charge | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.017 | $0.019 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:headroom` | tally-export-security | 3 | 100% [53–100] | 33% [8–75] | +67 pts | 0.40 | $0.021 | $0.060 | – | difference not significant (p=0.40); small sample: only large effects detectable |
| `addon:headroom` | tally-invoice-mismatch | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.016 | $0.019 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:headroom` | tally-red-build | 3 | 67% [25–92] | 67% [25–92] | 0 pts | 1.00 | $0.021 | $0.026 | – | small sample: only large effects detectable |
| `addon:headroom` | tally-remove-fmt | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.019 | $0.021 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:headroom` | tally-report-json | 3 | 67% [25–92] | 67% [25–92] | 0 pts | 1.00 | $0.043 | $0.030 | – | small sample: only large effects detectable |
| `addon:headroom` | tally-slow-export | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.019 | $0.020 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:headroom` | tally-storage | 3 | 67% [25–92] | 100% [53–100] | -33 pts | 1.00 | $0.023 | $0.022 | – | difference not significant (p=1.00); small sample: only large effects detectable |
| `addon:headroom` | tally-timezone | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.017 | $0.017 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:headroom` | tally-why-cap | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.005 | $0.007 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman` | tally-bisect | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.013 | $0.012 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman` | tally-csv-import | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.037 | $0.043 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman` | tally-double-charge | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.025 | $0.019 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman` | tally-export-security | 3 | 100% [53–100] | 33% [8–75] | +67 pts | 0.40 | $0.018 | $0.060 | – | difference not significant (p=0.40); small sample: only large effects detectable |
| `addon:caveman` | tally-invoice-mismatch | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.016 | $0.019 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman` | tally-red-build | 3 | 100% [53–100] | 67% [25–92] | +33 pts | 1.00 | $0.015 | $0.026 | – | difference not significant (p=1.00); small sample: only large effects detectable |
| `addon:caveman` | tally-remove-fmt | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.022 | $0.021 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman` | tally-report-json | 3 | 100% [53–100] | 67% [25–92] | +33 pts | 1.00 | $0.023 | $0.030 | – | difference not significant (p=1.00); small sample: only large effects detectable |
| `addon:caveman` | tally-slow-export | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.021 | $0.020 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman` | tally-storage | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.018 | $0.022 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman` | tally-timezone | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.015 | $0.017 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman` | tally-why-cap | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.007 | $0.007 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:control` | tally-bisect | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.013 | $0.012 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:control` | tally-csv-import | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.042 | $0.043 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:control` | tally-double-charge | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.021 | $0.019 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:control` | tally-export-security | 3 | 100% [53–100] | 33% [8–75] | +67 pts | 0.40 | $0.020 | $0.060 | – | difference not significant (p=0.40); small sample: only large effects detectable |
| `addon:control` | tally-invoice-mismatch | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.019 | $0.019 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:control` | tally-red-build | 3 | 33% [8–75] | 67% [25–92] | -33 pts | 1.00 | $0.047 | $0.026 | – | difference not significant (p=1.00); small sample: only large effects detectable |
| `addon:control` | tally-remove-fmt | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.021 | $0.021 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:control` | tally-report-json | 3 | 100% [53–100] | 67% [25–92] | +33 pts | 1.00 | $0.029 | $0.030 | – | difference not significant (p=1.00); small sample: only large effects detectable |
| `addon:control` | tally-slow-export | 3 | 67% [25–92] | 100% [53–100] | -33 pts | 1.00 | $0.023 | $0.020 | – | difference not significant (p=1.00); small sample: only large effects detectable |
| `addon:control` | tally-storage | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.018 | $0.022 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:control` | tally-timezone | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.017 | $0.017 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:control` | tally-why-cap | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.007 | $0.007 | – | small sample: only large effects detectable; ceiling: passes without the skill too |

## Cost and tokens

Median per run, with vs without, over all valid runs (passed or not). The range is a 90% bootstrap interval for the change. **cheaper** needs the whole range below zero and a pass rate that didn't drop by more than 15 pts.

The `addon:control` row changes nothing; it should say *same cost*. If it doesn't, the batch is biased.

| Subject | Cost/tokens verdict | Change | Pass rate change | Tasks |
| --- | --- | --- | --- | --- |
| `addon:rtk` | **same cost** | cost +2% [-1 to 5] | +6 pts | 12 |
| `addon:headroom` | **cheaper** | cost -12% [-17 to -7] | 0 pts | 12 |
| `addon:caveman` | **same cost** | cost -3% [-12 to 2] | +11 pts | 12 |
| `addon:control` | **same cost** | cost -3% [-5 to 5] | +3 pts | 12 |

*Shell commands*: median Bash calls per run, with vs without, and the programs run. An add-on that acts on shell output (a command rewriter) can only save anything where this is above zero.

| Subject | Task | Cost | Input tokens | Output tokens | Time | Turns | Shell commands | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `addon:rtk` | tally-bisect | $0.012 vs $0.012 (+3%) | 453,619 vs 396,775 (+14%) | 5,367 vs 5,197 (+3%) | 34s vs 31s (+9%) | 22 vs 21 (+5%) | 13 vs 10 (git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:rtk` | tally-csv-import | $0.038 vs $0.042 (-9%) | 792,758 vs 946,913 (-16%) | 35,187 vs 37,708 (-7%) | 152s vs 166s (-9%) | 39 vs 38 (+3%) | 4 vs 5 (git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:rtk` | tally-double-charge | $0.023 vs $0.020 (+19%) | 845,947 vs 598,663 (+41%) | 11,678 vs 9,129 (+28%) | 67s vs 50s (+34%) | 22 vs 18 (+22%) | 9 vs 7 (cat, env, find, head, ls, python3, wc) | fewer than 5 runs per arm: no verdict |
| `addon:rtk` | tally-export-security | $0.021 vs $0.021 (-1%) | 599,218 vs 561,276 (+7%) | 13,801 vs 13,438 (+3%) | 74s vs 69s (+6%) | 21 vs 19 (+11%) | 3 vs 3 (cat, find, git, grep, ls, python3) | fewer than 5 runs per arm: no verdict |
| `addon:rtk` | tally-invoice-mismatch | $0.019 vs $0.017 (+15%) | 610,478 vs 525,857 (+16%) | 8,301 vs 7,379 (+12%) | 51s vs 48s (+5%) | 26 vs 27 (-4%) | 4 vs 5 (python3) | fewer than 5 runs per arm: no verdict |
| `addon:rtk` | tally-red-build | $0.015 vs $0.018 (-17%) | 431,218 vs 423,730 (+2%) | 8,125 vs 9,289 (-13%) | 46s vs 47s (-3%) | 24 vs 24 (0%) | 12 vs 18 (cat, find, git, grep, python3) | fewer than 5 runs per arm: no verdict |
| `addon:rtk` | tally-remove-fmt | $0.022 vs $0.021 (+2%) | 728,414 vs 653,835 (+11%) | 13,008 vs 13,048 (0%) | 70s vs 71s (-1%) | 41 vs 39 (+5%) | 7 vs 8 (git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:rtk` | tally-report-json | $0.024 vs $0.027 (-9%) | 629,432 vs 683,994 (-8%) | 16,846 vs 18,799 (-10%) | 84s vs 92s (-8%) | 34 vs 37 (-8%) | 5 vs 6 (python3) | fewer than 5 runs per arm: no verdict |
| `addon:rtk` | tally-slow-export | $0.022 vs $0.021 (+7%) | 792,883 vs 710,571 (+12%) | 10,217 vs 9,698 (+5%) | 103s vs 98s (+6%) | 31 vs 31 (0%) | 10 vs 10 (find, git, grep, python3) | fewer than 5 runs per arm: no verdict |
| `addon:rtk` | tally-storage | $0.020 vs $0.021 (-2%) | 537,724 vs 603,406 (-11%) | 14,239 vs 13,530 (+5%) | 70s vs 68s (+3%) | 32 vs 33 (-3%) | 6 vs 7 (git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:rtk` | tally-timezone | $0.016 vs $0.015 (+4%) | 490,109 vs 449,884 (+9%) | 7,153 vs 9,399 (-24%) | 42s vs 54s (-22%) | 21 vs 23 (-9%) | 4 vs 4 (env, git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:rtk` | tally-why-cap | $0.008 vs $0.007 (+23%) | 206,687 vs 118,157 (+75%) | 3,547 vs 2,861 (+24%) | 23s vs 16s (+44%) | 10 vs 8 (+25%) | 7 vs 5 (git, grep) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-bisect | $0.012 vs $0.012 (-4%) | 389,529 vs 396,775 (-2%) | 5,443 vs 5,197 (+5%) | 39s vs 31s (+25%) | 26 vs 21 (+24%) | 17 vs 10 (cat, git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-csv-import | $0.035 vs $0.042 (-16%) | 876,208 vs 946,913 (-7%) | 31,854 vs 37,708 (-16%) | 147s vs 166s (-11%) | 35 vs 38 (-8%) | 3 vs 5 (git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-double-charge | $0.017 vs $0.020 (-13%) | 511,994 vs 598,663 (-14%) | 10,664 vs 9,129 (+17%) | 73s vs 50s (+46%) | 25 vs 18 (+39%) | 9 vs 7 (git, head, ls, python3, wc) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-export-security | $0.021 vs $0.021 (+0%) | 477,862 vs 561,276 (-15%) | 16,458 vs 13,438 (+22%) | 84s vs 69s (+21%) | 27 vs 19 (+42%) | 5 vs 3 (git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-invoice-mismatch | $0.016 vs $0.017 (-4%) | 392,691 vs 525,857 (-25%) | 9,031 vs 7,379 (+22%) | 51s vs 48s (+5%) | 30 vs 27 (+11%) | 5 vs 5 (python3) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-red-build | $0.014 vs $0.018 (-22%) | 291,330 vs 423,730 (-31%) | 8,669 vs 9,289 (-7%) | 51s vs 47s (+9%) | 23 vs 24 (-4%) | 16 vs 18 (cat, find, git, grep, python3) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-remove-fmt | $0.019 vs $0.021 (-12%) | 539,695 vs 653,835 (-17%) | 12,902 vs 13,048 (-1%) | 84s vs 71s (+19%) | 37 vs 39 (-5%) | 7 vs 8 (git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-report-json | $0.027 vs $0.027 (+3%) | 712,799 vs 683,994 (+4%) | 21,610 vs 18,799 (+15%) | 98s vs 92s (+6%) | 38 vs 37 (+3%) | 6 vs 6 (find, git, ls, python3) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-slow-export | $0.019 vs $0.021 (-9%) | 629,715 vs 710,571 (-11%) | 9,943 vs 9,698 (+3%) | 121s vs 98s (+24%) | 35 vs 31 (+13%) | 12 vs 10 (git, python3, time, wc) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-storage | $0.017 vs $0.021 (-17%) | 430,834 vs 603,406 (-29%) | 12,138 vs 13,530 (-10%) | 62s vs 68s (-9%) | 29 vs 33 (-12%) | 2 vs 7 (git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-timezone | $0.014 vs $0.015 (-10%) | 428,309 vs 449,884 (-5%) | 7,569 vs 9,399 (-19%) | 50s vs 54s (-7%) | 22 vs 23 (-4%) | 6 vs 4 (TZ=Asia/Kolkata, TZ=Europe/London, TZ=UTC, git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-why-cap | $0.005 vs $0.007 (-24%) | 74,741 vs 118,157 (-37%) | 2,027 vs 2,861 (-29%) | 14s vs 16s (-11%) | 5 vs 8 (-38%) | 3 vs 5 (git, grep) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-bisect | $0.014 vs $0.012 (+14%) | 521,658 vs 396,775 (+31%) | 4,162 vs 5,197 (-20%) | 36s vs 31s (+14%) | 23 vs 21 (+10%) | 16 vs 10 (cat, env, find, git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-csv-import | $0.036 vs $0.042 (-16%) | 938,753 vs 946,913 (-1%) | 26,377 vs 37,708 (-30%) | 114s vs 166s (-31%) | 35 vs 38 (-8%) | 4 vs 5 (git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-double-charge | $0.024 vs $0.020 (+23%) | 762,517 vs 598,663 (+27%) | 9,280 vs 9,129 (+2%) | 53s vs 50s (+6%) | 21 vs 18 (+17%) | 6 vs 7 (cat, find, grep, head, python3, wc) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-export-security | $0.017 vs $0.021 (-18%) | 413,240 vs 561,276 (-26%) | 10,199 vs 13,438 (-24%) | 55s vs 69s (-20%) | 16 vs 19 (-16%) | 3 vs 3 (find, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-invoice-mismatch | $0.016 vs $0.017 (-5%) | 448,319 vs 525,857 (-15%) | 6,243 vs 7,379 (-15%) | 37s vs 48s (-24%) | 23 vs 27 (-15%) | 4 vs 5 (find, grep, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-red-build | $0.015 vs $0.018 (-19%) | 442,312 vs 423,730 (+4%) | 6,314 vs 9,289 (-32%) | 40s vs 47s (-15%) | 20 vs 24 (-17%) | 10 vs 18 (cat, find, git, grep, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-remove-fmt | $0.022 vs $0.021 (+2%) | 600,195 vs 653,835 (-8%) | 12,221 vs 13,048 (-6%) | 68s vs 71s (-4%) | 39 vs 39 (0%) | 9 vs 8 (cat, git, grep, ls, python3, tail) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-report-json | $0.024 vs $0.027 (-12%) | 602,423 vs 683,994 (-12%) | 15,491 vs 18,799 (-18%) | 77s vs 92s (-16%) | 29 vs 37 (-22%) | 2 vs 6 (ls, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-slow-export | $0.021 vs $0.021 (+0%) | 777,805 vs 710,571 (+9%) | 8,101 vs 9,698 (-16%) | 94s vs 98s (-4%) | 30 vs 31 (-3%) | 10 vs 10 (cat, find, git, python3, timeout) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-storage | $0.018 vs $0.021 (-15%) | 420,862 vs 603,406 (-30%) | 11,042 vs 13,530 (-18%) | 55s vs 68s (-19%) | 26 vs 33 (-21%) | 2 vs 7 (find, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-timezone | $0.016 vs $0.015 (+2%) | 438,363 vs 449,884 (-3%) | 6,226 vs 9,399 (-34%) | 42s vs 54s (-21%) | 19 vs 23 (-17%) | 3 vs 4 (env, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-why-cap | $0.007 vs $0.007 (+4%) | 123,059 vs 118,157 (+4%) | 1,742 vs 2,861 (-39%) | 12s vs 16s (-27%) | 6 vs 8 (-25%) | 3 vs 5 (git, grep) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-bisect | $0.014 vs $0.012 (+16%) | 488,772 vs 396,775 (+23%) | 6,521 vs 5,197 (+25%) | 40s vs 31s (+28%) | 25 vs 21 (+19%) | 14 vs 10 (git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-csv-import | $0.041 vs $0.042 (-4%) | 768,600 vs 946,913 (-19%) | 38,176 vs 37,708 (+1%) | 166s vs 166s (0%) | 37 vs 38 (-3%) | 5 vs 5 (find, git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-double-charge | $0.021 vs $0.020 (+5%) | 691,419 vs 598,663 (+15%) | 9,669 vs 9,129 (+6%) | 67s vs 50s (+35%) | 20 vs 18 (+11%) | 10 vs 7 (cat, find, git, head, ls, python3, wc) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-export-security | $0.020 vs $0.021 (-2%) | 526,964 vs 561,276 (-6%) | 15,159 vs 13,438 (+13%) | 78s vs 69s (+13%) | 23 vs 19 (+21%) | 4 vs 3 (git, ls, python3) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-invoice-mismatch | $0.019 vs $0.017 (+15%) | 474,864 vs 525,857 (-10%) | 8,668 vs 7,379 (+17%) | 52s vs 48s (+8%) | 27 vs 27 (0%) | 4 vs 5 (git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-red-build | $0.015 vs $0.018 (-17%) | 386,066 vs 423,730 (-9%) | 8,154 vs 9,289 (-12%) | 46s vs 47s (-4%) | 19 vs 24 (-21%) | 14 vs 18 (cat, find, git, grep, head, ls, python3) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-remove-fmt | $0.020 vs $0.021 (-4%) | 638,895 vs 653,835 (-2%) | 12,675 vs 13,048 (-3%) | 82s vs 71s (+17%) | 38 vs 39 (-3%) | 7 vs 8 (git, grep, ls, python3) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-report-json | $0.030 vs $0.027 (+11%) | 918,426 vs 683,994 (+34%) | 19,631 vs 18,799 (+4%) | 112s vs 92s (+21%) | 43 vs 37 (+16%) | 6 vs 6 (find, git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-slow-export | $0.019 vs $0.021 (-7%) | 615,062 vs 710,571 (-13%) | 8,886 vs 9,698 (-8%) | 84s vs 98s (-13%) | 30 vs 31 (-3%) | 9 vs 10 (cat, git, ls, python3, wc) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-storage | $0.019 vs $0.021 (-8%) | 508,936 vs 603,406 (-16%) | 11,543 vs 13,530 (-15%) | 55s vs 68s (-19%) | 29 vs 33 (-12%) | 3 vs 7 (git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-timezone | $0.015 vs $0.015 (-1%) | 468,578 vs 449,884 (+4%) | 8,158 vs 9,399 (-13%) | 51s vs 54s (-5%) | 20 vs 23 (-13%) | 6 vs 4 (env, git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-why-cap | $0.007 vs $0.007 (+4%) | 145,737 vs 118,157 (+23%) | 2,543 vs 2,861 (-11%) | 16s vs 16s (+4%) | 8 vs 8 (0%) | 5 vs 5 (git) | fewer than 5 runs per arm: no verdict |


## Gaps

### Tasks too easy to measure (9)

Baseline already passes every time, so no skill can show lift. Add a harder task.

- `tally-bisect`
- `tally-csv-import`
- `tally-double-charge`
- `tally-invoice-mismatch`
- `tally-remove-fmt`
- `tally-slow-export`
- `tally-storage`
- `tally-timezone`
- `tally-why-cap`

## How to read this

- Each run starts from a fresh copy of the task's files. The skill is installed in `.claude/skills/` for the *with* arm only (a whole pack loads as a plugin, with its hooks). Pass/fail comes from hidden checks copied in after the agent finishes.
- A skill is only run on tasks judged a fair test of it (see *Why this pair* and matches.json). Skills only a person can start (`disable-model-invocation`) are started with `/name` and have no trigger rate.
- **Small samples.** With 3 repeats, only a 3-of-3 vs 0-of-3 split is significant. Use `--repeats 5` or more before telling a maintainer their skill doesn't help.
- **Many comparisons.** Testing many skills means a few will look significant by chance. Rerun surprising results before acting on them.
- **Cost and tokens** are what Claude Code reports for each run (input counts cached reads). They are measured on every run, so a saving shows even when both arms always pass. Prices and caching change, so compare within one report, not across months.
- A verdict is about *these tasks on this model*, not the skill in general. Other models (larger or smaller) may use skills differently.
- Built-in tasks are short samples (a few files, a clear prompt, a fixed check), not real project work. Long, vague, multi-step work on a real codebase may give different results.
