"""Reference solution: the upstream fix, read from the cached clone."""
import subprocess
from pathlib import Path

from skilllab.runner import ensure_commits

FIX = '8789df2cc35a4d9ddfebfa59c14f3e80e34234e1'
gitdir = ensure_commits('https://github.com/mahmoud/boltons.git', FIX)
for path in ['boltons/timeutils.py']:
    data = subprocess.run(['git', '--git-dir', str(gitdir), 'show', f'{FIX}:{path}'],
                          capture_output=True, check=True).stdout
    Path(path).write_bytes(data)
