---
name: julia-coding
description: Use whenever Codex reads, explains, reviews, edits, or writes Julia code. Apply Julia-specific editing discipline, local style preservation, multiple-dispatch judgment, mutation conventions, Revise-aware workflows, and scientific-code caution.
---

# Julia Coding

## Style References

At the start of each Julia coding task, before the first edit or write, open and read the current guidance at:

- [Julia Style Guide](https://docs.julialang.org/en/v1/manual/style-guide/)
- [Julia Short-Circuit Evaluation](https://docs.julialang.org/en/v1/manual/control-flow/#Short-Circuit-Evaluation)
- [BlueStyle](https://github.com/JuliaDiff/BlueStyle)
- [JuliaFormatter Code Style](https://domluna.github.io/JuliaFormatter.jl/dev/style/)

Read these references once per task. Do not reopen them before subsequent edits in the same task unless the user asks or the guidance must be rechecked.

Apply explicit user instructions and the existing local style first, then Julia's official guidance. Use BlueStyle and JuliaFormatter only for formatting decisions that remain unspecified.

## First Moves

Before editing Julia code:

1. Identify the requested edit scope: file, function, or exact skeleton.
2. If the user provided a skeleton, or the target is a `tmp_*.jl` / scratch script, preserve that shape. Fill blanks or fix the direct bug first.
3. Do not add helper functions, modules, file-level constants, new entrypoints, dependencies, or generalized APIs unless the user explicitly asks or the existing local pattern requires it.
4. Prefer the smallest local change that makes the current code work.
5. When running Julia in a repository or project, use the Julia Project REPL Workflow skill first.

## Editing Rules

- Match local style over generic Julia advice. When existing code provides a reference, follow its structure and syntax instead of substituting a preferred personal style.
- Before introducing or renaming an identifier, search analogous project code and follow the established convention. Preserve semantic distinctions carried by names, including the differentiation variable, scalar versus vector quantities, and callables versus computed values.
- Treat whitespace as intentional formatting. Preserve tabs versus spaces, relative indentation depth, blank lines, and horizontal spacing used to align related expressions or arguments vertically.
- When moving or inserting code, reproduce the surrounding block's relative indentation and column alignment. Before finalizing, inspect the diff and remove unintended whitespace-only or style-only changes outside the requested edit.
- Complete existing functions before considering refactors.
- Do not turn a narrow script fix into a reusable framework.
- Preserve existing Unicode/math notation such as `𝕢`, `τ`, `∂L∂q`, and `@SVector`.
- Preserve comments unless the corresponding code or explanation is no longer valid. In scientific code, write comments that explain mathematical or physical meaning, invariants, or non-obvious reasons rather than restating the syntax.
- Add a local variable, helper, wrapper, container conversion, or reassignment only when it clarifies a distinct concept, matches an established structure, or has a verified correctness or performance purpose.
- Prefer Base, stdlib, and existing project dependencies before adding anything new.
- In package or library code, use multiple dispatch and small functions when they reduce real complexity.
- In temporary scripts, notebooks, experiments, and user-provided skeletons, avoid new abstractions unless asked.

## Type Stability and Closures

- Treat type stability as a property of a concrete call path, not of an isolated expression or one observed input. Check the public or downstream call path with representative argument types from the supported API, using tools such as `@code_warntype` or `@inferred` when appropriate.
- Use type conversions, assertions, and return annotations only when they express a real numerical or API contract. They must not conceal an inference problem by forcing the observed result into a convenient type.
- A closure captures a binding when it uses a variable from an enclosing scope. Reassigning that captured binding can make Julia store it in `Core.Box`, a shared mutable container that can impede inference and add allocation. Prefer a closure-local binding with a distinct name when the values need not be shared; use an explicit state object when shared mutation is intentional.

## Julia Gotchas

- `TOML.parse(str)` parses TOML text; use `TOML.parsefile(path)` to read a TOML file.
- `include` re-evaluates a file; prefer `Revise.includet` when the project uses Revise or already calls `includet`.
- Julia does not require vectorization for performance. Use clear scalar loops when they express the algorithm.
- Mutating functions should end in `!`; remember `x *= y` rebinds `x`, while `x[i] = y` mutates.
- When broadcasting over non-array values such as dictionaries, models, tuples, or paths, use `Ref(x)` when needed to keep them scalar-like.

## Explanations

When explaining Julia code to users, translate punctuation and dispatch behavior only as needed for the question. Keep explanations grounded in the local code rather than generic Julia tutorials.
