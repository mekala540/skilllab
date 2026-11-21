# skilllab report

Model `claude-haiku-5-5` · 240 runs · 0 infrastructure errors (excluded) · $5.29 spent · a verdict needs a change of at least 30 pts and Fisher's exact p ≤ 0.1

## Verdicts

| Skill | Verdict | Tasks | Triggered | Tokens up front | Tokens on use |
| --- | --- | --- | --- | --- | --- |
| `addon:caveman` | **no lift** | tally-bisect, tally-csv-import, tally-double-charge, tally-export-security, tally-invoice-mismatch, tally-red-build, tally-remove-fmt, tally-report-json, tally-slow-export, tally-storage, tally-timezone, tally-why-cap | – | ≈0 | ≈0 |
| `addon:caveman-voice` | **no lift** | tally-bisect, tally-csv-import, tally-double-charge, tally-export-security, tally-invoice-mismatch, tally-red-build, tally-remove-fmt, tally-report-json, tally-slow-export, tally-storage, tally-timezone, tally-why-cap | – | ≈0 | ≈0 |
| `addon:control` | **no lift** | tally-bisect, tally-csv-import, tally-double-charge, tally-export-security, tally-invoice-mismatch, tally-red-build, tally-remove-fmt, tally-report-json, tally-slow-export, tally-storage, tally-timezone, tally-why-cap | – | ≈0 | ≈0 |
| `addon:headroom` | **no lift** | tally-bisect, tally-csv-import, tally-double-charge, tally-export-security, tally-invoice-mismatch, tally-red-build, tally-remove-fmt, tally-report-json, tally-slow-export, tally-storage, tally-timezone, tally-why-cap | – | ≈0 | ≈0 |

## Per task

Pass rates show a 90% confidence interval in brackets. Cost per pass = total spend / passing runs.

| Skill | Task | n | Pass with | Pass without | Lift | p | Cost/pass with | Cost/pass without | Why this pair | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `addon:caveman` | tally-bisect | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.014 | $0.015 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman` | tally-csv-import | 3 | 67% [25–92] | 67% [25–92] | 0 pts | 1.00 | $0.064 | $0.066 | – | small sample: only large effects detectable |
| `addon:caveman` | tally-double-charge | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.023 | $0.025 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman` | tally-export-security | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.022 | $0.022 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman` | tally-invoice-mismatch | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.017 | $0.021 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman` | tally-red-build | 3 | 33% [8–75] | 67% [25–92] | -33 pts | 1.00 | $0.050 | $0.030 | – | difference not significant (p=1.00); small sample: only large effects detectable |
| `addon:caveman` | tally-remove-fmt | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.023 | $0.025 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman` | tally-report-json | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.029 | $0.032 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman` | tally-slow-export | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.021 | $0.021 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman` | tally-storage | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.021 | $0.026 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman` | tally-timezone | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.017 | $0.018 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman` | tally-why-cap | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.008 | $0.008 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman-voice` | tally-bisect | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.014 | $0.015 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman-voice` | tally-csv-import | 3 | 100% [53–100] | 67% [25–92] | +33 pts | 1.00 | $0.044 | $0.066 | – | difference not significant (p=1.00); small sample: only large effects detectable |
| `addon:caveman-voice` | tally-double-charge | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.020 | $0.025 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman-voice` | tally-export-security | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.018 | $0.022 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman-voice` | tally-invoice-mismatch | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.017 | $0.021 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman-voice` | tally-red-build | 3 | 67% [25–92] | 67% [25–92] | 0 pts | 1.00 | $0.035 | $0.030 | – | small sample: only large effects detectable |
| `addon:caveman-voice` | tally-remove-fmt | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.021 | $0.025 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman-voice` | tally-report-json | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.029 | $0.032 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman-voice` | tally-slow-export | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.020 | $0.021 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman-voice` | tally-storage | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.021 | $0.026 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman-voice` | tally-timezone | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.015 | $0.018 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:caveman-voice` | tally-why-cap | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.008 | $0.008 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:headroom` | tally-bisect | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.014 | $0.015 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:headroom` | tally-csv-import | 3 | 67% [25–92] | 67% [25–92] | 0 pts | 1.00 | $0.062 | $0.066 | – | small sample: only large effects detectable |
| `addon:headroom` | tally-double-charge | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.021 | $0.025 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:headroom` | tally-export-security | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.025 | $0.022 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:headroom` | tally-invoice-mismatch | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.020 | $0.021 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:headroom` | tally-red-build | 3 | 100% [53–100] | 67% [25–92] | +33 pts | 1.00 | $0.016 | $0.030 | – | difference not significant (p=1.00); small sample: only large effects detectable |
| `addon:headroom` | tally-remove-fmt | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.028 | $0.025 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:headroom` | tally-report-json | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.026 | $0.032 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:headroom` | tally-slow-export | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.024 | $0.021 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:headroom` | tally-storage | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.036 | $0.026 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:headroom` | tally-timezone | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.019 | $0.018 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:headroom` | tally-why-cap | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.007 | $0.008 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:control` | tally-bisect | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.016 | $0.015 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:control` | tally-csv-import | 3 | 100% [53–100] | 67% [25–92] | +33 pts | 1.00 | $0.043 | $0.066 | – | difference not significant (p=1.00); small sample: only large effects detectable |
| `addon:control` | tally-double-charge | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.023 | $0.025 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:control` | tally-export-security | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.023 | $0.022 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:control` | tally-invoice-mismatch | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.020 | $0.021 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:control` | tally-red-build | 3 | 67% [25–92] | 67% [25–92] | 0 pts | 1.00 | $0.024 | $0.030 | – | small sample: only large effects detectable |
| `addon:control` | tally-remove-fmt | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.026 | $0.025 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:control` | tally-report-json | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.031 | $0.032 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:control` | tally-slow-export | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.022 | $0.021 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:control` | tally-storage | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.023 | $0.026 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:control` | tally-timezone | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.019 | $0.018 | – | small sample: only large effects detectable; ceiling: passes without the skill too |
| `addon:control` | tally-why-cap | 3 | 100% [53–100] | 100% [53–100] | 0 pts | 1.00 | $0.008 | $0.008 | – | small sample: only large effects detectable; ceiling: passes without the skill too |

## Cost and tokens

Median per run, with vs without, over all valid runs (passed or not). The range is a 90% bootstrap interval for the change. **cheaper** needs the whole range below zero and a pass rate that didn't drop by more than 15 pts.

The `addon:control` row changes nothing; it should say *same cost*. If it doesn't, the batch is biased.

| Subject | Cost/tokens verdict | Change | Pass rate change | Tasks |
| --- | --- | --- | --- | --- |
| `addon:caveman` | **cheaper** | cost -9% [-12 to -5] | -3 pts | 12 |
| `addon:caveman-voice` | **cheaper** | cost -9% [-14 to -6] | +3 pts | 12 |
| `addon:headroom` | **same cost** | cost -5% [-11 to 1] | +3 pts | 12 |
| `addon:control` | **same cost** | cost -6% [-10 to 0] | +3 pts | 12 |

*Shell commands*: median Bash calls per run, with vs without, and the programs run. An add-on that acts on shell output (a command rewriter) can only save anything where this is above zero.

| Subject | Task | Cost | Input tokens | Output tokens | Time | Turns | Shell commands | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `addon:caveman` | tally-bisect | $0.014 vs $0.015 (-8%) | 465,637 vs 522,037 (-11%) | 4,181 vs 5,277 (-21%) | 28s vs 37s (-23%) | 20 vs 24 (-17%) | 14 vs 12 (cat, find, git, grep, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-csv-import | $0.043 vs $0.044 (-3%) | 1,233,521 vs 1,053,291 (+17%) | 31,031 vs 37,535 (-17%) | 145s vs 165s (-12%) | 38 vs 40 (-5%) | 4 vs 5 (git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-double-charge | $0.023 vs $0.026 (-13%) | 892,088 vs 932,089 (-4%) | 10,313 vs 9,667 (+7%) | 63s vs 58s (+7%) | 23 vs 20 (+15%) | 10 vs 7 (cat, find, git, grep, head, ls, python3, wc) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-export-security | $0.022 vs $0.023 (-1%) | 731,136 vs 624,286 (+17%) | 12,341 vs 13,899 (-11%) | 67s vs 71s (-6%) | 22 vs 20 (+10%) | 10 vs 4 (git, grep, ls, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-invoice-mismatch | $0.017 vs $0.021 (-20%) | 481,940 vs 644,718 (-25%) | 6,150 vs 8,959 (-31%) | 36s vs 53s (-31%) | 25 vs 30 (-17%) | 5 vs 5 (find, git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-red-build | $0.016 vs $0.020 (-20%) | 447,766 vs 590,800 (-24%) | 7,022 vs 9,439 (-26%) | 41s vs 54s (-23%) | 18 vs 26 (-31%) | 13 vs 21 (cat, find, git, grep, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-remove-fmt | $0.023 vs $0.026 (-12%) | 776,779 vs 856,630 (-9%) | 11,183 vs 15,142 (-26%) | 63s vs 80s (-22%) | 40 vs 45 (-11%) | 7 vs 13 (cat, git, ls, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-report-json | $0.028 vs $0.034 (-17%) | 914,774 vs 1,129,723 (-19%) | 16,050 vs 20,495 (-22%) | 81s vs 103s (-21%) | 37 vs 44 (-16%) | 7 vs 9 (find, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-slow-export | $0.021 vs $0.022 (-5%) | 709,251 vs 625,758 (+13%) | 8,076 vs 9,286 (-13%) | 83s vs 96s (-13%) | 25 vs 30 (-17%) | 8 vs 10 (git, head, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-storage | $0.019 vs $0.026 (-27%) | 461,182 vs 720,887 (-36%) | 10,245 vs 17,446 (-41%) | 49s vs 82s (-39%) | 24 vs 34 (-29%) | 3 vs 7 (git, ls, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-timezone | $0.016 vs $0.017 (-8%) | 443,387 vs 518,020 (-14%) | 6,591 vs 7,080 (-7%) | 40s vs 44s (-8%) | 19 vs 22 (-14%) | 4 vs 4 (env, git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman` | tally-why-cap | $0.008 vs $0.008 (+6%) | 144,998 vs 165,642 (-12%) | 1,695 vs 2,274 (-25%) | 14s vs 16s (-8%) | 6 vs 7 (-14%) | 3 vs 4 (git) | fewer than 5 runs per arm: no verdict |
| `addon:caveman-voice` | tally-bisect | $0.014 vs $0.015 (-8%) | 480,035 vs 522,037 (-8%) | 4,075 vs 5,277 (-23%) | 31s vs 37s (-15%) | 19 vs 24 (-21%) | 11 vs 12 (git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman-voice` | tally-csv-import | $0.043 vs $0.044 (-3%) | 1,272,511 vs 1,053,291 (+21%) | 31,428 vs 37,535 (-16%) | 144s vs 165s (-13%) | 38 vs 40 (-5%) | 4 vs 5 (cat, find, git, grep, python3, sed) | fewer than 5 runs per arm: no verdict |
| `addon:caveman-voice` | tally-double-charge | $0.020 vs $0.026 (-23%) | 725,895 vs 932,089 (-22%) | 8,503 vs 9,667 (-12%) | 52s vs 58s (-10%) | 24 vs 20 (+20%) | 8 vs 7 (cat, find, grep, head, ls, python3, wc) | fewer than 5 runs per arm: no verdict |
| `addon:caveman-voice` | tally-export-security | $0.019 vs $0.023 (-18%) | 433,413 vs 624,286 (-31%) | 11,658 vs 13,899 (-16%) | 60s vs 71s (-16%) | 16 vs 20 (-20%) | 2 vs 4 (ls, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman-voice` | tally-invoice-mismatch | $0.019 vs $0.021 (-10%) | 554,970 vs 644,718 (-14%) | 7,178 vs 8,959 (-20%) | 45s vs 53s (-16%) | 25 vs 30 (-17%) | 5 vs 5 (cat, find, grep, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman-voice` | tally-red-build | $0.020 vs $0.020 (+0%) | 557,620 vs 590,800 (-6%) | 9,276 vs 9,439 (-2%) | 54s vs 54s (+1%) | 25 vs 26 (-4%) | 17 vs 21 (cat, find, git, grep, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman-voice` | tally-remove-fmt | $0.022 vs $0.026 (-15%) | 599,198 vs 856,630 (-30%) | 12,537 vs 15,142 (-17%) | 70s vs 80s (-13%) | 38 vs 45 (-16%) | 4 vs 13 (cat, find, git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman-voice` | tally-report-json | $0.029 vs $0.034 (-15%) | 905,671 vs 1,129,723 (-20%) | 17,547 vs 20,495 (-14%) | 91s vs 103s (-11%) | 38 vs 44 (-14%) | 5 vs 9 (git, ls, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman-voice` | tally-slow-export | $0.021 vs $0.022 (-1%) | 672,842 vs 625,758 (+8%) | 8,533 vs 9,286 (-8%) | 93s vs 96s (-3%) | 26 vs 30 (-13%) | 8 vs 10 (cat, find, git, ls, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman-voice` | tally-storage | $0.018 vs $0.026 (-32%) | 403,533 vs 720,887 (-44%) | 10,286 vs 17,446 (-41%) | 50s vs 82s (-39%) | 24 vs 34 (-29%) | 6 vs 7 (find, git, grep, ls, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman-voice` | tally-timezone | $0.015 vs $0.017 (-14%) | 367,647 vs 518,020 (-29%) | 6,258 vs 7,080 (-12%) | 38s vs 44s (-13%) | 16 vs 22 (-27%) | 1 vs 4 (env, python3) | fewer than 5 runs per arm: no verdict |
| `addon:caveman-voice` | tally-why-cap | $0.008 vs $0.008 (+4%) | 169,111 vs 165,642 (+2%) | 2,507 vs 2,274 (+10%) | 17s vs 16s (+6%) | 10 vs 7 (+43%) | 8 vs 4 (cat, git, grep) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-bisect | $0.014 vs $0.015 (-7%) | 493,603 vs 522,037 (-5%) | 5,035 vs 5,277 (-5%) | 36s vs 37s (-2%) | 22 vs 24 (-8%) | 13 vs 12 (find, git, ls, python3) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-csv-import | $0.042 vs $0.044 (-5%) | 1,050,218 vs 1,053,291 (0%) | 33,348 vs 37,535 (-11%) | 154s vs 165s (-7%) | 36 vs 40 (-10%) | 4 vs 5 (git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-double-charge | $0.022 vs $0.026 (-16%) | 751,643 vs 932,089 (-19%) | 12,070 vs 9,667 (+25%) | 71s vs 58s (+22%) | 25 vs 20 (+25%) | 5 vs 7 (git, ls, python3, wc) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-export-security | $0.027 vs $0.023 (+20%) | 823,642 vs 624,286 (+32%) | 16,990 vs 13,899 (+22%) | 92s vs 71s (+29%) | 26 vs 20 (+30%) | 10 vs 4 (git, grep, python3) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-invoice-mismatch | $0.020 vs $0.021 (-3%) | 631,026 vs 644,718 (-2%) | 9,242 vs 8,959 (+3%) | 54s vs 53s (+2%) | 28 vs 30 (-7%) | 5 vs 5 (git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-red-build | $0.016 vs $0.020 (-19%) | 444,559 vs 590,800 (-25%) | 8,279 vs 9,439 (-12%) | 49s vs 54s (-8%) | 22 vs 26 (-15%) | 16 vs 21 (cat, find, git, grep, head, python3, sed) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-remove-fmt | $0.029 vs $0.026 (+9%) | 1,031,586 vs 856,630 (+20%) | 15,212 vs 15,142 (+0%) | 89s vs 80s (+10%) | 43 vs 45 (-4%) | 9 vs 13 (git, head, python3) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-report-json | $0.024 vs $0.034 (-28%) | 687,455 vs 1,129,723 (-39%) | 16,119 vs 20,495 (-21%) | 83s vs 103s (-20%) | 33 vs 44 (-25%) | 5 vs 9 (git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-slow-export | $0.027 vs $0.022 (+22%) | 980,814 vs 625,758 (+57%) | 11,480 vs 9,286 (+24%) | 97s vs 96s (+1%) | 32 vs 30 (+7%) | 10 vs 10 (git, head, python3) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-storage | $0.035 vs $0.026 (+36%) | 1,075,326 vs 720,887 (+49%) | 26,882 vs 17,446 (+54%) | 133s vs 82s (+63%) | 47 vs 34 (+38%) | 9 vs 7 (cat, git, ls, python3) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-timezone | $0.018 vs $0.017 (+1%) | 572,117 vs 518,020 (+10%) | 8,977 vs 7,080 (+27%) | 56s vs 44s (+29%) | 24 vs 22 (+9%) | 4 vs 4 (TZ=Asia/Kolkata, TZ=Europe/London, env, python3) | fewer than 5 runs per arm: no verdict |
| `addon:headroom` | tally-why-cap | $0.007 vs $0.008 (-6%) | 124,954 vs 165,642 (-25%) | 2,206 vs 2,274 (-3%) | 15s vs 16s (-3%) | 6 vs 7 (-14%) | 3 vs 4 (git) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-bisect | $0.016 vs $0.015 (+6%) | 567,121 vs 522,037 (+9%) | 5,502 vs 5,277 (+4%) | 38s vs 37s (+2%) | 25 vs 24 (+4%) | 15 vs 12 (git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-csv-import | $0.045 vs $0.044 (+2%) | 1,029,598 vs 1,053,291 (-2%) | 35,648 vs 37,535 (-5%) | 158s vs 165s (-4%) | 38 vs 40 (-5%) | 6 vs 5 (find, git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-double-charge | $0.023 vs $0.026 (-11%) | 755,327 vs 932,089 (-19%) | 11,987 vs 9,667 (+24%) | 69s vs 58s (+19%) | 24 vs 20 (+20%) | 8 vs 7 (find, git, grep, head, ls, python3, wc) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-export-security | $0.021 vs $0.023 (-6%) | 620,317 vs 624,286 (-1%) | 12,545 vs 13,899 (-10%) | 67s vs 71s (-6%) | 21 vs 20 (+5%) | 7 vs 4 (cat, git, ls, python3) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-invoice-mismatch | $0.021 vs $0.021 (+2%) | 674,488 vs 644,718 (+5%) | 8,997 vs 8,959 (+0%) | 52s vs 53s (-1%) | 30 vs 30 (0%) | 5 vs 5 (find, git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-red-build | $0.016 vs $0.020 (-17%) | 450,405 vs 590,800 (-24%) | 6,626 vs 9,439 (-30%) | 40s vs 54s (-26%) | 21 vs 26 (-19%) | 15 vs 21 (cat, find, git, grep, python3) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-remove-fmt | $0.023 vs $0.026 (-11%) | 733,276 vs 856,630 (-14%) | 13,189 vs 15,142 (-13%) | 72s vs 80s (-11%) | 38 vs 45 (-16%) | 10 vs 13 (cat, cmp, find, git, ls, python3, wc) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-report-json | $0.032 vs $0.034 (-4%) | 1,006,736 vs 1,129,723 (-11%) | 20,850 vs 20,495 (+2%) | 104s vs 103s (+1%) | 38 vs 44 (-14%) | 4 vs 9 (find, git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-slow-export | $0.019 vs $0.022 (-10%) | 612,858 vs 625,758 (-2%) | 8,553 vs 9,286 (-8%) | 86s vs 96s (-10%) | 27 vs 30 (-10%) | 11 vs 10 (git, head, ls, python3) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-storage | $0.023 vs $0.026 (-9%) | 682,146 vs 720,887 (-5%) | 14,356 vs 17,446 (-18%) | 70s vs 82s (-14%) | 34 vs 34 (0%) | 7 vs 7 (git, ls, python3) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-timezone | $0.019 vs $0.017 (+8%) | 547,932 vs 518,020 (+6%) | 7,401 vs 7,080 (+5%) | 50s vs 44s (+14%) | 24 vs 22 (+9%) | 6 vs 4 (env, find, git, python3) | fewer than 5 runs per arm: no verdict |
| `addon:control` | tally-why-cap | $0.008 vs $0.008 (0%) | 128,340 vs 165,642 (-23%) | 2,552 vs 2,274 (+12%) | 17s vs 16s (+11%) | 5 vs 7 (-29%) | 2 vs 4 (git) | fewer than 5 runs per arm: no verdict |


## Gaps

### Tasks too easy to measure (10)

Baseline already passes every time, so no skill can show lift. Add a harder task.

- `tally-bisect`
- `tally-double-charge`
- `tally-export-security`
- `tally-invoice-mismatch`
- `tally-remove-fmt`
- `tally-report-json`
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
