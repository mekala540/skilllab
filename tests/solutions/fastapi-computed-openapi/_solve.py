"""Reference solution: the upstream fix, read from the cached clone."""
import subprocess
from pathlib import Path

from skilllab.runner import ensure_commits

FIX = 'a1a05b75d3e60f6ced5f3bb067232ebc6b47e201'
gitdir = ensure_commits('https://github.com/fastapi/fastapi.git', FIX)
for path in ['fastapi/_compat/v2.py']:
    data = subprocess.run(['git', '--git-dir', str(gitdir), 'show', f'{FIX}:{path}'],
                          capture_output=True, check=True).stdout
    Path(path).write_bytes(data)
