"""Draft task specs for skills that no task tests. Drafts need a human and a fixture before use."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import List, Optional

from .agent import _child_env, find_claude
from .skills import Skill

PROMPT = """You design benchmark tasks that test whether an AI coding-agent skill helps.

Skill name: {name}
Skill description (its claim): {description}

Propose ONE small, self-contained coding task where an agent WITH this skill should do
measurably better than one without it. It must be checkable by a script with exit code 0/1,
using only the Python standard library, and finish in a few minutes.

Reply with only a JSON object, no prose:
{{"id": "kebab-case-id", "title": "...", "tags": ["words from the claim"],
  "prompt": "what the agent is told", "fixture_files": {{"path": "starting content"}},
  "hidden_files": {{"path": "check script content"}}, "check": "{{python}} check_x.py",
  "protect": ["files the agent must not edit"]}}"""


def draft_task(skill: Skill, model: str, timeout: int = 300) -> Optional[dict]:
    binary = find_claude()
    if not binary:
        raise RuntimeError("claude CLI not found")
    proc = subprocess.run(
        [binary, "-p", "--output-format", "json", "--model", model,
         "--permission-mode", "dontAsk", "--allowedTools", "", "--no-session-persistence"],
        input=PROMPT.format(name=skill.name, description=skill.description or "(none)"),
        capture_output=True, text=True, timeout=timeout, env=_child_env(),
    )
    try:
        text = json.loads(proc.stdout).get("result", "")
    except ValueError:
        return None
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except ValueError:
        return None


def write_draft(draft: dict, skill: Skill, out_dir: Path) -> Path:
    """Write the task JSON plus fixture/hidden folders. Status stays 'draft' until a human
    checks that the fixture fails the check and a correct solution passes it."""
    tid = re.sub(r"[^a-z0-9-]", "-", str(draft.get("id") or skill.name).lower()).strip("-")
    # Same layout as a suite, so a reviewed draft can be moved over as is.
    dirs = {"fixture": out_dir / "fixtures" / tid, "hidden": out_dir / "fixtures" / f"{tid}-hidden"}
    for kind, base in dirs.items():
        for rel, content in (draft.get(f"{kind}_files") or {}).items():
            path = (base / rel).resolve()
            if base.resolve() not in path.parents:
                continue  # never write outside the draft folder
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(str(content), encoding="utf-8")
    spec = {
        "id": tid, "status": "draft", "drafted_for": skill.id,
        "title": draft.get("title", tid), "tags": draft.get("tags", []),
        "prompt": draft.get("prompt", ""), "check": draft.get("check", ""),
        "fixture": f"fixtures/{tid}", "hidden": f"fixtures/{tid}-hidden",
        "protect": draft.get("protect", []),
    }
    path = out_dir / "tasks" / f"{tid}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    return path


def suggest(skills: List[Skill], model: str, out_dir: Path, log=print) -> int:
    n = 0
    for skill in skills:
        draft = draft_task(skill, model)
        if not draft:
            log(f"{skill.id}: no usable draft")
            continue
        log(f"{skill.id}: drafted {write_draft(draft, skill, out_dir)}")
        n += 1
    return n
