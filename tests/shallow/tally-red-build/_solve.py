import subprocess
subprocess.run(["git", "add", "-A", "tally"], check=True)
subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m",
                "Fix regressions from the 2.5 prep commit"], check=True)
