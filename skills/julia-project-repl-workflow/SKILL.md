---
name: julia-project-repl-workflow
description: Use when doing Julia work in a repository or Julia project. Select the user's established Julia executable, keep one persistent REPL PTY, provision Revise in the shared Julia environment, track source before the first edit, and apply every later edit through Revise.
---

# Julia Project REPL Workflow

Use this skill before running Julia code in a repository or project.

## Highest-Priority Objective

Minimize steady-state edit-run latency during iterative Julia work. This objective governs every decision in this skill and takes priority over all later procedural guidance.

- The persistent REPL preserves loaded packages, plotting backends, runtime state, and JIT-compiled code across edits.
- Revise applies source differences to that same process, preserving unchanged definitions and their compiled state.
- Julia startup, package loading, Revise provisioning, and source tracking are one-time preparation steps.
- After preparation, the complete steady-state loop is exactly: edit the tracked source, call `Revise.revise()`, run the affected function.

Treat the remaining sections as the default implementation of this objective. When an actual environment makes a listed procedure conflict with the objective, choose the action that best preserves the warm process, unchanged definitions, compiled state, and smallest source delta, then report the procedural deviation.

## Required Execution Path

- Keep exactly one persistent Julia REPL PTY for the task and send every Julia command to it with `write_stdin`.
- Establish a Revise-ready REPL before loading the code under edit.
- Track every standalone source file once with `Revise.includet`; load packages only after Revise.
- Run every edit cycle as: edit source, call `Revise.revise()`, run the affected function, observe completion.
- Treat failure to establish any required state as a terminal setup result and report that state to the user.
- Limit environment setup to provisioning Revise in the user's shared Julia environment. Escalate any other environment change to the user.
- Use shell commands for repository inspection and executable discovery.

## Reuse The Warm REPL

- Treat the persistent REPL as a performance mechanism, not as an end state. Reuse its loaded packages, JIT-compiled methods, plotting backend, and loaded function definitions so repeated work executes without startup and recompilation costs.
- When source code is unchanged, run only the functions needed to consume the latest inputs and produce the requested outputs.
- When tracked source code changes, call `Revise.revise()` in the same REPL, then rerun only the affected functions.

## Run Commands To Completion

- Require evidence that the requested call returned successfully. For artifact-producing calls, require evidence produced after the artifact-writing call returns.
- Treat an artifact path emitted after its save operation as evidence that the artifact write completed. Treat a returned value, an `@time` summary from a call wrapped before execution, or the next `julia>` prompt as evidence that the enclosing Julia call returned.
- For routine repeated execution, send the function call with the default non-empty `write_stdin` behavior and evaluate the returned output immediately.
- When the returned output establishes completion or failure, finish the observation step and report the result.
- When the returned output is insufficient during an ordinary non-interactive Julia call, queue a newline or no-op with the normal non-empty `write_stdin` behavior and evaluate the returned chunk immediately. Use an empty poll instead when the running code may read terminal input.

## Select Julia Executable

Follow this order exactly:

1. If this task already has a live Julia REPL PTY, reuse it. Do not start another Julia.
2. If the user explicitly named a Julia executable for this task, use that executable.
3. Find the repository root: use the current working directory if it contains `Project.toml` or `JuliaProject.toml`; otherwise use the nearest parent that contains one; otherwise use the current working directory.
4. If the repository root is a native Windows path such as `C:\repo`, choose the user's Windows Julia in PowerShell:

```powershell
(Get-Command julia.exe -ErrorAction SilentlyContinue).Source
Get-ChildItem -LiteralPath "$env:USERPROFILE\.julia\juliaup" -Filter julia.exe -Recurse -File -ErrorAction SilentlyContinue |
    Select-Object -First 1 -ExpandProperty FullName
```

Use the first existing path that ends in `julia.exe` and is outside `WindowsApps`.

5. If the repository root path starts with `/mnt/`, choose the user's Windows Julia from WSL:

```bash
find /mnt/c/Users -path '*/.julia/juliaup/julia-*/bin/julia.exe' -print -quit 2>/dev/null
```

Use the path printed by that command. If it prints nothing, try:

```bash
command -v julia.exe
```

An acceptable Windows result ends in `julia.exe`, exists on disk, and has a path outside `WindowsApps`.

6. For a native Linux repository, choose Linux Julia with:

```bash
command -v julia
```

Use the exact path printed by that command as `<julia>`.

7. A discovery result is complete when it yields one existing executable for the selected environment. An empty result is a terminal discovery state; report the commands and their outputs.

## Start The REPL

Start the selected executable from the repository root with `tty=true`. Launch this one PTY with the approval and permission scope needed to access the project, the user's shared Julia depot, and the package network so Revise provisioning can complete in the same process.

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

## Establish The Revise Workflow

### 1. Provision Revise

Immediately after verifying the REPL, make Revise available in the user's shared Julia environment and restore the original project before continuing:

```julia
project = Base.active_project()
Base.find_package("Revise") === nothing && begin
    import Pkg
    try
        Pkg.activate()
        Pkg.add("Revise")
    finally
        Pkg.activate(dirname(project))
    end
end
using Revise
Base.active_project() == project || error("Failed to restore project: $project")
```

Successful completion of this block establishes the Revise-ready state. An installation, loading, or project-restoration error transitions to the `ReviseSetupFailed` state. At the returned prompt in the same REPL, collect:

```julia
(; active_project=Base.active_project(), repository_root=pwd())
```

Report the selected executable, provisioning command, complete observed error output, active project, and repository root. Keep the REPL at its prompt for user-directed recovery. A user-authorized recovery resumes this REPL and repeats only the failed provisioning step.

### 2. Track Source Once

Load packages after Revise so package source is tracked automatically:

```julia
using PackageUnderEdit
```

Track each standalone source file exactly once per REPL session:

```julia
Revise.includet("path/to/file.jl")
```

Keep repeatable computations inside functions. The tracked file defines those functions; the REPL invokes them.

### 3. Run The Edit Loop

For every requested source change, complete this cycle in the same REPL:

```julia
# edit the tracked source file
Revise.revise()
affected_function()
```

Observe the affected call until completion evidence defined above appears, then keep the REPL ready for the next edit cycle.

## Recovery

If the REPL cannot start, cannot accept input, exits unexpectedly, or uses the wrong project, stop and report:

- repository root,
- selected executable,
- command used,
- observed output or error,
- next proposed recovery step.

Keep the sole REPL open at its prompt while reporting a recoverable or terminal setup state. Resume that REPL only after the user authorizes the proposed recovery step.
