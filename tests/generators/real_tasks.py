"""Generate the `real` tier: tasks from real bug fixes in real open-source projects.

For each fix commit: the workspace is the project at the commit before the fix; the agent gets a
bug report written the way a user would file it; the hidden check is the test that came with the
upstream fix, plus the project's whole test suite. Nothing from upstream is copied into skilllab:
code and tests are read from the cached clone at run time.

Run from the repo root (needs network the first time, to clone into ~/.cache/skilllab/repos):

    python3 tests/generators/real_tasks.py              # every task
    python3 tests/generators/real_tasks.py TASK_ID ...  # only these
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from skilllab.runner import ensure_commits, ensure_env, materialize  # noqa: E402

SUITE = ROOT / "skilllab" / "suite"
SOLUTIONS = ROOT / "tests" / "solutions"
TOOLS = ["Bash(git:*)", "Bash(grep:*)", "Bash(find:*)", "Bash(head:*)", "Bash(tail:*)", "Bash(wc:*)"]
PYTEST_ENV = "-p no:cacheprovider -W ignore::DeprecationWarning"
TEST_HOW = ("Run the tests with `python3 -m pytest tests` (the package is importable from the repo "
            "as it is). Fix the bug in the library code and add a regression test. Keep the "
            "existing tests passing.")

PROJECTS = {
    "click": {"url": "https://github.com/pallets/click.git", "src": "src/click", "tests": "tests",
              "pythonpath": "{workspace}/src", "license": "BSD-3-Clause"},
    "sqlparse": {"url": "https://github.com/andialbrecht/sqlparse.git", "src": "sqlparse", "tests": "tests",
                 "pythonpath": "{workspace}", "license": "BSD-3-Clause"},
    "boltons": {"url": "https://github.com/mahmoud/boltons.git", "src": "boltons", "tests": "tests",
                "pythonpath": "{workspace}", "license": "BSD-3-Clause"},
    "more-itertools": {"url": "https://github.com/more-itertools/more-itertools.git", "src": "more_itertools",
                       "tests": "tests", "pythonpath": "{workspace}", "license": "MIT"},
    # Needs its pinned dependencies: the environment fastapi's own CI uses (`uv sync --group tests --extra all`).
    "fastapi": {"url": "https://github.com/fastapi/fastapi.git", "src": "fastapi", "tests": "tests",
                "pythonpath": "{workspace}", "license": "MIT",
                "deps": {"python": "3.12", "groups": ["tests"], "extras": ["all"]}},
}

TASKS = [
    ("click-choice-brackets", "click", "762c97eef7", ["cli", "help", "usage", "formatting", "bug"],
     "Bug report from a user of this library:\n\n> The usage line in `--help` shows doubled brackets for "
     "optional arguments that use `click.Choice`. With\n>\n> ```python\n> @click.command()\n> "
     "@click.argument(\"method\", type=click.Choice([\"foo\", \"bar\", \"baz\"]), required=False)\n> "
     "def cli(method): ...\n> ```\n>\n> `--help` prints `Usage: cli [OPTIONS] [[foo|bar|baz]]`. The same "
     "happens with `nargs=-1`, and with other types whose metavar is already in brackets. "
     "Expected: `[foo|bar|baz]`.\n\n"),
    ("click-default-map-nargs", "click", "3a3e0350b6", ["config", "defaults", "options", "bug"],
     "Bug report (issue #2745) from a user of this library:\n\n> We load `default_map` from a config "
     "file, so every value is a string. For an option with `nargs=2` (or a tuple type), "
     "`default_map={\"point\": \"3 4\"}` doesn't work: the command fails or gets the whole string, "
     "instead of `(3, 4)`. Setting the same value through the option's environment variable works, "
     "because click splits it. A string in `default_map` should be split the same way. Values that "
     "are already a list or tuple, and values given on the command line, must keep working.\n\n"),
    ("click-help-hint", "click", "1241abaed4", ["cli", "errors", "help", "usage", "bug"],
     "Bug report (issue #2790) from a user of this library:\n\n> Our group uses "
     "`context_settings={\"help_option_names\": [\"-h\", \"--help\"]}`, and a subcommand has its own "
     "`--host/-h` option. When you make a usage mistake in that subcommand, the error ends with "
     "`Try 'cli foo -h' for help.`, but `-h` there means `--host`, so the hint is wrong. The hint "
     "should only suggest help option names the command actually still accepts (preferring the "
     "longest, like `--help`), and show no hint if none are left.\n\n"),
    ("click-parameter-source", "click", "7d05a59b9d", ["parameters", "callbacks", "types", "regression", "bug"],
     "Bug report (issue #3458) from a user of this library, a regression in the latest release:\n\n"
     "> Inside a custom `ParamType.convert()`, `ctx.get_parameter_source(param.name)` now returns "
     "`None`. It used to return the source (`DEFAULT`, `COMMANDLINE`, ...). The same goes for eager "
     "option callbacks. Minimal example:\n>\n> ```python\n> class Source(click.ParamType):\n>     "
     "name = \"source\"\n>     def convert(self, value, param, ctx):\n>         return (value, "
     "ctx.get_parameter_source(param.name))\n>\n> @click.command()\n> @click.option(\"--default\", "
     "type=Source(), default=\"/tmp/file\")\n> def cli(default):\n>     click.echo(default)\n> ```\n>\n> "
     "prints `('/tmp/file', None)` instead of `('/tmp/file', <ParameterSource.DEFAULT: 3>)`. When "
     "several options share one parameter name, the source reported afterwards must still be the "
     "one of the option that won.\n\n"),
    ("sqlparse-begin-end", "sqlparse", "1a3bfbd50b", ["sql", "parser", "parsing", "split", "bug"],
     "Bug report (issue #809) from a user of this library:\n\n> `sqlparse.split()` breaks a single "
     "statement apart when it contains a `BEGIN ... END` block with semicolons inside, for example a "
     "`WITH FUNCTION ... BEGIN DECLARE ...; RETURN ...; END SELECT ...` query or a `CREATE PROCEDURE` "
     "body. The semicolons inside the block are part of the statement; splitting should only happen "
     "after the whole statement.\n\n"),
    ("sqlparse-strip-whitespace", "sqlparse", "0c4902f3f7", ["sql", "formatting", "format", "whitespace", "bug"],
     "Bug report (issue #782) from a user of this library:\n\n> `sqlparse.format(sql, "
     "strip_whitespace=True)` leaves trailing whitespace and line breaks in place when they are "
     "inside a group, such as a parenthesis or a sub-select, while the same whitespace at the top "
     "level is removed. All of it should be stripped.\n\n"),
    ("sqlparse-real-name", "sqlparse", "f66d12c245", ["sql", "parser", "parsing", "identifiers", "bug"],
     "Bug report (issue #332) from a user of this library:\n\n> For identifiers with more than two "
     "dotted parts, `get_real_name()` returns the wrong part:\n>\n> ```python\n> "
     "sqlparse.parse(\"db.schema.tbl.col\")[0].tokens[0].get_real_name()  # 'schema', expected 'col'\n"
     "> ```\n>\n> Two-part names like `tbl.col` are fine. `get_parent_name()` should keep behaving as "
     "documented.\n\n"),
    ("boltons-relative-time", "boltons", "8789df2cc3", ["datetime", "time", "timezone", "bug"],
     "Bug report (issue #469) from a user of this library:\n\n> "
     "`boltons.timeutils.relative_time(d)` and `decimal_relative_time(d)` fail for timezone-aware "
     "datetimes when you don't pass `other`: `relative_time(datetime.now(timezone.utc))` raises "
     "instead of returning `'0 seconds ago'`. Naive datetimes work. The default comparison time "
     "should match the timezone (or lack of one) of the datetime passed in.\n\n"),
    ("boltons-barrellist-slices", "boltons", "448b1db11a", ["data structures", "lists", "slicing", "bug"],
     "Bug report from a user of this library:\n\n> `boltons.listutils.BarrelList` doesn't slice like "
     "a list. Negative bounds, bounds past the end and negative steps give results that differ from "
     "the same slice on a plain `list` (for example `bl[::-1]` or `bl[-20:2]`). Every slice should "
     "give exactly what `list(bl)[slice]` gives, including `ValueError` for a step of 0.\n\n"),
    ("boltons-qsl-encoding", "boltons", "d45cc414e3", ["urls", "url", "encoding", "unicode", "bug"],
     "Bug report (issue #455) from a user of this library:\n\n> "
     "`boltons.urlutils.parse_qsl(qs, encoding='latin-1')` ignores the encoding: `parse_qsl('k=%E9', "
     "encoding='latin-1')` should give `[('k', 'é')]`, but the value is decoded as UTF-8. Keys have "
     "the same problem. The default behaviour (UTF-8) shouldn't change.\n\n"),
    ("more-itertools-bucket", "more-itertools", "2b8d5cddce", ["iterators", "iteration", "data structures", "bug"],
     "Bug report (issue #1284) from a user of this library:\n\n> Looking up a key that doesn't exist "
     "in a `more_itertools.bucket` adds it. After `'c' in s` (or `s['c']`) for a key with no items, "
     "`list(s)` suddenly lists `'c'`, so `'c' in s` and `'c' in list(s)` disagree. A lookup must not "
     "create keys; `list(s)` should only list keys that actually had items.\n\n"),
    ("more-itertools-one-falsy", "more-itertools", "def2dabea8", ["iterators", "errors", "exceptions", "bug"],
     "Bug report from a user of this library:\n\n> `more_itertools.one(it, too_long=MyError())` raises "
     "a plain `ValueError` instead of `MyError` when `MyError` instances are falsy (it defines "
     "`__bool__`). `only()` has the same problem, and so does `too_short`. A custom exception that "
     "was passed in must always be the one raised.\n\n"),
    ("fastapi-stream-nan", "fastapi", "d1fd422fd9", ["web", "api", "json", "streaming", "serialization", "bug"],
     "Bug report from a user of this library:\n\n> Streaming endpoints write invalid JSON for non-finite "
     "floats. A JSONL endpoint (an async generator path operation with no return annotation) or a "
     "Server-Sent Events endpoint (`response_class=EventSourceResponse`, or yielding "
     "`ServerSentEvent(data=...)`) that yields `float('nan')`, `float('inf')` or `float('-inf')`, alone, "
     "nested in dicts and lists, or inside a Pydantic model, sends bare `NaN` / `Infinity` tokens, which "
     "clients' JSON parsers reject. Each item should be serialized the way Pydantic serializes JSON by "
     "default (`pydantic_core.to_json`): non-finite floats become `null`, everything else unchanged. A model "
     "that sets its own `ser_json_inf_nan` must keep that setting, and `ServerSentEvent(raw_data=...)` must "
     "still be sent exactly as given.\n\n"),
    ("fastapi-router-wrapping", "fastapi", "ac88f563db", ["web", "api", "routing", "performance", "bug"],
     "Bug report from a user of this library:\n\n> With an older Sentry SDK, which wraps the endpoint "
     "each time FastAPI builds a route's request handler, our app eventually crashes with `RecursionError`. "
     "For routes added with `include_router()`, FastAPI seems to build a new request handler on every "
     "request, so the wrappers pile up: the Nth request runs the endpoint through N wrappers. A route's "
     "request handler (from `get_route_handler()`) should be built once and reused across requests, also "
     "for routes in included routers, separately for each place a router is included (different prefixes "
     "or `default_response_class`). Dependency overrides and routes added to a router later must still "
     "take effect.\n\n"),
    ("fastapi-computed-openapi", "fastapi", "a1a05b75d3", ["web", "api", "openapi", "schema", "pydantic", "bug"],
     "Bug report (discussion #14489) from a user of this library:\n\n> With "
     "`FastAPI(separate_input_output_schemas=False)`, a model with a `@computed_field` that is used for "
     "both the request body and the response gets separate `-Input` and `-Output` schemas, which is right. "
     "But when that model is only *nested* in the response model (as a field, in a list, or recursively), "
     "the OpenAPI schema is wrong: the response refers to the `-Input` schema, which lacks the computed "
     "field, instead of the `-Output` one. Any model with a computed field anywhere in its nested models "
     "should get separate input and output schemas, and responses should reference the `-Output` ones (with "
     "the computed field marked `readOnly`).\n\n"),
]

# Tests from the upstream fix that check something the bug report doesn't ask for. A check only
# enforces what the task states, so these are left out of must_pass and deselected from the suite.
UNSTATED = {
    # Checks a private context variable by name (`routing._effective_route_context_var`).
    "fastapi-router-wrapping": ["tests/test_route_handler_wrapping.py::test_failed_handler_construction_restores_context_and_can_retry"],
    # The fix also stops building the default message (which reprs items) when a custom
    # exception is given; the report is only about falsy exceptions.
    "more-itertools-one-falsy": ["tests/test_more.py::OneTests::test_too_long_does_not_evaluate_repr",
                                 "tests/test_more.py::OnlyTests::test_too_long_does_not_evaluate_repr"],
}


def git(gitdir, *args):
    return subprocess.run(["git", "--git-dir", str(gitdir), *args], capture_output=True, text=True, check=True).stdout


def requires_python(gitdir, rev):
    try:
        text = git(gitdir, "show", f"{rev}:pyproject.toml")
    except subprocess.CalledProcessError:
        return None
    m = re.search(r'requires-python\s*=\s*">=\s*(3\.\d+)', text)
    return m.group(1) if m else None


def failing_tests(project, rev, targets, python, from_fix=None):
    """Test ids that fail at `rev`, running `targets`. from_fix: (fix, files) to write over the
    workspace from the fix commit first (the fix's tests at the parent, to see which fail)."""
    ws = Path(tempfile.mkdtemp())
    materialize(project["url"], rev, ws)
    if from_fix:
        fix, files = from_fix
        gitdir = ensure_commits(project["url"], fix)
        for f in files:
            (ws / f).write_text(git(gitdir, "show", f"{fix}:{f}"))
    report = ws / "junit.xml"
    env = dict(__import__("os").environ, PYTHONPATH=project["pythonpath"].replace("{workspace}", str(ws)))
    subprocess.run([str(python), "-m", "pytest", "-q", "-p", "no:cacheprovider", "-W", "ignore::DeprecationWarning",
                    f"--junitxml={report}", *targets], cwd=ws, capture_output=True, env=env, timeout=900)
    ids = []
    for case in ET.parse(report).getroot().iter("testcase"):
        if any(c.tag in ("failure", "error") for c in case):
            parts = case.get("classname").split(".")
            # classname is path parts + optional class; the file is the longest existing prefix
            for i in range(len(parts), 0, -1):
                if (ws / ("/".join(parts[:i]) + ".py")).exists():
                    test_id = "::".join(["/".join(parts[:i]) + ".py", *parts[i:], case.get("name").split("[")[0]])
                    break
            else:
                # A whole module that fails to import has no test name to require.
                raise RuntimeError(f"{case.get('name')} failed to collect at {rev[:10]}; "
                                   "its tests can't be listed one by one")
            if test_id not in ids:
                ids.append(test_id)
    shutil.rmtree(ws)
    return ids


def main(only=()):
    for task_id, proj_name, short, tags, report in TASKS:
        if only and task_id not in only:
            continue
        project = PROJECTS[proj_name]
        gitdir = ensure_commits(project["url"], short)
        fix = git(gitdir, "rev-parse", f"{short}^{{commit}}").strip()
        parent = git(gitdir, "rev-parse", f"{fix}^").strip()
        changed = git(gitdir, "show", "--name-only", "--format=", fix).split()
        test_files = [f for f in changed if f.startswith(project["tests"] + "/") and f.endswith(".py")]
        src_files = [f for f in changed if f.startswith(project["src"] + "/")]
        deps = project.get("deps")
        python = ensure_env(project["url"], parent, deps) if deps else sys.executable
        must_pass = failing_tests(project, parent, test_files, python, from_fix=(fix, test_files))
        # Tests that fail even at the fix commit are broken in this environment (network, OS,
        # timing): no agent can make them pass, so they're deselected rather than required.
        broken = failing_tests(project, fix, [project["tests"]], python)
        must_pass = [t for t in must_pass if t not in broken]
        unstated = UNSTATED.get(task_id, [])
        assert set(unstated) <= set(must_pass), f"{task_id}: UNSTATED lists a test that doesn't fail before the fix"
        must_pass = [t for t in must_pass if t not in unstated]
        assert must_pass, f"{task_id}: no test fails before the fix"
        conftests = [f for f in git(gitdir, "ls-tree", "-r", "--name-only", parent).split() if f.endswith("conftest.py")]

        hidden = SUITE / "fixtures" / f"real-{task_id}-hidden"
        hidden.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SUITE / "fixtures" / "real-check" / "check_real.py", hidden / "check_real.py")
        check = {"project": project["url"], "fix": fix, "test_files": test_files, "conftests": conftests,
                 "must_pass": must_pass, "suite": [project["tests"]]}
        if unstated or broken:
            check["pytest_args"] = [arg for t in unstated + broken for arg in ("--deselect", t)]
        (hidden / "real_check.json").write_text(json.dumps(check, indent=2) + "\n")

        spec = {
            "id": task_id, "tier": "real",
            "title": f"{proj_name}: {report.split(':', 1)[0]}"[:90],
            "tags": tags,
            "repo": {"url": project["url"], "commit": parent, "fix": fix},
            "setup": "projects/snapshot-setup",
            "hidden": f"fixtures/real-{task_id}-hidden",
            "prompt": f"This repo is {proj_name} (an open-source Python library). " + report + TEST_HOW,
            "check": "{python} check_real.py",
            "protect": conftests,
            "env": {"PYTHONPATH": project["pythonpath"], "PYTEST_ADDOPTS": PYTEST_ENV},
            "tools": TOOLS,
            "requires": ["git"],
            "timeout": 1500,
            "source": f"{project['url'].removesuffix('.git')}/commit/{fix} ({project['license']})",
        }
        rp = None if deps else requires_python(gitdir, parent)
        if rp:
            spec["requires_python"] = rp
        if deps:
            spec["deps"] = deps
            spec["requires"].append("uv")
        (SUITE / "tasks" / f"{task_id}.json").write_text(json.dumps(spec, indent=2) + "\n")

        sol = SOLUTIONS / task_id
        sol.mkdir(parents=True, exist_ok=True)
        (sol / "_solve.py").write_text(
            '"""Reference solution: the upstream fix, read from the cached clone."""\n'
            "import subprocess\nfrom pathlib import Path\n\nfrom skilllab.runner import ensure_commits\n\n"
            f"FIX = {fix!r}\ngitdir = ensure_commits({project['url']!r}, FIX)\n"
            f"for path in {src_files!r}:\n"
            "    data = subprocess.run(['git', '--git-dir', str(gitdir), 'show', f'{FIX}:{path}'],\n"
            "                          capture_output=True, check=True).stdout\n"
            "    Path(path).write_bytes(data)\n")
        print(f"{task_id}: {len(must_pass)} failing tests before the fix, {len(broken)} broken here, "
              f"python {deps['python'] if deps else '>=' + str(rp)}")


if __name__ == "__main__":
    main(sys.argv[1:])  # task ids to (re)generate; none means all
