---
name: julia-project-repl-workflow
description: Use when doing Julia work in a repository or Julia project. Enforce one persistent Julia REPL PTY for iterative Julia execution, choose --project=. when the working directory has Project.toml or JuliaProject.toml, avoid one-shot julia invocations, and recover the REPL session correctly if it is lost.
---

# Julia Project REPL Workflow

## Scope

Use this skill for Julia work in any repository or Julia project.

This skill controls the Julia execution workflow. It does not change project code, add wrapper scripts, or introduce alternate entrypoints unless the user explicitly asks for that.

## Core Rule

Do not start a fresh `julia` process for every command.

For iterative Julia work, start one persistent Julia REPL with `tty=true`, then send subsequent Julia inputs into that same PTY session with `write_stdin`.

Do not use `julia -e` or other one-shot Julia invocations as a substitute for the persistent REPL.

## Choose The Working Directory

Start Julia from the repository or project root whenever one is known.

If the user or repository instructions specify a root directory, use that directory. Otherwise, use the current task's repository root or the nearest directory that owns the Julia project files.

## Startup

If the chosen working directory contains `Project.toml` or `JuliaProject.toml`, start Julia with:

```bash
source ~/.bashrc && julia --project=. --banner=no -q
```

If no project file exists in the chosen working directory, start Julia with:

```bash
source ~/.bashrc && julia --banner=no -q
```

Use `tty=true` when starting the REPL.

## Verify The Active Project

After startup, verify the active project when project activation matters:

```julia
Base.active_project()
```

If repository instructions provide an expected `Project.toml` path, compare against that exact value.

If the value is wrong, restart the persistent REPL from the correct directory with the correct startup command.

## Recovery

If the PTY session is lost:

1. Start a new Julia PTY session from the repository or project root using the appropriate startup command above.
2. Re-run any task-specific bootstrap code that had only lived in memory.
3. Verify `Base.active_project()` before continuing when project activation matters.

## Operational Notes

- Keep using the same persistent REPL for iterative Julia commands.
- Shell commands that are not Julia execution may still be run normally.
- Do not add repository-local wrapper scripts or alternate Julia entrypoints for this workflow unless the user explicitly asks for them.
