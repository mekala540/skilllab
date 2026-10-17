# Plausible but wrong: trusts git blame on the current line for the last change.
import subprocess
from pathlib import Path

log = subprocess.run(["git", "log", "--format=%H %s"], capture_output=True, text=True).stdout.splitlines()
h = {l.split(" ", 1)[1]: l.split()[0] for l in log}
Path("ANSWER.md").write_text(
    f"introduced: {h['Cap combined discounts at 25%']}\nissue: 214\n"
    f"last_value_change: {h['Move the cap back below the tables']}\nprevious_value: 0.25\n")
