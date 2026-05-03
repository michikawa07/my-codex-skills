---
name: julia-project-repl-workflow
description: Use when doing Julia work in a repository or Julia project. Select the user's established Julia executable, start one persistent REPL PTY, avoid one-shot Julia execution for editing or verification, use Revise/includet when appropriate, and stop instead of repairing Julia environments.
---

# Julia Project REPL Workflow

Use this skill before running Julia code in a repository or project.

## Non-Negotiables

- Use exactly one persistent Julia REPL PTY for iterative work.
- Send Julia code to that REPL with `write_stdin`.
- Do not use `julia -e` or fresh Julia processes for editing, testing, or verification.
- Do not install, repair, update, reset, or reconfigure Julia unless the user explicitly asks.
- Shell commands for file inspection and executable discovery are allowed.

## Select Julia Executable

Follow this order exactly:

1. If this task already has a live Julia REPL PTY, reuse it. Do not start another Julia.
2. If the user explicitly named a Julia executable for this task, use that executable.
3. Find the repository root: use the current working directory if it contains `Project.toml` or `JuliaProject.toml`; otherwise use the nearest parent that contains one; otherwise use the current working directory.
4. If the repository root path starts with `/mnt/c/`, choose the user's Windows Julia:

```bash
find /mnt/c/Users -path '*/.julia/juliaup/julia-*/bin/julia.exe' -print -quit 2>/dev/null
```

Use the path printed by that command. If it prints nothing, try:

```bash
command -v julia.exe
```

Do not use a `julia.exe` path under `WindowsApps`; treat that as no usable Windows Julia.

5. If the repository root does not start with `/mnt/c/`, choose WSL/Linux Julia with:

```bash
command -v julia
```

Use the exact path printed by that command as `<julia>`.

6. If the required discovery command for the selected environment prints no usable executable, stop and report only the discovery commands and outputs used for that selected environment. Do not probe, fall back to, or report another Julia environment unless the user approves.

## Start The REPL

Start the selected executable from the repository root with `tty=true`.

If the selected executable ends with `julia.exe`, run:

```bash
<julia.exe> --project=. --banner=no -q --color=no
```

Otherwise, if the repository root contains `Project.toml` or `JuliaProject.toml`, run:

```bash
source ~/.bashrc && <julia> --project=. --banner=no -q
```

Otherwise run:

```bash
source ~/.bashrc && <julia> --banner=no -q
```

If Windows Julia prints only `\e[6n` and appears stuck, reply in the same PTY with:

```text
\e[1;1R
```

Wait for the `julia>` prompt before sending Julia code.

## Verify The REPL

Immediately run in the same REPL:

```julia
Base.active_project()
pwd()
```

If `pwd()` is not the repository root, run:

```julia
cd(dirname(Base.active_project()))
pwd()
```

For Windows Julia launched from WSL, compare paths after conversion:

- `/mnt/c/Users/name/project` equals `C:\Users\name\project`
- `/mnt/d/path/to/project` equals `D:\path\to\project`

Apply this conversion only when comparing Julia-reported Windows paths with WSL repository paths.

For Windows Julia launched from WSL, an initial `pwd()` mismatch is expected and is not a failure if `Base.active_project()` equals the expected project file after this conversion and `cd(dirname(Base.active_project()))` corrects `pwd()`.

If `Base.active_project()` is not the expected project file when the repository has `Project.toml` or `JuliaProject.toml`, stop and report the mismatch. Do not continue in the wrong environment.

Keep the verified REPL alive for the rest of the task. Close it only when the task is complete and no further Julia work is needed.

If the user or scenario does not specify any Julia code to run after verification, stop after verification and report that the REPL is ready. Do not invent a Julia command.

Do not send `exit()` merely because verification succeeded. Keep the REPL available for subsequent Julia work unless the user explicitly asks to close it.

## Load Edited Files

If the project depends on Revise, or the codebase uses `includet`, load edited Julia files in the same REPL with:

```julia
using Revise
includet("path/to/file.jl")
```

Then re-run functions in the same REPL.

## Recovery

If the REPL cannot start, cannot accept input, exits unexpectedly, or uses the wrong project, stop and report:

- repository root,
- selected executable,
- command used,
- observed output or error,
- next proposed recovery step.

Do not switch Julia executables, use one-shot Julia commands, or modify the Julia installation without user approval.
