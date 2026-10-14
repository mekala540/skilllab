"""Agents that attempt a task inside a workspace.

Both agents speak Claude Code's stream-json output, so a fake agent in tests reports
cost and skill use the same way the real one does.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# What the agent may do without asking. Anything else is denied (dontAsk mode),
# so a skill's own scripts do not run unless the task allows them.
DEFAULT_TOOLS = [
    "Read", "Edit", "Write", "Glob", "Grep", "Skill",
    "Bash(python3:*)", "Bash(python:*)", "Bash(ls:*)", "Bash(cat:*)",
]

# Told to the agent in both arms, so neither wastes the run discovering the sandbox rules.
ENV_NOTE = (
    "You are working in a locked-down benchmark workspace. Shell commands must be single simple "
    "commands: no loops, pipes, `;`, `&&` or redirection. Commands allowed: {commands}. For "
    "anything multi-step, write a Python script with the Write tool and run it with python3. "
    "Work only inside the current directory."
)

# Set by a parent Claude Code session; a nested CLI refuses or misbehaves with them.
_PARENT_ENV = ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_SSE_PORT")


@dataclass
class AgentResult:
    infra_error: str = ""  # the agent never really ran: these runs are excluded
    note: str = ""  # ran but ended badly (timeout, max turns): counts as a failed attempt
    duration: float = 0.0
    cost_usd: Optional[float] = None
    input_tokens: int = 0
    output_tokens: int = 0
    turns: Optional[int] = None
    skills_invoked: List[str] = field(default_factory=list)


def parse_stream(text: str) -> AgentResult:
    """Read Claude Code stream-json: Skill tool calls and the final result event."""
    res = AgentResult()
    saw_result = False
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        kind = ev.get("type")
        if kind == "assistant":
            for block in (ev.get("message") or {}).get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Skill":
                    args = block.get("input") or {}
                    res.skills_invoked.append(str(args.get("skill") or args.get("command") or args.get("name") or ""))
        elif kind == "result":
            saw_result = True
            usage = ev.get("usage") or {}
            res.cost_usd = ev.get("total_cost_usd")
            res.input_tokens = sum(
                int(usage.get(k) or 0)
                for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
            )
            res.output_tokens = int(usage.get("output_tokens") or 0)
            res.turns = ev.get("num_turns")
            if ev.get("is_error"):
                detail = " ".join(str(x) for x in (ev.get("subtype"), ev.get("result")) if x)[:500] or "error"
                # An error before any real work (bad auth, bad flag) is infrastructure.
                if (res.turns or 0) <= 1 and not res.cost_usd:
                    res.infra_error = detail
                else:
                    res.note = detail
    if not saw_result:
        res.infra_error = res.infra_error or "agent produced no result event"
    return res


def _child_env() -> dict:
    env = dict(os.environ)
    for key in _PARENT_ENV:
        env.pop(key, None)
    return env


def _run(cmd: List[str], cwd: Path, timeout: int, stdin: Optional[str]) -> AgentResult:
    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd, cwd=str(cwd), input=stdin, capture_output=True, text=True,
            timeout=timeout, env=_child_env(),
        )
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        res = parse_stream(out)
        res.infra_error = ""
        res.note = f"timeout after {timeout}s"
        res.duration = time.monotonic() - start
        return res
    except OSError as exc:
        return AgentResult(infra_error=f"could not start agent: {exc}")
    res = parse_stream(proc.stdout)
    if res.infra_error and proc.returncode != 0 and res.infra_error == "agent produced no result event":
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-1:] or [""]
        res.infra_error = f"exit {proc.returncode}: {tail[0][:500]}"
    elif res.infra_error and proc.returncode != 0:
        res.infra_error = f"exit {proc.returncode}: {res.infra_error}"
    res.duration = time.monotonic() - start
    return res


def env_note(tools: List[str]) -> str:
    commands = sorted({t[5:-1].split(":")[0].split(" ")[0] for t in tools if t.startswith("Bash(")})
    return ENV_NOTE.format(commands=", ".join(commands) or "none")


def find_claude() -> Optional[str]:
    found = shutil.which("claude")
    if found:
        return found
    local = Path.home() / ".local" / "bin" / "claude"
    return str(local) if local.exists() else None


class ClaudeAgent:
    """Claude Code in headless mode, restricted to an allowlist of tools."""

    def __init__(self, model: str, tools: Optional[List[str]] = None,
                 max_budget_usd: Optional[float] = None, binary: Optional[str] = None):
        self.model = model
        self.tools = tools or DEFAULT_TOOLS
        self.max_budget_usd = max_budget_usd
        self.binary = binary or find_claude()

    def run(self, prompt: str, cwd: Path, timeout: int, tools: Optional[List[str]] = None,
            plugin_dirs: Optional[List[Path]] = None) -> AgentResult:
        if not self.binary:
            return AgentResult(infra_error="claude CLI not found on PATH or in ~/.local/bin")
        cmd = [
            self.binary, "-p",
            "--output-format", "stream-json", "--verbose",
            "--model", self.model,
            "--permission-mode", "dontAsk",
            "--allowedTools", ",".join(self.tools + list(tools or [])),
            "--setting-sources", "project",
            "--no-session-persistence",
        ]
        if self.max_budget_usd:
            cmd += ["--max-budget-usd", str(self.max_budget_usd)]
        for d in plugin_dirs or []:
            cmd += ["--plugin-dir", str(d)]
        cmd += ["--append-system-prompt", env_note(self.tools + list(tools or []))]
        # Prompt goes on stdin so it can't be mistaken for another --allowedTools value.
        return _run(cmd, cwd, timeout, stdin=prompt)


class CommandAgent:
    """Any command. {prompt_file} is replaced by a file holding the prompt.

    Used for tests and for plugging in other agents. Runs in the workspace.
    """

    def __init__(self, template: str):
        self.template = template

    def run(self, prompt: str, cwd: Path, timeout: int, tools: Optional[List[str]] = None,
            plugin_dirs: Optional[List[Path]] = None) -> AgentResult:
        fd, prompt_file = tempfile.mkstemp(prefix="skilllab-prompt-", suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(prompt)
            cmd = [part.replace("{prompt_file}", prompt_file) for part in shlex.split(self.template)]
            return _run(cmd, cwd, timeout, stdin=None)
        finally:
            os.unlink(prompt_file)
