"""Reference solution: the upstream fix, read from the cached clone."""
import subprocess
from pathlib import Path

from skilllab.runner import ensure_commits

FIX = '3a3e0350b6a2ea3e799440d48e779acabcf44de9'
gitdir = ensure_commits('https://github.com/pallets/click.git', FIX)
for path in ['src/click/core.py']:
    data = subprocess.run(['git', '--git-dir', str(gitdir), 'show', f'{FIX}:{path}'],
                          capture_output=True, check=True).stdout
    Path(path).write_bytes(data)
