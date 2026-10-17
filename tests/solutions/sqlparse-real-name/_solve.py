"""Reference solution: the upstream fix, read from the cached clone."""
import subprocess
from pathlib import Path

from skilllab.runner import ensure_commits

FIX = 'f66d12c245412f28c58f045b646eb53c0e691b8b'
gitdir = ensure_commits('https://github.com/andialbrecht/sqlparse.git', FIX)
for path in ['sqlparse/sql.py']:
    data = subprocess.run(['git', '--git-dir', str(gitdir), 'show', f'{FIX}:{path}'],
                          capture_output=True, check=True).stdout
    Path(path).write_bytes(data)
