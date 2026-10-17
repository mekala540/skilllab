"""Reference solution: the upstream fix, read from the cached clone."""
import subprocess
from pathlib import Path

from skilllab.runner import ensure_commits

FIX = '7d05a59b9d46a415d85937630d1d812cf477f60a'
gitdir = ensure_commits('https://github.com/pallets/click.git', FIX)
for path in ['src/click/core.py']:
    data = subprocess.run(['git', '--git-dir', str(gitdir), 'show', f'{FIX}:{path}'],
                          capture_output=True, check=True).stdout
    Path(path).write_bytes(data)
