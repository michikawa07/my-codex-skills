---
name: typst-to-tex-converter
description: Convert a Typst manuscript or document into TeX/LaTeX while preserving the Typst source meaning and adapting output syntax to the destination TeX style. Use when the user asks to translate, migrate, port, or convert `.typ` content into `.tex`, especially when an existing TeX file or template should be reused.
---

# Typst to TeX Converter

## Authority Model

- Convert `.typ` content to LaTeX when the user asks for `.tex` unless raw Plain TeX is explicitly requested.
- Typst source determines document content: order, active/commented status, wording, punctuation, paragraph boundaries, line-break intent, labels, references, equations, figures, tables, lists, comments, notes, and bibliography.
- TeX evidence determines output style. A destination/template file is scaffold to preserve. A sample/reference file is convention evidence, not content to copy.
- Preserve reusable TeX scaffold from the selected destination/template or same-class reference: class setup, template marker comments, placeholder commands such as `\history`, `\doi`, and `\markboth` when Typst has no explicit replacement, required package setup, reusable macros used by the output, `\BibTeX`, and caption/subfloat setup. Replace article-specific body and metadata from Typst or explicit user instruction.
- Treat `\corresp{...}` as corresponding-author metadata. Preserve it from an existing destination/template when there is no source replacement; do not copy an unrelated sample/reference article's `\corresp`.
- Package set equals preserved scaffold packages plus packages required by converted source constructs, fixed conventions below, or explicit user instruction.
- Official documentation determines command syntax when source and TeX evidence do not determine it.

Use `STOP:` only when the correct next action is to leave the output file uncreated/unchanged until the user decides. After `STOP:`, ask one concrete question.

## Fixed Conventions

- Quantities and units use raw siunitx unit strings: `\SI{5}{m}`, `\SI{2.2}{m/s}`, `\SI{30}{deg/s}`, `\si{mm}`, `\SI{95}{\%}`.
- Angle quantities use `\ang{...}` when siunitx is available.
- Global `\sisetup` appears only when TeX evidence already uses it or the user requests it.
- Grouped figures with child labels or child references use LaTeX `subfig`: `\usepackage[caption=false,font=footnotesize]{subfig}` plus `\subfloat`.
- With `subfig`, include `\captionsetup[subfloat]{labelformat=parens,labelsep=space,listofformat=subparens,subrefformat=subparens}` unless TeX evidence gives a different active subfloat setup.
- Child figure labels go inside the corresponding `\subfloat[...]`.
- Child figure references use the parent figure reference plus child subreference, e.g. `\figref{fig:parent}\subref{sfig-child}`, or the equivalent macros from TeX evidence.
- For active CJK text with a `pdflatex` build, use `CJKutf8` when the package is available and TeX evidence does not conflict.
- With `CJKutf8`, use `CJK*` unless TeX evidence uses non-star `CJK`.

## Sequential Passes

Run these passes in order. A later pass starts only after the constructs owned by the current pass have no unresolved active Typst syntax except inside comments or `% FIXME typst-to-tex:` fallback markers.

1. Inventory pass
   Record TeX evidence role, protected scaffold, build command, outline, active/commented labels, references, `//` comments and note attachment targets, source-local definitions, grouped-figure parent/child map with ratios, equations, lists, bibliography, units, and active CJK text.

2. STOP pass
   Stop before writing output if a required construct lacks a mechanical TeX representation from source facts, TeX evidence, fixed conventions, or official docs; if exact label preservation is impossible; if CJK/build/bibliography strategy is undetermined; or if user instruction conflicts with source/evidence semantics.

3. Scaffold pass
   Create or update the TeX file by preserving scaffold and replacing only the content region plus metadata derived from Typst or explicit instruction. Keep nonempty template placeholders such as publication history and DOI when Typst has no replacement value.

4. Outline pass
   Convert headings in source order. Active labels in TeX equal active Typst labels; commented labels stay inside comments.

5. Comment pass
   Convert each Typst `//` line to one TeX `%` line at the same structural location. Preserve commented-out Typst blocks line-by-line. Metadata comments stay adjacent to metadata/scaffold, not after `\maketitle`. Convert `#lnote[...]` and `#rnote[...]` to adjacent comments unless TeX evidence provides an active note mechanism. Do not add explanatory comments that are not source comments, source notes, fallback markers, or preserved scaffold comments.

6. Text, citation, and reference pass
   Convert prose paragraph by paragraph. Preserve wording, punctuation, paragraph boundaries, inline math boundaries, source line breaks inside converted command arguments/environments, and reference targets unless TeX syntax or the build requires a change. Resolve every active `@target`; citations become active TeX citations, adjacent source citations merge when TeX evidence uses grouped citations, and ordinary references use the target-specific macros from TeX evidence or standard LaTeX.

7. Math definition pass
   Convert source-local math definitions such as `#let rvec = ...` before converting expressions that use them. Use TeX macros or direct expansion so the Typst identifier is not emitted as active math text.

8. Equation and inline math pass
   Convert every math atom to TeX using source meaning, TeX evidence, fixed conventions, or official docs. Preserve source-local notation style when TeX syntax does not require a change. Typst structural separators such as commas in `cases(...)` arguments are syntax, not rendered math. Use TeX-evidence display environments for numbered displays. Quoted text inside math becomes `\text{...}`. Vectors use TeX-evidence notation, such as `physics` commands when that package is the local convention.

9. Unit pass
   Convert all `#qty` and `#unit` constructs with the raw siunitx convention above. Converted output has zero active occurrences of custom unit macros such as `\meter`, `\per`, `\degree`, `\newton`, `\radian`, or `\milli`.

10. List pass
    Convert list items in source order with preserved nesting, numbering, indentation intent, and spacing intent. If Typst sets enum labels or spacing and `enumitem` is available or already used, encode that with `enumitem` options.

11. Figure and table pass
    Convert each active source figure, grouped figure, and table into an active TeX float/table. Preserve image paths, captions, labels, visual order, child order, source column ratios, and one-parent-float structure for each grouped source figure. Preserve source block shape: `caption: "..."` stays one-line unless TeX syntax requires otherwise, while any bracketed or parenthesized Typst block spanning lines becomes a multi-line TeX command/environment body with source line breaks and internal comments preserved inside the corresponding TeX braces/environment.

12. Bibliography pass
    Convert active Typst bibliography into active TeX bibliography setup. If Typst uses `.bib` and TeX evidence uses BibTeX, emit active `\bibliographystyle{...}` and `\bibliography{...}`.

13. Build and audit pass
    Run `scripts/audit_tex_conversion.py source.typ output.tex --fix`; include `--tex-evidence evidence.tex` when available. Then run the user-provided build command, project/editor config, repository script, or `latexmk -pdf` for standalone output.

## Fallback Markers

If a construct cannot be converted mechanically after the STOP pass, insert a local marker:

`% FIXME typst-to-tex: <source fragment>`

The output is incomplete while any fallback marker remains. Active Typst syntax belongs only in comments or fallback markers.

## Completion Gate

Before reporting success, verify:

- audit script passes, with TeX evidence when available
- build command passes, or a `STOP:` report explains why it cannot run
- outline order, paragraph sentence counts, list item counts, and figure/table counts match the source
- source wording is preserved without summarization
- active label set and reference targets match Typst exactly
- label and reference keys keep source spelling literally
- each source comment appears once at the corresponding location unless repeated in source
- output comments are limited to source comments, active source notes, fallback markers, and preserved scaffold comments
- comments that occur inside a source bracket/parenthesis block remain inside the corresponding TeX command braces or environment
- source one-line arguments remain one-line and source multi-line arguments remain multi-line unless TeX syntax or the build requires a change
- active bibliography exists when source bibliography is active
- active Typst command/reference/label syntax remains only in comments or fallback markers
- raw Typst math tokens such as `theta_`, `integral`, `dots`, `plus.minus`, `max(`, and escaped math identifiers such as `F\_x` remain only in comments
- Typst syntax separators do not appear as rendered punctuation inside converted equations
- subfigure labels are inside `\subfloat[...]`, and child references include parent plus `\subref`
- multi-line Typst bracket/parenthesis blocks remain multi-line TeX blocks when converted to command arguments or environments
- raw siunitx unit style is used
- protected scaffold is preserved

Fix failed gate items by returning to the corresponding earlier pass.
