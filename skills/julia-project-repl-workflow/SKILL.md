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

Use Revise.jl for iterative package development whenever it is available in the active Julia load path. Load Revise before loading the package under development, keep the same REPL alive across edits, and call `Revise.revise()` before rerunning focused checks after file edits. Do not repeatedly restart Julia, reload the package from scratch, or run full `Pkg.test()` as the main edit-check loop.

## Choose The Working Directory

Start Julia from the repository or project root whenever one is known.

If the user or repository instructions specify a root directory, use that directory. Otherwise, use the current task's repository root or the nearest directory that owns the Julia project files.

## Startup

Before starting Julia, if the repository is under `/mnt/c` and a root `Manifest.toml` exists, check its `julia_version` header. If a matching Windows Juliaup executable exists under `/mnt/c/Users/<user>/.julia/juliaup/julia-<version>*/*/bin/julia.exe`, prefer that executable over WSL `julia`. This keeps the session on the same depot and manifest environment the Windows project normally uses.

Do not run `Pkg.instantiate()` or diagnose dependency corruption until you have verified that the Julia executable, `Base.active_project()`, and `DEPOT_PATH` match the intended project environment.

If the chosen working directory contains `Project.toml` or `JuliaProject.toml`, start Julia with:

```bash
source ~/.bashrc && julia --project=. --banner=no -q
```

If no project file exists in the chosen working directory, start Julia with:

```bash
source ~/.bashrc && julia --banner=no -q
```

Use `tty=true` when starting the REPL.

### WSL With Existing Windows Julia

If WSL `julia` is unavailable or Juliaup fails because it is trying to write configuration or lock files through Windows environment variables such as `APPDATA`, do not install or repair a separate WSL Julia unless the user explicitly asks for that.

When the user prefers the existing Windows Julia environment, or when the repository lives under `/mnt/c` and the manifest appears to have been generated from Windows Julia, launch the Windows Julia executable directly from WSL instead of using `cmd.exe`, `powershell.exe`, or the WindowsApps App Execution Alias. Do not hard-code a user-specific Julia path in instructions or project files. First discover candidate executables:

```bash
sed -n '1,8p' Manifest.toml
find /mnt/c/Users/$USER/.julia/juliaup -maxdepth 6 -name julia.exe -print
```

Choose the executable whose version matches `Manifest.toml` when possible. If `$USER` does not match the Windows profile name, inspect `/mnt/c/Users` narrowly for the project owner rather than scanning the whole drive. Then start the selected executable from the chosen repository/project root:

```bash
<discovered-julia.exe> --project=. --banner=no -q --color=no
```

Run this from the chosen repository/project root with `tty=true`, then continue to use the same PTY session with `write_stdin`.

If Julia starts in a different working directory because of Windows startup configuration, correct it inside the same REPL before using relative project paths:

```julia
cd(dirname(Base.active_project()))
```

Then verify the active project and depot:

```julia
Base.active_project()
VERSION
DEPOT_PATH
```

For package development, initialize the iterative session before loading the package:

```julia
try
    using Revise
catch err
    @warn "Revise is not available in the current load path; continue without it" exception=(err, catch_backtrace())
end
```

After this, load the package or test targets. If Revise loaded successfully, rerun `Revise.revise()` after code edits before repeating focused checks.

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
2. Verify `Base.active_project()` before continuing when project activation matters.
3. Load Revise before loading the package under development.
4. Re-run any task-specific bootstrap code that had only lived in memory.

## Operational Notes

- Keep using the same persistent REPL for iterative Julia commands.
- Prefer focused checks inside the persistent Revise session, for example rerunning the changed function, a narrow `@testset`, or a single included test file.
- Reserve full `Pkg.test()` for final verification or for failures that only reproduce in the package test sandbox. `Pkg.test()` creates a temporary test environment and can trigger extra package loading, precompilation, and disk writes.
- Shell commands that are not Julia execution may still be run normally.
- Do not add repository-local wrapper scripts or alternate Julia entrypoints for this workflow unless the user explicitly asks for them.

## Focused Benchmarks

When comparing Julia performance, use the standard Julia tool first: `BenchmarkTools.@benchmark` or `@btime`, not ad hoc wall-clock timing.

Prepare the compared conditions in the simplest reliable way available: two functions, two files, two branches, copied methods, stashed changes, or another local mechanism. The mechanism is incidental; keep inputs, setup, Julia version, project environment, and measured expression comparable.

Keep setup outside the measured expression unless setup cost is the target. Use `$` interpolation in BenchmarkTools expressions. Report time plus memory and allocation counts.

Do not create reusable benchmark infrastructure for a one-off speed question unless the user asks or you confirm first.
