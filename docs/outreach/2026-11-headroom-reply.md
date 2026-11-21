# Reply on headroomlabs-ai/headroom#4260 (draft, November 2026)

Answers the Devin triage questions (6 Nov) and the Mycroft comment (7 Nov). Not posted yet.

---

Thanks both. Answers to the three questions, from the same 12-task run linked above
(Claude Haiku 5.5, 3 runs per task per arm, Headroom 0.41.0):

**1. Per-task input tokens, with and without Headroom** (median per task; input here is all
input, i.e. fresh + cache reads + cache writes):

| Task | Without | With Headroom | Change |
| --- | ---: | ---: | ---: |
| tally-bisect | 396,775 | 389,529 | −2% |
| tally-csv-import | 946,913 | 876,208 | −7% |
| tally-double-charge | 598,663 | 511,994 | −14% |
| tally-export-security | 561,276 | 477,862 | −15% |
| tally-invoice-mismatch | 525,857 | 392,691 | −25% |
| tally-red-build | 423,730 | 291,330 | −31% |
| tally-remove-fmt | 653,835 | 539,695 | −17% |
| tally-report-json | 683,994 | 712,799 | +4% |
| tally-slow-export | 710,571 | 629,715 | −11% |
| tally-storage | 603,406 | 430,834 | −29% |
| tally-timezone | 449,884 | 428,309 | −5% |
| tally-why-cap | 118,157 | 74,741 | −37% |

Median per-task change: −15% input tokens and −11% cost with Headroom, against −4% and −2%
for our no-op control arm. So Headroom clearly reduces input; the bill moves less because most
of that input is billed at the cache-read rate.

**2. CCR retrievals:** none. Headroom's own `/stats` reports `mcp.retrievals: 0`, and the proxy
log's TOIN lines report "0 retrievals, 0.0% retrieval rate" throughout.

**3. Prompt-cache reads:** yes, they're counted. Cost is Claude Code's own `total_cost_usd` for
each run, which prices cache reads and writes at their own rates. Our token column adds the
three input types together; we didn't store the split in this run. We now record
`cache_read_input_tokens` and `cache_creation_input_tokens` separately for every run and will
include them in the next round.

**On `--no-cache`:** understood, and that was the intent: it turns off Headroom's response cache
so we measure compression alone. Anthropic's prompt caching stayed on in every arm, as in normal
use.

**On the savings counter (@tonydzi's point):** the numbers fit that explanation. In this run
`/stats` reports `tool_search` savings of 43,250,759 tokens valued at $6.10, about $0.14 per
million tokens. Haiku 5.5's list price is $0.10 per million for input (prompts up to 100K tokens)
and $0.01 per million for cache reads. Priced as cache reads, which is how most of a stable
tool-definition prefix is billed after the first request, the same tokens come to about $0.43.
Recording the cache split per arm will let us check this directly rather than estimate it, and
we'll also look at saving vs run length as suggested.

Happy to move this to Discussions if you prefer. We'll post the rerun results here or there,
whichever you'd like.
