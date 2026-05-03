---
name: julia-coding
description: Use whenever Codex reads, explains, reviews, edits, or writes Julia code. Apply Julia-specific editing discipline, local style preservation, multiple-dispatch judgment, mutation conventions, Revise-aware workflows, and scientific-code caution.
---

# Julia Coding

## First Moves

Before editing Julia code:

1. Identify the requested edit scope: file, function, or exact skeleton.
2. If the user provided a skeleton, or the target is a `tmp_*.jl` / scratch script, preserve that shape. Fill blanks or fix the direct bug first.
3. Do not add helper functions, modules, file-level constants, new entrypoints, dependencies, or generalized APIs unless the user explicitly asks or the existing local pattern requires it.
4. Prefer the smallest local change that makes the current code work.
5. When running Julia in a repository or project, use the Julia Project REPL Workflow skill first.

## Editing Rules

- Match local style over generic Julia advice.
- Complete existing functions before considering refactors.
- Do not turn a narrow script fix into a reusable framework.
- Preserve existing Unicode/math notation such as `𝕢`, `τ`, `∂L∂q`, and `@SVector`.
- Preserve local abbreviations and conventions such as `cal...`, `mk...`, `!` suffixes, dotted calls, and broadcast style.
- Prefer Base, stdlib, and existing project dependencies before adding anything new.
- In package or library code, use multiple dispatch and small functions when they reduce real complexity.
- In temporary scripts, notebooks, experiments, and user-provided skeletons, avoid new abstractions unless asked.

## Julia Gotchas

- `TOML.parse(str)` parses TOML text; use `TOML.parsefile(path)` to read a TOML file.
- `include` re-evaluates a file; prefer `Revise.includet` when the project uses Revise or already calls `includet`.
- Julia does not require vectorization for performance. Use clear scalar loops when they express the algorithm.
- Mutating functions should end in `!`; remember `x *= y` rebinds `x`, while `x[i] = y` mutates.
- When broadcasting over non-array values such as dictionaries, models, tuples, or paths, use `Ref(x)` when needed to keep them scalar-like.

## Explanations

When explaining Julia code to users, translate punctuation and dispatch behavior only as needed for the question. Keep explanations grounded in the local code rather than generic Julia tutorials.
