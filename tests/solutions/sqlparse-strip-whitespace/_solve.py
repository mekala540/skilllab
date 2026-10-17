"""Reference solution: the upstream fix, read from the cached clone."""
import subprocess
from pathlib import Path

from skilllab.runner import ensure_commits

FIX = '0c4902f3f7aafa8c2e63a375ec307c210842f543'
gitdir = ensure_commits('https://github.com/andialbrecht/sqlparse.git', FIX)
for path in ['sqlparse/filters/others.py']:
    data = subprocess.run(['git', '--git-dir', str(gitdir), 'show', f'{FIX}:{path}'],
                          capture_output=True, check=True).stdout
    Path(path).write_bytes(data)
