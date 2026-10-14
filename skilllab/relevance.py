"""Decide which skill/task pairs are worth running.

Keyword matching (tasks.matches) only proposes candidates: a shared word like "git" or
"test" pairs a skill that installs git hooks with a task about finding a regression. A
cheap model call then judges each candidate, and its yes/no plus a reason is saved to
matches.json, which you can read and edit. Entries already in the file are never re-judged,
so your edits stick.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from .agent import _child_env, find_claude
from .skills import Skill
from .tasks import Task, matches

JUDGE_MODEL = "claude-haiku-5-5"
BATCH = 15

CRITERIA = """For each numbered pair, decide whether the task is a fair test of the skill.

Relevant means the skill's own "use when" condition is clearly met by the task exactly as
given: an engineer doing this task would reasonably reach for this skill. (For a skill marked
"started by a person", ask whether a person would reasonably start it for this task.)

NOT relevant when:
- the skill is about a different activity that only shares a topic word (installing git
  hooks is not finding which commit broke something; migrating test assertions is not
  writing tests);
- it needs things the task doesn't provide: an existing plan or spec document, review
  feedback, an issue tracker, a past agent session, another language or library;
- it needs a back-and-forth conversation with a person.

Answer for every pair. Keep each reason under 15 words."""

SCHEMA = {
    "type": "object",
    "properties": {"pairs": {"type": "array", "items": {
        "type": "object",
        "properties": {"i": {"type": "integer"}, "relevant": {"type": "boolean"},
                       "reason": {"type": "string"}},
        "required": ["i", "relevant", "reason"]}}},
    "required": ["pairs"],
}

Judge = Callable[[List[Tuple[Skill, Task]]], Tuple[Dict[int, dict], float]]


def pair_key(skill_id: str, task_id: str) -> str:
    return f"{skill_id}|{task_id}"


def candidates(skills: List[Skill], tasks: List[Task]) -> List[Tuple[Skill, Task]]:
    return [(s, t) for s in skills for t in tasks if matches(s, t)]


def _prompt(batch: List[Tuple[Skill, Task]]) -> str:
    parts = [CRITERIA, ""]
    for i, (s, t) in enumerate(batch):
        who = " (started by a person, never by the agent)" if s.user_invoked else ""
        parts += [f"## Pair {i}",
                  f"Skill `{s.name}`{who}: {s.description[:600]}",
                  f"Task `{t.id}` ({t.title}): {t.prompt[:900]}", ""]
    return "\n".join(parts)


def claude_judge(model: str = JUDGE_MODEL, binary: Optional[str] = None) -> Judge:
    """A judge that asks Claude Code, with no tools, for structured yes/no answers."""
    binary = binary or find_claude()

    def judge(batch):
        if not binary:
            raise RuntimeError("claude CLI not found")
        with tempfile.TemporaryDirectory(prefix="skilllab-judge-") as cwd:
            proc = subprocess.run(
                [binary, "-p", "--output-format", "json", "--model", model, "--tools", "",
                 "--json-schema", json.dumps(SCHEMA), "--setting-sources", "project",
                 "--no-session-persistence"],
                input=_prompt(batch), capture_output=True, text=True, cwd=cwd,
                env=_child_env(), timeout=300)
        try:
            out = json.loads(proc.stdout)
        except ValueError:
            raise RuntimeError(f"relevance check failed: {(proc.stderr or proc.stdout)[-300:]}")
        if out.get("is_error"):
            raise RuntimeError(f"relevance check failed: {str(out.get('result'))[:300]}")
        data = out.get("structured_output")
        if data is None:
            text = out.get("result") or ""
            data = json.loads(text[text.find("{"): text.rfind("}") + 1])
        answers = {a["i"]: a for a in data.get("pairs", []) if isinstance(a.get("i"), int)}
        return answers, float(out.get("total_cost_usd") or 0)

    return judge


def load(path: Optional[Path]) -> Dict[str, dict]:
    if path and path.is_file():
        return json.loads(path.read_text(encoding="utf-8")).get("pairs", {})
    return {}


def save(path: Path, decisions: Dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {"_how": "relevant pairs are run; edit 'relevant' to change that. "
                    "by: judge (model), keyword (no judge), manual (--pair or your edit)",
            "pairs": dict(sorted(decisions.items()))}
    path.write_text(json.dumps(body, indent=2), encoding="utf-8")


def decide(skills: List[Skill], tasks: List[Task], known: Dict[str, dict],
           judge: Optional[Judge] = None, manual: Optional[List[str]] = None,
           log: Callable[[str], None] = print) -> Tuple[Dict[str, dict], float]:
    """Return {pair_key: {relevant, reason, by}} for every candidate and manual pair.

    known: earlier decisions (kept as they are). judge: None means keyword matches count
    as relevant. manual: "skill:task" pairs that are relevant whatever else says.
    """
    decisions = dict(known)
    cost = 0.0
    todo = [(s, t) for s, t in candidates(skills, tasks) if pair_key(s.id, t.id) not in decisions]
    if todo and judge is None:
        for s, t in todo:
            decisions[pair_key(s.id, t.id)] = {"relevant": True, "reason": "keyword match", "by": "keyword"}
    elif todo:
        log(f"Checking relevance of {len(todo)} skill/task candidates with {JUDGE_MODEL}…")
        for start in range(0, len(todo), BATCH):
            batch = todo[start:start + BATCH]
            answers, spent = judge(batch)
            cost += spent
            for i, (s, t) in enumerate(batch):
                a = answers.get(i)
                if a is None:
                    continue  # unanswered: asked again next time
                decisions[pair_key(s.id, t.id)] = {"relevant": bool(a["relevant"]),
                                                   "reason": str(a.get("reason", ""))[:200], "by": "judge"}
    by_name = {}
    for s in skills:
        by_name.setdefault(s.name, s)
        by_name[s.id] = s
    task_ids = {t.id for t in tasks}
    for spec in manual or []:
        name, _, task_id = spec.rpartition(":")
        s = by_name.get(name)
        if s is None or task_id not in task_ids:
            raise ValueError(f"--pair {spec}: unknown skill or task")
        decisions[pair_key(s.id, task_id)] = {"relevant": True, "reason": "chosen with --pair", "by": "manual"}
    return decisions, cost


def relevant_pairs(decisions: Dict[str, dict]) -> set:
    return {tuple(k.rsplit("|", 1)) for k, d in decisions.items() if d.get("relevant")}
