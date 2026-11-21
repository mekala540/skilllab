"""Reference solution: the upstream fix, read from the cached clone."""
import subprocess
from pathlib import Path

from skilllab.runner import ensure_commits

FIX = 'ac88f563db5f4d3300d43355eca728c93ed9ffe2'
gitdir = ensure_commits('https://github.com/fastapi/fastapi.git', FIX)
for path in ['fastapi/routing.py']:
    data = subprocess.run(['git', '--git-dir', str(gitdir), 'show', f'{FIX}:{path}'],
                          capture_output=True, check=True).stdout
    Path(path).write_bytes(data)
