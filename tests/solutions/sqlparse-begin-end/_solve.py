"""Reference solution: the upstream fix, read from the cached clone."""
import subprocess
from pathlib import Path

from skilllab.runner import ensure_commits

FIX = '1a3bfbd50b82c05d9adcc51bacba059671dc1bc7'
gitdir = ensure_commits('https://github.com/andialbrecht/sqlparse.git', FIX)
for path in ['sqlparse/engine/statement_splitter.py']:
    data = subprocess.run(['git', '--git-dir', str(gitdir), 'show', f'{FIX}:{path}'],
                          capture_output=True, check=True).stdout
    Path(path).write_bytes(data)
