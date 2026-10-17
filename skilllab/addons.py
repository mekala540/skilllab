"""Add-ons: anything that changes how the agent works without being a skill.

Token savers (output compressors, command rewriters, proxies), memory tools and
prompt styles install in different ways: a settings file with hooks, an environment
variable pointing at a proxy, a CLAUDE.md, an extra system prompt, a plugin. An add-on
folder describes that install once in `addon.json`, so the same task suite can run
with and without it.

addon.json (every field optional except name):

    {
      "name": "terse",
      "description": "One line: what it claims to do",
      "settings": "settings.json",        // file in this folder, or an inline object
      "plugin_dir": "plugin",             // loaded with --plugin-dir
      "skills_dir": "skills",             // each subfolder copied to .claude/skills/
      "claude_md": "CLAUDE.md",           // copied into the workspace
      "append_system_prompt": "Be brief.",
      "env": {"ANTHROPIC_BASE_URL": "http://127.0.0.1:8787"},
      "tools": ["Bash(rtk:*)"],           // extra tools the add-on's rewrites need
      "setup": ["rtk init --local"],      // run in each workspace before the agent
      "requires": ["rtk"]                 // programs that must be on PATH
    }
"""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

SETUP_TIMEOUT = 300


@dataclass
class Addon:
    name: str
    root: Path
    description: str = ""
    settings: Optional[Union[str, dict]] = None
    plugin_dir: Optional[str] = None
    skills_dir: Optional[str] = None
    claude_md: Optional[str] = None
    append_system_prompt: str = ""
    env: Dict[str, str] = field(default_factory=dict)
    tools: List[str] = field(default_factory=list)
    setup: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return f"addon:{self.name}"

    def missing(self) -> List[str]:
        return [r for r in self.requires if not shutil.which(r)]

    def settings_arg(self) -> Optional[str]:
        """The value for --settings: a file path, or inline JSON (the CLI accepts both)."""
        if self.settings is None:
            return None
        if isinstance(self.settings, dict):
            return json.dumps(self.settings)
        return str(self.root / self.settings)

    def context_chars(self) -> int:
        """Text the add-on itself puts in every session (CLAUDE.md, extra system prompt)."""
        n = len(self.append_system_prompt)
        if self.claude_md and (self.root / self.claude_md).is_file():
            n += len((self.root / self.claude_md).read_text(encoding="utf-8", errors="replace"))
        return n

    control: bool = False  # the built-in no-op arm that checks the method itself

    def meta(self) -> dict:
        how = [k for k in ("settings", "plugin_dir", "skills_dir", "claude_md", "env", "setup")
               if getattr(self, k)]
        if self.append_system_prompt:
            how.append("system prompt")
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description or f"Add-on ({', '.join(how) or 'no changes'})",
            "source": "addon",
            "upfront_tokens": self.context_chars() // 4,
            "onuse_tokens": 0,
            "user_invoked": False,
            "addon": True,
            "control": self.control,
        }

    def install(self, ws: Path) -> dict:
        """Prepare a workspace. Returns extra keyword arguments for agent.run."""
        if self.claude_md:
            shutil.copy2(self.root / self.claude_md, ws / "CLAUDE.md")
        if self.skills_dir:
            for d in sorted((self.root / self.skills_dir).iterdir()):
                if (d / "SKILL.md").is_file():
                    shutil.copytree(d, ws / ".claude" / "skills" / d.name, dirs_exist_ok=True)
        for cmd in self.setup:
            proc = subprocess.run(cmd, shell=True, cwd=str(ws), capture_output=True, text=True,
                                  timeout=SETUP_TIMEOUT)
            if proc.returncode != 0:
                raise RuntimeError(f"add-on {self.name} setup failed ({shlex.quote(cmd)}): "
                                   f"{(proc.stderr or proc.stdout).strip()[-300:]}")
        extra: dict = {}
        if self.plugin_dir:
            extra["plugin_dirs"] = [self.root / self.plugin_dir]
        if self.settings is not None:
            extra["settings"] = self.settings_arg()
        if self.env:
            extra["env"] = dict(self.env)
        if self.append_system_prompt:
            extra["append_prompt"] = self.append_system_prompt
        return extra


def control_addon() -> Addon:
    """Changes nothing. It runs exactly like the baseline under its own name, so any
    'cheaper' or 'costlier' it gets is bias in the method (run order, caching, noise)."""
    return Addon(name="control", root=Path.cwd().resolve(), control=True,
                 description="Changes nothing. Checks the method: it should come out 'same cost'.")


FIELDS = ("description", "settings", "plugin_dir", "skills_dir", "claude_md",
          "append_system_prompt", "env", "tools", "setup", "requires")


def load_addon(path: Path) -> Addon:
    path = Path(path)
    spec_file = path if path.is_file() else path / "addon.json"
    if not spec_file.is_file():
        raise ValueError(f"{path}: no addon.json")
    data = json.loads(spec_file.read_text(encoding="utf-8"))
    if not data.get("name"):
        raise ValueError(f"{spec_file}: needs a name")
    unknown = set(data) - set(FIELDS) - {"name"}
    if unknown:
        raise ValueError(f"{spec_file}: unknown fields {', '.join(sorted(unknown))}")
    # Absolute: settings and plugin_dir go to an agent that runs inside the workspace.
    root = spec_file.parent.resolve()
    for key in ("plugin_dir", "skills_dir", "claude_md"):
        if data.get(key) and not (root / data[key]).exists():
            raise ValueError(f"{spec_file}: {key} {data[key]!r} not found")
    if isinstance(data.get("settings"), str) and not (root / data["settings"]).is_file():
        raise ValueError(f"{spec_file}: settings file {data['settings']!r} not found")
    return Addon(name=data["name"], root=root, **{k: data[k] for k in FIELDS if k in data})
