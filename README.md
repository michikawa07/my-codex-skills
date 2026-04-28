# codex-skills

Personal Codex skills shared across machines.

This repository keeps user-authored skills in one Git-managed location. Each
machine can point Codex at `./skills` with a symlink, then update with `git pull`.

## Contents

- `skills/empirical-prompt-tuning`: prompt and skill evaluation workflow
- `skills/dynamixel-handler-release-notes`: DynamixelHandler_ release note workflow
- `skills/generate-ieee-response-letter`: IEEE response letter skeleton generation workflow
- `skills/julia-project-repl-workflow`: persistent Julia REPL workflow for Julia projects

## Install On A Machine

Clone this repository, then run:

```bash
./install.sh
```

By default this links:

```text
~/.agents/skills -> <repo>/skills
```

For older Codex setups that still read `~/.codex/skills`, run:

```bash
./install.sh --legacy-codex
```

If the target already exists as a normal directory, the script stops instead of
overwriting it. To move the existing directory aside and create the symlink:

```bash
./install.sh --legacy-codex --replace
```

Restart Codex after changing skill locations.

## Update

On each machine:

```bash
git pull
```

Because Codex reads the symlinked `skills/` directory, no copy step is needed
after pulling changes.
