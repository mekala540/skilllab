"""Reference solution: the upstream fix, read from the cached clone."""
import subprocess
from pathlib import Path

from skilllab.runner import ensure_commits

FIX = 'def2dabea858b6ecb84ee0c52e6e07929f2c409c'
gitdir = ensure_commits('https://github.com/more-itertools/more-itertools.git', FIX)
for path in ['more_itertools/more.py']:
    data = subprocess.run(['git', '--git-dir', str(gitdir), 'show', f'{FIX}:{path}'],
                          capture_output=True, check=True).stdout
    Path(path).write_bytes(data)
