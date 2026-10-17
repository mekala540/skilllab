# Headroom

- **Repo:** https://github.com/headroomlabs-ai/headroom (formerly `chopratejas/headroom`)
- **Followed:** release `v0.41.0` (commit `76133cf`, 14 October 2026): `README.md`, `docs/content/docs/quickstart.mdx` ("Alternative: proxy mode") and `docs/content/docs/proxy.mdx`.
- **Claims:** "20% fewer tokens for coding agents, 60-95% fewer tokens for JSON, same answers" (repo description). Its README proof table shows 21–57% on four MCP-output scenarios, and says short exchanges and dense output "see little or no reduction".

## How it installs

```bash
uv tool install --python 3.13 "headroom-ai[all]==0.41.0"   # or: pip install "headroom-ai[all]"
headroom proxy --host 127.0.0.1 --port 8787                  # proxy mode, zero code changes
ANTHROPIC_BASE_URL=http://127.0.0.1:8787 claude              # point Claude Code at it
```

## How this add-on maps it

| Install step | Here |
| --- | --- |
| `headroom proxy --host 127.0.0.1 --port 8787` | **You start it** in another terminal before the batch, and leave it running, with `--no-cache` (see below) |
| `ANTHROPIC_BASE_URL=http://127.0.0.1:8787` | `env`, set for the agent only |
| Proxy must be up | `setup` calls the documented `GET /health` endpoint, so a stopped proxy fails as an infrastructure error (retried on resume) instead of counting as failed runs |

This tests **proxy mode** only. `headroom wrap claude` also installs the Serena MCP server (registered in `~/.claude.json`) and can turn on memory. That's a different, larger setup that skilllab can't reproduce per workspace. Output shaping (`HEADROOM_OUTPUT_SHAPER=1`) is off by default and stays off here.

Start it for a batch with:

```bash
HEADROOM_BEACON=off headroom proxy --host 127.0.0.1 --port 8787 --no-cache
```

- `--host 127.0.0.1` keeps the proxy off your network.
- `HEADROOM_BEACON=off`: Headroom sends an anonymous beacon by default (compression ratios, model IDs, no prompts or code).
- `--no-cache`: **this add-on is measured on compression alone.** Besides compression, the proxy has a "semantic cache" that is on by default (`docs/content/docs/proxy.mdx`). Despite the name it's a response cache: keyed on a hash of the messages, a hit replays the stored reply without asking the API (`headroom/proxy/semantic_cache.py`; only non-streaming requests, `handlers/anthropic.py`). skilllab repeats the same task several times per arm, so a response cache could replay answers across repeats and inflate the savings in a way real use, where requests rarely repeat exactly, wouldn't.

## Is it a fair test here?

Partly. Headroom sits in front of every request, so skilllab's Bash allowlist doesn't stop it from running. But it doesn't compress everything:

- **It skips the agent's main tools.** The proxy's default `exclude_tools` (shown by `GET /health` on 0.41.0) includes `Read`, `Grep`, `Glob`, `Edit`, `Write` and `Skill`. skilllab's agent works mostly through those tools. What's left to compress here is mainly Bash output (`python3`, `ls`, `cat`) and user messages.
- **Small tasks.** By its own docs it pays off on long sessions with heavy tool output. skilllab's tasks are short with small files.

In pilot 3, most of the input saving came from deferring Claude Code's tool definitions (Headroom's tool search: about 3.3M tool-schema tokens held back, against 132k tokens removed by compressing content), not from compressing content.

Expect a small saving from compression at most. Read "same cost" as "no difference at this task size and tool mix", not "Headroom doesn't work".

Run one proxy per batch. Every run shares it, so its compression cache and stats cover the whole batch, and the baseline arm doesn't go through it.

## Results so far

Pilot 3 (17 October 2026): `skilllab compare` with rtk, Headroom, caveman and the no-op control arm, `--task fix-pagination --repeats 5 --model claude-haiku-5-5`. 30 runs, all passed, 0 infrastructure errors, $0.18. The control arm came out *same cost* (+2% [-14 to 22]), so the batch shows no bias. One easy task (`fix-pagination`), Haiku 5.5 only, 5 repeats per arm, so read these as a first look, not a verdict on the tool.

| Verdict | Cost | Input tokens | Output tokens | Pass rate |
| --- | --- | --- | --- | --- |
| **cheaper** | -33% [-36 to -13] | -46% | -7% | 0 pts |

Run with `--no-cache`; the proxy's `/stats` showed the response cache off and no replayed replies. Its 38 "cached" requests were Anthropic's own prompt-cache hits, which the baseline gets too.
