import subprocess
from pathlib import Path

log = subprocess.run(["git", "log", "--format=%H %s"], capture_output=True, text=True).stdout.splitlines()
h = {l.split(" ", 1)[1]: l.split()[0] for l in log}
Path("ANSWER.md").write_text(
    f"introduced: {h['Cap combined discounts at 25%']}\nissue: 214\n"
    f"last_value_change: {h['Raise the discount cap to 30% for the spring campaign']}\nprevious_value: 0.25\n")
