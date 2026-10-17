"""Reference solution: the upstream fix, read from the cached clone."""
import subprocess
from pathlib import Path

from skilllab.runner import ensure_commits

FIX = '448b1db11afdde8edaf7c2c280a5b38f0d8672a7'
gitdir = ensure_commits('https://github.com/mahmoud/boltons.git', FIX)
for path in ['boltons/listutils.py']:
    data = subprocess.run(['git', '--git-dir', str(gitdir), 'show', f'{FIX}:{path}'],
                          capture_output=True, check=True).stdout
    Path(path).write_bytes(data)
