# codex-skills

Personal Codex skills shared across machines.

This repository keeps user-authored skills in one Git-managed location. Each
machine can point Codex at `./skills` with a symlink, then update with `git pull`.

## Contents

- `skills/dynamixel-handler-release-notes`: DynamixelHandler_ release note workflow
- `skills/empirical-prompt-tuning`: prompt and skill evaluation workflow
- `skills/generate-ieee-response-letter`: IEEE response letter skeleton generation workflow
- `skills/julia-coding`: Julia code editing and review workflow
- `skills/julia-project-repl-workflow`: persistent Julia REPL workflow for Julia projects
- `skills/quote-revised-manuscript`: revised-manuscript quotation workflow for response letters
- `skills/todo-archive-consensus`: TODO.md and ARCHIVE.md maintenance workflow
- `skills/typst-to-tex-converter`: Typst-to-TeX conversion workflow

## Install On Ubuntu

Clone this repository to `~/codex-skills`, then run the installer:

```bash
git clone https://github.com/michikawa07/my-codex-skills.git ~/codex-skills
cd ~/codex-skills
./install.sh
```

By default this links:

```text
~/.agents/skills -> ~/codex-skills/skills
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

## Install On Windows

Clone this repository to `$HOME\codex-skills`:

```powershell
git clone https://github.com/michikawa07/my-codex-skills.git "$HOME\codex-skills"
```

Create a directory junction for each skill. Existing copies with the same names
are removed before the junctions are created. Linking skills individually keeps
Codex's bundled `$HOME\.codex\skills\.system` directory intact.

```powershell
$repoSkills = "$HOME\codex-skills\skills"
$codexSkills = "$HOME\.codex\skills"

New-Item -ItemType Directory -Force -Path $codexSkills | Out-Null

Get-ChildItem -LiteralPath $repoSkills -Directory | ForEach-Object {
    $link = Join-Path $codexSkills $_.Name

    if (Test-Path -LiteralPath $link) {
        Remove-Item -LiteralPath $link -Recurse -Force
    }

    New-Item -ItemType Junction -Path $link -Target $_.FullName | Out-Null
}
```

Restart Codex after changing skill locations.

## Update

On Ubuntu:

```bash
cd ~/codex-skills
git pull
```

On Windows:

```powershell
git -C "$HOME\codex-skills" pull
```

Because Codex reads the linked skill directories, no copy step is needed after
pulling changes.
