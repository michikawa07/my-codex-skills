# Typst-to-TeX Rulebook

Use these rules for known constructs. If a construct is not covered here, in `decisions.md`, by TeX evidence, or by official documentation, stop at the current semantic element and ask for a rule.

## Source And Scaffold

- Typst source controls manuscript content. TeX evidence controls scaffold, macro style, package style, and build conventions.
- Preserve protected scaffold that has no Typst replacement, including template comments, class setup, `\history`, `\doi`, `\markboth`, and `\BibTeX`, in their evidence-relative preamble/body positions.
- Preserve IEEE Access `\markboth` placeholder text from TeX evidence unless the user explicitly supplies replacement page-header text. Do not derive `\markboth` from Typst metadata by default.
- For corresponding-author metadata such as `\corresp`, keep the command style from TeX evidence but derive the argument from active Typst metadata; if the source has no value, use an empty placeholder rather than copying unrelated evidence text.
- Do not copy active body content from TeX evidence into the converted body.
- Add packages only when required by converted constructs, TeX evidence, or explicit user instruction.
- `#import` lines do not emit visible TeX when their effects are accounted for by TeX evidence, this rulebook, or later source constructs. Stop only when an imported package/template introduces an active construct whose TeX mapping is still unknown.
- A top-level `#show: template.with(...)` may be converted as document metadata/scaffold when TeX evidence supplies the corresponding LaTeX template. Stop on fields inside the call whose TeX destination cannot be determined.

## Metadata

- Convert active `title` to the TeX evidence title command, usually `\title{...}`, preserving source line-break intent inside the argument.
- Convert active `authors` to the TeX evidence author command style. For IEEE Access evidence, use `\uppercase{name}\authorrefmark{affiliation}` for each active author.
- Convert active `abstract` to the TeX evidence abstract environment and active `index-terms` to the TeX evidence keyword environment.
- If active authors reference affiliation ids but the source has no active affiliation records and no explicit user-provided replacement, stop at the first author affiliation id. Do not promote commented-out affiliation text to active metadata without user approval.
- Preserve source metadata comments adjacent to the corresponding metadata command or field.

## Semantic Elements

- Convert one semantic element at a time: metadata field, heading, comment block, paragraph, equation, figure, caption, grouped figure, list, table, or bibliography.
- A paragraph element may contain text, inline math, `@...`, `#qty`, and notes. Convert the paragraph only after all contained constructs are known.
- A figure element may contain image calls, captions, labels, comments, and child figures. Convert the figure only after all contained constructs are known.
- Unknown constructs stop conversion at the smallest construct, but the enclosing semantic element remains unconverted until the rule is decided.

## Comments And Notes

- Typst-local drafting setup for hidden margin notes, including `#import "@preview/drafting..."`, `#let default-rect(...)`, `#let lnote = margin-note.with(...)`, `#let rnote = margin-note.with(...)`, and `#set-margin-note-defaults(hidden: true)`, emits no TeX by itself when notes are converted to source-local comments.
- Convert each Typst `// ...` source comment to one TeX `% ...` comment at the corresponding source location.
- Preserve commented-out Typst blocks line-by-line as TeX comments. Do not move them to the end of the file.
- Convert `#lnote[...]` and `#rnote[...]` to adjacent TeX comments containing the raw note construct unless TeX evidence provides an active note mechanism.
- Comments inside a Typst bracket/parenthesis block remain inside the corresponding TeX command braces or environment.

## Labels, References, And Citations

- Preserve active label keys byte-for-byte. Do not invent labels.
- Commented labels remain commented.
- Convert citations to the citation command style used by TeX evidence, usually `\cite{key}`.
- Before converting any semantic element containing `@target`, locate the active source definition of `target` and determine its kind from the enclosing source element: heading, equation, figure, child figure, table, or citation/bibliography key.
- Choose the TeX reference macro from that recorded source kind, not from nearby prose wording and not from the output label prefix alone. Label prefix may be used only as a consistency check or fallback when the source definition is unavailable.
- Convert ordinary references by target kind using TeX evidence macros when present: figures use `\figref{...}`, tables use `\tabref{...}`, sections use `\secref{...}`, equations use `\eqref{...}`.
- Verify the emitted reference macro against the recorded target kind before moving on. A heading/section label must not be emitted as `\figref`, a figure label must not be emitted as `\secref`, and an equation label must not be emitted as `\figref` or `\secref`.
- If a target kind cannot be determined from source context, labels, or TeX evidence, stop and ask which TeX reference form to use.
- If TeX evidence groups adjacent citation keys in one `\cite{a,b}`, group adjacent Typst citations in the same sentence the same way.

## Units

- Typst-local `#let unit = unit.with(...)` and `#let qty = qty.with(...)` customize Typst rendering only. They emit no TeX by themselves; their effect is represented by the raw siunitx rules below.
- Convert `#qty(value, unit)` to raw siunitx unit strings: `\SI{value}{unit}`.
- Convert `#unit(unit)` to `\si{unit}`.
- Use `\ang{value}` for angle quantities when siunitx is available.
- Do not use siunitx unit macros such as `\meter`, `\per`, `\degree`, `\newton`, `\radian`, `\milli`, or `\percent` unless the TeX evidence explicitly uses that style.
- Do not add global `\sisetup` unless TeX evidence already uses it or the user requests it.
- Do not classify an active TeX `\qty(...)` command as leftover Typst solely from the three-character string `qty`. In this workflow, Typst quantity calls are `#qty(...)`; TeX `\qty(...)` can also be a valid `physics` command depending on context.

## Math

- `#show: equate.with(...)` emits no visible TeX by itself. Preserve equation labels and use the display/math environments indicated by TeX evidence; stop only if a specific equate option changes visible numbering or layout in a way not covered by TeX evidence.
- A custom `#let` helper definition with no active calls in the source emits no TeX by itself. If active calls exist and the helper's TeX behavior is not defined here, in `decisions.md`, or by TeX evidence, stop at the first active call.
- For a source-local math definition `#let name = $expr$` that is used as a math atom, define a TeX macro before first use, e.g. `\newcommand{\name}{<converted expr>}`. Preserve the source name literally in the macro name when TeX permits it.
- When TeX evidence uses the `physics` package, reuse it for vector notation. Convert generic Typst `vb(x)` to `\vb*{x}` so the rendered appearance matches the source as closely as possible.
- Convert Typst `vb(upright(x))` to `\vb{x}` when the `physics` package is available, because this matches the source appearance better than generic bold text commands.
- When TeX evidence uses the `physics` package and the expression is a vector cross product, use `\cross` rather than plain `\times` unless TeX evidence consistently uses `\times`. In `physics`, `\cross` is the vector cross-product symbol shorthand and renders as `\boldsymbol\times`.
- `#set math.cases(gap: ...)` may be ignored when TeX evidence has no custom cases spacing convention; convert the following cases expression with the local TeX evidence's standard cases/aligned style. Stop only if the user or TeX evidence requires preserving the exact spacing value.
- Typst `#h(...)` and `#move(...)` inside math are layout helpers. Preserve visible content inside them, and use TeX spacing/alignment only when needed; do not emit active `#h` or `#move` syntax.
- Convert math from source meaning and local notation, not from visual guesses.
- Quoted text inside math becomes `\text{...}`.
- Use display environments and vector/matrix notation consistent with TeX evidence.
- Use `align` as the default top-level environment for converted display math. Choose another top-level display environment only when it better matches the source expression and TeX evidence. Do not use `equation`; if avoiding `equation` while preserving the expression layout is unclear, stop before converting that display.
- A label attached to display math by a trailing Typst label, such as `$ ... $ <eq_key>`, becomes `\label{eq_key}` inside the corresponding TeX display before `\end{...}`.
- Convert source-local `#let` math definitions before their use. If the TeX representation of a local definition is not known, stop before converting expressions that use it.
- Convert Typst Greek/math identifiers to TeX commands throughout math expressions; do not leave active `theta_L`, `omega`, `tau`, `max(`, `abs(`, or similar Typst/math-source tokens in TeX.
- Typst syntax separators in function calls, `cases`, arrays, and argument lists are not rendered punctuation unless they are part of the mathematical expression.

## Figures, Captions, And Tables

- Typst-local `#let subpar_grid = subpar.grid.with(...)` emits no TeX by itself; it defines the grouped-figure construct that is converted by the `subfig` rules below.
- Convert each active source figure/table to one active TeX float/table unless source structure clearly requires otherwise.
- Preserve image paths, visual order, captions, labels, child order, and source column ratios.
- Convert grouped figures such as `subpar.grid` to one parent `figure` using LaTeX `subfig` and `\subfloat`.
- With `subfig`, use `\usepackage[caption=false,font=footnotesize]{subfig}` and keep child labels inside the corresponding `\subfloat[...]` unless TeX evidence has a different active subfloat setup.
- Child references use the parent figure reference plus `\subref{child-label}`.
- Preserve caption/block shape: one-line source arguments stay one-line; multi-line bracket/parenthesis blocks stay multi-line TeX command bodies or environments unless TeX syntax or the build requires a change.
- Convert `caption: [` blocks to multi-line `\caption{ ... }` bodies and keep comments that were inside the source caption block inside the TeX caption body.

## Lists And Bibliography

- `#set par(leading: ...)` immediately before bibliography or end matter may be ignored unless TeX evidence has an equivalent bibliography spacing convention.
- Convert list items in source order with preserved nesting, labels, indentation intent, and spacing intent.
- If Typst sets enum labels or spacing and `enumitem` is available or already used, encode that with `enumitem` options.
- Convert active Typst bibliography to active TeX bibliography setup. If Typst uses `.bib` and TeX evidence uses BibTeX, emit active `\bibliographystyle{...}` and `\bibliography{...}`. Use the TeX evidence's bibliography style convention; convert the source `.bib` path to the TeX bibliography argument without the `.bib` extension unless TeX evidence keeps extensions.
- Ignore Typst CSL style and bibliography title layout when TeX evidence uses BibTeX styling and heading conventions. Stop only if the user requires preserving the CSL/title formatting in TeX.
- If BibTeX output can contain `\url{...}` entries, ensure the TeX output loads `url` or an equivalent package before the bibliography is built.

## Unknowns

- Stop on unregistered `#command(...)`, unregistered package functions, template/show behavior not accounted for by TeX evidence, unresolved custom `#let`, and references whose TeX form cannot be determined.
- The stop report must include the source lines, the raw unknown construct, and one question asking for the TeX mapping.

## Post-Processing

- After all semantic elements are converted, run the indentation formatter once. Formatting may change leading whitespace only; it must not rewrite text, commands, comments, labels, references, unit syntax, math, captions, or bibliography commands.
- If indentation formatting changes anything other than leading whitespace, discard that formatting result and fix the formatter or the local indentation manually.
