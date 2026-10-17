"""Generate the `real` tier: tasks from real bug fixes in real open-source projects.

For each fix commit: the workspace is the project at the commit before the fix; the agent gets a
bug report written the way a user would file it; the hidden check is the test that came with the
upstream fix, plus the project's whole test suite. Nothing from upstream is copied into skilllab:
code and tests are read from the cached clone at run time.

Run from the repo root (needs network the first time, to clone into ~/.cache/skilllab/repos):

    python3 tests/generators/real_tasks.py
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
from skilllab.runner import ensure_commits, materialize  # noqa: E402

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
]


def git(gitdir, *args):
    return subprocess.run(["git", "--git-dir", str(gitdir), *args], capture_output=True, text=True, check=True).stdout


def requires_python(gitdir, rev):
    try:
        text = git(gitdir, "show", f"{rev}:pyproject.toml")
    except subprocess.CalledProcessError:
        return None
    m = re.search(r'requires-python\s*=\s*">=\s*(3\.\d+)', text)
    return m.group(1) if m else None


def failing_tests(project, parent, fix, test_files, pythonpath):
    """Test ids that fail at the parent once the fix's test files are in place."""
    ws = Path(tempfile.mkdtemp())
    materialize(project["url"], parent, ws)
    gitdir = ensure_commits(project["url"], fix)
    for f in test_files:
        (ws / f).write_text(git(gitdir, "show", f"{fix}:{f}"))
    report = ws / "junit.xml"
    env = dict(__import__("os").environ, PYTHONPATH=pythonpath.replace("{workspace}", str(ws)))
    subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-W", "ignore::DeprecationWarning",
                    f"--junitxml={report}", *test_files], cwd=ws, capture_output=True, env=env, timeout=900)
    ids = []
    for case in ET.parse(report).getroot().iter("testcase"):
        if any(c.tag in ("failure", "error") for c in case):
            parts = case.get("classname").split(".")
            # classname is path parts + optional class; the file is the longest existing prefix
            for i in range(len(parts), 0, -1):
                if (ws / ("/".join(parts[:i]) + ".py")).exists():
                    test_id = "::".join(["/".join(parts[:i]) + ".py", *parts[i:], case.get("name").split("[")[0]])
                    break
            if test_id not in ids:
                ids.append(test_id)
    shutil.rmtree(ws)
    return ids


def main():
    for task_id, proj_name, short, tags, report in TASKS:
        project = PROJECTS[proj_name]
        gitdir = ensure_commits(project["url"], short)
        fix = git(gitdir, "rev-parse", f"{short}^{{commit}}").strip()
        parent = git(gitdir, "rev-parse", f"{fix}^").strip()
        changed = git(gitdir, "show", "--name-only", "--format=", fix).split()
        test_files = [f for f in changed if f.startswith(project["tests"] + "/") and f.endswith(".py")]
        src_files = [f for f in changed if f.startswith(project["src"] + "/")]
        must_pass = failing_tests(project, parent, fix, test_files, project["pythonpath"])
        assert must_pass, f"{task_id}: no test fails before the fix"
        conftests = [f for f in git(gitdir, "ls-tree", "-r", "--name-only", parent).split() if f.endswith("conftest.py")]

        hidden = SUITE / "fixtures" / f"real-{task_id}-hidden"
        hidden.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SUITE / "fixtures" / "real-check" / "check_real.py", hidden / "check_real.py")
        (hidden / "real_check.json").write_text(json.dumps({
            "project": project["url"], "fix": fix, "test_files": test_files, "conftests": conftests,
            "must_pass": must_pass, "suite": [project["tests"]]}, indent=2) + "\n")

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
        rp = requires_python(gitdir, parent)
        if rp:
            spec["requires_python"] = rp
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
        print(f"{task_id}: {len(must_pass)} failing tests before the fix, python>={rp}")


if __name__ == "__main__":
    main()
