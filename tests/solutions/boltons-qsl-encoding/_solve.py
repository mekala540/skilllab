"""Reference solution: the upstream fix, read from the cached clone."""
import subprocess
from pathlib import Path

from skilllab.runner import ensure_commits

FIX = 'd45cc414e33aa4e08a73e0993574df4397e2e9db'
gitdir = ensure_commits('https://github.com/mahmoud/boltons.git', FIX)
for path in ['boltons/urlutils.py']:
    data = subprocess.run(['git', '--git-dir', str(gitdir), 'show', f'{FIX}:{path}'],
                          capture_output=True, check=True).stdout
    Path(path).write_bytes(data)
