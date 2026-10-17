"""Plan and execute runs: every task once without skills (baseline), and once per relevant
skill (or per whole pack)."""

from __future__ import annotations

import hashlib
import io
import json
import os
import random
import tarfile
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections import defaultdict
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from .addons import Addon
from .skills import Pack, Skill
from .tasks import Task, matches

CHECK_TIMEOUT = 300
GIT_TIMEOUT = 600
_repo_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)


def repo_cache() -> Path:
    return Path(os.environ.get("SKILLLAB_REPO_CACHE") or Path.home() / ".cache" / "skilllab" / "repos")


def repo_gitdir(url: str) -> Path:
    """Where the bare clone of `url` is cached: ~/.cache/skilllab/repos/<owner>-<name>.git"""
    path = url.rstrip("/")
    path = path[:-4] if path.endswith(".git") else path
    parts = path.split("/")
    return repo_cache() / f"{parts[-2]}-{parts[-1]}.git"


def _git(gitdir: Path, *args, check=True):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    return subprocess.run(["git", "--git-dir", str(gitdir), *args], capture_output=True, timeout=GIT_TIMEOUT,
                          check=check, env=env)


def ensure_commits(url: str, *shas: str) -> Path:
    """Clone `url` into the cache once (bare), fetching again only if a pinned commit is missing."""
    gitdir = repo_gitdir(url)
    with _repo_locks[str(gitdir)]:
        if not gitdir.exists():
            gitdir.parent.mkdir(parents=True, exist_ok=True)
            tmp = gitdir.with_name(gitdir.name + f".tmp{os.getpid()}")
            subprocess.run(["git", "clone", "--quiet", "--bare", url, str(tmp)], check=True, capture_output=True,
                           timeout=GIT_TIMEOUT, env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))
            os.replace(tmp, gitdir)
        missing = [s for s in shas if _git(gitdir, "cat-file", "-e", f"{s}^{{commit}}", check=False).returncode]
        if missing:
            _git(gitdir, "fetch", "--quiet", "origin", "+refs/heads/*:refs/heads/*", "+refs/tags/*:refs/tags/*")
            still = [s for s in missing if _git(gitdir, "cat-file", "-e", f"{s}^{{commit}}", check=False).returncode]
            if still:
                raise RuntimeError(f"{url}: commit {still[0]} not found")
    return gitdir


def materialize(url: str, sha: str, dest: Path) -> None:
    """Write the files of `url` at commit `sha` into dest (no history: later commits stay out)."""
    gitdir = ensure_commits(url, sha)
    data = _git(gitdir, "archive", "--format=tar", sha).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        for member in tar.getmembers():
            if member.name.startswith("/") or ".." in Path(member.name).parts:
                raise RuntimeError(f"unsafe path in {url}@{sha}: {member.name}")
        try:
            tar.extractall(dest, filter="data")  # Python 3.12+, and recent 3.9-3.11 patch releases
        except TypeError:
            tar.extractall(dest)


def task_env(task: Task, ws: Path) -> Dict[str, str]:
    return {k: v.replace("{workspace}", str(ws)) for k, v in task.env.items()}
# This many infrastructure errors in a row (usage limit, logged out, CLI missing) stops the batch.
MAX_CONSECUTIVE_ERRORS = 8


@dataclass
class Run:
    task: Task
    skill: Optional[Skill]  # None = baseline (or a pack run)
    repeat: int
    pack: Optional[Pack] = None
    addon: Optional[Addon] = None
    warmup: bool = False  # run first and discarded: fills the prompt cache for this arm

    @property
    def arm(self) -> str:
        if self.warmup:
            return "warmup"
        return ("addon" if self.addon else "pack" if self.pack else
                "skill" if self.skill else "baseline")

    @property
    def subject(self) -> Optional[str]:
        who = self.addon or self.pack or self.skill
        return who.id if who else None

    def key(self, model: str) -> str:
        return f"{model}|{self.arm}|{self.subject or '-'}|{self.task.id}|{self.repeat}"

    @property
    def is_baseline(self) -> bool:
        return not (self.skill or self.pack or self.addon)


def plan(skills: List[Skill], tasks: List[Task], repeats: int, all_tasks: bool = False,
         relevant: Optional[set] = None,
         pack_list: Optional[List[Pack]] = None) -> Tuple[List[Run], List[Skill]]:
    """Return the runs to do and the skills that no task tests (untested claims).

    relevant: the (skill id, task id) pairs to run, from the relevance check. Without it,
    keyword matches are used. pack_list: test these whole packs on every task instead of
    single skills. Baselines are shared: each task runs `repeats` times without skills,
    however many skills it is compared against.
    """
    if pack_list:
        runs = [Run(t, None, r) for t in tasks for r in range(repeats)]
        runs += [Run(t, None, r, pack=p) for p in pack_list for t in tasks for r in range(repeats)]
        return runs, []
    if all_tasks:
        pairs = [(s, t) for s in skills for t in tasks]
    elif relevant is not None:
        pairs = [(s, t) for s in skills for t in tasks if (s.id, t.id) in relevant]
    else:
        pairs = [(s, t) for s in skills for t in tasks if matches(s, t)]
    used_tasks = [t for t in tasks if any(t is pt for _, pt in pairs)]
    runs = [Run(t, None, r) for t in used_tasks for r in range(repeats)]
    runs += [Run(t, s, r) for s, t in pairs for r in range(repeats)]
    tested = {s.id for s, _ in pairs}
    return runs, [s for s in skills if s.id not in tested]


def plan_addons(addons: List[Addon], tasks: List[Task], repeats: int, warmup: bool = True) -> List[Run]:
    """Every add-on on every task, against one shared baseline per task.

    Cost depends on the prompt cache: the first run of an arm pays to write it, later runs
    read it at a fraction of the price. If every baseline ran first, later arms would look
    cheaper for nothing. So each arm gets one discarded warm-up run per task, and the
    measured runs are interleaved: repeat by repeat, every arm once, in a shuffled order
    (fixed seed, so a resumed batch plans the same way).
    """
    arms: List[Optional[Addon]] = [None] + list(addons)
    runs = [Run(t, None, 0, addon=a, warmup=True) for t in tasks for a in arms] if warmup else []
    for r in range(repeats):
        for t in tasks:
            block = list(arms)
            random.Random(f"{t.id}|{r}").shuffle(block)
            runs += [Run(t, None, r, addon=a) for a in block]
    return runs


def _install(skill: Skill, ws: Path) -> None:
    dest = ws / ".claude" / "skills" / skill.path.name
    shutil.copytree(skill.path, dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git"))


def _run_setup(task: Task, ws: Path) -> None:
    """Run the task's _setup.py in the workspace (e.g. to build a git history), then
    remove the setup files so the agent never sees them."""
    shutil.copytree(task.setup, ws, dirs_exist_ok=True)
    proc = subprocess.run([sys.executable, "_setup.py"], cwd=str(ws), capture_output=True,
                          text=True, timeout=CHECK_TIMEOUT)
    for item in task.setup.iterdir():
        target = ws / item.name
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
        elif target.exists():
            target.unlink()
    if proc.returncode != 0:
        raise RuntimeError(f"setup failed for {task.id}: {(proc.stderr or proc.stdout)[-300:]}")


def _hash(path: Path) -> Optional[str]:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def execute(run: Run, agent, model: str, keep: bool = False) -> dict:
    """One attempt in a fresh temp workspace. Returns the result record."""
    task = run.task
    ws = Path(tempfile.mkdtemp(prefix="skilllab-"))
    try:
        if task.repo:
            materialize(task.repo["url"], task.repo["commit"], ws)
        if task.base:
            shutil.copytree(task.base, ws, dirs_exist_ok=True)
        if task.fixture:
            shutil.copytree(task.fixture, ws, dirs_exist_ok=True)
        if task.setup:
            _run_setup(task, ws)
        prompt, extra = task.prompt, {}
        if run.skill:
            _install(run.skill, ws)
            if run.skill.user_invoked:
                # Only a person can start it, so start it the way a person would.
                prompt = f"/{run.skill.name} {task.prompt}"
        elif run.pack:
            if run.pack.plugin:
                extra["plugin_dirs"] = [run.pack.root]
            else:
                for s in run.pack.skills:
                    _install(s, ws)
        elif run.addon:
            extra = run.addon.install(ws)
        tools = list(task.tools) + (list(run.addon.tools) if run.addon else [])
        if task.env:
            extra["env"] = {**task_env(task, ws), **(extra.get("env") or {})}
        before = {p: _hash(ws / p) for p in task.protect}

        res = agent.run(prompt, ws, task.timeout, tools=tools, **extra)

        changed = [p for p, h in before.items() if _hash(ws / p) != h]
        passed, check_tail = False, ""
        if not res.infra_error:
            if task.hidden:
                # Hidden checks arrive after the agent is done, overwriting anything it wrote.
                shutil.copytree(task.hidden, ws, dirs_exist_ok=True)
            cmd = task.check.replace("{python}", shlex.quote(sys.executable))
            try:
                check_env = dict(os.environ, **task_env(task, ws))
                if task.repo:
                    check_env["SKILLLAB_REPO_GIT"] = str(repo_gitdir(task.repo["url"]))
                proc = subprocess.run(cmd, shell=True, cwd=str(ws), capture_output=True,
                                      text=True, timeout=CHECK_TIMEOUT, env=check_env)
                passed = proc.returncode == 0 and not changed
                check_tail = (proc.stdout + proc.stderr).strip()[-600:]
            except subprocess.TimeoutExpired:
                check_tail = f"check timed out after {CHECK_TIMEOUT}s"
        if run.addon:
            triggered = True  # always on: there is nothing to trigger
        elif run.pack:
            triggered = any(run.pack.owns(s) for s in res.skills_invoked)
        elif run.skill and run.skill.user_invoked:
            triggered = True  # started by the "person" in the prompt
        else:
            name = run.skill.name if run.skill else None
            triggered = bool(name and any(
                name == s or s.endswith(":" + name) or s.endswith("/" + name) for s in res.skills_invoked))
        return {
            "key": run.key(model),
            "model": model,
            "arm": run.arm,
            "skill": run.subject,
            "user_invoked": bool(run.skill and run.skill.user_invoked),
            "task": task.id,
            "repeat": run.repeat,
            "passed": passed,
            "infra_error": res.infra_error,
            "note": res.note,
            "protected_changed": changed,
            "skill_triggered": triggered,
            "skills_invoked": res.skills_invoked,
            "tool_calls": res.tool_calls,
            "bash_commands": res.bash_commands,
            "cost_usd": res.cost_usd,
            "input_tokens": res.input_tokens,
            "output_tokens": res.output_tokens,
            "turns": res.turns,
            "duration_s": round(res.duration, 1),
            "check_tail": check_tail,
            "workspace": str(ws) if keep else None,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
    finally:
        if not keep:
            shutil.rmtree(ws, ignore_errors=True)


def load_results(path: Path) -> List[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def final_results(records: List[dict]) -> List[dict]:
    """One record per run key. A retried run keeps its success over earlier
    infrastructure errors; otherwise the latest record wins."""
    by_key: Dict[str, dict] = {}
    for r in records:
        old = by_key.get(r["key"])
        if old is None or old.get("infra_error") or not r.get("infra_error"):
            by_key[r["key"]] = r
    return list(by_key.values())


def run_all(runs: List[Run], agent, model: str, results_path: Path, workers: int = 4,
            budget_usd: Optional[float] = None, keep: bool = False,
            log: Callable[[str], None] = print) -> Dict[str, float]:
    """Run in parallel, appending to results_path. Finished runs are skipped on resume.

    Stops starting new runs once recorded cost reaches budget_usd.
    """
    done = {r["key"] for r in load_results(results_path) if not r.get("infra_error")}
    spent = sum(r.get("cost_usd") or 0 for r in load_results(results_path))
    todo = [r for r in runs if r.key(model) not in done]
    log(f"{len(runs) - len(todo)} runs already done, {len(todo)} to go"
        + (f", ${spent:.2f} of ${budget_usd:.2f} budget used" if budget_usd else ""))
    lock = threading.Lock()
    stats = {"ran": 0, "spent": spent, "stopped_for_budget": 0, "stopped_for_errors": 0}
    streak = [0]
    queue = list(todo)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        pending = set()

        def fill():
            while queue and len(pending) < workers:
                if budget_usd is not None and stats["spent"] >= budget_usd:
                    stats["stopped_for_budget"] = len(queue)
                    queue.clear()
                    return
                run = queue.pop(0)
                fut = pool.submit(execute, run, agent, model, keep)
                fut.run_ref = run
                pending.add(fut)

        fill()
        while pending:
            finished, _ = wait(pending, return_when=FIRST_COMPLETED)
            for fut in finished:
                pending.discard(fut)
                try:
                    rec = fut.result()
                except Exception as exc:  # a bug in one run should not kill the batch
                    run = fut.run_ref
                    rec = {"key": run.key(model), "model": model, "arm": run.arm,
                           "skill": run.subject, "task": run.task.id,
                           "repeat": run.repeat, "passed": False,
                           "infra_error": f"runner error: {exc}", "cost_usd": None}
                with lock:
                    with results_path.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(rec) + "\n")
                    stats["ran"] += 1
                    stats["spent"] += rec.get("cost_usd") or 0
                    streak[0] = streak[0] + 1 if rec.get("infra_error") else 0
                    if streak[0] >= MAX_CONSECUTIVE_ERRORS and queue:
                        stats["stopped_for_errors"] = len(queue)
                        queue.clear()
                status = "ERROR " + rec["infra_error"] if rec.get("infra_error") else (
                    "pass" if rec["passed"] else "fail")
                who = rec["skill"] or "baseline"
                log(f"[{stats['ran']}/{len(todo)}] {rec['task']} · {who} · #{rec['repeat']}: {status}")
            fill()
    if stats["stopped_for_errors"]:
        log(f"stopped: {MAX_CONSECUTIVE_ERRORS} runs in a row failed before the agent did any work "
            f"(last error: {rec.get('infra_error', '')[:200]}). Often a usage limit or logged-out CLI. "
            f"{stats['stopped_for_errors']} runs not started; rerun the same command later to resume.")
    if stats["stopped_for_budget"]:
        log(f"budget reached: {stats['stopped_for_budget']} runs not started. "
            "--budget is the total for this results folder, including earlier runs. Raise it and rerun the same command to continue.")
    return stats
