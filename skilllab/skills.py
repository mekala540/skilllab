"""Find skills (folders with a SKILL.md) in local folders or git repos."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|fixtures?|examples?)(/|$)", re.I)


@dataclass
class Skill:
    id: str  # "<source>/<name>", unique across a run
    name: str
    description: str
    path: Path  # the folder that holds SKILL.md
    source: str
    body_chars: int
    # disable-model-invocation: true. Only a person can start it (/name); the agent never
    # sees its description, so it costs nothing up front and has no trigger rate.
    user_invoked: bool = False
    root: Optional[Path] = None  # the repo or folder it came from

    @property
    def upfront_tokens(self) -> int:
        """Name + description: loaded into every session. Characters / 4."""
        return 0 if self.user_invoked else (len(self.name) + len(self.description)) // 4

    @property
    def onuse_tokens(self) -> int:
        return self.body_chars // 4

    def meta(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "upfront_tokens": self.upfront_tokens,
            "onuse_tokens": self.onuse_tokens,
            "user_invoked": self.user_invoked,
        }


@dataclass
class Pack:
    """A whole source installed the way its users install it: as a Claude Code plugin
    (with its hooks) when it ships .claude-plugin/plugin.json, else every skill at once."""
    source: str
    root: Path
    skills: List[Skill]

    @property
    def id(self) -> str:
        return f"pack:{self.source}"

    @property
    def plugin(self) -> bool:
        return (self.root / ".claude-plugin" / "plugin.json").is_file()

    def owns(self, invoked: str) -> bool:
        names = {s.name for s in self.skills}
        return re.split(r"[:/]", invoked)[-1] in names

    def meta(self) -> dict:
        how = "plugin, with its hooks" if self.plugin else "all skills installed"
        return {
            "id": self.id,
            "name": f"{self.source} (whole pack)",
            "description": f"Every skill in {self.source} ({len(self.skills)}), {how}.",
            "source": self.source,
            "upfront_tokens": sum(s.upfront_tokens for s in self.skills),
            "onuse_tokens": max((s.onuse_tokens for s in self.skills), default=0),
            "user_invoked": False,
            "pack": True,
        }


def packs(skills: List[Skill]) -> List[Pack]:
    by_source: Dict[str, Pack] = {}
    for s in skills:
        if s.root is not None:
            by_source.setdefault(s.source, Pack(s.source, s.root, [])).skills.append(s)
    return list(by_source.values())


def parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    """Parse simple YAML frontmatter (key: value, plus > and | blocks)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}, text
    fields: Dict[str, str] = {}
    key = None
    for line in lines[1:end]:
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m and not line.startswith((" ", "\t")):
            key, value = m.group(1), m.group(2).strip()
            if value in (">", "|", ">-", "|-", ">+", "|+"):
                value = ""
            fields[key] = _unquote(value)
        elif key and line.strip():
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields, "\n".join(lines[end + 1:])


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def find_skills(root: Path, source: str) -> List[Skill]:
    """Every SKILL.md under root. Copies of one skill count once (shortest path wins)."""
    by_name: Dict[str, Skill] = {}
    for path in sorted(root.rglob("SKILL.md"), key=lambda p: (len(p.parts), str(p))):
        rel = path.relative_to(root).as_posix()
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if TEST_PATH.search(rel):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        fields, body = parse_frontmatter(text)
        name = fields.get("name") or path.parent.name
        if name in by_name:
            continue
        by_name[name] = Skill(
            id=f"{source}/{name}",
            name=name,
            description=fields.get("description", ""),
            path=path.parent,
            source=source,
            body_chars=len(body),
            user_invoked=fields.get("disable-model-invocation", "").strip().lower() == "true",
            root=root,
        )
    return list(by_name.values())


def is_git_url(spec: str) -> bool:
    return spec.startswith(("http://", "https://", "git@")) or spec.endswith(".git")


def source_label(spec: str) -> str:
    if is_git_url(spec):
        tail = re.sub(r"\.git$", "", spec.rstrip("/"))
        parts = re.split(r"[/:]", tail)
        return "/".join(parts[-2:])
    return Path(spec).resolve().name


def load_sources(specs: List[str], cache_dir: Path) -> List[Skill]:
    """Resolve each spec (folder or git URL) and collect its skills."""
    skills: List[Skill] = []
    for spec in specs:
        label = source_label(spec)
        if is_git_url(spec):
            dest = cache_dir / label.replace("/", "__")
            if not dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(
                    ["git", "clone", "--depth", "1", "--quiet", spec, str(dest)],
                    check=True,
                )
            root = dest
        else:
            root = Path(spec).resolve()
            if not root.is_dir():
                raise FileNotFoundError(f"not a folder: {spec}")
        skills.extend(find_skills(root, label))
    return skills
