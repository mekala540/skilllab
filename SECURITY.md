# Security

skilllab runs an AI agent, and code it writes, on your machine. Each run uses a fresh
temporary folder. The agent gets an allowlist of simple commands (no loops, pipes or
chaining), so a skill's own scripts and arbitrary shell commands are denied. Checkers then
run the agent's output (tests, hooks, scripts) as normal processes.

Treat skill packs you test as untrusted:

- Run batches on a machine or container you're comfortable exposing to untrusted code.
- Review a task's `tools` before running it; each entry widens what the agent may run.
- Don't run skilllab with credentials or production access in the environment.

If you find a way for a skill or task to escape the workspace or bypass the allowlist, please
report it privately through GitHub's "Report a vulnerability" (Security tab) rather than in a
public issue.
