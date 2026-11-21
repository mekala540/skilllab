"""Reference solution: the upstream fix, read from the cached clone."""
import subprocess
from pathlib import Path

from skilllab.runner import ensure_commits

FIX = 'd1fd422fd9c3b24b0e2bcf1cc89f1e7249b5fcd6'
gitdir = ensure_commits('https://github.com/fastapi/fastapi.git', FIX)
for path in ['fastapi/routing.py']:
    data = subprocess.run(['git', '--git-dir', str(gitdir), 'show', f'{FIX}:{path}'],
                          capture_output=True, check=True).stdout
    Path(path).write_bytes(data)
