---
name: julia-coding
description: Use whenever Codex reads, explains, reviews, edits, or writes Julia code. Apply Julia-specific syntax, idioms, style, abbreviation, Unicode notation, multiple dispatch, broadcasting, mutation conventions, module/import behavior, and performance guidance. Especially useful for Julia packages, scientific/numerical code, and code with symbols such as `!`, `?`, `::`, `where`, `Ref`, `Val`, dotted calls, Greek identifiers, `@SVector`, `@MVector`, or functions like `farm!`, `calFm!`, and `mk...`.
---

# Julia Coding

## Core Stance

Treat Julia as a multiple-dispatch, type-specializing scientific language, not as Python, MATLAB, or C with different syntax.

- Prefer small functions and dispatch over large type-switching code.
- Prefer clear scalar loops when they express the algorithm; Julia does not require vectorization for speed.
- Add type annotations mainly for dispatch, data layout, readability, and correctness. Do not add them reflexively for performance.
- Preserve existing Unicode mathematical notation when the file already uses it.
- Match local style before imposing generic Julia style.

## Reading Julia Syntax

Use these translations when explaining or modifying code:

- `f(x) = expr`: one-line method definition.
- `function f(x) ... end`: multi-line method definition.
- `x -> expr`: anonymous function.
- `do` block: anonymous function passed as the first argument, e.g. `map(xs) do x ... end`.
- `f(args...; kwargs...)`: positional arguments before `;`, keyword arguments after `;`.
- `where {T,N}`: method or type parameter binding.
- `x::T`: type annotation or assertion, depending on context.
- `T{A,B}`: type parameters, not block syntax.
- `a...`: splat in calls, slurp in varargs definitions.
- `a ? b : c`: ternary conditional.
- `:(...)` and `:name`: quoted expression and `Symbol`.
- `a |> f`: pipe `a` into function `f`.
- `f ∘ g`: function composition.
- `A'`: adjoint, not plain transpose for complex arrays.
- `(a, b)`: tuple; `(a=1, b=2)`: `NamedTuple`.
- `[a, b]`: vector; `[a b]`: horizontal concatenation; `[a; b]`: vertical concatenation.
- `a:b` and `a:s:b`: ranges; `:` alone usually means all indices in a dimension.
- `x[]`: index/getindex syntax; for zero-dimensional refs/arrays it gets the contained value.

## Naming And Conventions

Follow Julia Base conventions unless the codebase already made a deliberate local choice.

- Types and modules: `UpperCamelCase`.
- Functions: lowercase, often words joined together (`haskey`, `isequal`); use `_` only when it improves clarity.
- Mutating functions end in `!`, e.g. `update!`, `calFm!`. The `!` is a convention, not enforced by the compiler.
- Avoid cryptic abbreviation in new names. Existing `mk...`, `cal...`, or domain-specific symbols may be local convention; document or preserve them if widespread.
- Use `?` in predicate-like names only if the codebase does; Julia Base more often uses `is...` / `has...`.
- All-underscore identifiers are write-only discards. Use `_` or `___` to ignore values, not as readable state.
- Non-exported names are not hidden. They are accessible by qualification, but treat them as internal unless documented otherwise.

## Unicode And Mathematical Code

Julia permits Unicode identifiers and operators; scientific repositories often use them to mirror equations.

- Do not replace `𝕢`, `γ`, `l̇_c`, `∂L∂q`, `τ`, `η`, etc. just to make code ASCII.
- When adding nearby variables, follow the local mathematical vocabulary. Prefer a short comment over transliterating every symbol.
- Greek letters, subscripts, superscripts, primes, and combining marks are identifiers when valid.
- Operators can be identifiers too. Use parentheses or qualification when needed: `(+)`, `Base.:+`, `Base.:(==)`.
- Explain Unicode symbols in prose when user-facing docs need approachability.

## Multiple Dispatch And APIs

Prefer dispatch-friendly APIs.

- Add methods to a generic operation instead of branching on concrete types inside one method.
- Use abstract argument types for dispatch boundaries when they express the API (`AbstractVector`, `Real`, `Number`), but keep fields and containers concrete where performance matters.
- Do not over-constrain method arguments to `Vector{Float64}` if `AbstractVector{<:Real}` or no annotation better matches the algorithm.
- Follow Base argument order when designing new functions:
  function argument, `IO`, mutated input, type, non-mutated input, key, value, other args.
- If extending a function from another module, either qualify the method name (`Base.show(...) = ...`) or import the function before adding methods.
- Keep `export` near the top of modules when possible; treat exported names as public API.

## Mutation And Sharing

Julia passes arguments by sharing. Mutating an array or mutable struct inside a function can affect the caller's object.

- Use `!` suffix for functions that mutate any argument.
- Put the mutated argument early, usually first after a function argument or `IO`.
- Use `copy` or `deepcopy` explicitly when a non-mutating wrapper needs to protect caller-owned data.
- Distinguish rebinding (`x = ...`) from mutation (`x[i] = ...`, `x.field = ...`, `x .= ...`).
- Remember updating operators like `x *= 2` rebind `x` as `x = x * 2`; the variable type may change.

## Broadcasting And Dotted Syntax

Read dotted calls as broadcasting and prefer them for elementwise operations.

- `f.(xs)`: broadcast `f` over `xs`.
- `a .+ b`, `a .* b`, `A .^ 2`: elementwise operators.
- `.=`: broadcasted assignment, usually in-place.
- Dotted operations fuse: `2 .* A.^2 .+ sin.(A)` is one broadcast expression.
- `@.` dots a whole expression. Use carefully; it can dot calls you did not intend.
- `Ref(x)` in broadcast marks `x` as a scalar-like value: `length.(paths, Ref(q), Ref(l))`.
- Leave spaces around dotted numeric operators when ambiguity exists: `1 .+ x`, not `1.+x`.

## Types And Data Layout

Prefer concrete, parametric data structures in performance-sensitive code.

- Avoid fields typed as `Function`, `Array`, `Vector`, `Real`, or `Any` unless dynamic dispatch is intentional.
- Prefer `struct Wrapper{F}; f::F; end` over `f::Function`.
- Prefer `struct Foo{A}; data::A; end` or `data::Vector{T}` with `Foo{T}` over `data::Array`.
- Avoid `Vector{Real}` and other abstract-element containers for numeric kernels. Use concrete element types when practical.
- Use `zero(x)`, `oneunit(x)`, and `oftype(x, y)` to keep return and local variable types stable.
- Use `Val{N}` only when compile-time values materially help dispatch or inference; do not add it as decoration.
- For small fixed-size numerical vectors/matrices, `StaticArrays` patterns like `SVector`, `MVector`, `@SVector`, `@MVector`, and `@SMatrix` often signal intended fixed-size math. Keep them when the surrounding code relies on static sizes.

## Performance Checklist

When reviewing or changing Julia numerical code, check these before broad rewrites:

- Is the hot code inside functions, not at global scope?
- Are global constants marked `const` when they are performance-relevant?
- Does the function return a stable type across branches?
- Does a local variable change type inside a loop?
- Are containers and struct fields concrete enough?
- Is there a function barrier between setup code with uncertain types and tight kernels?
- Are allocations from slicing avoidable with views, `eachindex`, or preallocated outputs?
- Would a mutating `foo!` plus a non-mutating wrapper be clearer?
- Does `@code_warntype` show important non-concrete values in hot paths?
- Is a style rewrite likely to improve inference, allocation count, or API clarity? If not, leave it alone.

## Common Repository Idioms

Expect these in scientific Julia packages:

- `@kwdef`: keyword-default constructor for structs.
- `@unpack`: destructuring fields from `Parameters.jl`.
- `@recipe`: plotting recipe from `RecipesBase.jl`.
- `getproperty.(xs, :field)`: broadcast field access.
- `map(zip(...)) do (...) ... end`: zipped iteration with a multi-line anonymous function.
- `ntuple(i -> ..., N)`: construct tuples whose length may matter for type stability.
- `Base.show`, `Base.getproperty`, `Base.length`: extending Base interfaces for custom types.
- `mk...` prefixes often mean "make a closure", e.g. `mkM(p)` returning `M(q)`.
- `cal...` prefixes often mean "calculate"; preserve if established locally even if `compute...` would be clearer elsewhere.

## Editing Rules

- Preserve public API unless the user asks for a breaking change.
- Keep Unicode-heavy formulas readable by adding local comments or docstrings, not by renaming all variables.
- Do not change every loop into broadcasting or every broadcast into loops; choose the clearer and more type-stable form.
- Before adding dependencies, check whether Base, stdlib, or existing project dependencies already provide the tool.
- When explaining code to users, translate Julia-specific punctuation and dispatch behavior explicitly.
- When running Julia commands in a project, combine this skill with the repository's Julia REPL workflow skill if available.

## Official References

Primary references used for this skill:

- Julia Style Guide: https://docs.julialang.org/en/v1/manual/style-guide/
- Julia Performance Tips: https://docs.julialang.org/en/v1/manual/performance-tips/
- Julia Functions: https://docs.julialang.org/en/v1/manual/functions/
- Julia Methods: https://docs.julialang.org/en/v1/manual/methods/
- Julia Modules: https://docs.julialang.org/en/v1/manual/modules/
- Julia Variables: https://docs.julialang.org/en/v1/manual/variables/
- Julia Arrays: https://docs.julialang.org/en/v1/manual/arrays/
- Julia Mathematical Operations: https://docs.julialang.org/en/v1/manual/mathematical-operations/
- Julia Punctuation: https://docs.julialang.org/en/v1/base/punctuation/
