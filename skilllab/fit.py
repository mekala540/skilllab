"""fit: which skills does *your* work need?

Give it your tasks (and, to measure, your project and a check command). Step 1, triage, asks a
cheap model which skills fit each task and adds up the tokens spent every session on skills
that fit none of them. Step 2, --measure, runs your tasks in copies of your project with and
without each fitting skill, through the same runner, verdicts and reports as the suite.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from .agent import _child_env, find_claude
from .relevance import JUDGE_MODEL, pair_key
from .skills import Pack, Skill, packs
from .tasks import Task

# Never copied into run workspaces: rebuildable and often huge.
PROJECT_IGNORE = ["node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache",
                  "dist", "build", ".next", "target", ".tox"]
SKILLS_PER_CALL = 60

FIT_CRITERIA = """Below is one task a developer needs done, and a list of agent skills.
List every skill that fits this task: its own "use when" condition is clearly met by the task
as written, so an agent doing it would reasonably use the skill. (For a skill marked "started
by a person", list it if a person would reasonably start it for this task.)

Leave a skill out when it only shares a topic word with the task, needs things the task
doesn't mention (an existing plan, review feedback, an issue tracker, another language or
framework), or needs a back-and-forth conversation with a person.

Give each listed skill a reason under 15 words. List nothing if nothing fits."""

FIT_SCHEMA = {
    "type": "object",
    "properties": {"fits": {"type": "array", "items": {
        "type": "object",
        "properties": {"skill": {"type": "string"}, "reason": {"type": "string"}},
        "required": ["skill", "reason"]}}},
    "required": ["fits"],
}

FitJudge = Callable[[Task, List[Skill], str], Tuple[Dict[str, str], float]]


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "task"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


HEADING = re.compile(r"^(?:#{1,3}|h[1-3]\.)\s+(.+)$")  # markdown or Jira wiki headings
ISSUE_KEY = re.compile(r"^\s*\[?([A-Z][A-Z0-9]+-\d+)\]?\s*[:\-–]?\s*(.*)$")
BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")
SEPARATOR = re.compile(r"^\s*-{3,}\s*$")
CHECK_LINE = re.compile(r"^\s*check:\s*(.+)$", re.I)


def _blocks_from_text(text: str) -> List[Tuple[str, List[str], str]]:
    """(title, body lines, issue key) per task, from pasted text.

    - `# Title` / `## Title` / Jira `h1. Title` lines start tasks.
    - Otherwise, lines that start with an issue key (`SHOP-482: Summary`) start tasks.
    - Otherwise, `---` lines separate tasks; a list where every line is a bullet is one task
      per line; anything else (a pasted story with its acceptance criteria) is ONE task.
    """
    lines = text.splitlines()
    blocks: List[Tuple[str, List[str], str]] = []
    if any(HEADING.match(l) for l in lines):
        for line in lines:
            m = HEADING.match(line)
            if m:
                key_m = ISSUE_KEY.match(m.group(1))
                if key_m and key_m.group(2):
                    blocks.append((key_m.group(2).strip(), [], key_m.group(1)))
                else:
                    blocks.append((m.group(1).strip(), [], ""))
            elif blocks:
                blocks[-1][1].append(line)
        return blocks
    if any(ISSUE_KEY.match(l) and ISSUE_KEY.match(l).group(2) for l in lines if l.strip()):
        for line in lines:
            m = ISSUE_KEY.match(line)
            if m and m.group(2) and not BULLET.match(line):
                blocks.append((m.group(2).strip(), [], m.group(1)))
            elif blocks:
                blocks[-1][1].append(line)
        return blocks
    chunks: List[List[str]] = [[]]
    for line in lines:
        if SEPARATOR.match(line):
            chunks.append([])
        else:
            chunks[-1].append(line)
    for chunk in chunks:
        content = [l for l in chunk if l.strip() and not CHECK_LINE.match(l)]
        if not content:
            continue
        if len(chunks) == 1 and all(BULLET.match(l) for l in content):
            blocks += [(BULLET.sub("", l).strip(), [], "") for l in content]
            continue
        first = next(i for i, l in enumerate(chunk) if l.strip())
        blocks.append((chunk[first].strip(), chunk[first + 1:], ""))
    return blocks


def _adf_text(node) -> str:
    """Plain text from Atlassian Document Format (Jira Cloud API v3 descriptions)."""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(_adf_text(n) for n in node)
    if not isinstance(node, dict):
        return ""
    kind = node.get("type")
    if kind == "text":
        return node.get("text", "")
    if kind == "hardBreak":
        return "\n"
    inner = _adf_text(node.get("content", []))
    if kind == "listItem":
        return "- " + inner.strip() + "\n"
    if kind in ("paragraph", "heading", "codeBlock", "blockquote"):
        return inner.strip() + "\n\n"
    return inner


def _blocks_from_jira_json(data) -> List[Tuple[str, List[str], str]]:
    """A Jira issue, a search result ({"issues": [...]}) or a list of issues, as returned by
    Jira's REST API. Acceptance criteria are found by field name when the response has "names"."""
    names = data.get("names", {}) if isinstance(data, dict) else {}
    issues = data.get("issues") if isinstance(data, dict) and "issues" in data else \
        data if isinstance(data, list) else [data]
    blocks = []
    for issue in issues:
        fields = issue.get("fields", {}) if isinstance(issue, dict) else {}
        summary = (fields.get("summary") or "").strip()
        if not summary:
            continue
        body = _adf_text(fields.get("description") or "").strip()
        for fid, label in names.items():
            if "acceptance" in str(label).lower() and fields.get(fid):
                body += "\n\nAcceptance criteria:\n" + _adf_text(fields[fid]).strip()
        blocks.append((summary, body.splitlines(), issue.get("key", "")))
    return blocks


def _blocks_from_csv(text: str) -> List[Tuple[str, List[str], str]]:
    """A Jira CSV export (or any CSV with Summary/Description columns; optional Check)."""
    import csv
    import io
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return []
    header = [h.strip().lower() for h in rows[0]]

    def col(*names):
        for i, h in enumerate(header):
            if h in names:
                return i
        return None

    key_i, sum_i = col("issue key", "key"), col("summary", "title")
    desc_i, check_i = col("description"), col("check")
    ac_i = next((i for i, h in enumerate(header) if "acceptance" in h), None)
    if sum_i is None:
        raise ValueError("CSV needs a 'Summary' (or 'Title') column")
    blocks = []
    for row in rows[1:]:
        get = lambda i: row[i].strip() if i is not None and i < len(row) else ""
        if not get(sum_i):
            continue
        body = get(desc_i)
        if get(ac_i):
            body += "\n\nAcceptance criteria:\n" + get(ac_i)
        if get(check_i):
            body += "\ncheck: " + get(check_i)
        blocks.append((get(sum_i), body.splitlines(), get(key_i)))
    return blocks


def _tasks_from_blocks(blocks, project, default_check, tools, hidden) -> List[Task]:
    tasks, seen = [], set()
    for title, lines, key in blocks:
        check = default_check
        body = []
        for line in lines:
            m = CHECK_LINE.match(line)
            if m:
                check = m.group(1).strip()
            else:
                body.append(line)
        text = "\n".join(body).strip()
        heading = f"{key}: {title}" if key else title
        prompt = f"{heading}\n\n{text}" if text else heading
        tid = base = _slug(key or title)
        n = 2
        while tid in seen:
            tid, n = f"{base}-{n}", n + 1
        seen.add(tid)
        tasks.append(Task(id=tid, title=heading, prompt=prompt, check=check or "", tags=[],
                          fixture=project or Path("."), hidden=hidden, tools=list(tools or []),
                          ignore=list(PROJECT_IGNORE)))
    return tasks


def parse_tasks(text: str, project: Optional[Path] = None, default_check: Optional[str] = None,
                tools: Optional[List[str]] = None, hidden: Optional[Path] = None,
                fmt: str = "auto") -> List[Task]:
    """Tasks from tasks.md-style text, a pasted story, Jira text, a Jira CSV export or Jira JSON.

    fmt: auto (detect), text, csv or json. A `check: <command>` line in a task sets its check;
    the agent never sees it. hidden: a folder of check files copied in only after the agent.
    """
    stripped = text.lstrip()
    if fmt == "auto":
        if stripped.startswith(("{", "[")):
            fmt = "json"
        elif re.match(r'^﻿?"?(issue key|key|summary|title|issue type|issue id)"?\s*,', stripped, re.I):
            fmt = "csv"
        else:
            fmt = "text"
    if fmt == "json":
        blocks = _blocks_from_jira_json(json.loads(text))
    elif fmt == "csv":
        blocks = _blocks_from_csv(text.lstrip("﻿"))
    else:
        blocks = _blocks_from_text(text)
    return _tasks_from_blocks(blocks, project, default_check, tools, hidden)


def story_task(text: str, **kw) -> List[Task]:
    """One task from one piece of text (e.g. --task-text), however many lines it has."""
    lines = [l for l in text.strip().splitlines()]
    if not lines:
        return []
    m = ISSUE_KEY.match(lines[0])
    title, key = (m.group(2).strip(), m.group(1)) if m and m.group(2) else (lines[0].strip(), "")
    return _tasks_from_blocks([(title, lines[1:], key)], kw.get("project"), kw.get("default_check"),
                              kw.get("tools"), kw.get("hidden"))


LANGS = {".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript", ".js": "JavaScript",
         ".jsx": "JavaScript", ".mjs": "JavaScript", ".go": "Go", ".rs": "Rust", ".java": "Java",
         ".kt": "Kotlin", ".rb": "Ruby", ".php": "PHP", ".cs": "C#", ".swift": "Swift",
         ".c": "C", ".cpp": "C++", ".scala": "Scala", ".sql": "SQL", ".sh": "Shell",
         ".vue": "Vue", ".svelte": "Svelte"}
KNOWN_DEPS = ["react", "next", "vue", "svelte", "angular", "express", "nestjs", "typescript", "jest",
              "vitest", "mocha", "playwright", "cypress", "eslint", "prettier", "husky", "lint-staged",
              "django", "flask", "fastapi", "pytest", "sqlalchemy", "pandas", "numpy", "torch",
              "celery", "pydantic", "spring", "rails", "terraform"]
MAX_FILES = 20000


def profile_project(root: Path) -> dict:
    """What a skill's fit depends on, read from the files (no model calls): languages,
    frameworks and tools, tests, git, CI, docs."""
    langs: Dict[str, int] = {}
    tests = 0
    files = 0
    names = set()
    for path in root.rglob("*"):
        rel = path.relative_to(root).parts
        if any(part in PROJECT_IGNORE or part == ".git" for part in rel):
            continue
        if not path.is_file():
            continue
        files += 1
        if files > MAX_FILES:
            break
        names.add(path.name)
        lang = LANGS.get(path.suffix.lower())
        if lang:
            langs[lang] = langs.get(lang, 0) + 1
        if re.search(r"(^|/)(tests?|__tests__|spec)(/|$)", "/".join(rel)) or \
                re.search(r"(^test_.*\.py|_test\.(py|go)|\.(test|spec)\.[jt]sx?)$", path.name):
            tests += 1
    deps = set()
    for manifest in ("package.json", "pyproject.toml", "requirements.txt", "setup.py", "setup.cfg",
                     "Pipfile", "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "Gemfile"):
        f = root / manifest
        if f.is_file():
            text = f.read_text(encoding="utf-8", errors="replace").lower()
            deps.update(d for d in KNOWN_DEPS if re.search(r"(^|[\"'\s/@])" + re.escape(d) + r"($|[\"'\s=<>~^\[:])", text, re.M))
    ci = [c for c, present in (
        ("GitHub Actions", (root / ".github" / "workflows").is_dir()),
        ("GitLab CI", (root / ".gitlab-ci.yml").is_file()),
        ("Bitbucket Pipelines", (root / "bitbucket-pipelines.yml").is_file()),
        ("Jenkins", (root / "Jenkinsfile").is_file())) if present]
    return {
        "files": min(files, MAX_FILES),
        "languages": [l for l, _ in sorted(langs.items(), key=lambda kv: -kv[1])[:5]],
        "tools": sorted(deps),
        "manifests": sorted(n for n in names if n in ("package.json", "pyproject.toml", "requirements.txt",
                                                      "go.mod", "Cargo.toml", "pom.xml", "Gemfile")),
        "test_files": tests,
        "git": (root / ".git").exists(),
        "ci": ci,
        "docs": sorted(n for n in names if n.upper() in ("README.MD", "CLAUDE.MD", "AGENTS.MD", "CONTRIBUTING.MD")),
    }


def profile_text(profile: Optional[dict]) -> str:
    if not profile:
        return ""
    p = profile
    return "\n".join([
        f"- {p['files']} files; main languages: {', '.join(p['languages']) or 'unknown'}",
        f"- frameworks and tools: {', '.join(p['tools']) or 'none detected'}",
        f"- tests: {p['test_files']} test file{'' if p['test_files'] == 1 else 's'}"
        + ("" if p["test_files"] else " (no tests found)"),
        f"- git repository: {'yes' if p['git'] else 'no'}; CI: {', '.join(p['ci']) or 'none'}",
        f"- docs: {', '.join(p['docs']) or 'none'}",
    ])


def _fit_prompt(task: Task, skills: List[Skill], profile: str = "") -> str:
    lines = [FIT_CRITERIA, ""]
    if profile:
        lines += ["## The project this task is in", profile,
                  "A skill for a language, framework or tool the project doesn't use does not fit.", ""]
    lines += ["## Task", task.prompt[:3000], "", "## Skills"]
    for s in skills:
        who = " (started by a person)" if s.user_invoked else ""
        lines.append(f"- `{s.name}`{who}: {s.description[:400]}")
    return "\n".join(lines)


def claude_fit_judge(model: str = JUDGE_MODEL, binary: Optional[str] = None) -> FitJudge:
    binary = binary or find_claude()

    def judge(task, skills, profile=""):
        if not binary:
            raise RuntimeError("claude CLI not found")
        fits: Dict[str, str] = {}
        cost = 0.0
        for start in range(0, len(skills), SKILLS_PER_CALL):
            chunk = skills[start:start + SKILLS_PER_CALL]
            with tempfile.TemporaryDirectory(prefix="skilllab-fit-") as cwd:
                proc = subprocess.run(
                    [binary, "-p", "--output-format", "json", "--model", model, "--tools", "",
                     "--json-schema", json.dumps(FIT_SCHEMA), "--setting-sources", "project",
                     "--no-session-persistence"],
                    input=_fit_prompt(task, chunk, profile), capture_output=True, text=True, cwd=cwd,
                    env=_child_env(), timeout=300)
            try:
                out = json.loads(proc.stdout)
            except ValueError:
                raise RuntimeError(f"fit check failed: {(proc.stderr or proc.stdout)[-300:]}")
            if out.get("is_error"):
                raise RuntimeError(f"fit check failed: {str(out.get('result'))[:300]}")
            data = out.get("structured_output")
            if data is None:
                text = out.get("result") or ""
                data = json.loads(text[text.find("{"): text.rfind("}") + 1])
            cost += float(out.get("total_cost_usd") or 0)
            names = {s.name for s in chunk}
            for f in data.get("fits", []):
                name = str(f.get("skill", "")).strip("` ")
                if name in names:
                    fits[name] = str(f.get("reason", ""))[:200]
        return fits, cost

    return judge


def triage(skills: List[Skill], tasks: List[Task], known: Dict[str, dict], judge: FitJudge,
           profile: str = "", log: Callable[[str], None] = print) -> Tuple[Dict[str, dict], float]:
    """{pair_key: {relevant, reason, by, task_sha}} for every skill x task. Decisions for a task
    whose text (and project profile) hasn't changed are kept, including your edits; changed
    tasks are judged again."""
    decisions: Dict[str, dict] = {}
    cost = 0.0
    for t in tasks:
        sha = _sha(t.prompt + "\n" + profile)
        mine = {pair_key(s.id, t.id): known.get(pair_key(s.id, t.id)) for s in skills}
        if all(d and d.get("task_sha") == sha for d in mine.values()):
            decisions.update(mine)
            continue
        log(f"Checking which of {len(skills)} skills fit '{t.title}'…")
        fits, spent = judge(t, skills, profile)
        cost += spent
        for s in skills:
            fit = s.name in fits
            decisions[pair_key(s.id, t.id)] = {
                "relevant": fit, "reason": fits.get(s.name, "not a fit"), "by": "judge", "task_sha": sha}
    return decisions, cost


def _session_hooks(pack: Pack) -> List[str]:
    """Hook events in a pack that add context to every session or prompt."""
    events = set()
    for path in list(pack.root.rglob("hooks.json")) + list(pack.root.rglob("settings.json")):
        if any(part in ("node_modules", ".git", "tests", "test") for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        events.update(e for e in ("SessionStart", "UserPromptSubmit") if f'"{e}"' in text)
    return sorted(events)


def summarize_fit(skills: List[Skill], tasks: List[Task], decisions: Dict[str, dict],
                  sessions_per_day: Optional[float] = None,
                  price_per_mtok: Optional[float] = None, profile: Optional[dict] = None) -> dict:
    per_task = []
    for t in tasks:
        fits = [{"skill": s.id, "name": s.name, "reason": decisions[pair_key(s.id, t.id)]["reason"],
                 "user_invoked": s.user_invoked}
                for s in skills if decisions.get(pair_key(s.id, t.id), {}).get("relevant")]
        per_task.append({"id": t.id, "title": t.title, "check": t.check, "fits": fits})
    fitting = {f["skill"] for pt in per_task for f in pt["fits"]}
    rows = []
    for s in skills:
        used_by = [pt["id"] for pt in per_task if any(f["skill"] == s.id for f in pt["fits"])]
        status = "fits" if used_by else ("user-only, unused" if s.user_invoked else "not needed")
        rows.append({"id": s.id, "name": s.name, "status": status, "tasks": used_by,
                     "upfront_tokens": s.upfront_tokens, "onuse_tokens": s.onuse_tokens,
                     "user_invoked": s.user_invoked})
    unneeded = [r for r in rows if r["status"] == "not needed"]
    waste = sum(r["upfront_tokens"] for r in unneeded)
    loaded = sum(s.upfront_tokens for s in skills)
    out = {
        "tasks": per_task, "skills": rows,
        "counts": {"skills": len(skills), "fit": len(fitting), "not_needed": len(unneeded),
                   "user_only_unused": sum(1 for r in rows if r["status"] == "user-only, unused")},
        "tokens": {"loaded_per_session": loaded, "unneeded_per_session": waste},
        "hooks": [{"pack": p.id, "events": ev} for p in packs(skills) for ev in [_session_hooks(p)] if ev],
        "project": profile,
    }
    if sessions_per_day:
        out["tokens"]["unneeded_per_month"] = round(waste * sessions_per_day * 30)
        if price_per_mtok:
            out["tokens"]["unneeded_usd_per_month"] = round(waste * sessions_per_day * 30 * price_per_mtok / 1e6, 2)
    return out


def to_markdown(fit: dict, model: str) -> str:
    c, tok = fit["counts"], fit["tokens"]
    out = ["# skilllab fit", "",
           f"{c['skills']} skills checked against {len(fit['tasks'])} tasks with `{model}`: "
           f"**{c['fit']} fit at least one task**, **{c['not_needed']} fit none** "
           f"({c['user_only_unused']} more are user-only and unused, which cost nothing up front).", ""]
    if fit.get("project"):
        out += ["## Project (read from its files, used in every fit decision)", "",
                profile_text(fit["project"]), ""]
    out += ["## Tokens", "",
           f"- Skill descriptions loaded into every session: ≈{tok['loaded_per_session']} tokens.",
           f"- Of that, skills that fit none of your tasks: **≈{tok['unneeded_per_session']} tokens per session**."]
    if "unneeded_per_month" in tok:
        out.append(f"- At your session count: ≈{tok['unneeded_per_month']:,} tokens a month"
                   + (f", about **${tok['unneeded_usd_per_month']:.2f} a month**." if "unneeded_usd_per_month" in tok else "."))
    for h in fit["hooks"]:
        out.append(f"- `{h['pack']}` runs {', '.join(h['events'])} hooks that add context to every "
                   "session or prompt; its size shows only in a measured run (`--measure --pack`).")
    out += ["", "Estimates are characters ÷ 4. A skill's body loads only when it is used.", "",
            "## By task", ""]
    for t in fit["tasks"]:
        check = f" · check: `{t['check']}`" if t["check"] else " · no check (can't measure pass rate)"
        out += [f"### {t['title']}", f"`{t['id']}`{check}", ""]
        out += [f"- `{f['name']}`{' (start with /' + f['name'] + ')' if f['user_invoked'] else ''}: {f['reason']}"
                for f in t["fits"]] or ["- No skill fits."]
        out.append("")
    unneeded = [r for r in fit["skills"] if r["status"] == "not needed"]
    out += ["## Fit none of your tasks", "",
            "Candidates to remove *for this work*. A skill can still help with work not on this list.", ""]
    out += [f"- `{r['id']}` (≈{r['upfront_tokens']} tokens every session)"
            for r in sorted(unneeded, key=lambda r: -r["upfront_tokens"])] or ["- None."]
    out += ["", "## What this does and doesn't tell you", "",
            "- **Fits** means the skill's description matches the task, judged by a model. It does "
            "not mean the skill helps. To find out, add a check per task and run `skilllab fit ... --measure`.",
            "- The judgments and reasons are in `matches.json`. Edit `relevant` to overrule one; "
            "edits are kept until that task's text changes.",
            "- Only as good as your task list: list the kinds of work you really do.", ""]
    return "\n".join(out)


def precheck(task: Task, timeout: int = 300) -> Tuple[bool, str]:
    """Does the task's check already pass on the untouched project? Then it can't show lift."""
    ws = Path(tempfile.mkdtemp(prefix="skilllab-precheck-"))
    try:
        shutil.copytree(task.fixture, ws, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*task.ignore))
        if task.hidden:
            shutil.copytree(task.hidden, ws, dirs_exist_ok=True)
        cmd = task.check.replace("{python}", sys.executable)
        try:
            proc = subprocess.run(cmd, shell=True, cwd=str(ws), capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return False, "check timed out"
        return proc.returncode == 0, (proc.stdout + proc.stderr).strip()[-300:]
    finally:
        shutil.rmtree(ws, ignore_errors=True)
