"""Reference solution: the upstream fix, read from the cached clone."""
import subprocess
from pathlib import Path

from skilllab.runner import ensure_commits

FIX = '1241abaed4e441582a21f4bf90c8482de02b92df'
gitdir = ensure_commits('https://github.com/pallets/click.git', FIX)
for path in ['src/click/exceptions.py']:
    data = subprocess.run(['git', '--git-dir', str(gitdir), 'show', f'{FIX}:{path}'],
                          capture_output=True, check=True).stdout
    Path(path).write_bytes(data)
