# codex-skills

Personal Codex skills and hooks shared across machines.

This repository keeps user-authored skills and hooks in one Git-managed
location. Each machine links Codex to `./skills` and `./hooks`, then receives
updates with `git pull`.

## Contents

- `skills/dynamixel-handler-release-notes`: DynamixelHandler_ release note workflow
- `skills/empirical-prompt-tuning`: prompt and skill evaluation workflow
- `skills/generate-ieee-response-letter`: IEEE response letter skeleton generation workflow
- `skills/julia-coding`: Julia code editing and review workflow
- `skills/julia-project-repl-workflow`: persistent Julia REPL workflow for Julia projects
- `skills/quote-revised-manuscript`: revised-manuscript quotation workflow for response letters
- `skills/todo-archive-consensus`: TODO.md and ARCHIVE.md maintenance workflow
- `skills/typst-to-tex-converter`: Typst-to-TeX conversion workflow
- `hooks/restore_recent_context.py`: restores recent conversation and tool context after compaction

## Installation

Install in the same operating-system environment and user account where Codex
stores its configuration. For example, use WSL instructions only when Codex is
also running in WSL and uses that WSL user's `~/.codex`.

### Install with Codex

Give Codex the following request:

```text
Install https://github.com/michikawa07/my-codex-skills into ~/codex-skills.
If it is already cloned there, update it with a fast-forward-only pull instead.
Read its README and use the instructions for the operating-system environment
where this Codex session stores its configuration. Install both the skills and
hooks, verify the resulting links, and do not delete, replace, or move any
existing non-link path without asking me first. Finally, tell me how to review
and trust the SessionStart hook in the Codex surface I am currently using.
```

On Linux, macOS, or WSL, Codex should normally run `./install.sh --hooks`.
It should stop and ask before adding `--replace`, because that option moves
existing skills or hook paths aside.

### Manual installation on Linux, macOS, or WSL

Clone the repository and install both the skills and shared hooks:

```bash
git clone https://github.com/michikawa07/my-codex-skills.git ~/codex-skills
cd ~/codex-skills
./install.sh --hooks
```

This creates symlinks instead of copying files:

```text
~/.agents/skills    -> ~/codex-skills/skills
~/.codex/hooks      -> ~/codex-skills/hooks
~/.codex/hooks.json -> ~/codex-skills/hooks/hooks.json
```

To install only the skills, omit `--hooks`. For older Codex setups that still
read `~/.codex/skills`, add `--legacy-codex`.

If a target is an existing normal file or directory, the installer stops
without changing it. Inspect that path before using `--replace`; replacement
moves it to a timestamped backup and may supersede an existing hooks setup.

### Manual installation on native Windows

Clone this repository to `$HOME\codex-skills`:

```powershell
git clone https://github.com/michikawa07/my-codex-skills.git "$HOME\codex-skills"
```

Create a directory junction for each skill. The snippet checks every destination
before changing anything and stops if a same-named path already exists. Linking
skills individually keeps Codex's bundled `$HOME\.codex\skills\.system`
directory intact.

```powershell
$repoSkills = "$HOME\codex-skills\skills"
$codexSkills = "$HOME\.codex\skills"

New-Item -ItemType Directory -Force -Path $codexSkills | Out-Null

$plannedLinks = Get-ChildItem -LiteralPath $repoSkills -Directory | ForEach-Object {
    [PSCustomObject]@{
        Source = $_.FullName
        Link = Join-Path $codexSkills $_.Name
    }
}

$conflicts = $plannedLinks | Where-Object { Test-Path -LiteralPath $_.Link }
if ($conflicts) {
    $paths = ($conflicts.Link -join "`n")
    throw "Existing skill paths must be reviewed before installation:`n$paths"
}

$plannedLinks | ForEach-Object {
    New-Item -ItemType Junction -Path $_.Link -Target $_.Source | Out-Null
}
```

For the hooks, first confirm that `$HOME\.codex\hooks` and
`$HOME\.codex\hooks.json` do not contain another hooks setup. Then create a
directory junction and file symbolic link:

```powershell
$repoHooks = "$HOME\codex-skills\hooks"
$codexRoot = "$HOME\.codex"

New-Item -ItemType Directory -Force -Path $codexRoot | Out-Null
New-Item -ItemType Junction -Path "$codexRoot\hooks" -Target $repoHooks
New-Item -ItemType SymbolicLink -Path "$codexRoot\hooks.json" -Target "$repoHooks\hooks.json"
```

On native Windows, `hooks/hooks.json` uses the Python runtime bundled with
Codex Desktop:

```text
%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

Verify that runtime before enabling the hook:

```powershell
$python = "$HOME\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Codex bundled Python was not found: $python"
}
& $python --version
```

If Codex stores its bundled runtime elsewhere, update `commandWindows` in
`hooks/hooks.json` to that Python executable. This does not affect the
Linux, macOS, or WSL `command`, which continues to use `python3`.

Creating a file symbolic link may require Windows Developer Mode or an elevated
PowerShell session. Do not overwrite an existing `hooks.json`; merge its hook definitions
or back it up deliberately instead.

### Trust the hook

Restart or reload Codex after installation. In the VS Code extension, open the
Codex sidebar settings, select **Hooks**, find the `SessionStart` hook under the
user configuration, and select **Trust**. In the Codex CLI, review it from
`/hooks`. The installer cannot grant this trust.

Codex requires another review whenever the hook definition changes.

### What the compaction hook restores

On context compaction, the hook restores one chronological event stream built
from up to five recent conversation exchanges and the five latest tool uses.
User and Codex messages, tool-call inputs, and tool results retain their
transcript line order. Event content is copied verbatim; when the size limit is
reached, older content is shortened first with an explicit truncation marker
instead of being summarized.

## Update

On Linux, macOS, or WSL:

```bash
git -C ~/codex-skills pull --ff-only
```

On native Windows:

```powershell
git -C "$HOME\codex-skills" pull --ff-only
```

Because Codex reads the linked skills and hooks, no copy step is needed after
pulling changes. If `hooks.json` changed, review and trust the hook again from
the VS Code **Hooks** settings or the CLI `/hooks` screen.
