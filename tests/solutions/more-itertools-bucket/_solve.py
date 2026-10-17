"""Reference solution: the upstream fix, read from the cached clone."""
import subprocess
from pathlib import Path

from skilllab.runner import ensure_commits

FIX = '2b8d5cddce4ea01f88a973551cd50479cf5fa45f'
gitdir = ensure_commits('https://github.com/more-itertools/more-itertools.git', FIX)
for path in ['more_itertools/more.py']:
    data = subprocess.run(['git', '--git-dir', str(gitdir), 'show', f'{FIX}:{path}'],
                          capture_output=True, check=True).stdout
    Path(path).write_bytes(data)
