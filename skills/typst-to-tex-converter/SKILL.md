---
name: typst-to-tex-converter
description: Convert a Typst manuscript or document into TeX/LaTeX while preserving the Typst source meaning and adapting output syntax to the destination TeX style. Use when the user asks to translate, migrate, port, or convert `.typ` content into `.tex`, especially when an existing TeX file or template should be reused.
---

# Typst to TeX Converter

## Operating Model

- Convert `.typ` content to LaTeX when the user asks for `.tex` unless raw Plain TeX is explicitly requested.
- Typst source determines content, order, active/commented status, labels, references, equations, figures, tables, lists, comments, and bibliography.
- TeX evidence determines style. A destination/template is scaffold to preserve; a sample/reference is evidence for conventions only.
- From a sample/reference, copy only mechanisms needed by the source or Fixed Defaults. Do not copy unrelated title/author/address/history, unused content-specific macros, or packages that are not required by the converted source.
- For a full-document sample/reference in the same target class, preserve reusable class scaffold such as class setup blocks, template marker comments, `\BibTeX` definitions, reference macros used by output, and caption/subfloat setup required by output; replace only article-specific metadata and body content.
- When no TeX evidence is provided, use a minimal standalone LaTeX article with only packages directly required by source constructs or Fixed Defaults.
- Official documentation determines syntax when a command, package, class, or Typst construct is not determined by source or TeX evidence.
- Protected scaffold means class, preamble, metadata, template markers, and non-content regions in the TeX evidence. Preserve it; make only mechanical additions required by source constructs, Fixed Defaults, or explicit user instruction.
- If TeX evidence conflicts, use the file explicitly named by the user for that role. If resolving the conflict changes semantics, use `STOP:`.

Use `STOP:` only when the correct next action is to leave the output file uncreated/unchanged until the user decides. After `STOP:`, ask one concrete question.

## Fixed Defaults

These defaults are part of this converter and require no extra confirmation unless the user gives a conflicting instruction.

- `#qty` and `#unit` become raw siunitx units: `\SI{5}{m}`, `\SI{2.2}{m/s}`, `\SI{30}{deg/s}`, `\si{mm}`, `\SI{95}{\%}`.
- Do not define custom siunitx unit macros for converted Typst units; write the raw unit string in each `\SI`/`\si` call.
- Do not add global `\sisetup` unless TeX evidence already uses it or the user explicitly requests it.
- Angle quantities become `\ang{...}` when siunitx is available.
- Grouped figures with child labels or child references use LaTeX `subfig`; add `\usepackage[caption=false,font=footnotesize]{subfig}` when needed.
- When using `subfig`, add `\captionsetup[subfloat]{labelformat=parens,labelsep=space,listofformat=subparens,subrefformat=subparens}` unless TeX evidence gives a different active subfloat caption setup.
- Child figure labels go inside each child `\subfloat[...]`.
- Child figure references use the parent figure plus child subreference, e.g. `\figref{fig:parent}\subref{sfig-child}`, or an equivalent macro already present in TeX evidence.
- For active CJK text with a `pdflatex` build, `CJKutf8` is the default strategy when the package is available and TeX evidence does not conflict.

## Workflow

1. Inspect the full Typst source and the TeX evidence before editing.
2. Make a compact checklist of: TeX evidence role, outline, protected scaffold, metadata source, active/commented labels, references, source `//` comment line count and attachment targets, grouped-figure parent/child label map, equations and source-local math definitions, lists, bibliography, CJK/Unicode, and build command.
3. Run STOP Conditions before creating or changing the output file; CJK support is decided before output creation, not after a failed build.
4. If the output is based on a template or existing destination TeX file, preserve the protected scaffold and replace only the content region unless the user explicitly requests otherwise.
5. Convert by the smallest coherent interval: heading, paragraph block, equation, list, figure/table, grouped figure, comment block, or bibliography block.
6. For each interval, preserve source wording, order, paragraph boundaries, active/commented status, label spelling, math/text boundaries, reference targets, indentation, and blank-line intent; choose TeX mechanisms from TeX evidence, Fixed Defaults, or official documentation.
7. Before leaving an interval, compare source and output for labels, references, comments, paragraph sentence counts, list item counts, construct structure, and remaining active Typst syntax; evaluate active constructs only on non-comment output lines.
8. If active Typst command/reference/label syntax remains, source content is summarized, or an active construct is only commented out in the output interval, keep that interval open and convert it before moving on.
   Typst wrapper delimiters such as standalone `)`, `]`, or trailing function-call syntax are source syntax; remove or convert them, never leave them as active TeX text.
9. Run `scripts/audit_tex_conversion.py source.typ output.tex --fix`; if TeX evidence is available, include `--tex-evidence evidence.tex`. Fix reported failures before moving on.
10. Compile after meaningful chunks when a build command is known; fix conversion errors in the current interval before moving on.

## Construct Rules

References:

- Resolve every Typst reference to its source label and target type before conversion.
- Convert every active Typst `@target`: citations become active TeX citations, and source labels become the typed TeX reference command for the resolved target.
- Adjacent Typst citations with no intervening prose become one TeX citation command with comma-separated keys when TeX evidence uses grouped citations.
- Use the TeX reference command from TeX evidence for that target type; if none exists, use standard LaTeX reference commands for ordinary sections, figures, tables, and equations.
- For every subfigure child target, look up its parent in the grouped-figure label map and output the parent figure reference plus the child `\subref{...}`.
- Use figure reference macros only with parent figure labels; child labels appear in `\subref{...}` only.
- Use a reference wrapper macro only when that macro appears in the Typst source definitions or TeX evidence; otherwise emit the reference commands directly.

Labels:

- Place each label on the corresponding converted TeX construct.
- Keep active labels active and commented labels inside comments.
- In `\label{...}` and reference keys, keep source key characters such as `_`, `:`, and `-` literal; escape characters only in active text, not in keys.
- Label spelling changes require `STOP:`.

Comments:

- Convert `// ...` to `% ...`.
- Preserve each source `//` line as one TeX comment line at the corresponding location; convert commented-out Typst blocks line-by-line, not as summaries.
- A source comment appears once in the output unless it appears multiple times in the source; do not duplicate comments to satisfy audits.
- Preserve block shape, order, indentation intent, and original Typst fragments inside comments.
- Place comments adjacent to the converted construct they annotate, including comments inside captions, figure arguments, equations, and commented-out blocks.
- Margin notes such as `#lnote[...]` and `#rnote[...]` become adjacent TeX comments unless TeX evidence provides an active note mechanism.

Math:

- For each math interval, identify symbols, Greek names, functions/operators, relations, delimiters, subscripts/superscripts, and source-local definitions before writing TeX.
- Every source math fragment remains active TeX math: inline Typst math becomes inline TeX math, display Typst math becomes the display environment used by TeX evidence.
- Resolve source-local math definitions such as `#let name = $...$`; when the name is used later, define/use a TeX macro or expand the definition, but do not emit the Typst identifier as raw math text.
- Convert every math atom to the TeX mechanism from TeX evidence, Fixed Defaults, or official documentation.
- Convert Typst math names and functions to TeX commands; raw tokens such as `k_tau`, `theta_L`, `integral`, `dots`, `plus.minus`, or `max(` must not remain in active TeX.
- Convert Typst math quoted text such as `x_"foot"` and `"otherwise"` to `\text{...}` in TeX math, not `\mathrm{...}`.
- If the source imports vector notation and TeX evidence provides `physics`, use the package vector commands for converted vectors instead of raw `\mathbf{...}`.
- Preserve mathematical meaning, order, labels, and reference targets.
- Use TeX evidence for display environments and notation macros.
- If TeX evidence consistently uses one top-level display math environment for numbered equations, use that environment for converted numbered displays unless the source construct requires a different environment.
- Place equation labels inside the converted display math construct.
- After conversion, escaped math identifiers such as `F\_x` and source-style math tokens may remain only inside comments.

Figures and tables:

- Preserve logical structure: parent object, child objects, captions, labels, image paths, layout ratios, spacing, placement, and visual order.
- Every active source figure, table, or grouped figure has an active TeX float or table output.
- For grouped figures, implement child figures with `subfig` according to Fixed Defaults unless TeX evidence provides another subfigure mechanism.
- Represent source column ratios as child widths, preserve source order, and keep one parent float for one grouped source figure.
- Parent labels belong to the parent float; child labels belong inside child `\subfloat[...]`.
- Active grouped figures produce active `\subfloat` children; Typst source comments may be preserved as comments but do not replace the active figure output.

Lists:

- Preserve item text, order, nesting, numbering, indentation intent, and spacing intent.
- Use the list mechanism from TeX evidence; if Typst specifies enum numbering, indentation, or spacing and `enumitem` is available, encode those options with `enumitem` rather than local label redefinition.

Units and package commands:

- Convert `#qty` and `#unit` using raw siunitx units from Fixed Defaults.
- Add `siunitx` when unit conversion requires it and TeX evidence does not conflict.
- Use TeX evidence for existing package-command style; use official documentation for unfamiliar commands.

Bibliography:

- Convert active Typst bibliography to active TeX bibliography.
- If Typst uses a `.bib` file and TeX evidence uses BibTeX, use active `\bibliographystyle{...}` and `\bibliography{...}`.
- Bibliography build errors are build blockers to report, not content to remove.

Preamble and metadata:

- Preserve template/destination scaffold exactly except for required mechanical additions.
- Preserve reusable class scaffold from a full-document sample/reference when using its class/style; keep nonempty template placeholders such as publication history and DOI if the Typst source has no replacement value.
- For a sample/reference file, reuse style mechanisms but regenerate title, authors, addresses, headers, correspondence, and other metadata from the Typst source or explicit user instruction.
- Define new macros only when used by the converted output, required by source-local definitions, or already part of preserved destination/template scaffold.

Build and Unicode:

- Use the user-provided build command first, then project/editor config, then repository scripts/docs, then `latexmk -pdf` for a standalone LaTeX output.
- If active CJK text is present, choose a concrete engine/package strategy from TeX evidence, project build facts, Fixed Defaults, or explicit user instruction; record the evidence for that choice.
- If using `CJKutf8` for `pdflatex`, add `\usepackage{CJKutf8}` and wrap active CJK document content with `CJK*`.
- Fix build failures while preserving source content, comments, labels, bibliography, and template scaffold; otherwise report the blocker.
- Build success does not justify summarizing source text or commenting out active source constructs.

## STOP Conditions

Use `STOP:` before writing output when the next correct action is no file change:

- a required source construct has no mechanical TeX representation from source facts, TeX evidence, Fixed Defaults, or official docs
- preserving a label exactly is impossible
- active CJK text requires an engine/package strategy not determined by TeX evidence, project build facts, Fixed Defaults, or user instruction
- conversion requires a class, template, build-toolchain, shell option, or bibliography-tool decision outside TeX evidence, Fixed Defaults, and explicit user instruction
- user instruction conflicts with source or TeX evidence in a way that changes output semantics

## Final Audit

Before reporting success, mechanically check and report:

- `scripts/audit_tex_conversion.py source.typ output.tex` passes; with TeX evidence, `scripts/audit_tex_conversion.py source.typ output.tex --tex-evidence evidence.tex` passes
- outline order, paragraph sentence counts, and list item counts match the source
- active source constructs are represented by active non-comment TeX constructs
- no active source interval is summarized, compressed, omitted, or replaced by a comment-only placeholder
- active Typst command/reference/label syntax remains only inside comments
- active labels and references are accounted for
- label and reference keys preserve source spelling literally
- commented labels remain in comments
- reference wrapper macros correspond to source-local definitions or TeX evidence
- subfigure labels are inside `\subfloat[...]`
- subfigure references include parent plus `\subref`
- child labels are not the sole argument of figure reference macros
- subfigure audit counts use non-comment lines only
- raw-unit style is used, and occurrences of `\meter`, `\per`, `\degree`, `\newton`, `\radian`, and `\milli` are zero
- every source comment block is accounted for at its corresponding location
- source `//` comment line count equals the corresponding converted TeX comment line count, excluding template comments already present in TeX evidence
- escaped math identifiers and source-style math tokens remain only in comments
- active bibliography commands are present when the source bibliography is active
- protected scaffold is preserved
- selected build command was run, or a `STOP:` report explains why it cannot run

Fix failed audit items before reporting success. Report remaining blockers separately from successful checks.
