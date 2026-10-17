"""Task suite: what each task asks, how it is checked, and which skills it tests."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .skills import Skill

DEFAULT_SUITE = Path(__file__).parent / "suite"


@dataclass
class Task:
    id: str
    title: str
    prompt: str
    check: str  # shell command run in the workspace after the agent; exit 0 = pass
    tags: List[str]
    fixture: Path  # starting files copied into a fresh workspace
    hidden: Optional[Path] = None  # copied in only after the agent finishes
    protect: List[str] = field(default_factory=list)  # files the agent must not change
    timeout: int = 900
    tier: str = "standard"  # "easy" tasks are for smoke tests; most models pass them
    setup: Optional[Path] = None  # folder with _setup.py, run in the workspace then removed
    tools: List[str] = field(default_factory=list)  # extra tools this task allows (e.g. git)
    requires: List[str] = field(default_factory=list)  # programs that must be on PATH
    base: Optional[Path] = None  # shared project copied first; the fixture is laid over it

    def meta(self) -> dict:
        return {"id": self.id, "title": self.title, "tags": self.tags, "tier": self.tier}

    def missing(self) -> List[str]:
        return [r for r in self.requires if not shutil.which(r)]


# easy: smoke tests. standard: short focused tasks. project: work inside one shared, realistic
# project (many files, git, test runs, logs), where token savers and memory tools have room to act.
TIERS = ("easy", "standard", "project", "all")


def load_suite(suite_dir: Path = DEFAULT_SUITE, tier: str = "all") -> List[Task]:
    tasks = []
    for path in sorted((suite_dir / "tasks").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("status") == "draft":
            continue
        task_tier = data.get("tier", "standard")
        if tier != "all" and task_tier != tier:
            continue
        fixture = suite_dir / data["fixture"]
        hidden = suite_dir / data["hidden"] if data.get("hidden") else None
        tasks.append(
            Task(
                id=data["id"],
                title=data.get("title", data["id"]),
                prompt=data["prompt"],
                check=data["check"],
                tags=[t.lower() for t in data.get("tags", [])],
                fixture=fixture,
                hidden=hidden,
                protect=data.get("protect", []),
                timeout=int(data.get("timeout", 900)),
                tier=task_tier,
                setup=suite_dir / data["setup"] if data.get("setup") else None,
                tools=data.get("tools", []),
                requires=data.get("requires", []),
                base=suite_dir / data["base"] if data.get("base") else None,
            )
        )
    return tasks


def load_suites(suite_dirs: List[Path], tier: str = "all") -> List[Task]:
    """Tasks from several suites (e.g. the public one plus a private, held-out one)."""
    tasks, seen = [], {}
    for d in suite_dirs:
        for t in load_suite(Path(d), tier):
            if t.id in seen:
                raise ValueError(f"task id {t.id!r} is in both {seen[t.id]} and {d}")
            seen[t.id] = d
            tasks.append(t)
    return tasks


def _claim_text(skill: Skill) -> str:
    return (re.sub(r"[-_]", " ", skill.name) + " " + skill.description).lower()


def matches(skill: Skill, task: Task) -> bool:
    """A task tests a skill when one of its tags appears as a word in the skill's claim."""
    text = _claim_text(skill)
    return any(re.search(r"\b" + re.escape(tag) + r"\b", text) for tag in task.tags)
