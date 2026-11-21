# caveman-voice

The caveman voice without the rest of the plugin, asked for by caveman's maintainers
([caveman#1323](https://github.com/JuliusBrussee/caveman/issues/1323)) to separate the voice's
cost from the bundled skills' that `--plugin-dir` also loads. Compare with [`../caveman`](../caveman/).

- **Repo:** https://github.com/JuliusBrussee/caveman, release `v4.0.1` (commit `d262ab3`).
- **Followed:** `README.md`, "Say less": *"Only want this rock? The skill alone, no proxy:
  `npx skills add JuliusBrussee/caveman -g` … Type `/caveman` … if it doesn't start on its own."*

## What this add-on does

- Copies one skill, `skills/caveman/` from the caveman checkout, into the workspace's
  `.claude/skills/`. No plugin, no hooks, none of the other skills. Fetch the checkout first, as
  in [`../caveman/README.md`](../caveman/README.md).
- Starts every task with `/caveman`, the way a skill-only user turns the voice on. Without a
  hook nothing turns it on by itself, so this measures the voice rather than an idle skill.
