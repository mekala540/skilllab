# Headroom

- **Repo:** https://github.com/headroomlabs-ai/headroom (formerly `chopratejas/headroom`)
- **Followed:** release `v0.41.0` (commit `76133cf`, 14 October 2026): `README.md`, `docs/content/docs/quickstart.mdx` ("Alternative: proxy mode") and `docs/content/docs/proxy.mdx`.
- **Claims:** "20% fewer tokens for coding agents, 60-95% fewer tokens for JSON, same answers" (repo description). Its README proof table shows 21–57% on four MCP-output scenarios, and says short exchanges and dense output "see little or no reduction".

## How it installs

```bash
uv tool install --python 3.13 "headroom-ai[all]==0.41.0"   # or: pip install "headroom-ai[all]"
headroom proxy --host 127.0.0.1 --port 8787                                   # proxy mode, zero code changes
ANTHROPIC_BASE_URL=http://127.0.0.1:8787 claude              # point Claude Code at it
```

## How this add-on maps it

| Install step | Here |
| --- | --- |
| `headroom proxy --host 127.0.0.1 --port 8787` | **You start it** in another terminal before the batch, and leave it running |
| `ANTHROPIC_BASE_URL=http://127.0.0.1:8787` | `env`, set for the agent only |
| Proxy must be up | `setup` calls the documented `GET /health` endpoint, so a stopped proxy fails as an infrastructure error (retried on resume) instead of counting as failed runs |

This tests **proxy mode** only. `headroom wrap claude` also installs the Serena MCP server (registered in `~/.claude.json`) and can turn on memory. That's a different, larger setup that skilllab can't reproduce per workspace. Output shaping (`HEADROOM_OUTPUT_SHAPER=1`) is off by default and stays off here.

Telemetry: Headroom sends an anonymous beacon by default (compression ratios, model IDs, no prompts or code). To turn it off, start the proxy with `HEADROOM_BEACON=off headroom proxy --host 127.0.0.1 --port 8787`.

## Is it a fair test here?

Partly. Headroom sits in front of every request, so skilllab's Bash allowlist doesn't stop it from running. But it doesn't compress everything:

- **It skips the agent's main tools.** The proxy's default `exclude_tools` (shown by `GET /health` on 0.41.0) includes `Read`, `Grep`, `Glob`, `Edit`, `Write` and `Skill`. skilllab's agent works mostly through those tools. What's left to compress here is mainly Bash output (`python3`, `ls`, `cat`) and user messages.
- **Small tasks.** By its own docs it pays off on long sessions with heavy tool output. skilllab's tasks are short with small files.

Expect a small saving at most. Read "same cost" as "no difference at this task size and tool mix", not "Headroom doesn't work".

Run one proxy per batch. Every run shares it, so its cache and stats cover the whole batch, and the baseline arm doesn't go through it.
